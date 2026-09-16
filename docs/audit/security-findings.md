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

## Priority 1 — credentials committed to public repositories

These repositories are public. Treat every value below as compromised and rotate it.

| # | Repository | Location | Finding |
|---|---|---|---|
| 1 | `aqie-alert-back-end-service` | `src/config.js` | Ricardo UK-AIR account email and password present as convict **defaults** |
| 2 | `aqie-privatebeta-test` | `test/helpers/config.js` | Working defaults for the holding-page password, an ephemeral forecast API key, Ricardo API credentials and AQSR alert API credentials |
| 3 | `aqie-data-privatebeta-perftest` | `scenarios/AQIE_GetAirPollutionData_v1..v5.jmx` | Recorded AWS pre-signed S3 URLs carrying `X-Amz-Security-Token` and `X-Amz-Credential` — temporary STS credentials for the historic data buckets |
| 4 | `aqie-dataselector-frontend` | `src/config/config.js` | A real-looking literal password default (`AQIE_PASSWORD` key) |
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
| 14 | `aqie-dc-admin-frontend` | `src/server/server.js` | **Authentication is configured but never enforced.** The session cookie strategy is registered, but `server.auth.default` is never called and no route sets `auth`. Every caseworker screen, including routes that write review decisions, is reachable unauthenticated |
| 15 | `aqie-dc-admin-frontend` | `src/config/azure-auth.js` | No authorisation model. Only `openid`, `profile` and `email` are requested; no group or role claim is checked. Any tenant user who signs in is treated as a caseworker |
| 16 | `aqie-dc-backend` | `src/config.js` | `CDP_X_API_KEY` is sent by both frontends but never read by the backend. No Hapi auth strategy exists in the backend at all |
| 17 | `aqie-dc-backend` | `src/routes/upload-callback.js` | `POST /upload-callback` is explicitly `auth: false`. Any in-network caller can trigger a register import by posting a crafted callback naming an arbitrary S3 bucket and key |
| 18 | `aqie-dc-backend` | technical review routes | Reviewer identity (`reviewedBy` name and email) is supplied in the request body and trusted |
| 19 | `aqie-notify-service` | `GET /process-sms-replies` | Poller trigger has no authentication or rate limiting |
| 20 | `aqie-notify-service` | `POST /send-notification` | Accepts any template id and any recipient from any caller on the internal network |

## Priority 2 — transport and validation

| # | Repository | Location | Finding |
|---|---|---|---|
| 21 | `aqie-alert-back-end-service` | `src/users/utils/ricardoApiClient.js` | TLS verification disabled (`rejectUnauthorized: false`) whenever `NODE_ENV !== 'production'` |
| 22 | `aqie-dataselector-frontend` | `src/server/index.js` | **CSRF validation effectively disabled.** The crumb `skip` predicate returns true for every POST except `/cookies`, so no journey form is token-validated |
| 23 | `aqie-dataselector-frontend` | `src/server/download_aurn/controller.js` | Unbounded one-second job-status polling loop with no attempt cap or wall-clock timeout — resource exhaustion risk |
| 24 | `aqie-prtr-frontend` | `src/server/routes/download/download-proxy.js` | Server-side fetch of a URL received from an upstream response; validates scheme only, with no host allow-list |

## Priority 3 — weak defaults and disclosure

| # | Repository | Location | Finding |
|---|---|---|---|
| 25 | `aqie-front-end` | `src/config/schema-extra.js` | Sign-in gate ships with a default username of `admin` and a placeholder default password |
| 26 | `aqie-front-end` | `src/config/schema-extra.js` | Mock affordances including a hardcoded default mock OTP. If enabled in production these would bypass one-time-code verification on the alert journey |
| 27 | `aqie-front-end` | `src/server/test-routes/`, `src/server/notify/debug/` | Test-fixture and debug routes registered in the same router as production pages |
| 28 | `aqie-alert-back-end-service` | `src/config.js` | `RICARDO_API_USE_MOCK` defaults to `true`, pointing both alert feeds at public WireMock Cloud stubs |
| 29 | `aqie-laqm-data-explorer` | `app/lib/laqm-api.js` | The `/assessment` page renders a masked hint containing the last four characters of `LAQM_API_KEY` — partial secret disclosure |
| 30 | `aqie-dataselector-frontend` | `src/config/config.js` | Shared placeholder cookie-signing secret as a committed default; fails open if the environment variable is unset |
| 31 | `aqie-dataselector-frontend` | `src/config/config.js` | LAQM API key defaults equal the environment variable names, so an unset environment makes a live unauthenticated outbound call rather than failing fast |
| 32 | `aqie-privatebeta-perftest` | `scenarios/AQIE_..._DebugV2.jmx` | Replays recorded Google Analytics beacons containing a real measurement ID and client identifier |

## Priority 3 — supply chain and hygiene

| # | Repository | Location | Finding |
|---|---|---|---|
| 33 | `aqie-dc-backend` | `package.json` | `xlsx` installed from `https://cdn.sheetjs.com/...` rather than the npm registry, bypassing normal auditing |
| 34 | `aqie-dataselector-frontend` | `package.json` | Unused `@langchain/*`, `pdf2json`, `xlsx` and `@aws-sdk/*` dependencies — avoidable supply-chain surface |
| 35 | `aqie-dc-admin-frontend` | `src/config/azure-auth.js` | MSAL logs via `console.log` at `Info`, bypassing pino redaction |
| 36 | `aqie-dc-frontend` | `src/server/common/api/api.js` | `console.log` of full records, which contain applicant contact details |
| 37 | `aqie-prtr-backend` | `scripts/tsv-ingest/config.js` | `TSV_DIR` defaults to a named individual's local Windows path |
| 38 | `aqie-prtr-journey-tests` | `downloads/` | Approximately 200 MB of dataset XML committed in a non-gitignored directory |

## Data retention

No retention or deletion policy was found for collections holding citizen contact details:

- `aqie-notify-service` — `sms_replies`, `user-notification-details`, `user-contact-details`
- `aqie-alert-back-end-service` — `USERS`, `pollutant-alerts-audit`, `metoffice-forecast-audit`
- `aqie-dc-backend` — `SqsMessages` (holds applicant contact details indefinitely)

Separately, opting out of alerts deletes the entire `USERS` document, so unsubscribing
from one location removes all of a citizen's subscribed locations.

## Suggested next steps

1. Confirm which Priority 1 credentials are live, and rotate them.
2. Get a clearance decision on the committed Strategic Outline Case PDF.
3. Confirm whether `aqie-dc-admin-frontend` is currently deployed and reachable, given
   finding 14.
4. Agree a retention policy for the collections listed above.
5. Decide whether these findings should move to a tracked security backlog rather than
   living in a documentation repository.
