# aqie-data-priv-beta-api-perftest

> JMeter API load tests for the data-side backends — location, monitoring station and
> historic data — with no user interface involved.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-data-priv-beta-api-perftest`](https://github.com/DEFRA/aqie-data-priv-beta-api-perftest) |
| Service domain | `Shared` |
| Service type | `Quality/Test Service` |
| Lifecycle stage | `Beta` |
| Primary language | Shell and JMeter XML |
| Runtime | Apache JMeter in `defradigital/cdp-perf-test-docker` |
| Default branch | `main` |
| Created (UTC) | `2025-04-11` |
| Last main commit (UTC) | `2025-05-07T22:45:49Z` |
| Last analysed commit | `d0c93d0` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Inactive` |

## 2. Purpose and Responsibilities

**Does:**

- Applies load to the three data-domain backend APIs that sit behind the historic data
  download journey, so their latency can be measured without frontend rendering cost.

**Does not:**

- Exercise `aqie-dataselector-frontend` — that is `aqie-data-privatebeta-perftest`.
- Cover the citizen-facing services — those are the `aqie-privatebeta-*` suites.

Despite the similar name, this is **not** a duplicate of `aqie-data-privatebeta-perftest`.
That suite drives the user interface; this one drives the APIs underneath it. Its one
scenario has not changed since May 2025, so it has not kept pace with the endpoints added
to `aqie-historicaldata-backend` since.

## 3. Architecture

**Pattern:** a single JMeter plan plus a shell entrypoint, layered onto the DEFRA CDP
performance-test base image.

| Component | Path | Responsibility |
|---|---|---|
| Scenario | `scenarios/AQIE_DataStream_APIs.jmx` | One thread group covering four requests |
| Data files | `scenarios/Postcode.csv`, `scenarios/Frequency.csv` | Postcodes and Hourly/Daily selector |
| Runner | `entrypoint.sh` | Runs JMeter and publishes results |

## 4. API Surface

This is a test harness and exposes no API.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-monitoringstation-backend` | AQIE service | `GET https://aqie-monitoringstation-backend.perf-test.cdp-int.defra.cloud/monitoringstation/location={postcode}&miles=50` | Nearby monitoring stations within a radius | None (internal) |
| `aqie-location-backend` | AQIE service | `GET https://aqie-location-backend.perf-test.cdp-int.defra.cloud/osnameplaces/userLocation={postcode}` | Gazetteer matches for a user-entered location | None (internal) |
| `aqie-historicaldata-backend` | AQIE service | `POST https://aqie-historicaldata-backend.perf-test.cdp-int.defra.cloud/AtomHistoryHourlydata/` | Hourly historic measurement extract request | None (internal) |
| `aqie-historicaldata-backend` | AQIE service | `POST .../AtomHistoryexceedence/` | Exceedence data extract request | None (internal) |
| AWS S3 | Datastore | `RESULTS_OUTPUT_S3_PATH` | JMeter dashboard and CSV results upload | CDP task role |

> The **GET** forms used here differ from the POST forms recorded in
> [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml) for
> `/monitoringstation` and `/osnameplaces`. Either both verbs are supported or the test
> plan has drifted — worth confirming against the service source.

## 6. Consumed By (Inbound Dependencies)

Nothing consumes this repository.

## 7. Data

- **Fixtures:** a short list of UK postcodes and a Hourly/Daily frequency selector. No
  personal data.
- **Environment:** hosts are hardcoded to `perf-test` in the plan.

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
- **Pipelines:** `.github/workflows/publish.yml` on push to `main`. No build since May 2025.

## 10. Observability

- **Reports:** the raw CSV results file and the whole JMeter HTML dashboard directory are
  copied to `RESULTS_OUTPUT_S3_PATH`.

## 11. Open Questions

- [ ] The plan covers only two of the nine `aqie-historicaldata-backend` Atom endpoints and
      predates the custom dataset work. Is it still representative?
- [ ] Confirm whether `/monitoringstation` and `/osnameplaces` accept GET as well as POST.
- [ ] The repository name is easily confused with `aqie-data-privatebeta-perftest`. Consider
      renaming to make the API-versus-UI split obvious.
- [ ] Has this suite been run since May 2025? If not, confirm whether it should be revived
      or archived.
