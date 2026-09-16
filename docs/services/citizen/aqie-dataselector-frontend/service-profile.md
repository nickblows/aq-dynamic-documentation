# aqie-dataselector-frontend

> The public "Get air pollution data" journey. Lets citizens, researchers and local authority
> officers select historic UK air quality measurements — by monitoring station or by building
> a custom dataset — and download them as files or have a download link emailed to them.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-dataselector-frontend`](https://github.com/DEFRA/aqie-dataselector-frontend) |
| Service domain | `Citizen` |
| Service type | `Auxilary Frontend` |
| Lifecycle stage | `Production` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22` (ES modules, Babel-compiled to `.server`) |
| Default branch | `main` |
| Created (UTC) | `2025-02-14` |
| Last main commit (UTC) | `2026-09-15T10:34:28Z` |
| Last analysed commit | `cf660ae0` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Runs two parallel selection journeys over historic air quality data:
  1. **By monitoring station** — search a place, disambiguate it, pick a nearby station,
     then download that station's measurements for a chosen pollutant, frequency and year.
  2. **Custom dataset** — pick pollutants, pick a data source network, pick locations
     (local authorities or countries), pick years, then request a bulk extract.
- Resolves free-text place names and finds nearby monitoring stations by calling
  `aqie-location-backend` and `aqie-monitoringstation-backend`.
- Fetches the selectable pollutant master list and the available data sources per pollutant
  from `aqie-historicaldata-backend`.
- Shows a live count of matching monitoring stations as the citizen narrows a custom dataset.
- Creates asynchronous extract jobs in `aqie-historicaldata-backend`, polls them to
  completion, and redirects the citizen to the resulting download URL.
- Offers an email alternative for large extracts: the citizen submits an email address, and
  a time-limited verification link later exchanges a job reference for a pre-signed
  download URL.
- Fetches the UK LAQM local authority list from the LAQM Portal to populate the
  local-authority picker, with a long in-process cache and graceful degradation.
- Provides a complete **no-JavaScript fallback journey** alongside the enhanced one.
- Serves the supporting static pages — about, privacy, accessibility, cookies — and a
  consent-gated Google Tag Manager integration.

**Does not:**

- Hold or generate the measurement data. Every extract is produced by
  `aqie-historicaldata-backend`; this service only orchestrates the selection and the wait.
- Serve current air quality, DAQI bands or forecasts — that is `aqie-front-end` over
  `aqie-back-end`.
- Plot stations on an interactive map — that is `aqie-maps-frontend`.
- Send the notification emails itself. It posts the citizen's request to
  `aqie-historicaldata-backend`, which owns delivery. It does not use
  `aqie-notify-service` or `aqie-alert-back-end-service`, which serve the air quality
  *alert subscription* journey, not data download.
- Hold the Ordnance Survey API key. Place-name lookup goes through `aqie-location-backend`,
  which owns that credential.
- Accept file uploads from citizens. The journey is read-only and unauthenticated (see the
  `cdp-uploader` finding in Section 5).

## 3. Architecture

**Pattern:** Hapi server-side rendered GOV.UK Frontend service using Nunjucks, with per-step
state kept in a `@hapi/yar` session backed by Redis. Each journey step is a folder under
`src/server/` containing `index.js` (route plugin), `controller.js` (handler) and one or
more `.njk` templates, registered centrally in `src/server/router.js`. Client-side
enhancement is bundled by Webpack from `src/client/`.

| Component | Path | Responsibility |
|---|---|---|
| Router | `src/server/router.js` | Registers all 29 route plugins plus static assets |
| Shared API client | `src/server/common/helpers/api-client.js` | `postJson` helper; `@hapi/wreck` with an `x-api-key` on localhost, `axios` everywhere else |
| Proxy-aware fetch | `src/server/common/helpers/catch-proxy-fetch-error.js` | CDP egress-proxy-aware fetch returning `[status, body]` |
| Station helpers | `src/server/common/helpers/station-helpers.js` | Builds hourly-data and exceedence requests; formats station coordinates as map links |
| Network helpers | `src/server/common/helpers/network-helpers.js` | Resolves non-AURN network identifiers for extract requests |
| Content packs | `src/server/data/en/` | Page copy separated from controllers |
| Session cache | `src/server/common/helpers/redis-client.js` | `catbox-redis` / `ioredis`, `catbox-memory` locally |
| Config | `src/config/config.js` | `convict` schema, ~55 settings |
| Client bundle | `src/client/javascripts/` | Accessible autocomplete, cookie banner, GTM loader |

**Environment-split endpoint configuration.** Nearly every upstream call has *two* config
entries: a deployed URL (for example `pollutantMasterApiUrl`) and a localhost development
URL pointing at `ephemeral-protected.api.dev.cdp-int.defra.cloud` (for example
`pollutantMasterDevUrl`). `config.get('isDevelopment')` selects between them, and the dev
branch adds an `x-api-key` from `OS_NAMES_DEV_API_KEYS`. This doubles the configuration
surface and is the main source of confusion when reading the code — the deployed path is
always the non-`Dev` key.

### Progressive enhancement and the no-JavaScript journey

This is a deliberate design decision, not an accident of history. The enhanced journey uses
client-side autocomplete, in-page pollutant and location pickers, and background polling of
extract job status. Every one of those steps has a server-rendered equivalent whose route or
template name ends in `nojs`:

| Enhanced step | No-JS equivalent |
|---|---|
| In-page pollutant picker | `GET`/`POST /airpollutant/nojs` |
| In-page local authority picker | `GET`/`POST /location-aurn/nojs` (template `index_nojs.njk`) |
| Custom dataset form submit | `GET`/`POST /download_dataselectornojs` |
| Station detail and year switching | `POST /stationDetailsNojs`, `GET /stationDetailsNojs/{id}`, `GET /stationDetailsNojs/year/{year}` |
| Station file download | `GET /stationdetails/download/{pollutant}/{frequency}` |
| Per-pollutant download | `GET /downloaddatanojs/{poll}/{freq}` |
| Extract job creation | `GET /download_aurn_nojs/{year}`, `GET /download_aurn_nojs/{year}/{dataSource}` |

The custom dataset page sets its form `action` to the `nojs` endpoint and swaps the picker
links to the `nojs` routes, so the page works with scripting disabled and the client script
upgrades it in place when available. A `<noscript>` block confirms the fallback behaviour
to the citizen. The practical consequence is that **a change to any selection step must be
made twice** — once in the enhanced controller and once in its `nojs` counterpart.

## 4. API Surface

73 routes are registered. They are grouped below by journey step rather than listed
individually. All are user-facing HTML unless noted.

### Entry and hub

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Service start page |
| `GET` | `/hubpage` | Chooses between the station journey and the custom dataset journey |
| `GET` | `/health` | Liveness probe (JSON) |

### Journey A — by monitoring station

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/search-location` | Enter a place name or postcode |
| `GET` | `/search-location/searchagain` | Re-enter the search |
| `GET`, `POST` | `/multiplelocations` | Disambiguate between matching places; also renders the "no location" and "no station" outcomes |
| `GET` | `/monitoring-station` | Nearby stations with the pollutants each measures |
| `GET`, `POST` | `/location` and `GET /location/{id}` | Select a specific location/station identifier |
| `GET`, `POST` | `/stationdetails` | Station detail page |
| `GET` | `/stationdetails/year/{year}` | Switch reporting year on the station page |
| `GET` | `/year` | Year selection for station pollution detail |
| `GET` | `/rendertable/{year}` | Exceedence table for a year |
| `GET` | `/downloaddata/{poll}/{freq}` | Download a station series by pollutant and frequency |
| `GET` | `/stationdetails/download/{download}/{pollutant}/{frequency}` | Station file download |
| `POST` | `/stationDetailsNojs` | No-JS station detail |
| `GET` | `/stationDetailsNojs/{id}`, `/stationDetailsNojs/year/{year}` | No-JS station detail and year switch |
| `GET` | `/stationdetails/download/{pollutant}/{frequency}` | No-JS station file download |
| `GET` | `/downloaddatanojs/{poll}/{freq}` | No-JS series download |

### Journey B — custom dataset

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/customdataset` | The dataset builder; shows current selections and a live station count |
| `GET` | `/customdataset/{pollutants}` | Builder pre-seeded with pollutants |
| `GET` | `/customdataset/year/{year}` | Builder with a year applied |
| `POST` | `/customdataset/location` | Apply a location selection to the builder |
| `GET` | `/customdataset/clear` | Reset the builder |
| `GET` | `/stationcount_ukeap` | Station count for the UKEAP network |

### Pollutant selection

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/airpollutant` | Pollutant picker |
| `POST` | `/addpollutants` | Apply pollutant selection |
| `GET`, `POST` | `/airpollutant/nojs` | No-JS pollutant picker |

### Data source selection

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/datasource` | Choose the monitoring network / data source |

### Location selection (custom dataset)

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/location-aurn` | Choose countries or local authorities |
| `GET`, `POST` | `/location-aurn/change` | Change an existing location selection |
| `GET`, `POST` | `/location-aurn/nojs` | No-JS location picker |

### Year selection

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/year-aurn` | Choose reporting years |
| `GET`, `POST` | `/year-aurn/change` | Change an existing year selection |

### Download and extract jobs

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/download_dataselector` | Confirm and submit the extract request |
| `GET`, `POST` | `/download_dataselectornojs` | No-JS equivalent |
| `GET` | `/download_aurn/{year}`, `/download_aurn/{year}/{dataSource}` | Create the extract job and wait for it |
| `GET` | `/download_aurn_nojs/{year}`, `/download_aurn_nojs/{year}/{dataSource}` | No-JS equivalents |
| `GET` | `/download_aurn/status/{jobID}`, `/download_aurn_status/{jobID}` | Job status pages |

### Email download request

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/emailrequest` | Submit an email address for a large extract |
| `GET`, `POST` | `/emailrequest/{dataSource}` | Data-source-specific variant |
| `GET`, `POST` | `/emailrequest/confirm` | Confirmation step |
| `GET` | `/download_emailreq/{id}/{timestamp}` | Exchange the emailed link for a pre-signed download URL |

### Static and support pages

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/about`, `/privacy`, `/accessibility` | Static content |
| `GET`, `POST` | `/cookies` | Cookie preferences; the only POST route with CSRF validation applied |
| `GET` | `/problem-with-service` | Error page |
| `GET` | `/assets/{param*}`, `/public/{param*}`, `/favicon.ico` | Static assets (MoJ Frontend assets, Webpack bundle) |
| `GET` | `/some-path` | Legacy route in `year_pollutiondetails` — see Section 11 |

### Extract job lifecycle

Job creation and completion are handled entirely server-side inside a single request:
`download_aurn/controller.js` posts the selection criteria to
`POST /AtomDataSelection`, receives a job identifier, then polls
`POST /AtomDataSelectionJobStatus` in a **one-second loop that continues until the job
status is `Completed`**, and finally redirects to the `resultUrl` the backend returns.
There is no iteration cap and no overall timeout on that loop — a job that never completes
holds the request open. Failures redirect to `/problem-with-service`.

The email path instead posts to `POST /AtomEmailJobDataSelection` to register the request.
When the citizen later follows the emailed link, `/download_emailreq/{id}/{timestamp}` posts
to `POST /AtomDataSelectionPresignedUrlMail` and normalises the response — which may be
either a bare URL string or an object carrying `resultUrl` — into a redirect.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-historicaldata-backend` | AQIE service | `GET /AtomDataSelectionPollutantMaster` | Master list of selectable pollutants | CDP internal network |
| `aqie-historicaldata-backend` | AQIE service | `POST /AtomDataSelectionPollutantDataSource` | Selected pollutants in; available data sources out | CDP internal network |
| `aqie-historicaldata-backend` | AQIE service | `POST /AtomDataSelection` | Selection criteria in; extract job identifier out. Also used for the live station count | CDP internal network |
| `aqie-historicaldata-backend` | AQIE service | `POST /AtomDataSelectionJobStatus` | Job reference in; status and `resultUrl` out | CDP internal network |
| `aqie-historicaldata-backend` | AQIE service | `POST /AtomEmailJobDataSelection` | Email address and job criteria in; request registration out | CDP internal network |
| `aqie-historicaldata-backend` | AQIE service | `POST /AtomDataSelectionPresignedUrlMail` | Job reference and timestamp in; pre-signed download URL out | CDP internal network |
| `aqie-historicaldata-backend` | AQIE service | `POST /AtomHistoryHourlydata` | Station, pollutant and frequency in; hourly series out | CDP internal network |
| `aqie-historicaldata-backend` | AQIE service | `POST /AtomHistoryexceedence` | Station and year in; exceedence statistics out | CDP internal network |
| `aqie-location-backend` | AQIE service | `POST /osnameplaces` | `{ userLocation }` in; OS Names matches out | CDP internal network |
| `aqie-monitoringstation-backend` | AQIE service | `POST /monitoringstation` | `{ userLocation, usermiles }` in; nearby stations with pollutants out | CDP internal network |
| **LAQM Portal** | **External API** | **`GET https://www.laqmportal.co.uk/xapi/getLocalAuthorities/json`** | **UK local authority list for the location picker** | **`X-API-Key` and `X-API-PartnerId` headers from `LAQMAPIKEY` and `LAQMAPIPARTNERID`** |
| Google Tag Manager | External (browser) | `gtm.js` / `ns.html` container load | Analytics, loaded only after the citizen accepts analytics cookies | Container ID from `GOOGLE_TAG_MANAGER_KEYS` |
| Redis | Datastore | `catbox-redis` / `ioredis` | Journey session state | `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_TLS` |

The LAQM Portal edge is **not recorded in the integration catalogue** — see Section 11.

### Verified NOT integrations

- **`cdp-uploader` — the catalogue edge `dataselector-frontend__cdp-uploader` is not real.**
  `src/config/config.js` defines `cdpUploaderUrl` (`CDP_UPLOADER_URL`) and
  `aws.s3BucketName` (`AWS_S3_BUCKET_NAME`), but no code anywhere in `src/` reads either
  key, and no template posts a file. There is no upload journey, no multipart route and no
  `@hapi/inert`-based upload handling. The supporting evidence is that the same commit range
  also left behind `backendApiUrl` ("document analysis (getS3 and summarize endpoints)"),
  `analysisTypeMapping` and unused `@langchain/core`, `@langchain/community`, `pdf2json`,
  `xlsx` and `@aws-sdk/client-s3` dependencies — all artefacts of the document-analysis
  proof of concept, copied in and never wired up. The edge should be removed from the
  catalogue, or reduced to a note that the configuration exists but is dead.
- **AWS S3 direct access.** `@aws-sdk/client-s3` and `@aws-sdk/credential-providers` are
  declared dependencies but are not imported anywhere in `src/`. The service only follows
  pre-signed HTTPS URLs handed to it by `aqie-historicaldata-backend`. The
  `integration-catalog.yaml` `datastores` entry listing `AWS S3` for this service is
  therefore misleading.
- **`aqie-back-end` / `aiqe-dataservice-backend`.** Two config entries default to
  `https://aiqe-dataservice-backend.dev.cdp-int.defra.cloud` (note the transposed letters).
  Neither is read by any code. `aqie-data-service-backend` is an archived repository.

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| Public internet (citizens) | All HTML routes above | Selection criteria in; measurement extracts and download links out |
| `aqie-dataselector-perf-frontend` (archived) | Public journey routes | Historic load testing |

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** none of its own. Redis holds the journey session (`@hapi/yar` over
  `catbox-redis`), falling back to in-memory locally. `REDIS_ENABLED` defaults to `false`,
  so Redis must be explicitly switched on per environment.
- **Session state held across the journey:** the raw and normalised search query, the
  selected location and its identifier, selected countries, selected local authorities and
  their LAQM identifiers, selected pollutants, selected data source, selected years,
  extract job references, and validation error summaries. The citizen's email address is
  held for the duration of the email-request step.
- **In-process cache:** the LAQM local authority list is cached in module scope with a TTL
  of twelve hours' worth of milliseconds. On upstream timeout, non-200 response or
  unexpected payload shape the controller falls back to the stale cached value, and if
  there is none it returns an empty list flagged `unavailable` so the page can degrade
  rather than fail. Because the cache is per-process, each ECS task warms it independently.
- **Retention:** session cache TTL and cookie TTL both default to four hours. Static asset
  caching defaults to one week. No measurement data is persisted by this service.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `PORT`, `NODE_ENV`, `ENVIRONMENT`, `SERVICE_VERSION` | Runtime identity; `ENVIRONMENT` is interpolated into every default upstream URL |
| `ASSET_PATH`, `STATIC_CACHE_TIMEOUT` | Static asset serving |
| `POLLUTANT_MASTER_API_URL`, `DATASOURCE_API_URL`, `STATION_COUNT_API_URL`, `Download_aurn_URL`, `Polling_URL`, `Email_URL`, `DOWNLOAD_EMAIL_URL`, `Download_URL`, `Table_URL` | `aqie-historicaldata-backend` endpoints (deployed) |
| `Osname api url`, `OS_NAMES_API_URL_1` | `aqie-location-backend` and `aqie-monitoringstation-backend` endpoints (deployed) |
| `POLLUTANT_MASTER_DEV_URL`, `DATASOURCE_DEV_URL`, `STATION_COUNT_DEV_URL`, `DOWNLOAD_AURN_DEV_URL`, `POLLING_DEV_URL`, `EMAIL_DEV_URL`, `DOWNLOAD_EMAIL_DEV_URL`, `DOWNLOAD_DEV_URL`, `TABLE_DEV_URL`, `OS_LOCATION_DEV_URL`, `OS_MONITORING_STATION_DEV_URL` | Localhost-only equivalents of the above |
| `OS_NAMES_DEV_API_KEYS` | Single `x-api-key` used for all localhost dev endpoints |
| `LAQMAPIKEY`, `LAQMAPIPARTNERID` | LAQM Portal credentials |
| `GOOGLE_TAG_MANAGER_KEYS` | Comma-separated GTM container IDs |
| `REDIS_ENABLED`, `REDIS_HOST`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_KEY_PREFIX`, `REDIS_TLS`, `USE_SINGLE_INSTANCE_CACHE` | Session cache backend |
| `SESSION_CACHE_ENGINE`, `SESSION_CACHE_NAME`, `SESSION_CACHE_TTL` | Catbox cache selection and lifetime |
| `SESSION_COOKIE_PASSWORD`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_TTL`, `COOKIE_PASSWORD` | Cookie signing and lifetime |
| `CDP_HTTP_PROXY`, `CDP_HTTPS_PROXY` | CDP egress proxy |
| `ENABLE_SECURE_CONTEXT` | TLS trust store |
| `ENABLE_METRICS`, `TRACING_HEADER` | Observability |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |
| `AQIE_PASSWORD`, `BACKEND_API_URL`, `ANALYSIS_TYPE_MAPPING`, `CDP_UPLOADER_URL`, `AWS_S3_BUCKET_NAME` | Declared but unused — see Section 5 and Section 11 |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` through a
  `development` stage to `defradigital/node`; entrypoint `node .`, exposing `PORT`.
- **Build:** Webpack bundles the client assets, Babel compiles `src/` to `.server/`.
- **Environments:** CDP `dev`, `test`, `perf-test`, `prod`.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — lint, test and SonarCloud scan on PR
  - `.github/workflows/build.yml` — build
  - `.github/workflows/publish.yml` — build and publish on push
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish
- **Testing:** `jest` with `jest-environment-jsdom`, `jest-fetch-mock` and `cheerio`.
  Note this repository still uses Jest while `aqie-prtr-backend` and `aqie-prtr-frontend`
  have moved to Vitest.

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, `@elastic/ecs-pino-format` in production, with
  `req.headers.authorization`, `req.headers.cookie` and `res.headers` redacted in
  production only.
- **Tracing:** `@defra/hapi-tracing` using `TRACING_HEADER` (`x-cdp-request-id`).
- **Metrics:** `aws-embedded-metrics` (CloudWatch EMF), gated by `ENABLE_METRICS`.
- **Shutdown:** `hapi-pulse`.
- **Error handling:** an `onPreResponse` extension plus a `catchAll` handler render the
  GOV.UK error pages; upstream failures are logged and surfaced as
  `/problem-with-service`.
- **Analytics:** Google Tag Manager is injected only after the citizen accepts analytics
  cookies, including the `<noscript>` iframe variant.

## 11. Open Questions

- [ ] **CSRF protection.** `@hapi/crumb` is registered, but its `skip` function returns true
      for every `POST` whose path is not `/cookies`. In effect, token validation is applied
      to the cookie preferences form only and to no other form in the journey. Confirm
      whether this is intentional and, if not, narrow the skip predicate.
- [ ] **Job polling has no bound.** The extract status loop in
      `src/server/download_aurn/controller.js` repeats every second until the status is
      `Completed`, with no maximum attempts and no wall-clock timeout. Confirm the intended
      behaviour for a stuck or failed job.
- [ ] **Hardcoded credential defaults in `src/config/config.js`.** The `aqiePassword`
      (`AQIE_PASSWORD`) setting has a real-looking literal default committed to the
      repository, and `cookiePassword`, `sessionCookiePassword` and
      `session.cookie.password` all default to a shared placeholder constant. Confirm these
      are always overridden in every deployed environment, and remove the literal defaults.
      The value itself is deliberately not recorded here.
- [ ] **Dead configuration and dependencies.** `cdpUploaderUrl`, `aws.s3BucketName`,
      `backendApiUrl` (twice, including one nested inside the `redis` block),
      `analysisTypeMapping` and `aqiePassword` are never read, and `@langchain/core`,
      `@langchain/community`, `pdf2json`, `xlsx`, `@aws-sdk/client-s3` and
      `@aws-sdk/credential-providers` are never imported. Confirm these can be removed —
      the unused AWS SDK and LangChain packages are an avoidable supply-chain surface.
- [ ] **`Osname api url` is used as an environment variable name.** The `OS_NAMES_API_URL`
      config entry declares its `env` as the literal string `Osname api url`, which contains
      spaces and cannot be set conventionally. Confirm whether the deployed default is
      relied upon.
- [ ] **Commented-out configuration.** `laqmAPIkey` and `laqmAPIPartnerId` each have a
      commented-out duplicate block immediately below the live one, with different defaults.
      Confirm which is intended. As committed, the defaults are the placeholder strings
      `LAQMAPIKEY` and `LAQMAPIPARTNERID`, so an unset environment yields a live but
      unauthenticated call.
- [ ] **`GET /some-path`** in `src/server/year_pollutiondetails/index.js` is an unnamed
      route with no obvious journey role. Confirm whether it is reachable and whether it can
      be removed.
- [ ] **Catalogue gap:** the LAQM Portal integration is missing from
      `integration-catalog.yaml` — see Section 5.
- [ ] **Catalogue error:** `dataselector-frontend__cdp-uploader` is not supported by the
      code and the `datastores` entry lists `AWS S3` for this service incorrectly — see
      Section 5.
- [ ] Confirm the operational owner and support contact for the LAQM Portal API, and the
      expected availability, given that the local authority picker degrades to an empty
      list when it is unreachable and the cache is cold.
