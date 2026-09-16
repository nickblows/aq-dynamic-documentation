# aqie-forecast-api

> Collects the Met Office air quality forecast files from the DEFRA SFTP drop once a day,
> parses them into MongoDB, and serves the resulting five-day forecast and written summary
> to citizen-facing services through a single read-only endpoint.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-forecast-api`](https://github.com/DEFRA/aqie-forecast-api) |
| Service domain | `Data` |
| Service type | `Auxilary Backend Service` |
| Lifecycle stage | `Production` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2025-05-15` |
| Last main commit (UTC) | `2026-06-08T17:08:07Z` |
| Last analysed commit | `cdaaf94d` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Monitoring` |

## 2. Purpose and Responsibilities

**Does:**

- Runs a single daily scheduled job that connects to the DEFRA-hosted SFTP drop where the
  Met Office deposits air quality forecast files.
- Retrieves two files per day: the site-level forecast XML (`MetOfficeDefraAQSites_<YYYYMMDD>.xml`)
  and the written forecast summary text file (`EMARC_AirQualityForecast_<YYYY-MM-DD>-*.txt`).
- Parses the forecast XML into one document per forecast site, holding the site name, the
  issue timestamp, a GeoJSON point and up to five days of DAQI values.
- Parses the summary text file and keeps only the single most recent summary, rejecting any
  file whose issue date is not today.
- Serves both datasets together from `GET /forecast` for front-end and alerting consumers.

**Does not:**

- Ingest or serve measured pollutant concentrations or monitoring station metadata — that is
  `aqie-back-end`.
- Calculate or band DAQI itself. The DAQI values are taken as issued by the Met Office; DAQI
  derived from measurements is calculated in `aqie-back-end`.
- Decide when a forecast is bad enough to notify a citizen. Alert thresholds and dispatch
  belong to `aqie-alert-back-end-service` and `aqie-notify-service`.
- Render anything. Presentation is `aqie-front-end` and `aqie-maps-frontend`.
- Serve historic or archived forecast series — only the current forecast set is retained.

## 3. Architecture

**Pattern:** Hapi HTTP API with a `node-cron` scheduled SFTP ingest job registered as a Hapi
plugin in the same process. The job takes a `mongo-locks` distributed lock before running so
only one container in the ECS service performs a given ingest.

| Component | Path | Responsibility |
|---|---|---|
| Forecast route | `src/forecast/index.js` | Registers `GET /forecast` |
| Forecast controller | `src/forecast/forecastController.js` | Reads both collections and returns the combined payload |
| Scheduler plugin | `src/forecast/batch-scheduler/seed-forecasts.js` | Registers the cron job and stops it on server shutdown |
| Sync job | `src/forecast/batch-scheduler/runForecastSyncJob.js` | Locking, collection/index setup, idempotency check, invokes polling |
| Polling loop | `src/forecast/helpers/pollUntilFound.js` | Connect, look for files, parse, upsert, sleep, retry, escalate, give up |
| SFTP transport | `src/forecast/helpers/connectSftpViaProxy.js` | Opens an SSH tunnel through the CDP `CONNECT` proxy |
| Parsers | `src/forecast/helpers/parse-forecast-xml.js`, `parse-forecast-summary-txt.js` | XML and text file parsing |
| Filename rules | `src/forecast/helpers/utility.js` | Derives today's expected file names |
| Config | `src/config.js` | `convict` schema for all settings |
| Common helpers | `src/common/helpers/` | MongoDB, logging, metrics, tracing, secure context, proxy |

### Polling and retry model

This is the part of the service most worth understanding, because the Met Office upload time
is not guaranteed.

1. The cron expression in `FORECAST_SCHEDULE` fires (default `00 04 * * *` — 04:00 daily).
2. The job acquires the Mongo lock. If it cannot, it logs and exits without doing work.
3. It derives today's two expected filenames from the current date.
4. It checks MongoDB for documents already updated within today's UTC window. **If both the
   forecast and the summary already exist for today, the job exits immediately** — the run is
   idempotent and re-running it costs nothing.
5. Otherwise it enters the polling loop. Each pass opens an SFTP connection, lists the
   directory named in `MET_OFFICE_DIRECTORY`, and looks for each still-missing file.
   The forecast file is matched on an exact name; the summary file is matched on a name prefix
   plus a `.txt` extension, because the Met Office appends a run identifier.
6. Anything found is downloaded and parsed. Forecast sites are written with a bulk
   `replaceOne` upsert keyed on site name. The summary is upserted as a single `latest`
   document, but is rejected if its parsed issue date is not today.
7. The connection is closed and, if anything is still missing, the loop sleeps for
   `FORECAST_RETRY_INTERVAL` milliseconds (default 900000 — 15 minutes) and repeats.
8. **Escalation:** if files are still missing at 10:00 and again at 15:00 Europe/London, the
   job logs an `error`-level alert naming the specific missing files. These log lines are the
   operational signal that the Met Office has not delivered.
9. **Give up:** polling stops at 23:30 Europe/London. The next day's cron run starts afresh.
10. SFTP connection failures are treated the same as a missing file — logged, then retried
    after the same interval, rather than failing the run.

A parse failure is treated differently from a missing file: it is raised, which aborts the
run and releases the lock, because a corrupt file will not fix itself by waiting.

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/health` | Liveness probe | — | Status payload |
| `GET` | `/forecast` | Current Met Office forecast and written summary | — | `message`, `forecasts` (array of sites with name, issue timestamp, GeoJSON point and up to five daily DAQI values), `forecast-summary` (latest written summary) |

`/forecast` sets `Access-Control-Allow-Origin` from `ACCESS_CONTROL_ALLOW_ORIGIN_URL`.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| Met Office (via DEFRA SFTP drop) | External (SFTP) | Directory listing and file read under `MET_OFFICE_DIRECTORY`, tunnelled through the CDP proxy | Daily forecast XML and forecast summary text files | SSH private key (`SSH_PRIVATE_KEY`, base64-encoded) |
| MongoDB | Datastore | Driver connection | Forecast site documents and the latest summary document | `MONGO_URI` |

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| `aqie-front-end` | `GET /forecast` | Five-day DAQI forecast and written summary for location pages |
| `aqie-maps-frontend` | `GET /forecast` | Forecast values overlaid on the map |
| `aqie-alert-back-end-service` | `GET /forecast` | Forecast DAQI values compared against the alert threshold by the forecast alert scheduler — **not yet in the integration catalogue, see Section 11** |

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Store:** MongoDB (`MONGO_DATABASE`, defaulting to `aqie-forecast-api`), with `mongo-locks`
  providing distributed ingest locking.
- **Collections:**
  - `forecasts` — one document per Met Office forecast site. Unique index on `name`. Holds the
    site name, the issue timestamp derived from the file's year/month/day/hour attributes, a
    GeoJSON `Point`, and an array of up to five `{ day, value }` DAQI entries.
  - `forecast-summary` — a single document with `type: 'latest'`, holding the parsed written
    summary, the source filename and an `updated` timestamp.
- **Refresh:** once per day on `FORECAST_SCHEDULE`, with in-day retries on
  `FORECAST_RETRY_INTERVAL`.
- **Retention:** neither collection accumulates history. Forecast documents are replaced in
  place per site and the summary is replaced wholesale, so the service always holds exactly
  one current forecast set.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `PORT`, `HOST` | HTTP listener |
| `NODE_ENV`, `ENVIRONMENT`, `SERVICE_VERSION` | Runtime identity and CDP environment |
| `MONGO_URI`, `MONGO_DATABASE` | MongoDB connection |
| `FORECAST_SCHEDULE` | Cron expression for the daily ingest job |
| `FORECAST_RETRY_INTERVAL` | Milliseconds to wait between polling attempts |
| `MET_OFFICE_DIRECTORY` | Remote SFTP directory to list |
| `SSH_PRIVATE_KEY` | SFTP authentication key, supplied base64-encoded |
| `HTTP_PROXY` | CDP egress proxy used to tunnel the SFTP connection |
| `ACCESS_CONTROL_ALLOW_ORIGIN_URL` | CORS origin |
| `ENABLE_SECURE_CONTEXT`, `TRUSTSTORE_ONE` | TLS trust store |
| `ENABLE_METRICS`, `TRACING_HEADER` | Observability |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |

`config.validate({ allowed: 'strict' })` is applied, so an unrecognised key fails startup.

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`;
  entrypoint `node src`.
- **Internal address:** `https://aqie-forecast-api.<env>.cdp-int.defra.cloud`.
- **Environments:** the config enumerates `local`, `infra-dev`, `management`, `dev`, `test`,
  `perf-test`, `ext-test`, `prod`.
- **Egress:** all outbound traffic, including the SFTP session, is forced through the CDP
  proxy. The SFTP connection is established by issuing an HTTP `CONNECT` to the proxy and
  handing the resulting socket to the SSH client.
- **Local development:** `compose.yml` provides MongoDB, Redis and LocalStack.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — lint, test and SonarQube scan on PR
  - `.github/workflows/publish.yml` — build and publish on push
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, formatted with `@elastic/ecs-pino-format` in production.
  The ingest job is verbose by design — the "file not uploaded" alerts at 10:00 and 15:00 are
  emitted at `error` level so they can be alerted on.
- **Tracing:** `@defra/hapi-tracing` propagating the header named in `TRACING_HEADER`.
- **Metrics:** `aws-embedded-metrics` (CloudWatch EMF), gated by `ENABLE_METRICS`.
- **Shutdown:** `hapi-pulse` for graceful draining; the cron job is stopped on `onPostStop`.

## 11. Open Questions

- [ ] `aqie-alert-back-end-service` calls `GET /forecast` via its `FORECAST_API_URL` setting.
      This edge is evidenced in code but is **missing from the integration catalogue** and
      should be added.
- [ ] The SFTP host and the SFTP username are hardcoded constants in the source rather than
      configuration. Confirm with the owner whether this is intentional and whether the
      account should be moved into CDP configuration.
- [ ] Confirm whether the 23:30 Europe/London polling cut-off is the agreed operational
      behaviour, and what the manual recovery process is when the Met Office delivers late.
- [ ] Redis appears in `compose.yml` but is not used by the application. Confirm it can be
      removed from the local environment.
- [ ] Confirm the agreed alerting route for the 10:00 and 15:00 missing-file log lines — are
      they wired to a monitor, or checked manually?
