# aqie-alert-back-end-service

> The system of record for citizen air quality alert subscriptions. Holds the subscriber list,
> polls Ricardo UK-AIR and the AQIE forecast API for breaches, decides who should be told, and
> hands each message to `aqie-notify-service` for delivery.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-alert-back-end-service`](https://github.com/DEFRA/aqie-alert-back-end-service) |
| Service domain | `Data` |
| Service type | `Auxilary Backend Service` |
| Lifecycle stage | `Production` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22.16.0` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2025-12-09` |
| Last main commit (UTC) | `2026-08-10T09:25:53Z` |
| Last analysed commit | `e6ff1414` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Owns the subscriber record. The `USERS` collection holds one document per citizen contact
  (mobile number or email address) with up to five subscribed locations, the alert channel
  (`sms` or `email`) and the preferred language (`en` or `cy`).
- Creates subscriptions on `POST /setup-alert` and removes them on
  `DELETE /opt-out-sms-alert` and `DELETE /opt-out-email-alert`.
- Runs three independent schedulers that decide when an alert is warranted:
  a pollutant (AQSR) job and a DAQI job, each polling Ricardo UK-AIR every 15 minutes,
  and a Met Office forecast job that runs hourly between 05:00 and 10:00 UTC.
- Resolves a UK region for every alert and every subscribed location by testing coordinates
  against bundled ITL GeoJSON boundaries, then matches alerts to subscribers by region.
- Deduplicates alerts so a single continuous breach notifies a citizen once, using per-alert
  state collections and unique audit indexes as the idempotency guard.
- Serves breach data to the front end for the location and breaches pages through
  `GET /aqsr-alert` and `GET /daqi-alert`.
- Builds the unsubscribe and "check air quality" deep links embedded in outgoing messages.

**Does not:**

- Talk to GOV.UK Notify. It holds no Notify API key; every message is posted to
  `aqie-notify-service` at `/send-notification`, which owns the Notify relationship.
- Verify contact details. One-time passcodes and email verification links are issued and
  checked by `aqie-notify-service` before `/setup-alert` is ever called.
- Serve pollutant measurements, monitoring stations or DAQI bands for location pages —
  that is `aqie-back-end`.
- Produce the Met Office forecast itself. It consumes `GET /forecast` from
  `aqie-forecast-api` and only applies the alert threshold.
- Render any user interface. The subscription journey and the unsubscribe pages live in
  `aqie-front-end`.

## 3. Architecture

**Pattern:** Hapi HTTP API co-located with three `node-cron` scheduled alert workers in a
single process. Each scheduled cycle is wrapped in a `mongo-locks` distributed lock so that
only one container in the ECS service processes a given cycle, and each scheduler also runs
one cycle immediately at server start so a restart between ticks does not miss alerts.

| Component | Path | Responsibility |
|---|---|---|
| Subscription API | `src/users/routes/`, `src/users/controllers/` | `/setup-alert`, both opt-out routes, `/aqsr-alert`, `/daqi-alert` |
| Scheduler factory | `src/plugins/createAlertSchedulerPlugin.js` | Shared cron + distributed-lock wrapper used by the pollutant and DAQI schedulers |
| Pollutant scheduler | `src/plugins/pollutant-alert-scheduler.js`, `src/users/utils/pollutantAlertProcessor.js` | AQSR breach detection, state tracking, audit rows, dispatch |
| DAQI scheduler | `src/plugins/daqi-alert-scheduler.js`, `src/users/utils/daqiAlertProcessor.js` | DAQI threshold breaches from Ricardo |
| Forecast scheduler | `src/plugins/forecast-alert-scheduler.js`, `src/users/utils/forecastAlertProcessor.js` | Daily forecast breach alerts, guarded by per-day schedule state |
| Ricardo client | `src/users/utils/ricardoApiClient.js` | Token login, authenticated GETs, proxy and timeout handling |
| Site/region cache | `src/users/utils/ricardoSiteAndRegionCache.js`, `src/users/utils/regionResolver.js` | Maps Ricardo `siteId` to a UK region, refreshed in the background |
| Region boundaries | `src/GeoBoundaries/`, `src/users/utils/regionFinder.js` | Point-in-polygon region lookup over England, Scotland, Wales and Northern Ireland GeoJSON |
| Notify client | `src/users/utils/notifyServiceClient.js` | Posts message requests to `aqie-notify-service` |
| Forecast client | `src/users/utils/forecastApiClient.js` | Reads `GET /forecast` from `aqie-forecast-api` |
| Dedup and audit | `src/users/utils/alertDedupUtils.js`, `src/users/utils/alertCycleUtils.js` | Collapse repeats, expand users to locations, dispatch with audit idempotency |
| Masking | `src/users/utils/maskingUtils.js` | Masks phone numbers, emails and template ids before logging |
| Migrations | `src/migrations/` | One-off index and state-shape corrections applied at start-up |
| Config | `src/config.js` | `convict` schema for every endpoint, schedule, template id and credential |

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/health` | Liveness probe | — | Status payload |
| `POST` | `/setup-alert` | Subscribe a verified contact to alerts for one location | `phoneNumber` or `emailAddress`, `alertType`, `location`, `lat`, `long`, `lang` | Created subscription, or `409` for a duplicate location and `400` beyond five locations |
| `DELETE` | `/opt-out-sms-alert` | Remove an SMS subscriber by phone number | `phoneNumber` | Success flag, `404` when unknown |
| `DELETE` | `/opt-out-email-alert` | Remove an email subscriber by email address | `emailAddress` | Success flag, `404` when unknown |
| `GET` | `/aqsr-alert` | Pollutant breach alerts, either for the current day at a coordinate or over a date range | `current-day` with `lat`/`long`, **or** `start-date`/`end-date` (`yyyy-mm-dd`) | Breach entries with pollutant name, concentration, threshold and start time |
| `GET` | `/daqi-alert` | DAQI breaches for the region resolved from a coordinate | `lat`, `long` | DAQI entries above the configured threshold, deduplicated and newest first |

> `/setup-alert` is only ever called after `aqie-notify-service` has verified the contact
> details. The route itself performs format and duplicate validation but does not re-verify
> ownership of the mobile number or email address.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| Ricardo UK-AIR API | External API | `POST /api/login_check` | Credentials exchanged for a bearer token | `RICARDO_API_EMAIL` / `RICARDO_API_PASSWORD` |
| Ricardo UK-AIR API | External API | `GET /api/aqsr_alerts` | Pollutant breach alerts with concentration and threshold | Bearer token |
| Ricardo UK-AIR API | External API | `GET /api/daqi_alerts` | DAQI breach alerts by sampling point | Bearer token |
| Ricardo UK-AIR API | External API | `GET /api/site_meta_datas` | Site metadata used to map `siteId` to a region | Bearer token |
| `aqie-notify-service` | AQIE service | `POST /send-notification` | Recipient, Notify template id and personalisation out; notification id back | CDP internal network |
| `aqie-forecast-api` | AQIE service | `GET /forecast` | Met Office DAQI forecast values with station coordinates | CDP internal network |
| `aqie-front-end` | AQIE service | Link construction only — `/notify/unsubscribe-email-link` | Email identifier as a query parameter inside outgoing messages | Tokenised link |
| check-air-quality.service.gov.uk | External (link) | Link construction only — `/location/{slug}?lang=` | Location deep link inside outgoing messages | None |
| MongoDB | Datastore | Driver connection, `mongo-locks` for scheduler locking | Subscribers, alert state, audit records | `MONGO_URI` |

> The `aqie-notify-service` and `aqie-forecast-api` edges are **not** yet recorded in
> [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml) — see Section 11.

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| `aqie-front-end` | `POST /setup-alert` | Verified contact, location name and coordinates, channel, language |
| `aqie-front-end` | `DELETE /opt-out-email-alert` | Email address from the unsubscribe link |
| `aqie-front-end` | `GET /aqsr-alert`, `GET /daqi-alert` | Current and historic breach data for the location and breaches pages |
| `aqie-notify-service` | `DELETE /opt-out-sms-alert` | Phone number of a citizen who replied STOP by SMS |

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).
> Only the `aqie-notify-service` edge is currently recorded there; the `aqie-front-end` edges
> are evidenced in this analysis but missing from the catalogue — see Section 11.

## 7. Data

- **Store:** MongoDB (`MONGO_DATABASE`, default `aqie-alert-back-end-service`), with
  `mongo-locks` providing distributed scheduler locking. Redis appears only in the local
  `compose.yml` and is not used by application code.
- **Key entities:**
  - `USERS` — the subscriber record: contact value, channel, language, and an array of up to
    five locations each carrying name, coordinates and resolved region.
  - `pollutant-alert-processing-state` — one document per continuous pollutant breach event,
    keyed on sampling point and breach start timestamp, with a unique compound index.
  - `pollutant-alerts-audit` — one row per alert and recipient, with the notification id
    returned by `aqie-notify-service`.
  - `metoffice-forecast-audit` — per-day, per-user-location forecast alert rows; a unique
    index makes re-runs idempotent.
  - `forecast-schedule-state` — per-day marker recording that the forecast cycle completed,
    so later hourly ticks short-circuit.
- **Refresh:** `POLLUTANT_CRON_SCHEDULE` and `DAQI_ALERT_CRON_SCHEDULE` default to every 15
  minutes; `FORECAST_CRON_SCHEDULE` defaults to hourly between 05:00 and 10:00 UTC. Alerts are
  only considered if Ricardo marks them validated and they fall within a rolling 24-hour window.
- **Caching:** an in-process site-to-region cache built from Ricardo site metadata and the
  bundled GeoJSON boundaries, refreshed in the background and re-fetched on demand if empty.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `PORT`, `HOST` | HTTP listener |
| `NODE_ENV`, `ENVIRONMENT`, `SERVICE_VERSION` | Runtime identity |
| `MONGO_URI`, `MONGO_DATABASE`, `MONGO_RETRY_WRITES`, `MONGO_READ_PREFERENCE` | MongoDB connection and driver behaviour |
| `RICARDO_API_LOGIN_URL`, `RICARDO_API_ALERTS_URL`, `RICARDO_API_DAQI_ALERTS_URL`, `RICARDO_API_SITE_METADATA_URL` | Ricardo UK-AIR endpoints |
| `RICARDO_API_EMAIL`, `RICARDO_API_PASSWORD` | Ricardo credentials — see the security note in Section 11 |
| `RICARDO_API_USE_MOCK`, `RICARDO_API_DAQI_MOCK_URL`, `RICARDO_API_AQSR_MOCK_URL` | WireMock stubs used in place of Ricardo for local and test running |
| `POLLUTANT_CRON_SCHEDULE`, `DAQI_ALERT_CRON_SCHEDULE`, `FORECAST_CRON_SCHEDULE` | Cron expressions for the three schedulers |
| `NOTIFICATION_SERVICE_URL` | Full URL of the `aqie-notify-service` send endpoint |
| `FORECAST_API_URL` | Base URL of `aqie-forecast-api` |
| `DAQI_ALERT_THRESHOLD` | Minimum DAQI value that triggers an alert |
| `SMS_SET_UP_CONFIRMATION_TEMPLATE_ID`, `EMAIL_SET_UP_CONFIRMATION_TEMPLATE_ID` | Notify templates for subscription confirmation |
| `SMS_ALERT_TEMPLATE_ID`, `SMS_ALERT_CY_TEMPLATE_ID`, `EMAIL_ALERT_TEMPLATE_ID`, `EMAIL_ALERT_CY_TEMPLATE_ID` | Notify templates for pollutant alerts, English and Welsh |
| `SMS_DAQI_ALERT_TEMPLATE_ID`, `SMS_DAQI_ALERT_CY_TEMPLATE_ID`, `EMAIL_DAQI_ALERT_TEMPLATE_ID`, `EMAIL_DAQI_ALERT_CY_TEMPLATE_ID` | Notify templates for DAQI alerts |
| `SMS_FORECAST_ALERT_TEMPLATE_ID`, `SMS_FORECAST_ALERT_CY_TEMPLATE_ID`, `EMAIL_FORECAST_ALERT_TEMPLATE_ID`, `EMAIL_FORECAST_ALERT_CY_TEMPLATE_ID` | Notify templates for forecast alerts |
| `UNSUBSCRIBE_EMAIL_LINK`, `CHECK_AIR_QUALITY_LINK` | Base URLs for the deep links placed in messages |
| `HTTP_PROXY`, `HTTPS_PROXY` | CDP egress proxy |
| `ENABLE_METRICS`, `TRACING_HEADER` | Observability |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`;
  entrypoint `node src`.
- **Internal address:** `https://aqie-alert-back-end.<env>.cdp-int.defra.cloud` — this is the
  host `aqie-front-end` defaults to, and it differs from the repository name.
- **Environments:** `local`, `infra-dev`, `management`, `dev`, `test`, `perf-test`, `ext-test`,
  `prod` are all accepted values of `ENVIRONMENT`.
- **Local development:** `compose.yml` provides MongoDB, Redis and LocalStack.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — lint, test and SonarQube on PR
  - `.github/workflows/publish.yml` — build and publish on push to `main`
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, ECS-formatted in production with
  `@elastic/ecs-pino-format`. Phone numbers, email addresses and Notify template ids are
  masked before every log write, and upstream error bodies are truncated so a proxy block page
  cannot flood the logs.
- **Tracing:** `@defra/hapi-tracing` propagating the header named in `TRACING_HEADER`;
  request handlers also honour an inbound `x-request-id`.
- **Metrics:** `aws-embedded-metrics` (CloudWatch EMF), gated by `ENABLE_METRICS`.
- **Auditing:** `@defra/cdp-auditing`; alert dispatch is additionally auditable through the
  per-alert audit collections described in Section 7.
- **Shutdown:** `hapi-pulse` for graceful draining; each scheduler stops its cron job on
  `onPostStop`.

## 11. Open Questions

- [ ] **Security — hardcoded upstream credentials.** `src/config.js` ships a real-looking
      Ricardo UK-AIR login email and password as the convict *defaults* for
      `RICARDO_API_EMAIL` and `RICARDO_API_PASSWORD`. The values are not reproduced here.
      They are committed to a public repository and must be rotated, removed from the
      defaults and required from CDP secrets instead.
- [ ] **Security — GOV.UK Notify template ids committed as defaults.** Every alert and
      confirmation template id in `src/config.js` has a live-looking UUID default. Template
      ids are lower risk than keys but should still come from configuration.
- [ ] **Security — TLS verification disabled outside production.** The Ricardo dispatcher in
      `src/users/utils/ricardoApiClient.js` sets `rejectUnauthorized: false` whenever
      `NODE_ENV` is not `production`, to tolerate the Ricardo staging certificate. Confirm
      no non-production CDP environment carries citizen data through that path.
- [ ] **Catalogue gap:** `aqie-alert-back-end-service → aqie-notify-service`
      (`POST /send-notification`) is the single delivery path for every alert, yet it is not
      in `docs/integration-catalog.yaml`.
- [ ] **Catalogue gap:** `aqie-alert-back-end-service → aqie-forecast-api` (`GET /forecast`)
      drives the daily forecast alert and is not in the catalogue.
- [ ] **Catalogue gap:** `aqie-front-end → aqie-alert-back-end-service`
      (`POST /setup-alert`, `DELETE /opt-out-email-alert`, `GET /aqsr-alert`,
      `GET /daqi-alert`) is not in the catalogue.
- [ ] `aqie-front-end` is configured with a subscription-count path of `/api/subscriptions`
      against this service's base URL, but no such route exists here. Confirm whether the
      route was removed, renamed, or never built.
- [ ] `RICARDO_API_USE_MOCK` defaults to `true`, pointing both alert feeds at public WireMock
      Cloud stubs. Confirm it is explicitly set to `false` in `prod`.
- [ ] Opt-out deletes the whole `USERS` document, so a citizen unsubscribing from one
      location loses all five. Confirm this is the intended policy. (catalogue `oq-005`)
- [ ] Confirm the retention policy for `pollutant-alerts-audit` and
      `metoffice-forecast-audit`, which hold contact values indefinitely.
