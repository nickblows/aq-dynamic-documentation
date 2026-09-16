# aqie-notify-service

> The messaging edge of the alerts estate. It is the only service that holds a GOV.UK Notify
> API key: it verifies a citizen's mobile number or email address before they subscribe, sends
> every SMS and email on behalf of `aqie-alert-back-end-service`, and processes inbound STOP
> replies.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-notify-service`](https://github.com/DEFRA/aqie-notify-service) |
| Service domain | `Data` |
| Service type | `Auxilary Backend Service` |
| Lifecycle stage | `Production` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22.16.0` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2025-09-16` |
| Last main commit (UTC) | `2026-05-28T08:59:17Z` |
| Last analysed commit | `1646e247` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Monitoring` |

## 2. Purpose and Responsibilities

**Does:**

- Owns the GOV.UK Notify relationship. It is the only AQIE alerts service that holds a Notify
  API key and the only one that calls the Notify API.
- Verifies mobile numbers: generates a five-digit one-time passcode, normalises the number to
  E.164, stores the code with a 15-minute single-use expiry, and sends it by SMS.
- Verifies email addresses: mints a UUID token with a 15-minute expiry, stores the pending
  subscription details against it, and emails a verification link pointing at `aqie-front-end`.
- Returns the verified subscription details (email, channel, location, coordinates) when the
  link is validated, so the front end can complete the subscription.
- Sends any message on request through `POST /send-notification` — the delivery path used by
  every alert that `aqie-alert-back-end-service` generates — and records the returned Notify
  notification id against the originating alert id.
- Polls GOV.UK Notify for inbound SMS replies on a timer, treats a message of `STOP` as an
  unsubscribe, calls the alert backend to remove the subscriber, sends a confirmation SMS, and
  records every reply so it is processed exactly once.

**Does not:**

- Own the subscriber record. Subscriptions live in the `USERS` collection of
  `aqie-alert-back-end-service`. This service only holds short-lived verification state,
  inbound SMS history and a notification audit.
- Decide when an alert is warranted. Threshold evaluation, region matching and deduplication
  are all done by `aqie-alert-back-end-service`.
- Create subscriptions. Verification succeeds here; the front end then posts to
  `POST /setup-alert` on the alert backend.
- Handle email unsubscribes. The unsubscribe link in an alert email points at
  `aqie-front-end`, which calls `DELETE /opt-out-email-alert` on the alert backend directly.
  Only the SMS STOP path passes through this service.
- Render any user interface, or store air quality data of any kind.

## 3. Architecture

**Pattern:** Hapi HTTP API with a single background poller. The poller is a `setInterval` job
registered as a Hapi plugin (not `node-cron`), cleared on server stop, and can be disabled
entirely by configuration.

| Component | Path | Responsibility |
|---|---|---|
| OTP routes and controller | `src/subscribe/routes/generate-otp.route.js`, `validate-otp.route.js`, `src/subscribe/controllers/otp.controller.js` | Mobile verification endpoints with Joi payload validation |
| OTP service | `src/subscribe/services/otp.service.js`, `src/common/helpers/otp-generator.js` | Cryptographically generated five-digit code with expiry |
| Phone validation | `src/common/helpers/phone-validation.js` | Accepts UK formats and normalises to E.164 |
| Email verification | `src/subscribe/services/email-verification.service.js`, `src/subscribe/controllers/email-verification.controller.js`, `validate-link.controller.js` | UUID token issue, storage of pending subscription data, single-use validation |
| Contact store | `src/subscribe/services/user-contact-service.js` | Shared secret store with single-use and expiry semantics |
| Notify client | `src/subscribe/services/notify-service.js` | `notifications-node-client` wrapper with structured error categorisation and retry guidance |
| Generic send | `src/subscribe/routes/send-notification.route.js`, `src/subscribe/controllers/notification.controller.js` | The endpoint the alert backend posts every message to |
| Notification audit | `src/subscribe/services/user-notification-detail.service.js` | Links Notify notification ids to alert ids |
| SMS reply poller | `src/plugins/sms-reply-cron.js`, `src/subscribe/services/sms-reply.service.js` | Retrieves received texts, handles STOP, calls the alert backend, records outcomes |
| Masking and logging context | `src/common/helpers/masking-utils.js`, `logging-context.js` | Masks numbers, emails, template ids and UUIDs; carries a correlation id through log lines |
| Config | `src/config.js` | `convict` schema, including a hard guard on mock mode in protected environments |

## 4. API Surface

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/health` | Liveness probe | — | Status payload |
| `POST` | `/subscribe/generate-otp` | Issue and send a five-digit SMS passcode | `phoneNumber` in any accepted UK format | `201` with Notify notification id and `submitted` status |
| `POST` | `/subscribe/validate-otp` | Validate a passcode; single use, 15-minute expiry | `phoneNumber`, `otp` | `200` confirmation, `400` when invalid, expired, reused or unknown |
| `POST` | `/subscribe/generate-link` | Issue a UUID verification link and email it | `emailAddress`, `alertType`, `location`, `lat`, `long` | `201` acknowledgement; the token is only echoed when mock mode is on |
| `GET` | `/subscribe/validate-link/{uuid}` | Validate a link and return the pending subscription details | `uuid` path parameter | `200` with email, channel, location and coordinates; `400` when expired or already used, still echoing the stored details |
| `POST` | `/send-notification` | Send an SMS or email through Notify and record the result | `phoneNumber` or `emailAddress`, `templateId`, `personalisation`, `alertId` | `201` with the Notify notification id and `submitted` status; `424` on a Notify failure |
| `GET` | `/process-sms-replies` | Manual trigger for the inbound SMS poller | — | Counts of messages seen and newly processed |

> `status: submitted` acknowledges that Notify accepted the request. It is not a delivery
> confirmation.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| GOV.UK Notify | External API | `notifications-node-client` — send SMS, send email | Recipient, template id and personalisation out; notification id and status back | `NOTIFY_API_KEY` |
| GOV.UK Notify | External API | `notifications-node-client` — received text messages | Inbound SMS replies with sender number, content and timestamp | `NOTIFY_API_KEY` |
| `aqie-alert-back-end-service` | AQIE service | `DELETE /opt-out-sms-alert` | Phone number out; opt-out result back | CDP internal network |
| `aqie-front-end` | AQIE service | Link construction only — `/notify/register/email-confirm-link?token=` | Verification token carried in the emailed link | Tokenised link |
| MongoDB | Datastore | Driver connection | Verification secrets, inbound SMS history, notification audit | `MONGO_URI` |

> The verification-link edge to `aqie-front-end` is **not** yet recorded in
> [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml) — see Section 11.

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| `aqie-alert-back-end-service` | `POST /send-notification` | Recipient, Notify template id, personalisation and originating alert id |
| `aqie-front-end` | `POST /subscribe/generate-otp`, `POST /subscribe/validate-otp` | Mobile number and passcode during the SMS subscription journey |
| `aqie-front-end` | `POST /subscribe/generate-link`, `GET /subscribe/validate-link/{uuid}` | Email address and pending subscription details during the email subscription journey |

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).
> Neither inbound edge above is currently recorded there — see Section 11.

## 7. Data

- **Store:** MongoDB (`MONGO_DATABASE`, default `aqie-notify-service`). Redis appears only in
  the local `compose.yml` and is not used by application code.
- **Key entities:**
  - `user-contact-details` — one document per contact holding the current OTP, its expiry and
    a `validated` flag. Upserted on each request, so only the latest code is live.
  - `user-email-verification-details` — one document per email address holding the UUID token,
    expiry, validated flag and the pending subscription payload (channel, location,
    coordinates). Unique indexes on both contact and token.
  - `sms_replies` — one row per inbound Notify message id with the outcome
    (`unsubscribed`, `user_not_found`, `duplicate_stop` or `ignored`). The message id is the
    idempotency key that stops a reply being processed twice.
  - `user-notification-details` — Notify notification id paired with the originating alert id
    and submission status.
- **Retention / refresh:** OTPs and email links expire after 15 minutes (extended to three
  hours when mock mode is on) and are single use. Inbound replies are polled every
  `NOTIFY_SMS_REPLY_POLL_INTERVAL_MINUTES`, default one minute. No automatic purge of any
  collection was found.

## 8. Configuration

Environment variable **names** only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `PORT`, `HOST` | HTTP listener |
| `NODE_ENV`, `ENVIRONMENT`, `SERVICE_VERSION` | Runtime identity |
| `MONGO_URI`, `MONGO_DATABASE` | MongoDB connection |
| `NOTIFY_API_KEY` | GOV.UK Notify API key |
| `NOTIFY_SMS_VERIFY_OTP_TEMPLATE_ID`, `NOTIFY_OTP_PERSONALISATION_KEY` | OTP SMS template and the personalisation field carrying the code |
| `NOTIFY_EMAIL_VERIFY_LINK_TEMPLATE_ID` | Email verification link template |
| `NOTIFY_SMS_UNSUBSCRIBE_CONFIRMATION_TEMPLATE_ID` | Confirmation SMS sent after a STOP reply |
| `NOTIFY_TIMEOUT_MS` | Notify send timeout |
| `NOTIFY_SMS_REPLY_POLL_ENABLED`, `NOTIFY_SMS_REPLY_POLL_INTERVAL_MINUTES` | Inbound SMS poller switch and interval |
| `ALERT_BACKEND_URL` | Base URL of `aqie-alert-back-end-service` for the STOP opt-out call |
| `ALERT_FRONTEND_BASE_URL` | Base URL of `aqie-front-end`, used to build the emailed verification link |
| `USE_MOCK` | Automation affordance — fixes the stored OTP, extends expiries and echoes the email token. Start-up fails if it is set in `prod` or `ext-test` |
| `HTTP_PROXY` | CDP egress proxy |
| `ENABLE_METRICS`, `TRACING_HEADER` | Observability |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`;
  entrypoint `node src`.
- **Internal address:** `https://aqie-notify-service.<env>.cdp-int.defra.cloud`.
- **Environments:** `local`, `infra-dev`, `management`, `dev`, `test`, `perf-test`, `ext-test`,
  `prod` are all accepted values of `ENVIRONMENT`; mock mode is refused in the last two.
- **Local development:** `compose.yml` provides MongoDB, Redis and LocalStack.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — lint, test and SonarQube on PR, plus a
    scheduled run
  - `.github/workflows/publish.yml` — build and publish on push to `main`
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, ECS-formatted in production. Log events use a stable
  dotted vocabulary (`otp.generate.failed`, `sms_reply.stop.unsubscribed`, and so on) and are
  catalogued in the repository's own `docs/LOGGING.md`. Phone numbers, emails, template ids
  and UUIDs are masked; Notify response bodies are deliberately not logged because they echo
  the rendered message text.
- **Tracing:** `@defra/hapi-tracing` with the header named in `TRACING_HEADER`; every endpoint
  also accepts `x-cdp-request-id` and threads it through as `requestId`.
- **Metrics:** `aws-embedded-metrics` (CloudWatch EMF), gated by `ENABLE_METRICS`.
- **Auditing:** `@defra/cdp-auditing`.
- **Shutdown:** `hapi-pulse` for graceful draining; the SMS poller interval is cleared on stop.

## 11. Open Questions

- [ ] **Catalogue gap:** `aqie-front-end → aqie-notify-service` (the four `/subscribe/*`
      endpoints) is evidenced but not in `docs/integration-catalog.yaml`.
- [ ] **Catalogue gap:** `aqie-alert-back-end-service → aqie-notify-service`
      (`POST /send-notification`) is evidenced but not in the catalogue.
- [ ] **Catalogue gap:** the emailed verification link points at `aqie-front-end`
      (`/notify/register/email-confirm-link`), an outbound-link edge equivalent to the one
      already recorded for the alert backend.
- [ ] `GET /process-sms-replies` triggers the poller with no authentication and no rate
      limiting. Confirm it is reachable only inside the CDP network.
- [ ] `POST /send-notification` accepts any template id from any caller on the internal
      network, with no allow-list. Confirm whether that is acceptable.
- [ ] The service still carries the CDP template's `GET /example` routes. Confirm they can be
      removed.
- [ ] Confirm the retention and deletion policy for `sms_replies`, which stores full inbound
      message content and sender numbers, and for `user-notification-details`.
- [ ] Activity status is `Monitoring` in the repository catalogue while the alert backend is
      `Active` and depends on this service for every message. Confirm ownership and support
      arrangements. (catalogue `oq-005`)
