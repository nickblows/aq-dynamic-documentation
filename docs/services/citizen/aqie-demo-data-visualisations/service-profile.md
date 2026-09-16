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
| Last main commit (UTC) | `2026-09-09T10:11:22Z` |
| Last analysed commit | `69aab1a2` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Lets a user find a monitoring station by town or place name, postcode or outcode, or by part
  of a station name, and ranks the nearest stations by great-circle distance.
- Shows a per-station pollutant summary table: 24-hour average, data capture percentage and
  hourly exceedances, rendered server-side so it works without JavaScript.
- Draws interactive hourly charts with D3 as a progressive enhancement, in either a combined
  overlay or small-multiples layout, over 24-hour, 7-day, one-month or one-year windows.
- Fetches the full hourly time series directly from the public DEFRA Sensor Observation Service
  (SOS) `GetObservation` feed and decodes the SWE-encoded block server-side, aggregating to
  daily means for the longer windows.
- Canonicalises raw DEFRA parameter identifiers into displayable pollutants (for example
  `GE10` and `GR10` to PM10, `GR25` to PM2.5) and discards sentinel values such as `-9999`,
  which is what the data-capture percentage measures.
- Applies legal hourly limits only where one exists (NO₂ 200 µg/m³, SO₂ 350 µg/m³), keeping
  DAQI bands separate as a health index rather than a legal threshold.
- Carries a written feasibility assessment and productionisation notes, including the proposed
  `GET /measurements/history` contract for `aqie-back-end` and a migration checklist.

**Does not:**

- Change `aqie-back-end` in any way. The spike is deliberately self-contained; the hourly-series
  fetch and decode live here rather than upstream.
- Persist anything. There is no database, cache, message queue or scheduled job — every request
  hits the upstream feeds live.
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
| Back-end client | `app/lib/aqie-api.js` | Fetches the station list from `aqie-back-end` and assembles history responses |
| SOS history | `app/lib/sos-history.js` | Builds the SOS temporal filter, decodes the SWE values block, aggregates to daily means |
| Search | `app/lib/search.js` | Resolves postcodes, outcodes, station names and place names, then ranks by haversine distance |
| Station view model | `app/lib/station-view.js`, `app/lib/summary.js` | Builds the summary table, exceedance counts and data-capture percentages |
| Reference data | `app/data/pollutants.js`, `app/data/legal-limits.js` | Pollutant canonicalisation and the hourly legal limits |
| Proxy | `app/lib/proxy.js` | Sets an `undici` proxy dispatcher, with the back-end host excluded so internal traffic bypasses the egress proxy |
| Error description | `app/lib/describe-error.js` | Turns opaque `fetch` failures into readable causes |
| Charts | `app/assets/javascripts/charts.js`, `vendor/d3.min.js` | SVG charts, loaded only on the station page |
| Views | `app/views/` | Landing, station list, station detail and not-found pages |

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/` | Landing page with the search form and an upstream connectivity summary | — | HTML |
| `GET` | `/stations` | Search results, ranked by distance where the query geocoded | `q` | HTML; redirects to `/` when `q` is empty |
| `GET` | `/station/{siteId}` | Station page: summary table, data tables and charts | `period` (`24h`, `7d`, `month`, `year`), `layout` (`combined`, `small-multiples`) | HTML, or `404` with a not-found page for an unknown station |
| `GET` | `/station/{siteId}/data.json` | The decoded series behind the charts, deliberately shaped like the proposed back-end endpoint | `period` | `{ siteId, period, resolution, pollutants }` |

> Every variant is a shareable link, which was used to run user research on the layout and
> timeframe options.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-back-end` | AQIE service | `GET /measurements` | Station list keyed by `localSiteID`, with the per-pollutant feature-of-interest identifiers | None (CDP internal network) |
| DEFRA Sensor Observation Service | External API | `GET /sos-ukair/service?service=AQD&request=GetObservation` | Feature-of-interest and temporal range in; SWE-encoded hourly time series out | None (public feed) |
| postcodes.io | External API | `GET /postcodes/{postcode}`, `GET /outcodes/{outcode}`, `GET /places?q=` | Postcode, outcode or place name in; coordinates out | None |

> Stations are sourced from `/measurements` rather than `/monitoringStations` on purpose. The
> two collections share no identifiers (`MY1` against `UKA00315`) and only `/measurements`
> carries the feature-of-interest identifiers the SOS series lookup needs.

## 6. Consumed By (Inbound Dependencies)

No AQIE service consumes this one. It is a standalone demonstration reached directly in a browser.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** none. No database, cache, queue or build step.
- **Key entities:** a *station* (name, `localSiteID`, coordinates as `[latitude, longitude]`,
  per-pollutant feature-of-interest identifiers) and a *series* of `{ time, value }` points per
  pollutant. Pollutants whose feature of interest is the `missingFOI` sentinel are skipped
  because no series can be fetched for them.
- **Retention / refresh:** nothing is retained. The station list and the hourly series are
  fetched live on every request. Freshness of the station list depends on the ingest schedules
  in `aqie-back-end`; on a cold back-end start `/measurements` is empty until its first
  pollutants run completes.
- **Aggregation:** 24-hour and 7-day windows are served at hourly resolution; month and year
  windows are aggregated to daily means on the Europe/London calendar, because an hourly year
  is roughly 8,760 points per pollutant.

## 8. Configuration

Variable names only — values are set as CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `AQIE_BACK_END_URL` | Base URL for `aqie-back-end`; also used to work out which host must bypass the egress proxy |
| `SOS_URL` | Base URL and fixed query prefix for the DEFRA SOS `GetObservation` feed |
| `CDP_HTTPS_PROXY`, `CDP_HTTP_PROXY`, `HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY` | CDP egress proxy selection and bypass list |
| `PORT`, `NODE_ENV` | HTTP listener and runtime mode |
| `PASSWORD`, `PASSWORD_KEYS` | GOV.UK Prototype Kit basic authentication, required on CDP |
| `USE_HTTPS` | Disabled in the production image because CDP terminates TLS at the nginx layer |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`.
  Development runs `npm run dev`, production runs `npm start`.
- **Egress:** Node's global `fetch` ignores the standard proxy variables, so the service sets an
  `undici` proxy dispatcher explicitly at start-up and excludes `localhost`,
  `.cdp-int.defra.cloud` and the back-end host from it.
- **Access control:** Prototype Kit basic authentication is on by default in CDP environments.
- **Environments:** `dev` (prototype environments only).
- **Pipelines:**
  - `.github/workflows/publish.yml` — build and publish on push to `main`

## 10. Observability

- **Logging:** default GOV.UK Prototype Kit / Express console logging, with upstream failure
  causes unwrapped and logged explicitly. No structured logging or log shipping.
- **Tracing:** none.
- **Metrics:** none. The landing page performs a connectivity probe against the configured
  upstreams and reports the result in the page, but this is not wired to platform monitoring.
- **Accessibility:** the spike reports zero axe-core WCAG 2.2 A/AA violations across all pages,
  verified with keyboard-only navigation, contrast checks and JavaScript disabled. Charts use
  colour, line style and a legend together rather than colour alone.

## 11. Open Questions

- [ ] The spike recommends moving the hourly-series fetch and SWE decode into `aqie-back-end`
      as `GET /measurements/history`. Confirm whether that work is planned, and whether it would
      be served live or from stored history.
- [ ] Confirm whether the SOS feed is an acceptable production dependency, given it is hit live
      with no caching or retry here and can return `504`s.
- [ ] Confirm whether postcodes.io is acceptable for location search in this journey, or whether
      it should use the OS Names integration that `aqie-front-end` already has.
- [ ] Confirm whether this demo should be archived once the feasibility decision is taken.
