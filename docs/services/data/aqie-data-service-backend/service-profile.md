# aqie-data-service-backend

> A short-lived combined location and monitoring station API from early 2025. Its two
> responsibilities were separated into the services that run in production today.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-data-service-backend`](https://github.com/DEFRA/aqie-data-service-backend) |
| Service domain | `Data` |
| Service type | `Auxilary Backend Service` |
| Lifecycle stage | `Archived` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2025-01-23` |
| Last main commit (UTC) | `2025-02-20T13:28:22Z` |
| Last analysed commit | `3a686fd0` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Archived` |

## 2. Purpose and Responsibilities

> **Archived.** Superseded by the split pair `aqie-location-backend` (place-name search) and
> `aqie-monitoringstation-backend` (nearest monitoring stations). Retained for historical
> reference. Do not deploy.

**Does:**

- Resolves a user-supplied place name to candidate locations using the Ordnance Survey Names
  API.
- Finds monitoring stations near those coordinates, using `geolib` for distance calculation,
  and enriches them with current pollutant readings from `aqie-back-end`.

**Does not:**

- Ingest or own any measurement data. It was always a read-through aggregator over
  `aqie-back-end`.

**Lineage.** This was the first backend built for the data selector journey, combining place
lookup and station lookup in one Hapi service. Both of its domain routes survive today,
but in two separate services: `/osnameplaces` is now served by `aqie-location-backend`, and
the nearest-station lookup is now `aqie-monitoringstation-backend`'s `/monitoringstation`.
Both successors carry the same route names, the same Ordnance Survey integration and the same
onward call to `aqie-back-end`, so the split is well evidenced. The repository was archived in
February 2025, a month after it was created.

One consequence of the split is still visible in the estate: `aqie-dataselector-perf-frontend`
retains configuration pointing at this service's CDP host, under a transposed spelling
(`aiqe-dataservice-backend`) that no longer resolves.

## 3. Architecture

- **Pattern:** Hapi HTTP API on the CDP Node.js backend template, with a single domain plugin.

| Component | Path | Responsibility |
|---|---|---|
| Location plugin | `src/api/location/` | Both domain routes; OS Names lookup, nearest-station calculation and measurement enrichment |
| Location helpers | `src/api/location/helpers/` | `get-osplace-util`, `get-nearest-location`, `fetch-data`, `location-util` |
| Health | `src/api/health/` | Liveness endpoint |
| Config | `src/config/` | `convict` schema |

## 4. API Surface

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness probe |
| `GET` | `/osnameplaces` | Place-name search |
| `GET` | `/monitoringstation/location={userLocation}` | Nearest monitoring stations for a place |
| `GET` | `/example`, `/example/{exampleId}` | Unmodified CDP template routes |

Both domain routes were handled by the same controller, which is why the split into two
services was straightforward.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-back-end` | AQIE service | `GET /measurements` | Current pollutant concentrations per station | CDP internal network |
| Ordnance Survey Names API | External API | Place-name search | Place name in; candidate locations out | API key from configuration |
| MongoDB | Datastore | Driver connection | Present via the CDP template; no domain collections written | `MONGO_URI` |

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| `aqie-dataselector-perf-frontend` | `GET /osnameplaces`, `GET /monitoringstation/location=` | Historical configuration only; the host no longer exists |

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** MongoDB was wired up by the CDP template but no domain collection is written.
  All responses were composed live from Ordnance Survey and `aqie-back-end`.
- **Key entities:** candidate locations, monitoring stations with distance and pollutant values.
- **Retention / refresh:** none — no persistence, no scheduled jobs.

## 8. Configuration

Variable **names** only.

| Variable | Purpose |
|---|---|
| `PORT`, `NODE_ENV`, `SERVICE_VERSION` | Runtime identity |
| `OSPlace_API_URL` | Ordnance Survey Names endpoint |
| `MEASUREMENTS_API_URL` | `aqie-back-end` measurements endpoint |
| `MONGO_URI`, `MONGO_DATABASE` | MongoDB connection |
| `CDP_HTTP_PROXY`, `CDP_HTTPS_PROXY` | CDP egress proxy |
| `ENABLE_SECURE_CONTEXT`, `TRUSTSTORE_ONE` | TLS trust store |
| `ENABLE_METRICS`, `TRACING_HEADER` | Observability |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |
| `ACCESS_CONTROL_ALLOW_ORIGIN_URL` | CORS origin |

No secret values are committed.

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS, `dev` only as far as the
  configuration shows.
- **Container:** CDP Node.js base images, entrypoint `node .`.
- **Pipelines:** the standard CDP set — `check-pull-request.yml`, `publish.yml`,
  `publish-hotfix.yml`.

## 10. Observability

- **Logging:** `pino` via `hapi-pino` with `@elastic/ecs-pino-format`.
- **Tracing:** `@defra/hapi-tracing`.
- **Metrics:** `aws-embedded-metrics`, gated by `ENABLE_METRICS`.

## 11. Open Questions

- [ ] Confirm the split was deliberate rather than a rebuild, and record the decision. The
      route-level correspondence is strong but no architecture decision record exists.
- [ ] Should the stale `aiqe-dataservice-backend` host references in
      `aqie-dataselector-perf-frontend` be removed, or is that repository also for deletion?
- [ ] The repository is already archived on GitHub. Confirm it can be deleted, given both
      successors are live and no code is shared back.
