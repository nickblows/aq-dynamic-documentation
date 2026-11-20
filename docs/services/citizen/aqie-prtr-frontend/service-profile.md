# aqie-prtr-frontend

> The public GOV.UK journey for the UK Pollutant Release and Transfer Register. Lets citizens
> find industrial sites by name, location, region, river basin or reporting year, view what
> each site released or transferred in a given year, and download the full annual dataset.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-prtr-frontend`](https://github.com/DEFRA/aqie-prtr-frontend) |
| Service domain | `Citizen` |
| Service type | `Auxilary Frontend` |
| Lifecycle stage | `Beta` |
| Primary language | JavaScript |
| Runtime | Node.js `>=24` (ES modules); container parent image is Node 24.22.1 while `.nvmrc` still says `v24.14.1` |
| Default branch | `main` |
| Created (UTC) | `2026-05-21` |
| Last main commit (UTC) | `2026-10-26T16:49:06Z` |
| Last analysed commit | `ad0ec2f6` |
| Last analysed (UTC) | `2026-11-19T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Presents the PRTR search journey: choose a search method, then search by facility name,
  by location, by region, by river basin or by reporting year.
- Resolves a citizen's free-text location to candidate places, disambiguates multiple
  matches, and lists industrial sites near the chosen place.
- Renders a facility's release and transfer record for a chosen year, with drill-down into
  a single release, transfer or waste line.
- Renders facility reference detail and the facility's competent authority and contacts.
- Offers the full annual PRTR dataset as a file download, streamed through the service so
  the browser saves it rather than rendering the XML inline.
- Serves the supporting static pages — about, service problem, no-location-found — and the
  GOV.UK Frontend asset bundle built by Vite.

**Does not:**

- Hold or query any PRTR data itself. Every data read is an HTTP call to `aqie-prtr-backend`;
  there is no database in this service.
- Call `aqie-location-backend` directly. Place-name lookup goes through the backend's
  `/locations/search`, unlike `aqie-dataselector-frontend` and `aqie-front-end`, which each
  call the location backend themselves.
- Talk to S3 with AWS credentials. It only fetches a pre-signed HTTPS URL that
  `aqie-prtr-backend` hands it.
- Show ambient air quality, DAQI or forecasts — that is `aqie-front-end`.
- Provide historic ambient monitoring extracts — that is `aqie-dataselector-frontend`.
- Provide any admin, upload or data-maintenance function. The journey is read-only and
  unauthenticated.
- Accept PRTR submissions. The `aqie-prtr-submissions-frontend` and `aqie-prtr-submissions-backend`
  repositories created in October 2026 are unconnected scaffolds. This site neither links to
  them nor calls them, and they do not replace it.

## 3. Architecture

**Pattern:** Hapi server-side rendered GOV.UK Frontend service using Nunjucks, with a thin
typed API client layer over `aqie-prtr-backend`. Each route is a folder containing
`index.js` (route registration and param validation), `controller.js` (handler) and
`content.js` (page copy), with a co-located `.njk` template.

| Component | Path | Responsibility |
|---|---|---|
| Router | `src/server/plugins/router.js` | Registers every route plugin and static file serving |
| Search entry | `src/server/routes/search-facility/` | Chooses which search method to use; stores a selection error in session |
| Name search | `src/server/routes/search-by-name/` | Facility name search form and results |
| Location search | `src/server/routes/find-industrial-sites-by-location/` | Free-text place search, with a `searchagain` variant |
| Location disambiguation | `src/server/routes/multiplelocations/` | Picks between multiple matching places; caches the result set in session |
| No match | `src/server/routes/no-location-found/` | Dead-end page when a place cannot be resolved |
| Region / river basin / year search | `src/server/routes/search-by-region/`, `search-by-river-basin/`, `search-by-year/` | The three remaining field searches |
| Results list | `src/server/routes/facilities/` | Paginated facility result list |
| Facility record | `src/server/routes/facility-record/` | Releases and transfers for a facility and year |
| Line detail | `src/server/routes/additional-detail/` | One release, transfer or waste line |
| Facility details | `src/server/routes/facility-details/` | Address, NACE, NUTS, river basin reference view |
| Competent authority | `src/server/routes/competent-authority/` | Regulator name and contacts |
| Download | `src/server/routes/download/` | Year chooser plus a temporary server-side file proxy |
| API client | `src/server/common/api/` | One module per backend resource over a shared `fetchJson` helper |
| Resilience helper | `src/server/common/helpers/fetch-with-retry.js` | Timeout (10 seconds by default) and optional retry around backend calls; callers set no retries, so there are none |
| Language | `src/server/common/helpers/resolve-language.js`, each route's `content.js` | `?lang=en` or `?lang=cy` selects the page copy; the Welsh strings are placeholders |
| Session cache | `src/server/plugins/session-cache.js`, `src/server/common/helpers/session-cache/cache-engine.js`, `src/server/common/helpers/redis-client.js` | `yar` sessions on `catbox-redis` in deployed environments, `catbox-memory` locally |
| Config | `src/config/config.js` | `convict` schema |

`src/server/common/api/api-common.js` centralises base-URL normalisation, the `Accept`
header, retry, non-2xx handling and `204` handling, so every resource module is a one-line
path builder. All backend paths are built with `encodeURIComponent` on user-supplied
identifiers.

## 4. API Surface

Routes are user-facing HTML pages unless noted. `{language?}` on the start and download pages
accepts `en` or `cy` only and is rejected at route validation otherwise. Other pages select the
language with a `?lang=en` or `?lang=cy` query parameter. Every Welsh (`cy`) string in all 16 page
content modules is a placeholder, the English text with ` --CY` appended, so there is no real Welsh
translation yet.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness probe (JSON) |
| `GET` | `/uk-pollutant-release-and-transfer-register/{language?}` | Service start page |
| `GET` | `/about` | About the register |
| `GET`, `POST` | `/search-facility` | Choose a search method |
| `GET`, `POST` | `/search-by-name` | Search by facility name |
| `GET`, `POST` | `/find-industrial-sites-by-location` | Search by place name or postcode |
| `GET` | `/find-industrial-sites-by-location/searchagain` | Re-enter a location search |
| `GET`, `POST` | `/multiplelocations` | Choose between multiple matching places |
| `GET` | `/no-location-found` | No matching place |
| `GET`, `POST` | `/search-by-region` | Search by region or county |
| `GET`, `POST` | `/search-by-river-basin` | Search by river basin district |
| `GET`, `POST` | `/search-by-year` | Search by reporting year |
| `GET` | `/facilities` | Paginated facility results |
| `GET` | `/facility/{id}` | Facility record for the latest reporting year |
| `GET` | `/facility/{id}/{year}` | Facility record for a chosen year |
| `GET` | `/facility/{id}/{year}/lines/{lineId}` | One release, transfer or waste line |
| `GET` | `/facility/{id}/details` | Facility reference detail |
| `GET` | `/facility/{id}/competent-authority` | Competent authority and contacts |
| `GET` | `/download-all-data-for-a-year/{language?}` | Choose a dataset year to download (only years the backend flags `reportIsLive`, newest first) |
| `GET` | `/download-all-data-for-a-year/file/{year}` | Streams the dataset file (four-digit year enforced) |
| `GET` | `/problem-with-service` | Error page, optionally carrying a `statusCode` |
| `GET` | `/favicon.ico`, `/public/{param*}` | Static assets |

### Download mechanism

`/download-all-data-for-a-year/file/{year}` is explicitly marked temporary in the code. It
asks `aqie-prtr-backend` for a pre-signed link, validates that the returned URL parses and
uses `https:`, fetches it server-side with a plain `fetch` (no allow-list on the host and no
timeout), and streams the body back with `Content-Disposition: attachment` and
`Cache-Control: no-store`, naming the file `uk_prtr_dataset_<year>.xml`. The URL is never taken from
the citizen: it comes only from the backend response, and the year must be four digits. The stated
intent is to drop this proxy and link straight to the pre-signed URL once the backend sets the
disposition header itself. Any failure redirects to `/problem-with-service?statusCode=502`.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-prtr-backend` | AQIE service | `GET /facilities/search` (`BACKEND_URL`) | Search type, term and pagination in; facility results out | CDP internal network |
| `aqie-prtr-backend` | AQIE service | `GET /facilities/nearby` | Coordinates, radius and pagination in; distance-sorted facilities out | CDP internal network |
| `aqie-prtr-backend` | AQIE service | `GET /facilities/{id}/record/{year?}` | Facility id and year in; releases, transfers and waste lines out | CDP internal network |
| `aqie-prtr-backend` | AQIE service | `GET /facilities/{id}/record/{year}/lines/{lineId}` | Line identifier in; line detail out | CDP internal network |
| `aqie-prtr-backend` | AQIE service | `GET /facilities/{id}/details` | Facility id in; address, NACE, NUTS, river basin out | CDP internal network |
| `aqie-prtr-backend` | AQIE service | `GET /facilities/{id}/competent-authority` | Facility id in; regulator and contacts out | CDP internal network |
| `aqie-prtr-backend` | AQIE service | `GET /locations/search` | Place-name query in; candidate locations out | CDP internal network |
| `aqie-prtr-backend` | AQIE service | `GET /reports` | Available report years | CDP internal network |
| `aqie-prtr-backend` | AQIE service | `GET /reports/get-download-link/{year}` | Year in; S3 pre-signed URL out | CDP internal network |
| AWS S3 (pre-signed) | External | `GET <pre-signed URL>` from `download-proxy.js` | Annual PRTR dataset XML streamed to the citizen | Signature embedded in the URL |
| Redis | Datastore | `catbox-redis` / `ioredis` | Server-side session cache | `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_TLS` |

Outbound links to `gov.uk` and to the Eurostat NUTS overview are static hyperlinks in
templates and content, not runtime calls.

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| Public internet (citizens) | All HTML routes above | Search criteria in; facility and release information out |
| `aqie-prtr-journey-tests` | Public journey routes | End-to-end browser assertions |

`aqie-prtr-perftest` is an unconfigured template (see its profile) and sends no traffic to this service yet.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).
> The catalogue lists all nine backend endpoints this service calls and the pre-signed S3 fetch.
> Redis is recorded as a datastore, not an edge. No other AQIE service calls this one.

## 7. Data

- **Stores:** none of its own. Redis is used only as a server-side session cache
  (`catbox-redis`, `@hapi/yar`), falling back to in-memory locally.
- **Session keys held:** `fullSearchQuery` (the citizen's raw location input),
  `locationsResult` (the candidate location set for the disambiguation page),
  `chooserError` and `errorMessage`/`errors` for validation summaries. No personal data is
  persisted beyond the session TTL.
- **Retention:** session cache TTL and cookie TTL both default to four hours
  (`SESSION_CACHE_TTL`, `SESSION_COOKIE_TTL`). Static asset caching defaults to one week.
- **MongoDB appears in `compose.yml` only** — it is inherited from the CDP frontend template
  and is not used by the service.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `PORT`, `HOST` | HTTP listener |
| `NODE_ENV`, `SERVICE_VERSION` | Runtime identity |
| `BACKEND_URL` | `aqie-prtr-backend` base URL |
| `ASSET_PATH`, `STATIC_CACHE_TIMEOUT` | Static asset serving |
| `REDIS_HOST`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_KEY_PREFIX`, `REDIS_TLS`, `USE_SINGLE_INSTANCE_CACHE` | Session cache backend |
| `SESSION_CACHE_ENGINE`, `SESSION_CACHE_NAME`, `SESSION_CACHE_TTL` | Catbox cache selection and lifetime |
| `SESSION_COOKIE_PASSWORD`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_TTL` | Session cookie signing and lifetime. The password has a committed placeholder default, so confirm the variable is set in CDP |
| `HTTP_PROXY` | CDP egress proxy |
| `ENABLE_SECURE_CONTEXT` | Declared in config but not read by service code |
| `TRACING_HEADER` | CDP trace header name |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT`, `LOG_REDACT` | Logging |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` through a
  `development` stage to `defradigital/node`, parent image `3.2.4-node24.22.1`; entrypoint
  `node src`. `prestart` runs the Vite frontend build.
- **Environments:** CDP `dev`, `test`, `perf-test`, `prod`. The repository does not show which are
  actually deployed.
- **Local development:** `compose.yml` provides Redis, MongoDB (unused) and a `floci`
  container.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — security audit, Vite build, format check, lint
    (ESLint and Stylelint), tests, a Docker build test and a Sonar scan (skipped for Dependabot) on PR
  - `.github/workflows/publish.yml` — build and publish on push
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish
- **Testing:** `vitest` with coverage and `cheerio` for rendered-markup assertions.

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, `@elastic/ecs-pino-format` in production, with
  `LOG_REDACT` paths applied. The shared API client logs every outbound URL at info level
  and truncates upstream error bodies to 200 characters.
- **Tracing:** `@defra/hapi-tracing` using `TRACING_HEADER`.
- **Metrics:** `@defra/cdp-metrics`.
- **Auditing:** `@defra/cdp-auditing` is declared but never imported, so no audit events are
  emitted.
- **Security headers:** `blankie` with `@hapi/scooter` for Content Security Policy.
- **Shutdown:** `hapi-pulse`.

## 11. Open Questions

- [ ] Welsh language: every Welsh string in the page content modules is a placeholder (the English
      text with ` --CY` appended). Confirm whether real Welsh content is planned before the service
      is promoted, and whether the `cy` routes should be hidden until then.
- [ ] The dataset download proxy is marked temporary pending the backend setting
      `Content-Disposition`. Confirm whether that backend change is planned, and whether the
      proxy should then be removed.
- [ ] The proxy validates only that the pre-signed URL parses and is HTTPS, and fetches it with
      no timeout; it does not constrain the host. The URL comes only from the backend response.
      Confirm whether an S3 host allow-list and a timeout should be added as defence in depth
      (see Section 11 of the backend profile for the issuing side).
- [ ] `compose.yml` provisions MongoDB that the service does not use. Confirm it can be
      dropped from the template.
- [ ] Confirm the intended production `BACKEND_URL`; the config default is `http://localhost:3001`.
- [ ] `SESSION_COOKIE_PASSWORD` has a committed placeholder default in `src/config/config.js`.
      Confirm the variable is set in every deployed environment.
- [ ] How will this public register relate to the PRTR submissions services? They are unconnected
      scaffolds today and neither site links to the other.
