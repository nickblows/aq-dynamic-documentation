# aqie-dc-poc-frontend

> A proof-of-concept frontend scaffold for the domestic combustion service. It is an
> unmodified CDP Node.js frontend template with no smoke control screens, superseded by
> `aqie-dc-frontend` and `aqie-dc-admin-frontend`.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-dc-poc-frontend`](https://github.com/DEFRA/aqie-dc-poc-frontend) |
| Service domain | `Citizen` |
| Service type | `Prototype Service (including PoC)` |
| Lifecycle stage | `Prototype/PoC` |
| Primary language | JavaScript |
| Runtime | Node.js `>=24` (ES modules), pinned to `v24.14.1` in `.nvmrc` |
| Default branch | `main` |
| Created (UTC) | `2026-05-14` |
| Last main commit (UTC) | `2026-05-14T09:32:58Z` |
| Last analysed commit | `38e62e1f` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Monitoring` |

## 2. Purpose and Responsibilities

**Does:**

- Provides a runnable CDP frontend skeleton: a Hapi server, Nunjucks and GOV.UK Frontend
  templating, a Redis-backed or in-memory session cache, a content security policy, proxy
  setup, structured logging, request tracing and graceful shutdown.
- Serves the template's home, about and health pages and the static asset pipeline.

**Does not:**

- Show any part of the smoke control register. There is no finder, no search, no filtering, no
  detail page and no legal basis content. The public register is `aqie-dc-frontend`.
- Provide any caseworker screen, sign-in or review journey. That is `aqie-dc-admin-frontend`.
- Call any backend. There is no API client, no `BACKEND_URL` setting and no outbound HTTP call
  anywhere in the repository — including to `aqie-dc-poc-backend`.
- Support Welsh. The bilingual content and language toggle exist only in `aqie-dc-frontend`.

**Relationship to the live services.** The repository was created on 14 May 2026 and has a
single commit, the initial template. `aqie-dc-frontend` was created on 26 January 2026 and
`aqie-dc-admin-frontend` on 3 February 2026 — both predate it and both carry real domestic
combustion behaviour. It is superseded by that pair in the sense that they are the services
that exist; on the evidence this is a scaffold created after them rather than a prototype they
grew out of. See Section 11.

**Shared infrastructure with the live pair:** none that is visible in code. This repository
declares its own Redis settings and its `compose.yml` starts a local MongoDB that the
application never connects to. There is no shared session store key prefix, no shared backend
and no cross-reference in either direction.

## 3. Architecture

**Pattern:** Hapi server-rendered GOV.UK Frontend application — the unmodified CDP frontend
template, with Vite building the client bundle.

| Component | Path | Responsibility |
|---|---|---|
| Server composition | `src/server/server.js` | Registers plugins and the router |
| Router | `src/server/plugins/router.js` | Registers home, about, health and static assets |
| Route modules | `src/server/routes/home/`, `about/`, `health/` | Template pages |
| Session cache | `src/server/plugins/session-cache.js`, `src/server/common/helpers/redis-client.js` | Redis or in-memory session state |
| Content security policy | `src/server/plugins/content-security-policy.js` | CSP headers |
| Nunjucks setup | `src/config/nunjucks/` | Template environment, filters, globals and page context |
| Config | `src/config/config.js` | `convict` schema |

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/` | Template home page | — | HTML |
| `GET` | `/about` | Template about page | — | HTML |
| `GET` | `/health` | Liveness probe | — | Status payload |
| `GET` | `/favicon.ico`, static assets | Static assets | — | Files |

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| Redis | Datastore | `catbox-redis` session cache | Session state only | `REDIS_USERNAME` / `REDIS_PASSWORD` |
| GOV.UK | External (link only) | Footer links to accessibility, cookies and privacy pages | Outbound hyperlinks; no data exchanged | None |

No calls are made to any AQIE service.

## 6. Consumed By (Inbound Dependencies)

None. No AQIE service references this repository.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).
> There is no edge for this service, which matches the evidence.

## 7. Data

- **Stores:** Redis only, for session state. A MongoDB container is present in `compose.yml`
  with an initialisation script, but the application code never opens a MongoDB connection.
- **Key entities:** none — no domain model is defined.
- **Retention / refresh:** session TTL is `SESSION_CACHE_TTL`; cookie lifetime is
  `SESSION_COOKIE_TTL`; static assets are cached for `STATIC_CACHE_TIMEOUT`.

## 8. Configuration

Environment variable names only — never values.

| Variable | Purpose |
|---|---|
| `PORT`, `HOST` | HTTP listener |
| `NODE_ENV`, `SERVICE_VERSION` | Runtime identity |
| `REDIS_HOST`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_KEY_PREFIX`, `REDIS_TLS` | Redis session store |
| `SESSION_CACHE_ENGINE`, `SESSION_CACHE_NAME`, `SESSION_CACHE_TTL`, `USE_SINGLE_INSTANCE_CACHE` | Session cache behaviour |
| `SESSION_COOKIE_PASSWORD`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_TTL` | Session cookie |
| `ASSET_PATH`, `STATIC_CACHE_TIMEOUT` | Static asset serving |
| `HTTP_PROXY` | CDP egress proxy |
| `ENABLE_SECURE_CONTEXT` | TLS trust store |
| `TRACING_HEADER` | CDP request tracing header name |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT`, `LOG_REDACT` | Logging and redaction paths |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`;
  production entrypoint `node src`, with the Vite bundle built beforehand.
- **Internal address:** `https://aqie-dc-poc-frontend.<env>.cdp-int.defra.cloud` if deployed.
- **Environments:** CDP defaults. There is no evidence in the repository of a deployment to
  any environment beyond the template pipelines.
- **Local development:** `compose.yml` provides Redis and an unused MongoDB.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — lint and test on PR
  - `.github/workflows/publish.yml` — build and publish on push to `main`
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish

## 10. Observability

- **Logging:** `pino` with ECS formatting in production; redaction paths configurable via
  `LOG_REDACT`.
- **Tracing:** trace header propagation via the template's `request-tracing` plugin, using
  `TRACING_HEADER`.
- **Metrics:** none configured beyond the template's `AWS_EMF_ENVIRONMENT` development setting.
- **Shutdown:** `hapi-pulse` for graceful draining.

## 11. Open Questions

- [ ] Confirm the intended relationship with `aqie-dc-frontend` and `aqie-dc-admin-frontend`.
      This repository was created after both and contains no domain code, so "proof of concept"
      may not describe what it actually is.
- [ ] Is this repository still needed? If it was a scaffold that was never taken forward, it
      should be archived so it stops appearing as an active DC service.
- [ ] Confirm whether it has ever been deployed to a CDP environment, and whether any Redis
      instance provisioned for it can be released.
- [ ] Confirm that its Redis key prefix could not collide with the live frontends' session
      store if they were ever to share a Redis instance.
- [ ] The `compose.yml` MongoDB container and its initialisation script are unused. Confirm
      they can be removed.
- [ ] Confirm an owning team, so that dependency and security updates are not left unattended.

