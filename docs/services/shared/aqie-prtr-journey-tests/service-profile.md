# aqie-prtr-journey-tests

> WebdriverIO journey, data-validation and accessibility tests for
> `aqie-prtr-frontend` — the UK Pollutant Release and Transfer Register.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-prtr-journey-tests`](https://github.com/DEFRA/aqie-prtr-journey-tests) |
| Service domain | `Shared` |
| Service type | `Quality/Test Service` |
| Lifecycle stage | `Beta` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22.13.1` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2026-05-20` |
| Last main commit (UTC) | `2026-08-21T16:09:41Z` |
| Last analysed commit | `3916684` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Runs end-to-end browser journeys against `aqie-prtr-frontend`, entering through the
  holding page and covering the landing page, facility navigation and the download data
  pages for reporting years 2007 to 2024.
- Validates that migrated PRTR facility data rendered by the service matches the legacy
  reference data, year by year, using committed spreadsheets as the expected values.
- Downloads the published PRTR XML dataset for each year and checks the download
  completes, then validates its content.
- Runs WCAG accessibility checks over the download data pages using a vendored
  `wcag-js-v2` library and a custom Allure accessibility plugin.

**Does not:**

- Measure performance — that is `aqie-prtr-perftest` (which is not yet configured).
- Call `aqie-prtr-backend` directly; everything goes through the frontend.

## 3. Architecture

**Pattern:** WebdriverIO 9 with Mocha and the page-object pattern. Data validation is
implemented as a separate layer of utilities and validators rather than inside specs, so
the same comparison logic is reused across the seven per-year suites.

| Component | Path | Responsibility |
|---|---|---|
| Specs | `test/specs/` | 11 suites — Phase 1 E2E, migrated data check, per-year validation, downloads, accessibility |
| Page objects | `test/page-objects/` | Landing, download data and not-found pages |
| Helpers | `test/helpers/` | Facility navigation, download completion waiting, logging |
| Utilities | `test/utils/` | Excel reading, facility comparison, Allure and report writing |
| Validators | `test/validators/` | `FacilityValidator` — the comparison rules |
| Expected data | `test/test-data/`, `test/data/expected/` | Per-year reference spreadsheets and a JSON fixture |
| Runner configs | `wdio.*.js` | CDP, local, GitHub Actions and BrowserStack variants |
| Local stack | `compose.yml`, `docker/` | MongoDB, Redis, LocalStack and headless Chrome |

`FACILITY_LIMIT` caps how many facilities each per-year suite checks, so a full
validation run can be reduced to a smoke check.

## 4. API Surface

This is a test harness and exposes no API.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-prtr-frontend` | AQIE service | `https://aqie-prtr-frontend.<ENVIRONMENT>.cdp-int.defra.cloud/uk-pollutant-release-and-transfer-register/en` — the browser base URL | Whole site under test | Holding-page password |
| `aqie-prtr-frontend` | AQIE service | Landing page, facility search and detail pages | Facility names, addresses, releases and transfers for comparison | Session cookie |
| `aqie-prtr-frontend` | AQIE service | Download data pages, one per year 2007–2024 | Triggers the PRTR XML dataset download | Session cookie |
| `aqie-prtr-frontend` | AQIE service | `http://localhost:3000` under the GitHub Actions configurations | The same site, running in Docker Compose | None |
| BrowserStack | External | Remote WebDriver grid | Browser sessions | `BROWSERSTACK_USERNAME`/`BROWSERSTACK_USER`, `BROWSERSTACK_KEY` |
| AWS S3 | Datastore | `RESULTS_OUTPUT_S3_PATH` | Allure report and log upload | CDP task role |

Because everything is driven through the browser, `aqie-prtr-backend` and
`aqie-location-backend` are exercised indirectly but never addressed directly.

> `wdio.browserstack.conf.js` sets the base URL to
> `aqie-prtr-journey-tests.<env>.cdp-int.defra.cloud`, which is the test suite's own CDP
> name rather than the service under test. This looks like a copy-and-paste error.

## 6. Consumed By (Inbound Dependencies)

Nothing consumes this repository.

## 7. Data

- **Expected data:** six Excel workbooks (`PRTR_2010` through `PRTR_2024`) and a JSON
  fixture for a single facility, used as the reference for migration validation.
- **Downloaded artefacts:** `downloads/` contains fourteen committed PRTR dataset XML
  files (2011–2024) totalling around 200 MB expanded. The directory is **not** in
  `.gitignore`, so a local test run adds further downloads to the working tree.
- **Personal data:** none found. PRTR facility data is published open data covering
  operators and sites, not individuals.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `ENVIRONMENT` | Selects the target CDP environment in the base URL |
| `FACILITY_LIMIT` | Caps the number of facilities validated per year |
| `BROWSERSTACK_USERNAME`, `BROWSERSTACK_USER`, `BROWSERSTACK_KEY` | BrowserStack grid |
| `CHROMEDRIVER_URL`, `CHROMEDRIVER_PORT` | WebDriver endpoint |
| `HTTP_PROXY` | CDP egress proxy |
| `RESULTS_OUTPUT_S3_PATH`, `RUN_ID` | Result publishing |
| `DEBUG` | Diagnostics |

## 9. Hosting and Deployment

- **Platform:** DEFRA CDP. Packaged as a Docker image and run as an ECS task from the
  CDP Portal.
- **Triggers:**
  - Manual from the CDP Portal against a chosen environment.
  - `.github/workflows/journey-tests.yml` — `workflow_dispatch` or `workflow_call`, using
    `DEFRA/cdp-node-journey-test-suite-template/run-journey-tests`, so the service repository
    can call this suite from its own pipeline.
  - `.github/workflows/publish.yml` builds and publishes the image on push to `main`.
- No schedule is defined in the repository.

## 10. Observability

- **Reports:** Allure, generated as a single-file report and copied to
  `RESULTS_OUTPUT_S3_PATH`, together with the contents of `logs/`.
- **Custom reporting:** `MigrationValidationReportWriter` and `ReportWriter` produce
  per-year data comparison summaries attached to the Allure report.
- **Failure signalling:** a `FAILED` marker file causes the entrypoint to exit non-zero.

## 11. Open Questions

- [ ] **Security.** The specs hardcode the holding-page password inline as a literal in
      `Phase1e2e.js` and `MigratedDataCheckE2E.js`. The value is not recorded here. Move it
      to an environment variable supplied from a CDP secret.
- [ ] `downloads/` holds roughly 200 MB of committed dataset XML and is not gitignored.
      Confirm whether those files are genuinely needed as fixtures; if not, remove them and
      ignore the directory.
- [ ] `wdio.browserstack.conf.js` points at the test suite's own hostname rather than
      `aqie-prtr-frontend`. Confirm and correct.
- [ ] `compose.yml` is still the unedited CDP template with the services under test commented
      out, so the GitHub Actions configurations targeting `localhost:3000` cannot currently
      start anything. Is the GitHub path in use?
- [ ] Expected-value spreadsheets exist for 2010–2024 but the specs cover 2007 onwards.
      Where do the pre-2010 expectations come from?
