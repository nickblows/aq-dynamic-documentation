# aqie-front-end

> The public "Check air quality" service at check-air-quality.service.gov.uk. It is the
> bilingual citizen-facing front end that turns a place-name or postcode search into current
> pollutant readings, DAQI bands, forecasts, health advice and air quality alert subscriptions.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-front-end`](https://github.com/DEFRA/aqie-front-end) |
| Service domain | `Citizen` |
| Service type | `Core Frontend Service` |
| Lifecycle stage | `Production` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22.16.0` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2024-02-02` |
| Last main commit (UTC) | `2026-09-02T16:29:50Z` |
| Last analysed commit | `ee5b1151` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Serves the public air quality service in English and Welsh, with a parallel Welsh route tree
  (`/lleoliad`, `/llygryddion`, `/chwilio-lleoliad/cy` and so on) rather than a language toggle
  over a single route set.
- Resolves free-text location searches — town, place name, postcode and Northern Ireland
  postcode — into coordinates, and disambiguates multiple gazetteer matches for the citizen.
- Composes a location page from several upstream sources: pollutant concentrations and DAQI
  bands from `aqie-back-end`, multi-day forecast from `aqie-forecast-api`, and the national
  forecast narrative published by UK-AIR.
- Renders pollutant explainer pages (NO₂, O₃, SO₂, PM10, PM2.5), health-effects content and
  "actions to reduce exposure" guidance in both languages.
- Runs the full air quality alert sign-up journey for SMS and email — number/address capture,
  one-time-code and magic-link verification, duplicate and maximum-subscription checks,
  confirmation and unsubscribe — delegating all state and message sending to
  `aqie-notify-service` and `aqie-alert-back-end-service`.
- Serves the statutory pages (cookies, privacy, accessibility) and the compiled client-side
  asset bundle.
- Caches location and shared page data in a session store (Redis in deployed environments,
  in-memory locally) with explicit pressure guards to protect Redis under load.

**Does not:**

- Ingest, normalise or store air quality measurements. All readings and station metadata come
  from `aqie-back-end`; this service holds no measurement database.
- Calculate DAQI bands. Banding is done upstream in `aqie-back-end`.
- Own alert subscriber state, verification codes or message delivery. Subscriptions live in
  `aqie-notify-service` / `aqie-alert-back-end-service`; this service only drives the journey.
- Render the interactive national map — that is `aqie-maps-frontend`.
- Serve historic or bulk archive data downloads — that is `aqie-dataselector-frontend` and
  `aqie-historicaldata-backend`.
- Provide any machine-readable public API. The only non-HTML endpoints are the platform health
  check and internal debug affordances.

## 3. Architecture

**Pattern:** Hapi server rendering Nunjucks views, with progressive-enhancement client
JavaScript built by webpack. Each page is a self-contained Hapi plugin under `src/server/`
holding its own routes, controller and templates; Welsh variants sit in a `cy/` subfolder of
the same plugin. Outbound calls are made server-side only, through an explicit proxy agent
because CDP brokers all egress through a forward proxy.

| Component | Path | Responsibility |
|---|---|---|
| Router | `src/server/router.js` | Registers every page plugin and the static file handler |
| Location search | `src/server/search-location/`, `src/server/locations/` | Query parsing, gazetteer lookup, result ranking |
| Location detail | `src/server/location-id/` | Assembles the per-location page from measurements, forecast and narrative |
| Multiple results | `src/server/multiple-results/` | Disambiguation when a search matches more than one place |
| Not found / retry | `src/server/location-not-found/`, `src/server/retry/`, `src/server/loading/` | Failure and in-progress states for slow upstream calls |
| Pollutant pages | `src/server/nitrogen-dioxide/`, `ozone/`, `sulphur-dioxide/`, `particulate-matter-10/`, `particulate-matter-25/` | Static pollutant explainer content |
| Health content | `src/server/health-effects/`, `src/server/actions-reduce-exposure/`, `src/server/air-pollution-breaches/` | Health advice and exceedance messaging |
| Alerts journey | `src/server/notify/` | SMS and email registration, verification, duplicate handling, unsubscribe |
| Notify clients | `src/server/common/services/notify-backend.js`, `notify-subscription-service.js` | HTTP clients for `aqie-notify-service` and `aqie-alert-back-end-service` |
| Upstream helpers | `src/server/common/helpers/` | Proxy agents, retry/circuit breaker, OAuth token fetch, caches, metrics |
| Session cache | `src/server/common/helpers/session-cache/`, `redis-client.js` | Catbox Redis/memory engine plus Redis pressure guards |
| Config | `src/config/index.js`, `src/config/schema-extra.js` | `convict` schema — all upstream URLs, paths and credentials |
| Client assets | `src/client/` | SCSS and progressive-enhancement JavaScript, including analytics loading |
| Statutory pages | `src/server/cookies/`, `privacy/`, `accessibility/` | Cookie, privacy and accessibility content |

## 4. API Surface

The service exposes HTML pages, not an API. 108 routes were detected on `main`; they are
grouped below by journey rather than listed individually. Welsh routes are registered
separately and are noted alongside their English equivalents.

| Journey | Representative paths | Purpose |
|---|---|---|
| Entry and search | `GET /`, `GET /cy`, `GET|POST /search-location`, `GET /chwilio-lleoliad/cy` | Landing page and the location search form |
| Search results | `GET /location`, `GET /lleoliad`, `GET /results`, `GET /multiple-results`, `GET /canlyniadau-lluosog/cy` | Result listing and disambiguation between gazetteer matches |
| Location detail | `GET /location/{id}`, `GET /lleoliad/{id}` | The main page: measurements, DAQI band, forecast and narrative for one location |
| Interstitial and failure states | `GET /loading`, `GET /loading-status`, `GET /retry`, `GET /location-not-found`, `GET /lleoliad-heb-ei-ganfod/cy` | Shown while upstream calls run, or when a lookup fails or returns nothing |
| Pollutant explainers | `GET /pollutants/nitrogen-dioxide`, `/pollutants/ozone`, `/pollutants/sulphur-dioxide`, `/pollutants/particulate-matter-10`, `/pollutants/particulate-matter-25`, and `/llygryddion/*/cy` | Per-pollutant background content |
| Health advice | `GET /location/{locationId}/health-effects`, `GET /location/{locationId}/actions-reduce-exposure`, `GET /air-pollution-breaches`, plus `/lleoliad/{id}/effeithiau-iechyd`, `/lleoliad/{locationId}/camau-lleihau-amlygiad/cy`, `/torriadau-llygredd-aer/cy` | Health effects, exposure-reduction actions and breach messaging |
| Alerts — SMS sign-up | `GET|POST /notify/mobile-phone`, `/notify/confirm-mobile`, `/notify/activation-code`, `/notify/text-alerts`, `/notify/register/sms-mobile-number`, `sms-send-activation`, `sms-verify-code`, `sms-send-new-code`, `sms-confirm-details`, `sms-success`, `sms-duplicate`, `sms-max-emails` | Mobile capture, one-time-code issue and verification, confirmation |
| Alerts — email sign-up | `GET|POST /notify/enter-email`, `/notify/email-alerts`, `/notify/register/email-details`, `email-verify-email`, `email-send-activation`, `email-send-new-link`, `email-confirm-link`, `email-confirm-token`, `email-duplicate`, `alerts-success` | Email capture and magic-link verification |
| Alerts — shared and unsubscribe | `GET /notify/confirm-alert`, `/notify/success`, `/notify/register/confirm-alert-details`, `/notify/register/check-max-alerts`, `/notify/unsubscribe-email-link`, `/notify/unsubscribe-success`, `/notify/unsubscribe-keep-alerts` | Shared confirmation steps and the unsubscribe journey reached from alert emails |
| Statutory pages | `GET /cookies`, `/privacy`, `/accessibility`, and `/preifatrwydd/cy`, `/hygyrchedd/cy`, `/briwsion/cy` | Cookie, privacy and accessibility statements |
| Platform and assets | `GET /health`, `GET /public/{param*}`, `GET /favicon.ico`, `GET /favicon.svg`, `GET /.well-known/{param*}` | Liveness probe and static asset serving |
| Debug and test affordances | `GET /notify/debug/mock-storage`, `POST /notify/debug/clear-mock-storage`, plus the fixtures under `src/server/test-routes/` (`/simple-path`, `/some-other-path`, `/x`) | Local development and test support only — see Open Questions |

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-back-end` | AQIE service | `GET /measurements` | Per-station pollutant concentrations and DAQI bands | CDP internal network |
| `aqie-back-end` | AQIE service | `GET /monitoringStationInfo` | Station metadata, coordinates and pollutants measured | CDP internal network |
| `aqie-forecast-api` | AQIE service | `GET /forecast` | Multi-day forecast DAQI values by day and region | CDP internal network |
| `aqie-notify-service` | AQIE service | `POST /subscribe/generate-otp`, `/subscribe/validate-otp`, `/send-email-code`, `/subscribe/generate-link`, `/subscribe/validate-link` | Mobile number or email address, one-time codes, magic-link tokens | CDP internal network; `CDP_X_API_KEY` family when routed via the protected API gateway |
| `aqie-alert-back-end-service` | AQIE service | `POST /setup-alert`, `/opt-out-email-alert`, `GET /api/subscriptions`, `/aqsr-alert`, `/daqi-alert` | Alert subscription create/delete, subscription counts, breach and DAQI alert content | CDP internal network; `CDP_X_API_KEY` family |
| OS Names API | External API | `GET /search/names/v1/find` | Free-text query in; gazetteer matches with coordinates out | `OS_NAMES_API_KEY` |
| OS Places (Northern Ireland) | External API | `OS_PLACES_POSTCODE_NORTHERN_IRELAND_URL` | NI postcode in; address and coordinates out | OAuth 2.0 client credentials |
| Microsoft Entra ID | External API | `login.microsoftonline.com/{tenant}/oauth2/v2.0/token` | Client credentials exchanged for an access token used for the NI lookup | `OS_PLACES_POSTCODE_NORTHERN_IRELAND_CLIENT_ID` / `_CLIENT_SECRET` |
| postcodes.io | External API | `GET /postcodes?q=` | Postcode query in; coordinates out (Northern Ireland fallback path) | None |
| UK-AIR website | External | `GET /ajax/forecast_text_summary.php` | National forecast narrative as text/HTML | None |
| Qualtrics | External | User-follows-link to the feedback survey | No service data | None |
| Google Tag Manager / Google Analytics | External (browser) | Tag loaded in the citizen's browser, gated by cookie consent | Page analytics events | None |
| CDP protected API gateway | Platform | `EPHEMERAL_PROTECTED_*_API_URL` | Routes calls to protected backends in non-production environments | `CDP_X_API_KEY`, `CDP_X_API_KEY_DEV`, `_TEST`, `_PERF_TEST` |
| Redis | Datastore | Catbox Redis session cache | Session state, cached location and shared page data | `REDIS_USERNAME` / `REDIS_PASSWORD` |

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| `aqie-alert-back-end-service` | `GET /notify/unsubscribe-email-link`, plus `check-air-quality.service.gov.uk/location/` deep links | Link construction only — the alert service embeds these URLs in outgoing messages; it does not call this service at runtime |
| `aqie-notify-service` | Service base URL held in its own configuration | Link construction for messages it sends |

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** no database of its own. Redis (via `@hapi/catbox-redis` and `ioredis`) backs the
  session cache in deployed environments; `@hapi/catbox-memory` is used locally and in tests.
  `@hapi/yar` holds the session cookie.
- **Key entities:** a resolved *location* (gazetteer match, coordinates, nearest monitoring
  station, pollutant values, DAQI band, forecast days, narrative text); an in-progress *alert
  subscription* (contact detail, verification state, chosen location) held in session until the
  notify services confirm it.
- **Caching and refresh:** separate TTLs for the shared server cache, per-user data cache and
  shared location cache (`SERVER_SHARED_CACHE_TTL_MS`, `USER_DATA_CACHE_TTL_MS`,
  `SHARED_LOCATION_CACHE_TTL_MS`), with a background refresh interval
  (`REFRESH_INTERVAL_MS`). A global session guard sheds load when Redis memory growth crosses
  configured thresholds.
- **Resilience:** the Northern Ireland lookup has its own timeout, retry, cache and circuit
  breaker settings, independent of the other upstream calls.
- **Personal data:** mobile numbers and email addresses pass through the alert journey but are
  not persisted here — they are forwarded to the notify services.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here. The `convict`
schema defines around 140 variables; the table groups the significant ones.

| Variable | Purpose |
|---|---|
| `HOST`, `PORT`, `NODE_ENV`, `SERVICE_VERSION` | Runtime identity and HTTP listener |
| `MEASUREMENTS_API_URL`, `NEW_RICARDO_MEASUREMENTS_API_URL` | `aqie-back-end` measurements and station-info endpoints |
| `USE_NEW_RICARDO_MEASUREMENTS_ENABLED` | Feature flag selecting the newer measurements source |
| `FORECAST_API_URL` | `aqie-forecast-api` forecast endpoint |
| `FORECAST_SUMMARY_URL` | UK-AIR national forecast narrative |
| `OS_NAMES_API_URL`, `OS_NAMES_API_KEY` | OS Names gazetteer lookup |
| `POSTCODE_NORTHERN_IRELAND_URL`, `OS_PLACES_POSTCODE_NORTHERN_IRELAND_URL`, `OS_PLACES_POSTCODE_NORTHERN_IRELAND_REDIRECT_URI` | Northern Ireland postcode lookup |
| `OS_PLACES_POSTCODE_NORTHERN_IRELAND_OAUTH_TOKEN_URL`, `OAUTH_TOKEN_NORTHERN_IRELAND_API_TENANT_ID`, `OS_PLACES_POSTCODE_NORTHERN_IRELAND_CLIENT_ID`, `OS_PLACES_POSTCODE_NORTHERN_IRELAND_CLIENT_SECRET`, `OS_PLACES_POSTCODE_NORTHERN_IRELAND_CLIENT_SCOPE` | OAuth client-credentials flow for the NI lookup |
| `NI_API_TIMEOUT_MS`, `NI_API_MAX_RETRIES`, `NI_API_RETRY_DELAY_MS`, `NI_API_CACHE_ENABLED`, `NI_API_CACHE_TTL_MS`, `NI_API_CIRCUIT_BREAKER_ENABLED`, `NI_API_CIRCUIT_BREAKER_FAILURE_THRESHOLD`, `NI_API_CIRCUIT_BREAKER_OPEN_MS` | NI lookup resilience controls |
| `NOTIFY_ENABLED`, `NOTIFY_BASE_URL` | `aqie-notify-service` toggle and base URL |
| `ALERT_BACKEND_BASE_URL` | `aqie-alert-back-end-service` base URL |
| `NOTIFY_SMS_PATH`, `NOTIFY_VERIFY_OTP_PATH`, `NOTIFY_EMAIL_PATH`, `NOTIFY_EMAIL_GENERATE_LINK_PATH`, `NOTIFY_EMAIL_VALIDATE_LINK_PATH`, `NOTIFY_SETUP_ALERT_PATH`, `NOTIFY_OPT_OUT_EMAIL_ALERT_PATH`, `NOTIFY_GET_SUBSCRIPTIONS_PATH`, `NOTIFY_BREACHES_PATH`, `NOTIFY_DAQI_ALERT_PATH` | Upstream notify and alert API paths |
| `NOTIFY_SMS_*_PATH`, `NOTIFY_EMAIL_*_PATH`, `NOTIFY_UNSUBSCRIBE_*_PATH`, `NOTIFY_ALERTS_SUCCESS_PATH`, `NOTIFY_DUPLICATE_SUBSCRIPTION_PATH` | Internal page paths for the alert journey, kept configurable |
| `NOTIFY_MOCK_OTP_ENABLED`, `NOTIFY_MOCK_OTP_CODE`, `NOTIFY_MOCK_SETUP_ALERT_ENABLED`, `NOTIFY_MOCK_SUBSCRIPTION_CHECK_MAX_REACHED` | Mock affordances for the alert journey |
| `SUBSCRIPTION_API_ENABLED`, `SUBSCRIPTION_API_BASE_URL`, `SUBSCRIPTION_API_KEY`, `SUBSCRIPTION_API_EMAIL_PATH`, `SUBSCRIPTION_API_SMS_PATH`, `SUBSCRIPTION_API_TIMEOUT_MS` | Optional subscription-capture API (disabled by default — see Open Questions) |
| `CDP_X_API_KEY`, `CDP_X_API_KEY_DEV`, `CDP_X_API_KEY_TEST`, `CDP_X_API_KEY_PERF_TEST` | API keys for the CDP protected gateway |
| `EPHEMERAL_PROTECTED_DEV_API_URL`, `EPHEMERAL_PROTECTED_TEST_API_URL`, `EPHEMERAL_PROTECTED_PERF_TEST_API_URL` | Protected gateway base URLs per environment |
| `SESSION_CACHE_ENGINE`, `SESSION_CACHE_NAME`, `SESSION_CACHE_TTL`, `SESSION_CACHE_MEMORY_MAX_BYTE_SIZE`, `USE_SINGLE_INSTANCE_CACHE` | Session cache engine selection |
| `SESSION_COOKIE_TTL`, `SESSION_COOKIE_PASSWORD`, `SESSION_COOKIE_SECURE`, `COOKIE_PASSWORD` | Session cookie behaviour and signing |
| `REDIS_HOST`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_KEY_PREFIX`, `REDIS_TLS` | Redis connection |
| `SESSION_GLOBAL_GUARD_ENABLED`, `REDIS_PRESSURE_CHECK_INTERVAL_MS`, `REDIS_PRESSURE_WINDOW_MS`, `REDIS_PRESSURE_COOLDOWN_MS`, `REDIS_PRESSURE_MIN_GROWTH_MEBIBYTES`, `BYTES_PER_MEBIBYTE` | Redis pressure guard thresholds |
| `REFRESH_INTERVAL_MS`, `SERVER_SHARED_CACHE_TTL_MS`, `USER_DATA_CACHE_TTL_MS`, `SHARED_LOCATION_CACHE_TTL_MS`, `STATIC_CACHE_TIMEOUT` | Data refresh and cache windows |
| `SIGNIN_USERNAME`, `AIRQUALITY_SIGNIN_PASSWORD` | Sign-in gate credentials |
| `USER_RESEARCH_PANEL_URL` | Qualtrics feedback survey link |
| `ASSET_PATH` | Base path for the compiled client bundle |
| `HTTP_PROXY`, `HTTPS_PROXY` | CDP egress proxy |
| `ENABLE_SECURE_CONTEXT` | TLS trust store |
| `ENABLE_METRICS`, `TRACING_HEADER` | Observability |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |
| `ENABLED_MOCK`, `DISABLE_TEST_MOCKS` | Test and mock affordances |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`;
  entrypoint `node src`, with a development stage running `npm run docker:dev`.
- **Public address:** `https://check-air-quality.service.gov.uk`.
- **Internal address:** `https://aqie-front-end.<env>.cdp-int.defra.cloud`.
- **Environments:** `dev`, `test`, `perf-test`, `prod`.
- **Build:** webpack compiles SCSS and client JavaScript into the served asset bundle; the
  build runs ahead of both `start` and `test`.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — lint, test and coverage on pull request and on
    a schedule, posting results back as a PR comment
  - `.github/workflows/publish.yml` — build and publish on push to `main`
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish
  - `.github/workflows/template.yml`, `validate-template.yml` — CDP template sync
- **Performance tooling:** `scripts/` holds local load and Redis-pressure sign-off harnesses
  (autocannon based) used to validate the session cache guards before release.

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, formatted with `@elastic/ecs-pino-format`.
- **Tracing:** `@defra/hapi-tracing` propagating the header named in `TRACING_HEADER`
  (`x-cdp-request-id` by default).
- **Metrics:** `aws-embedded-metrics` (CloudWatch EMF), gated by `ENABLE_METRICS`.
- **KPI tracking:** a Hapi extension emits `transaction_initiated` and `transaction_completed`
  events, correlated by a per-session journey identifier, for the service performance metrics.
- **Auditing:** `@defra/cdp-auditing`.
- **Shutdown:** `hapi-pulse` for graceful draining.

## 11. Open Questions

- [ ] `SUBSCRIPTION_API_BASE_URL` has no default and the feature is disabled by default. Confirm
      whether a subscription-capture API is used in production and, if so, which service it is,
      so the edge can be added to the integration catalogue.
- [ ] Confirm which of `aqie-notify-service` and `aqie-alert-back-end-service` owns subscriber
      state, and whether the front end should ever call both (catalogue `oq-005`).
- [ ] `USE_NEW_RICARDO_MEASUREMENTS_ENABLED` switches the measurements source. Confirm the
      production setting and whether the older path can be retired.
- [ ] The sign-in gate (`SIGNIN_USERNAME` / `AIRQUALITY_SIGNIN_PASSWORD`) ships with weak
      defaults. Confirm whether it is active in any deployed environment.
- [ ] `src/server/test-routes/` and `/notify/debug/*` are registered in the same router as the
      production pages. Confirm they are excluded or disabled in production.
- [ ] Confirm the Northern Ireland postcode lookup is live in production, and which Entra ID
      tenant and OS Places product it uses.
