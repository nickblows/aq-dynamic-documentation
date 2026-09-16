# aqie-performance-test

> An abandoned first attempt at JMeter performance testing for the air quality service.
> The test plan it contains is empty.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-performance-test`](https://github.com/DEFRA/aqie-performance-test) |
| Service domain | `Shared` |
| Service type | `Quality/Test Service` |
| Lifecycle stage | `Prototype/PoC` — abandoned |
| Primary language | None detected |
| Runtime | None — no Dockerfile, no entrypoint, no pipeline |
| Default branch | `main` |
| Created (UTC) | `2024-08-15` |
| Last main commit (UTC) | `2024-08-21T12:17:55Z` |
| Last analysed commit | `ad5f448` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Inactive` |

## 2. Purpose and Responsibilities

**Intended:** JMeter load testing of the citizen air quality journey — location search,
location list search, and ESW and NI postcode search.

**Actual:** the repository holds five CSV data files and a single `.jmx` file that is
one byte long and contains no test plan. There is no README, no Dockerfile, no
`entrypoint.sh` and no GitHub Actions workflow. Nothing here can run.

The repository was created six days before `aqie-privatebeta-perftest` and last touched
the day the latter began. The CSV files (`ESWPostcode.csv`, `ESWPostcodeList.csv`,
`LocationSearch.csv`, `LocationListSearch.csv`, `NIPostcode.csv`) are identical in
purpose and near-identical in content to files carried forward into
`aqie-privatebeta-perftest/scenarios/`. This repository was superseded by that one.

## 3. Architecture

None. There is no runnable component — only data files and a broken test plan.

## 4. API Surface

This is a test harness and exposes no API.

## 5. Consumes (Outbound Dependencies)

None that can be evidenced. The only `.jmx` file is empty, so no target hosts or
endpoints are recorded anywhere in the repository. The CSV fixtures imply an intent to
test the citizen location and postcode search journeys on `aqie-front-end`, but that
intent is not expressed in any runnable artefact.

## 6. Consumed By (Inbound Dependencies)

Nothing consumes this repository.

## 7. Data

- **Fixtures:** UK place names with counties, place names alone, and ESW and NI postcodes.
  All public reference data; no personal data and no credentials.

## 8. Configuration

No configuration is defined — there is no Dockerfile, entrypoint or properties file, so
no environment variables are read.

## 9. Hosting and Deployment

Not deployed. No Dockerfile and no GitHub Actions workflow exist, so no image has ever
been published and the suite cannot be run from the CDP Portal.

## 10. Observability

None.

## 11. Open Questions

- [ ] Recommend archiving. The repository has been dormant since August 2024, contains no
      working test plan, and its fixtures live on in `aqie-privatebeta-perftest`.
- [ ] Confirm the one-byte `.jmx` file is a mistake rather than a stripped artefact that
      should be recovered from history.
