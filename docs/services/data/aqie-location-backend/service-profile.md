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
| Last main commit (UTC) | `2026-05-19T15:31:48Z` |
| Last analysed commit | `7d489140` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Monitoring` |

## 2. Purpose and Responsibilities

**Does:**

- Exposes a single application endpoint, `POST /osnameplaces`, taking a `userLocation` string.
- Calls the Ordnance Survey Names `find` API on the caller's behalf, holding the OS API key so
  that consuming services never need it.
- Restricts results to the place types that make sense for air quality lookups — City, Town,
  Village, Suburban Area, Postcode and Airport — by applying an `fq` filter.
- Removes exact duplicate results returned by the gazetteer.
- Filters results down to those whose `NAME1` or `NAME2` genuinely relate to what the user
  typed, comparing on an alphanumeric-normalised, case-insensitive basis.
- Applies a specific partial-postcode rule: where the input looks like a postcode district
  (for example `SW1A`), it collapses the result set to the single best match and substitutes a
  sensible display name.
- Derives a hyphenated lowercase `ID` slug for each match from the place name and its
  district or county, which consumers use to build location page URLs.
- Suppresses the upstream call entirely when the input contains characters that cannot appear
  in a place name, rather than forwarding junk to Ordnance Survey.
- Returns `'no data found'` for blank or malformed input instead of raising an error.

**Does not:**

- Hold or serve any air quality data. It knows nothing about pollutants, stations or DAQI.
- Find the nearest monitoring stations to a place — that is `aqie-monitoringstation-backend`,
  which calls this service first and then does the distance work.
- Do reverse geocoding (coordinates to postcode). `aqie-back-end` uses postcodes.io for that.
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
| Upstream call | `src/api/getosname/helper/fetch-data.js` | Builds the OS Names URL with filters and key, calls it through the proxy |
| Match filtering | `src/api/getosname/helper/middleware-helpers.js` | Name matching, partial-postcode rule, slug generation |
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
| `GET` | `/health` | Liveness probe | — | Status payload |
| `POST` | `/osnameplaces` | Resolve a UK place name or postcode | JSON body with `userLocation` | `{ message: 'success', getOSPlaces }` where `getOSPlaces` is the filtered array of OS gazetteer entries, each with an added `ID` slug |
| `GET` | `/example` | CDP template scaffold — not part of the service contract | — | Sample documents |
| `GET` | `/example/{exampleId}` | CDP template scaffold — not part of the service contract | `exampleId` | Sample document |

Responses set `Access-Control-Allow-Origin` plus a full set of security headers
(`Content-Security-Policy`, `Referrer-Policy`, `X-Content-Type-Options`, `X-Frame-Options`,
`X-XSS-Protection`, `Strict-Transport-Security`).

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| Ordnance Survey Names API | External API | `GET /search/names/v1/find` with `query`, `fq` local-type filters and `key` | Place-name query in; gazetteer entries with names, district/county and coordinates out | API key (`OS_NAMES_API_KEY`), passed as a query parameter |
| MongoDB | Datastore | Driver connection | Used only by the scaffold `example` routes | `MONGO_URI` |

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| `aqie-monitoringstation-backend` | `POST /osnameplaces` | Location string in; gazetteer matches out, used as the origin for the nearest-station search |
| `aqie-dataselector-frontend` | `POST /osnameplaces` | Place names entered in the historic data selection journey |
| `aqie-prtr-backend` | `POST /osnameplaces` | Place names for pollutant release facility location search |

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).
>
> `aqie-prtr-backend` records in its own configuration that "the upstream service owns the API
> key" — this service exists precisely so that key stays in one place.

## 7. Data

- **Store:** MongoDB (`MONGO_DATABASE`, defaulting to `aqie-location-backend`). Used only by
  the scaffold `example` routes; the place-name path is stateless.
- **Key entities:** Ordnance Survey `GAZETTEER_ENTRY` objects, passed through largely as
  received, with an `ID` slug added and `NAME1` occasionally rewritten by the partial-postcode
  rule.
- **Retention / refresh:** none. No caching layer, no TTL, no scheduled work. Freshness is
  whatever Ordnance Survey returns at request time.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `PORT` | HTTP listen port |
| `NODE_ENV`, `SERVICE_VERSION` | Runtime identity |
| `OS_NAMES_API_URL` | Ordnance Survey Names `find` endpoint |
| `OS_NAMES_API_KEY` | Ordnance Survey API key (marked `sensitive` in the convict schema) |
| `MONGO_URI`, `MONGO_DATABASE` | MongoDB connection |
| `CDP_HTTP_PROXY`, `CDP_HTTPS_PROXY` | CDP egress proxy |
| `ACCESS_CONTROL_ALLOW_ORIGIN_URL` | CORS origin |
| `ENABLE_SECURE_CONTEXT`, `TRUSTSTORE_ONE` | TLS trust store |
| `ENABLE_METRICS`, `TRACING_HEADER` | Observability |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |

`config.validate({ allowed: 'strict' })` is applied, so an unrecognised key fails startup.

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`;
  entrypoint `node .`.
- **Internal address:** `https://aqie-location-backend.<env>.cdp-int.defra.cloud`. An
  `ephemeral-protected.api.<env>.cdp-int.defra.cloud/aqie-location-backend/...` form appears in
  consumers' commented-out configuration and is used for ephemeral test environments.
- **Environments:** `dev`, `test`, `perf-test`, `prod`. A separate
  `aqie-location-perf-backend` repository exists for performance testing and is archived.
- **Local development:** `compose.yml` provides MongoDB, Redis and LocalStack.
- **Pipelines:**
  - `.github/workflows/build.yml` — build and SonarQube scan on push and PR
  - `.github/workflows/check-pull-request.yml` — lint and test on PR
  - `.github/workflows/publish.yml` — build and publish on push
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, formatted with `@elastic/ecs-pino-format` in production.
  Authorization and cookie headers are redacted in production.
- **Tracing:** `@defra/hapi-tracing` propagating the header named in `TRACING_HEADER`.
- **Metrics:** `aws-embedded-metrics` (CloudWatch EMF), gated by `ENABLE_METRICS`.
- **Shutdown:** `hapi-pulse` for graceful draining.

## 11. Open Questions

- [ ] The CDP scaffold `example` routes are still registered and reachable in deployed
      environments. Confirm they can be removed — which would also remove the only reason this
      service needs MongoDB.
- [ ] The Ordnance Survey API key is sent as a URL query parameter. Confirm whether OS supports
      a header-based alternative for this endpoint, since query parameters are more likely to
      end up in proxy and access logs.
- [ ] There is no caching. Confirm with the owner whether the OS Names licence and rate limits
      make a short-lived cache worthwhile given three services call this on user-facing paths.
- [ ] The partial-postcode rule silently rewrites `NAME1`. Confirm this is the agreed display
      behaviour with the content designers.
- [ ] Redis appears in `compose.yml` but is not used by the application. Confirm it can be
      removed from the local environment.
