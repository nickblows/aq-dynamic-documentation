# aqie-data-privatebeta-perftest

> JMeter load tests for the historic data download journey — the `aqie-dataselector-frontend`
> user interface and the S3 files it hands users on to.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-data-privatebeta-perftest`](https://github.com/DEFRA/aqie-data-privatebeta-perftest) |
| Service domain | `Shared` |
| Service type | `Quality/Test Service` |
| Lifecycle stage | `Beta` |
| Primary language | Shell and JMeter XML |
| Runtime | Apache JMeter in `defradigital/cdp-perf-test-docker` |
| Default branch | `main` |
| Created (UTC) | `2025-04-03` |
| Last main commit (UTC) | `2026-02-05T09:14:40Z` |
| Last analysed commit | `adff3e0` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Monitoring` |

## 2. Purpose and Responsibilities

**Does:**

- Applies concurrent load to the `aqie-dataselector-frontend` download journey: postcode
  and location search, station details, per-pollutant and per-frequency extracts, and the
  year-by-year AURN downloads.
- Follows the journey through to the presigned S3 URLs the service issues, so download
  throughput from the `aqie-historicaldata-backend` bucket is measured as well as page latency.
- Covers the custom dataset builder added in the latest plan — pollutant selection, year
  and location selection, the no-JavaScript download path, and the email-request path.

**Does not:**

- Call the data APIs directly — that is `aqie-data-priv-beta-api-perftest`.
- Assert data correctness; assertions are limited to response validity.

## 3. Architecture

**Pattern:** JMeter scenarios plus a shell entrypoint, layered onto the DEFRA CDP
performance-test base image.

| Component | Path | Responsibility |
|---|---|---|
| Scenarios | `scenarios/AQIE_GetAirPollutionData_v1..v5.jmx` | Five successive versions of one plan |
| Data files | `scenarios/*.csv` | Postcodes, locations, local authorities, pollutant names |
| Runner | `entrypoint.sh` | Runs JMeter and publishes results |

Versions v1 to v4 are near-identical and target `perf-test`; v5 is the current plan,
targets `dev`, and adds seven thread groups for the custom dataset journey. Only v5 is
referenced by the entrypoint.

## 4. API Surface

This is a test harness and exposes no API.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-dataselector-frontend` | AQIE service | `https://aqie-dataselector-frontend.dev.cdp-int.defra.cloud` in v5; `...perf-test...` in v1–v4 | Whole download journey | Session cookie |
| `aqie-dataselector-frontend` | AQIE service | `GET /`, `GET /hubpage`, `GET /search-location`, `GET`/`POST /multiplelocations`, `GET /stationdetails/{station}` | Search and station selection | Session cookie |
| `aqie-dataselector-frontend` | AQIE service | `GET /rendertable/{year}`, `GET /downloaddata/{pollutant}/{Hourly\|Daily}` | Station data table and extract requests | Session cookie |
| `aqie-dataselector-frontend` | AQIE service | `GET /customdataset`, `GET /airpollutant`, `POST /addpollutants`, `GET`/`POST /year-aurn`, `GET`/`POST /location-aurn` | Custom dataset builder | Session cookie |
| `aqie-dataselector-frontend` | AQIE service | `POST /download_dataselector`, `POST /download_dataselectornojs`, `GET /emailrequest`, `POST /emailrequest/confirm`, `GET /download_aurn/{year}` | Download and email-delivery paths | Session cookie |
| `aqie-historicaldata-backend` S3 bucket | Datastore | `dev-aqie-historicaldata-backend-*.s3.eu-west-2.amazonaws.com` (v5) and `perf-test-aqie-historicaldata-backend-*` (v1–v4) | Measurement CSV and AURN ZIP extracts | Presigned URL |
| AWS S3 | Datastore | `RESULTS_OUTPUT_S3_PATH` | JMeter dashboard and CSV results upload | CDP task role |

> None of the `aqie-dataselector-frontend` routes above appear in
> [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml), which currently
> records only that service's outbound edges. They are a useful inventory of its surface.

## 6. Consumed By (Inbound Dependencies)

Nothing consumes this repository.

## 7. Data

- **Fixtures:** CSV files of UK postcodes, place names, London borough local-authority
  names and pollutant names. All public reference data; no personal data.
- **Downloaded artefacts:** the plans request real measurement CSV and AURN ZIP extracts
  from the historic data bucket during the run.
- **Environment:** the current plan targets `dev`, not `perf-test`. See section 11.

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

- **Reports:** both the raw CSV results file and the whole JMeter HTML dashboard directory
  are copied to `RESULTS_OUTPUT_S3_PATH`. This is more complete than the citizen-side perf
  suites, which publish only `index.html`.

## 11. Open Questions

- [ ] **Security — priority.** All five `.jmx` files contain recorded AWS presigned S3 URLs
      with `X-Amz-Security-Token` and `X-Amz-Credential` query parameters — that is, temporary
      STS credentials for the historic data buckets committed to a public repository. The
      values are not recorded here. They should be treated as exposed, revoked, and the
      recordings parameterised so presigned URLs are extracted at run time.
- [ ] The current plan (v5) targets the `dev` environment. Confirm whether performance testing
      is intentionally run against `dev` rather than `perf-test`.
- [ ] Plans v1 to v4 appear superseded by v5 and could be removed.
- [ ] Some plans refer to `aqie-dataselector-perf-frontend`, a repository that is now archived.
      Confirm those references are historic only.
