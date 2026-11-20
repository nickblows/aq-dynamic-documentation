# aqie-back-end

> The core data API for the Air Quality estate. Serves monitoring station metadata, per-station
> DAQI and live pollutant readings (current, and the last 24 hours or 7 days) to citizen-facing
> services. Station and DAQI data is cached in MongoDB on cron schedules; current readings and
> station history are read live from the Ricardo UK-AIR API.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-back-end`](https://github.com/DEFRA/aqie-back-end) |
| Service domain | `Data` |
| Service type | `Core Backend Service` |
| Lifecycle stage | `Production` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22.16.0` (ES modules; `.nvmrc` and parent image pinned to 22.16.0) |
| Default branch | `main` |
| Created (UTC) | `2024-02-26` |
| Last main commit (UTC) | `2026-11-16T14:41:25Z` |
| Last analysed commit | `77a030c3` |
| Last analysed (UTC) | `2026-11-19T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Refreshes the monitoring station cache from the Ricardo UK-AIR API every 6 hours and at
  start-up. Open and close dates and current pollutant coverage come from Ricardo pollutant
  metadata, and each station is enriched with its local authority by reverse geocoding.
- Calculates a DAQI (Daily Air Quality Index) per station every 30 minutes from Ricardo hourly
  and 15-minute readings, applying a 75% data-capture rule, and stores it for the map layer.
- Reads Ricardo live on request: current readings for stations near a point
  (`/monitoringStationInfo`), and an hourly history for one station over 24 hours or 7 days
  with averages, data capture, exceedances and DAQI (`/monitoringStationHistory`).
- Reads Met Office forecast files from a DEFRA SFTP share on request.
- Still runs two ingest jobs whose output nothing reads since the `/measurements` and
  `/forecasts` endpoints were removed: an hourly sweep of the public UK-AIR site listing and
  observation service, and a fetch of the UK-AIR forecast RSS feed.

**Does not:**

- Render any user interface — presentation belongs to `aqie-front-end` and `aqie-maps-frontend`.
- Resolve citizen place-name searches — that is `aqie-location-backend`.
- Serve long-range historic/archive extracts — that is `aqie-historicaldata-backend`. It serves
  only the last 24 hours or 7 days of hourly readings for one station.
- Own alert subscriptions or message delivery — those are `aqie-alert-back-end-service`
  and `aqie-notify-service`. It makes no call to GOV.UK Notify.

## 3. Architecture

**Pattern:** Hapi HTTP API co-located with `node-cron` scheduled jobs in a single process. Each
job takes a lock (an insert into a `locks` collection with a one-hour expiry) so only one
container in the ECS service performs a given run.

| Component | Path | Responsibility |
|---|---|---|
| AURN DAQI job | `src/api/aurn/` | Every 30 minutes: reads current stations from `monitoringStations`, fetches yesterday's and today's readings per station from Ricardo (five stations at a time), calculates the DAQI and writes `aurnMeasurements`. Serves `/aurnData` |
| Averaging rules | `src/common/helpers/averaging.js` | One implementation of the 75% data-capture and averaging rules, shared by the DAQI job and the history summary |
| Location site | `src/api/locationsite/` | `/monitoringStationInfo` (live, uncached), `/monitoringStations` (MongoDB cache), `/monitoringStationHistory` (live, cached for 15 minutes); the station refresh job; Ricardo token helpers; local authority lookup |
| UK-AIR SOS ingest | `src/api/pollutants/` | Hourly sweep of 16 UK-AIR regions into `measurements` and `historicalMeasurements`. **Ingest only — the `/measurements` read endpoint was removed by [PR #163](https://github.com/DEFRA/aqie-back-end/pull/163).** Its `helpers/common/` folder also holds constants and a freshness check that 12 other modules import, so it must stay or move before the job is retired |
| Forecast ingest | `src/api/forecast/` | UK-AIR forecast RSS into `forecasts` and `historicalForecasts`. **Ingest only — the `/forecasts` read endpoint was removed by [PR #163](https://github.com/DEFRA/aqie-back-end/pull/163)** |
| Met Office SFTP | `src/api/metOfficeForecast/` | `/sftp/files` and `/sftp/file/{filename}`, read through an HTTP CONNECT tunnel on the CDP proxy. Two further connection helpers in the folder are never imported |
| Health | `src/api/health/` | Liveness endpoint for the platform |
| Config | `src/config/` | `convict` schema — all endpoints, schedules and credentials. Several keys are declared but never read (section 8) |
| Shared helpers | `src/helpers/`, `src/common/helpers/` | Two parallel helper trees. In use: Mongo plugin, locks, logging, proxy fetch and secure context (`src/helpers/`); proxy set-up, graceful shutdown and averaging (`src/common/helpers/`). Never imported: request tracing, metrics, a second Mongo plugin and `start-server.js` |

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/health` | Liveness probe | — | `{ message }` |
| `GET` | `/monitoringStationInfo` | **Primary data endpoint for the citizen journey.** Current pollutant concentrations per station, read live from Ricardo on every request (one station list call, then five calls per station, one station at a time). No cache | `latitude`, `longitude`, `distance`, `page`, `networks[]`, `with-closed`, `with-pollutants`, `start-date`, `stream`, `totalItems` | `{ message, measurements }`: stations with per-pollutant value, unit and time. `stream=data` returns the raw Ricardo payload instead |
| `GET` | `/monitoringStations` | Full monitoring station list, served from a MongoDB cache refreshed every 6 hours and at start-up. No Ricardo call per request | — | `{ message, stations }` |
| `GET` | `/monitoringStationHistory` | Hourly series for PM2.5, PM10, NO2, O3 and SO2 at one station, SO2 15-minute means, and a summary of averages, data capture, exceedances and DAQI. Read live from Ricardo (five calls per request) and cached in process for 15 minutes per station and period | `siteId` (required, Ricardo form such as `UKA00315`; the short local code is rejected), `period` (`24h`, the default, or `7d`) | Window bounds, series and summary. `400` for a bad `siteId` or `period`, `502` if Ricardo cannot be reached or refuses |
| `GET` | `/aurnData` | Per-station observed DAQI index calculated every 30 minutes from AURN readings | — | `{ message, measurements }`: one record per station with `localSiteID`, `daqiIndex`, `measuredAt`, `updatedAt` and the concentration behind each pollutant's index |
| `GET` | `/sftp/files` | List forecast files on the DEFRA SFTP share | — | `{ success, files }` |
| `GET` | `/sftp/file/{filename}` | Read a specific forecast file | `filename` | XML; `404` if the file is not in the listing |

No route is authenticated; access relies on the CDP internal network.

> **Decommissioned.** `GET /measurements` and `GET /forecasts` were removed by
> [PR #163](https://github.com/DEFRA/aqie-back-end/pull/163) (merged 2026-09-23) after CDP logs
> showed no production traffic on either. **The scheduled ingest for both still runs**:
> `measurements` and `forecasts` are still rewritten, and `historicalMeasurements` and
> `historicalForecasts` still grow, with no reader. See
> [`/docs/master/measurements-data-flow.md`](../../../master/measurements-data-flow.md).
>
> `/monitoringStationInfo` is the replacement for `/measurements`. It is not a drop-in
> equivalent: it is fed by Ricardo rather than the UK-AIR SOS service, it performs no
> caching, and it does not publish the feature-of-interest mapping. See
> [`/docs/master/monitoring-station-info-data-flow.md`](../../../master/monitoring-station-info-data-flow.md).

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| Ricardo UK-AIR API | External API | `POST /api/login_check` | Credentials exchanged for a bearer token, once per scheduled job run and per request when the caller's session holds none | `RICARDO_API_EMAIL` / `RICARDO_API_PASSWORD` |
| Ricardo UK-AIR API | External API | `GET /api/site_meta_datas` | Monitoring site metadata: all sites including closed for the cache; allow-listed filters for `/monitoringStationInfo` | Bearer token |
| Ricardo UK-AIR API | External API | `GET /api/pollutant_metadatas` | Paged per-station pollutant instrument records, used for open and close dates and current pollutant coverage | Bearer token |
| Ricardo UK-AIR API | External API | `GET /api/pollutant_measurement_datas` | Hourly and 15-minute pollutant readings per station, for the DAQI job, `/monitoringStationInfo` and `/monitoringStationHistory` | Bearer token |
| DEFRA UK-AIR site listing and SOS | External API | `GET /data/API/site-process-featureofinterest-by-region`, then `GET /sos-ukair/service` (`GetObservation`) | Hourly sweep of 16 regions: sites with feature-of-interest ids, then one observation request per pollutant per site. Output has no reader | None (public) |
| DEFRA UK-AIR forecast feed | External API | `GET /assets/rss/forecast.xml` | Forecast RSS parsed into forecast documents. Output has no reader | None (public) |
| postcodes.io | External API | `GET /postcodes?lon&lat&radius&wideSearch` | Coordinates in; local authority out. Called through the CDP egress proxy | None |
| Met Office forecast files (DEFRA SFTP share) | External (SFTP) | SFTP over an HTTP CONNECT tunnel on the CDP proxy | Directory listing and file read, on request. Host, account name and directory are fixed in code | `SSH_PRIVATE_KEY` |
| MongoDB | Datastore | Driver connection | Stations, DAQI, measurements, forecasts and locks (section 7) | `MONGO_URI` |

> The `NOTIFY_BASE_URL` setting is read nowhere and there is no GOV.UK Notify client, so the
> service does not call Notify (catalogue `oq-001`, now answered).

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| `aqie-front-end` | `GET /monitoringStationInfo` | Live pollutant concentrations and station metadata for location pages |
| `aqie-maps-frontend` | `GET /monitoringStations`, `GET /aurnData` (and `GET /monitoringStationInfo`, only through a proxy route that nothing in that repository calls) | Station plotting and the station list, and the observed DAQI that colours the markers |
| `aqie-maps-prototype` | `GET /monitoringStations`, `GET /monitoringStationInfo`, `GET /health` | Prototype map data and connectivity probe |
| `aqie-monitoringstation-backend` | `GET /monitoringStationInfo?with-closed=true&with-pollutants=1&stream=data` | Full station metadata including closed sites, for nearby-station responses |
| `aqie-dataselector-frontend` | `GET /monitoringStationHistory` | Hourly series and summary figures for the last 24 hours and last 7 days of one station |

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml),
> including the removed `/measurements` and `/forecasts` call sites still present in some
> consumers (`decommissioned_edges`).

## 7. Data

- **Store:** MongoDB (`MONGO_DATABASE`), read preference `secondary`, write retries off.
  Collections:
  - `monitoringStations` — station cache: name, area, local authority, `localSiteID`, area type,
    location, status, open and close dates, current pollutants. Upserted by `name` every 6 hours;
    at start-up it is replaced wholesale if Ricardo returns stations (this start-up run takes no
    lock). Read by `/monitoringStations` and by the DAQI job.
  - `aurnMeasurements` — one document per station: `localSiteID`, `daqiIndex`, `measuredAt`,
    `updatedAt` and the concentration behind each pollutant index. Upserted by `localSiteID` every
    30 minutes. A station with no calculable index is skipped and keeps its previous document.
    Read by `/aurnData`.
  - `measurements`, `historicalMeasurements` — latest reading per pollutant per station from
    the UK-AIR SOS sweep (upserted by `name`), and an insert-only copy of every hourly sweep.
    **Nothing reads either.**
  - `forecasts`, `historicalForecasts` — latest UK-AIR forecast per location (upserted by
    `name`), and an insert-only copy of every run. **Nothing reads either.**
  - `locks` — one document per running job, with a one-hour expiry index.
- **Key entities:** monitoring stations, per-station DAQI with the concentrations behind it,
  SOS measurement snapshots (value, reading time and feature-of-interest id per pollutant),
  forecasts (location and a short per-day series).
- **Refresh:** cron expressions with these defaults — `AURN_SCHEDULE` every 30 minutes,
  `POLLUTANTS_SCHEDULE` hourly, `MONITORING_STATIONS_SCHEDULE` every 6 hours,
  `FORECAST_SCHEDULE` hourly from 05:00 to 10:00. The station refresh and the forecast fetch
  also run once after the server starts listening. The pollutant and DAQI jobs have no start-up run.
- **Locking:** a job inserts a document with its name as `_id` into `locks` and skips the run if
  that fails. The one-hour expiry means a lock left by a crashed container clears within about
  an hour. The `mongo-locks` package is initialised but never used.
- **Caching:** an in-process `lru-cache` holds `/monitoringStationHistory` responses (500
  entries, 15 minutes). `/monitoringStations` and `/aurnData` read MongoDB; `/monitoringStationInfo`
  is uncached. The Ricardo bearer token is kept in the caller's `yar` session.
- **Retention:** the two `historical*` collections grow without limit (no expiry, no pruning).
  Everything else is replaced in place.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `PORT`, `HOST` | HTTP listener |
| `NODE_ENV`, `SERVICE_VERSION` | Runtime identity. `NODE_ENV=production` also switches on the secure context and ECS-format logs |
| `MONGO_URI`, `MONGO_DATABASE` | MongoDB connection |
| `RICARDO_API_LOGIN_URL`, `RICARDO_API_ALL_DATA_URL`, `RICARDO_API_SITE_ID_URL`, `RICARDO_API_POLLUTANT_METADATA_URL` | Ricardo UK-AIR endpoints. The code defaults point at the supplier's staging host and `.env.example` documents the production host. Production sets all four in the service-wide defaults and overrides none per environment, per CDP environment configuration (catalogue `oq-012`) |
| `RICARDO_API_EMAIL`, `RICARDO_API_PASSWORD` | Ricardo credentials |
| `POSTCODES_API_URL` | Reverse geocoding endpoint |
| `POLLUTANTS_URL`, `POLLUTANTS_URL_EXTRA` | UK-AIR site listing and SOS observation endpoints |
| `FORECAST_URL` | UK-AIR forecast RSS feed |
| `AURN_SCHEDULE`, `POLLUTANTS_SCHEDULE`, `MONITORING_STATIONS_SCHEDULE`, `FORECAST_SCHEDULE` | Cron expressions for the four jobs (defaults in section 7) |
| `SSH_PRIVATE_KEY` | SFTP authentication |
| `ACCESS_CONTROL_ALLOW_ORIGIN_URL` | Origin written to the `Access-Control-Allow-Origin` header on `/aurnData` and the two SFTP routes |
| `HTTP_PROXY`, `HTTPS_PROXY` | CDP egress proxy for outbound calls and the SFTP tunnel |
| `TRUSTSTORE_*` (any variable with this prefix) | Extra CA certificates, loaded in production |
| `LOG_LEVEL` | Level for the main logger |
| `LOG_ENABLED`, `LOG_FORMAT` | Read only by a secondary logger used by the proxy helper and the shutdown hook |
| `YAR_COOKIE_PASSWORD` | Session cookie encryption (read directly from the environment); a random per-process value is used if unset |
| `MOCK_INVALID_POLLUTANTS` | Test affordance: replaces about 90% of `/monitoringStationInfo` values with invalid sentinels |
| `ENVIRONMENT`, `NOTIFY_BASE_URL`, `SQUID_USERNAME`, `SQUID_PASSWORD`, `ENABLE_SECURE_CONTEXT`, `ENABLE_METRICS`, `TRACING_HEADER` | Declared in the schema but read by no running code (dead configuration) |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`
  (parent image 2.8.5 for Node 22.16.0); the production stage installs production dependencies
  only, adds `curl` for the platform health check, and runs `node src`.
- **Internal address:** `https://aqie-back-end.<env>.cdp-int.defra.cloud`.
- **Environments:** `dev`, `test`, `perf-test`, `prod`.
- **Start-up and shutdown:** the first station refresh and forecast fetch run after the server
  is listening, so `/health` answers while they run. `SIGTERM` and `SIGINT` stop the server
  gracefully (10 second timeout).
- **Local development:** `compose.yml` provides MongoDB, Redis (not used by the service code) and
  the service itself on port 3001.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — on pull request: dependency review (fails on
    high severity), format check, lint, tests, Docker build and SonarCloud scan
  - `.github/workflows/publish.yml` — build and publish through the CDP build action on push to
    `main`, then tests and SonarCloud
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish
  - `.github/workflows/template.yml`, `validate-template.yml` — CDP template: applies the
    template on a fork's first run (skipped for this repository) and, on pull request, checks that
    a production-like container starts, answers `/health` and logs valid JSON

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, in ECS format (`@elastic/ecs-pino-format`) when
  `NODE_ENV=production` and `pino-pretty` otherwise. Authorization and cookie request headers
  and response headers are removed from request logs.
- **Tracing:** none active. `@defra/hapi-tracing` is a dependency and a tracing plugin is
  defined in `src/common/helpers/request-tracing.js`, but it is never registered, so
  `TRACING_HEADER` has no effect.
- **Metrics:** none emitted. The CloudWatch embedded-metrics helper in
  `src/common/helpers/metrics.js` is never called.
- **Shutdown:** `hapi-pulse`, registered first, stops the server on `SIGTERM` or `SIGINT` and
  logs when shutdown starts and finishes.

## 11. Open Questions

- [ ] Should the Ricardo URL defaults in code be removed so that a missing variable fails fast?
      They are the supplier's staging host (`uk-air-api.staging.rcdo.co.uk`); `.env.example`
      documents `api-ukair.defra.gov.uk`. The platform configuration sets all four in the
      service-wide defaults, so production does not rely on the code defaults, per CDP
      environment configuration, and catalogue `oq-012` is answered for this service. A secret
      of the same name would override the configuration without showing in it.
- [ ] (catalogue `oq-029`) The README says Ricardo ignores the `start-date-time` and `end-date-time` parameters and
      returns the latest measurement instead. The DAQI job and `/monitoringStationInfo` send
      exactly those parameters. If the README is right, the 75% data-capture rule can never be met
      for PM2.5, PM10 and O3 on the map. Which is true?
- [ ] (catalogue `oq-030`) A station that stops meeting the data-capture rule keeps its old `aurnMeasurements`
      document, so `/aurnData` serves an old DAQI with only `updatedAt` as a signal. Is that
      intended, and do consumers check it?
- [ ] Should the pollutants and forecast jobs, and the four collections they fill, be retired now
      that nothing reads them? `historicalMeasurements` and `historicalForecasts` have no
      retention. (catalogue `oq-019`)
- [ ] Does anything call `/sftp/files` or `/sftp/file/{filename}`? They are unauthenticated and no
      consumer is recorded. Who operates the SFTP share and account?
- [ ] (catalogue `oq-031`) Has Ricardo agreed the request-time load (1 + 5N calls per `/monitoringStationInfo`
      request, five per uncached `/monitoringStationHistory` request)?
- [ ] The UK-AIR SOS job aborts the whole run on one failed request, and later sites in a chunk
      appear to receive the first site's readings. Confirm before anyone relies on `measurements`.
- [ ] Can the unused configuration keys, the unwired tracing, metrics and second Mongo plugin,
      and the dependencies that nothing imports be removed?
