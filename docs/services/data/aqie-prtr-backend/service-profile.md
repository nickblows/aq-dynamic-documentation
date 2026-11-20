# aqie-prtr-backend

> The read-only data API behind the UK Pollutant Release and Transfer Register (PRTR). Serves
> industrial facility records, their annual pollutant releases and transfers, and pre-signed
> links to the published annual PRTR dataset files held in S3.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-prtr-backend`](https://github.com/DEFRA/aqie-prtr-backend) |
| Service domain | `Data` |
| Service type | `Auxilary Backend Service` |
| Lifecycle stage | `Beta` |
| Primary language | JavaScript |
| Runtime | Node.js `>=24` (ES modules); container parent image is Node 24.22.1 while `.nvmrc` still says `v24.14.1` |
| Default branch | `main` |
| Created (UTC) | `2026-05-21` |
| Last main commit (UTC) | `2026-10-26T16:50:55Z` |
| Last analysed commit | `caf106fe` |
| Last analysed (UTC) | `2026-11-19T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Serves paginated facility search over the PRTR register by name, region/county,
  river basin district or reporting year.
- Serves a geospatial "facilities near me" search, sorted nearest-first, using a
  MongoDB `2dsphere` index over facility coordinates.
- Serves a facility's release and transfer record for a chosen reporting year, split
  into releases to air, water and soil, transfers to waste water, and waste transfers.
- Serves facility reference detail (address, NACE code, NUTS region, river basin) and
  the facility's latest competent authority and contact details.
- Serves line-level "additional detail" for a single release, transfer or waste line.
- Acts as a backend-for-frontend for place-name lookup, proxying `aqie-location-backend`
  and mapping its raw OS Names payload into a stable public shape.
- Issues time-limited S3 pre-signed URLs for the published annual PRTR dataset XML files.
- Ships a TSV ingest CLI (`scripts/tsv-ingest`) that loads the Ricardo PRTR public export into MongoDB.
  Its own code describes it as a one-shot migration, run by hand.

**Does not:**

- Render any user interface — that is `aqie-prtr-frontend`.
- Hold ambient air quality measurements, DAQI bands or forecasts — those are
  `aqie-back-end` and `aqie-forecast-api`.
- Serve historic ambient monitoring extracts — that is `aqie-historicaldata-backend`.
- Hold the OS Names API key or call Ordnance Survey directly — all place-name lookups
  go through `aqie-location-backend`, which owns that credential.
- Ingest PRTR data automatically. There is **no scheduler, cron job or queue consumer**
  in the running service; the TSV loaders are a manual CLI (see Section 7).
- Generate or upload the annual PRTR dataset XML files. It only lists and signs files that
  already exist in its S3 bucket, and never writes to the bucket.
- Read the report year list from MongoDB. `GET /reports` serves a fixed list held in code.
- Receive PRTR submissions. The `aqie-prtr-submissions-backend` and
  `aqie-prtr-submissions-frontend` repositories created in October 2026 are unconnected
  scaffolds: neither calls this service nor is called by it, and they share no database,
  bucket or URL setting with it.

## 3. Architecture

**Pattern:** Hapi HTTP API acting as a backend-for-frontend over MongoDB and S3, plus a
separate offline Node CLI for bulk data loading. Routes are thin — validation with `joi`,
delegation to a service module, and mapping of typed service errors (`LocationBackendError`,
`S3BackendError`, `ReportsBackendError`) onto `502 Bad Gateway`.

| Component | Path | Responsibility |
|---|---|---|
| Routes | `src/routes/` | One module per resource; `joi` query/param schemas and error mapping |
| Facility search | `src/services/facility-search-service.js` | Field search by name, region, river basin or year; escapes regex metacharacters before building the filter |
| Facility geo search | `src/services/facility-service.js` | `$geoNear` aggregation returning distance-sorted results |
| Facility record | `src/services/facility-record-service.js` | Shapes a facility header plus one year's report into the record DTO |
| Facility details | `src/services/facility-details-service.js` | Address, NACE, NUTS and river basin reference view |
| Competent authority | `src/services/competent-authority-service.js` | Latest competent authority and contacts for a facility |
| Additional detail | `src/services/additional-detail-service.js` | Single release/transfer/waste line detail |
| Location BFF | `src/services/location-service.js`, `location-mapper.js` | Calls `aqie-location-backend` and normalises the response |
| Coordinate helper | `src/services/coords.js` | Converts OS grid eastings/northings to WGS84 via `mt-osgridref` |
| S3 access | `src/services/s3-service.js` | Object listing, metadata lookup by filename, pre-signed URL generation |
| Reports | `src/services/reports-service.js` | Serves the fixed report year list and orchestrates download-link creation |
| Report year list | `src/data/example-reports.js` | Fixed list of report years 2007 to 2025 with a `reportIsLive` flag (2025 is not live); despite its name this is live data, not a template leftover |
| Plugins | `src/plugins/` | MongoDB connection, router, request logging, tracing, graceful shutdown |
| Resilience helper | `src/common/helpers/fetch-with-retry.js` | Timeout (10 seconds by default) and optional retry wrapper for outbound HTTP; no caller sets retries, so there are none |
| TSV ingest CLI | `scripts/tsv-ingest/` | 18 ordered loaders, quarantine handling, index creation |
| Config | `src/config.js` | `convict` schema for all endpoints, stores and limits |

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/health` | Liveness probe | — | Status payload |
| `GET` | `/facilities/search` | Paginated field search | `searchType` (`name`\|`region`\|`river-basin`\|`year`), `q`, `page`, `perPage` (max 100) | `count`, `total`, `page`, `perPage`, `totalPages`, `results[]` with id, name, main PRTR activity, latest reporting year and types |
| `GET` | `/facilities/nearby` | Distance-sorted geo search | `lat`, `lng`, `radius` miles (default and max 50), `page`, `perPage` | Same envelope as search, with distance per facility |
| `GET` | `/facilities/{id}/details` | Facility reference detail | `id` = `internalFacilityId` | Address, NACE, NUTS region, river basin district |
| `GET` | `/facilities/{id}/competent-authority` | Latest competent authority (year-independent) | `id` | Authority name and contact details |
| `GET` | `/facilities/{id}/record/{year?}` | Release and transfer record; year defaults to the facility's latest reporting year | `id`, optional `year` | Facility header plus `releasesToAir`, `releasesToWater`, `releasesToSoil`, `transfersToWasteWater`, `wasteTransfers` |
| `GET` | `/facilities/{id}/record/{year}/lines/{lineId}` | Detail of one release, transfer or waste line | `id`, `year`, `lineId` (`ricardoReleaseTransferId`) | Line detail, or `404` when not found |
| `GET` | `/locations/search` | Place-name lookup proxied to `aqie-location-backend` | `q` (2–100 chars, restricted character set) | Normalised candidate locations with a `count` |
| `GET` | `/reports` | Catalogue of report years | — | Report records (id, year, `reportIsLive`) with `count`, taken from a fixed list in code rather than MongoDB |
| `GET` | `/reports/get-download-link/{year}` | Pre-signed download link for a year's dataset | `year` (integer, 2007 to current year) | `{ downloadLink }` |

> The `README.md` API table is stale — it still lists the CDP template's `/example`
> endpoints and does not describe any of the routes above. The route descriptions for
> `/reports` also say it checks S3 health and reads the database, which the handler does not do.

### Report download mechanism

`/reports/get-download-link/{year}` is meant to look the S3 object key up in MongoDB first, but that
lookup cannot succeed: it reads a collection named `Reports` for an `s3Key` field, the TSV loader writes a
differently named `reports` collection, nothing writes `s3Key`, and the write-back that would cache the key
is commented out. So every request scans the bucket with `ListObjectsV2`, issues a `HeadObject` per key
and matches the object metadata field `encodedfilename` against the expected name
`uk_prtr_dataset_<year>.xml`. It then returns a `GetObject` pre-signed URL valid for 9,000 seconds
(150 minutes). Credentials come from the ECS task IAM role — the service holds no static AWS keys. The
scan is `O(objects)` HEAD requests on every download and is a latency and cost risk if the bucket grows;
see Section 11.

The `encodedfilename` key is the user metadata that the CDP Uploader writes on the files it stores, and
the uploader names objects by upload and file identifiers rather than by file name, which explains why the
scan is needed. The files were therefore almost certainly uploaded through a CDP Uploader flow, although
no PRTR repository calls the uploader.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-location-backend` | AQIE service | `POST /osnameplaces` (`OSPLACE_API_URL`) | `{ userLocation }` in; OS Names matches out. Forwards the CDP trace header | CDP internal network; optional `x-api-key` from `OSPLACE_API_KEY` for ephemeral environments |
| MongoDB | Datastore | Driver connection (`MONGO_URI`) | Facilities, facility reports, reference collections | Connection string |
| AWS S3 | Datastore | `ListObjectsV2`, `HeadObject`, `GetObject` pre-sign (`S3_BUCKET`, `AWS_REGION`); read-only | Annual PRTR dataset XML files | ECS task IAM role |

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| `aqie-prtr-frontend` | `GET /facilities/search`, `GET /facilities/nearby`, `GET /facilities/{id}/details`, `GET /facilities/{id}/competent-authority`, `GET /facilities/{id}/record/{year?}`, `GET /facilities/{id}/record/{year}/lines/{lineId}`, `GET /locations/search`, `GET /reports`, `GET /reports/get-download-link/{year}` | Facility search results, facility records, place-name matches, report catalogue and pre-signed download links |

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).
> The catalogue entry `prtr-frontend__prtr-backend` lists all nine endpoints. No other service
> calls this one; in particular the PRTR submissions services do not.

## 7. Data

- **Stores:** MongoDB (`MONGO_DATABASE`, default `aqie-prtr-backend`) and one AWS S3 bucket
  (`S3_BUCKET`) holding the published annual PRTR dataset XML files.
- **Origin of the data: an offline manual load, not a live feed.** `scripts/tsv-ingest` is a
  CLI that reads a directory of tab-separated files from the Ricardo PRTR public export
  (`TSV_DIR`) and upserts them into MongoDB. It was added between June and July
  2026 (merged in July as the data migration scripts) and its own comments call it a one-shot
  migration. It is invoked by hand — locally, in CI, or "inside a CDP break-glass session" per its
  own configuration comments. Nothing in the running Hapi service triggers it; there is no cron,
  queue or webhook. Whether it has been run since the first load is not known.
- **Ingest loaders:** 18 loaders run in an explicit `meta.order` sequence across three phases:
  - *reference* (orders 10–23) → `agencies`, `regulatory_authorities`, `pollutants`,
    `nace_codes`, `nuts_regions`, `activities`, `river_basin_districts`, `counties`,
    `countries`, `methods`, `release_transfer_types`, `confidential_reasons`,
    `methodology_notes`, `reports`
  - *in-memory* (order 25) → `postcodeMap` from `postcode_location.tsv`, used to backfill
    coordinates where the source facility row has none; writes no collection
  - *core* (orders 30–32) → `facilities`, `facility_reports`, then `facilityLatestSummary`
    which updates `facilities` in place with precomputed fields such as
    `mainPrtrActivity` and `latestReportingYear`
- **Key entities:**
  - **Facility** (`facilities`): keyed by `facilityCode` (unique index) with a deterministic
    `internalFacilityId` minted as `f-` plus a truncated SHA-256 of the facility ID, so IDs
    are stable across environments and re-runs. Embeds parent company, permits, INSPIRE
    mapping and EU production hierarchy; denormalises agency, regulatory authority, NACE,
    NUTS, river basin and county names. `facility.tsv` holds one row per facility per year;
    the loader groups by `facility_code` and keeps the latest-year row as the header.
  - **Facility report** (`facility_reports`): one document per facility per reporting year,
    containing `pollutantReleases` (each carrying a `mediumCode` of `AIR`, `WATER` or `LAND`,
    a `pollutantId`/`pollutantName` and a `totalQuantity` value and unit),
    `pollutantTransfers`, and `wasteTransfers` (quantity, waste type code, treatment code).
    Each line carries a `ricardoReleaseTransferId`, which is the `lineId` exposed by the API.
  - **Reference collections** as listed above, plus `reports` (the year catalogue, from
    `year.tsv`). No API route reads it: `/reports` serves a fixed list in code, and the
    download-link lookup queries a differently named `Reports` collection.
- **Ingest safety:** loaders are idempotent upserts and stop on first failure. Rows whose
  column count deviates from the expected header width are written to a quarantine file
  rather than loaded — usually caused by embedded newlines in free-text fields. `--dry-run`
  parses without writing; `--reset` drops the whole database and requires a second
  `--confirm-reset` flag.
- **Indexes:** created by `scripts/tsv-ingest/create-indexes.js`, including a `2dsphere`
  index on facility `location` (with a partial variant) that backs `/facilities/nearby`.
  The Hapi `mongodb` plugin creates only the `mongo-locks` and leftover `example-data`
  indexes at start-up.
- **Retention / refresh:** no automated refresh. The dataset changes only when an operator
  runs the ingest CLI against a new Ricardo export, and when new dataset XML files are
  placed in the S3 bucket (almost certainly through the CDP Uploader; nothing in this service
  or the PRTR frontend does it). The 2025 reporting year is listed but flagged not live.
  There is no loader, scheduler or upload route for new annual data in any PRTR repository.
- **Pollutant thresholds:** not yet available — the record service returns `threshold: null`
  because `pollutant_threshold` is absent from the Ricardo export.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `PORT`, `HOST` | HTTP listener |
| `NODE_ENV`, `ENVIRONMENT`, `SERVICE_VERSION` | Runtime identity; `ENVIRONMENT` is also interpolated into the default location-backend URL |
| `MONGO_URI`, `MONGO_DATABASE` | MongoDB connection |
| `MONGO_RETRY_WRITES`, `MONGO_READ_PREFERENCE` | MongoDB driver overrides |
| `S3_BUCKET`, `AWS_REGION` | Report file storage |
| `OSPLACE_API_URL` | `aqie-location-backend` `/osnameplaces` endpoint |
| `OSPLACE_API_KEY` | Optional `x-api-key` for protected ephemeral environments |
| `OSPLACE_API_TIMEOUT_MS` | Timeout for location-backend calls |
| `ACCESS_CONTROL_ALLOW_ORIGIN_URL` | CORS origin |
| `HTTP_PROXY` | CDP egress proxy |
| `TRACING_HEADER` | Name of the CDP trace header, forwarded upstream |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |
| `TSV_DIR`, `INGEST_BATCH_SIZE`, `INGEST_DRY_RUN` | TSV ingest CLI only |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`,
  parent image `3.2.4-node24.22.1`; entrypoint `node src`.
- **Internal address:** by CDP convention `https://aqie-prtr-backend.<env>.cdp-int.defra.cloud`. The
  repository does not state it; the frontend takes it from `BACKEND_URL`.
- **Local development:** `compose.yml` provides MongoDB, Redis and a `floci` container.
  Note the service itself does not use Redis — it is inherited from the CDP template.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — security audit, format check, lint, tests and a
    Docker build test on PR, plus a Sonar scan that runs only when `SONAR_TOKEN` is set and the
    actor is not Dependabot
  - `.github/workflows/publish.yml` — test, build and publish on push, then a Sonar scan that
    does not fail the build
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish
- **Testing:** `vitest` with `vitest-mongodb` and coverage; `npm run security-audit` runs
  `npm audit --audit-level=critical` in the pre-commit hook.

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, formatted with `@elastic/ecs-pino-format` in production.
  In production the `authorization` and `cookie` request headers and all response headers are
  removed from logs.
- **Tracing:** `@defra/hapi-tracing` propagating the header named in `TRACING_HEADER`; the
  location-service client forwards it to `aqie-location-backend`.
- **Metrics:** `@defra/cdp-metrics`.
- **Auditing:** `@defra/cdp-auditing` is declared but never imported, so no audit events are
  emitted.
- **Shutdown:** `hapi-pulse` for graceful draining.
- **Locking:** `mongo-locks` is a dependency and its index is created, but no ingest job runs
  in-process, so nothing currently takes a lock.

## 11. Open Questions

- [ ] Has `scripts/tsv-ingest` been run since the first load? Its own code calls it a one-shot
      migration. If it is to be repeated, who runs it, against which Ricardo export and on what
      cadence, and how will a new reporting year reach the register? The 2025 year is listed but
      not live (`oq-010`).
- [ ] The `encodedfilename` object metadata that the lookup relies on is the key the CDP Uploader
      writes, so the `uk_prtr_dataset_<year>.xml` files were almost certainly uploaded through an
      uploader flow. Which service or person initiates those uploads, and who produces the XML?
      No PRTR repository calls the uploader (`oq-010`).
- [ ] `scripts/tsv-ingest/config.js` defaults `TSV_DIR` to a developer's local Windows
      user-profile path (the file header says no host-specific path is baked in). Confirm this is
      only a convenience default and should be replaced.
- [ ] `src/config.js` carries a `TODO: replace this commented code before going to prod`
      against the `OSPlaceApiUrl` block, and `location-service.js` carries a
      `TODO: remove when going to PROD` against the `x-api-key` header. Confirm the intended
      production configuration before go-live.
- [ ] The MongoDB shortcut for the S3 key cannot succeed (it reads a `Reports` collection for an
      `s3Key` field that nothing writes, and the write-back is commented out), so every download
      request issues one `HeadObject` per bucket object. Confirm the expected bucket size and
      whether the shortcut should be fixed.
- [ ] Pre-signed URLs last 150 minutes. Confirm this is an accepted exposure window for
      published open data.
- [ ] Are pollutant reporting thresholds expected in a future Ricardo export? The record
      service returns `null` for every threshold today.
- [ ] `/reports` serves a fixed year list from `src/data/example-reports.js` although its route
      description and commented-out code say it reads MongoDB. Should it read the `reports`
      collection the ingest loads? `src/services/ExampleFind.js` (imported by nothing) and the
      `example-data` index in `src/plugins/mongodb.js` are template leftovers that can be removed.
- [ ] (catalogue `oq-032`) How will the PRTR submissions services relate to this service? They are unconnected
      scaffolds today, so it is unknown whether submissions will be written to this database,
      feed the TSV or XML route, or stay separate.
