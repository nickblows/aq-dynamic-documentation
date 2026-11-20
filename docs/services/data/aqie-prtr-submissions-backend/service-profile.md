# aqie-prtr-submissions-backend

> A backend scaffold for the Pollutant Release and Transfer Register (PRTR) submissions service. It is
> an unmodified CDP Node.js backend template with only health and example routes: no submission logic,
> no data model and no integrations yet.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-prtr-submissions-backend`](https://github.com/DEFRA/aqie-prtr-submissions-backend) |
| Service domain | `Data` |
| Service type | `Auxilary Backend Service` |
| Lifecycle stage | `Prototype/PoC` |
| Primary language | JavaScript |
| Runtime | Node.js `>=24` (ES modules), pinned to `v24.22.1` in `.nvmrc` |
| Default branch | `main` |
| Created (UTC) | `2026-10-26` |
| Last main commit (UTC) | `2026-11-09T16:27:11Z` |
| Last analysed commit | `04620b7e` |
| Last analysed (UTC) | `2026-11-19T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Intended:** the backend for a PRTR submissions service, paired with `aqie-prtr-submissions-frontend`,
whose About page says the service lets you submit your pollutant release and transfer data. That sentence
and the repository name are the only indications of purpose. No code in this repository states a design.

**Actual:** the repository is the DEFRA CDP Node.js backend template. It was generated on 26 October 2026,
and the only changes since are Sonar wiring and `cross-env` and `nodemon` development scripts. It builds a
Hapi server with platform plumbing and a MongoDB connection, and serves two kinds of route: a health check
and the template's example endpoints.

**Does:**

- Serves `GET /health` for the platform's liveness check.
- Serves the template example endpoints `GET /example` and `GET /example/{exampleId}`, which read an
  `example-data` collection.
- Connects to its own MongoDB database and keeps a lock manager ready for future use (nothing calls it).
- Provides the standard CDP plumbing: structured logging, trace header propagation, metrics, graceful
  shutdown and secure-context certificate loading.

**Does not:**

- Accept, validate, store or forward any submission. There is no submission route, schema, data model,
  file handling or workflow.
- Authenticate or authorise anyone. No route has any authentication.
- Call any other service. There is no HTTP client, and no use of the CDP Uploader, GOV.UK Notify, an
  identity or sign-in provider, S3 or SQS.
- Hold or serve any existing PRTR data. The register data lives in `aqie-prtr-backend`; this service has
  its own database name and no link to it.

**Relationship to the existing PRTR services.** It shares the `aqie-prtr-` name with the public register
services `aqie-prtr-backend` and `aqie-prtr-frontend`, but none of the four repositories refers to
another, and they share no database, bucket or URL setting. The shared name is the only link. On `main`
it stands alone. Whether submissions will eventually feed the register is not stated anywhere in code
(see Section 11).

## 3. Architecture

**Pattern:** CDP Node.js backend template. A Hapi HTTP API over MongoDB, with thin plugins for logging,
tracing, metrics and shutdown. Only template routes exist.

| Component | Path | Responsibility |
|---|---|---|
| Server | `src/server.js` | Builds the Hapi server, sets security headers, registers the plugins |
| Router | `src/plugins/router.js` | Registers the health and example routes |
| Health route | `src/routes/health.js` | `GET /health` |
| Example routes | `src/routes/example.js`, `src/services/ExampleFind.js` | Template example; lists or fetches documents from `example-data` |
| MongoDB plugin | `src/plugins/mongodb.js` | Connects, creates the lock manager and indexes, decorates `server.db` and `request.db` |
| Lock helpers | `src/common/helpers/mongo-lock.js` | Wrappers for acquiring a lock (no caller) |
| Validation failure | `src/common/helpers/fail-action.js` | Logs a validation failure and rethrows it |
| Logging and tracing | `src/plugins/logger-options.js`, `request-logger.js`, `request-tracing.js` | `pino` logging and trace header handling |
| Shutdown | `src/plugins/pulse.js` | Graceful shutdown with a ten second timeout |
| Config | `src/config.js` | `convict` schema with strict validation |

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/health` | Liveness probe | — | `{ message: 'success' }` |
| `GET` | `/example` | Template example: every document in `example-data` | — | JSON array (empty unless the collection is seeded) |
| `GET` | `/example/{exampleId}` | Template example: one document | `exampleId` | The document, or `404` |

The `README.md` endpoint table matches the code. No route requires authentication. The two `/example`
routes are template leftovers.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| MongoDB | Datastore | Driver connection (`MONGO_URI`, `MONGO_DATABASE`) | `mongo-locks` and `example-data` collections only | Connection string supplied by CDP |

There are no calls to any AQIE service or external API. `@aws-sdk/credential-providers`, `aws4` and
`@defra/cdp-auditing` are declared in `package.json` but never imported, and `HTTP_PROXY` is declared in
config but nothing reads it. The platform's outbound proxy is set through the Node 24 variables
`NODE_USE_ENV_PROXY`, `HTTPS_PROXY` and `NO_PROXY`, which the README describes.

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| CDP platform | `GET /health` | Liveness check |

No AQIE service calls this one. In particular `aqie-prtr-submissions-frontend` has no backend URL setting
and no HTTP client, and a GitHub code search of the DEFRA organisation finds no other public repository
that names this service.

> Inbound and outbound edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).
> This service has none. The catalogue records the negative results under `refuted_edges`.

## 7. Data

- **Stores:** one MongoDB database, named by `MONGO_DATABASE` (default is the service name, which is not the
  `aqie-prtr-backend` database). It holds `mongo-locks` (created at start-up) and `example-data` (template
  example, empty unless seeded).
- **Key entities:** none. No submission, submitter or file entity exists.
- **Retention / refresh:** not applicable; nothing writes data.
- **No S3 bucket, queue or cache** is configured.

## 8. Configuration

Variable names only. Values are held in CDP and never recorded here.

| Variable | Purpose |
|---|---|
| `PORT`, `HOST` | HTTP listener (config default port `3001`; the Dockerfile sets `3000`) |
| `NODE_ENV`, `ENVIRONMENT`, `SERVICE_VERSION` | Runtime identity; `ENVIRONMENT` must be one of the CDP environment names |
| `MONGO_URI`, `MONGO_DATABASE` | MongoDB connection and database name |
| `MONGO_RETRY_WRITES`, `MONGO_READ_PREFERENCE` | MongoDB driver overrides |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |
| `TRACING_HEADER` | Name of the CDP trace header |
| `HTTP_PROXY` | Declared but not read by service code |
| `NODE_USE_ENV_PROXY`, `HTTPS_PROXY`, `NO_PROXY` | Platform outbound proxy. The README says the platform sets them; service code does not read them |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS. The repository is the CDP Node.js backend
  template and publishes through the CDP build action.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`, parent
  image `3.2.4-node24.22.1`. `curl` is added for the platform health check. Entrypoint `node src`.
- **Environments:** the config accepts `local`, `infra-dev`, `management`, `dev`, `test`, `perf-test`,
  `ext-test` and `prod`. The repository does not show which of them the service is deployed to.
- **Local development:** `compose.yml` starts MongoDB, Redis and the Floci AWS emulator alongside the
  service. The service itself uses only MongoDB.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` runs the security audit, format check, lint, tests and a
    Docker build test on pull requests, and the Sonar scan when `SONAR_TOKEN` is set.
  - `.github/workflows/publish.yml` tests, builds and publishes through the CDP build action on push to
    `main`, then runs Sonar without failing the build.
  - `.github/workflows/publish-hotfix.yml` is a manual hotfix publish.
- **Testing:** `vitest` with an in-memory MongoDB and coverage.

## 10. Observability

- **Logging:** `pino` through `hapi-pino`, ECS format in production and `pino-pretty` elsewhere. In production
  the `authorization` and `cookie` request headers and all response headers are removed from logs. `/health` is
  excluded from request logs.
- **Tracing:** `@defra/hapi-tracing` propagating the header named in `TRACING_HEADER`.
- **Metrics:** `@defra/cdp-metrics`.
- **Auditing:** `@defra/cdp-auditing` is declared but never imported, so no audit events are emitted.
- **Shutdown:** `hapi-pulse`.

## 11. Open Questions

- [ ] (catalogue `oq-032`) What is the intended relationship between the submissions services and the existing register? On
      `main` this service is unconnected to `aqie-prtr-backend`, so it is unknown whether submissions will be
      written into that database, feed its TSV or XML route, or stay separate.
- [ ] (catalogue `oq-032`) Who will submit data (operators, regulators or both), and how will they sign in? There is no
      authentication code yet.
- [ ] (catalogue `oq-032`) Will `aqie-prtr-submissions-frontend` call this service? It has no backend URL setting yet.
- [ ] (catalogue `oq-032`) Is the service deployed to any CDP environment, and when is a first release expected? The
      repository does not say.
- [ ] The template `/example` routes are live and unauthenticated. Confirm they will be removed before any
      real data is stored.
- [ ] Before accepting submissions, what is the plan for audit events (`@defra/cdp-auditing` is unused), a
      data protection assessment and retention?
