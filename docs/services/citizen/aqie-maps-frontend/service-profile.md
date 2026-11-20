# aqie-maps-frontend

> A full-screen interactive map of the UK air quality monitoring network. It plots the active
> monitoring stations, colours each marker by its observed DAQI value and shows station detail on
> selection, using data served by `aqie-back-end` (with forecasts from `aqie-forecast-api`). It
> links to and from the historic data service, `aqie-dataselector-frontend`.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-maps-frontend`](https://github.com/DEFRA/aqie-maps-frontend) |
| Service domain | `Citizen` |
| Service type | `Auxilary Frontend` |
| Lifecycle stage | `Beta` |
| Primary language | JavaScript |
| Runtime | Node.js `>=24` (ES modules; `.nvmrc` pins v24.14.1) |
| Default branch | `main` |
| Created (UTC) | `2026-06-08` |
| Last main commit (UTC) | `2026-11-18T11:27:49Z` |
| Last analysed commit | `13a9eb7f` |
| Last analysed (UTC) | `2026-11-19T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Renders a pannable, zoomable map of the United Kingdom using the pre-release
  `@defra/interactive-map` component over a MapLibre provider, with OpenFreeMap vector tiles. The
  panels become bottom sheets on narrow screens, and on-page zoom buttons replace the component's
  built-in ones.
- Plots each active monitoring station as a marker. Closed and inactive stations are not plotted
  and cannot be selected.
- Colours each marker by the station's observed DAQI value from the AURN dataset, using the ten
  official DAQI colours, with the index shown on the marker. The highest values are drawn on top.
  A station with no index in the data is still plotted, grey and without a number, and its panel
  reads "Not available". The map neither hides nor estimates it.
- Shows a station detail panel with the station name and status, the pollutants monitored there,
  the observed DAQI value and band, local authority, site type and start date.
- Provides a pollutant filter (the five DAQI pollutants; an "Other pollutants" tab is a
  placeholder), a "Data sources" group that offers only AURN, and a map key. Markers can be
  operated from the keyboard.
- Links from the station panel to the full station summary on `aqie-dataselector-frontend`, as a
  form post from the citizen's browser. The map view is kept in the browser's session storage for
  up to 30 minutes, so the citizen returns to where they were.
- Accepts a form post at `/map/view` from `aqie-dataselector-frontend` and opens the map zoomed to
  that station with it selected.
- Loads forecast points from `aqie-forecast-api` on every map load. The code to colour markers from
  the forecast point nearest a station (within about 5 km) for a chosen day remains, but the
  forecast tab was hidden on purpose in August 2026 ("until design implementation is ready"), so no
  control in the page templates selects that view.
- Proxies the upstream data through its own server-side `/api/*` endpoints, so the browser never
  calls `aqie-back-end` directly and no cross-origin requests or API keys are exposed.
- Serves a cookie banner and cookies page consistent with the wider service. Analytics load only
  after consent.

**Does not:**

- Ingest or store air quality data. It holds no measurement database and performs no
  scheduled work.
- Resolve place-name or postcode searches. There is no gazetteer integration here; location
  search belongs to `aqie-front-end`.
- Run the alert sign-up journey or hold any subscriber data — that is `aqie-front-end` with
  `aqie-notify-service` and `aqie-alert-back-end-service`.
- Show historic data or station readings. The station summary page on
  `aqie-dataselector-frontend` does that.
- Serve pollutant explainer, health-effects or statutory content. Its only content page is the
  cookies page; `/about` is an empty placeholder.
- Calculate DAQI values from raw concentrations. It maps an index to a colour and band label;
  the index comes from `aqie-back-end` (observed) or `aqie-forecast-api` (forecast).
- Show when an AURN reading was taken. It reads only each station's ID and DAQI index and ignores
  the measurement times, so it cannot show how old an index is.

## 3. Architecture

**Pattern:** Hapi server rendering Nunjucks views, with a client-side map bundle built by Vite.
Each page and each internal API endpoint is a Hapi plugin under `src/server/routes/`, registered
through a single router plugin. Two thin helpers wrap the upstream services; all outbound calls
use `undici` with explicit timeouts. The browser holds most of the behaviour: it fetches the
data, joins stations to DAQI values and draws the markers.

| Component | Path | Responsibility |
|---|---|---|
| Router | `src/server/plugins/router.js` | Registers page routes, internal API routes and asset serving |
| Map page | `src/server/routes/map/` | `GET /map`, plus `POST /map/view` with its Joi payload schema, which renders the map at a posted station |
| Home and about | `src/server/routes/home/`, `src/server/routes/about/` | Landing page with a start button; `/about` is an empty placeholder |
| Internal API | `src/server/routes/api/` | Server-side proxy endpoints for stations, station info, forecasts and AURN data |
| Cookies | `src/server/routes/cookies/` | Cookie policy page and consent handling |
| Health | `src/server/routes/health/` | Liveness endpoint for the platform |
| Back-end client | `src/server/common/helpers/aqie-back-end.js` | `undici` client for `aqie-back-end`, with a long timeout for station info |
| Forecast client | `src/server/common/helpers/aqie-forecast-api.js`, `http-client.js` | Calls `aqie-forecast-api`; when no forecast URL is set it falls back to `GET /forecasts` on `aqie-back-end`, an endpoint that no longer exists |
| Content security policy | `src/server/plugins/content-security-policy.js` | `blankie` policy allowing the tile and analytics origins, and the dataselector origin as a form target |
| Session cache | `src/server/plugins/session-cache.js`, `src/server/common/helpers/session-cache/`, `redis-client.js` | `yar` session with Catbox Redis or in-memory storage; no route currently uses the session |
| Map client | `src/client/javascripts/map.js` | Map set-up, data loading, marker plotting and click selection |
| Map data and DAQI | `src/client/javascripts/map-station-data.js`, `map-daqi.js`, `map-utils.js` | Data loaders, station and forecast matching, DAQI palette and marker drawing |
| Map panels | `src/client/javascripts/map-station-panel.js`, `map-filter-panel.js`, `map-panels.js`, `map-zoom-controls.js` | Station panel and its dataselector form, pollutant filter, panel and key behaviour on small screens, zoom buttons |
| Map state and access | `src/client/javascripts/map-view-state.js`, `map-marker-accessibility.js` | Saving and restoring the view in session storage, reading the station posted to `/map/view`, and keyboard access to markers |
| Station list | `src/client/javascripts/station-list.js`, `src/server/common/templates/partials/station-list.njk` | Builds a grouped station list inside a hidden container, so citizens never see it |
| Consent and analytics | `src/client/javascripts/cookie-banner.js`, `cookie-functions.js`, `cookies-page.js`, `load-analytics.js` | Consent cookie handling and consent-gated analytics |
| Config | `src/config/config.js` | `convict` schema — upstream URLs, Redis, session and logging settings |

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/health` | Liveness probe | — | Status payload |
| `GET` | `/` | Landing page with a "View map" start button | — | HTML |
| `GET` | `/about` | Placeholder page with no content | — | HTML |
| `GET` | `/map` | Full-screen interactive map | — | HTML |
| `POST` | `/map/view` | Opens the map at a station, for the dataselector's "View map of nearby monitoring stations" form | Form fields `lat` and `lng` (inside a UK bounding box) and optional `siteId` (letters and digits, up to 12); payload limit 1 KB | HTML map page; invalid input redirects to `/map` |
| `GET` | `/cookies` | Cookie policy and consent | — | HTML |
| `GET` | `/api/monitoring-stations` | Station list for map plotting | — | JSON passed through from `aqie-back-end` |
| `GET` | `/api/monitoring-station-info` | Detail for stations (120 second upstream timeout); nothing in this repository calls it | — | JSON passed through from `aqie-back-end` |
| `GET` | `/api/forecasts` | Forecast values (called on every map load) | — | JSON from `aqie-forecast-api` |
| `GET` | `/api/aurn-data` | Observed DAQI index per AURN station, used to colour markers | — | JSON passed through from `aqie-back-end` |
| `GET` | `/public/{param*}` | Compiled client assets | — | Static files |
| `GET` | `/map-assets/{param*}` | Files of the `@defra/interactive-map` package, served from `node_modules` | — | Static files |
| `GET` | `/favicon.ico` | Empty icon response (production) | — | `204` |

> The `/api/*` routes exist purely so the browser talks only to this service. They are thin,
> unauthenticated, uncached pass-throughs and are not intended as a public API. An upstream
> failure returns `500` with a short message; the browser treats that as no data.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-back-end` | AQIE service | `GET /monitoringStations` | Full station list for map plotting | CDP internal network |
| `aqie-back-end` | AQIE service | `GET /aurnData` | Observed DAQI index per AURN station, which colours the markers. Only the site ID and index are read; measurement times and per-pollutant values are ignored | CDP internal network |
| `aqie-back-end` | AQIE service | `GET /monitoringStationInfo` (120 second timeout), reached only through `GET /api/monitoring-station-info`, which nothing in this repository calls | Station detail | CDP internal network |
| `aqie-back-end` | AQIE service | `GET /forecasts` — **endpoint removed by [PR #163](https://github.com/DEFRA/aqie-back-end/pull/163)**; the fallback code is still present and would now 404 | Forecast fallback, used only when `AQIE_FORECAST_API_URL` is unset. The variable is set in every environment the service is deployed to, per CDP environment configuration (checked 2026-11-19), so the fallback is not reached | CDP internal network |
| `aqie-forecast-api` | AQIE service | `GET /forecast` | Forecast DAQI values by day and location | CDP internal network |
| `aqie-dataselector-frontend` | AQIE service (browser-side link) | `POST /station-summary`, submitted as a form by the citizen's browser when `DATASELECTOR_FRONT_END_URL` is set | Station latitude, longitude and name | None (public route) |
| OpenFreeMap | External | `https://tiles.openfreemap.org/styles/liberty` | Vector basemap tiles requested by the browser | None |
| Google Tag Manager / Google Analytics | External (browser) | Tags loaded in the citizen's browser, gated by cookie consent | Page analytics events | None |
| Redis | Datastore | Catbox Redis session cache | Session state (nothing is currently stored) | `REDIS_USERNAME` / `REDIS_PASSWORD` |

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| `aqie-dataselector-frontend` | `POST /map/view` (station page "View map of nearby monitoring stations" form); `GET /map` ("Search on a map" link on the hub page, and the Back link from a station opened from the map) | Station latitude, longitude and local site ID. The citizen's browser follows the link; there is no server-to-server call |

No other AQIE service links to or calls this one. Citizens reach it directly.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** no database. Redis (via `@hapi/catbox-redis` and `ioredis`) backs the `yar` session
  cache in deployed environments, with `@hapi/catbox-memory` used locally, but no route reads or
  writes a session, so nothing is stored. The local `compose.yml` starts Redis and a Floci AWS
  emulator with no resources configured; it does not start MongoDB. In the citizen's browser, the
  map view is held in `sessionStorage` and consent in the `airaqie_cookies_analytics` cookie.
- **Key entities:** a *station* (`localSiteID`, name, status, coordinates as latitude then
  longitude, pollutants monitored, area, local authority, site type, open and close dates), an
  *AURN reading* (`localSiteID` and `daqiIndex`; the response also carries measurement times and
  per-pollutant values, which the map ignores) and a *forecast point* (location and a DAQI value
  by day). The browser joins readings to stations by site ID to produce the marker colour; forecast
  points are matched to stations by nearest point.
- **Retention / refresh:** none held. Data is fetched from upstream on each map load (the browser
  requests the station list twice, once for the markers and once for the hidden station list);
  freshness is governed by the ingest schedules in `aqie-back-end` and `aqie-forecast-api`. Since
  `aqie-back-end` PR #165 (2026-10-30) an AURN index is calculated only where at least 75% of the
  readings are present, so more stations can have none and show grey. A station whose new index
  cannot be calculated keeps its previous record in `aqie-back-end`, so the map can show an older
  index as current. A saved map view expires after 30 minutes and is used once. Static assets are
  cached for `STATIC_CACHE_TIMEOUT`.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `HOST`, `PORT`, `NODE_ENV`, `SERVICE_VERSION` | Runtime identity and HTTP listener |
| `AQIE_BACK_END_URL` | Base URL for `aqie-back-end` |
| `AQIE_FORECAST_API_URL` | Base URL for `aqie-forecast-api`. Optional in the schema; when unset the service falls back to `aqie-back-end`, which no longer serves the forecast endpoint |
| `DATASELECTOR_FRONT_END_URL` | Optional browser-reachable base URL of `aqie-dataselector-frontend`. Sets the target of the station summary link and is added to the `form-action` content security policy. The link is hidden when it is unset |
| `ASSET_PATH`, `STATIC_CACHE_TIMEOUT` | Static asset base path and cache window |
| `SESSION_CACHE_ENGINE`, `SESSION_CACHE_NAME`, `SESSION_CACHE_TTL`, `USE_SINGLE_INSTANCE_CACHE` | Session cache engine selection |
| `SESSION_COOKIE_PASSWORD`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_TTL` | Session cookie behaviour and signing. The service refuses to start in production with the built-in default password |
| `REDIS_HOST`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_KEY_PREFIX`, `REDIS_TLS` | Redis connection |
| `HTTP_PROXY` | CDP egress proxy |
| `ENABLE_SECURE_CONTEXT` | TLS trust store |
| `TRACING_HEADER` | Observability header to propagate |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT`, `LOG_REDACT` | Logging and redaction |

> `OS_NAMES_API_KEY` appears in `.env.example` and the README as required for an Ordnance Survey
> names lookup, but no code reads it.

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`
  (parent image `3.0.5-node24.14.1`); exposed port `3000`; entrypoint `node src`, with a
  development stage running `npm run docker:dev`.
- **Internal address:** `https://aqie-maps-frontend.<env>.cdp-int.defra.cloud`.
- **Environments:** `dev`, `test`, `prod`.
- **Build:** Vite serves client assets in development through a Hapi middleware bridge and
  produces the static bundle for production.
- **Local development:** `compose.yml` provides Redis and a Floci AWS emulator on the shared
  `cdp-tenant` network; the upstream URLs point at locally running services.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — on pull request: dependency review (fails on
    high severity), `audit-ci` security audit, build, format check, lint, tests, a Docker image
    build and SonarCloud analysis
  - `.github/workflows/publish.yml` — build, test, publish through the CDP build action and
    SonarCloud analysis on push to `main`
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, formatted with `@elastic/ecs-pino-format`, with
  redaction configured through `LOG_REDACT`.
- **Tracing:** `@defra/hapi-tracing` propagating the header named in `TRACING_HEADER`.
- **Metrics:** `@defra/cdp-metrics`.
- **Security headers:** `blankie` with `@hapi/scooter` enforces a content security policy that
  allows the OpenFreeMap tile origin, the Google analytics origins and, when configured, the
  dataselector origin as a form target. Hapi also sets HSTS, `nosniff` and frame protection.
- **Shutdown:** `hapi-pulse` for graceful draining.
- **Code quality:** SonarCloud quality gate, security rating and coverage badges on the repository.

## 11. Open Questions

- [ ] (catalogue `oq-017`) The `GET /forecasts` fallback to `aqie-back-end` now targets a removed endpoint and the code
      is still present. `AQIE_FORECAST_API_URL` is set in every environment the service is
      deployed to, per CDP environment configuration (checked 2026-11-19), so the fallback is
      not reached; delete it.
- [ ] (catalogue `oq-017`) The map page fetches forecasts on every load, but the forecast tab was hidden in August 2026
      "until design implementation is ready" and no control selects that view. Confirm whether it
      is meant to return. If not, remove the fetch and the code.
- [ ] `GET /api/monitoring-station-info` is unused by this repository and triggers live calls
      upstream on every request. Remove the route, or cache and rate-limit it.
- [ ] (catalogue `oq-035`) This service uses `DATASELECTOR_FRONT_END_URL` as a browser form target, and the dataselector's
      built-in default for the reverse link is a CDP-internal address. Confirm the addresses
      configured in each environment can be reached from a citizen's browser, not only from the
      internal network.
- [ ] (catalogue `oq-030`) `aqie-back-end` keeps a station's last AURN record when it cannot calculate a new index
      (75% data-capture rule since its PR #165), and this map ignores the reading times, so an
      older index can be shown as current. Confirm this is intended, and whether the back-end
      should drop stale records or the map should show the reading time.
- [ ] A station with no AURN index is drawn grey, but the map key has no grey entry, and a failed
      `/api/aurn-data` call looks the same. Decide how the key and panel should explain missing
      data.
- [ ] Nothing reads or writes the session, yet production depends on Redis at start-up. Confirm
      whether the session cache is still needed.
- [ ] Template leftovers: `OS_NAMES_API_KEY` is documented but unread, `/about` is empty,
      `@defra/cdp-auditing` is declared but never imported, and the compose MongoDB references
      are commented-out text. Confirm whether a place search is planned and remove the rest.
- [ ] Confirm the intended public address and whether this map will be linked from, or merged
      into, `aqie-front-end`.
- [ ] (catalogue `oq-008`) Confirm that OpenFreeMap is an acceptable long-term tile provider for a production
      service, or whether an OS basemap is intended.
