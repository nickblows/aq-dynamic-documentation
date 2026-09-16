# Shared Services

Repositories that exercise or support the AQIE estate without being part of it at runtime,
plus services that do not sit cleanly in the Citizen or Data domains.

## Quality and performance testing

No suite runs on a schedule. All are triggered on demand, either from the CDP portal or by
a GitHub workflow.

| Repository | System under test | Framework | Status | Profile |
|---|---|---|---|---|
| `aqie-privatebeta-test` | `aqie-front-end` | WebdriverIO 8 / Mocha / Allure | Active — best maintained | [Profile](aqie-privatebeta-test/service-profile.md) |
| `aqie-prtr-journey-tests` | `aqie-prtr-frontend` | WebdriverIO 9 / Mocha / Allure | Active | [Profile](aqie-prtr-journey-tests/service-profile.md) |
| `aqie-privatebeta-perftest` | `aqie-front-end` UI, notify and alert services | JMeter | Active | [Profile](aqie-privatebeta-perftest/service-profile.md) |
| `aqie-privatebeta-api-perftest` | `aqie-back-end` API, Ricardo alerts | JMeter | Active | [Profile](aqie-privatebeta-api-perftest/service-profile.md) |
| `aqie-data-privatebeta-perftest` | `aqie-dataselector-frontend` UI | JMeter | Active but drifting — targets `dev` | [Profile](aqie-data-privatebeta-perftest/service-profile.md) |
| `aqie-data-priv-beta-api-perftest` | Location, monitoring station and historic data APIs | JMeter | Stale | [Profile](aqie-data-priv-beta-api-perftest/service-profile.md) |
| `aqie-publicbeta-test` | `aqie-front-end`, `aqie-back-end` | WebdriverIO 8 / Mocha | Redundant — subset of `aqie-privatebeta-test` | [Profile](aqie-publicbeta-test/service-profile.md) |
| `aqie-prtr-perftest` | Nothing — placeholder host | JMeter | Scaffolded, unconfigured | [Profile](aqie-prtr-perftest/service-profile.md) |
| `aqie-performance-test` | Nothing — test plan is 1 byte | JMeter (intended) | Abandoned | [Profile](aqie-performance-test/service-profile.md) |

### Naming caution

`aqie-privatebeta-api-perftest`, `aqie-data-privatebeta-perftest` and
`aqie-data-priv-beta-api-perftest` look like duplicates but are not. They target the citizen
API, the data selector UI and the data backend APIs respectively. The naming is the problem,
not the code.

## Archived performance forks

Four short-lived March 2025 forks of production services, created to run load tests against
an isolated copy and archived within weeks. None was superseded — their sources are all
still live.

| Repository | Fork of | Profile |
|---|---|---|
| `aqie-dataselector-perf-frontend` | `aqie-dataselector-frontend` | [Profile](aqie-dataselector-perf-frontend/service-profile.md) |
| `aqie-historicaldata-perf-backend` | `aqie-historicaldata-backend` | [Profile](aqie-historicaldata-perf-backend/service-profile.md) |
| `aqie-location-perf-backend` | `aqie-location-backend` | [Profile](aqie-location-perf-backend/service-profile.md) |
| `aqie-monitorstation-perf-backend` | `aqie-monitoringstation-backend` (never contained code) | [Profile](aqie-monitorstation-perf-backend/service-profile.md) |

## Other

| Repository | Note | Profile |
|---|---|---|
| `aqie-kpi-metrics-dashboard` | Standalone browser-side prototype. No data source, no AQIE dependency | [Profile](aqie-kpi-metrics-dashboard/service-profile.md) |

## Consolidation candidates

Identified during analysis, pending owner confirmation:

- `aqie-performance-test` — empty test plan, no pipeline, superseded within a week of creation.
- `aqie-publicbeta-test` — every spec has a newer counterpart in `aqie-privatebeta-test`.
- `aqie-prtr-perftest` — unmodified CDP template, never configured.
- `aqie-monitorstation-perf-backend` — single commit, unmodified template, zero content.
- Within `aqie-data-privatebeta-perftest`, JMeter plans v1–v4 are superseded by v5.
