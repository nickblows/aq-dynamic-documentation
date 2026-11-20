# aqie-dataselector-frontend

> The public "Get air pollution data" journey. Lets citizens, researchers and local authority
> officers select historic UK air quality measurements — by monitoring station (with a
> recent-readings summary for each station) or by building a custom dataset — and download
> them as files or have a download link emailed to them.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-dataselector-frontend`](https://github.com/DEFRA/aqie-dataselector-frontend) |
| Service domain | `Citizen` |
| Service type | `Auxilary Frontend` |
| Lifecycle stage | `Production` (live public service; every page carries a GOV.UK Beta phase banner) |
| Primary language | JavaScript |
| Runtime | Node.js `>=26` (ES modules, Babel-compiled to `.server`) |
| Default branch | `main` |
| Created (UTC) | `2025-02-14` |
| Last main commit (UTC) | `2026-11-19T08:45:23Z` |
| Last analysed commit | `41776ca8` |
| Last analysed (UTC) | `2026-11-19T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Runs two parallel selection journeys over historic air quality data:
  1. **By monitoring station** — search a place, disambiguate it, pick a nearby station,
     read that station's pollutant summary, then download its measurements for a chosen
     pollutant, frequency and year. The station page has a tab for each reporting year
     since 2018, plus **Last 7 days** and **Last 24 hours** tabs and, when its feature flag
     is on, a **Daily Air Quality Index (DAQI)** tab.
  2. **Custom dataset** — pick pollutants (individually, or as a "core" or "compliance"
     group), pick a data source network, pick locations (countries, local authorities,
     zones or agglomerations), pick a time period (last 7 days, year to date, one year, or
     a range of up to five years), see a live count of matching stations, then request the
     extract.
- Resolves free-text place names and finds nearby monitoring stations by calling
  `aqie-location-backend` and `aqie-monitoringstation-backend`. Also looks up a single
  station by coordinates, for deep links from the map.
- Fetches the selectable pollutant master list, the available data sources per pollutant,
  and the zone and agglomeration lists from `aqie-historicaldata-backend`.
- Fetches each station's last 24 hours, last 7 days and DAQI figures from `aqie-back-end`
  (`GET /monitoringStationHistory`) and formats them for display.
- Shows a live count of matching monitoring stations as the citizen narrows a custom dataset.
- Creates asynchronous extract jobs in `aqie-historicaldata-backend`. In the enhanced
  journey the citizen's browser starts the job, polls its status and follows the resulting
  download URL; the no-JavaScript journey waits on the server instead (Section 4).
- Offers an email alternative for multi-year requests, and as a fallback when a download
  takes longer than three minutes: the citizen submits an email address, and the emailed
  link later exchanges a job reference for a pre-signed download URL.
- Fetches the UK LAQM local authority list from the LAQM Portal to populate the
  local-authority picker, with a long in-process cache and graceful degradation.
- Hands over to and from the interactive map in `aqie-maps-frontend`: accepts a station
  deep link, shows a "Search on a map" link on the hub page and a "View map of nearby
  monitoring stations" form on station pages (both behind a feature flag), and returns the
  citizen to the map from a station they opened from it.
- Provides a complete **no-JavaScript fallback journey** alongside the enhanced one.
- Serves the supporting static pages — about, privacy, accessibility, cookies — and a
  consent-gated Google Tag Manager integration.

**Does not:**

- Hold or generate the measurement data. Every extract is produced by
  `aqie-historicaldata-backend`; this service only orchestrates the selection and the wait.
- Calculate air quality figures. DAQI indices, averages, data capture and exceedances are
  calculated by `aqie-back-end` and `aqie-historicaldata-backend`; this service only
  formats them. It does not serve forecasts, current-conditions pages or the alert
  subscription journey — those belong to `aqie-front-end` over `aqie-back-end`,
  `aqie-alert-back-end-service` and `aqie-notify-service`.
- Plot stations on an interactive map — that is `aqie-maps-frontend`. This service only
  links to it and accepts links from it.
- Send the notification emails itself. It posts the citizen's request to
  `aqie-historicaldata-backend`, which owns delivery (through `aqie-notify-service`). It
  does not call `aqie-notify-service` or `aqie-alert-back-end-service`, which serve the air
  quality *alert subscription* journey, not data download.
- Hold the Ordnance Survey API key. Place-name lookup goes through `aqie-location-backend`,
  which owns that credential.
- Accept file uploads from citizens. The journey is read-only and unauthenticated (see the
  `cdp-uploader` finding in Section 5).

## 3. Architecture

**Pattern:** Hapi server-side rendered GOV.UK Frontend service using Nunjucks, with per-step
state kept in a `@hapi/yar` session (Redis in production, memory locally). Each journey
step is a folder under `src/server/` containing `index.js` (route plugin), `controller.js`
(handler) and one or more `.njk` templates, registered centrally in `src/server/router.js`.
Client-side enhancement is bundled by Webpack from `src/client/`.

| Component | Path | Responsibility |
|---|---|---|
| Router | `src/server/router.js` | Registers 30 route plugins, the health check and the static asset routes |
| Server assembly | `src/server/index.js` | Registers logging, tracing, secure context, graceful shutdown, session, `@hapi/scooter`, the Content Security Policy plugin, `@hapi/crumb`, Nunjucks and the router |
| Shared API client | `src/server/common/helpers/api-client.js` | `postJson` and `getJson` helpers, used by place search and station lookups; `@hapi/wreck` with an `x-api-key` on localhost, `axios` everywhere else. Most other controllers still carry their own copy of that branch |
| Proxy-aware fetch | `src/server/common/helpers/proxy.js`, `catch-proxy-fetch-error.js` | `undici` fetch through the CDP egress proxy when configured, pinned to HTTP/1.1; used for the LAQM Portal call only; returns `[status, body]` |
| Station helpers | `src/server/common/helpers/station-helpers.js` | Builds hourly-data and exceedence requests; fetches a station by coordinates and a station's recent history; formats station coordinates as a Google Maps link |
| History summaries | `src/server/common/helpers/daqi-summary.js`, `last-7-days-summary.js`, `history-summary-shared.js` | Map the `aqie-back-end` history response onto the DAQI, Last 24 hours and Last 7 days table rows. Only display rounding happens here |
| Map links | `src/server/common/helpers/map-url.js` | Builds links to `aqie-maps-frontend`, gated by a feature flag and a URL setting |
| Content Security Policy | `src/server/common/helpers/content-security-policy.js`, `src/server/common/constants/csp-directives.js` | Nonce-based policy through `blankie` |
| Custom dataset modules | `src/server/customdataset/` | `selection-helpers.js` (parse selections), `datasource-category.js` (near real-time versus other data; zone and last-7-days rules), `station-count-workflow.js` and `station-count.js` (live station counts) |
| Network helpers | `src/server/common/helpers/network-helpers.js` | Resolves AURN and non-AURN network identifiers and station counts for extract requests |
| Content packs | `src/server/data/en/` | Page copy separated from controllers, including the DAQI, Last 24 hours and Last 7 days wording |
| Session cache | `src/server/common/helpers/session-cache/`, `redis-client.js` | `@hapi/yar` over `catbox-redis` / `ioredis`; `catbox-memory` locally |
| Config | `src/config/config.js` | `convict` schema, about 60 environment-bound settings; the service throws at start-up if `SESSION_COOKIE_PASSWORD` is missing |
| Client bundle | `src/client/javascripts/` | Accessible autocomplete, cookie banner, GTM loader |

**Environment-split endpoint configuration.** Nearly every upstream call has *two* config
entries: a deployed URL (for example `pollutantMasterApiUrl`) and a localhost development
URL pointing at `ephemeral-protected.api.dev.cdp-int.defra.cloud` (for example
`pollutantMasterDevUrl`). `config.get('isDevelopment')` selects between them, and the dev
branch adds an `x-api-key` from `OS_NAMES_DEV_API_KEYS`. This doubles the configuration
surface and is the main source of confusion when reading the code — the deployed path is
always the non-`Dev` key. Deployed URLs are built from the `ENVIRONMENT` variable, which is
read straight from the process environment rather than through the config schema.

### Feature flags

All three are off by default and are read once at start-up, so a change needs a restart.

| Variable | Effect when `true` |
|---|---|
| `VIEW_DAQI_TAB_ENABLED` | Shows the Daily Air Quality Index tab on station pages, makes it the default tab, and registers `GET /stationdetails/daqi`. While off, `GET /rendertable/daqi` returns 404 and the year tabs are the default |
| `VIEW_GRAPH_SUMMARY_ENABLED` | Shows the "View graph and pollutant summary" button (JavaScript users only) and registers `GET /stationdetails/graph-summary`, which is currently a placeholder page |
| `SEARCH_ON_MAP_ENABLED` | Shows the "Search on a map" link on the hub page and the "View map of nearby monitoring stations" form on station pages. Also needs the maps URL (`MAPS_FRONT_END_URL`, which defaults to the `aqie-maps-frontend` host for the CDP environment); with neither set the links stay hidden. The Back link to the map from a station opened from the map is not gated by the flag |

### Security controls

- **Content Security Policy** through `blankie` with a generated nonce for inline scripts
  (it replaced a fixed header in September 2026). Scripts are allowed from this service,
  Google Tag Manager and Analytics, `code.jquery.com` and one hash for the GOV.UK template
  script. Styles allow inline. Frames are limited to Google Tag Manager, `frame-ancestors`
  to this service, and form targets to this service plus the maps origin.
- **Other headers:** HSTS for one year including subdomains, no-sniff, frame and XSS
  protection, `Referrer-Policy: strict-origin-when-cross-origin`, and a
  `Cache-Control: no-store` header on every non-error response.
- **CSRF:** `@hapi/crumb` is registered but only `POST /cookies` is validated (Section 11).
- **Session cookie:** encrypted and signed with `SESSION_COOKIE_PASSWORD`, which has no
  default; secure flag on in production; four-hour lifetime.
- **Direct-access guard:** several pages (station details and its no-JS version, location
  choice, the custom dataset builder, email request, and the two "change" pages) return
  "page not found" unless the Referer header contains this host. It is a navigation
  convenience, not an access control. A deep link from the map passes it once through a
  one-time session flag.
- **Input handling:** place search text is limited to letters, digits, spaces and a few
  punctuation marks; `POST /station-summary` is checked by a Joi schema (latitude and
  longitude ranges, name length); the cookie form's return URL must be a path on this site.

### Progressive enhancement and the no-JavaScript journey

This is a deliberate design decision, not an accident of history. The enhanced journey uses
client-side autocomplete, in-page pollutant and location pickers, in-place tab loading on the
station page, and background polling of extract job status. Every one of those steps has a
server-rendered equivalent:

| Enhanced step | No-JS equivalent |
|---|---|
| In-page pollutant picker | `GET`/`POST /airpollutant/nojs` |
| In-page location picker (countries, local authorities, zones, agglomerations) | `GET`/`POST /location-aurn/nojs` (template `index_nojs.njk`) |
| Custom dataset form submit | `GET`/`POST /download_dataselectornojs` |
| Station detail and year switching | `POST /stationDetailsNojs`, `GET /stationDetailsNojs/{id}`, `GET /stationDetailsNojs/year/{year}` |
| Station tabs loaded in place by `GET /rendertable/{tab}` | Full pages: `GET /stationdetails/year/{year}`, `/stationdetails/last-24-hours`, `/stationdetails/last-7-days` and `/stationdetails/daqi` |
| Station file download | `GET /stationdetails/download/{pollutant}/{frequency}` |
| Per-pollutant download | `GET /downloaddatanojs/{poll}/{freq}` |
| Extract job creation and waiting (browser polls) | `GET /download_aurn_nojs/{year}`, `GET /download_aurn_nojs/{year}/{dataSource}` (the server waits for the job to finish) |

The graph summary button is for JavaScript users only. The custom dataset page sets its form
`action` to the `nojs` endpoint and swaps the picker links to the `nojs` routes, so the page
works with scripting disabled and the client script upgrades it in place when available. A
`<noscript>` block confirms the fallback behaviour to the citizen. The practical consequence
is that **a change to any selection step must be made twice** — once in the enhanced
controller and once in its `nojs` counterpart.

## 4. API Surface

75 application routes are registered when both route-level feature flags are on (73 by
default), plus three static asset routes. They are grouped below by journey step rather than
listed individually. All are user-facing HTML unless noted.

### Entry and hub

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Service start page |
| `GET` | `/hubpage` | Chooses between the station journey and the custom dataset journey; also offers "Search on a map" when `SEARCH_ON_MAP_ENABLED` is on |
| `GET` | `/health` | Liveness probe (JSON) |

### Journey A — by monitoring station

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/search-location` | Enter a place name or postcode |
| `GET` | `/search-location/searchagain` | Re-enter the search |
| `GET`, `POST` | `/multiplelocations` | Disambiguate between matching places; also renders the "no location" and "no station" outcomes |
| `GET` | `/monitoring-station` | Nearby stations with the pollutants each measures |
| `GET`, `POST` | `/location` and `GET /location/{id}` | Select a specific location/station identifier |
| `POST` | `/station-summary` | Deep link from `aqie-maps-frontend`. Takes `lat`, `lng` and `name`, validates them, looks the station up, seeds the session and redirects to `/stationdetails`; an invalid or unmatched request shows "page not found" |
| `GET`, `POST` | `/stationdetails` | Station page; opens on the DAQI tab when `VIEW_DAQI_TAB_ENABLED` is on, otherwise on the current year |
| `GET` | `/stationdetails/year/{year}` | Year tab (exceedence table for that year) |
| `GET` | `/stationdetails/last-24-hours` | Last 24 hours tab, as a full page (linkable; the no-JS route to the tab) |
| `GET` | `/stationdetails/last-7-days` | Last 7 days tab, as a full page |
| `GET` | `/stationdetails/daqi` | DAQI tab (registered only when `VIEW_DAQI_TAB_ENABLED` is on) |
| `GET` | `/stationdetails/graph-summary` | "View graph and pollutant summary" page; a placeholder (registered only when `VIEW_GRAPH_SUMMARY_ENABLED` is on) |
| `GET` | `/year` | Year selection for station pollution detail |
| `GET` | `/rendertable/{year}` | Tab content loaded in place: the exceedence table for a year, or the `daqi`, `last-24-hours` or `last-7-days` fragment |
| `GET` | `/downloaddata/{poll}/{freq}` | Download a station series by pollutant and frequency; returns the download URL as text |
| `GET` | `/stationdetails/download/{download}/{pollutant}/{frequency}` | Station file download |
| `POST` | `/stationDetailsNojs` | No-JS station detail |
| `GET` | `/stationDetailsNojs/{id}`, `/stationDetailsNojs/year/{year}` | No-JS station detail and year switch |
| `GET` | `/stationdetails/download/{pollutant}/{frequency}` | No-JS station file download |
| `GET` | `/downloaddatanojs/{poll}/{freq}` | No-JS series download |

### Journey B — custom dataset

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/customdataset` | The dataset builder; shows current selections and a live station count |
| `GET` | `/customdataset/{pollutants}` | Builder pre-seeded with pollutants |
| `GET` | `/customdataset/year/{year}` | Builder with a year applied |
| `POST` | `/customdataset/location` | Apply a location selection to the builder |
| `GET` | `/customdataset/clear` | Reset the builder |
| `GET` | `/stationcount_ukeap` | Returns the non-AURN station count held in the session (JSON). No page in this service calls it |

### Pollutant selection

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/airpollutant` | Pollutant picker: specific pollutants, or a "core" or "compliance" group |
| `POST` | `/addpollutants` | Apply pollutant selection |
| `GET`, `POST` | `/airpollutant/nojs` | No-JS pollutant picker |

### Data source selection

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/datasource` | Choose the monitoring network / data source |

### Location selection (custom dataset)

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/location-aurn` | Choose countries, local authorities, zones or agglomerations. Zones and agglomerations only offer AURN data |
| `GET`, `POST` | `/location-aurn/change` | Change an existing location selection |
| `GET`, `POST` | `/location-aurn/nojs` | No-JS location picker |

### Time period selection

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/year-aurn` | Choose the last 7 days, year to date, one year (1973 onwards) or a range of up to five years |
| `GET`, `POST` | `/year-aurn/change` | Change an existing time period |

### Download and extract jobs

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/download_dataselector` | Confirm and submit the extract request; lists the networks and station counts with a download button per network and year |
| `GET`, `POST` | `/download_dataselectornojs` | No-JS equivalent |
| `GET` | `/download_aurn/{year}`, `/download_aurn/{year}/{dataSource}` | Create the extract job and return its job reference as JSON (the enhanced journey) |
| `GET` | `/download_aurn_nojs/{year}`, `/download_aurn_nojs/{year}/{dataSource}` | Create the job, wait on the server until it completes, and render the result page |
| `GET` | `/download_aurn/status/{jobID}`, `/download_aurn_status/{jobID}` | One status check for a job, returned as JSON |

### Email download request

| Method | Path | Purpose |
|---|---|---|
| `GET`, `POST` | `/emailrequest` | Submit an email address for a multi-year or slow extract |
| `GET`, `POST` | `/emailrequest/{dataSource}` | Data-source-specific variant |
| `GET`, `POST` | `/emailrequest/confirm` | Confirmation step |
| `GET` | `/download_emailreq/{id}/{timestamp}` | The target of the emailed link: exchanges the job reference for a pre-signed download URL and starts the download; links older than 48 hours show an expiry page |

### Static and support pages

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/about`, `/privacy`, `/accessibility` | Static content |
| `GET`, `POST` | `/cookies` | Cookie preferences; the only POST route with CSRF validation applied |
| `GET` | `/problem-with-service` | Error page |
| `GET` | `/assets/{param*}`, `/public/{param*}`, `/favicon.ico` | Static assets (MoJ Frontend assets, Webpack bundle) |
| `GET` | `/some-path` | Legacy route in `year_pollutiondetails` that redirects to `/invalid-path`, which does not exist — see Section 11 |

### Extract job lifecycle

**Enhanced journey (JavaScript).** For a single year, the citizen's browser calls
`GET /download_aurn/{year}/{dataSource}`. The server posts the selection criteria to
`POST /AtomDataSelection` and returns the job reference as JSON straight away. The browser
then calls `GET /download_aurn_status/{jobID}` every two seconds; each call makes one
`POST /AtomDataSelectionJobStatus` request and returns the status. When the status is
`Completed`, the browser goes to the `resultUrl` (a pre-signed download URL). After three
minutes without completion the browser gives up and sends the citizen to `/emailrequest`.
If the first call fails, it falls back to the no-JavaScript route.

**No-JavaScript journey.** `GET /download_aurn_nojs/{year}[/{dataSource}]` creates the job
in the same way, then **waits on the server**: it checks the job status once a second
**until the status is `Completed`**, then renders the result page with the download link.
There is no attempt limit and no timeout, and a `Failed` status is not treated as an end, so
a job that never completes holds the request open. Failures to start or check the job
redirect to `/problem-with-service`.

**Station downloads.** `GET /downloaddata/{poll}/{freq}` posts to
`POST /AtomHistoryHourlydata` and returns the download URL as text for the browser to follow.
There is no job and no polling.

**Email path.** `POST /emailrequest/confirm` validates the address, then posts the selection
and address to `POST /AtomEmailJobDataSelection`; the backend answers `Success` and sends the
email later. When the citizen follows the emailed link, `/download_emailreq/{id}/{timestamp}`
rejects a timestamp more than 48 hours old, posts the job reference to
`POST /AtomDataSelectionPresignedUrlMail` (the response may be a bare URL or an object
carrying `resultUrl`), makes a server-side check that the returned URL responds, and then
shows a "Your file is downloading" page that sends the browser to the URL after one second
(a meta refresh without JavaScript). The 48-hour rule uses the timestamp in the link, which
is not signed.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-historicaldata-backend` | AQIE service | `GET /AtomDataSelectionPollutantMaster` | Master list of selectable pollutants | CDP internal network |
| `aqie-historicaldata-backend` | AQIE service | `POST /AtomDataSelectionPollutantDataSource` | Selected pollutant in; data source categories and networks out | CDP internal network |
| `aqie-historicaldata-backend` | AQIE service | `GET /AtomDataSelectionRegionMaster` | Zone (region) list for the location picker | CDP internal network |
| `aqie-historicaldata-backend` | AQIE service | `GET /AtomDataSelectionAgglomerationMaster` | Agglomeration list for the location picker | CDP internal network |
| `aqie-historicaldata-backend` | AQIE service | `POST /AtomDataSelection` | Selection criteria in; extract job reference out. Also used, with count parameters, for the live station count | CDP internal network |
| `aqie-historicaldata-backend` | AQIE service | `POST /AtomDataSelectionJobStatus` | Job reference in; status and `resultUrl` out | CDP internal network |
| `aqie-historicaldata-backend` | AQIE service | `POST /AtomEmailJobDataSelection` | Selection criteria and email address in; the text `Success` out. The backend sends the email later | CDP internal network |
| `aqie-historicaldata-backend` | AQIE service | `POST /AtomDataSelectionPresignedUrlMail` | Job reference from the emailed link in; pre-signed download URL out | CDP internal network |
| `aqie-historicaldata-backend` | AQIE service | `POST /AtomHistoryHourlydata` | Station, pollutant, year and frequency in; download URL for the series out | CDP internal network |
| `aqie-historicaldata-backend` | AQIE service | `POST /AtomHistoryexceedence` | Station and year in; exceedence table out | CDP internal network |
| `aqie-location-backend` | AQIE service | `POST /osnameplaces` | `{ userLocation }` in; OS Names matches out. A 4xx reply is treated as "no match" | CDP internal network |
| `aqie-monitoringstation-backend` | AQIE service | `POST /monitoringstation` | `{ userLocation, usermiles }` in; nearby stations with pollutants out | CDP internal network |
| `aqie-monitoringstation-backend` | AQIE service | `GET /monitoringstation/by-location` | `lat`, `lng` and `name` query parameters in; one matching station out (404 when none). Used for deep links from the map | CDP internal network |
| `aqie-back-end` | AQIE service | `GET /monitoringStationHistory` | `siteId` (Ricardo AURN form) and `period` (`24h` or `7d`) in; hourly readings and summary figures out. Feeds the DAQI, Last 24 hours and Last 7 days tabs | CDP internal network |
| **LAQM Portal** | **External API** | **`GET https://www.laqmportal.co.uk/xapi/getLocalAuthorities/json`** | **UK local authority list for the location picker. 2.5-second timeout; 12-hour in-process cache with stale fallback** | **`X-API-Key` and `X-API-PartnerId` headers from `LAQMAPIKEY` and `LAQMAPIPARTNERID`** |
| AWS S3 | Datastore (pre-signed URL) | `GET` of a pre-signed URL | Server-side check, on the emailed-link route, that the URL responds (aborted after the first bytes). The citizen's browser then follows such URLs to download extracts | Pre-signed URL |
| `aqie-maps-frontend` | AQIE service (browser link) | `GET {MAPS_FRONT_END_URL}/map` link; `POST {MAPS_FRONT_END_URL}/map/view` form | Hub page link and a station page form that posts `lat`, `lng` and the station id from the citizen's browser so the map centres on the station. Behind `SEARCH_ON_MAP_ENABLED`; the Back link to the map is not | None |
| Google Tag Manager | External (browser) | `gtm.js` / `ns.html` container load | Analytics, loaded only after the citizen accepts analytics cookies | Container IDs from `GOOGLE_TAG_MANAGER_KEYS` |
| jQuery CDN | External (browser) | `https://code.jquery.com/jquery-3.6.0.min.js` | Script for the MoJ Frontend components; no AQIE data sent | None; the script tag has an integrity hash |
| Qualtrics | External (browser link) | Feedback survey link in the beta banner | No service data | None |
| Google Maps | External (browser link) | `https://www.google.co.uk/maps?q=<lat>,<lon>` link on the station page | Station coordinates in the link | None |
| Redis | Datastore | `catbox-redis` / `ioredis` | Journey session state; used when `SESSION_CACHE_ENGINE` is `redis`, which is the production default | `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_TLS` |

The server-to-server rows, the maps link, the S3 check and the browser-side rows are edges in
`integration-catalog.yaml` (ids beginning `dataselector-frontend__`; the inbound map link is
`maps-frontend__dataselector-frontend`). The Google Maps link is a plain outbound link and is
not catalogued.

### Verified NOT integrations

- **`cdp-uploader` — re-checked at `41776ca8`: still not an integration.** The configuration
  keys that suggested it (`CDP_UPLOADER_URL` and `AWS_S3_BUCKET_NAME`, with `BACKEND_API_URL`,
  `ANALYSIS_TYPE_MAPPING` and `AQIE_PASSWORD`) were never read by any code and were deleted
  from `src/config/config.js` on 19 October 2026. The matching unused packages
  (`@langchain/*`, `pdf2json`, `xlsx` and `@aws-sdk/*`), all artefacts of the
  document-analysis proof of concept, are gone from `package.json` (5 and 29 October). There
  is no upload route, no multipart handler and no file input in any template. The only
  remnants are stale ignore patterns for `src/server/cdp-uploader/` and
  `src/server/utils/xlsxParser.js` in `jest.config.js` and `sonar-project.properties`. The
  catalogue records this as a refuted edge.
- **AWS S3 direct access.** The AWS SDK packages are gone. The service has no S3 client and
  no IAM access; it only handles pre-signed HTTPS URLs supplied by
  `aqie-historicaldata-backend` (the server-side check above, and browser downloads).
- **`aiqe-dataservice-backend`.** Two config entries once defaulted to
  `aiqe-dataservice-backend` (note the transposed letters), which belonged to an archived
  service. Neither was read by any code and both were deleted on 19 October 2026. Do not
  confuse this with the real `aqie-back-end` history call above.

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| Public internet (citizens) | All HTML routes above | Selection criteria in; measurement extracts and download links out |
| `aqie-maps-frontend` (through the citizen's browser) | `POST /station-summary` | Station `lat`, `lng` and `name` in; redirect to the station page out |
| Citizens' email clients | `GET /download_emailreq/{id}/{timestamp}` | The link in the email sent for a requested extract. `aqie-historicaldata-backend` builds it (the configured base address plus the job id and the job's creation time in milliseconds) and sends it through `aqie-notify-service` (Section 11) |
| `aqie-dataselector-perf-frontend` (archived) | Public journey routes | Historic load testing. Not re-verified this cycle |

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** none of its own. Redis holds the journey session (`@hapi/yar` over
  `catbox-redis`) when `SESSION_CACHE_ENGINE` is `redis`, which is the default when
  `NODE_ENV=production`. Otherwise (locally and in tests) the session is held in memory. The
  old `REDIS_ENABLED` switch no longer exists.
- **Session state held across the journey:** the raw and normalised search query, the
  selected place and the monitoring station results (including the station being viewed),
  selected pollutants (specific or group), selected data source, location type with the
  selected countries, local authorities (and their LAQM identifiers), zones or
  agglomerations (and their identifiers), the selected time period, live station counts,
  extract job references and download URLs, and validation error summaries. A deep link
  from the map sets a station, a one-time "trusted" flag and the station to return to. The
  citizen's email address is stored when the email form is submitted and is **not cleared**
  afterwards: it stays in the session until the session expires.
- **In-process cache:** the LAQM local authority list is cached in module scope for 12
  hours. On upstream timeout, non-200 response or unexpected payload shape the controller
  falls back to the stale cached value, and if there is none it returns an empty list
  flagged `unavailable` so the page can degrade rather than fail. Because the cache is
  per-process, each ECS task warms it independently. The pollutant, data source, zone and
  agglomeration lists are fetched on request and not cached in process. Network names and
  descriptions come from a local content pack that enriches the data source response.
- **Retention:** session cache TTL and cookie TTL both default to four hours. Static asset
  caching is configured for one week (`STATIC_CACHE_TIMEOUT`); the `onPreResponse` extension
  also sets `Cache-Control: no-store` on every non-error response, and which header the
  static assets finally carry has not been verified. No measurement data is persisted by
  this service.

## 8. Configuration

Variable names only — values are never recorded here. About 60 settings are bound to
environment variables.

| Variable | Purpose |
|---|---|
| `PORT`, `NODE_ENV`, `ENVIRONMENT`, `SERVICE_VERSION` | Runtime identity; `ENVIRONMENT` is read straight from the process environment and interpolated into every default upstream URL |
| `ASSET_PATH`, `STATIC_CACHE_TIMEOUT` | Static asset serving |
| `POLLUTANT_MASTER_API_URL`, `DATASOURCE_API_URL`, `REGION_MASTER_API_URL`, `AGGLOMERATION_MASTER_API_URL`, `STATION_COUNT_API_URL`, `Download_aurn_URL`, `Polling_URL`, `Email_URL`, `DOWNLOAD_EMAIL_URL`, `Download_URL`, `Table_URL` | `aqie-historicaldata-backend` endpoints (deployed) |
| `Osname api url`, `OS_NAMES_API_URL_1` | `aqie-location-backend` and `aqie-monitoringstation-backend` endpoints (deployed). The monitoring station URL is also the base for the by-location lookup |
| `MONITORING_STATION_HISTORY_URL` | `aqie-back-end` station history endpoint (deployed) |
| `POLLUTANT_MASTER_DEV_URL`, `DATASOURCE_DEV_URL`, `REGION_MASTER_DEV_URL`, `AGGLOMERATION_MASTER_DEV_URL`, `STATION_COUNT_DEV_URL`, `DOWNLOAD_AURN_DEV_URL`, `POLLING_DEV_URL`, `EMAIL_DEV_URL`, `DOWNLOAD_EMAIL_DEV_URL`, `DOWNLOAD_DEV_URL`, `TABLE_DEV_URL`, `OS_LOCATION_DEV_URL`, `OS_MONITORING_STATION_DEV_URL`, `MONITORING_STATION_HISTORY_DEV_URL` | Localhost-only equivalents of the above |
| `OS_NAMES_DEV_API_KEYS` | Single `x-api-key` used for all localhost dev endpoints |
| `LAQMAPIKEY`, `LAQMAPIPARTNERID` | LAQM Portal credentials. Both default to their own variable names when unset (Section 11) |
| `GOOGLE_TAG_MANAGER_KEYS` | Comma-separated GTM container IDs; a default container ID is committed (not a secret) |
| `VIEW_DAQI_TAB_ENABLED`, `VIEW_GRAPH_SUMMARY_ENABLED`, `SEARCH_ON_MAP_ENABLED` | Feature flags, all off by default (Section 3) |
| `MAPS_FRONT_END_URL` | `aqie-maps-frontend` base URL for map links; defaults to the CDP-environment host when `ENVIRONMENT` is set, and the links stay hidden when neither is set |
| `REDIS_HOST`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_KEY_PREFIX`, `REDIS_TLS`, `USE_SINGLE_INSTANCE_CACHE` | Session cache backend |
| `SESSION_CACHE_ENGINE`, `SESSION_CACHE_NAME`, `SESSION_CACHE_TTL` | Catbox cache selection and lifetime |
| `SESSION_COOKIE_PASSWORD`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_TTL` | Cookie signing and lifetime. `SESSION_COOKIE_PASSWORD` is mandatory: no default, and the service refuses to start without it |
| `CDP_HTTP_PROXY`, `CDP_HTTPS_PROXY` | CDP egress proxy (used for the LAQM Portal call) |
| `ENABLE_SECURE_CONTEXT` | TLS trust store |
| `TRACING_HEADER` | Trace header name |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |

No longer in the config schema (no code ever read them): `AQIE_PASSWORD`, `BACKEND_API_URL`,
`ANALYSIS_TYPE_MAPPING`, `CDP_UPLOADER_URL`, `AWS_S3_BUCKET_NAME`, `COOKIE_PASSWORD`,
`REDIS_ENABLED` and `ENABLE_METRICS`. They can be dropped from environment configuration.

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` (parent version
  `latest-26`) through a `development` stage to `defradigital/node`; entrypoint `node .`,
  exposing `PORT` (3000 in the image; the config default is 3001 when `PORT` is unset).
- **Build:** Webpack bundles the client assets, Babel compiles `src/` to `.server/`.
- **Environments:** CDP `dev`, `test`, `perf-test`, `prod`.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — a Dependency Review job (fails on critical
    findings) and a validator job (format check, lint, Jest, Docker image build, SonarCloud
    scan) on pull requests to `main`
  - `.github/workflows/build.yml` — SonarQube scan on push to `main` and on pull requests
  - `.github/workflows/publish.yml` — CDP build and publish on push to `main`, then tests
    and a SonarCloud scan
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish
- **Local development:** `compose.yml` runs the app on port 3010 with Redis, plus LocalStack
  and MongoDB containers left over from the CDP template (this service uses neither), on
  offset ports so it can run beside the other AQIE services. The station tabs need
  `aqie-monitoringstation-backend` and `aqie-back-end` running locally.
- **Testing:** `jest` with `jest-environment-jsdom`, `jest-fetch-mock` and `cheerio`.
  Note this repository still uses Jest while `aqie-prtr-backend` and `aqie-prtr-frontend`
  have moved to Vitest.

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, `@elastic/ecs-pino-format` in production, with
  `req.headers.authorization`, `req.headers.cookie` and `res.headers` redacted in
  production only. The LAQM fetch logs status, duration and the underlying failure cause;
  the other upstream calls log only an error message.
- **Tracing:** `@defra/hapi-tracing` using `TRACING_HEADER` (`x-cdp-request-id`).
- **Metrics:** none emitted. `aws-embedded-metrics` is declared in `package.json` but never
  imported, and the `ENABLE_METRICS` flag was removed.
- **Shutdown:** `hapi-pulse` with a ten-second timeout.
- **Error handling:** an `onPreResponse` extension plus a `catchAll` handler render the
  GOV.UK error pages; upstream failures are logged and surfaced as
  `/problem-with-service`.
- **Analytics:** Google Tag Manager is injected only after the citizen accepts analytics
  cookies, including the `<noscript>` iframe variant. When consent is withdrawn the server
  expires the Google cookies on the next response, which also covers users without
  JavaScript.

## 11. Open Questions

- [ ] **CSRF protection.** `@hapi/crumb` is registered, but its `skip` function returns true
      for every `POST` whose path is not `/cookies`. In effect, token validation is applied
      to the cookie preferences form only and to no other form in the journey. The skip also
      covers the cross-origin `POST /station-summary` from `aqie-maps-frontend`, which needs
      to be exempt. Confirm whether the blanket exemption is intentional and, if not, narrow
      the skip predicate to `/station-summary` and add the token to the other forms.
- [ ] **The no-JavaScript job wait has no bound.** `GET /download_aurn_nojs/...` (and the
      fallback from the enhanced journey) checks the extract job every second until its
      status is `Completed`, with no maximum attempts and no timeout, and a `Failed` status
      is not treated as an end (`src/server/download_aurn/controller.js`). The enhanced
      journey is bounded: the browser stops after three minutes. Confirm the intended
      behaviour for a stuck or failed job on the no-JavaScript route.
- [ ] **Feature flags per environment.** Are `VIEW_DAQI_TAB_ENABLED`,
      `VIEW_GRAPH_SUMMARY_ENABLED` and `SEARCH_ON_MAP_ENABLED` set in `test`, `perf-test` and
      `prod`? All default to off and the repository cannot say, so what a citizen sees (year
      tabs only, or DAQI first) depends on environment configuration. What is the intended
      end state of the graph summary page, which is currently a placeholder?
- [ ] **Emailed link and its expiry.** (catalogue `oq-034`) `aqie-historicaldata-backend`
      builds the link `/download_emailreq/{id}/{timestamp}` (the configured base address plus
      the job id and the job's creation time in milliseconds) and sends it through
      `aqie-notify-service`. The 48-hour rule shown to citizens is enforced only in this
      service, by checking that timestamp, which is not signed, and
      `aqie-historicaldata-backend` issues a fresh pre-signed URL (seven-day expiry) for any
      known job reference. Confirm which period is the policy and where expiry is meant to be
      enforced.
- [ ] **Rate limiting and abuse.** Is any rate limiting or bot protection applied (by the
      platform or the backend) to `POST /emailrequest/confirm`, which makes the backend send
      an email to any address typed in, and to the job-creating `GET /download_aurn/...`
      routes? This service has none and every route is anonymous.
- [ ] **Pre-signed URL handling on the emailed-link route.** `src/server/verify/controller.js`
      writes the backend response (the pre-signed URL) to the log at info level, fetches the
      URL server-side without checking its scheme or host, and the result page writes it
      unescaped into an inline script. Confirm these can be tightened.
- [ ] **Email address kept in the session.** The address is stored on submission and never
      cleared, so it stays in Redis for up to the four-hour session lifetime. Confirm this is
      acceptable for the privacy notice and any data protection assessment, or clear it after
      the request is sent.
- [ ] **Session cookie secret rotation.** The committed default for the session cookie
      secret was removed on 19 October 2026 and the service now refuses to start without
      `SESSION_COOKIE_PASSWORD`. The repository's own remediation note still lists
      confirming and rotating the secret in every live environment as an outstanding action,
      and the old default (and the literal `AQIE_PASSWORD` default removed at the same time)
      remain in public git history. Confirm rotation and whether any history clean-up is
      wanted. The values are deliberately not recorded here.
- [ ] **LAQM Portal credentials and owner.** `LAQMAPIKEY` and `LAQMAPIPARTNERID` still
      default to their own names, so an unset environment makes a live but unauthenticated
      call (`src/config/config.js`). Confirm the operational owner, support contact and
      expected availability of the LAQM Portal API (catalogue question `oq-007`), given that
      the local authority picker degrades to an empty list when it is unreachable and the
      cache is cold.
- [ ] **`Osname api url` is used as an environment variable name.** The `OS_NAMES_API_URL`
      config entry declares its `env` as the literal string `Osname api url`, which contains
      spaces and cannot be set conventionally. Confirm whether the deployed default is
      relied upon.
- [ ] **`GET /some-path`** in `src/server/year_pollutiondetails/index.js` redirects to
      `/invalid-path`, which is not a route, and has no journey role. Confirm whether it is
      reachable and whether it can be removed.
- [ ] **Leftover template and proof-of-concept residue.** `@hapi/cookie`,
      `aws-embedded-metrics`, `global-agent`, `http-proxy-agent`, `node-fetch`,
      `path-browserify` and `util` are declared in `package.json` but never imported;
      `jest.config.js` and `sonar-project.properties` still ignore `src/server/cdp-uploader/`
      and `src/server/utils/xlsxParser.js`, which do not exist; `getAPIdownloadUKEAP` in
      `src/server/download_dataselector/index.njk` calls `/download_ukeap/...` routes that do
      not exist; and `GET /stationcount_ukeap` is not called by any page. Confirm these can
      be removed.
- [ ] **Accessibility statement.** The published statement says the service complies with
      WCAG 2.2 AA and was last independently tested on 5 June 2025, before the DAQI, Last 24
      hours and Last 7 days tabs and the map hand-off were added. The repository records that
      the legally defined DAQI band colours fall short of the usual contrast standard (bands
      8 and 10), mitigated by always showing the band number and label. Confirm a re-test is
      planned and that the statement will list the contrast exception.
