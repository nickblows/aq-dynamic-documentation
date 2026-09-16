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
| Runtime | Node.js `>=24` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2026-05-21` |
| Last main commit (UTC) | `2026-07-23T14:41:04Z` |
| Last analysed commit | `4cff62c4` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
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
- Ships an operator-run TSV ingest CLI (`scripts/tsv-ingest`) that loads the Ricardo
  PRTR public export into MongoDB.

**Does not:**

- Render any user interface — that is `aqie-prtr-frontend`.
- Hold ambient air quality measurements, DAQI bands or forecasts — those are
  `aqie-back-end` and `aqie-forecast-api`.
- Serve historic ambient monitoring extracts — that is `aqie-historicaldata-backend`.
- Hold the OS Names API key or call Ordnance Survey directly — all place-name lookups
  go through `aqie-location-backend`, which owns that credential.
- Ingest PRTR data automatically. There is **no scheduler, cron job or queue consumer**
  in the running service; the TSV loaders are a manual CLI (see Section 7).
- Generate the annual PRTR dataset XML files. It only lists and signs files that already
  exist in its S3 bucket.

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
| Reports | `src/services/reports-service.js` | Report year catalogue and download-link orchestration |
| Plugins | `src/plugins/` | MongoDB connection, router, request logging, tracing, graceful shutdown |
| Resilience helper | `src/common/helpers/fetch-with-retry.js` | Timeout and retry wrapper for outbound HTTP |
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
| `GET` | `/reports` | Catalogue of published report years | — | Report records with `count` |
| `GET` | `/reports/get-download-link/{year}` | Pre-signed download link for a year's dataset | `year` (integer, 2007 to current year) | `{ downloadLink }` |

> The `README.md` API table is stale — it still lists the CDP template's `/example`
> endpoints and does not describe any of the routes above.

### Report download mechanism

`/reports/get-download-link/{year}` first looks the S3 object key up in MongoDB. If the key
is absent it falls back to scanning the bucket with `ListObjectsV2`, issuing a `HeadObject`
per key and matching the object metadata field `encodedfilename` against the expected name
pattern `uk_prtr_dataset_<year>.xml`. It then returns a `GetObject` pre-signed URL valid for
9,000 seconds (150 minutes). Credentials come from the ECS task IAM role — the service holds
no static AWS keys. The metadata scan is `O(objects)` HEAD requests and is a latency risk if
the bucket grows; see Section 11.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-location-backend` | AQIE service | `POST /osnameplaces` (`OSPLACE_API_URL`) | `{ userLocation }` in; OS Names matches out. Forwards the CDP trace header | CDP internal network; optional `x-api-key` from `OSPLACE_API_KEY` for ephemeral environments |
| MongoDB | Datastore | Driver connection (`MONGO_URI`) | Facilities, facility reports, reference collections | Connection string |
| AWS S3 | Datastore | `ListObjectsV2`, `HeadObject`, `GetObject` pre-sign (`S3_BUCKET`, `AWS_REGION`) | Annual PRTR dataset XML files | ECS task IAM role |

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| `aqie-prtr-frontend` | `GET /facilities/search`, `GET /facilities/nearby`, `GET /facilities/{id}/details`, `GET /facilities/{id}/competent-authority`, `GET /facilities/{id}/record/{year?}`, `GET /facilities/{id}/record/{year}/lines/{lineId}`, `GET /locations/search`, `GET /reports`, `GET /reports/get-download-link/{year}` | Facility search results, facility records, place-name matches, report catalogue and pre-signed download links |

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).
> The catalogue entry `prtr-frontend__prtr-backend` lists only four of the nine endpoints
> actually called — see Section 11.

## 7. Data

- **Stores:** MongoDB (`MONGO_DATABASE`, default `aqie-prtr-backend`) and one AWS S3 bucket
  (`S3_BUCKET`) holding the published annual PRTR dataset XML files.
- **Origin of the data: an offline manual load, not a live feed.** `scripts/tsv-ingest` is a
  CLI that reads a directory of tab-separated files from the Ricardo PRTR public export
  (`TSV_DIR`) and upserts them into MongoDB. It is invoked by hand — locally, in CI, or
  "inside a CDP break-glass session" per its own configuration comments. Nothing in the
  running Hapi service triggers it; there is no cron, queue or webhook.
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
    `year.tsv`).
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
  placed in the S3 bucket.
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
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`;
  entrypoint `node src`.
- **Internal address:** `https://aqie-prtr-backend.<env>.cdp-int.defra.cloud`.
- **Local development:** `compose.yml` provides MongoDB, Redis and a `floci` container.
  Note the service itself does not use Redis — it is inherited from the CDP template.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — lint, test and SonarQube scan on PR
  - `.github/workflows/publish.yml` — build and publish on push
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish
- **Testing:** `vitest` with `vitest-mongodb` and coverage; `npm run security-audit` runs
  `npm audit --audit-level=critical` in the pre-commit hook.

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, formatted with `@elastic/ecs-pino-format` in production.
  Request/response bodies and auth headers are redacted in production.
- **Tracing:** `@defra/hapi-tracing` propagating the header named in `TRACING_HEADER`; the
  location-service client forwards it to `aqie-location-backend`.
- **Metrics:** `@defra/cdp-metrics`.
- **Auditing:** `@defra/cdp-auditing`.
- **Shutdown:** `hapi-pulse` for graceful draining.
- **Locking:** `mongo-locks` is a dependency and its index is created, but no ingest job runs
  in-process, so nothing currently takes a lock.

## 11. Open Questions

- [ ] How is the annual PRTR dataset refreshed in production? Who runs `scripts/tsv-ingest`,
      against which Ricardo export, and on what cadence? Is a break-glass session the
      intended long-term mechanism or is an automated pipeline planned?
- [ ] Who places the `uk_prtr_dataset_<year>.xml` files into the S3 bucket, and what sets the
      `encodedfilename` object metadata the lookup relies on?
- [ ] `scripts/tsv-ingest/config.js` defaults `TSV_DIR` to an individual developer's local
      Windows path. Confirm this is only a convenience default and should be replaced.
- [ ] `src/config.js` carries a `TODO: replace this commented code before going to prod`
      against the `OSPlaceApiUrl` block, and `location-service.js` carries a
      `TODO: remove when going to PROD` against the `x-api-key` header. Confirm the intended
      production configuration before go-live.
- [ ] The pre-signed link fallback issues one `HeadObject` per bucket object. Confirm the
      expected bucket size, or whether the S3 key should always be present in MongoDB.
- [ ] Pre-signed URLs last 150 minutes. Confirm this is an accepted exposure window for
      published open data.
- [ ] Are pollutant reporting thresholds expected in a future Ricardo export? The record
      service returns `null` for every threshold today.
- [ ] `src/plugins/mongodb.js` still creates an `example-data` index and `src/data/example-reports.js`
      and `src/services/ExampleFind.js` remain from the CDP template. Confirm these can be removed.
- [ ] The catalogue edge `prtr-frontend__prtr-backend` understates the API surface — see the
      report in Section 6. Confirm the additional endpoints and update the catalogue.
