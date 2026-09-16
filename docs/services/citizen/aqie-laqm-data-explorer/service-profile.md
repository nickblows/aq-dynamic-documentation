# aqie-laqm-data-explorer

> A GOV.UK Prototype Kit spike that probes the LAQM Portal API and reports, endpoint by
> endpoint, what local authority air quality data is actually available and how complete it is.
> It exists to de-risk building local authority information pages.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-laqm-data-explorer`](https://github.com/DEFRA/aqie-laqm-data-explorer) |
| Service domain | `Citizen` |
| Service type | `Data/Analytics Support Service` |
| Lifecycle stage | `Prototype/PoC` |
| Primary language | HTML |
| Runtime | Node.js `>=22` (CommonJS) |
| Default branch | `main` |
| Created (UTC) | `2026-06-30` |
| Last main commit (UTC) | `2026-07-08T14:16:27Z` |
| Last analysed commit | `5b10202a` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Calls the **live** LAQM (Local Air Quality Management) Portal API and displays, for each
  endpoint, the records returned and a field-by-field completeness assessment.
- Provides a single "data availability assessment" page that probes every endpoint at once for
  a chosen local authority and reporting year, reporting HTTP status, the portal's own result
  code, record count, field count, completeness percentage and response duration.
- Maps each endpoint to the local authority information it could support — overall compliance,
  action plan measures from Annual Status Report table 2.2, and the NO₂ compliance dataset.
- Browses the individual datasets: all local authorities, regions, a single local authority
  record, NO₂ diffusion tube monitoring, automatic (ADES) monitoring with exceedances, and the
  top three AQAP action plan measures.
- Auto-paginates the diffusion tube and automatic monitoring endpoints and aggregates the pages
  before assessing completeness.
- Validates that every path parameter it sends is a non-negative integer, because the portal
  accepts a restricted character set and the values are interpolated into the request path.
- Degrades to a readable error page — distinguishing timeouts, TLS and DNS failures, non-JSON
  responses and portal result codes — rather than failing opaquely.

**Does not:**

- Serve citizens. It is an internal spike tool behind CDP basic authentication.
- Store, cache or transform LAQM data. Every page view calls the live portal; there is no
  database and no scheduled job.
- Call any AQIE service. It does not read from `aqie-back-end` and is not part of the
  measurement or forecast data flow.
- Provide monitoring station readings, DAQI values or forecasts — those come from
  `aqie-back-end` and `aqie-forecast-api` and are surfaced by `aqie-front-end`.
- Build the local authority information pages themselves. It only assesses whether the data
  needed to build them exists.

## 3. Architecture

**Pattern:** GOV.UK Prototype Kit (Express and Nunjucks) with a single route file, one API
client and a completeness analyser. All calls run server-side; there is no client-side
JavaScript beyond the GOV.UK Frontend bundle.

| Component | Path | Responsibility |
|---|---|---|
| Routes | `app/routes.js` | One route per dataset, plus the combined assessment page |
| LAQM client | `app/lib/laqm-api.js` | Wraps the portal endpoints, applies auth headers, timeouts, proxy dispatcher, pagination and error shaping |
| Completeness | `app/lib/completeness.js` | Calculates per-field and overall completeness for a set of records |
| Views | `app/views/` | One template per dataset, the assessment table and an error page |
| Config | `app/config.json` | Prototype Kit service name and plugin settings |

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/` | Landing page linking to each dataset and the assessment | — | HTML |
| `GET` | `/local-authorities` | Directory of local authorities | — | HTML |
| `GET` | `/regions` | Region list used for grouping and filtering | — | HTML |
| `GET` | `/local-authority` | Single local authority record, including report links | `laId` | HTML |
| `GET` | `/diffusion-tubes` | NO₂ diffusion tube monitoring, auto-paginated | `laId`, `year`, `perPage` | HTML |
| `GET` | `/automatic-monitoring` | Automatic (ADES) monitoring and exceedances, auto-paginated | `laId`, `year`, `perPage` | HTML |
| `GET` | `/aqap-measures` | Top three AQAP action plan measures | `laId`, `year` | HTML |
| `GET` | `/assessment` | Probes all six endpoints in parallel and tabulates availability and completeness | `laId`, `year` | HTML |

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| LAQM Portal API (UK-AIR) | External API | `GET /xapi/getLocalAuthorities/json` | Directory of local authorities | `X-API-Key` and `X-API-PartnerId` headers |
| LAQM Portal API (UK-AIR) | External API | `GET /xapi/getRegions/json` | Region list | Same |
| LAQM Portal API (UK-AIR) | External API | `GET /xapi/getSingleLAData/{laId}/json` | Local authority identity, AQAP and annual report links | Same |
| LAQM Portal API (UK-AIR) | External API | `GET /xapi/getSingleDTDataByYear/{year}/{laId}/{page}/{perPage}/json` | NO₂ diffusion tube records, available from reporting year 2021 | Same |
| LAQM Portal API (UK-AIR) | External API | `GET /xapi/getADESDataByYear/{year}/{laId}/{page}/{perPage}/json` | Automatic monitoring records and exceedances, available from 2025 | Same |
| LAQM Portal API (UK-AIR) | External API | `GET /xapi/getTop3AQAPMeasuresByYear/{laId}/{year}/json` | Top three action plan measures, available from 2025 | Same |

> `LAQM_API_BASE_URL` points at the public LAQM Portal (`www.laqmportal.co.uk`), **not** at an
> AQIE service. This answers catalogue open question `oq-004`. The edge is not yet recorded in
> the integration catalogue.

## 6. Consumed By (Inbound Dependencies)

No AQIE service consumes this one. It is a standalone spike tool reached directly in a browser.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** none. No database, cache, queue or build step.
- **Key entities:** a *local authority* (identity, region, report links), a *diffusion tube
  record* and an *automatic monitoring record* for a reporting year, and an *AQAP measure*.
  The portal wraps each response in an envelope carrying a `result_code` alongside the data array.
- **Derived data:** a completeness assessment per response — how many fields each record type
  has and what proportion of them are populated across the returned records.
- **Retention / refresh:** nothing is retained. Every request calls the live portal. The default
  reporting year comes from configuration and the default page size is set in the route layer.

## 8. Configuration

Variable names only — values are held in CDP secrets and a local `.env` file, and are never
recorded here.

| Variable | Purpose |
|---|---|
| `LAQM_API_BASE_URL` | LAQM Portal base URL; defaults to the public portal |
| `LAQM_API_PARTNER_ID` | Partner identifier sent as the `X-API-PartnerId` header |
| `LAQM_API_KEY` | Secret key sent as the `X-API-Key` header |
| `LAQM_API_TIMEOUT_MS` | Request timeout |
| `LAQM_DEFAULT_YEAR` | Default reporting year for the dataset pages |
| `CDP_HTTPS_PROXY`, `HTTPS_PROXY`, `HTTP_PROXY` | CDP egress proxy selection |
| `NODE_EXTRA_CA_CERTS` | Trusts a corporate TLS-inspecting proxy's root CA during local development |
| `PORT`, `NODE_ENV` | HTTP listener and runtime mode |
| `PASSWORD`, `PASSWORD_KEYS` | GOV.UK Prototype Kit basic authentication, required on CDP |
| `USE_HTTPS` | Disabled in the production image because CDP terminates TLS at the nginx layer |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`;
  `curl` is added to the production image for the CDP health check. Development runs
  `npm run dev`, production runs `npm start`.
- **Egress:** the service uses `undici`'s own `fetch` with an explicit `ProxyAgent` because
  Node's global `fetch` ignores the proxy environment variables. HTTP/2 is disabled on both the
  proxy leg and the tunnelled origin leg, since negotiating it breaks the CONNECT tunnel
  through the CDP proxy.
- **Request identity:** an explicit `User-Agent` is sent because the portal's edge protection
  rejects default client user agents.
- **Access control:** Prototype Kit basic authentication is on by default in CDP environments.
- **Environments:** `dev` (prototype environments only).
- **Pipelines:**
  - `.github/workflows/publish.yml` — build and publish on push to `main`

## 10. Observability

- **Logging:** console logging only. Upstream failures are logged with the underlying cause
  unwrapped, and any proxy URL is redacted of embedded credentials before it is logged.
- **Tracing:** none.
- **Metrics:** none, although the assessment page records and displays per-endpoint response
  durations, which is the tool's main purpose.

## 11. Open Questions

- [ ] `oq-004` is answered — `LAQM_API_BASE_URL` targets the external LAQM Portal. Confirm the
      commercial and data-sharing basis for the partner identifier and API key before any
      production use.
- [ ] Confirm which organisation operates the LAQM Portal API and who owns the AQIE partner
      credentials.
- [ ] Confirm whether the assessment concluded the data is fit to build local authority pages,
      and which service would own those pages.
- [ ] Automatic monitoring and AQAP data are only available from reporting year 2025 and
      diffusion tube data from 2021. Confirm whether earlier years are obtainable another way.
