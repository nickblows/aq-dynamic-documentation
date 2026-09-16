# aqie-maps-prototype

> A GOV.UK Prototype Kit spike that proved the `@defra/interactive-map` component could plot the
> UK monitoring network from live `aqie-back-end` data. It is the predecessor of
> `aqie-maps-frontend`.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-maps-prototype`](https://github.com/DEFRA/aqie-maps-prototype) |
| Service domain | `Citizen` |
| Service type | `Prototype Service (including PoC)` |
| Lifecycle stage | `Prototype/PoC` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22` (CommonJS) |
| Default branch | `main` |
| Created (UTC) | `2026-05-05` |
| Last main commit (UTC) | `2026-06-05T15:31:51Z` |
| Last analysed commit | `1b9a8a53` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Monitoring` |

## 2. Purpose and Responsibilities

**Does:**

- Demonstrates a full-screen interactive map of the UK monitoring network, built with
  `@defra/interactive-map` over a MapLibre provider and OpenFreeMap tiles.
- Plots monitoring stations and colours them by DAQI band, filtered by pollutant (NO₂, O₃,
  SO₂, PM2.5, PM10), with an option to show or hide inactive stations.
- Shows a station detail panel and a companion station list for keyboard and non-map access.
- Proxies `aqie-back-end` and `aqie-forecast-api` through its own Express routes, so the
  browser makes same-origin calls only.
- Displays a live connection banner: the browser polls an internal health route every few
  seconds and shows whether the configured back end is reachable, which made it easy to
  demonstrate against a locally running `aqie-back-end` or a deployed one.

**Does not:**

- Serve production traffic. It is a Prototype Kit application behind CDP basic authentication
  and carries no service-level commitments.
- Ingest, calculate or store any air quality data — it holds no database and no scheduled work.
- Resolve place-name or postcode searches. There is no gazetteer integration.
- Provide the statutory cookie, privacy or accessibility content that a live service needs;
  `aqie-maps-frontend` is where that behaviour was implemented.
- Receive further development. It has been superseded by `aqie-maps-frontend`, which
  reimplements the same idea on Hapi with the CDP frontend template.

## 3. Architecture

**Pattern:** GOV.UK Prototype Kit (Express and Nunjucks) with a single route file and one thin
upstream client. All rendering is server-side; the map is a client-side enhancement driven by
same-origin `fetch` calls to the prototype's own routes.

| Component | Path | Responsibility |
|---|---|---|
| Routes | `app/routes.js` | Page routes and the internal JSON proxy routes |
| Back-end client | `app/api/aqieBackEnd.js` | `fetch` wrapper for `aqie-back-end` and `aqie-forecast-api`, with per-call timeouts |
| Map client | `app/assets/javascripts/map.js` | Map initialisation, DAQI colouring, pollutant filter, marker plotting |
| Station list | `app/assets/javascripts/station-list.js` | Loads the station list and hands it to the map |
| Connection banner | `app/assets/javascripts/backend-poll.js` | Polls the internal health route and updates the connected/not-connected banner |
| Views | `app/views/` | Landing page, map page and the station list, station panel and banner partials |
| Config | `app/config.json` | Prototype Kit service name and plugin settings |

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/` | Landing page with a link to the map and the connection banner | — | HTML |
| `GET` | `/map` | Full-screen map page | — | HTML |
| `GET` | `/api/health` | Reports whether the configured back end responded, and at which URL | — | `{ connected, url }` |
| `GET` | `/monitoringStations` | Station list for map plotting | — | JSON passed through from `aqie-back-end` |
| `GET` | `/monitoringStationInfo` | Station detail (120 second timeout) | — | JSON passed through from `aqie-back-end` |
| `GET` | `/forecasts` | Forecast values for DAQI colouring | — | JSON from `aqie-forecast-api` |

> Upstream failures on the station routes are surfaced as `502` with a short message, and the
> map degrades rather than failing the page.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-back-end` | AQIE service | `GET /health` | Connectivity probe behind the connection banner | CDP internal network |
| `aqie-back-end` | AQIE service | `GET /monitoringStations` | Full station list for map plotting | CDP internal network |
| `aqie-back-end` | AQIE service | `GET /monitoringStationInfo` | Station detail for the selected-station panel | CDP internal network |
| `aqie-forecast-api` | AQIE service | `GET /forecast` | Forecast DAQI values used to colour markers | CDP internal network |
| OpenFreeMap | External | `https://tiles.openfreemap.org/styles/liberty` | Vector basemap tiles requested by the browser | None |

## 6. Consumed By (Inbound Dependencies)

No AQIE service consumes this one. It is a standalone prototype reached directly in a browser.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** none. No database, cache or message queue. Prototype Kit session defaults live in
  `app/data/session-data-defaults.js` and are not used for air quality data.
- **Key entities:** a *station* (name, status, coordinates, pollutants) and a *forecast entry*
  (DAQI value), joined in the browser to produce marker colour.
- **Retention / refresh:** none. Every page view fetches live from upstream.

## 8. Configuration

Variable names only — values are set as CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `AQIE_BACK_END_URL` | Base URL for `aqie-back-end`; falls back to a local development address |
| `AQIE_FORECAST_API_URL` | Base URL for `aqie-forecast-api` |
| `PORT`, `NODE_ENV` | HTTP listener and runtime mode |
| `PASSWORD`, `PASSWORD_KEYS` | GOV.UK Prototype Kit basic authentication, required on CDP |
| `USE_HTTPS` | Disabled in the production image because CDP terminates TLS at the nginx layer |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`;
  `curl` is added to the production image for the CDP health check. Development runs
  `npm run dev`, production runs `npm start`.
- **Access control:** Prototype Kit basic authentication is on by default in CDP environments;
  the password is supplied through the CDP Portal secrets page.
- **Environments:** `dev` (prototype environments only).
- **Local development:** `compose.yml` joins the shared `cdp-tenant` network and points
  `AQIE_BACK_END_URL` and `AQIE_FORECAST_API_URL` at locally running services.
- **Pipelines:**
  - `.github/workflows/publish.yml` — build and publish on push to `main`

## 10. Observability

- **Logging:** default GOV.UK Prototype Kit / Express console logging. No structured logging,
  ECS formatting or log shipping.
- **Tracing:** none.
- **Metrics:** none. The only health signal is the internal `/api/health` route used by the
  in-page connection banner, which is not wired to platform monitoring.

## 11. Open Questions

- [ ] Confirm this prototype can be archived now that `aqie-maps-frontend` exists, or state
      what it is still being kept for.
- [ ] Confirm whether it is still deployed to any CDP environment, and if so who has the
      basic-authentication password.
