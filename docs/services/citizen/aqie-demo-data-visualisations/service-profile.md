# aqie-demo-data-visualisations

> A non-production spike exploring accessible, interactive hourly pollution graphs for each
> monitoring station. It answers whether hourly site graphs could be delivered into the
> "Get air pollution data" service, and at what cost.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-demo-data-visualisations`](https://github.com/DEFRA/aqie-demo-data-visualisations) |
| Service domain | `Citizen` |
| Service type | `Demo Service` |
| Lifecycle stage | `Prototype/PoC` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22` (CommonJS) |
| Default branch | `main` |
| Created (UTC) | `2026-07-30` |
| Last main commit (UTC) | `2026-10-07T09:10:49Z` |
| Last analysed commit | `7f8d8f53` |
| Last analysed (UTC) | `2026-11-19T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Lets a user find a monitoring station by town or place name, postcode or outcode, or by part
  of a station name, and ranks the nearest stations by great-circle distance.
- Shows a per-station pollutant summary table: average over the selected window, data capture
  percentage and hourly exceedances, rendered server-side so it works without JavaScript.
- Draws interactive hourly charts with D3 as a progressive enhancement, in either a combined
  overlay or small-multiples layout, over the last 24 hours or the last 7 days.
- Reads the station list and the hourly readings directly from the Ricardo UK-AIR API, logging
  in with its own account credentials. It caches the station list for six hours and the bearer
  token for fifty minutes, and fetches readings live on every request, one call per pollutant.
- Maps Ricardo's pollutant names onto five canonical pollutants (requesting PM10 as `GE10` and
  PM2.5 as `PM25`, which Ricardo requires), keeps only hourly rows because SO₂ also returns
  15-minute rows, and turns `-9999` and other negative values into gaps, which is what the
  data-capture percentage measures.
- Anchors each window on the most recent reading rather than the clock, so a station that has
  stopped publishing shows a gap, and lists current stations only.
- Applies legal hourly limits only where one exists (NO₂ 200 µg/m³, SO₂ 350 µg/m³), keeping
  DAQI bands separate as a health index rather than a legal threshold.
- Carries a written feasibility assessment and productionisation notes: where the Ricardo call
  should live in production, the silent 10,000-row cap on longer ranges, extending beyond 24
  hours and 7 days, station coverage, porting to the CDP front-end stack, tests and a shared
  cache.

**Does not:**

- Depend on any AQIE service. It no longer calls `aqie-back-end`: the station list and the
  hourly readings come straight from the Ricardo UK-AIR API and geocoding from postcodes.io, so
  nothing else has to be running or changed for it to work.
- Persist anything. There is no database, message queue or scheduled job. Only two in-process
  caches exist (station list, bearer token); readings are fetched live on every request.
- Serve production traffic or carry service-level commitments. It is a Prototype Kit
  application behind CDP basic authentication.
- Provide the alert, forecast or map journeys — those are `aqie-front-end` and
  `aqie-maps-frontend`.
- Replace the bulk archive download journey, which belongs to `aqie-dataselector-frontend` and
  `aqie-historicaldata-backend`.

## 3. Architecture

**Pattern:** GOV.UK Prototype Kit (Express and Nunjucks), not Hapi, with an `app/` source tree
rather than `src/`. All outbound calls run server-side, so there is no cross-origin request and
no API key in the browser. Tables are server-rendered; the D3 charts hydrate from a JSON block
embedded in the page.

| Component | Path | Responsibility |
|---|---|---|
| Routes | `app/routes.js` | Landing, search results, station page and the station data endpoint |
| Ricardo client | `app/lib/ricardo-api.js` | Logs in to Ricardo, caches the bearer token and the station list, fetches hourly readings per pollutant, trims each window to end at the latest reading, and runs the connectivity probe |
| Search | `app/lib/search.js` | Resolves postcodes, outcodes, station names and place names, then ranks by haversine distance |
| Station view model | `app/lib/station-view.js`, `app/lib/summary.js` | Builds the summary table, exceedance counts and data-capture percentages for the shown window |
| Reference data | `app/data/pollutants.js`, `app/data/legal-limits.js` | The five canonical pollutants and the hourly legal limits |
| Proxy | `app/lib/proxy.js` | Picks the egress proxy from `HTTPS_PROXY`, `HTTP_PROXY`, `CDP_HTTPS_PROXY` or `CDP_HTTP_PROXY` in that order, sets an `undici` proxy dispatcher that bypasses localhost and `.cdp-int.defra.cloud` hosts, and can probe a `CONNECT` tunnel for diagnostics |
| Error description | `app/lib/describe-error.js` | Turns opaque `fetch` failures into readable causes |
| Filters | `app/filters.js` | `readingTime`, which formats reading times in UTC |
| Charts | `app/assets/javascripts/charts.js`, `vendor/d3.min.js` | SVG charts, loaded only on the station page |
| Views | `app/views/` | Landing, station list, station detail and not-found pages, plus two placeholder pages for the map and dataset journeys |

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/` | Landing page with the search form and an upstream connectivity summary | — | HTML |
| `GET` | `/stations` | Search results, ranked by distance where the query geocoded | `q` | HTML; redirects to `/` when `q` is empty |
| `GET` | `/station/{siteId}` | Station page: summary table, data tables and charts. `siteId` is the Ricardo site id (the `UKA…` form) | `period` (`24h`, `7d`), `layout` (`combined`, `small-multiples`) | HTML, or `404` with a not-found page for an unknown station |
| `GET` | `/station/{siteId}/data.json` | The hourly series behind the charts | `period` | `{ siteId, period, resolution, from, to, pollutants }` |
| `GET` | `/search-on-a-map`, `/create-and-download-datasets` | Placeholder pages linked from the service navigation, rendered by the Prototype Kit from `app/views` | — | HTML |

> Every variant is a shareable link, which was used to run user research on the layout and
> timeframe options.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| Ricardo UK-AIR API | External API | `POST /api/login_check`, `GET /api/site_meta_datas`, `GET /api/pollutant_measurement_datas` | Account credentials in and a bearer token out; the station list with per-pollutant metadata; hourly readings for one station and pollutant over a date window | Bearer token obtained by logging in with an account email and password (`RICARDO_API_EMAIL`, `RICARDO_API_PASSWORD`) |
| postcodes.io | External API | `GET /postcodes/{postcode}`, `GET /outcodes/{outcode}`, `GET /places?q=` | Postcode, outcode or place name in; coordinates out | None |

> The demo depends on no AQIE service. It used to read stations from `aqie-back-end`
> `/measurements` and hourly series from the DEFRA Sensor Observation Service. PR #15 (merged
> 2026-10-07) replaced both with the direct Ricardo calls above, so the removal of
> `/measurements` by [PR #163](https://github.com/DEFRA/aqie-back-end/pull/163) no longer
> affects it. It was not moved to `/monitoringStationInfo`. Ricardo is called on its production
> host by default, and every data call leaves the platform through the egress proxy. See
> [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml) `oq-018`.

## 6. Consumed By (Inbound Dependencies)

No AQIE service consumes this one. It is a standalone demonstration reached directly in a browser.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** none. No database, queue or build step. Two per-instance in-process caches only:
  the station list (six hours) and the Ricardo bearer token (fifty minutes).
- **Key entities:** a *station* (Ricardo `siteId` in the `UKA…` form, `localSiteId`, name, area,
  `latitude` and `longitude` as numbers, and the pollutants it currently reports) and a *series*
  of `{ time, value }` points per pollutant. `value` is null where the instrument produced no
  reading.
- **Retention / refresh:** readings are not retained. They are fetched live on every request,
  one call per pollutant. Because the caches are per instance, replicas warm independently.
- **Windows:** only 24-hour and 7-day windows are served, both at hourly resolution (24 and 168
  points per pollutant). Ricardo takes whole dates, so a request returns slightly more than the
  window and the series is trimmed to end at the latest reading. Ricardo caps a result at
  10,000 rows without an error, and the client logs a warning when a response is exactly at
  the cap.

## 8. Configuration

Variable names only — values are set as CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `RICARDO_API_EMAIL`, `RICARDO_API_PASSWORD` | Ricardo account credentials used for the login |
| `RICARDO_API_LOGIN_URL`, `RICARDO_API_ALL_DATA_URL`, `RICARDO_API_SITE_ID_URL` | Override the login, station-list and readings URLs. Each defaults to the production Ricardo host. All three are set in the dev environment, per CDP environment configuration |
| `RICARDO_TIMEOUT_MS` | Timeout for each Ricardo call (default 20 seconds) |
| `AQIE_BACK_END_URL`, `SOS_URL` | **No longer read** by the code. `AQIE_BACK_END_URL` is still set in the dev environment, per CDP environment configuration |
| `CDP_HTTPS_PROXY`, `CDP_HTTP_PROXY`, `HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY` | CDP egress proxy selection and bypass list |
| `PORT`, `NODE_ENV` | HTTP listener and runtime mode |
| `PASSWORD`, `PASSWORD_KEYS`, `USE_AUTH` | GOV.UK Prototype Kit basic authentication, required on CDP unless `USE_AUTH` is false |
| `USE_HTTPS` | Disabled in the production image because CDP terminates TLS at the nginx layer |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`.
  Development runs `npm run dev`, production runs `npm start`.
- **Egress:** Node's global `fetch` ignores the standard proxy variables, so the service sets an
  `undici` proxy dispatcher explicitly at start-up and excludes `localhost`,
  `.cdp-int.defra.cloud` and any hosts in `NO_PROXY` from it. Every data call now goes through
  the proxy.
- **Access control:** Prototype Kit basic authentication is on by default in CDP environments.
- **Environments:** not stated in the repository. Its own deployment configuration was not read beyond the variables noted in section 8.
- **Pipelines:**
  - `.github/workflows/publish.yml` — build and publish on push to `main`

## 10. Observability

- **Logging:** default GOV.UK Prototype Kit / Express console logging, with upstream failure
  causes unwrapped and logged explicitly. No structured logging or log shipping.
- **Tracing:** none.
- **Metrics:** none. The landing page probes the Ricardo login and postcodes.io, and repeats a
  `CONNECT` against each configured proxy variable, then reports the results and the proxy
  address in the page. This is not wired to platform monitoring.
- **Accessibility:** the spike reports zero axe-core WCAG 2.2 A/AA violations across all pages,
  verified with keyboard-only navigation, contrast checks and JavaScript disabled. Charts use
  colour, line style and a legend together rather than colour alone.

## 11. Open Questions

- [ ] (catalogue `oq-039`) The prototype holds Ricardo account credentials itself and defaults to the production
      host. Confirm the account is dedicated and read-only, and who owns it.
- [ ] (catalogue `oq-039`) `.env.template` carries a literal value against `PASSWORD`. Confirm it is a placeholder and
      not the deployed prototype password.
- [ ] The spike's notes say a production version would put the Ricardo call behind a back-end
      service, so that credentials live in one place and the response can be cached across
      replicas. Confirm whether that work is planned, and whether it would be served live or
      from stored history.
- [ ] Readings are fetched live from Ricardo on every request, one call per pollutant, with no
      shared cache and no retry beyond one re-login after a 401. Confirm that is acceptable for
      the user research it supports.
- [ ] Confirm whether postcodes.io is acceptable for location search in this journey, or whether
      it should use the OS Names integration that `aqie-front-end` already has.
- [ ] Confirm whether this demo should be archived once the feasibility decision is taken.
