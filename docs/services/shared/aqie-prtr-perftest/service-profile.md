# aqie-prtr-perftest

> A scaffolded JMeter performance test suite for the PRTR service. The CDP template has
> been created but never configured, so it currently tests nothing.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-prtr-perftest`](https://github.com/DEFRA/aqie-prtr-perftest) |
| Service domain | `Shared` |
| Service type | `Quality/Test Service` |
| Lifecycle stage | `Prototype/PoC` |
| Primary language | Shell and JMeter XML |
| Runtime | Apache JMeter in `defradigital/cdp-perf-test-docker` |
| Default branch | `main` |
| Created (UTC) | `2026-06-19` |
| Last main commit (UTC) | `2026-06-19T12:09:52Z` |
| Last analysed commit | `a6688f5` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Inactive` |

## 2. Purpose and Responsibilities

**Intended:** JMeter performance testing of the PRTR service — presumably
`aqie-prtr-frontend` and `aqie-prtr-backend`.

**Actual:** the repository is the unmodified DEFRA CDP performance test template. The
single scenario, `scenarios/test.jmx`, issues one `GET /` against a placeholder host of
`service-name.<env>.cdp-int.defra.cloud`, and the README still instructs the reader to
replace `service-name` in the Compose file. No PRTR endpoint, journey or data file has
been added. Everything in the repository was committed on the day it was created and
nothing has changed since.

The scaffolding itself is sound and is a better starting point than the older AQIE perf
suites, because `TEST_SCENARIO` selects the plan and the target host is parameterised
rather than hardcoded. It simply has not been filled in.

## 3. Architecture

**Pattern:** the CDP JMeter template — a scenarios folder plus a shell entrypoint layered
onto `defradigital/cdp-perf-test-docker`.

| Component | Path | Responsibility |
|---|---|---|
| Scenario | `scenarios/test.jmx` | Template placeholder — one GET against a parameterised host |
| Runner | `entrypoint.sh` | Selects the plan from `TEST_SCENARIO`, runs JMeter, publishes results |
| Local stack | `compose.yml`, `compose/` | LocalStack, Redis and a placeholder service container |

Unlike the older AQIE perf suites, the entrypoint passes `domain`, `port` and `protocol`
to JMeter as properties, so a completed plan could be pointed at any environment without
a rebuild.

## 4. API Surface

This is a test harness and exposes no API.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| Placeholder | — | `GET https://service-name.<ENVIRONMENT>.cdp-int.defra.cloud/`, overridable via `SERVICE_ENDPOINT` | None — template request | None |
| AWS S3 | Datastore | `RESULTS_OUTPUT_S3_PATH` | JMeter dashboard and CSV results upload | CDP task role |

No AQIE service is currently exercised.

## 6. Consumed By (Inbound Dependencies)

Nothing consumes this repository.

## 7. Data

No test data or fixtures exist. `user.properties` is empty. No personal data and no
credentials.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `ENVIRONMENT` | Used to build the default target hostname |
| `SERVICE_ENDPOINT`, `SERVICE_PORT`, `SERVICE_URL_SCHEME` | Override the target host, port and scheme |
| `TEST_SCENARIO` | Selects which `.jmx` plan to run |
| `RUN_ID` | CDP run identifier echoed to the log |
| `RESULTS_OUTPUT_S3_PATH`, `S3_ENDPOINT` | Result publishing |
| `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | AWS access (LocalStack only when run locally) |
| `SERVICE_VERSION` | Image tag for the service under test in Compose |
| `JM_HOME` | JMeter working directory |

## 9. Hosting and Deployment

- **Platform:** DEFRA CDP. Would run as an ECS task from the CDP Portal.
- **Trigger:** manual from the CDP Portal. No schedule is defined.
- **Pipelines:** `.github/workflows/publish.yml` on push to `main`. The workflow skips the
  very first run, and since no further commits have been made, no image has been published.
- **Local:** `docker compose up --build` brings up LocalStack, Redis, a placeholder service
  and the test runner.

## 10. Observability

- **Reports:** the entrypoint copies the raw CSV results file and the whole JMeter HTML
  dashboard directory to `RESULTS_OUTPUT_S3_PATH`.
- **Diagnostics:** the entrypoint runs with `set -x`, so every command is traced to the log.

## 11. Open Questions

- [ ] Is PRTR performance testing still planned? If so, the template needs real scenarios and
      the placeholder `service-name` references replaced.
- [ ] If not, recommend archiving so the estate does not carry an empty suite.
- [ ] Which PRTR component is the intended system under test — the frontend download journey,
      the backend API, or both?
