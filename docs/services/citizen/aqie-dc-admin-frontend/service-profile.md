# aqie-dc-admin-frontend

> The internal caseworker interface for smoke control certification. DEFRA staff sign in with
> Microsoft Entra ID, work through the technical review of each appliance in an application,
> and close the case once every item has been decided.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-dc-admin-frontend`](https://github.com/DEFRA/aqie-dc-admin-frontend) |
| Service domain | `Citizen` (see Section 11 — this is an internal service) |
| Service type | `Auxilary Frontend` |
| Lifecycle stage | `Beta` |
| Primary language | JavaScript |
| Runtime | Node.js `>=24` (ES modules), pinned to `v24.11.1` in `.nvmrc` |
| Default branch | `main` |
| Created (UTC) | `2026-02-03` |
| Last main commit (UTC) | `2026-09-15T08:44:45Z` |
| Last analysed commit | `2c66e099` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Does:**

- Authenticates DEFRA staff against Microsoft Entra ID using the MSAL confidential client
  OpenID Connect authorisation code flow, and holds the resulting session in an encrypted
  cookie.
- Presents a certification management dashboard showing case counts by status.
- Lists appliance applications awaiting or under review, with a per-case summary of the items
  inside each one.
- Drives the **technical review of a single appliance**, screen by screen:
  - *Technical drawings* — pass or fail the drawings check.
  - *Conformity mark* — pass or fail the conformity mark check.
  - *Permitted fuels* — confirm the fuels the appliance may burn and whether wood is
    permitted, recording the field values and the check result in one backend call.
  - *Review appliance* — record the overall item decision as started, accepted or rejected.
- Shows an incomplete-review page when a caseworker tries to accept an item that still has
  outstanding checks.
- Drives the **application-level close-out**: shows the application with its items grouped
  into accepted and rejected, then marks the whole application complete, stamping the case
  with the signed-in reviewer's name and email.
- Shows a confirmation page once the application review is complete.

**Does not:**

- Hold any data. Every read and write goes to `aqie-dc-backend`; this service stores only
  session state.
- Serve the public. The published register is `aqie-dc-frontend`, which is unauthenticated,
  read-only and bilingual. This service is English-only, authenticated, and is the only one of
  the pair that writes.
- Accept applications from manufacturers. Applications arrive at `aqie-dc-backend` from the
  DEFRA Forms service over a queue; caseworkers never key one in.
- Perform bulk register imports. `aqie-dc-backend` exposes `POST /admin/import/initiate` and
  `GET /admin/import/status`, but no screen in this repository calls them — imports are
  currently driven by backend operator scripts.
- Review fuel applications. Every review screen here is appliance-specific; the fuel review
  journey does not yet exist.
- Manage users, roles or permissions. Entra ID group membership is not read or checked.

## 3. Architecture

**Pattern:** Hapi server-rendered GOV.UK Frontend application. Each caseworker screen is a
self-contained folder holding its route definition, controller and a small `*-data.js` module
that is the only place that talks to the backend, so the backend contract for a screen is
visible in one file.

| Component | Path | Responsibility |
|---|---|---|
| Server composition | `src/server/server.js` | Registers the cookie auth strategy, session cache, CSP, metrics and the router |
| Router | `src/server/router.js` | Registers every screen plugin plus health and static assets |
| Entra ID plugin | `src/server/plugins/azure-auth.js` | `/auth/login`, `/auth/callback` and `/auth/logout` routes |
| MSAL configuration | `src/config/azure-auth.js` | Lazily constructs the MSAL confidential client from tenant, client id and secret |
| Backend client | `src/server/common/api/api.js` | `fetchJson` and `patchJson` with shared headers and error handling |
| Dashboard | `src/server/manage-certification/` | Case counts |
| Application list | `src/server/appliance-applications/` | Applications with item summaries |
| Application review | `src/server/review-appliance-application/` | One application with its appliance summary |
| Appliance review | `src/server/review-appliance/` | Item decision and the incomplete-review page |
| Check screens | `src/server/technical-drawings/`, `src/server/conformity-mark/`, `src/server/check-permitted-fuels/` | Individual documentation and listing checks |
| Close-out | `src/server/finish-application-review/`, `src/server/application-review-complete/`, `src/server/incomplete-application-review/` | Completing the case and confirming the outcome |
| Session cache | `src/server/common/helpers/session-cache/` | `@hapi/yar` over Redis or memory |
| Config | `src/config/config.js` | `convict` schema |

### Authentication flow

1. A caseworker requests `GET /auth/login`. The service asks MSAL for an authorisation code
   URL scoped to `openid`, `profile` and `email`, with `response_mode=form_post`, and redirects
   the browser to `https://login.microsoftonline.com/{tenantId}`.
2. Entra ID authenticates the user and form-posts the authorisation code back to
   `POST /auth/callback` at `AZURE_REDIRECT_URI`.
3. The service exchanges the code for tokens using the confidential client, then stores the
   account's home account id, username and display name in the `yar` session and sets the
   `auth` cookie via the Hapi `cookie` strategy with `isAuthenticated` true.
4. The user is redirected onward into the service.
5. `GET /auth/logout` clears the cookie and the session and redirects to the Entra ID
   `oauth2/v2.0/logout` endpoint for the tenant.

The reviewer's name and email taken from this session are what get written to the backend as
`reviewedBy` when a decision is recorded.

> **Important:** the `session` cookie strategy is registered but is not applied — there is no
> `server.auth.default('session')` and no route sets `auth: 'session'`. On the current `main`,
> signing in is possible but is not required to reach any caseworker screen. See Section 11.

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/` | Landing page | — | HTML |
| `GET` | `/auth/login` | Begin Entra ID sign-in | — | Redirect to Microsoft |
| `POST` | `/auth/callback` | Entra ID authorisation code form post | `code` | Session established, redirect |
| `GET` | `/auth/logout` | Sign out | — | Redirect to Microsoft logout |
| `GET` | `/manage-certification` | Certification dashboard with case counts | — | HTML |
| `GET` | `/appliance-applications` | Applications awaiting review | — | HTML list |
| `GET` | `/review-appliance-application/{applicationId}` | One application and its appliances | `applicationId` | HTML |
| `GET` | `/review-appliance/{applianceId}` | Technical review checklist for one appliance | `applianceId` | HTML |
| `POST` | `/review-appliance/{applianceId}` | Record the item decision | Decision | Redirect |
| `GET` | `/review-appliance/{applianceId}/incomplete-review` | Outstanding checks blocking acceptance | `applianceId` | HTML |
| `GET` | `/review-appliance/{applianceId}/technical-drawings` | Technical drawings check | `applianceId` | HTML |
| `POST` | `/review-appliance/{applianceId}/technical-drawings` | Record the drawings result | Pass or fail | Redirect |
| `GET` | `/review-appliance/{applianceId}/conformity-mark` | Conformity mark check | `applianceId` | HTML |
| `POST` | `/review-appliance/{applianceId}/conformity-mark` | Record the conformity mark result | Pass or fail | Redirect |
| `GET` | `/review-appliance/{applianceId}/permitted-fuels` | Permitted fuels check | `applianceId` | HTML |
| `POST` | `/review-appliance/{applianceId}/permitted-fuels` | Record permitted fuels and whether wood is allowed | Fuel list, wood flag | Redirect |
| `GET` | `/finish-application-review/{applicationId}` | Application grouped into accepted and rejected items | `applicationId` | HTML |
| `POST` | `/finish-application-review/{applicationId}` | Mark the application complete | Reviewer identity | Redirect |
| `GET` | `/application-review-complete/{applicationId}` | Completion confirmation | `applicationId` | HTML |
| `GET` | `/incomplete-application-review/{applicationId}` | Items still outstanding on the application | `applicationId` | HTML |
| `GET` | `/about` | About the service | — | HTML |
| `GET` | `/health` | Liveness probe | — | Status payload |
| `GET` | `/favicon.ico`, static assets | Static assets | — | Files |

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| Microsoft Entra ID | External API | `https://login.microsoftonline.com/{tenantId}` authorisation code flow and `oauth2/v2.0/logout` | Authorisation code out, identity claims back | OIDC confidential client — `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` |
| `aqie-dc-backend` | AQIE service | `GET /applications/counts` | Case counts by status | `x-api-key` header from `CDP_X_API_KEY` |
| `aqie-dc-backend` | AQIE service | `GET /applications/summary` | Applications with item summaries | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `GET /applications/{id}/summary?type=appliance` | Appliance names and review statuses for one case | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `GET /applications/{id}?groupBy=techReviewStatus` | Application with items grouped accepted or rejected | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `PATCH /applications/{id}/complete` | Reviewer name and email out; updated application back | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `GET /appliances/{id}/technical-review` | Appliance review state and outstanding checks | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `PATCH /appliances/{id}/technical-review` | Item status (`in_review`, `accepted`, `rejected`) and reviewer identity | `x-api-key` header |
| `aqie-dc-backend` | AQIE service | `PATCH /appliances/{id}/technical-review/checks` | Check name, result and — for permitted fuels — the confirmed field values | `x-api-key` header |
| Redis | Datastore | `catbox-redis` session cache | Session and signed-in user details | `REDIS_USERNAME` / `REDIS_PASSWORD` |

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| DEFRA caseworkers | All routes | Certification case management |

No AQIE service calls this frontend.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).
> The catalogue currently lists `GET /applications/search` and `POST /admin/import/initiate`
> for this edge; neither is called from this repository. The eight endpoints in Section 5 are
> what the code actually uses.

## 7. Data

- **Stores:** Redis only, for `@hapi/yar` session state and the Hapi cookie cache. No database.
- **Key entities:** none owned. The signed-in user (home account id, username, display name)
  is held in session for the duration of the sign-in and is written through to the backend as
  the `reviewedBy` name and email on review decisions.
- **Retention / refresh:** session TTL is `SESSION_CACHE_TTL`; the auth cookie lifetime is
  `SESSION_COOKIE_TTL` and it is cleared on logout. Every screen reads current state from the
  backend on each request — nothing about a case is cached.

## 8. Configuration

Environment variable names only — never values. `AZURE_CLIENT_SECRET`, `SESSION_COOKIE_PASSWORD`
and `CDP_X_API_KEY` are secrets held in CDP and are never recorded here.

| Variable | Purpose |
|---|---|
| `PORT`, `HOST` | HTTP listener |
| `NODE_ENV`, `SERVICE_VERSION` | Runtime identity |
| `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_REDIRECT_URI` | Entra ID application registration and reply URL |
| `BACKEND_URL` | Base URL of `aqie-dc-backend` |
| `CDP_X_API_KEY` | API key sent to the backend on every request |
| `REDIS_HOST`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_KEY_PREFIX`, `REDIS_TLS` | Redis session store |
| `SESSION_CACHE_ENGINE`, `SESSION_CACHE_NAME`, `SESSION_CACHE_TTL`, `USE_SINGLE_INSTANCE_CACHE` | Session cache behaviour |
| `SESSION_COOKIE_PASSWORD`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_TTL` | Auth and session cookie |
| `ASSET_PATH`, `STATIC_CACHE_TIMEOUT` | Static asset serving |
| `HTTP_PROXY` | CDP egress proxy |
| `ENABLE_SECURE_CONTEXT` | TLS trust store |
| `TRACING_HEADER` | CDP request tracing header name |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`;
  production entrypoint `node src`, with the webpack frontend bundle built beforehand.
- **Internal address:** `https://aqie-dc-admin-frontend.<env>.cdp-int.defra.cloud`. This
  address must also be registered as a reply URL on the Entra ID application registration for
  each environment.
- **Environments:** `dev`, `test`, `perf-test`, `prod`.
- **Local development:** `compose.yml` provides Redis.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — lint, test and quality gate on PR, plus a
    scheduled run
  - `.github/workflows/publish.yml` — build and publish on push to `main`
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, ECS-formatted in production.
- **Tracing:** `@defra/hapi-tracing` propagating `TRACING_HEADER`.
- **Metrics:** `@defra/cdp-metrics`.
- **Security headers:** HSTS with a one-year max age and subdomains, XSS protection, no-sniff
  and frame protection, plus a content security policy via `@hapi/scooter`.
- **Shutdown:** `hapi-pulse` for graceful draining.
- **MSAL logging:** PII logging is explicitly disabled in the MSAL logger options; the
  callback writes to `console.log` rather than the structured logger.

## 11. Open Questions

- [ ] **No route requires authentication.** The `session` cookie strategy is registered in
      `src/server/server.js` but `server.auth.default` is never called and no route sets
      `auth: 'session'`. Every caseworker screen — including the `POST` routes that write
      review decisions — is reachable without signing in. This needs urgent owner
      confirmation, and correction if the only control today is network placement.
- [ ] **No authorisation.** Entra ID group or role claims are not requested or checked, so any
      user in the tenant who authenticates would be treated as a caseworker. Confirm the
      intended access model.
- [ ] `POST /auth/callback` redirects to `/home` on success, but the router registers the
      landing page at `/`. Confirm whether sign-in currently lands on a 404.
- [ ] The backend accepts the reviewer's name and email from the request payload. Confirm
      whether the backend should instead verify the caseworker identity independently, rather
      than trusting whatever this frontend sends.
- [ ] The MSAL logger callback writes messages with `console.log` at `Info` level, bypassing
      pino and its redaction rules. Confirm this can be routed through the structured logger.
- [ ] There is no fuel review journey, only appliances. Confirm whether fuel applications are
      reviewed elsewhere or the journey is still to be built.
- [ ] The backend's bulk import endpoints are unused here. Confirm whether an admin import
      screen is planned, or whether imports remain an operator-script activity.
- [ ] `repository-catalog.yaml` classifies this service under the `Citizen` domain, but it is
      an internal staff tool with no citizen users. Confirm whether the domain should change
      to `Shared` or an internal-facing equivalent.

