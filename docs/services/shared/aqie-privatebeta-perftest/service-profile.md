# aqie-privatebeta-perftest

> JMeter load, stress, endurance and capacity tests for the citizen-facing
> `aqie-front-end` service, run as an ECS task from the CDP Portal.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-privatebeta-perftest`](https://github.com/DEFRA/aqie-privatebeta-perftest) |
| Service domain | `Shared` |
| Service type | `Quality/Test Service` |
| Lifecycle stage | `Production` (supports the live service) |
| Primary language | Shell and JMeter XML (GitHub reports HTML because of the committed reports) |
| Runtime | Apache JMeter in `defradigital/cdp-perf-test-docker` |
| Default branch | `main` |
| Created (UTC) | `2024-08-21` |
| Last main commit (UTC) | `2026-08-19T07:54:43Z` |
| Last analysed commit | `f710950` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Applies concurrent browser-like load to `aqie-front-end` across four thread groups:
  location search, location-list search, NI postcode search and ESW postcode search.
- Covers distinct test shapes in separate scenario files — smoke, load, stress,
  capacity (including a 3x capacity run), two-hour endurance, and a scenario written
  specifically to reproduce a production caching defect on bookmarked URLs.
- Load-tests the alert sign-up journey end to end, including the alert and notify
  service APIs reached through the CDP ephemeral protected gateway.
- Load-tests bookmarked location URLs, which bypass the search journey and hit the
  location page cache directly.

**Does not:**

- Assert functional correctness beyond basic response assertions — that is
  `aqie-privatebeta-test`.
- Test backend APIs in isolation — that is `aqie-privatebeta-api-perftest`.

## 3. Architecture

**Pattern:** a JMeter scenario library plus a shell entrypoint. The Docker image layers
the `scenarios/` folder onto the DEFRA CDP performance-test base image; `entrypoint.sh`
runs JMeter headless, generates the HTML dashboard, and copies `index.html` to S3.

| Component | Path | Responsibility |
|---|---|---|
| Scenarios | `scenarios/*.jmx` | ~20 JMeter test plans, one per test shape |
| Data files | `scenarios/*.csv` | Postcodes, location names, bookmark URLs, mobile numbers |
| Runner | `entrypoint.sh` | Runs JMeter and publishes results |
| JMeter config | `jmeter.properties`, `user.properties`, `log4j2.xml`, etc. | Engine tuning |
| Committed reports | `index.html`, `OverTime.html`, `ResponseTimes.html` | Historic result snapshots |

The scenario file is **hardcoded in `entrypoint.sh`**, so only one plan runs per image
build. The `TEST_SCENARIO` variable names the report but does not select the plan.

## 4. API Surface

This is a test harness and exposes no API.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-front-end` | AQIE service | `https://aqie-front-end.perf-test.cdp-int.defra.cloud` (hardcoded in the plans) | All journeys below | Holding-page form post |
| `aqie-front-end` | AQIE service | `GET /`, `POST /?userId=&utm_source=`, `GET /check-local-air-quality`, `GET /search-location` | Entry and holding-page journey | Session cookie |
| `aqie-front-end` | AQIE service | `POST /location`, `GET /location/{locationId}` | Location search and results | Session cookie |
| `aqie-front-end` | AQIE service | `GET /pollutants/{pollutant}`, `GET /air-pollution-breaches` | Pollutant detail and breaches pages | Session cookie |
| `aqie-front-end` | AQIE service | `GET`/`POST /notify/register/{sms-mobile-number\|email-details}`, `POST /notify/register/sms-send-activation`, `POST /notify/register/sms-verify-code`, `POST /notify/register/sms-confirm-details`, `GET /notify/register/check-max-alerts`, `GET /notify/register/email-send-new-link`, `GET /notify/unsubscribe-success` | Full alert sign-up and unsubscribe journey | Session cookie |
| `aqie-notify-service` | AQIE service | `GET https://ephemeral-protected.api.perf-test.cdp-int.defra.cloud/aqie-notify-service/subscribe/validate-link/{token}` | Email verification token validation | CDP ephemeral gateway |
| `aqie-alert-back-end-service` | AQIE service | `POST .../aqie-alert-back-end-service/setup-alert`, `DELETE .../aqie-alert-back-end-service/opt-out-email-alert` | Alert creation and opt-out | CDP ephemeral gateway |
| Google Tag Manager / Analytics | External | `www.googletagmanager.com`, `region1.google-analytics.com` | Recorded analytics beacons replayed by the debug plan | None |
| AWS S3 | Datastore | `RESULTS_OUTPUT_S3_PATH` | JMeter HTML dashboard upload | CDP task role |

> The `/subscribe/validate-link/{token}`, `/setup-alert` and `/opt-out-email-alert`
> endpoints and the `ephemeral-protected.api` gateway pattern are **not** currently in
> [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 6. Consumed By (Inbound Dependencies)

Nothing consumes this repository.

## 7. Data

- **Fixtures:** CSV files driving the thread groups — ESW and NI postcodes, location
  and county names, bookmarked location URLs with expected page headings, and single
  pollutant names.
- **Mobile numbers:** `Mobile_ESWLocation.csv` and `Mobile_NIPostcode.csv` supply
  sequential numbers in the Ofcom `07000 0xxxxx` drama-and-fiction range. These are
  reserved for testing and are not real subscribers.
- **Environment:** the plans hardcode `perf-test` hosts rather than reading
  `ENVIRONMENT`, so they cannot be pointed at another environment without editing.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `ENVIRONMENT` | Passed to JMeter as the `env` property (largely unused; hosts are hardcoded) |
| `TEST_SCENARIO` | Names the report and log files |
| `RUN_ID` | CDP run identifier echoed to the log |
| `RESULTS_OUTPUT_S3_PATH`, `S3_ENDPOINT` | Result publishing |
| `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | AWS access (LocalStack only when run locally) |
| `JM_HOME` | JMeter working directory |

## 9. Hosting and Deployment

- **Platform:** DEFRA CDP. The image is run as an ECS task from the CDP Portal, which
  provisions the load generator and passes the result bucket path.
- **Trigger:** manual from the CDP Portal. No schedule is defined in the repository.
- **Pipelines:** `.github/workflows/publish.yml` builds and publishes on push to `main`
  via `DEFRA/cdp-build-action/build-test`.
- **Local:** `docker build` plus LocalStack S3, as documented in the README.

## 10. Observability

- **Reports:** the JMeter HTML dashboard. Only `index.html` is copied to
  `RESULTS_OUTPUT_S3_PATH` because the CDP Portal expects a single HTML file, so the
  supporting assets and the raw CSV results are discarded on each run.
- **Logs:** JMeter writes to `logs/perftest-<scenario>.log` inside the container; these
  are not published.

## 11. Open Questions

- [ ] The scenario file name is hardcoded in `entrypoint.sh`, so choosing a different
      test shape needs a code change and a rebuild. Should `TEST_SCENARIO` select the plan,
      as it already does in `aqie-prtr-perftest`?
- [ ] Target hosts are hardcoded to `perf-test`. Confirm the suite is never expected to run
      against `dev` or `test`.
- [ ] Only `index.html` is published, so the dashboard loses its charts and the raw results
      are lost. Should the whole report directory be uploaded, as the data suites do?
- [ ] Several very large scenario files (2 MB each) are near-identical recorded variants.
      Confirm which are current and prune the rest.
- [ ] `AQIE_DisplayAirQualityResult_DebugV2.jmx` replays recorded Google Analytics beacons
      containing a real measurement ID and client identifier. Confirm this is acceptable, or
      strip the third-party requests.
