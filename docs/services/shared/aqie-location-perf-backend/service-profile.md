# aqie-location-perf-backend

> A March 2025 fork of `aqie-location-backend`, created so that performance testing could run
> against a disposable copy of the service. Archived within days.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-location-perf-backend`](https://github.com/DEFRA/aqie-location-perf-backend) |
| Service domain | `Shared` |
| Service type | `Quality/Test Service` |
| Lifecycle stage | `Archived` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2025-03-17` |
| Last main commit (UTC) | `2025-03-20T15:39:56Z` |
| Last analysed commit | `1ea50ace` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Archived` |

## 2. Purpose and Responsibilities

> **Archived.** A performance-test copy of `aqie-location-backend`. Not superseded — the
> service it copied is still live. Retained for historical reference. Do not deploy.

**The `*-perf-*` pattern.** In March 2025 the team created four throwaway forks of data
selector services so that load could be driven against them without touching the shared `dev`
and `test` environments: this repository, `aqie-monitorstation-perf-backend`,
`aqie-historicaldata-perf-backend` and `aqie-dataselector-perf-frontend`. All four were created
within two hours of each other on 17 March 2025, all four were abandoned within weeks, and all
four are archived on GitHub. They contain no unique behaviour and no test scripts — the load
scripts themselves live elsewhere.

**Does:**

- Reproduces `aqie-location-backend` at its March 2025 state: resolves a user-supplied place
  name to candidate locations using the Ordnance Survey Names API.

**Does not:**

- Contain any load-testing harness, scenario definitions or results. Nothing in this
  repository explains what was measured or what the outcome was.
- Differ meaningfully from its production counterpart. The module layout under `src/api` is
  identical.

## 3. Architecture

- **Pattern:** Hapi HTTP API on the CDP Node.js backend template — identical to
  `aqie-location-backend`.

| Component | Path | Responsibility |
|---|---|---|
| Place-name lookup | `src/api/getosname/` | Ordnance Survey Names search |
| Health | `src/api/health/` | Liveness endpoint |
| Config | `src/config/` | `convict` schema |

## 4. API Surface

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness probe |
| `GET` | `/osnameplaces/userLocation={userLocation}` | Place-name search |
| `GET` | `/example`, `/example/{exampleId}` | Unmodified CDP template routes |

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| Ordnance Survey Names API | External API | `GET /search/names/v1/find` | Place name in; candidate locations out | `OS_NAMES_API_KEY` |
| MongoDB | Datastore | Driver connection, with `mongo-locks` | CDP template wiring; no domain collections | `MONGO_URI` |

At the time it was run, it would have consumed live Ordnance Survey quota. No AQIE service is
called.

## 6. Consumed By (Inbound Dependencies)

None recorded. Notably, `aqie-dataselector-perf-frontend` points at the **production**
`aqie-location-backend` host, not at this fork.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** MongoDB from the CDP template; no domain collections.
- **Retention / refresh:** none.

## 8. Configuration

Variable **names** only.

| Variable | Purpose |
|---|---|
| `PORT`, `NODE_ENV`, `SERVICE_VERSION` | Runtime identity |
| `OS_NAMES_API_URL`, `OS_NAMES_API_KEY` | Ordnance Survey Names endpoint and key |
| `MONGO_URI`, `MONGO_DATABASE` | MongoDB connection |
| `CDP_HTTP_PROXY`, `CDP_HTTPS_PROXY` | CDP egress proxy |
| `ENABLE_SECURE_CONTEXT`, `TRUSTSTORE_ONE` | TLS trust store |
| `ENABLE_METRICS`, `TRACING_HEADER` | Observability |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |
| `ACCESS_CONTROL_ALLOW_ORIGIN_URL` | CORS origin |

No secret values are committed.

## 9. Hosting and Deployment

- **Platform:** DEFRA CDP on AWS ECS, intended for the `perf-test` environment.
- **Container:** CDP Node.js base images, entrypoint `node .`.
- **Pipelines:** the standard CDP set — `check-pull-request.yml`, `publish.yml`,
  `publish-hotfix.yml`. Publishing an image for an archived load-test fork is a small waste of
  build capacity, but the workflows are inert while the repository is archived.

## 10. Observability

- **Logging:** `pino` via `hapi-pino` with `@elastic/ecs-pino-format`.
- **Tracing:** `@defra/hapi-tracing`.
- **Metrics:** `aws-embedded-metrics`.

## 11. Open Questions

- [ ] Where are the load-test scripts and results for the March 2025 exercise? They are not in
      this repository. Check `aqie-performance-test` and
      `aqie-data-priv-beta-api-perftest`, which are not currently in the catalogue.
- [ ] Was this fork ever actually deployed and driven, or was the exercise run against the
      production services instead? The frontend fork points at production hosts, which suggests
      the perf backends may never have been wired in.
- [ ] Confirm the repository can be deleted. It is a stale copy of a live service, which is a
      maintenance and confusion risk, and it will not receive dependency patches.
- [ ] If future performance testing is planned, agree a pattern that does not require forking
      production repositories.
