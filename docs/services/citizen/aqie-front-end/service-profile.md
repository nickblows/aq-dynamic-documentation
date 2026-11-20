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
| Runtime | Node.js `>=22.23.4` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2024-02-02` |
| Last main commit (UTC) | `2026-11-05T09:47:13Z` |
| Last analysed commit | `210c0c03` |
| Last analysed (UTC) | `2026-11-19T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Serves the public air quality service in English and Welsh, with a parallel Welsh route tree
  (`/lleoliad`, `/llygryddion`, `/chwilio-lleoliad/cy` and so on) rather than a language toggle
  over a single route set.
- Resolves free-text location searches — town, place name, postcode and Northern Ireland
  postcode — into coordinates, and disambiguates multiple gazetteer matches for the citizen.
- Composes a location page from several upstream sources: pollutant concentrations and station
  detail for the three nearest monitoring stations from `aqie-back-end`, and the five-day
  forecast DAQI values and the daily forecast summary text from `aqie-forecast-api`.
- Works out the DAQI bands itself. For each station pollutant it applies its own thresholds to
  the measured concentration (a coarse index of 1, 4, 7 or 10, with English or Welsh band
  labels), and it maps the forecast API's numeric DAQI for each day to a band and advice text.
- Shows current and recent air pollution breaches and DAQI alerts for a location, read from
  `aqie-alert-back-end-service`.
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
- Take DAQI bands from `aqie-back-end`. The one `aqie-back-end` route this service calls carries
  no DAQI, and the front end overwrites any `daqi` or `band` it receives with the value from its
  own threshold table. Known differences between that table and the published DEFRA bands are
  recorded in [`/docs/master/measurements-data-flow.md`](../../../master/measurements-data-flow.md).
  Forecast DAQI numbers are issued by `aqie-forecast-api`; only their band and advice mapping is
  local.
- Own alert subscriber state, verification codes or message delivery. Subscriptions live in
  `aqie-alert-back-end-service`; verification codes and magic-link state live in
  `aqie-notify-service`, which sends the messages. This service only drives the journey, and
  holds a citizen's contact details in its session while the journey runs.
- Render the interactive national map — that is `aqie-maps-frontend`.
- Serve historic or bulk archive data downloads — that is `aqie-dataselector-frontend` and
  `aqie-historicaldata-backend`.
- Provide any machine-readable public API. The only non-HTML endpoints are the platform health
  check and test and debug affordances.

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
| Location detail | `src/server/location-id/` | Assembles the per-location page from nearby-station measurements, the forecast and the forecast summary text |
| Multiple results | `src/server/multiple-results/` | Disambiguation when a search matches more than one place |
| Failure states | `src/server/location-not-found/`, `src/server/retry/` | Shown when a lookup fails or returns nothing |
| Pollutant pages | `src/server/nitrogen-dioxide/`, `ozone/`, `sulphur-dioxide/`, `particulate-matter-10/`, `particulate-matter-25/` | Static pollutant explainer content |
| Health content | `src/server/health-effects/`, `src/server/actions-reduce-exposure/`, `src/server/air-pollution-breaches/` | Health advice and breach messaging (breach data read from `aqie-alert-back-end-service`) |
| DAQI banding | `src/server/locations/helpers/pollutant-threshold-config.js`, `src/server/data/en/air-quality.js`, `src/server/data/cy/air-quality.js` | Thresholds that turn a concentration into an index and band, and the mapping from a forecast index to a band and advice text |
| Alerts journey | `src/server/notify/register/`, `src/server/notify/unsubscribe/` | SMS and email registration, verification, duplicate handling, unsubscribe, in English and Welsh |
| Notify clients | `src/server/common/services/notify-backend.js`, `notify.js`, `notify-subscription-service.js`, `subscription.js` | HTTP clients for `aqie-notify-service` and `aqie-alert-back-end-service`, plus an optional, disabled-by-default capture client |
| Upstream helpers | `src/server/common/helpers/` | Proxy agents, retry/circuit breaker, OAuth token fetch, caches, metrics |
| Session cache | `src/server/common/helpers/session-cache/`, `redis-client.js` | Catbox Redis/memory engine plus Redis pressure guards |
| Config | `src/config/index.js`, `src/config/schema-extra.js` | `convict` schema — all upstream URLs, paths and credentials |
| Client assets | `src/client/` | SCSS and progressive-enhancement JavaScript, including analytics loading |
| Statutory pages | `src/server/cookies/`, `privacy/`, `accessibility/` | Cookie, privacy and accessibility content |
| Test and mock routes | `src/server/test-routes/`, `src/server/notify/debug/` | Mock DAQI and pollutant pages, a mock alert-storage view and a mock Northern Ireland lookup. Registered in every environment except the `/notify/debug/*` pair, which is skipped in production |
| Unregistered code | `src/server/loading/`, `src/server/notify-register/`, `src/server/check-local-air-quality/` routes, `src/server/notify/index.js`, `src/server/notify/routes.js`, `routes.js` twins under `src/server/notify/register/` | Superseded or unfinished code that the router does not register |

## 4. API Surface

The service exposes HTML pages, not an API. About 120 routes (GET and POST counted separately,
about 93 distinct paths) are registered on `main`, found by following the plugin list in
`src/server/router.js`; they are grouped below by journey rather than listed individually.
Welsh routes are registered separately, with their own path names, and are noted alongside
their English equivalents. The alert sign-up journey has a full Welsh twin under `/hysbysiad/...`.

| Journey | Representative paths | Purpose |
|---|---|---|
| Entry and search | `GET /`, `GET /cy`, `GET /search-location`, `GET /chwilio-lleoliad/cy` | Landing page and the location search form |
| Search results | `GET|POST /location`, `GET|POST /lleoliad`, `GET /multiple-results`, `GET /canlyniadau-lluosog/cy` | Result handling and disambiguation between gazetteer matches |
| Location detail | `GET /location/{id}`, `GET /lleoliad/{id}` | The main page: nearby-station measurements, DAQI bands, forecast and forecast summary for one location |
| Failure states | `GET|POST /retry`, `GET /location-not-found`, `GET /lleoliad-heb-ei-ganfod/cy` | Shown when a lookup fails or returns nothing. The `/loading` and `/loading-status` pages are not registered |
| Pollutant explainers | `GET /pollutants/nitrogen-dioxide`, `/pollutants/ozone`, `/pollutants/sulphur-dioxide`, `/pollutants/particulate-matter-10`, `/pollutants/particulate-matter-25`, and `/llygryddion/*/cy` | Per-pollutant background content |
| Health advice | `GET /location/{locationId}/health-effects`, `GET /location/{locationId}/actions-reduce-exposure`, `GET /air-pollution-breaches`, plus `/lleoliad/{id}/effeithiau-iechyd`, `/lleoliad/{locationId}/camau-lleihau-amlygiad/cy`, `/torriadau-llygredd-aer/cy` | Health effects, exposure-reduction actions and breach messaging |
| Alerts — SMS sign-up | `GET|POST /notify/register/sms-mobile-number`, `sms-send-activation`, `sms-verify-code`, `sms-send-new-code`, `sms-confirm-details`, `sms-success`; `GET /notify/register/duplicate-subscription`, `/notify/register/sms-max-alerts`; Welsh `/hysbysiad/cofrestru/sms-*` | Mobile capture, one-time-code issue and verification, confirmation |
| Alerts — email sign-up | `GET|POST /notify/register/email-details`, `email-send-activation`, `email-send-new-link`, `email-confirm-token`, `alerts-success`; `GET /notify/register/email-verify-email`, `email-confirm-link`, `email-duplicate`; Welsh `/hysbysiad/cofrestru/ebost-*` | Email capture and magic-link verification |
| Alerts — shared and unsubscribe | `GET|POST /notify/register/confirm-alert-details`, `GET /notify/register/check-max-alerts`, `GET|POST /notify/unsubscribe-email-link`, `GET /notify/unsubscribe-success`, `GET /notify/unsubscribe-keep-alerts`; Welsh `/hysbysiad/dad-danysgrifio-*` and `/hysbysiad/cadw-hysbysiadau-ebost` | Shared confirmation steps and the unsubscribe journey reached from alert emails. The unsubscribe link carries the plain email address as a query parameter |
| Statutory pages | `GET /cookies`, `/privacy`, `/accessibility`, and `/preifatrwydd/cy`, `/hygyrchedd/cy`, `/briwsion/cy` | Cookie, privacy and accessibility statements |
| Platform and assets | `GET /health`, `GET /public/{param*}`, `GET /favicon.ico`, `GET /favicon.svg`, `GET /.well-known/{param*}` | Liveness probe and static asset serving |
| Test and debug affordances | `GET /test-daqi`, `/test-daqi-all`, `/test-pollutants`, `/test-pollutants-custom`, `/test-pollutants-all`, `/test/mock-pollutant/direct/{locationId}`, `/test-mock-alerts`, `/results` (mock Northern Ireland lookup), `POST /test/client-log` (refuses in production); `GET /notify/debug/mock-storage` and `POST /notify/debug/clear-mock-storage` (not registered in production) | Mock DAQI and pollutant pages, a mock alert-storage view and a mock lookup, for development and test. The `/test*` routes are registered in every environment — see Open Questions |

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-back-end` | AQIE service | `GET /monitoringStationInfo` | Searched coordinates in; the nearest current stations with their latest pollutant concentrations, station metadata and coordinates out (no DAQI) | CDP internal network |
| `aqie-forecast-api` | AQIE service | `GET /forecast` | Five-day forecast DAQI values by day and region, and the daily forecast summary text | CDP internal network |
| `aqie-notify-service` | AQIE service | `POST /subscribe/generate-otp`, `/subscribe/validate-otp`, `/subscribe/generate-link`; `GET /subscribe/validate-link/{token}` | Mobile number or email address, one-time codes, magic-link tokens | CDP internal network; `CDP_X_API_KEY` family when routed via the protected API gateway |
| `aqie-alert-back-end-service` | AQIE service | `POST /setup-alert`, `DELETE /opt-out-email-alert`, `GET /aqsr-alert`, `GET /daqi-alert`, `GET /api/subscriptions/{contact}` | Alert subscription create/delete, breach and DAQI alert content. The last route does not exist on the alert backend, so the SMS maximum-locations check fails open | CDP internal network; `CDP_X_API_KEY` family when routed via the protected API gateway |
| OS Names API | External API | `GET /search/names/v1/find` | Free-text query in; gazetteer matches with coordinates out | `OS_NAMES_API_KEY`, sent as a query-string parameter |
| OS Places (Northern Ireland) | External API | `OS_PLACES_POSTCODE_NORTHERN_IRELAND_URL` (host not in source) | NI postcode in; address and coordinates out | OAuth 2.0 client credentials |
| Microsoft Entra ID | External API | `login.microsoftonline.com/{tenant}/oauth2/v2.0/token` | Client credentials exchanged for an access token used for the NI lookup | `OS_PLACES_POSTCODE_NORTHERN_IRELAND_CLIENT_ID` / `_CLIENT_SECRET` |
| Qualtrics | External | User-follows-link to the user research sign-up form, shown on the alert success pages | No service data | None |
| Google Tag Manager / Google Analytics | External (browser) | Tag loaded in the citizen's browser, only after analytics cookie consent | Page analytics events | None |
| CDP protected API gateway | Platform | `EPHEMERAL_PROTECTED_*_API_URL` | Used only when a request arrives on localhost, to reach backends in the dev or test environments | `CDP_X_API_KEY`, `CDP_X_API_KEY_DEV`, `_TEST`, `_PERF_TEST` |
| Redis | Datastore | Catbox Redis session cache | Session state, cached location and shared page data | `REDIS_USERNAME` / `REDIS_PASSWORD` |

> `FORECAST_SUMMARY_URL` (a UK-AIR address) and `POSTCODE_NORTHERN_IRELAND_URL` (a postcodes.io
> address) are defined in the configuration but read nowhere, so this service calls neither the
> UK-AIR website nor postcodes.io. The forecast summary text arrives in the `aqie-forecast-api`
> response, and the Northern Ireland lookup uses OS Places.

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| `aqie-alert-back-end-service` | `GET /notify/unsubscribe-email-link`, plus `check-air-quality.service.gov.uk/location/` deep links | Link construction only — the alert service embeds these URLs in outgoing messages; it does not call this service at runtime. The unsubscribe link carries the plain email address as a query parameter, with no token |
| `aqie-notify-service` | `GET /notify/register/email-confirm-link` | Link construction only — the verification token is carried in the emailed link, which this service then validates with `aqie-notify-service` |

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** no database of its own. Redis (via `@hapi/catbox-redis` and `ioredis`) backs the
  session cache in deployed environments; `@hapi/catbox-memory` is used locally and in tests.
  `@hapi/yar` keeps the session on the server side, and the cookie holds only the session id.
- **Key entities:** a resolved *location* (gazetteer match, coordinates, the three nearest
  monitoring stations, pollutant values, DAQI bands, forecast days, forecast summary text); an
  in-progress *alert subscription* (contact detail, verification state, chosen location) held in
  session until the notify and alert services confirm it.
- **Caching and refresh:** separate TTLs for the shared server cache, per-user data cache and
  shared location cache (`SERVER_SHARED_CACHE_TTL_MS`, `USER_DATA_CACHE_TTL_MS`,
  `SHARED_LOCATION_CACHE_TTL_MS`), with a background refresh interval
  (`REFRESH_INTERVAL_MS`). A global session guard sheds load when Redis memory growth crosses
  configured thresholds.
- **Resilience:** the Northern Ireland lookup has its own timeout, retry, cache and circuit
  breaker settings, independent of the other upstream calls.
- **Personal data:** mobile numbers and email addresses pass through the alert journey. They are
  held in the server-side session (Redis) while the journey runs, for the session lifetime
  (`SESSION_CACHE_TTL`, default four hours), and are forwarded to the notify and alert
  services. They are not otherwise stored here, but the application logs can contain email
  addresses (see Open Questions).

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here. The `convict`
schema defines about 110 variables, plus a few read directly from the environment; the table
groups the significant ones.

| Variable | Purpose |
|---|---|
| `HOST`, `PORT`, `NODE_ENV`, `SERVICE_VERSION` | Runtime identity and HTTP listener |
| `NEW_RICARDO_MEASUREMENTS_API_URL` | `aqie-back-end` `/monitoringStationInfo` endpoint, used for every runtime request |
| `MEASUREMENTS_API_URL` | **Dead config.** Its default points at `aqie-back-end` `/measurements`, removed by [PR #163](https://github.com/DEFRA/aqie-back-end/pull/163). It is read only by a branch that no runtime caller can reach. Set in every environment, per CDP environment configuration. Candidate for deletion |
| `USE_NEW_RICARDO_MEASUREMENTS_ENABLED` | **Vestigial flag**, default `true`, and `true` in every environment, per CDP environment configuration. The English journey ignores it. In the Welsh journey it only chooses the response parser: set to `false`, the new response would go to the legacy parser, which by reading the code (not run) fails, so the Welsh location page would most likely return an HTTP 500. It no longer selects the URL, so it is not a rollback switch. Candidate for deletion |
| `FORECAST_API_URL` | `aqie-forecast-api` forecast endpoint, which also supplies the forecast summary text |
| `FORECAST_SUMMARY_URL` | **Dead config.** The default is a UK-AIR address, but nothing reads it |
| `OS_NAMES_API_URL`, `OS_NAMES_API_KEY` | OS Names gazetteer lookup (the key travels in the query string) |
| `OS_PLACES_POSTCODE_NORTHERN_IRELAND_URL`, `OS_PLACES_POSTCODE_NORTHERN_IRELAND_REDIRECT_URI` | Northern Ireland postcode lookup (OS Places) |
| `POSTCODE_NORTHERN_IRELAND_URL` | **Dead config.** The default is a postcodes.io address, but nothing reads it |
| `OS_PLACES_POSTCODE_NORTHERN_IRELAND_OAUTH_TOKEN_URL`, `OAUTH_TOKEN_NORTHERN_IRELAND_API_TENANT_ID`, `OS_PLACES_POSTCODE_NORTHERN_IRELAND_CLIENT_ID`, `OS_PLACES_POSTCODE_NORTHERN_IRELAND_CLIENT_SECRET`, `OS_PLACES_POSTCODE_NORTHERN_IRELAND_CLIENT_SCOPE` | OAuth client-credentials flow for the NI lookup |
| `NI_API_TIMEOUT_MS`, `NI_API_MAX_RETRIES`, `NI_API_RETRY_DELAY_MS`, `NI_API_CACHE_ENABLED`, `NI_API_CACHE_TTL_MS`, `NI_API_CIRCUIT_BREAKER_ENABLED`, `NI_API_CIRCUIT_BREAKER_FAILURE_THRESHOLD`, `NI_API_CIRCUIT_BREAKER_OPEN_MS` | NI lookup resilience controls |
| `NOTIFY_ENABLED`, `NOTIFY_BASE_URL` | `aqie-notify-service` toggle and base URL |
| `ALERT_BACKEND_BASE_URL` | `aqie-alert-back-end-service` base URL |
| `NOTIFY_SMS_PATH`, `NOTIFY_VERIFY_OTP_PATH`, `NOTIFY_EMAIL_PATH`, `NOTIFY_EMAIL_GENERATE_LINK_PATH`, `NOTIFY_EMAIL_VALIDATE_LINK_PATH`, `NOTIFY_SETUP_ALERT_PATH`, `NOTIFY_OPT_OUT_EMAIL_ALERT_PATH`, `NOTIFY_GET_SUBSCRIPTIONS_PATH`, `NOTIFY_BREACHES_PATH`, `NOTIFY_DAQI_ALERT_PATH` | Upstream notify and alert API paths. `NOTIFY_EMAIL_PATH` has no caller, and `NOTIFY_GET_SUBSCRIPTIONS_PATH` (default `/api/subscriptions`) names a route the alert backend does not serve. It is unset in every environment, per CDP environment configuration, so the default is what is called |
| `NOTIFY_SMS_*_PATH`, `NOTIFY_EMAIL_*_PATH`, `NOTIFY_UNSUBSCRIBE_*_PATH`, `NOTIFY_ALERTS_SUCCESS_PATH`, `NOTIFY_DUPLICATE_SUBSCRIPTION_PATH` | Internal page paths for the alert journey, kept configurable |
| `NOTIFY_MOCK_OTP_ENABLED`, `NOTIFY_MOCK_OTP_CODE`, `NOTIFY_MOCK_SETUP_ALERT_ENABLED`, `NOTIFY_MOCK_SUBSCRIPTION_CHECK_MAX_REACHED` | Mock affordances for the alert journey, off by default. The default mock code is committed |
| `SUBSCRIPTION_API_ENABLED`, `SUBSCRIPTION_API_BASE_URL`, `SUBSCRIPTION_API_KEY`, `SUBSCRIPTION_API_EMAIL_PATH`, `SUBSCRIPTION_API_SMS_PATH`, `SUBSCRIPTION_API_TIMEOUT_MS` | Optional subscription-capture client (`src/server/common/services/subscription.js`): when enabled and given a base URL it posts the captured email address or mobile number to `/capture/email` or `/capture/sms`. Disabled by default, and the enabling, base URL, key and path variables are unset in every environment's app config, per CDP environment configuration. No AQIE service serves those routes |
| `CDP_X_API_KEY`, `CDP_X_API_KEY_DEV`, `CDP_X_API_KEY_TEST`, `CDP_X_API_KEY_PERF_TEST` | API keys for the CDP protected gateway |
| `EPHEMERAL_PROTECTED_DEV_API_URL`, `EPHEMERAL_PROTECTED_TEST_API_URL`, `EPHEMERAL_PROTECTED_PERF_TEST_API_URL` | Protected gateway base URLs per environment |
| `SESSION_CACHE_ENGINE`, `SESSION_CACHE_NAME`, `SESSION_CACHE_TTL`, `SESSION_CACHE_MEMORY_MAX_BYTE_SIZE`, `USE_SINGLE_INSTANCE_CACHE` | Session cache engine selection |
| `SESSION_COOKIE_TTL`, `SESSION_COOKIE_PASSWORD`, `SESSION_COOKIE_SECURE`, `COOKIE_PASSWORD` | Session cookie behaviour and signing. `SESSION_COOKIE_PASSWORD` has a committed placeholder default and no start-up check; `COOKIE_PASSWORD` is read nowhere |
| `REDIS_HOST`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_KEY_PREFIX`, `REDIS_TLS` | Redis connection |
| `SESSION_GLOBAL_GUARD_ENABLED`, `REDIS_PRESSURE_CHECK_INTERVAL_MS`, `REDIS_PRESSURE_WINDOW_MS`, `REDIS_PRESSURE_COOLDOWN_MS`, `REDIS_PRESSURE_MIN_GROWTH_MEBIBYTES`, `BYTES_PER_MEBIBYTE` | Redis pressure guard thresholds |
| `REFRESH_INTERVAL_MS`, `SERVER_SHARED_CACHE_TTL_MS`, `USER_DATA_CACHE_TTL_MS`, `SHARED_LOCATION_CACHE_TTL_MS`, `STATIC_CACHE_TIMEOUT` | Data refresh and cache windows |
| `SIGNIN_USERNAME`, `AIRQUALITY_SIGNIN_PASSWORD` | **Dead config.** Read nowhere, and no sign-in gate exists |
| `USER_RESEARCH_PANEL_URL` | Qualtrics user research sign-up link, shown on the alert success pages |
| `ASSET_PATH` | Base path for the compiled client bundle |
| `HTTP_PROXY`, `HTTPS_PROXY` | CDP egress proxy |
| `ENABLE_SECURE_CONTEXT` | TLS trust store |
| `ENABLE_METRICS`, `TRACING_HEADER` | Observability |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |
| `ENABLED_MOCK`, `DISABLE_TEST_MOCKS` | Test and mock affordances. `DISABLE_TEST_MOCKS` switches off the mock query parameters and defaults to true in production and perf-test; it does not stop the test routes being registered |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`
  (Node 22.23.4 parent image); entrypoint `node src`, with a development stage running
  `npm run docker:dev`.
- **Public address:** `https://check-air-quality.service.gov.uk`.
- **Internal address:** `https://aqie-front-end.<env>.cdp-int.defra.cloud`.
- **Environments:** `dev`, `test`, `perf-test`, `prod`.
- **Build:** webpack compiles SCSS and client JavaScript into the served asset bundle; the
  build runs ahead of both `start` and `test`.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — lint, test and coverage, dependency review and a
    SonarCloud scan on pull request and on a weekly schedule, posting results back as a PR
    comment
  - `.github/workflows/publish.yml` — build and publish on push to `main`, with a SonarCloud scan
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish
  - `.github/workflows/template.yml`, `validate-template.yml` — CDP template sync
- **Performance tooling:** `scripts/` holds local load and Redis-pressure sign-off harnesses
  (autocannon based) used to validate the session cache guards before release.

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, formatted with `@elastic/ecs-pino-format`. In production,
  redaction covers only the authorization and cookie request headers and the response headers.
  The shared fetch helpers log request URLs, and some alert-journey controllers log upstream
  response bodies (see Open Questions).
- **Tracing:** `@defra/hapi-tracing` propagating the header named in `TRACING_HEADER`
  (`x-cdp-request-id` by default).
- **Metrics:** `aws-embedded-metrics` (CloudWatch EMF), gated by `ENABLE_METRICS`.
- **KPI tracking:** a Hapi extension emits `transaction_initiated` and `transaction_completed`
  events, correlated by a per-session journey identifier, for the service performance metrics.
- **Auditing:** `@defra/cdp-auditing`.
- **Shutdown:** `hapi-pulse` for graceful draining.

## 11. Open Questions

- [ ] The SMS journey's maximum-locations check calls `GET /api/subscriptions/{contact}` on the
      alert backend, which has no such route, so the check fails open (catalogue `oq-015`). Add
      the route to the alert backend, or remove the call and rely on the 400 from
      `POST /setup-alert`, as the email journey does?
- [ ] (catalogue `oq-038`) The unsubscribe link carries the plain email address and no token, and the confirm step
      deletes the subscription for whatever address is in the session. Confirm that is
      acceptable. A signed-link helper exists unused in `notify-util/`.
- [ ] The `/test*` routes and `/results` are registered in every environment. Only the
      `/notify/debug/*` pair is skipped in production, and `/test/client-log` refuses in
      production. Confirm the rest are blocked at the platform edge, or stop registering them
      in production.
- [ ] `USE_NEW_RICARDO_MEASUREMENTS_ENABLED`, `MEASUREMENTS_API_URL` and the legacy measurements
      branch can no longer restore the old behaviour (catalogue `oq-016`). Confirm and delete
      them, including the variable in CDP configuration.
- [ ] Keys and personal data reach the logs: the OS Names key travels in the request URL, which
      the shared fetch helper logs, and the response to the verification-link check, which
      includes the email address, is logged at info level. Confirm who can read the logs and
      for how long, and stop logging both.
- [ ] Confirm which dead code and configuration can go: the unregistered route trees (see
      Architecture), `FORECAST_SUMMARY_URL`, `POSTCODE_NORTHERN_IRELAND_URL`, `NOTIFY_EMAIL_PATH`,
      the sign-in variables, `COOKIE_PASSWORD`, the `SUBSCRIPTION_API_*` capture client (catalogue `oq-013`), the
      `.checkpoints/` archive and the unused `notify-util/` helpers.
- [ ] (catalogue `oq-037`) Committed test material: a Postman collection under `src/server/notify/` holds a CDP
      gateway key variable with a literal value, and three committed Postman collections carry
      UK mobile numbers and corporate email addresses that may belong to real people. Confirm
      the key has expired or revoke it, and replace the personal details with reserved test
      values.
- [ ] Confirm the Northern Ireland OS Places host and product, which are not in source.
      `OS_PLACES_POSTCODE_NORTHERN_IRELAND_URL` is set in every environment and `ENABLED_MOCK` is
      unset, per CDP environment configuration, so the lookup is configured and not mocked. The
      Entra ID tenant and the product are not recorded here.
