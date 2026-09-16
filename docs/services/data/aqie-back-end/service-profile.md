# aqie-back-end

> The core data API for the Air Quality estate. Ingests monitoring and forecast data from
> upstream providers on a schedule, normalises it into MongoDB, and serves it to citizen-facing
> services through a small read-only HTTP API.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-back-end`](https://github.com/DEFRA/aqie-back-end) |
| Service domain | `Data` |
| Service type | `Core Backend Service` |
| Lifecycle stage | `Production` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22.16.0` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2024-02-26` |
| Last main commit (UTC) | `2026-08-25T15:30:38Z` |
| Last analysed commit | `13996aea` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Ingests monitoring station metadata, pollutant metadata and pollutant measurements from the
  Ricardo UK-AIR API on independent cron schedules.
- Calculates DAQI (Daily Air Quality Index) bands from raw pollutant concentrations.
- Enriches monitoring stations with the owning local authority via reverse geocoding.
- Collects Met Office forecast files over SFTP and exposes them for retrieval.
- Serves the normalised dataset as a read-only HTTP API to citizen-facing services.

**Does not:**

- Render any user interface — presentation belongs to `aqie-front-end` and `aqie-maps-frontend`.
- Resolve citizen place-name searches — that is `aqie-location-backend`.
- Serve historic/archive extracts — that is `aqie-historicaldata-backend`.
- Own alert subscriptions or message delivery — those are `aqie-alert-back-end-service`
  and `aqie-notify-service`.

## 3. Architecture

**Pattern:** Hapi HTTP API co-located with `node-cron` scheduled ingest workers in a single
process. Ingest jobs take a distributed lock (`mongo-locks`) so only one container in the
ECS service performs a given ingest run.

| Component | Path | Responsibility |
|---|---|---|
| AURN ingest | `src/api/aurn/` | Fetches AURN measurements, calculates DAQI, populates MongoDB |
| Forecast | `src/api/forecast/` | Serves forecast data and populates the forecast collection |
| Met Office SFTP | `src/api/metOfficeForecast/` | Lists and reads forecast files from the Met Office SFTP drop |
| Location site | `src/api/locationsite/` | Station metadata, station dates, local authority enrichment |
| Pollutants | `src/api/pollutants/` | Pollutant metadata ingest and `/measurements` endpoint |
| Health | `src/api/health/` | Liveness endpoint for the platform |
| Config | `src/config/` | `convict` schema — all endpoints, schedules and credentials |
| Common helpers | `src/common/` | MongoDB connection, proxy handling, secure context, logging |

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/health` | Liveness probe | — | Status payload |
| `GET` | `/measurements` | Current pollutant concentrations keyed by `localSiteID` | Optional filters | Stations with per-pollutant values and DAQI bands |
| `GET` | `/monitoringStations` | Full monitoring station list | — | Station collection |
| `GET` | `/monitoringStationInfo` | Detail for stations, optionally including closed sites | `with-closed`, `with-pollutants`, `stream` | Station metadata and coordinates |
| `GET` | `/aurnData` | AURN network dataset | — | AURN measurement records |
| `GET` | `/forecasts` | Forecast data held by this service | — | Forecast records |
| `GET` | `/sftp/files` | List forecast files available on the Met Office drop | — | File listing |
| `GET` | `/sftp/file/{filename}` | Read a specific forecast file | `filename` | File contents |

> `/measurements` and `/monitoringStations` are **not** interchangeable. Only `/measurements`
> keys stations by the `localSiteID` that downstream consumers use to resolve
> feature-of-interest identifiers, which is why `aqie-demo-data-visualisations` sources its
> station list from `/measurements`.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| Ricardo UK-AIR API | External API | `POST /api/login_check` | Credentials exchanged for bearer token | `RICARDO_API_EMAIL` / `RICARDO_API_PASSWORD` |
| Ricardo UK-AIR API | External API | `GET /api/site_meta_datas` | Monitoring site metadata | Bearer token |
| Ricardo UK-AIR API | External API | `GET /api/pollutant_metadatas` | Pollutant definitions, units, thresholds | Bearer token |
| Ricardo UK-AIR API | External API | `GET /api/pollutant_measurement_datas` | Pollutant concentration time series | Bearer token |
| postcodes.io | External API | `GET /postcodes?lat&lon&radius` | Coordinates in; postcode and local authority out | None |
| Met Office | External (SFTP) | SFTP directory poll | Forecast data files | `SSH_PRIVATE_KEY` |
| GOV.UK Notify | External API | `NOTIFY_BASE_URL` | Notification dispatch | API key — see open question |
| MongoDB | Datastore | Driver connection | Persisted stations, pollutants, measurements, forecasts | `MONGO_URI` |

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| `aqie-front-end` | `GET /measurements`, `GET /monitoringStationInfo` | Concentrations, DAQI bands, station metadata for location pages |
| `aqie-maps-frontend` | `GET /monitoringStations`, `GET /monitoringStationInfo`, `GET /measurements`, `GET /aurnData` | Station plotting and map colouring |
| `aqie-monitoringstation-backend` | `GET /monitoringStationInfo`, `GET /measurements` | Station enrichment for nearby-station responses |
| `aqie-demo-data-visualisations` | `GET /measurements` | Station list keyed by `localSiteID` for demo charts |

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Store:** MongoDB (`MONGO_DATABASE`), with `mongo-locks` providing distributed ingest locking.
- **Key entities:** monitoring stations (metadata, coordinates, local authority, pollutants
  measured), pollutant metadata (units, thresholds, DAQI bands), pollutant measurements
  (time series keyed by station and pollutant), forecasts.
- **Refresh:** driven entirely by cron expressions — `AURN_SCHEDULE`,
  `POLLUTANTS_SCHEDULE`, `MONITORING_STATIONS_SCHEDULE`, `FORECAST_SCHEDULE`.
- **Caching:** in-process `lru-cache`; a cached stations index backs `/monitoringStations`.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `PORT`, `HOST` | HTTP listener |
| `NODE_ENV`, `ENVIRONMENT`, `SERVICE_VERSION` | Runtime identity |
| `MONGO_URI`, `MONGO_DATABASE` | MongoDB connection |
| `RICARDO_API_LOGIN_URL`, `RICARDO_API_ALL_DATA_URL`, `RICARDO_API_SITE_ID_URL`, `RICARDO_API_POLLUTANT_METADATA_URL` | Ricardo UK-AIR endpoints |
| `RICARDO_API_EMAIL`, `RICARDO_API_PASSWORD` | Ricardo credentials |
| `POSTCODES_API_URL` | Reverse geocoding endpoint |
| `POLLUTANTS_URL`, `POLLUTANTS_URL_EXTRA`, `FORECAST_URL` | Upstream data endpoints |
| `AURN_SCHEDULE`, `POLLUTANTS_SCHEDULE`, `MONITORING_STATIONS_SCHEDULE`, `FORECAST_SCHEDULE` | Cron expressions for ingest jobs |
| `SSH_PRIVATE_KEY` | Met Office SFTP authentication |
| `NOTIFY_BASE_URL` | GOV.UK Notify base URL |
| `ACCESS_CONTROL_ALLOW_ORIGIN_URL` | CORS origin |
| `HTTP_PROXY`, `HTTPS_PROXY`, `SQUID_USERNAME`, `SQUID_PASSWORD` | CDP egress proxy |
| `ENABLE_SECURE_CONTEXT`, `TRUSTSTORE_ONE` | TLS trust store |
| `ENABLE_METRICS`, `TRACING_HEADER` | Observability |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |
| `YAR_COOKIE_PASSWORD` | Session cookie signing |
| `MOCK_INVALID_POLLUTANTS` | Test affordance |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`;
  entrypoint `node src`.
- **Internal address:** `https://aqie-back-end.<env>.cdp-int.defra.cloud`.
- **Environments:** `dev`, `test`, `perf-test`, `prod`.
- **Local development:** `compose.yml` provides MongoDB, Redis and LocalStack.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — lint, test, SonarQube on PR
  - `.github/workflows/publish.yml` — build and publish on push to `main`
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish
  - `.github/workflows/template.yml`, `validate-template.yml` — CDP template sync

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, formatted with `@elastic/ecs-pino-format` for ECS ingestion.
- **Tracing:** `@defra/hapi-tracing` propagating the header named in `TRACING_HEADER`.
- **Metrics:** `aws-embedded-metrics` (CloudWatch EMF), gated by `ENABLE_METRICS`.
- **Shutdown:** `hapi-pulse` for graceful draining.

## 11. Open Questions

- [ ] Does this service still send notifications directly via GOV.UK Notify, or is
      `NOTIFY_BASE_URL` vestigial now that `aqie-notify-service` exists? (catalogue `oq-001`)
- [ ] The Ricardo endpoint defaults reference `uk-air-api.staging.rcdo.co.uk` while
      `aqie-alert-back-end-service` defaults to `api-ukair.defra.gov.uk`. Confirm which is
      authoritative for production.
- [ ] Is `aqie-historicaldata-backend` fed from this service's MongoDB or independently
      from Ricardo? (catalogue `oq-002`)
- [ ] Confirm data retention policy for the measurements collection.
