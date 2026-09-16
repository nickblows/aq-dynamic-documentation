# aqie-monitorstation-perf-backend

> A March 2025 performance-test fork of `aqie-monitoringstation-backend` that was never
> populated. It contains only the unmodified CDP backend template.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-monitorstation-perf-backend`](https://github.com/DEFRA/aqie-monitorstation-perf-backend) |
| Service domain | `Shared` |
| Service type | `Quality/Test Service` |
| Lifecycle stage | `Archived` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2025-03-17` |
| Last main commit (UTC) | `2025-03-17T16:09:37Z` |
| Last analysed commit | `8fe70b2b` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Archived` |

## 2. Purpose and Responsibilities

> **Archived and empty.** Intended as a performance-test copy of
> `aqie-monitoringstation-backend`, but no domain code was ever added. Not superseded — the
> service it was meant to copy is still live. Do not deploy.

**The `*-perf-*` pattern.** This is one of four throwaway forks created within two hours of
each other on 17 March 2025 so that load could be driven without touching shared environments;
the others are `aqie-location-perf-backend`, `aqie-historicaldata-perf-backend` and
`aqie-dataselector-perf-frontend`. See
[`aqie-location-perf-backend`](../aqie-location-perf-backend/service-profile.md) for the full
description of the pattern.

**Does:**

- Nothing. The repository has a single commit, "Applying template", made the day it was
  created. It is the CDP Node.js backend template with the repository name substituted.

**Does not:**

- Contain any monitoring station logic. There is no `/monitoringstation` route and no call to
  `aqie-back-end` or `aqie-location-backend`, unlike the production service it was named after.
- Contain any load-testing harness or results.

## 3. Architecture

- **Pattern:** the unmodified CDP Node.js backend template — Hapi HTTP API with MongoDB wiring.

| Component | Path | Responsibility |
|---|---|---|
| Example plugin | `src/api/example/` | CDP template placeholder |
| Health | `src/api/health/` | Liveness endpoint |
| Config | `src/config/` | `convict` schema, template defaults only |

## 4. API Surface

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness probe |
| `GET` | `/example`, `/example/{exampleId}` | Unmodified CDP template routes |

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| MongoDB | Datastore | Driver connection, with `mongo-locks` | CDP template wiring; no domain collections | `MONGO_URI` |

No external API and no AQIE service is called. This is the clearest evidence that the fork was
abandoned before any work was done.

## 6. Consumed By (Inbound Dependencies)

None.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** MongoDB from the CDP template; no collections written.
- **Retention / refresh:** none.

## 8. Configuration

Variable **names** only — all template defaults.

| Variable | Purpose |
|---|---|
| `PORT`, `NODE_ENV`, `SERVICE_VERSION` | Runtime identity |
| `MONGO_URI`, `MONGO_DATABASE` | MongoDB connection |
| `HTTP_PROXY` | CDP egress proxy |
| `ENABLE_SECURE_CONTEXT`, `TRUSTSTORE_ONE` | TLS trust store |
| `ENABLE_METRICS`, `TRACING_HEADER` | Observability |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |

No secret values are committed.

## 9. Hosting and Deployment

- **Platform:** DEFRA CDP on AWS ECS. There is no evidence it was ever deployed.
- **Container:** CDP Node.js base images, entrypoint `node .`.
- **Pipelines:** the standard CDP set — `check-pull-request.yml`, `publish.yml`,
  `publish-hotfix.yml`.

## 10. Observability

- **Logging:** `pino` via `hapi-pino` with `@elastic/ecs-pino-format`.
- **Tracing:** `@defra/hapi-tracing`.
- **Metrics:** `aws-embedded-metrics`.

## 11. Open Questions

- [ ] This repository has no content of any kind. Confirm it can be deleted rather than merely
      archived — it is the strongest deletion candidate in the estate.
- [ ] Was the monitoring station service excluded from the March 2025 performance exercise, or
      was it tested some other way?
- [ ] Note the naming inconsistency: `monitorstation` here versus `monitoringstation` in the
      production service. If any tooling matches repositories by name prefix, this fork will
      not be associated with its counterpart.
