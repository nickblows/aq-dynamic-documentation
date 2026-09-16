# aqie-dc-frontend

> The public-facing register of appliances and fuels that may lawfully be used in a smoke
> control area. A bilingual, read-only search and browse service for citizens, installers and
> retailers.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-dc-frontend`](https://github.com/DEFRA/aqie-dc-frontend) |
| Service domain | `Citizen` |
| Service type | `Auxilary Frontend` |
| Lifecycle stage | `Beta` |
| Primary language | JavaScript |
| Runtime | Node.js `>=24 <=26` (ES modules), pinned to `v24.11.1` in `.nvmrc` |
| Default branch | `main` |
| Created (UTC) | `2026-01-26` |
| Last main commit (UTC) | `2026-04-21T09:16:55Z` |
| Last analysed commit | `0100dc25` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Monitoring` |

## 2. Purpose and Responsibilities

**Does:**

- Presents the exempt appliance register and the authorised fuel register as browsable,
  paginated lists, ten items to a page, with ellipsised pagination for long result sets.
- Provides free-text search across a register. A comma-separated query is treated as several
  independent terms, any of which may match. Appliances match on name, manufacturer, model
  number or appliance type; fuels match on name, manufacturer or identifier.
- Applies faceted filters — for example by country of authorisation — with each selected
  filter rendered as a removable tag that rebuilds the query string without that value.
- Renders a detail page for a single appliance or fuel.
- Explains the legal basis for the register, per register type.
- Serves every register page in both English and Welsh. Language is a path segment
  (`.../{language?}`), and a toggle link rewrites the current path to the other language,
  preserving the query string. Lookup values, filter labels and dates are all translated,
  including month names.
- Normalises the backend response for display — lower-casing manufacturer, fuel, type and
  country-of-authorisation values so that search and filtering behave consistently.

**Does not:**

- Accept applications. Manufacturers apply through the DEFRA Forms service; this frontend has
  no `POST` route of any kind and no application journey.
- Perform any caseworking, technical review or certification decision — that is
  `aqie-dc-admin-frontend`.
- Hold the register itself. All data comes from `aqie-dc-backend`; this service persists
  nothing but session state.
- Authenticate anyone. The register is public and there is no sign-in.
- Show air quality measurements, forecasts or monitoring stations — that is `aqie-front-end`
  and `aqie-maps-frontend`.

## 3. Architecture

**Pattern:** Hapi server-rendered GOV.UK Frontend application using Nunjucks templates, with
a thin `node-fetch` client to the backend. There is no client-side data fetching; search,
filtering and pagination are all evaluated on the server against the full list returned by the
backend.

| Component | Path | Responsibility |
|---|---|---|
| Router | `src/server/router.js` | Registers home, about, finder, detail, legal basis, health and static assets |
| Finder | `src/server/finder/` | Controller, search matching, filter construction and static page content |
| Detail page | `src/server/listItem/` | Single appliance or fuel view |
| Legal basis | `src/server/legalBasis/` | Register-specific legal basis content |
| Backend client | `src/server/common/api/api.js` | `fetchAll` and `fetchById`, plus response normalisation |
| Shared utilities | `src/server/common/util.js` | Translation, sanitisation, singularisation, language toggle, input validation |
| Lookup content | `src/server/common/content.js` | Bilingual lookup lists used by filters and translation |
| Nunjucks setup | `src/config/nunjucks/` | Template environment, filters, globals and page context |
| Session cache | `src/server/common/helpers/session-cache/` | Redis-backed or in-memory session store |
| Config | `src/config/config.js` | `convict` schema |

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/` | Service start page | — | HTML |
| `GET` | `/finder/{type}/{language?}` | Search, filter and paginate a register | `type` (appliances or fuels), optional language, `search`, `page` and filter query parameters | HTML result list |
| `GET` | `/details/{type}/{id}/{language?}` | Detail page for one register entry | `type`, `id`, optional language | HTML |
| `GET` | `/legal-basis-for-{type}/{language?}` | Legal basis content for a register | `type`, optional language | HTML |
| `GET` | `/about` | About the service | — | HTML |
| `GET` | `/health` | Liveness probe | — | Status payload |
| `GET` | `/assets/{param*}`, `/favicon.ico` | Static assets | — | Files |

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-dc-backend` | AQIE service | `GET /get-all/{type}` | Register type in; full list of appliances or fuels out | `x-api-key` header from `CDP_X_API_KEY` |
| `aqie-dc-backend` | AQIE service | `GET /get/{type}/{id}` | Register type and identifier in; single record out | `x-api-key` header from `CDP_X_API_KEY` |
| Redis | Datastore | `catbox-redis` session cache | Session state only | `REDIS_USERNAME` / `REDIS_PASSWORD` |
| GOV.UK | External (link only) | `SCA_URL`, `DEFRA_URL` and GOV.UK footer links | Outbound hyperlinks; no data exchanged | None |

> The two backend paths above are what the code actually calls. They do not match the
> endpoints currently recorded for this edge in the integration catalogue, and they are not
> served by `aqie-dc-backend` on `main` — see Section 11.

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| Members of the public | All `GET` routes | Register search and detail pages |

No AQIE service calls this frontend.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** Redis only, and only for session state via `@hapi/yar` and `catbox-redis`. When
  `SESSION_CACHE_ENGINE` selects the in-memory engine, no external store is used.
- **Key entities:** none are owned. Appliance and fuel records are read from the backend per
  request and shaped for display; the service holds no register data of its own.
- **Retention / refresh:** no caching of register data — every finder or detail page request
  fetches from the backend. Session TTL is `SESSION_CACHE_TTL`; cookie lifetime is
  `SESSION_COOKIE_TTL`; static assets are cached for `STATIC_CACHE_TIMEOUT`.

## 8. Configuration

Environment variable names only — never values.

| Variable | Purpose |
|---|---|
| `PORT`, `HOST` | HTTP listener |
| `NODE_ENV`, `SERVICE_VERSION` | Runtime identity |
| `BACKEND_URL` | Base URL of `aqie-dc-backend` |
| `CDP_X_API_KEY` | API key sent to the backend on every request |
| `DEFRA_URL`, `SCA_URL` | GOV.UK destinations for the DEFRA organisation page and smoke control area rules |
| `REDIS_HOST`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_KEY_PREFIX`, `REDIS_TLS` | Redis session store |
| `SESSION_CACHE_ENGINE`, `SESSION_CACHE_NAME`, `SESSION_CACHE_TTL`, `USE_SINGLE_INSTANCE_CACHE` | Session cache behaviour |
| `SESSION_COOKIE_PASSWORD`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_TTL` | Session cookie |
| `ASSET_PATH`, `STATIC_CACHE_TIMEOUT` | Static asset serving |
| `HTTP_PROXY` | CDP egress proxy |
| `ENABLE_SECURE_CONTEXT` | TLS trust store |
| `ENABLE_METRICS`, `TRACING_HEADER` | Observability |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`;
  production entrypoint `node src`, with the webpack frontend bundle built beforehand.
- **Internal address:** `https://aqie-dc-frontend.<env>.cdp-int.defra.cloud`.
- **Environments:** `dev`, `test`, `perf-test`, `prod`.
- **Local development:** `compose.yml` provides Redis.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — lint, test and quality gate on PR, plus a
    scheduled run
  - `.github/workflows/publish.yml` — build and publish on push to `main`
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, ECS-formatted in production.
- **Tracing:** `@defra/hapi-tracing` propagating `TRACING_HEADER`.
- **Metrics:** `aws-embedded-metrics` (CloudWatch EMF), gated by `ENABLE_METRICS`.
- **Security headers:** HSTS, XSS protection, no-sniff and frame protection are set on the
  Hapi server; a content security policy is applied via `@hapi/scooter`.
- **Shutdown:** `hapi-pulse` for graceful draining.

## 11. Open Questions

- [ ] **The frontend and backend contracts do not line up.** This service calls
      `GET /get-all/{type}` and `GET /get/{type}/{id}`; `aqie-dc-backend` on `main` serves
      `GET /api/appliances/search`, `GET /api/fuels/search`, `GET /appliances` and
      `GET /fuels`. Confirm whether the deployed public register is currently working, and
      which side is expected to change.
- [ ] The integration catalogue records this edge as using `/api/appliances/search`,
      `/api/fuels/search` and `POST /applications`. There is no `POST` to the backend anywhere
      in this repository. The catalogue entry needs correcting.
- [ ] `CDP_X_API_KEY` is sent on every backend request but `aqie-dc-backend` does not read it.
      Confirm where, if anywhere, that key is enforced.
- [ ] The service was last changed in April 2026 while the backend and admin frontend have
      continued to move. Confirm whether the public register is still in active development or
      awaiting a rebuild against the current backend contract.
- [ ] `fetchAll` returns an empty array and `fetchById` returns null on any backend failure, so
      a backend outage renders as an empty register rather than an error. Confirm this is the
      intended citizen-facing behaviour.
- [ ] A debug `console.log` of the full record returned from the database remains in
      `src/server/common/api/api.js`. Confirm it can be removed — register records include
      applicant contact details.
- [ ] Confirm the Welsh content is owner-approved translation rather than placeholder.

