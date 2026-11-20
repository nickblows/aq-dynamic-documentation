# aqie-location-backend

> A thin shared wrapper around the Ordnance Survey Names API. It turns a free-text UK place
> name or postcode into a filtered, de-duplicated list of gazetteer matches with coordinates
> and a stable URL slug, so that no other AQIE service needs to hold an OS API key.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-location-backend`](https://github.com/DEFRA/aqie-location-backend) |
| Service domain | `Data` |
| Service type | `Auxilary Backend Service` |
| Lifecycle stage | `Production` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2025-02-14` |
| Last main commit (UTC) | `2026-10-29T12:35:11Z` |
| Last analysed commit | `5f1beb5f` |
| Last analysed (UTC) | `2026-11-19T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Exposes a single application endpoint, `POST /osnameplaces`, taking a JSON body with a
  `userLocation` string.
- Calls the Ordnance Survey Names `find` API on the caller's behalf, holding the OS API key so
  that consuming services never need it.
- Restricts results to the place types that make sense for air quality lookups — City, Town,
  Village, Suburban Area, Postcode and Airport — by applying an `fq` filter.
- Removes exact duplicate results returned by the gazetteer.
- Filters results down to those whose `NAME1` or `NAME2` genuinely relate to what the user
  typed, comparing on an alphanumeric-normalised, case-insensitive basis.
- Derives a hyphenated lowercase `ID` slug for each match from the place name and its
  district or county, which consumers use to build location page URLs.
- Suppresses the upstream call entirely when the input contains one of the characters
  `%`, `$`, `&`, `#`, `!`, `¬` or a backtick, rather than forwarding junk to Ordnance Survey,
  and answers with an empty list.
- Returns an empty list when Ordnance Survey finds no matches, and the text `no data found`
  for blank input, instead of raising an error.

**Does not:**

- Hold or serve any air quality data. It knows nothing about pollutants, stations or DAQI.
- Find the nearest monitoring stations to a place — that is `aqie-monitoringstation-backend`,
  which calls this service first and then does the distance work.
- Do reverse geocoding (coordinates to postcode). `aqie-back-end` uses postcodes.io for that;
  this service makes no call to postcodes.io or to anything other than Ordnance Survey.
- Collapse a short postcode district to a single best match. The code contains that rule, but
  its length check reads a constant from the wrong module, so the branch never runs. See
  Section 11.
- Cache results. Every request is a fresh call to Ordnance Survey.
- Persist anything. MongoDB is wired up by the CDP template but the place-name path does not
  read or write it.

## 3. Architecture

**Pattern:** Hapi HTTP API, stateless, one upstream call per request. It is built from the CDP
Node.js backend template and still carries the template's scaffold.

| Component | Path | Responsibility |
|---|---|---|
| Route | `src/api/getosname/index.js` | Registers `POST /osnameplaces` |
| Controller | `src/api/getosname/controller/osplace.js` | Response shaping and security headers |
| Orchestration | `src/api/getosname/helper/get-osplace-util.js` | Input validation, de-duplication, delegating to filtering |
| Upstream call | `src/api/getosname/helper/fetch-data.js` | Builds the OS Names URL with filters and key, refuses input containing the blocked characters, calls it through the proxy |
| Proxy call | `src/api/common/helpers/catch-proxy-fetch-error.js`, `src/api/common/helpers/proxy.js` | Performs the proxy-aware `fetch`, turns failures into a result tuple, and logs the full request URL (including the key — see Section 11) |
| Match filtering | `src/api/getosname/helper/middleware-helpers.js` | Name matching, slug generation, empty list when OS returns no `results`; contains the partial-postcode rule, which does not run (Section 11) |
| Health | `src/api/health/index.js` | Liveness endpoint |
| Example scaffold | `src/api/example/` | Unmodified CDP template sample — see below |
| Router | `src/api/router.js` | Registers health, example and `osnameplaces` plugins |
| Config | `src/config/index.js` | `convict` schema |
| Common helpers | `src/api/common/helpers/` | MongoDB, proxy, logging, metrics, tracing, secure context |

### Scaffold routes still present

`src/api/router.js` registers the CDP template's `example` plugin alongside the real one, so
`GET /example` and `GET /example/{exampleId}` are live in every deployed environment. These are
template sample code backed by a MongoDB `example-data` collection and have nothing to do with
place-name lookup. They are the reason MongoDB is a dependency at all. They should be removed;
see Section 11.

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/health` | Liveness probe | — | `{ message: 'success' }` |
| `POST` | `/osnameplaces` | Resolve a UK place name or postcode | JSON body with `userLocation` | `{ message: 'success', getOSPlaces }` where `getOSPlaces` is the filtered array of OS gazetteer entries, each with an added `ID` slug; an empty array when nothing matches or the input contains a blocked character; the text `no data found` for blank input; absent when the upstream call fails (the status is still 200) |
| `GET` | `/example` | CDP template scaffold — not part of the service contract | — | Sample documents |
| `GET` | `/example/{exampleId}` | CDP template scaffold — not part of the service contract | `exampleId` | Sample document |

`/osnameplaces` is `POST` only, and a trailing slash is accepted. The service served
`GET /osnameplaces/userLocation={userLocation}` until August 2025, when the search text moved
into a request body after a penetration test; that path no longer matches any route, so a
request to it gets `404`.

Responses set `Access-Control-Allow-Origin` plus a full set of security headers
(`Content-Security-Policy`, `Referrer-Policy`, `X-Content-Type-Options`, `X-Frame-Options`,
`X-XSS-Protection`, `Strict-Transport-Security`).

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| Ordnance Survey Names API | External API | `GET /search/names/v1/find` with `query`, `fq` local-type filters and `key` | Place-name query in; gazetteer entries with names, district/county and coordinates out | API key (`OS_NAMES_API_KEY`), passed as a query parameter and written to the application log with the rest of the URL (Section 11) |
| MongoDB | Datastore | Driver connection | Connected at start-up; used only by the scaffold `example` routes | `MONGO_URI` |

> This is the only outbound HTTP call in the service. There is no call to postcodes.io or to
> any other AQIE service.

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| `aqie-monitoringstation-backend` | `POST /osnameplaces` | Location string in; gazetteer matches out, used as the origin for the nearest-station search |
| `aqie-dataselector-frontend` | `POST /osnameplaces` | Place names entered in the historic data selection journey |
| `aqie-prtr-backend` | `POST /osnameplaces` | Place names for pollutant release facility location search |

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).
>
> All three callers send `POST` with a JSON body `{ userLocation }`. The performance test plan
> in `aqie-data-priv-beta-api-perftest` still uses the old `GET /osnameplaces/userLocation=`
> form, which no route serves any longer, so those requests would get `404` (catalogue
> `oq-009`).
>
> `aqie-prtr-backend` records in its own configuration that "the upstream service owns the API
> key" — this service exists precisely so that key stays in one place.

## 7. Data

- **Store:** MongoDB (`MONGO_DATABASE`, defaulting to `aqie-location-backend`). Connected and
  indexed at start-up (`example-data` and `mongo-locks`) but used only by the scaffold
  `example` routes; the place-name path is stateless. The lock manager is set up but nothing
  acquires a lock.
- **Key entities:** Ordnance Survey `GAZETTEER_ENTRY` objects, passed through as received,
  with an `ID` slug added.
- **Retention / refresh:** none. No caching layer, no TTL, no scheduled work. Freshness is
  whatever Ordnance Survey returns at request time.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `PORT` | HTTP listen port (code default 3001; the Docker image sets 3000) |
| `NODE_ENV`, `SERVICE_VERSION` | Runtime identity |
| `OS_NAMES_API_URL` | Ordnance Survey Names `find` endpoint |
| `OS_NAMES_API_KEY` | Ordnance Survey API key (marked `sensitive` in the convict schema; its default is the variable's own name, so an unset variable sends an invalid key rather than failing start-up) |
| `MONGO_URI`, `MONGO_DATABASE` | MongoDB connection |
| `CDP_HTTP_PROXY`, `CDP_HTTPS_PROXY` | CDP egress proxy |
| `ACCESS_CONTROL_ALLOW_ORIGIN_URL` | CORS origin |
| `ENABLE_SECURE_CONTEXT`, `TRUSTSTORE_ONE` | TLS trust store |
| `ENABLE_METRICS`, `TRACING_HEADER` | Observability |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |

`config.validate({ allowed: 'strict' })` is applied, so an unrecognised key fails startup.

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development:latest-22` to
  `defradigital/node:latest-22` (Node.js 22; `.nvmrc` pins `v22.11.0`); entrypoint `node .`.
- **Internal address:** `https://aqie-location-backend.<env>.cdp-int.defra.cloud`. An
  `ephemeral-protected.api.<env>.cdp-int.defra.cloud/aqie-location-backend/...` form appears in
  consumers' commented-out configuration and is used for ephemeral test environments.
- **Environments:** `dev`, `test`, `perf-test`, `prod`. A separate
  `aqie-location-perf-backend` repository exists for performance testing and is archived.
- **Local development:** `compose.yml` provides MongoDB, Redis and LocalStack. The
  application does not use Redis.
- **Pipelines:**
  - `.github/workflows/build.yml` — SonarQube scan on push to `main` and on PR (on a Windows
    runner)
  - `.github/workflows/check-pull-request.yml` — format check, lint, test, test image build
    and SonarCloud scan on PR
  - `.github/workflows/publish.yml` — CDP build and publish on push, then test and SonarCloud
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish
  - The Sonar token comes from the organisation secret `AQIE_SONAR_TOKEN`. Some actions are
    referenced by branch (`@master`, `@main`) rather than a pinned version.

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, formatted with `@elastic/ecs-pino-format` in production.
  Authorization and cookie headers are redacted in production. The redaction does not cover
  message text: the service logs the complete upstream URL, which includes the Ordnance Survey
  key, and the search text the citizen typed (Section 11).
- **Tracing:** `@defra/hapi-tracing` propagating the header named in `TRACING_HEADER`.
- **Metrics:** an `aws-embedded-metrics` (CloudWatch EMF) helper exists, gated by
  `ENABLE_METRICS`, but nothing in the application calls it, so no custom metrics are emitted.
- **Shutdown:** `hapi-pulse` for graceful draining.

## 11. Open Questions

- [ ] **The Ordnance Survey API key is written to the application log.** The helper that
      makes the call logs the complete request URL, which carries the key as a query
      parameter, on every request and on failure. Confirm the logs can be cleaned, rotate the
      key after the fix, and confirm whether OS supports a header-based alternative for this
      endpoint.
- [ ] (catalogue `oq-036`) The partial-postcode rule does not run. Its length check reads
      `locationNameOrPostcodelength` from `src/api/common/constants/status-codes.js`, which has
      no such key (the value 3 is defined in `src/api/getosname/helper/constants.js`, which the
      file does not import), so the comparison is always false. The unit test hides this by
      mocking the module. Since July 2025 a short postcode district has therefore been treated
      like any other search. Confirm whether the rule is still wanted, noting that a threshold
      of three characters would not cover a district such as `SW1A`, and whether callers
      depend on the rewritten `NAME1` it was meant to produce.
- [ ] Upstream failures (network error, 401, 403, 429, 5xx) come back as HTTP 200
      `{ message: 'success' }` with no `getOSPlaces`, so callers cannot tell an outage from no
      matches. The `getOSPlaces` field is also sometimes an array, sometimes the text
      `no data found` and sometimes absent. Confirm that is intended.
- [ ] Whatever the citizen types, often a home postcode, is logged at info level and again
      inside the logged URL. Confirm that is acceptable and what the log retention period is.
- [ ] (catalogue `oq-009`) The performance test plan in `aqie-data-priv-beta-api-perftest` still calls the removed
      `GET` forms of this endpoint and of `/monitoringstation`. Who will update it?
- [ ] The CDP scaffold `example` routes are still registered and reachable in deployed
      environments. Confirm they can be removed — which would also remove the only reason this
      service needs MongoDB.
- [ ] There is no authentication, rate limit or caching in front of a key-protected, quota
      limited upstream, and three services call this on user-facing paths. Confirm with the
      owner whether the OS Names licence and rate limits make a short-lived cache or per-caller
      limit worthwhile.
- [ ] The README is the unedited CDP template: it documents only `/health` and the example
      routes and says Node.js `>= v18`, whereas `package.json` requires `>=22`. Confirm it will
      be replaced with a description of `/osnameplaces`.
- [ ] Which port does CDP expect? The code default is 3001, the Docker image sets 3000 and
      `compose.yml` publishes 3555.
- [ ] Redis appears in `compose.yml` but is not used by the application. Confirm it can be
      removed from the local environment.
