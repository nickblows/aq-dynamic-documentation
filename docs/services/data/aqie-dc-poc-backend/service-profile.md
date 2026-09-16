# aqie-dc-poc-backend

> A proof-of-concept backend scaffold for the domestic combustion service. It is an
> unmodified CDP Node.js backend template with no smoke control domain logic, superseded by
> `aqie-dc-backend`.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-dc-poc-backend`](https://github.com/DEFRA/aqie-dc-poc-backend) |
| Service domain | `Data` |
| Service type | `Prototype Service (including PoC)` |
| Lifecycle stage | `Prototype/PoC` |
| Primary language | JavaScript |
| Runtime | Node.js `>=24` (ES modules), pinned to `v24.14.1` in `.nvmrc` |
| Default branch | `main` |
| Created (UTC) | `2026-05-14` |
| Last main commit (UTC) | `2026-05-14T09:00:44Z` |
| Last analysed commit | `fa3f4448` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Monitoring` |

## 2. Purpose and Responsibilities

**Does:**

- Provides a runnable CDP backend skeleton: a Hapi server, a MongoDB connection pool attached
  to the server and request objects, distributed locking via `mongo-locks`, structured
  logging, request tracing, proxy setup and a graceful shutdown handler.
- Exposes a health endpoint and the template's example CRUD routes.

**Does not:**

- Implement any part of the smoke control regime. There is no appliance register, no fuel
  register, no application, no technical review and no certification logic of any kind. The
  only route module beyond health is the template's `example`.
- Supersede or precede `aqie-dc-backend` in function. **`aqie-dc-backend` is the live
  service and holds all domestic combustion behaviour.** This repository does not contain an
  earlier working version of it.
- Share any infrastructure with the live pair. It defines its own MongoDB database name and
  has no queue, no S3 bucket, no uploader integration and no reference to
  `aqie-dc-backend` or either frontend.
- Serve `aqie-dc-poc-frontend`. That repository contains no backend client and never calls
  this service.

**Relationship to the live services.** The repository was created on 14 May 2026 and has not
been changed since — its only commit is the initial template. The live `aqie-dc-backend` was
created on 26 January 2026, nearly four months earlier, and has been developed continuously
since. On the evidence in the code, this is a scaffold created after the live service rather
than a prototype it grew out of. It is superseded by `aqie-dc-backend` in the sense that
`aqie-dc-backend` is the service that exists; the direction of that supersession needs owner
confirmation (Section 11).

## 3. Architecture

**Pattern:** Hapi HTTP API with a MongoDB plugin — the unmodified CDP backend template.

| Component | Path | Responsibility |
|---|---|---|
| Server composition | `src/server.js` | Registers plugins and the router |
| Router | `src/plugins/router.js` | Registers health and example routes |
| MongoDB plugin | `src/plugins/mongodb.js` | Connection pool attached to server and request |
| Mongo lock helper | `src/common/helpers/mongo-lock.js` | Distributed locking scaffold |
| Example service | `src/services/ExampleFind.js` | Template data access example |
| Logging and tracing | `src/plugins/logger-options.js`, `request-logger.js`, `request-tracing.js` | Structured logging and trace header propagation |
| Config | `src/config.js` | `convict` schema |

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/health` | Liveness probe | — | Status payload |
| `GET` | `/example` | Template example collection | — | Example records |
| `GET` | `/example/{exampleId}` | Template example record | `exampleId` | Example record |

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| MongoDB | Datastore | Driver connection | Template example documents only | `MONGO_URI` |

No outbound HTTP calls to any AQIE service or external system exist in the repository.

## 6. Consumed By (Inbound Dependencies)

None. No AQIE service references this repository.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).
> There is no edge for this service, which matches the evidence.

## 7. Data

- **Stores:** MongoDB (`MONGO_DATABASE`), configured but holding only the template's example
  documents. No collections of domestic combustion data are defined.
- **Key entities:** none — no schema or model is defined in the repository.
- **Retention / refresh:** not applicable. No scheduled jobs, ingest or TTL rules exist.

## 8. Configuration

Environment variable names only — never values.

| Variable | Purpose |
|---|---|
| `PORT`, `HOST` | HTTP listener |
| `NODE_ENV`, `ENVIRONMENT`, `SERVICE_VERSION` | Runtime identity |
| `MONGO_URI`, `MONGO_DATABASE` | MongoDB connection |
| `MONGO_RETRY_WRITES`, `MONGO_READ_PREFERENCE` | Mongo driver overrides |
| `HTTP_PROXY` | CDP egress proxy |
| `TRACING_HEADER` | CDP request tracing header name |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`;
  production entrypoint `node src`.
- **Internal address:** `https://aqie-dc-poc-backend.<env>.cdp-int.defra.cloud` if deployed.
- **Environments:** CDP defaults. There is no evidence in the repository of a deployment to
  any environment beyond the template pipelines.
- **Local development:** `compose.yml` provides MongoDB.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — lint and test on PR
  - `.github/workflows/publish.yml` — build and publish on push to `main`
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish

## 10. Observability

- **Logging:** `pino` with ECS formatting in production.
- **Tracing:** trace header propagation via the template's `request-tracing` plugin, using
  `TRACING_HEADER`.
- **Metrics:** none configured beyond the template's `AWS_EMF_ENVIRONMENT` development setting.
- **Shutdown:** `hapi-pulse` for graceful draining.

## 11. Open Questions

- [ ] Confirm the intended relationship with `aqie-dc-backend`. This repository was created
      after the live service and contains no domain code, so "proof of concept" may not
      describe what it actually is.
- [ ] Is this repository still needed? If it was a scaffold that was never taken forward, it
      should be archived so it stops appearing as an active DC service.
- [ ] Confirm whether it has ever been deployed to a CDP environment, and if so whether the
      environment and its MongoDB instance can be decommissioned.
- [ ] Confirm there is no shared MongoDB instance with `aqie-dc-backend` — the two declare
      different database names, but the underlying cluster is a platform concern not visible
      in either repository.
- [ ] Confirm an owning team, so that dependency and security updates are not left unattended.

