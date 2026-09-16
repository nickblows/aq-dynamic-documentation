# aqie-privatebeta-test

> WebdriverIO functional and accessibility journey tests for the citizen-facing
> `aqie-front-end` service. The most actively maintained test suite in the estate.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-privatebeta-test`](https://github.com/DEFRA/aqie-privatebeta-test) |
| Service domain | `Shared` |
| Service type | `Quality/Test Service` |
| Lifecycle stage | `Production` (supports the live service) |
| Primary language | JavaScript |
| Runtime | Node.js `>=20.3.0` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2024-03-15` |
| Last main commit (UTC) | `2026-08-06T12:20:53Z` |
| Last analysed commit | `2e6f998` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Runs end-to-end browser journeys against `aqie-front-end`: location and postcode
  search (England/Scotland/Wales and Northern Ireland), forecast pages, pollutant
  static pages, bookmarked location URLs, headers, footers, cookie banner and the
  full Welsh-language toggle.
- Exercises the air quality alert sign-up journeys — SMS mobile number entry,
  activation code, confirmation, and the email registration and unsubscribe flows.
- Validates the air pollution breaches page against data fetched independently from
  the Ricardo AQSR alerts API, so the page is checked against source rather than itself.
- Runs WCAG accessibility checks using a vendored `wcag-js-v2` library, plus an
  Allure accessibility report.

**Does not:**

- Measure performance or load — that is `aqie-privatebeta-perftest`.
- Test any backend service directly except where needed to establish expected values.

## 3. Architecture

**Pattern:** WebdriverIO 8 with the Mocha framework and the page-object pattern.
Multiple `wdio.conf.*.cjs` files select the runner: CDP container, local Chrome,
mobile emulation, BrowserStack, and a hybrid web-plus-mobile configuration.

| Component | Path | Responsibility |
|---|---|---|
| Specs | `test/specs/` | 23 journey and validation suites |
| Page objects | `test/page-objects/` | Selectors and page interactions |
| Test data | `test/testdata/` | JSON fixtures of locations, postcodes and tooltips |
| Helpers | `test/helpers/` | `convict` config, logging, proxy agents, AQSR alerts client |
| Accessibility | `accessibility-checking.js`, `libs/` | WCAG rule execution and reporting |
| Runner configs | `wdio.*.cjs` | Environment and capability selection |

Two specs — `mobileHappyPath.js` and `accessibility.e2e.js` — are excluded from the
default CDP run and only execute under the mobile or BrowserStack configurations.

## 4. API Surface

This is a test harness and exposes no API.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-front-end` | AQIE service | `https://aqie-front-end.<ENVIRONMENT>.cdp-int.defra.cloud/` — the browser base URL | Whole site under test | Holding-page password |
| `aqie-front-end` | AQIE service | Holding page `/`, `/check-local-air-quality`, `/search-location`, `/location/{id}`, `/pollutants/{pollutant}`, `/air-pollution-breaches` | Page rendering | Session cookie |
| `aqie-front-end` | AQIE service | `/notify/register/*` — mobile number, activation, verify code, confirm details, email details, unsubscribe | Alert sign-up journeys | Session cookie |
| `aqie-forecast-api` | AQIE service | `GET /forecast` (primary), with a fallback through `https://ephemeral-protected.api.<env>.cdp-int.defra.cloud/aqie-forecast-api/forecast` | Forecast values used to assert page content | API key header |
| Ricardo UK-AIR | External API | `POST https://api-ukair.defra.gov.uk/api/login_check` | Credentials exchanged for bearer token | Email/password |
| Ricardo UK-AIR | External API | `GET /api/aqsr_alerts` | Air pollution breach records for assertion | Bearer token |
| Ricardo UK-AIR | External API | `GET /api/site_meta_datas`, `GET /api/pollutant_measurement_datas` | Station and measurement data for assertion | Bearer token |
| DEFRA UK-AIR website | External | `https://uk-air.defra.gov.uk/ajax/forecast_text_summary.php` | Forecast summary text for assertion | None |
| BrowserStack | External | Remote WebDriver grid | Browser sessions | `BROWSERSTACK_USER` / `BROWSERSTACK_KEY` |
| AWS S3 | Datastore | `RESULTS_OUTPUT_S3_PATH` | Allure report upload | CDP task role |

> Note that the suite calls the **new** Ricardo host `api-ukair.defra.gov.uk`, whereas
> `aqie-back-end` still defaults to the staging host. See the open question below.

## 6. Consumed By (Inbound Dependencies)

Nothing consumes this repository. It is triggered by operators, not by other services.

## 7. Data

- **Fixtures:** JSON files under `test/testdata/` holding locations, regions, NI and
  ESW postcodes, case-sensitivity variants, invalid mobile numbers and tooltip text.
- **Live data:** the breaches and forecast assertions read real production data from
  Ricardo and UK-AIR at run time, so results depend on upstream availability.
- **Personal data:** the alert journeys use a single real UK mobile number and a real
  public webmail address as the test account. Both are committed as `convict` defaults.
  See section 11.
- **Retention:** Allure results are regenerated each run; nothing is persisted locally.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `ENVIRONMENT` | Selects the target CDP environment in the base URL |
| `DAQIE_PASSWORD` | Holding-page password for the service under test |
| `FORECAST_URL`, `EPHEMERAL_FORECAST_URL`, `EPHEMERAL_API_KEY` | Forecast API access |
| `FORECAST_SUMMARY_URL` | UK-AIR forecast summary endpoint |
| `NEW_RICARDO_SITE_META_DATA`, `POLLUTANTS_MEASUREMENTS_URL`, `SITE_META_DATA_LOGIN_URL` | Ricardo endpoints |
| `NEW_RICARDO_API_EMAIL`, `NEW_RICARDO_API_PWD` | Ricardo credentials |
| `AQSR_ALERTS_URL`, `AQSR_ALERTS_API_EMAIL`, `AQSR_ALERTS_API_PWD` | AQSR alerts API |
| `ALERT_MOBILE_NUMBER`, `ALERT_EMAIL_ADDRESS` | Test account used for alert sign-up |
| `BROWSERSTACK_USER`, `BROWSERSTACK_KEY` | BrowserStack grid |
| `CHROMEDRIVER_URL`, `CHROMEDRIVER_PORT` | WebDriver endpoint |
| `HTTP_PROXY`, `HTTPS_PROXY` | CDP egress proxy |
| `RESULTS_OUTPUT_S3_PATH`, `RUN_ID` | Result publishing |
| `DEBUG`, `LOG_LEVEL`, `NODE_ENV` | Diagnostics |

## 9. Hosting and Deployment

- **Platform:** DEFRA CDP. The suite is packaged as a Docker image and run as an
  ECS task from the CDP Portal against a chosen environment.
- **Trigger:** manual from the CDP Portal. No schedule is defined in the repository.
- **Pipelines:** `.github/workflows/publish.yml` builds and publishes the image on push
  to `main` via `DEFRA/cdp-build-action/build-test`; `check-pull-request.yml` lints on PR.
- **Local:** `npm run test:local` against `test`; `npm run test:browserstack` for
  cross-browser and mobile runs.

## 10. Observability

- **Reports:** Allure, generated into `allure-report/` and copied to
  `RESULTS_OUTPUT_S3_PATH` by `bin/publish-tests.sh` for display in the CDP Portal.
- **Failure signalling:** a `FAILED` marker file is written and copied into the report
  so the platform can surface a red run.
- **Logging:** `pino` with `@elastic/ecs-pino-format`.

## 11. Open Questions

- [ ] **Security — priority.** `test/helpers/config.js` commits working default values for
      the holding-page password, the ephemeral forecast API key, the Ricardo API email and
      password, and the AQSR alerts API email and password. These are live credentials in a
      public repository. They should be removed from source and supplied only as CDP secrets,
      and the underlying accounts rotated.
- [ ] **Personal data.** The same file commits a real UK mobile number and a real webmail
      address used as the alert test account. Confirm ownership and move to secrets.
- [ ] This suite uses `api-ukair.defra.gov.uk` while `aqie-back-end` defaults to the Ricardo
      staging host. Which is authoritative for production?
- [ ] Should this suite run on a schedule rather than on demand?
- [ ] `aqie-publicbeta-test` duplicates a subset of these specs. Confirm it can be archived.
