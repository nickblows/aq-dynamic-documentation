# aqie-dataselector-perf-frontend

> A March 2025 fork of `aqie-dataselector-frontend`, created so that performance testing could
> drive the data selector journey against a disposable copy. Archived in April 2025.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-dataselector-perf-frontend`](https://github.com/DEFRA/aqie-dataselector-perf-frontend) |
| Service domain | `Shared` |
| Service type | `Quality/Test Service` |
| Lifecycle stage | `Archived` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2025-03-17` |
| Last main commit (UTC) | `2025-04-10T15:16:14Z` |
| Last analysed commit | `cd566d8a` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Archived` |

## 2. Purpose and Responsibilities

> **Archived.** A performance-test copy of `aqie-dataselector-frontend`. Not superseded — the
> service it copied is still live. Retained for historical reference. Do not deploy.

**The `*-perf-*` pattern.** This is one of four throwaway forks created within two hours of
each other on 17 March 2025 so that load could be driven without touching shared environments;
the others are `aqie-location-perf-backend`, `aqie-monitorstation-perf-backend` and
`aqie-historicaldata-perf-backend`. See
[`aqie-location-perf-backend`](../aqie-location-perf-backend/service-profile.md) for the full
description of the pattern. This fork was the longest-lived of the four, receiving a second
round of changes on 10 April 2025 on a branch named `Perf-april10`.

**Does:**

- Reproduces the data selector journey as it stood in spring 2025: search for a location,
  disambiguate between multiple matches, view a monitoring station, and request historic data
  downloads by year, pollutant and frequency.

**Does not:**

- Contain any load-testing harness, scenario definitions or results.
- Isolate itself from the shared environments. This is the important finding: its configuration
  points at the **production** backends in the `dev` environment —
  `aqie-location-backend`, `aqie-monitoringstation-backend` and `aqie-historicaldata-backend` —
  and not at the three perf backend forks created alongside it. Load driven through this
  frontend would have landed on the real services.

It also retains a reference to the archived `aqie-data-service-backend` under a transposed
hostname (`aiqe-dataservice-backend`) that no longer resolves.

## 3. Architecture

- **Pattern:** Hapi frontend on the CDP Node.js frontend template — Nunjucks server-side
  rendering, GOV.UK Frontend, webpack asset build, Redis-backed session cache.

| Component | Path | Responsibility |
|---|---|---|
| Server routes | `src/server/` | One folder per page: search, multiple locations, monitoring station, download, table rendering |
| Client | `src/client/` | Progressive enhancement scripts and SCSS |
| Config | `src/config/` | Two `convict` schemas, `index.js` and `config.js`, holding backend URLs |

## 4. API Surface

Page routes rather than an API. Journey pages include `/`, `/search-location` (and
`searchagain`), `/multiplelocations`, `/location/{id}`, `/monitoring-station`,
`/stationdetails/...`, `/rendertable/{year}` and `/downloaddata/{year}/{poll}/{freq}`, plus the
standard footer pages (`/about`, `/accessibility`, `/cookies`, `/privacy`), `/health` and
static asset routes.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-location-backend` | AQIE service | `GET /osnameplaces/userLocation=` | Place name in; candidate locations out | CDP internal network |
| `aqie-monitoringstation-backend` | AQIE service | `GET /monitoringstation/location=` | Nearest stations for a location | CDP internal network |
| `aqie-historicaldata-backend` | AQIE service | `AtomHistoryHourlydata`, `AtomHistoryexceedence` | Historic measurements and exceedence data | CDP internal network |
| `aqie-data-service-backend` | AQIE service (archived) | `/osnameplaces/userLocation=` | Dead configuration; host no longer exists | — |
| Redis | Datastore | Session cache | Server-side session state | `REDIS_PASSWORD` |

## 6. Consumed By (Inbound Dependencies)

None. It was driven directly by load-testing tooling.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** Redis only, for the session cache. No database of its own.
- **Retention / refresh:** session TTL from `SESSION_CACHE_TTL` and `SESSION_COOKIE_TTL`.

## 8. Configuration

Variable **names** only.

| Variable | Purpose |
|---|---|
| `PORT`, `NODE_ENV`, `ENVIRONMENT`, `SERVICE_VERSION` | Runtime identity |
| `BACKEND_API_URL` | Backend base URL |
| `REDIS_HOST`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_TLS`, `REDIS_KEY_PREFIX` | Session cache |
| `SESSION_CACHE_ENGINE`, `SESSION_CACHE_NAME`, `SESSION_CACHE_TTL`, `USE_SINGLE_INSTANCE_CACHE` | Session cache behaviour |
| `SESSION_COOKIE_PASSWORD`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_TTL` | Session cookie |
| `ASSET_PATH`, `STATIC_CACHE_TIMEOUT` | Static assets |
| `CDP_HTTP_PROXY`, `CDP_HTTPS_PROXY` | CDP egress proxy |
| `ENABLE_SECURE_CONTEXT`, `TRUSTSTORE_ONE` | TLS trust store |
| `ENABLE_METRICS`, `TRACING_HEADER` | Observability |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |

Backend hostnames are hardcoded as `convict` defaults rather than being supplied per
environment, which is how the stale `aqie-data-service-backend` reference survived.

## 9. Hosting and Deployment

- **Platform:** DEFRA CDP on AWS ECS, intended for the `perf-test` environment.
- **Container:** CDP Node.js base images; development and production stages.
- **Pipelines:** the standard CDP set — `check-pull-request.yml`, `publish.yml`,
  `publish-hotfix.yml`, with SonarCloud analysis.

## 10. Observability

- **Logging:** `pino` via `hapi-pino` with `@elastic/ecs-pino-format`.
- **Tracing:** `@defra/hapi-tracing`.
- **Metrics:** `aws-embedded-metrics`.

## 11. Open Questions

- [ ] Confirm whether load was in fact driven against the `dev` instances of the production
      backends. If so, the three perf backend forks served no purpose and any conclusions drawn
      about backend capacity need re-reading in that light.
- [ ] Where are the load-test scripts and results for the March and April 2025 runs?
- [ ] What changed on the `Perf-april10` branch, and was it a fix found by the testing that
      should also have been applied to `aqie-dataselector-frontend`? This is the one place in
      the four perf forks where useful findings might have been captured in code.
- [ ] Confirm the repository can be deleted. It is a stale copy of a live service, holds dead
      configuration, and will not receive dependency patches.
