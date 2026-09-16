# aqie-maps-frontend

> A full-screen interactive map of the UK air quality monitoring network. It plots every
> monitoring station, colours each marker by its DAQI band and shows station detail on
> selection, using data served by `aqie-back-end` and `aqie-forecast-api`.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-maps-frontend`](https://github.com/DEFRA/aqie-maps-frontend) |
| Service domain | `Citizen` |
| Service type | `Auxilary Frontend` |
| Lifecycle stage | `Beta` |
| Primary language | JavaScript |
| Runtime | Node.js `>=24` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2026-06-08` |
| Last main commit (UTC) | `2026-08-25T08:32:08Z` |
| Last analysed commit | `fb412364` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Renders a pannable, zoomable map of the United Kingdom using `@defra/interactive-map` over a
  MapLibre provider, with OpenFreeMap vector tiles.
- Plots each monitoring station as a marker and colours it by DAQI band (green for 1–3, yellow
  for 4–6, red for 7–9, black for 10, grey where the band cannot be determined).
- Derives today's DAQI value for a station from the forecast point nearest to it.
- Shows a station detail panel with the station name and status, today's DAQI value and band,
  the pollutants monitored there and the matched forecast.
- Provides a station list and a filter panel so a station can be found and selected without
  using the map itself.
- Proxies the upstream data through its own server-side `/api/*` endpoints, so the browser
  never calls `aqie-back-end` directly and no cross-origin requests or API keys are exposed.
- Serves a map key overlay, cookie banner and cookies page consistent with the wider service.

**Does not:**

- Ingest or store air quality data. It holds no measurement database and performs no
  scheduled work.
- Resolve place-name or postcode searches. There is no gazetteer integration here; location
  search belongs to `aqie-front-end`.
- Run the alert sign-up journey or hold any subscriber data — that is `aqie-front-end` with
  `aqie-notify-service` and `aqie-alert-back-end-service`.
- Serve pollutant explainer, health-effects or statutory content beyond its own cookies page.
- Calculate DAQI bands from raw concentrations; banding and forecast data come from upstream.

## 3. Architecture

**Pattern:** Hapi server rendering Nunjucks views, with a client-side map bundle built by Vite.
Each page and each internal API endpoint is a Hapi plugin under `src/server/routes/`, registered
through a single router plugin. Two thin helpers wrap the upstream services; all outbound calls
use `undici` with explicit timeouts.

| Component | Path | Responsibility |
|---|---|---|
| Router | `src/server/plugins/router.js` | Registers page routes, internal API routes and asset serving |
| Map page | `src/server/routes/map/` | Renders the full-screen map layout |
| Home and about | `src/server/routes/home/`, `src/server/routes/about/` | Landing page and service explanation |
| Internal API | `src/server/routes/api/` | Server-side proxy endpoints for stations, station info, forecasts and AURN data |
| Cookies | `src/server/routes/cookies/` | Cookie policy page and consent handling |
| Health | `src/server/routes/health/` | Liveness endpoint for the platform |
| Back-end client | `src/server/common/helpers/aqie-back-end.js` | `undici` client for `aqie-back-end`, with a long timeout for station info |
| Forecast client | `src/server/common/helpers/aqie-forecast-api.js` | Calls `aqie-forecast-api`, falling back to `aqie-back-end` when no forecast URL is set |
| Content security policy | `src/server/plugins/content-security-policy.js` | `blankie` policy allowing the tile and analytics origins only |
| Session cache | `src/server/common/helpers/session-cache/`, `redis-client.js` | Catbox Redis or in-memory session storage |
| Map client | `src/client/javascripts/map.js`, `map-daqi.js`, `map-filter-panel.js`, `station-list.js`, `map-utils.js` | Map initialisation, DAQI colouring, filtering and station list behaviour |
| Config | `src/config/config.js` | `convict` schema — upstream URLs, Redis, session and logging settings |

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/health` | Liveness probe | — | Status payload |
| `GET` | `/` | Landing page | — | HTML |
| `GET` | `/about` | Explanation of the map and its data | — | HTML |
| `GET` | `/map` | Full-screen interactive map | — | HTML |
| `GET` | `/cookies` | Cookie policy and consent | — | HTML |
| `GET` | `/api/monitoring-stations` | Station list for map plotting | — | JSON passed through from `aqie-back-end` |
| `GET` | `/api/monitoring-station-info` | Detail for stations, used for the detail panel | — | JSON passed through from `aqie-back-end` |
| `GET` | `/api/forecasts` | Forecast values used for DAQI colouring | — | JSON from `aqie-forecast-api` |
| `GET` | `/api/aurn-data` | AURN network dataset | — | JSON passed through from `aqie-back-end` |
| `GET` | `/public/{param*}` | Compiled client assets and map assets | — | Static files |

> The `/api/*` routes exist purely so the browser talks only to this service. They are thin
> pass-throughs and are not intended as a public API.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-back-end` | AQIE service | `GET /monitoringStations` | Full station list for map plotting | CDP internal network |
| `aqie-back-end` | AQIE service | `GET /monitoringStationInfo` | Station detail for the selected-station panel (120 second timeout) | CDP internal network |
| `aqie-back-end` | AQIE service | `GET /aurnData` | AURN network dataset | CDP internal network |
| `aqie-back-end` | AQIE service | `GET /forecasts` | Forecast fallback, used only when `AQIE_FORECAST_API_URL` is unset | CDP internal network |
| `aqie-forecast-api` | AQIE service | `GET /forecast` | Forecast DAQI values by day and region | CDP internal network |
| OpenFreeMap | External | `https://tiles.openfreemap.org/styles/liberty` | Vector basemap tiles requested by the browser | None |
| Google Tag Manager / Google Analytics | External (browser) | Tag loaded in the citizen's browser, gated by cookie consent | Page analytics events | None |
| Redis | Datastore | Catbox Redis session cache | Session state | `REDIS_USERNAME` / `REDIS_PASSWORD` |

## 6. Consumed By (Inbound Dependencies)

No AQIE service consumes this one. It is a leaf frontend reached directly by citizens.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** no database. Redis (via `@hapi/catbox-redis` and `ioredis`) backs the session
  cache in deployed environments, with `@hapi/catbox-memory` used locally. The local
  `compose.yml` also starts MongoDB, but no application code connects to it.
- **Key entities:** a *station* (name, status, coordinates, pollutants monitored) and a
  *forecast point* (DAQI value by day), joined in the browser by nearest-point matching to
  produce the marker colour.
- **Retention / refresh:** none held. Data is fetched from upstream per request; freshness is
  governed by the ingest schedules in `aqie-back-end` and `aqie-forecast-api`. Static assets
  are cached for `STATIC_CACHE_TIMEOUT`.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `HOST`, `PORT`, `NODE_ENV`, `SERVICE_VERSION` | Runtime identity and HTTP listener |
| `AQIE_BACK_END_URL` | Base URL for `aqie-back-end` |
| `AQIE_FORECAST_API_URL` | Base URL for `aqie-forecast-api`; when unset the service falls back to `aqie-back-end` |
| `ASSET_PATH`, `STATIC_CACHE_TIMEOUT` | Static asset base path and cache window |
| `SESSION_CACHE_ENGINE`, `SESSION_CACHE_NAME`, `SESSION_CACHE_TTL`, `USE_SINGLE_INSTANCE_CACHE` | Session cache engine selection |
| `SESSION_COOKIE_PASSWORD`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_TTL` | Session cookie behaviour and signing |
| `REDIS_HOST`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_KEY_PREFIX`, `REDIS_TLS` | Redis connection |
| `HTTP_PROXY` | CDP egress proxy |
| `ENABLE_SECURE_CONTEXT` | TLS trust store |
| `TRACING_HEADER` | Observability header to propagate |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT`, `LOG_REDACT` | Logging and redaction |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`;
  entrypoint `node src`, with a development stage running `npm run docker:dev`.
- **Internal address:** `https://aqie-maps-frontend.<env>.cdp-int.defra.cloud`.
- **Environments:** `dev`, `test`, `prod`.
- **Build:** Vite serves client assets in development through a Hapi middleware bridge and
  produces the static bundle for production.
- **Local development:** `compose.yml` provides Redis and MongoDB on the shared `cdp-tenant`
  network so the service can reach a locally running `aqie-back-end`.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — lint, test and SonarCloud analysis on pull request
  - `.github/workflows/publish.yml` — build and publish on push to `main`
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, formatted with `@elastic/ecs-pino-format`, with
  redaction configured through `LOG_REDACT`.
- **Tracing:** `@defra/hapi-tracing` propagating the header named in `TRACING_HEADER`.
- **Metrics:** `@defra/cdp-metrics`.
- **Auditing:** `@defra/cdp-auditing`.
- **Security headers:** `blankie` with `@hapi/scooter` enforces a content security policy that
  allows only the OpenFreeMap tile origin and the Google analytics origins.
- **Shutdown:** `hapi-pulse` for graceful draining.
- **Code quality:** SonarCloud quality gate, security rating and coverage badges on the repository.

## 11. Open Questions

- [ ] The local `compose.yml` starts MongoDB and seeds it, but no application code connects to
      it. Confirm whether this is left over from the CDP template and can be removed.
- [ ] Confirm whether the `GET /forecasts` fallback to `aqie-back-end` is used in any deployed
      environment, or whether `AQIE_FORECAST_API_URL` is always set.
- [ ] Confirm the intended public address and whether this map will be linked from, or merged
      into, `aqie-front-end`.
- [ ] Confirm that OpenFreeMap is an acceptable long-term tile provider for a production
      service, or whether an OS basemap is intended.
