# aqie-kpi-metrics-dashboard

> A standalone GOV.UK-styled dashboard for reporting AQIE service KPIs. It has no data source:
> figures are typed in or uploaded as a spreadsheet by the user, calculated in the browser and
> kept in browser storage.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-kpi-metrics-dashboard`](https://github.com/DEFRA/aqie-kpi-metrics-dashboard) |
| Service domain | `Shared` |
| Service type | `Data/Analytics Support Service` |
| Lifecycle stage | `Prototype/PoC` |
| Primary language | JavaScript |
| Runtime | Node.js `>=24` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2026-02-09` |
| Last main commit (UTC) | `2026-03-11T11:28:24Z` |
| Last analysed commit | `814e9948` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Inactive` |

## 2. Purpose and Responsibilities

**Does:**

- Serves a small set of server-rendered Nunjucks pages — overview, analytics, performance,
  reports, user feedback and settings — using the GOV.UK Design System.
- Lets a user enter KPI parameters, including a cost breakdown that is totalled as they type.
- Parses an uploaded user-satisfaction spreadsheet **entirely in the browser**, normalising
  free-text satisfaction responses and Excel serial dates into counts by category and date.
- Calculates the KPI figures client-side and persists the result to browser `localStorage`
  under a single key, which is re-read when the dashboard page loads.

**Does not:**

- Connect to any AQIE service, database or analytics platform. The page handlers return
  deliberately empty data structures; a comment in the metrics controller records that the
  previous mock data files were deleted. **This answers catalogue open question `oq-003`:
  there is no live data source.**
- Persist anything server-side. There is no MongoDB, no S3 and no API client in the codebase.
  Redis is configured only as a session/cache engine inherited from the CDP frontend template.
- Expose any API. Every route returns HTML.
- Provide air quality data, DAQI values or monitoring station information — those belong to
  `aqie-back-end` and `aqie-forecast-api`.
- Replace the CDP platform's own service metrics. It reports programme-level KPIs entered by
  hand, not runtime telemetry.

## 3. Architecture

**Pattern:** DEFRA CDP Node.js frontend template — a Hapi server rendering Nunjucks views,
with a webpack-built client bundle. All KPI logic lives in the client bundle; the server is a
view layer only.

| Component | Path | Responsibility |
|---|---|---|
| Metrics pages | `src/server/metrics/` | Route table and handlers for the six dashboard pages; each returns an empty data object |
| Dashboard views | `src/server/metrics/kpi-dashboard.njk`, `partials/` | KPI cards, charts, filters and side navigation |
| Client KPI engine | `src/client/javascripts/application.js` | Cost totalling, spreadsheet parsing via `xlsx`, KPI calculation, `localStorage` read and write |
| Home / About / Health | `src/server/home/`, `about/`, `health/` | Landing page, static content, liveness probe |
| Nunjucks setup | `src/config/nunjucks/` | Template environment, filters (date, currency), navigation builder |
| Session cache | `src/server/common/helpers/session-cache/`, `redis-client.js` | Catbox memory locally, Catbox Redis when deployed — template default, unused by page logic |
| Security headers | `src/server/common/helpers/content-security-policy.js` | `blankie`/`scooter` CSP |
| Config | `src/config/config.js` | `convict` schema — template defaults only |

## 4. API Surface

All routes render HTML. No JSON API is exposed.

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/health` | Liveness probe | — | Status payload |
| `GET` | `/` | Landing page | — | HTML |
| `GET` | `/about` | Static service information | — | HTML |
| `GET` | `/kpi-dashboard` | KPI overview; seeded with an empty data object and hydrated from browser storage | — | HTML |
| `GET` | `/analytics` | Analytics page, empty state | — | HTML |
| `GET` | `/performance` | Performance page, empty state | — | HTML |
| `GET` | `/reports` | Reports page | — | HTML |
| `GET` | `/user-feedback` | User feedback page, empty state | — | HTML |
| `GET` | `/settings` | KPI parameter entry, including the cost breakdown | — | HTML |
| `GET` | `/favicon.ico`, static asset path | Static files via `@hapi/inert` | — | Asset |

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| Redis | Datastore | Catbox Redis session cache (template default; no application use found) | Session entries only | `REDIS_USERNAME` / `REDIS_PASSWORD` |
| GOV.UK | External (link) | Footer links to GOV.UK cookie, privacy and accessibility pages | None | None |

No AQIE service, database or analytics API is called from this codebase.

## 6. Consumed By (Inbound Dependencies)

No AQIE service consumes this one. It is reached directly by people in a browser.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).
> This service correctly has no edges recorded there.

## 7. Data

- **Stores:** none server-side. Redis is available for session caching through the template
  but no page writes to it.
- **Key entities:** a single browser `localStorage` entry holding the calculated KPI result
  set, and an in-memory representation of the uploaded satisfaction spreadsheet — response
  category counts keyed by date.
- **Retention / refresh:** data lives only in the user's browser and is overwritten each time
  the KPIs are recalculated. Nothing is shared between users, sessions or devices.

## 8. Configuration

Environment variable **names** only — never record values.

| Variable | Purpose |
|---|---|
| `PORT`, `HOST` | HTTP listener |
| `NODE_ENV`, `SERVICE_VERSION` | Runtime identity |
| `REDIS_HOST`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_KEY_PREFIX`, `REDIS_TLS` | Redis session cache |
| `SESSION_CACHE_ENGINE`, `SESSION_CACHE_NAME`, `SESSION_CACHE_TTL`, `USE_SINGLE_INSTANCE_CACHE` | Catbox cache selection |
| `SESSION_COOKIE_PASSWORD`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_TTL` | Session cookie |
| `ASSET_PATH`, `STATIC_CACHE_TIMEOUT` | Static asset serving |
| `ENABLE_SECURE_CONTEXT` | TLS trust store |
| `HTTP_PROXY` | CDP egress proxy |
| `TRACING_HEADER` | Trace header name |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`;
  entrypoint `node src`.
- **Environments:** CDP standard set. No environment-specific configuration is present in the
  repository beyond the template defaults.
- **Local development:** `compose.yml` provides LocalStack, Redis and MongoDB; the frontend
  service in that file is still named `your-frontend` from the template.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — lint, test and SonarQube on PR, plus a
    scheduled run
  - `.github/workflows/publish.yml` — build and publish on push
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, ECS-formatted with `@elastic/ecs-pino-format` in
  production, `pino-pretty` locally.
- **Tracing:** `@defra/hapi-tracing` propagating the header named in `TRACING_HEADER`.
- **Metrics:** `@defra/cdp-metrics`; auditing via `@defra/cdp-auditing`.
- **Shutdown:** `hapi-pulse` for graceful draining.

## 11. Open Questions

- [ ] **Catalogue `oq-003` — answered.** There is no live data source. All figures are
      hand-entered or uploaded as a spreadsheet, calculated in the browser and stored in
      `localStorage`. The open question can be closed once the owner confirms this is the
      intended design rather than an unfinished integration.
- [ ] Is the service still wanted? Last commit was 2026-03-11 and it is marked `Inactive`. If
      it is retained, the intent behind the deleted mock data files needs recording.
- [ ] Because results live only in the user's browser, two people looking at the same
      deployment see different numbers. Confirm whether shared, server-side KPI storage is
      required.
- [ ] Is the dashboard deployed to any CDP environment, and is it access-controlled? No
      authentication or authorisation exists in the codebase, yet the spreadsheet upload can
      contain user research responses.
- [ ] Is the uploaded satisfaction spreadsheet personal data? It is never transmitted to the
      server, but confirm the source and its handling requirements.
- [ ] The repository still carries the template `description` of `CDP Frontend Template` and
      an unrenamed compose service. Confirm whether the repository should be tidied or
      archived.
