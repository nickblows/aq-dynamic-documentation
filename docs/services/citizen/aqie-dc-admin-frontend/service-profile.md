# aqie-dc-admin-frontend

> The internal caseworker interface for smoke control certification. DEFRA staff sign in with
> Microsoft Entra ID, work through the technical review of each appliance and fuel in an
> application, close the case once every item has been decided, and manage the published
> register of appliances.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-dc-admin-frontend`](https://github.com/DEFRA/aqie-dc-admin-frontend) |
| Service domain | `Citizen` (see Section 11 — this is an internal service) |
| Service type | `Auxilary Frontend` |
| Lifecycle stage | `Beta` |
| Primary language | JavaScript |
| Runtime | Node.js `>=24` (ES modules); `.nvmrc` pins `v24.11.1` (used by the CI workflows); the container parent image is `defradigital/node:3.2.4-node24.22.1` |
| Default branch | `main` |
| Created (UTC) | `2026-02-03` |
| Last main commit (UTC) | `2026-11-18T12:30:08Z` |
| Last analysed commit | `04050215` |
| Last analysed (UTC) | `2026-11-19T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Authenticates DEFRA staff against Microsoft Entra ID using the MSAL confidential client
  OpenID Connect authorisation code flow, and holds the signed-in identity in an encrypted
  cookie. Every screen requires that sign-in except the landing page, the health check,
  static assets and the `/auth/*` routes. Anyone who is not signed in is redirected to
  Microsoft and returned to the page they asked for.
- Presents a certification management dashboard showing, for appliances and for fuels, the
  number of new applications, applications in progress and total records.
- Lists appliance applications and fuel applications that are not started or in progress,
  with the reviewer, and lets a caseworker start a review (which marks the application in
  progress and records who started it) or continue one.
- Drives the **technical review of a single appliance**, screen by screen:
  - *Documentation checks*, each passed or failed: test reports (rated output, tested output
    and smoke emission), technical drawings, conformity mark and instruction manual (title,
    optional version and publication date, which are published on the public listing).
  - *Public listing checks*, each completed: check appliance details, with change pages for
    model name, model number, appliance type (and "other" type), variant details, nominal
    output and the multifuel answer (this last page is expected to fail on save, see
    Section 11); permitted fuels and whether wood is permitted; and additional conditions.
  - *Decision*: accept or reject the appliance. An incomplete-review page explains what is
    outstanding when the backend refuses an acceptance.
- Drives the **technical review of a single fuel**. Two supplier types are handled: a
  manufacturer adds test results (smoke emission and sulphur content) and checks the fuel
  details; a rebrander reviews the letter from the original manufacturer, checks the fuel
  details and adds a fuel description. Change pages cover the brand name or rebrand name,
  additional brand names, the original manufacturer, the original fuel name or brand,
  whether the original fuel was changed or mixed (and how), appearance, weight, composition,
  sulphur content, manufacturing process and quality control system. Accept or reject, with
  an incomplete-review page.
- Drives the **application-level close-out for appliance applications**: shows the
  application with its items grouped into accepted and rejected, then marks the whole
  application complete, stamping the case with the signed-in reviewer's name and email.
  Shows a confirmation page, or the outstanding items if the application is not ready.
- Manages the **appliance register**: searches it by keyword (it holds appliances from
  completed applications and legacy records), filters by status (pending, live, hidden,
  rejected) with paging, and opens an individual record.
  A record shows its overall status, certification status for England, Scotland, Wales and
  Northern Ireland, the public listing state, and pages for appliance details, application
  details, instruction manual, test reports, legacy comments (legacy records only) and a
  paged action history.
- Changes the state of a register record: certifies or uncertifies an appliance in one
  country, and hides an appliance from, or makes it live on, the public list. Both record
  the signed-in user.

**Does not:**

- Hold any data. Every read and write goes to `aqie-dc-backend`; this service stores only
  session state.
- Serve the public. The published register is `aqie-dc-frontend`, which is unauthenticated,
  read-only and bilingual. This service is English-only, authenticated, and is the only one of
  the pair that writes.
- Accept applications from manufacturers. Applications arrive at `aqie-dc-backend` from the
  DEFRA Forms service over a queue; caseworkers never key one in.
- Perform bulk register imports. `aqie-dc-backend` exposes `POST /admin/import/initiate` and
  `GET /admin/import/status`, but no screen in this repository calls them, so imports are
  triggered from outside this service.
- Close out a fuel application. The fuel journey stops at the fuel application page: its
  "Continue" button links to `/incomplete-application-review` with no application id, which
  is not a registered route, and the finish and completion screens are only linked from the
  appliance journey. There is also no fuel register screen (the dashboard "Fuel records"
  link is a placeholder).
- Check what a signed-in user is allowed to do. Any account that can sign in is treated as a
  caseworker: Entra ID group and role claims are not requested or checked.
- Manage users, roles or permissions.

## 3. Architecture

**Pattern:** Hapi server-rendered GOV.UK Frontend application. Each caseworker screen is a
self-contained folder holding its route definition, controller and a small `*-data.js` module
that is the only place that talks to the backend, so the backend contract for a screen is
visible in one file.

| Component | Path | Responsibility |
|---|---|---|
| Server composition | `src/server/server.js` | Registers logging, tracing, metrics, secure context, shutdown handling, the `yar` session cache, Nunjucks, CSP and the cookie plugin; defines the `session` auth strategy; makes it the default for every route; then registers the router, the 401 redirect and the catch-all error page |
| Router | `src/server/router.js` | Registers health, home, about, the auth plugin and every screen plugin, then static assets |
| Entra ID plugin | `src/server/plugins/azure-auth.js` | `/auth/login`, `/auth/callback` and `/auth/logout` routes (the only auth-exempt routes besides `/`, `/health` and static assets) |
| MSAL configuration | `src/config/azure-auth.js` | Lazily constructs the MSAL confidential client from authority host, tenant, client id and secret; routes MSAL logging to pino at debug level |
| Backend client | `src/server/common/api/api.js` | `fetchJson` (GET) and `patchJson` (PATCH) with the shared `x-api-key` header and error handling; the only two verbs used |
| Shared review reads | `src/server/common/services/` | Technical-review reads for one appliance or one fuel, reused by the check and change screens |
| Dashboard | `src/server/manage-certification/` | Counts for appliances and fuels |
| Application lists | `src/server/appliance-applications/`, `src/server/fuel-applications/` | New and in-progress applications with reviewer and item summary |
| Application review | `src/server/review-appliance-application/`, `src/server/review-fuel-application/` | One application with its items; the "start review" action |
| Appliance review | `src/server/review-appliance/` | Review checklist, decision and incomplete-review page |
| Appliance documentation checks | `src/server/test-reports/`, `technical-drawings/`, `conformity-mark/`, `instruction-manual/` | Pass or fail screens, with data capture for test results and the manual |
| Appliance listing checks and edits | `src/server/appliance-details/`, `check-permitted-fuels/`, `additional-conditions/`, `model-name/`, `model-number/`, `appliance-type/`, `other-appliance-type/`, `variant-appliance/`, `nominal-output/`, `multifuel-appliance/` | Public listing details and the change pages behind them |
| Fuel review | `src/server/review-fuel/`, `test-results/`, `manufacturer-letter/`, `fuel-details/`, `fuel-description/` | Fuel checklist, decision, documentation checks and the fuel details summary |
| Fuel detail edits | `src/server/brand-name/`, `additional-brand-names/`, `original-manufacturer/`, `original-brand/`, `fuel-changes/`, `fuel-appearance/`, `fuel-weight/`, `fuel-composition/`, `sulphur-content/`, `manufacturing-process/`, `quality-control/` | One change page per fuel attribute |
| Close-out | `src/server/finish-application-review/`, `application-review-complete/`, `incomplete-application-review/` | Completing an appliance application and confirming the outcome |
| Appliance register | `src/server/appliance-records/` | Searchable, filterable list of all appliance records |
| Appliance record | `src/server/appliance-record/` | One record plus sub-pages for details, application, instruction manual, test reports, legacy comments and action history |
| Record actions | `src/server/approval-status/`, `src/server/change-display-status/` | Per-country certification decision; hide or show on the public list |
| Session cache | `src/server/common/helpers/session-cache/` | `@hapi/yar` over Redis or memory |
| Browser assets | `src/client/` | GOV.UK Frontend styles and scripts, plus a small script that auto-submits the register status filter; bundled by webpack into `.public` |
| Config | `src/config/config.js` | `convict` schema |

### Authentication flow

1. A request to any protected route without a valid `auth` cookie gets a 401 from the Hapi
   cookie strategy. A response hook stores the page the caseworker asked for (path and query)
   in the `yar` session as `returnTo` and redirects the browser to `/auth/login`.
2. `GET /auth/login` creates a random state and nonce, keeps them in the `yar` session and
   asks MSAL for an authorisation code URL scoped to `openid`, `profile` and `email`, with
   `response_mode=query` and `prompt=select_account`. The authority is
   `AZURE_AUTHORITY_HOST` (default `https://login.microsoftonline.com`) plus
   `AZURE_TENANT_ID`. The browser is redirected there.
3. Entra ID authenticates the user and redirects the browser to `GET /auth/callback` at
   `AZURE_REDIRECT_URI` with the authorisation code and state in the query string.
4. The callback shows a "Sign-in error" page if Entra ID returned an error or the state is
   missing or does not match the one in the session. Otherwise it exchanges the code for
   tokens using the confidential client, passing the nonce.
5. It then sets the `auth` cookie (stateless, encrypted with `SESSION_COOKIE_PASSWORD`,
   HTTP-only, `SameSite=Lax`, secure in production, `SESSION_COOKIE_TTL` lifetime extended on
   each request) holding `isAuthenticated` and the account's home account id, username (email)
   and display name, and redirects to the remembered `returnTo` page or `/`.
6. `GET /auth/logout` clears the cookie, resets the session and redirects to the tenant's
   `oauth2/v2.0/logout` endpoint. No page links to it, and the configured post-logout redirect
   variable is not read.

The reviewer's name and email taken from this session are written to the backend as
`reviewedBy` (or `decidedBy` for country certification) when a decision is recorded. If either
is missing the write still goes ahead under a placeholder reviewer name and email.

> **Enforcement:** `src/server/server.js` calls `server.auth.default` with the `session`
> strategy in `required` mode before the router registers any route, so every route needs a
> valid session unless it sets `auth: false`. Only `/`, `/health`, `/favicon.ico`, the static
> asset path and the three `/auth/*` routes do. The strategy accepts any session that carries a
> user, so there is **no authorisation**: no group or role claim is checked.
>
> **Local development bypass:** when `SSO_ENABLED` is false the cookie strategy is replaced by
> one that authenticates every request as a stub user (`DEV_USER_ID`, `DEV_USER_EMAIL`,
> `DEV_USER_NAME`). It defaults to on, the `dev` npm scripts and the test configuration turn it
> off, and nothing in the code stops it being turned off in a deployed environment. See
> Section 11.

## 4. API Surface

100 routes (61 `GET`, 39 `POST`) on 63 paths. Every route needs a signed-in session except
those marked **public**. All pages are HTML and English-only. Every module that takes a path
parameter validates it (a short identifier of letters, digits and hyphens), and the `POST`
routes validate their payloads with Joi, with the exception of the register search form.
State-changing `POST` routes redirect on success; a `POST` that the backend refuses because
checks are outstanding (`409`) redirects to the relevant incomplete-review page.

**Sign-in and platform**

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/` | Landing page (an empty placeholder) — **public** | — | HTML |
| `GET` | `/about` | About page (an empty placeholder) | — | HTML |
| `GET` | `/auth/login` | Begin Entra ID sign-in — **public** | — | Redirect to Microsoft |
| `GET` | `/auth/callback` | Entra ID authorisation code return — **public** | `code`, `state` (query) | Cookie set, redirect to the remembered page or `/` |
| `GET` | `/auth/logout` | Sign out — **public** | — | Redirect to Microsoft logout |
| `GET` | `/health` | Liveness probe — **public** | — | `{ message }` |
| `GET` | `/favicon.ico`, `{ASSET_PATH}/{param*}` | Static assets — **public** | — | Files |

**Dashboard, applications and close-out**

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/manage-certification` | Dashboard: new, in-progress and total counts for appliances and fuels | — | HTML |
| `GET` | `/appliance-applications` | Appliance applications, not started and in progress | — | HTML |
| `GET` | `/fuel-applications` | Fuel applications, not started and in progress | — | HTML |
| `GET` | `/review-appliance-application/{applicationId}` | One appliance application with its appliances and their review status | `applicationId` | HTML |
| `POST` | `/review-appliance-application/{applicationId}/start` | Start the review (marks the application in progress) | Reviewer from session | Redirect |
| `GET` | `/review-fuel-application/{applicationId}` | One fuel application with applicant and fuels | `applicationId` | HTML |
| `POST` | `/review-fuel-application/{applicationId}/start` | Start the review | Reviewer from session | Redirect |
| `GET` | `/finish-application-review/{applicationId}` | Appliance application with items grouped as accepted and rejected | `applicationId` | HTML |
| `POST` | `/finish-application-review/{applicationId}` | Mark the application complete | Reviewer from session | Redirect |
| `GET` | `/application-review-complete/{applicationId}` | Completion confirmation | `applicationId` | HTML |
| `GET` | `/incomplete-application-review/{applicationId}` | Items still outstanding on the application | `applicationId` | HTML |

**Appliance review** (`GET` shows the screen, `POST` saves it and redirects back to the checklist)

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET`, `POST` | `/review-appliance/{applianceId}` | Review checklist; record the decision | `decision`: accept or reject | HTML; redirect to the application |
| `GET` | `/review-appliance/{applianceId}/incomplete-review` | Checks blocking acceptance | — | HTML |
| `GET`, `POST` | `/review-appliance/{applianceId}/test-reports` | Review test reports | Rated output, tested output and smoke emission output, pass or fail | HTML; redirect |
| `GET`, `POST` | `/review-appliance/{applianceId}/technical-drawings` | Technical drawings check | Pass or fail | HTML; redirect |
| `GET`, `POST` | `/review-appliance/{applianceId}/conformity-mark` | Conformity mark check | Pass or fail | HTML; redirect |
| `GET`, `POST` | `/review-appliance/{applianceId}/instruction-manual` | Instruction manual check | Title, optional version, publication date, pass or fail | HTML; redirect |
| `GET`, `POST` | `/review-appliance/{applianceId}/appliance-details` | Check appliance details summary and mark it completed | — | HTML; redirect |
| `GET`, `POST` | `/review-appliance/{applianceId}/permitted-fuels` | Permitted fuels and whether wood is permitted | Fuel text, wood answer | HTML; redirect |
| `GET`, `POST` | `/review-appliance/{applianceId}/additional-conditions` | Enter additional conditions | Conditions text | HTML; redirect |
| `GET`, `POST` | `/review-appliance/{applianceId}/model-name` | Change the model name | Model name | HTML; redirect |
| `GET`, `POST` | `/review-appliance/{applianceId}/model-number` | Change the model number | Model number | HTML; redirect |
| `GET`, `POST` | `/review-appliance/{applianceId}/appliance-type` | Change the appliance type | Type choice | HTML; redirect |
| `GET`, `POST` | `/review-appliance/{applianceId}/other-appliance-type` | Choose the "other" appliance type | Type choice | HTML; redirect |
| `GET`, `POST` | `/review-appliance/{applianceId}/variant-appliance` | Is it a variant, and of which appliance | Yes or no, details | HTML; redirect |
| `GET`, `POST` | `/review-appliance/{applianceId}/nominal-output` | Change the nominal thermal output | kW value | HTML; redirect |
| `GET`, `POST` | `/review-appliance/{applianceId}/multifuel-appliance` | Is it a multifuel appliance (expected to fail on save, see Section 11) | Yes or no | HTML; redirect |

**Fuel review** (same pattern)

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET`, `POST` | `/review-fuel/{fuelId}` | Review checklist, which depends on supplier type; record the decision | `decision`: accept or reject | HTML; redirect to the application |
| `GET` | `/review-fuel/{fuelId}/incomplete-review` | Checks blocking acceptance | — | HTML |
| `GET`, `POST` | `/review-fuel/{fuelId}/test-results` | Add test results (manufacturers) | Smoke emission, sulphur content, pass or fail | HTML; redirect |
| `GET`, `POST` | `/review-fuel/{fuelId}/manufacturer-letter` | Review the letter from the original manufacturer (rebrands) | Pass or fail | HTML; redirect |
| `GET`, `POST` | `/review-fuel/{fuelId}/fuel-details` | Check fuel details summary and mark it completed | — | HTML; redirect |
| `GET`, `POST` | `/review-fuel/{fuelId}/fuel-description` | Check the fuel description (appearance, weight, composition, sulphur content, manufacturing process, each with a change link) and mark it completed (rebrands) | — | HTML; redirect |
| `GET`, `POST` | `/review-fuel/{fuelId}/brand-name`, `/rebrand-name` | Change the brand name, or the rebranded name | Name | HTML; redirect |
| `GET`, `POST` | `/review-fuel/{fuelId}/additional-brand-names`, `/additional-rebrand-names` | Additional brand names, or rebrand names | Comma-separated names | HTML; redirect |
| `GET`, `POST` | `/review-fuel/{fuelId}/original-manufacturer` | Original fuel manufacturer | Name | HTML; redirect |
| `GET`, `POST` | `/review-fuel/{fuelId}/original-brand` | Original fuel name or brand | Name | HTML; redirect |
| `GET`, `POST` | `/review-fuel/{fuelId}/fuel-changes` | Was the original fuel changed or mixed, and how | Yes or no, explanation | HTML; redirect |
| `GET`, `POST` | `/review-fuel/{fuelId}/fuel-appearance` | Fuel appearance | Text | HTML; redirect |
| `GET`, `POST` | `/review-fuel/{fuelId}/fuel-weight` | Fuel weight | Text | HTML; redirect |
| `GET`, `POST` | `/review-fuel/{fuelId}/fuel-composition` | Fuel composition | Text | HTML; redirect |
| `GET`, `POST` | `/review-fuel/{fuelId}/sulphur-content` | Sulphur content (%) | Number | HTML; redirect |
| `GET`, `POST` | `/review-fuel/{fuelId}/manufacturing-process` | Manufacturing process | Text | HTML; redirect |
| `GET`, `POST` | `/review-fuel/{fuelId}/quality-control` | Is a monitored quality control system in place | Yes or no | HTML; redirect |

**Appliance register and records**

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET`, `POST` | `/appliance-records` | Search and filter the appliance register (completed applications and legacy records), 10 per page | `keywords`, `filters` (pending, live, hidden, rejected), `page` | HTML |
| `GET` | `/appliance-record/{applianceId}` | One record: status, certification by country, public listing state, links | `applianceId` | HTML |
| `GET` | `/appliance-record/{applianceId}/appliance-details` | Appliance details (live or legacy) | — | HTML |
| `GET` | `/appliance-record/{applianceId}/application-details` | The application the appliance came from | — | HTML |
| `GET` | `/appliance-record/{applianceId}/instruction-manual` | Instruction manual details | — | HTML |
| `GET` | `/appliance-record/{applianceId}/test-reports` | Test results | — | HTML |
| `GET` | `/appliance-record/{applianceId}/legacy-comments` | Comments carried over from the legacy register | — | HTML |
| `GET` | `/appliance-record/{applianceId}/action-history` | Paged action history, newest first | `page` | HTML |
| `GET`, `POST` | `/appliance-record/{applianceId}/approval-status-{country}` | Set or change certification in one country (`england`, `scotland`, `wales`, `northern-ireland`) | `decision` | HTML; redirect to the record |
| `GET`, `POST` | `/appliance-record/{applianceId}/change-display-status` | Hide from, or make live on, the public list | `isVisibleToPublic` | HTML; redirect to the record |

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| Microsoft Entra ID | External API | `{AZURE_AUTHORITY_HOST}/{AZURE_TENANT_ID}` authorisation code flow (browser redirect to authorise, server-side token exchange through MSAL) and `oauth2/v2.0/logout` | Authorisation code and state out, identity claims back (home account id, username, display name) | OIDC confidential client — `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` |
| `aqie-dc-backend` | AQIE service | `GET /applications/counts` | Case counts by status for appliances and fuels | `x-api-key` header from `CDP_X_API_KEY` |
| `aqie-dc-backend` | AQIE service | `GET /applications/summary-by-status?type=appliance` or `fuel` | Applications not started and in progress, with item names | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `GET /applications/{id}/summary?type=appliance` or `fuel` | Items in one application with their review status | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `GET /applications/{id}` (optionally `?groupBy=techReviewStatus`) | One application; with `groupBy`, items split into accepted and rejected | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `GET /appliances/{id}` | Full appliance record | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `GET /appliances/{id}/technical-review` | Appliance review state and outstanding checks | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `GET /fuels/{id}/technical-review` | Fuel review state, supplier type and outstanding checks | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `GET /appliance-types?isPrimary=true` or `false` | Appliance type lists | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `GET /admin/appliances/search` | Keyword, status filter and page in; appliance register page out | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `GET /admin/appliances/{id}` | Admin view of one appliance: statuses, certification by country, manual, test reports, legacy comments | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `GET /api/admin/appliances/{id}/action-history?page=` | One page of action history | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `PATCH /applications/{id}/in-progress` | Reviewer name and email out; application marked in progress | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `PATCH /applications/{id}/complete` | Reviewer name and email out; updated application back | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `PATCH /appliances/{id}` | Edited appliance fields (type, other type, model name, model number, nominal output, variant, multifuel) | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `PATCH /appliances/{id}/technical-review` | Decision (`accepted` or `rejected`) and reviewer identity | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `PATCH /appliances/{id}/technical-review/checks` | Check name, result and, for some checks, the entered data (permitted fuels, additional conditions, test reports, instruction manual) | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `PATCH /appliances/{id}/certification/{country}` | `certified` or `uncertified` and the deciding user | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `PATCH /appliances/{id}/visibility` | Show or hide on the public list and the acting user | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `PATCH /fuels/{id}` | Edited fuel fields (brand names, original fuel, description, manufacturing process, quality control) | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `PATCH /fuels/{id}/technical-review` | Decision and reviewer identity | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `PATCH /fuels/{id}/technical-review/checks` | Check name, result and, for test results, the measurements | `x-api-key` header |
| Redis | Datastore | `catbox-redis` session cache (in-memory outside production) | Session state | `REDIS_USERNAME` / `REDIS_PASSWORD` |

All calls go through one client that uses only `GET` and `PATCH`. `aqie-dc-backend` does not
read or check the `x-api-key` header, so the signed-in reviewer's name and email in the request
body are the only identity the backend receives, and it trusts them.

Each of the 21 distinct backend method and path pairs above is registered in `aqie-dc-backend`
at its commit `49f950cd`; none is missing. One payload mismatch is known: the multifuel change
page sends the key `multifuelAppliance`, but the backend field is `isMultifuelAppliance` and its
`PATCH /appliances/{id}` route rejects unknown keys, so saving that page is expected to fail
(Section 11). The appliance register keyword search also sends free text to a backend that
accepts at most 50 characters of letters, digits, spaces and `- _ . & '`; anything else comes
back as a `400` and shows a generic error page.

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| DEFRA caseworkers | All routes (the landing page, health check, static assets and `/auth/*` routes are reachable without signing in) | Certification case management and appliance register administration |

No AQIE service calls this frontend.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).
> The 21 backend method and path pairs in Section 5 are what the code actually calls. Backend
> endpoints this service does not call, such as `GET /applications/search` and
> `POST /admin/import/initiate`, have no call site here.

## 7. Data

- **Stores:** Redis only, for the `@hapi/yar` session cache. No database. `yar` is left on its
  default cookie size threshold, so small sessions travel in the encrypted session cookie and
  the Redis-backed cache (in-memory outside production) takes larger ones. The `auth` cookie
  is stateless and not stored in Redis.
- **Key entities:** none owned. The signed-in user (home account id, username, display name)
  is held in the encrypted `auth` cookie for the duration of the sign-in and is written
  through to the backend as the `reviewedBy` (or `decidedBy`) name and email on decisions.
  The sign-in state and nonce, and the page to return to after sign-in, are held briefly in
  the session.
- **Retention / refresh:** session TTL is `SESSION_CACHE_TTL`; the auth cookie lifetime is
  `SESSION_COOKIE_TTL` (four hours by default) and is extended on each authenticated request,
  with no absolute limit. It is cleared on logout. Every screen reads current state from the
  backend on each request — nothing about a case is cached.

## 8. Configuration

Environment variable names only — never values. `AZURE_CLIENT_SECRET`, `SESSION_COOKIE_PASSWORD`,
`REDIS_PASSWORD` and `CDP_X_API_KEY` are secrets held in CDP and are never recorded here.
`SESSION_COOKIE_PASSWORD` also has a placeholder default in `src/config/config.js`, so an
environment that forgets to set it still starts (see Section 11).

| Variable | Purpose |
|---|---|
| `PORT`, `HOST` | HTTP listener |
| `NODE_ENV`, `SERVICE_VERSION` | Runtime identity |
| `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_REDIRECT_URI` | Entra ID application registration and reply URL (the `GET /auth/callback` address) |
| `AZURE_AUTHORITY_HOST` | Entra authority host, defaulting to the Microsoft public cloud sign-in host |
| `AZURE_POST_LOGOUT_REDIRECT_URI` | Defined but not read anywhere in `src/` |
| `SSO_ENABLED` | Turns Entra sign-in on (the default). Set to false for local development, when every request is authenticated as a stub user |
| `DEV_USER_ID`, `DEV_USER_EMAIL`, `DEV_USER_NAME` | The stub user, read only when `SSO_ENABLED` is false |
| `BACKEND_URL` | Base URL of `aqie-dc-backend` |
| `CDP_X_API_KEY` | API key sent to the backend on every request |
| `REDIS_HOST`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_KEY_PREFIX`, `REDIS_TLS` | Redis session store |
| `SESSION_CACHE_ENGINE`, `SESSION_CACHE_NAME`, `SESSION_CACHE_TTL`, `USE_SINGLE_INSTANCE_CACHE` | Session cache behaviour |
| `SESSION_COOKIE_PASSWORD`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_TTL` | Encryption, secure flag and lifetime of the auth and session cookies |
| `ASSET_PATH`, `STATIC_CACHE_TIMEOUT` | Static asset serving |
| `HTTP_PROXY` | CDP egress proxy |
| `ENABLE_SECURE_CONTEXT` | TLS trust store |
| `TRACING_HEADER` | CDP request tracing header name |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`
  (parent image `3.2.4-node24.22.1`); production entrypoint `node src`, with the webpack
  frontend bundle built beforehand and `npm ci --omit=dev` so development dependencies are not
  in the image. `curl` is added for the platform health check. Default port 3000.
- **Internal address:** `https://aqie-dc-admin-frontend.<env>.cdp-int.defra.cloud` (CDP
  convention; not stated in this repository). This address followed by `/auth/callback` must
  also be registered as a reply URL on the Entra ID application registration for each
  environment, and set as `AZURE_REDIRECT_URI`.
- **Environments:** `dev`, `test`, `perf-test`, `prod` (CDP convention; the code itself only
  distinguishes production from non-production through `NODE_ENV`).
- **Local development:** `compose.yml` is the CDP template's (LocalStack, Redis and MongoDB,
  plus a placeholder frontend service); only Redis is relevant to this service. `npm run dev`
  and the tests run with `SSO_ENABLED=false`, so no Entra ID registration is needed locally.
- **Pipelines** (unchanged since the previous analysis):
  - `.github/workflows/check-pull-request.yml` — on pull requests to `main` and a weekly
    Monday schedule: frontend build, format check, lint, tests with coverage, `npm audit` at
    critical level, a Docker image build and the SonarCloud scan (skipped for Dependabot)
  - `.github/workflows/publish.yml` — on push to `main`: build, tests, publish with the CDP
    build action, then a SonarCloud scan that does not block the publish
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish with format check, lint and
    tests before publishing
  - The workflows take Node from `.nvmrc` (`v24.11.1`), which no longer matches the Node
    version in the container parent image (24.22.1).

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, ECS-formatted in production (`LOG_FORMAT`). Health-check
  requests are not logged. In production the request authorisation header, cookie header and
  response headers are removed from logs. Each backend call logs its URL at info level, and a
  failed call logs the status and the first 200 characters of the response body.
- **Tracing:** `@defra/hapi-tracing` propagating `TRACING_HEADER`.
- **Metrics:** `@defra/cdp-metrics`.
- **Security headers:** HSTS with a one-year max age and subdomains, XSS protection, no-sniff
  and frame protection, plus a content security policy via `blankie` (with `@hapi/scooter`):
  scripts from the service itself plus one hashed GOV.UK Frontend snippet, no framing of the
  service by other sites, no objects, forms may only post back to the service.
- **Shutdown:** `hapi-pulse` for graceful draining (ten-second timeout).
- **MSAL logging:** PII logging is explicitly disabled in the MSAL logger options, and MSAL
  messages now go through the structured logger at debug level. No `console` logging remains
  in the service.
- **Audit:** `@defra/cdp-auditing` is declared in `package.json` but not used.

## 11. Open Questions

Sign-in is now enforced in code on every route except the landing page, health check, static
assets and `/auth/*` (the earlier finding that authentication was configured but never applied
is fixed). The questions below are what remains.

- [ ] **Is sign-in really on in every deployed environment?** (catalogue `oq-020`) Setting `SSO_ENABLED=false`
      authenticates every request as a stub user, and nothing in `src/server/server.js` stops
      that in production. Separately, `SESSION_COOKIE_PASSWORD` has a placeholder default, so
      an environment that forgets to set it still starts and its cookies could be forged by
      anyone who knows the placeholder. Deployed values are held in deployment configuration
      outside this repository. Confirm both are correct in dev, test, perf-test and prod
      (and that `AZURE_REDIRECT_URI` matches a registered reply URL in each), then consider
      failing start-up when SSO is off under `NODE_ENV=production` and removing the default
      password.
- [ ] **No authorisation.** (catalogue `oq-021`) Entra ID group or role claims are not requested or checked, so any
      account that can sign in is treated as a caseworker. Confirm the intended access model:
      is "assignment required" set on the Entra enterprise application, or should the service
      check a group or app role?
- [ ] **Does anything validate the `x-api-key` this service sends?** (catalogue `oq-022`) `aqie-dc-backend` never
      reads it and has no auth strategy. If no gateway checks it, every `PATCH` route
      (decisions, certification, visibility) is open to any caller that can reach the backend.
- [ ] **Reviewer identity.** The backend now requires `reviewedBy` or `decidedBy` in the body
      and trusts it. If the session lacks a name or email this service still writes, under a
      placeholder reviewer. Field edits and individual check results carry no identity at all.
      Confirm whether the backend should verify identity itself, whether writes should be
      refused when identity is incomplete, and whether edits need attribution in the action
      history.
- [ ] **Multifuel change page.** (catalogue `oq-023`) It reads and saves `multifuelAppliance`, but the backend field
      is `isMultifuelAppliance` and the backend rejects unknown keys, so saving it is expected
      to fail and the check-appliance-details summary will show the answer as "Not provided".
      Confirm and fix.
- [ ] **Fuel journey is incomplete.** There is no fuel application close-out: the "Continue"
      button on the fuel application page points at `/incomplete-application-review` with no
      application id, which is not a route. The dashboard "Fuel records" link is a placeholder.
      Confirm what is planned.
- [ ] **No start page, navigation or sign-out.** `/` and `/about` are unchanged template
      placeholders with empty bodies, the layout renders no service navigation, and nothing
      links to `/auth/logout` (and `AZURE_POST_LOGOUT_REDIRECT_URI` is never read). After
      sign-in with no remembered page, staff land on an empty page. Confirm whether a start
      page and a sign-out link are planned.
- [ ] **Register search input.** The keyword is passed straight to a backend that accepts only
      50 characters of letters, digits, spaces and `- _ . & '`. Any other input returns a `400`
      and a generic error page. Confirm whether the frontend should validate and explain.
- [ ] **Unescaped model names.** The appliance register list builds HTML from the supplier's
      model name without escaping it (newer modules escape). The content security policy blocks
      inline script, but the list should still escape. Confirm this will be fixed.
- [ ] (catalogue `oq-025`) The backend's bulk import endpoints are unused here. Confirm whether an admin import
      screen is planned, or whether imports are triggered from outside the service.
- [ ] `repository-catalog.yaml` classifies this service under the `Citizen` domain, but it is
      an internal staff tool with no citizen users. Confirm whether the domain should change
      to `Shared` or an internal-facing equivalent.

