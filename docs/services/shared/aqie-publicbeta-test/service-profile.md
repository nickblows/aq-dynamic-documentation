# aqie-publicbeta-test

> A reduced copy of `aqie-privatebeta-test` targeting the same `aqie-front-end` service.
> Superseded and not maintained since November 2025.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-publicbeta-test`](https://github.com/DEFRA/aqie-publicbeta-test) |
| Service domain | `Shared` |
| Service type | `Quality/Test Service` |
| Lifecycle stage | `Beta` — effectively superseded |
| Primary language | JavaScript |
| Runtime | Node.js `>=20.11.1` (CommonJS) |
| Default branch | `main` |
| Created (UTC) | `2024-08-29` |
| Last main commit (UTC) | `2025-11-28T14:28:33Z` |
| Last analysed commit | `8412841` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Inactive` |

## 2. Purpose and Responsibilities

**Does:**

- Runs browser journeys against `aqie-front-end`: location and postcode search,
  forecast pages, pollutant static pages, page titles, headers, footers, cookie
  banner, unhappy paths and the Welsh-language toggles.
- Fetches measurements from `aqie-back-end` to derive expected values for assertions.

**Does not:**

- Cover the alert sign-up journeys, bookmarks, mobile emulation, accessibility checks
  or the Ricardo breach validations — all of which exist only in `aqie-privatebeta-test`.

**Honest assessment:** every spec here has a same-named counterpart in
`aqie-privatebeta-test`, which is on a newer WebdriverIO version and has been
maintained nine months more recently. This repository appears redundant.

## 3. Architecture

**Pattern:** WebdriverIO 8 with Mocha and the page-object pattern. Two runner
configurations only: `wdio.conf.js` for CDP and `wdio.local.conf.js` for local Chrome.

| Component | Path | Responsibility |
|---|---|---|
| Specs | `test/specs/` | 15 journey suites |
| Page objects | `test/page-objects/` | Selectors and page interactions |
| Test data | `test/testdata/` | JSON fixtures of regions, postcodes and tooltips |
| Helpers | `test/helpers/` | `convict` config and logging |

`passwordPageLogin.js` is a helper spec that signs in through the holding page. It is
excluded from the spec list but imported by the Welsh and footer suites.

## 4. API Surface

This is a test harness and exposes no API.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-front-end` | AQIE service | `https://aqie-front-end.<ENVIRONMENT>.cdp-int.defra.cloud/` — browser base URL | Whole site under test | Holding-page password |
| `aqie-back-end` | AQIE service | `GET /measurements` | Pollutant concentrations used to derive expected page values | None (internal) |
| DEFRA UK-AIR website | External | `https://uk-air.defra.gov.uk/ajax/forecast_text_summary.php` | Forecast summary text for assertion | None |
| DEFRA UK-AIR website | External | `https://uk-air.defra.gov.uk/assets/rss/forecast.xml` | Forecast RSS feed for assertion | None |
| AWS S3 | Datastore | `RESULTS_OUTPUT_S3_PATH` | Allure report upload | CDP task role |

## 6. Consumed By (Inbound Dependencies)

Nothing consumes this repository.

## 7. Data

- **Fixtures:** JSON files under `test/testdata/` holding regions, NI and ESW postcodes,
  case-sensitivity variants and tooltip text. No personal data.
- **Live data:** forecast assertions read the public UK-AIR feeds at run time.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `ENVIRONMENT` | Selects the target CDP environment in the base URL |
| `DAQIE_PASSWORD` | Holding-page password for the service under test |
| `FORECAST_SUMMARY_URL`, `FORECAST_URL` | UK-AIR forecast sources |
| `MEASUREMENTS_API_URL` | `aqie-back-end` measurements endpoint |
| `CHROMEDRIVER_URL`, `CHROMEDRIVER_PORT` | WebDriver endpoint |
| `HTTP_PROXY`, `HTTPS_PROXY` | CDP egress proxy |
| `RESULTS_OUTPUT_S3_PATH`, `RUN_ID` | Result publishing |
| `DEBUG`, `LOG_LEVEL`, `NODE_ENV` | Diagnostics |

## 9. Hosting and Deployment

- **Platform:** DEFRA CDP. Packaged as a Docker image and run as an ECS task from the
  CDP Portal.
- **Trigger:** manual from the CDP Portal. No schedule is defined in the repository.
- **Pipelines:** `.github/workflows/publish.yml` on push to `main`;
  `check-pull-request.yml` on PR. Neither has run since November 2025.

## 10. Observability

- **Reports:** Allure, copied to `RESULTS_OUTPUT_S3_PATH` by `bin/publish-tests.sh`.
- **Logging:** `pino` with `@elastic/ecs-pino-format`.

## 11. Open Questions

- [ ] **Security.** `test/helpers/config.js` commits a working default for the holding-page
      password (`DAQIE_PASSWORD`). Remove from source and supply as a CDP secret.
- [ ] Recommend archiving. Confirm with the QA lead that `aqie-privatebeta-test` fully
      covers the public beta scenarios before doing so.
- [ ] Despite the "public beta" name the suite still signs in through a holding page.
      Confirm whether a password gate is still in front of the public service.
