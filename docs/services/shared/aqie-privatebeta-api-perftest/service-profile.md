# aqie-privatebeta-api-perftest

> JMeter API load tests for the citizen data path — `aqie-back-end` and the Ricardo
> UK-AIR alerts API — with no browser involved.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-privatebeta-api-perftest`](https://github.com/DEFRA/aqie-privatebeta-api-perftest) |
| Service domain | `Shared` |
| Service type | `Quality/Test Service` |
| Lifecycle stage | `Production` (supports the live service) |
| Primary language | Shell and JMeter XML |
| Runtime | Apache JMeter in `defradigital/cdp-perf-test-docker` |
| Default branch | `main` |
| Created (UTC) | `2024-09-06` |
| Last main commit (UTC) | `2026-07-23T22:15:02Z` |
| Last analysed commit | `30ce55d` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Applies load directly to `aqie-back-end` read endpoints, bypassing the front end so
  API latency can be measured in isolation.
- Applies load to the Ricardo UK-AIR high-alert (DAQI alerts) API, including the token
  exchange that precedes it, to confirm the upstream provider can sustain the request
  rate the alert service needs.

**Does not:**

- Exercise any user interface — that is `aqie-privatebeta-perftest`.
- Cover the data-download APIs — that is `aqie-data-priv-beta-api-perftest`.

This repository is the API counterpart of `aqie-privatebeta-perftest`, not a duplicate
of it. The two target different layers of the same service.

## 3. Architecture

**Pattern:** JMeter scenarios plus a shell entrypoint, layered onto the DEFRA CDP
performance-test base image. Each plan uses a single thread group.

| Component | Path | Responsibility |
|---|---|---|
| Scenarios | `scenarios/*.jmx` | Four plans — two backend API, two high-alert API |
| Data files | `scenarios/HighAlertStartEndDate.csv` | Date ranges for the alerts query |
| Runner | `entrypoint.sh` | Runs JMeter and publishes results |

`scenarios/test.jmx` is a copy of `AQIE_DisplayAirQualityResult_APIs_V2.jmx` and appears
to be a leftover. The entrypoint hardcodes the high-alert plan, so the plain backend API
plans do not run from the published image without a code change.

## 4. API Surface

This is a test harness and exposes no API.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-back-end` | AQIE service | `GET https://aqie-back-end.perf-test.cdp-int.defra.cloud/forecasts` | Forecast records | None (internal) |
| `aqie-back-end` | AQIE service | `GET https://aqie-back-end.perf-test.cdp-int.defra.cloud/measurements` | Pollutant concentrations and DAQI bands | None (internal) |
| Ricardo UK-AIR | External API | `POST https://uk-air-api.staging.rcdo.co.uk/api/login_check` | Credentials exchanged for bearer token | Email/password form post |
| Ricardo UK-AIR | External API | `GET https://api-ukair.defra.gov.uk/api/daqi_alerts` | DAQI alert records over a date range | Bearer token |
| AWS S3 | Datastore | `RESULTS_OUTPUT_S3_PATH` | JMeter HTML dashboard upload | CDP task role |

> The plans authenticate against the Ricardo **staging** host but then query the
> **production** host for alerts. This mismatch is worth confirming with the service
> owner — it mirrors an inconsistency already recorded for `aqie-back-end`.

## 6. Consumed By (Inbound Dependencies)

Nothing consumes this repository.

## 7. Data

- **Fixtures:** `HighAlertStartEndDate.csv` supplies the start and end dates for the
  alerts query. No personal data.
- **Environment:** hosts are hardcoded to `perf-test` in the plans rather than read from
  `ENVIRONMENT`.
- **Credentials:** the Ricardo login request sends a `password` argument. The value is
  carried in the plan rather than injected at run time — see section 11.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `ENVIRONMENT` | Passed to JMeter as the `env` property |
| `TEST_SCENARIO` | Names the report and log files |
| `RUN_ID` | CDP run identifier echoed to the log |
| `RESULTS_OUTPUT_S3_PATH`, `S3_ENDPOINT` | Result publishing |
| `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | AWS access (LocalStack only when run locally) |
| `JM_HOME` | JMeter working directory |

## 9. Hosting and Deployment

- **Platform:** DEFRA CDP. Run as an ECS task from the CDP Portal.
- **Trigger:** manual from the CDP Portal. No schedule is defined in the repository.
- **Pipelines:** `.github/workflows/publish.yml` on push to `main`.

## 10. Observability

- **Reports:** JMeter HTML dashboard; only `index.html` is copied to
  `RESULTS_OUTPUT_S3_PATH`, so charts and raw CSV results are discarded.
- **Logs:** written inside the container only.

## 11. Open Questions

- [ ] **Security.** The Ricardo `login_check` plans carry a `password` argument inside the
      committed `.jmx` files. Confirm whether a real credential is embedded; if so, rotate it
      and move to a JMeter property supplied from a CDP secret. The value is not recorded here.
- [ ] Authentication targets the Ricardo staging host while the alerts query targets the
      production host. Which is correct?
- [ ] The entrypoint hardcodes the high-alert plan, so the `/forecasts` and `/measurements`
      load tests never run from the published image. Was that intended?
- [ ] `scenarios/test.jmx` duplicates another plan and can probably be deleted.
