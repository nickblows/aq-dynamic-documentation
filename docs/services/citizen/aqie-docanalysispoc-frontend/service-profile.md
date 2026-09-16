# aqie-docanalysispoc-frontend

> The first of three repositories in the document analysis proof of concept: a minimal,
> password-gated page for uploading a PDF business case and receiving an AI-generated summary.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-docanalysispoc-frontend`](https://github.com/DEFRA/aqie-docanalysispoc-frontend) |
| Service domain | `Citizen` |
| Service type | `Prototype Service (including PoC)` |
| Lifecycle stage | `Prototype/PoC` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22.16.0` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2025-07-17` |
| Last main commit (UTC) | `2025-08-21T08:01:20Z` |
| Last analysed commit | `b8889c1c` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Inactive` |

## 2. Purpose and Responsibilities

> **Superseded and inactive.** The first user interface for the document analysis proof of
> concept. Replaced by `aqie-docanalysisawspoc-frontend`, which added AWS-based file handling
> and Azure Entra ID sign-in. Not formally archived on GitHub. Do not deploy.

**The document analysis proof of concept.** Three repositories, all created within a week in
July 2025, explored whether a large language model could review and summarise DEFRA business
case documents. Despite the `aqie-` prefix and the AQIE team owning them, the subject matter is
not air quality: the prompts appraise business cases against HM Treasury Green Book guidance,
produce Red Team challenge reviews, and draft investment committee and executive briefings.
The sequence is: this repository first (17 July), then `aqie-docanalysispoc-backend` (22 July),
then `aqie-docanalysisawspoc-frontend` (23 July), which became the surviving front end and was
still receiving changes in December 2025.

**Does:**

- Gates access behind a single shared password held in configuration, with a Redis-backed
  session.
- Accepts a single PDF upload of up to 50 MB, extracts its text in-process, and posts that text
  to `aqie-docanalysispoc-backend` for summarisation, passing a model selector.
- Renders the returned summary back to the user.

**Does not:**

- Store the uploaded document anywhere durable. There is no S3 integration and no database.
  This is the main gap that the AWS successor closed.
- Use departmental sign-in. There are no named users and no role model, only the shared
  password.

## 3. Architecture

- **Pattern:** Hapi frontend on the CDP Node.js frontend template, with a bespoke `login`
  authentication strategy and a single upload journey.

| Component | Path | Responsibility |
|---|---|---|
| Login | `src/server/login/` | Shared-password sign-in and sign-out |
| Upload | `src/server/upload/` | Multipart PDF upload, text extraction, backend call, result rendering |
| PDF parser | `src/server/utils/pdfParser.js` | Extracts text from the uploaded PDF |
| Summariser | `src/server/utils/summarizer.js` | Client-side helper for the summarisation call |
| Config | `src/config/config.js` | `convict` schema |

## 4. API Surface

| Method | Path | Purpose |
|---|---|---|
| `GET` \| `POST` | `/` | Password sign-in page and submission |
| `GET` | `/logout` | End session |
| `GET` \| `POST` | `/upload` | Upload form and PDF submission (authenticated) |
| `GET` | `/about`, `/health`, `/favicon.ico`, static assets | Supporting routes |

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-docanalysispoc-backend` | AQIE service | `POST /summarize?model=` | Extracted document text in; summary out | CDP internal network |
| Azure OpenAI | External API | `AI_OPEN_API_URL` | Configured but summarisation is delegated to the backend | `OPEN_AI_KEY` |
| Redis | Datastore | Session cache | Session state | `REDIS_PASSWORD` |

## 6. Consumed By (Inbound Dependencies)

None. It was the entry point for the proof of concept.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** Redis for sessions only. Uploaded PDFs are handled in-process and not retained.
- **Key entities:** uploaded document text and the generated summary, both transient.
- **Retention / refresh:** session TTL only. Document text was, however, sent to a third-party
  model endpoint — see the open questions.

## 8. Configuration

Variable **names** only.

| Variable | Purpose |
|---|---|
| `POC_PASSWORD` | Shared access password for the prototype |
| `AI_OPEN_API_URL`, `OPEN_AI_KEY` | Azure OpenAI endpoint and key |
| `BACKEND_API_URL` | `aqie-docanalysispoc-backend` base URL |
| `PORT`, `HOST`, `NODE_ENV`, `SERVICE_VERSION` | Runtime identity |
| `REDIS_HOST`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_TLS`, `REDIS_KEY_PREFIX` | Session cache |
| `SESSION_CACHE_*`, `SESSION_COOKIE_*`, `USE_SINGLE_INSTANCE_CACHE` | Session behaviour |
| `ASSET_PATH`, `STATIC_CACHE_TIMEOUT` | Static assets |
| `HTTP_PROXY`, `ENABLE_SECURE_CONTEXT`, `TRUSTSTORE_ONE` | CDP egress and TLS |
| `ENABLE_METRICS`, `TRACING_HEADER`, `LOG_*` | Observability |

> **Security note.** The final commit on `main` is titled "remove password". The shared
> prototype password was therefore committed at some point and later removed from the working
> tree. Removing a value from the latest commit does not remove it from the public Git history,
> so it must be treated as compromised and rotated wherever it was reused. The value is not
> recorded here. The `OPEN_AI_KEY` default is empty, so the model key does not appear to have
> been committed in this repository.

## 9. Hosting and Deployment

- **Platform:** DEFRA CDP on AWS ECS, `dev` only.
- **Container:** CDP Node.js base images, entrypoint `node src`.
- **Pipelines:** the standard CDP set — `check-pull-request.yml` (also on a schedule),
  `publish.yml`, `publish-hotfix.yml`, with SonarQube analysis.

## 10. Observability

- **Logging:** `pino` via `hapi-pino` with `@elastic/ecs-pino-format` and a redaction list.
- **Tracing:** `@defra/hapi-tracing`.
- **Metrics:** `aws-embedded-metrics`.

## 11. Open Questions

- [ ] **Rotate the shared prototype password.** It is recoverable from the public Git history
      of this repository. Confirm it was not reused for anything else.
- [ ] What documents were actually uploaded during the proof of concept, and were any of them
      sensitive or unpublished? Nothing is persisted in the repository, but the runtime
      behaviour sent document text to a hosted model endpoint.
- [ ] Confirm `aqie-docanalysisawspoc-frontend` is the formal successor and that this
      repository can be archived on GitHub, or deleted.
- [ ] Was the Azure OpenAI instance used (`tradeplatform-ai`) an AQIE-owned resource, or one
      borrowed from another DEFRA programme? The naming suggests the latter, which has
      information governance implications.
