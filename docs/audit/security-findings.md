# Security Findings

Findings raised during the deep documentation analysis of the AQIE estate.

**Status: unreviewed.** These were identified by static reading of public `main` branches.
They have not been validated with service owners, and some may already be known,
mitigated or accepted.

## How to read this

- **No secret values are recorded anywhere in this repository.** Findings state the
  repository and file location only. Retrieve the value from the source repository if
  you need to assess or rotate it.
- Severity is an initial assessment for triage, not a formal rating.
- Every item needs owner confirmation before action.
- Findings 1 to 38 were raised on 2026-09-15. A review on 2026-11-19 re-checked the twelve
  repositories with new commits on `main`, marked earlier findings **Fixed** or changed in
  place, and added findings 39 onwards in [Review of 2026-11-19](#review-of-2026-11-19).
  Repositories with no new commits since the baseline were not re-analysed, so their
  findings stand as recorded.

## Priority 1 — credentials committed to public repositories

These repositories are public. Treat every value below as compromised and rotate it.

| # | Repository | Location | Finding |
|---|---|---|---|
| 1 | `aqie-alert-back-end-service` | `src/config.js` | Ricardo UK-AIR account email and password present as convict **defaults** |
| 2 | `aqie-privatebeta-test` | `test/helpers/config.js` | Working defaults for the holding-page password, an ephemeral forecast API key, Ricardo API credentials and AQSR alert API credentials |
| 3 | `aqie-data-privatebeta-perftest` | `scenarios/AQIE_GetAirPollutionData_v1..v5.jmx` | Recorded AWS pre-signed S3 URLs carrying `X-Amz-Security-Token` and `X-Amz-Credential` — temporary STS credentials for the historic data buckets |
| 4 | `aqie-dataselector-frontend` | `src/config/config.js` | **Fixed in source 2026-11-19** (the setting was deleted; the old value remains recoverable from git history, so keep treating it as compromised if it was ever reused). A real-looking literal password default (`AQIE_PASSWORD` key) |
| 5 | `aqie-docanalysisawspoc-frontend` | `src/config/config.js` | Shared prototype access password committed as a literal |
| 6 | `aqie-docanalysispoc-frontend` | Git history | The same password remains recoverable from public history; the HEAD commit is titled "remove password" |
| 7 | `aqie-publicbeta-test` | `test/helpers/config.js` | Committed default for the holding-page password |
| 8 | `aqie-prtr-journey-tests` | `test/specs/Phase1e2e.js`, `MigratedDataCheckE2E.js` | Holding-page password inlined as a string literal in five places |
| 9 | `aqie-privatebeta-api-perftest` | JMeter plans | Ricardo `login_check` password carried in the plan rather than injected |
| 10 | `AQIE-Citizen-Alpha` | `application-local*.properties` | Local H2 and PostgreSQL passwords committed (archived, never deployed) |

## Priority 1 — information governance

| # | Repository | Location | Finding |
|---|---|---|---|
| 11 | `aqie-docanalysisawspoc-frontend` | `docs/` | A **real DEFRA business document** (a Strategic Outline Case) committed to a public repository as a test fixture. Needs a publication clearance check and, if unpublished, removal from git history |
| 12 | `aqie-docanalysispoc-backend` | — | No record of an information governance assessment or DPIA for sending DEFRA business case text to Azure OpenAI and AWS Bedrock (catalogue `oq-011`) |
| 13 | `aqie-privatebeta-test` | `test/helpers/config.js` | A real UK mobile number and a real public webmail address used as a live alert test account |

## Priority 2 — access control

| # | Repository | Location | Finding |
|---|---|---|---|
| 14 | `aqie-dc-admin-frontend` | `src/server/server.js` | **Fixed in code 2026-11-19** (PR #19, merged 2026-09-28; residual risk in finding 39). Was: **authentication configured but never enforced.** The session cookie strategy was registered, but `server.auth.default` was never called and no route set `auth`, so every caseworker screen, including routes that write review decisions, was reachable unauthenticated |
| 15 | `aqie-dc-admin-frontend` | `src/config/azure-auth.js` | **Still present 2026-11-19.** No authorisation model. Only `openid`, `profile` and `email` are requested; no group or role claim is checked, and the session is accepted whenever it holds a user. Any account in the tenant that can sign in is treated as a caseworker, so access depends on the Entra app registration (not visible from the repository) |
| 16 | `aqie-dc-backend` | `src/config.js` | **Still present, broader 2026-11-19** (now 38 routes, including writes and deletes). `CDP_X_API_KEY` is sent by both frontends but never read by the backend. No Hapi auth strategy exists in the backend at all |
| 17 | `aqie-dc-backend` | `src/routes/upload-callback.js` | **Fixed by removal 2026-11-19** (route deleted by PR #123 on 2026-10-27; residual items in findings 43 and 52). `POST /upload-callback` was explicitly `auth: false`. Any in-network caller could trigger a register import by posting a crafted callback naming an arbitrary S3 bucket and key |
| 18 | `aqie-dc-backend` | technical review routes | **Still present, broader 2026-11-19.** Reviewer identity (`reviewedBy` or `decidedBy` name and email) is supplied in the request body and trusted, and is now written into the new action history as fact |
| 19 | `aqie-notify-service` | `GET /process-sms-replies` | Poller trigger has no authentication or rate limiting |
| 20 | `aqie-notify-service` | `POST /send-notification` | Accepts any template id and any recipient from any caller on the internal network |

## Priority 2 — transport and validation

| # | Repository | Location | Finding |
|---|---|---|---|
| 21 | `aqie-alert-back-end-service` | `src/users/utils/ricardoApiClient.js` | TLS verification disabled (`rejectUnauthorized: false`) whenever `NODE_ENV !== 'production'` |
| 22 | `aqie-dataselector-frontend` | `src/server/index.js` | **Still present 2026-11-19.** **CSRF validation effectively disabled.** The crumb `skip` predicate returns true for every POST except `/cookies`, so no journey form is token-validated. The new cross-origin `POST /station-summary` from `aqie-maps-frontend` now depends on the skip, so the fix is to narrow it to that route, not to leave all POSTs exempt |
| 23 | `aqie-dataselector-frontend` | `src/server/download_aurn/controller.js` | **Narrower than first recorded, not fixed (2026-11-19).** The JavaScript journey polls once per request every two seconds and gives up after three minutes. The unbounded one-second server-side polling loop with no attempt cap or timeout remains on the no-JavaScript routes (`/download_aurn_nojs/...`), and a `Failed` job is not treated as an end state, so a failed job holds the request open — resource exhaustion risk |
| 24 | `aqie-prtr-frontend` | `src/server/routes/download/download-proxy.js` | **Still present 2026-11-19.** Server-side fetch of a URL received from an upstream response (the backend's `downloadLink`, not user input); validates scheme only, with no host allow-list and no timeout |

## Priority 3 — weak defaults and disclosure

| # | Repository | Location | Finding |
|---|---|---|---|
| 25 | `aqie-front-end` | `src/config/schema-extra.js` | **Changed 2026-11-19: dead configuration.** The sign-in username and password settings (`src/config/schema-extra.js:381-394`) are read nowhere. `@hapi/cookie` is registered but no authentication strategy is defined, so no gate exists and the defaults protect nothing; delete the settings. Was: sign-in gate ships with a default username of `admin` and a placeholder default password |
| 26 | `aqie-front-end` | `src/config/schema-extra.js` | **Still present in code 2026-11-19; not enabled in production** (the mock one-time-code and mock setup-alert switches are true in the dev environment only and unset elsewhere, per CDP environment configuration). The default mock code is still committed (`src/config/schema-extra.js:75-80`) and the mock branches remain (`src/server/common/services/notify-backend.js:218-257,310-337`). Mock affordances including a hardcoded default mock OTP. If enabled in production these would bypass one-time-code verification on the alert journey |
| 27 | `aqie-front-end` | `src/server/test-routes/`, `src/server/notify/debug/` | **Still present, wider than first recorded 2026-11-19.** The test routes are registered unconditionally (`src/server/router.js:97`, `src/server/test-routes/index.js:14-36`) with no environment check; only `/test/client-log` refuses in production. Fixture pages for the DAQI bands, pollutant levels and mock alerts, a mock-pollutant route and `/results` are reachable by reading the code. The `/notify/debug/*` routes are properly gated (`src/server/notify/debug/clear-mock-storage.js:13-16`), and the file comments saying "dev/test only" are not enforced. Test-fixture and debug routes registered in the same router as production pages |
| 28 | `aqie-alert-back-end-service` | `src/config.js` | `RICARDO_API_USE_MOCK` defaults to `true`, pointing both alert feeds at public WireMock Cloud stubs |
| 29 | `aqie-laqm-data-explorer` | `app/lib/laqm-api.js` | The `/assessment` page renders a masked hint containing the last four characters of `LAQM_API_KEY` — partial secret disclosure |
| 30 | `aqie-dataselector-frontend` | `src/config/config.js` | **Fixed 2026-11-19** (the default was removed and the service now refuses to start without the variable; the repository's own remediation note records that rotating the value in every environment is still outstanding, and the old placeholder remains in git history). Shared placeholder cookie-signing secret as a committed default; failed open if the environment variable was unset |
| 31 | `aqie-dataselector-frontend` | `src/config/config.js` | **Still present 2026-11-19.** LAQM API key defaults equal the environment variable names, so an unset environment makes a live unauthenticated outbound call rather than failing fast |
| 32 | `aqie-privatebeta-perftest` | `scenarios/AQIE_..._DebugV2.jmx` | Replays recorded Google Analytics beacons containing a real measurement ID and client identifier |

## Priority 3 — supply chain and hygiene

| # | Repository | Location | Finding |
|---|---|---|---|
| 33 | `aqie-dc-backend` | `package.json` | **Fixed 2026-11-19** (`xlsx` removed; every lockfile entry now resolves from the npm registry). `xlsx` was installed from `https://cdn.sheetjs.com/...` rather than the npm registry, bypassing normal auditing |
| 34 | `aqie-dataselector-frontend` | `package.json` | **Fixed for the named packages 2026-11-19** (`@langchain/*`, `pdf2json`, `xlsx` and `@aws-sdk/*` removed; seven other declared packages are still never imported — see finding 68). Was: unused `@langchain/*`, `pdf2json`, `xlsx` and `@aws-sdk/*` dependencies — avoidable supply-chain surface |
| 35 | `aqie-dc-admin-frontend` | `src/config/azure-auth.js` | **Fixed 2026-11-19** (MSAL now logs through the pino logger with PII logging off). MSAL logged via `console.log` at `Info`, bypassing pino redaction |
| 36 | `aqie-dc-frontend` | `src/server/common/api/api.js` | `console.log` of full records, which contain applicant contact details |
| 37 | `aqie-prtr-backend` | `scripts/tsv-ingest/config.js` | **Still present 2026-11-19.** `TSV_DIR` defaults to a developer's local Windows user-profile path (a numeric profile folder, not a personal name), although the file header says no host-specific paths are baked in |
| 38 | `aqie-prtr-journey-tests` | `downloads/` | Approximately 200 MB of dataset XML committed in a non-gitignored directory |

## Review of 2026-11-19

Twelve repositories had new commits on `main` since the baseline, and two new repositories
appeared. Each was re-analysed at the commit named in its service profile. Earlier findings
are marked in place above. Headlines:

- **Fixed in code:** 14, 35 (`aqie-dc-admin-frontend` now enforces sign-in), 17, 33
  (`aqie-dc-backend`), 4, 30 and part of 34 (`aqie-dataselector-frontend`). Rotation of the
  old values is still outstanding where noted, because they remain in git history.
- **Still present:** 15, 16, 18, 22, 24, 26, 27, 31, 37. Findings 16 and 18 now cover a larger
  unauthenticated surface, and 27 is wider than first recorded. Finding 25 is now dead
  configuration, not a live gate.
- **New:** findings 39 to 81 below. The highest priorities are 71 (a possible live gateway
  key in a committed Postman collection, high until the owner confirms it has expired), 39 (a
  configuration switch that would silently disable sign-in), 46 (an API key written to logs,
  needs rotation after the logging is fixed), 41 (unauthenticated write routes on the smoke
  control register), 72 (any email address can be unsubscribed by anyone who knows it) and 47
  (a runtime past its end of support).
- **Not re-checked:** the 27 repositories with no new commits (two of them newly archived and
  one now private).
- Several new findings depend on deployed configuration that cannot be read from source.
  They are raised as open questions in the integration catalogue (`oq-020` to `oq-039`).

| # | Repository | Location | Finding |
|---|---|---|---|
| 39 | `aqie-dc-admin-frontend` | `src/server/server.js:91-110`, `src/config/config.js:256-282` | **High until deployed configuration is confirmed, then medium.** Setting `SSO_ENABLED=false` authenticates every request as a stub user with no sign-in. Nothing ties it to a non-production `NODE_ENV`; the only protection is the default of true and a start-up warning. It is the successor to finding 14: a configuration slip would silently reproduce it. Confirm the setting is true or unset in every deployed environment (`oq-020`) and make start-up fail if it is false in production |
| 40 | `aqie-dc-admin-frontend`, `aqie-front-end`, `aqie-prtr-frontend`, `aqie-prtr-submissions-frontend` | `src/config/config.js` (`SESSION_COOKIE_PASSWORD`); `src/config/index.js:335-356` in `aqie-front-end` | **Medium in `aqie-dc-admin-frontend`, low in the others.** The session cookie password has a committed placeholder default, the same pattern as finding 30 (now fixed in the dataselector). In `aqie-dc-admin-frontend` it encrypts the `auth` cookie, so anyone who knows the placeholder could forge a signed-in cookie if the variable is unset. In `aqie-front-end` the server also starts without error when it is unset, and a second setting, `COOKIE_PASSWORD`, has the same default and is read nowhere. Remove the defaults so start-up fails when unset, and confirm the variable is a secret in every environment. The CDP frontend template is the likely common source, so other template-derived frontends may share it (not checked) |
| 41 | `aqie-dc-backend` | `src/plugins/router.js:114-142`, `src/routes/appliances/create-appliance.js`, `src/routes/fuels/create-fuel.js` | **Medium.** Unauthenticated `DELETE /appliances/{id}`, `DELETE /fuels/{fuelId}`, `POST /appliances`, `POST /fuels` and general `PATCH` routes exist although neither frontend uses delete or create. Any in-network caller can remove register entries, and the create routes accept the status, visibility and country-certification fields that `PATCH` refuses, so an item can be created already live and appear on the public list. Extends finding 16. Remove the unused write routes; protect or restrict the rest |
| 42 | `aqie-dc-backend` | `src/controllers/appliances-controller.js:129-154`, `fuels-controller.js:120-145`, `applications-controller.js:178-270` | **Medium.** The by-id and list-all reads return whole stored documents: `GET /appliances/{id}` and `GET /fuels/{fuelId}` ignore item status and include applicant contact details, and `GET /applications` returns every application. The public lists are filtered to live items, but the by-id routes a public frontend would naturally move to are not (see `oq-006`). Add a public projection that excludes contact details and non-live items before the public frontend is repointed |
| 43 | `aqie-dc-backend` | `src/routes/admin-import.js:103-138`, `src/common/helpers/cdp-uploader.js:80-88` | **Medium.** `GET /admin/import/status` fetches whatever URL the caller supplies in `statusUrl` and returns the response; the only check is that it is a URI, with no allow-list of the uploader host. Any in-network caller can make the service request internal addresses (same pattern as finding 24). Restrict to the uploader host or remove the route, since the import flow no longer completes (`oq-025`) |
| 44 | `aqie-dc-backend` | `src/controllers/application-review-controller.js:53-61,97-123` | **Medium.** The email to the devolved administrations is a log-line stub, yet completing an application writes a "Sent to governments for approval" history entry and moves accepted items' countries to `awaiting_decision`. The audit trail asserts a notification that did not happen, and no administration is asked to decide (`oq-024`). Do not record the entry or the status change until a real send exists, or make the stub fail loudly |
| 45 | `aqie-back-end` | `src/api/metOfficeForecast/index.js:10-29` | **Medium.** `GET /sftp/files` and `GET /sftp/file/{filename}` have no authentication. Any caller on the CDP network can list the SFTP share and read any file in it using the service's SFTP key. No consumer is recorded for either route. Remove or protect them (the filename is matched against the directory listing, so path traversal is not possible) |
| 46 | `aqie-location-backend` | `src/api/common/helpers/catch-proxy-fetch-error.js:14-27`, `src/api/getosname/helper/fetch-data.js:22-24` | **Medium, act first.** The Ordnance Survey API key is a query parameter, and the helper that makes the call logs the complete URL, key included, at info level on every request and again on failure. Log redaction covers only headers, so the key sits in the platform's logs together with the user's search text. Log host and path only, move the key to a header if the API allows, and rotate the key once logging is fixed because the existing log history contains it |
| 47 | `aqie-historicaldata-backend` | `AqieHistoricaldataBackend.csproj:4`, `Dockerfile:2,15` | **Medium.** The service targets .NET 8 and builds and runs on the .NET 8 base images. Microsoft's published end-of-support date for .NET 8 is 10 November 2026, so the runtime no longer receives security patches. CI already builds with the .NET 10 SDK. Retarget the projects and both Docker base images |
| 48 | `aqie-historicaldata-backend` | `Atomfeed/Models/AtomHistoryModel.cs:226`, `Atomfeed/Services/AtomDataSelectionEmailJobService.cs:44,142,243` | **Medium (information governance).** The citizen's email address is stored in `aqie_csvemailexport_jobs` with no TTL or deletion and is written to the application log in clear text when an email job is processed and when Notify rejects it. Agree a retention period, add a TTL or sweep, mask the address in logs, and add the collection to the retention list below |
| 49 | `aqie-historicaldata-backend` | `Atomfeed/Endpoints/AtomHistoryEndpoints.cs:22-26`, `Atomfeed/Services/AtomDataSelectionNonAurnNetworks.cs:95-133`, `Example/Endpoints/ExampleEndpoints.cs:14-22` | **Medium.** No authentication or authorisation of any kind. `POST /AtomDataSelectionNonAurnNetworks` lets any in-network caller drop and rebuild the reference collections (leaving them empty while it runs); the CDP template's `example` module still exposes unauthenticated `POST`, `PUT` and `DELETE` on a MongoDB collection; and each call to the new region and agglomeration master endpoints logs in to Ricardo and downloads the full site list with no caching. Remove the `example` module, protect or remove the reload endpoint (start-up already seeds), and cache the site list |
| 50 | `aqie-maps-frontend` | `src/server/routes/api/monitoring-stations/index.js:16-20`, `src/server/common/helpers/aqie-back-end.js:7,37-43` | **Medium.** `GET /api/monitoring-station-info` is an unauthenticated, uncached pass-through to `aqie-back-end` `/monitoringStationInfo`, which makes 1 + 5N live Ricardo calls per request (120 second timeout). Nothing in the shipped interface uses it, so it is an amplification path with no benefit. Delete the route and helper, or add caching and rate limiting |
| 51 | `aqie-dataselector-frontend` | `src/server/data/en/homecontent.js:638-641`, `src/client/stylesheets/core/_daqi.scss:1-11` | **Medium (accessibility governance).** The published accessibility statement says the service complies with WCAG 2.2 AA and was last independently tested on 5 June 2025. Since then the station page gained DAQI, Last 24 hours and Last 7 days tabs, colour-coded DAQI tables and a map hand-off, and the repository itself records that the legally defined DAQI band colours fall short of the usual contrast standard for two bands. Re-test the new screens and list any known non-compliance in the statement |
| 52 | `aqie-dc-backend` | `src/common/helpers/cdp-uploader.js:30-50`, `callback-payload*.json` in the repository root | **Low.** Initiate still registers an `/upload-callback` URL that no longer exists, so uploads started through `POST /admin/import/initiate` are scanned and stored but never imported or cleaned up. Three sample callback payloads naming a bucket and object key remain in the repository root. Remove the registration or restore a handler, and delete the samples (`oq-025`) |
| 53 | `aqie-dc-backend` | `src/controllers/appliances-controller.js:246-250` | **Low.** `searchAdminAppliances` builds a regular expression from the `status` query value without escaping and passes `q` to `$regex`. The admin frontend sends only fixed statuses, but any other caller can send arbitrary text. Escape both values |
| 54 | `aqie-dc-admin-frontend` | `src/server/appliance-records/controller.js:58-68`, `src/server/review-appliance/controller.js:62-73` and six similar handlers, `src/server/server.js:70-110` | **Low.** Hardening gaps: the appliance register list builds HTML by string concatenation with supplier-supplied text unescaped; if the session lacks a name or email a decision is recorded against a placeholder reviewer instead of being refused; no CSRF token on any of the 39 POST routes (reliance on `SameSite=Lax`); no page links to sign-out and the four-hour cookie slides with no absolute limit; and content edits and per-check results carry no reviewer identity, so they cannot be attributed in the action history |
| 55 | `aqie-dataselector-frontend` | `src/server/verify/controller.js:136-161`, `src/server/verify/index.njk:21-31` | **Low.** The emailed-link route makes a server-side GET to whatever URL the backend returns, with no scheme or host check (same pattern as finding 24), then writes the URL unescaped into an inline script and a meta refresh. The URL is not user-supplied, so exploitation needs a compromised or confused backend. Validate `https` and an expected S3 host suffix, and escape for the script context |
| 56 | `aqie-dataselector-frontend` | `src/server/verify/controller.js:103-121` | **Low.** The "link expires after 48 hours" rule checks a timestamp taken from the URL path, which is not signed, so editing it bypasses the page-level expiry; the backend issues a fresh pre-signed URL with a seven-day expiry for any known job reference (`oq-034`). Sign the timestamp or check the job age in the backend |
| 57 | `aqie-dataselector-frontend` | `src/server/emailrequest/controller.js:305` | **Low (information governance).** The citizen's email address is stored in the session and never cleared, so it stays in Redis for up to the four-hour session lifetime. Clear it once the request is submitted and confirm the privacy notice covers the retention |
| 58 | `aqie-dataselector-frontend` | `src/server/common/helpers/navigation-helpers.js:11-17` | **Low.** Several routes return 404 unless the Referer header contains the request host. That is a substring check on a client-supplied header, so it is a navigation convenience, not an access control. Make sure nothing relies on it as one |
| 59 | `aqie-dataselector-frontend`, `aqie-historicaldata-backend` | `src/server/verify/controller.js:57,73`; `Atomfeed/Services/AWSS3BucketService.cs:115`, `AtomDataSelectionPresignedUrlMail.cs:102`, `AtomDataSelectionEmailJobService.cs:125,142` | **Low.** Pre-signed S3 download URLs (seven-day expiry; URLs issued under an assumed role also embed temporary credentials, compare finding 3) are written to application logs at info level, so anyone with log access can download the extract during that period. The data is open UK-AIR data, which keeps this low. Log the object key and expiry, never the URL |
| 60 | `aqie-historicaldata-backend` | `Atomfeed/Services/AWSPreSignedURLService.cs:25,30` | **Low.** When URL generation fails the method returns the literal text `error`, which callers treat as a URL, so a job can be marked Completed with a result URL of `error` and an email sent with a broken link. Return null and fail the job |
| 61 | `aqie-location-backend`, `aqie-monitoringstation-backend` | `src/api/getosname/helper/get-osplace-util.js:27,30`; `src/api/location/helpers/get-osplace-util.js:36-85` | **Low (information governance).** Whatever the citizen types, most often a home postcode, is written to the application logs at info level (in `aqie-location-backend` also inside the logged upstream URL, see finding 46). Stop logging the query text or hash it, and confirm log retention |
| 62 | `aqie-location-backend` | `src/api/index.js:49-56`, `src/config/index.js:59` | **Low.** No authentication, rate limit or cache in front of a key-protected, quota-limited upstream, so any internal caller can consume the Ordnance Survey allowance; and the API key setting defaults to the variable's own name, so an environment without it starts normally and sends an invalid key (compare finding 31). Add per-caller limiting or a short-lived cache and make the setting required in production |
| 63 | `aqie-monitoringstation-backend` | `src/api/common/helpers/catch-fetch-error.js:16`, `src/api/location/controllers/location.js:35,46,66-77` | **Low.** Since PR #51 the HTTP 400 body returns the raw error message, which for upstream failures contains the full internal upstream URL and status, so a frontend that relays it would disclose internal topology. The new `GET /monitoringstation/by-location` has no route validation or error handling and reads the whole `stations` collection into memory on every request. Return a fixed message and keep the detail in the log; add validation and limit the query |
| 64 | `aqie-back-end` | `src/api/metOfficeForecast/controllers/connectSftpViaProxy.js`, `src/config/index.js:266-290`, `src/api/locationsite/controller.js:51-55`, `src/helpers/mongodb.js:41-56` | **Low.** Hygiene. SFTP host names and the SFTP account name are hard-coded in a public repository (the private key is injected through a variable; values not reproduced here). SFTP and Ricardo payloads are logged at info level in volume. The four Ricardo URL defaults are the supplier's staging host: production overrides them per CDP environment configuration, but removing a variable would silently select staging (`oq-012`). `/monitoringStationInfo` fans out to Ricardo with a caller-controlled, unbounded `totalItems` and request state shared through a global. `historicalMeasurements` and `historicalForecasts` are insert-only with no TTL (`oq-019`) |
| 65 | `aqie-maps-frontend` | `src/client/javascripts/load-analytics.js:12-33`, `audit-ci.jsonc:6-12`, `package.json:39`, `src/server/plugins/serve-static-files.js:51-76` | **Low.** After a citizen accepts analytics cookies, the Consent Mode defaults set advertising, personalisation, functionality and security storage all to granted and a container whose content is outside the repository is loaded; the only allow-listed audit advisory expired on 2026-11-09, so the pull-request audit gate is not meaningful; and the production map depends on a pre-release package (`@defra/interactive-map` alpha) whose whole package directory is served publicly under `/map-assets` |
| 66 | `aqie-prtr-backend` | `src/services/reports-service.js:83,106-115`, `src/services/s3-service.js:64-94` | **Low (availability and cost).** Every download request runs a full bucket scan (a list plus one `HeadObject` per object) because the database shortcut reads a collection named `Reports` while the loader writes `reports`, and nothing writes the key field. The public route has no rate limit, so request volume multiplies into S3 calls. Fix or remove the shortcut and cache the key |
| 67 | `aqie-prtr-submissions-backend`, `aqie-prtr-submissions-frontend` | `src/routes/example.js:4-26` (backend); `src/server/common/helpers/is-safe-redirect.js:14-19` (frontend) | **Low now; higher once data is accepted.** Template `/example` routes are live and unauthenticated. The stated purpose is to take submitted pollutant release and transfer data from outside parties, but there is no authentication, authorisation, input handling or audit trail on `main` (`@defra/cdp-auditing` is declared by all four PRTR repositories and imported by none), and submitted data may include named contacts, so personal data rules apply. The open-redirect guard accepts a leading `/\`. Before any live submission agree the identity model, complete a DPIA or confirm none is needed, add service-specific privacy, cookies and accessibility pages, and wire audit events (`oq-032`) |
| 68 | `aqie-back-end` (14 packages, including a mistyped-install placeholder named `save-dev`), `aqie-dc-backend` (8), `aqie-dc-admin-frontend` (2), `aqie-monitoringstation-backend` (4), `aqie-dataselector-frontend` (7), `aqie-historicaldata-backend` (Hangfire, HtmlAgilityPack and a test-only library) | `package.json` and project files | **Low (supply chain).** Production dependencies are declared but never imported by non-test source (found by parsing imports, so dynamic loading would not show), several used only by unreachable code. Continues finding 34. Remove them |
| 69 | `aqie-monitoringstation-backend`, `aqie-location-backend` | `.github/workflows/publish.yml:42`; `check-pull-request.yml:40`, `publish.yml:27,42`, `publish-hotfix.yml:35` | **Low.** Workflows reference `SonarSource/sonarcloud-github-action@master` (in a job that also holds `id-token: write`, `contents: write` and the Sonar token) and `DEFRA/cdp-build-action/...@main` by moving branch rather than a pinned tag or commit. Pin to a version or commit SHA |
| 70 | `aqie-dataselector-frontend`, `aqie-dc-backend` | `jest.config.js`, `sonar-project.properties` | **Low (hygiene).** Ignore globs still name files from removed code (`src/server/cdp-uploader/`, `src/server/utils/xlsxParser.js`; `upload-callback.js`, `s3-download.js`). Harmless, but they are the last trace of removed features and invite their reintroduction. Delete them |

### Front end and demonstration prototype (findings 71 to 81)

These come from the review of `aqie-front-end` and `aqie-demo-data-visualisations`, which
finished after the others, so they are numbered after them and ordered by severity within
this group. No secret value or personal detail is recorded: credential-like literals and
personal data are reported by location only.

| # | Repository | Location | Finding |
|---|---|---|---|
| 71 | `aqie-front-end` | `src/server/notify/postman-collection-sms-alert-api.json` (collection variable `cdpXApiKey`; committed since 2026-01-21) | **High until the owner confirms it has expired.** A committed Postman collection holds a literal value against the variable `cdpXApiKey` that is not a placeholder. The repository's own `.env.example` says the CDP protected-gateway key expires after 24 hours, so it may already be dead, but treat it as exposed: confirm, revoke if live, and remove the file or blank the value (and clean history if required). The same file also names a protected-gateway address. No value is recorded here (`oq-037`) |
| 72 | `aqie-front-end`, `aqie-alert-back-end-service` | `src/server/notify/unsubscribe/unsubscribe-email-link/controller.js:54-100`, `.../index.js:13-34`; links built in `src/users/controllers/setupAlertController.js:102-103`, `src/users/utils/daqiAlertProcessor.js:332-335`, `forecastAlertProcessor.js:218-221`, `pollutantAlertProcessor.js:363-366` | **Medium.** Anyone who knows an email address can unsubscribe it. The link in every alert email carries the plain address (`?email=`) with no token or signature, and the front end keeps whatever address it is given in the session. The confirm click then calls the alert backend `DELETE /opt-out-email-alert`, which removes the whole subscriber record, every location (see Data retention). The address also sits in URLs, so it appears in request logs and browser history, and there is no CSRF protection (finding 78). A signed-token helper with expiry exists in the front end's `notify-util/` folder but nothing in `src/` imports it. Sign the links (HMAC and expiry) and verify the token on both the GET and the POST (`oq-038`) |
| 73 | `aqie-front-end` | `src/server/locations/helpers/get-os-places.js:93-109`, `src/server/common/helpers/catch-proxy-fetch-error.js:10-16,35-41` | **Medium.** The Ordnance Survey Names API key is carried in the request URL query string, and the shared proxy fetch helper logs the full URL at info level, so the key is written to application logs on every UK location lookup. The log redaction list covers only the authorisation and cookie request headers and the response headers (`src/config/index.js:197-203`). Same pattern as finding 46. Move the key out of the URL if the API allows it, strip query strings from logged URLs, and rotate the key if the log index is widely readable |
| 74 | `aqie-front-end` | `docs/postman/` (two collections), `src/server/notify/postman-collection-sms-alert-api.json:332` | **Medium (information governance).** Three committed Postman collections carry UK mobile numbers that are outside the Ofcom reserved drama range (two, one and one distinct numbers), so they may be real people's numbers used as live alert test accounts. The two `docs/postman` files also carry two corporate-domain email addresses each, and one file name carries an individual's first name. Same class as finding 13. Confirm whose they are and whether they consented, replace them with reserved numbers and `example.com` addresses, and consider history removal (`oq-037`) |
| 75 | `aqie-front-end` | `src/server/notify/register/email-confirm-link/controller.js:162-170` (also `:210-212`), `src/server/notify/unsubscribe/unsubscribe-email-link/controller.js:85-87` | **Medium (information governance).** Personal data in application logs. The full response from the notify `validate-link` call is logged at info level, and the code reads the email address, location and coordinates from it, so the address is written to the log; the setup-alert response is logged the same way (contents not verified). The unsubscribe handler logs the local part of the address and masks only the domain. Log booleans and identifiers, not payloads. The unused helpers in `notify-util/` include redaction functions |
| 76 | `aqie-demo-data-visualisations` | `.env.template:2` | **Medium.** A literal value is committed against `PASSWORD`, the Prototype Kit basic-authentication password, in a public repository. It was empty at the previous analysis; PR #15 restored a value that first appeared in the initial version of the file. The repository cannot say whether it is a placeholder or the deployed password. Treat it as exposed if it is the real one: rotate it and replace the template value with a blank (`oq-039`) |
| 77 | `aqie-front-end` | `.checkpoints/checkpoint-20250924T134422Z.tar.gz` (committed 2025-09-26, 97 MB) | **Low.** A snapshot of a developer's working directory is committed to the public repository. Its file listing shows `node_modules`, `.venv`, a complete `.git` directory with pack files, compiled server output and coverage output. No `.env` file is in the listing and the two small files checked inside it (`.npmrc` and `.git/config`) contain no token patterns, but the rest of the archive was not searched. Delete it from the repository (and from history if the embedded `.git` holds anything not already public) and ignore the folder |
| 78 | `aqie-front-end` | `src/server/index.js:29-61`, `package.json` | **Low.** No CSRF protection (no crumb plugin) and no Content-Security-Policy header set by the application, which sets only HSTS, XSS, no-sniff and frame options. The platform edge may add a policy, which the repository cannot show. Confirm, and add crumb to the POST forms (alert sign-up and unsubscribe). Compare findings 22 and 54 |
| 79 | `aqie-front-end` | `src/client/assets/javascripts/components/load-analytics.mjs:10-58` | **Low.** After a citizen accepts analytics cookies, consent mode is set to granted for advertising and personalisation storage as well as analytics, and two analytics measurement ids and two Tag Manager containers are loaded. Grant only analytics storage and confirm both containers are intended. Same pattern as finding 65 |
| 80 | `aqie-demo-data-visualisations` | `app/lib/ricardo-api.js:24-36,102-130` | **Low (governance).** Since PR #15 the prototype holds Ricardo account credentials itself and defaults to the production Ricardo host, in a public repository behind one shared basic-authentication password. Confirm that the account is dedicated and read-only and who owns it. The repository's own notes list credential management as the main risk (`oq-039`) |
| 81 | `aqie-demo-data-visualisations` | `app/views/index.html:13-62`, `app/lib/ricardo-api.js:368-397`, `app/lib/proxy.js:136-147` | **Low.** The landing page shows the upstream data-source origin, the outbound proxy address and upstream error text to anyone who passes basic authentication. Acceptable for a prototype; remove before any wider use |

## Data retention

No retention or deletion policy was found for collections holding citizen contact details:

- `aqie-notify-service` — `sms_replies`, `user-notification-details`, `user-contact-details`
- `aqie-alert-back-end-service` — `USERS`, `pollutant-alerts-audit`, `metoffice-forecast-audit`
- `aqie-dc-backend` — `SqsMessages` (holds applicant contact details indefinitely) and, added
  2026-11-19, `Actions` (reviewer names and emails in the audit trail)
- `aqie-historicaldata-backend` — `aqie_csvemailexport_jobs` (citizens' email addresses, finding
  48) and the generated extracts in S3 (no lifecycle rule in code)
- `aqie-dataselector-frontend` — the citizen's email address kept in the Redis session for up to
  four hours (finding 57)
- `aqie-front-end` — the in-progress alert sign-up, including the citizen's email address or
  mobile number, kept in the Redis session for up to four hours (the default session
  lifetime), and email addresses that can reach the application logs (finding 75)

The insert-only `historicalMeasurements` and `historicalForecasts` collections in
`aqie-back-end` also have no retention rule, but hold no personal data.

Separately, opting out of alerts deletes the entire `USERS` document, so unsubscribing
from one location removes all of a citizen's subscribed locations.

## Suggested next steps

1. Confirm which Priority 1 credentials are live, and rotate them. Add the CDP gateway key in
   the `aqie-front-end` Postman collection (finding 71), and check the committed contact
   details in the Postman collections (finding 74).
2. Get a clearance decision on the committed Strategic Outline Case PDF.
3. Confirm that `SSO_ENABLED` is true (or unset) and `SESSION_COOKIE_PASSWORD` is set from a
   secret in every deployed environment of `aqie-dc-admin-frontend` (findings 39 and 40).
   This replaces the earlier step about whether the admin interface was reachable, since
   finding 14 is fixed in code.
4. Fix the logging in `aqie-location-backend` and `aqie-front-end`, then rotate the Ordnance
   Survey API keys (findings 46 and 73).
5. Decide how `aqie-dc-backend` write routes will be authenticated, and confirm whether a
   gateway validates the `x-api-key` the frontends send (findings 16, 18, 41 and `oq-022`).
6. Sign the unsubscribe links in alert emails, or require a token on the receiving route
   (finding 72).
7. Move `aqie-historicaldata-backend` off .NET 8 (finding 47).
8. Agree a retention policy for the collections listed above.
9. Decide whether these findings should move to a tracked security backlog rather than
   living in a documentation repository. This repository is public, and the list now includes
   unfixed issues in running services, so the decision is more pressing than it was.
