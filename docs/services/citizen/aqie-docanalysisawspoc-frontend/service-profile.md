# aqie-docanalysisawspoc-frontend

> The surviving front end of the document analysis proof of concept, branded "Business Case
> Summarisation". Adds departmental sign-in, CDP Uploader file handling and a set of named
> review prompts.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-docanalysisawspoc-frontend`](https://github.com/DEFRA/aqie-docanalysisawspoc-frontend) |
| Service domain | `Citizen` |
| Service type | `Prototype Service (including PoC)` |
| Lifecycle stage | `Prototype/PoC` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22.16.0` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2025-07-23` |
| Last main commit (UTC) | `2025-12-17T16:10:49Z` |
| Last analysed commit | `3765abbe` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Inactive` |

## 2. Purpose and Responsibilities

> **Inactive prototype.** Supersedes `aqie-docanalysispoc-frontend`. Nothing has superseded
> this repository — the proof of concept stopped in December 2025. Not formally archived on
> GitHub. Do not deploy.

**The document analysis proof of concept.** Three repositories created within a week in July
2025 explored whether a large language model could review and summarise DEFRA business case
documents. Despite the `aqie-` prefix, the subject matter is not air quality. This repository
was created one day after `aqie-docanalysispoc-backend` and six days after the original front
end, but it outlived both by several months and is where the proof of concept actually
developed.

**Does:**

- Signs users in with Azure Entra ID, and restricts each review type to an allow-list of email
  addresses supplied through configuration.
- Accepts a document either through the shared CDP Uploader service or by direct upload to S3,
  and tracks upload progress by request identifier.
- Runs one of five named prompts against the document: Green Book appraisal, Red Team
  challenge review, Red Investment Committee briefing, executive briefing, and a comparison of
  an old and a new version of a document.
- Delegates summarisation to `aqie-docanalysispoc-backend`, with a local LangChain summariser
  as an alternative path.

**Does not:**

- Handle air quality data of any kind.
- Provide an evaluation of output quality. There is no scoring, no reviewer feedback capture
  and no record of findings in the repository.

**What the prompts reveal.** The five prompts are the clearest statement of what was being
investigated: whether a model could act as a first-pass appraiser and briefing writer for
business cases, applying HM Treasury Green Book criteria and Red Team challenge techniques, and
whether it could reliably spot differences between document versions.

## 3. Architecture

- **Pattern:** Hapi frontend on the CDP Node.js frontend template, with an Azure Entra ID
  authentication plugin and two parallel upload paths.

| Component | Path | Responsibility |
|---|---|---|
| Azure auth plugin | `src/server/plugins/azure-auth.js`, `src/config/azure-auth.js` | OAuth sign-in, callback, session and sign-out |
| CDP Uploader journey | `src/server/cdp-uploader/` | Initiate upload, poll status, handle completion |
| Basic upload journey | `src/server/basic-upload/` | Direct S3 upload alternative |
| Status | `src/server/status/` | Upload and analysis progress by request identifier |
| Prompts | `src/server/common/constants/prompts.js` | The five named review prompts |
| Summariser | `src/server/utils/summarizer.js` | LangChain summarisation path |
| Config | `src/config/config.js` | `convict` schema, including the per-review-type allow-lists |

## 4. API Surface

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/`, `/logout` | Landing and sign-out |
| `GET` | `/auth/login`, `/auth/callback`, `/auth/session`, `/auth/logout` | Azure Entra ID flow |
| `GET` \| `POST` | `/Uploader` | CDP Uploader journey |
| `GET` | `/Uploader/complete`, `/Uploader/status` | Upload completion and polling |
| `GET` | `/basic`, `/basic/complete` | Direct S3 upload journey |
| `GET` | `/progress/{requestId}`, `/status/{requestId}` | Analysis progress |
| `GET` | `/about`, `/health`, static assets | Supporting routes |

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| `aqie-docanalysispoc-backend` | AQIE service | Summarisation and S3 retrieval routes | Document reference in; summary out | CDP internal network |
| `cdp-uploader` | Platform service | `CDP_UPLOADER_URL` initiate and status | File upload brokering and virus scanning | CDP internal network |
| Microsoft Entra ID | External API | `login.microsoftonline.com` OAuth | Sign-in and user identity | `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID` |
| Azure OpenAI | External API | `AI_OPEN_API_URL` | Document text in; summary out, on the local LangChain path | `OPEN_AI_KEY` |
| AWS S3 | Datastore | SDK | Uploaded documents | IAM role |
| Redis | Datastore | Session cache | Session state | `REDIS_PASSWORD` |

## 6. Consumed By (Inbound Dependencies)

None. It is the entry point for the proof of concept.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** AWS S3 for uploaded documents; Redis for sessions.
- **Key entities:** uploaded business case documents, generated summaries and briefings, and
  the signed-in user's email address used for access control.
- **Retention / refresh:** no retention policy is defined. Uploaded documents remain in the S3
  bucket unless removed separately.

> **Committed document.** The repository contains a real DEFRA business document at
> `docs/Protected Sites Strategies (PSS) Strategic Outline Case (SOC) 17.03.2025.pdf`, almost
> certainly used as a test fixture. This is a public repository. Confirm whether the document
> is cleared for publication; if not, it must be removed from the repository and its Git
> history.

## 8. Configuration

Variable **names** only.

| Variable | Purpose |
|---|---|
| `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`, `AZURE_REDIRECT_URI` | Entra ID sign-in |
| `R_TEAM`, `G_TEAM`, `ICB_TEAM`, `EB_TEAM` | Email allow-lists for the Red Team, Green Book, investment committee and executive briefing review types |
| `POC_PASSWORD` | Legacy shared password carried over from the earlier front end |
| `AI_OPEN_API_URL`, `OPEN_AI_KEY` | Azure OpenAI endpoint and key |
| `BACKEND_API_URL` | `aqie-docanalysispoc-backend` base URL |
| `CDP_UPLOADER_URL`, `ENABLE_CDP_UPLOADER` | CDP Uploader integration and its feature flag |
| `AWS_REGION`, `AWS_S3_BUCKET_NAME` | S3 location for uploads |
| `APP_BASE_URL`, `PORT`, `HOST`, `NODE_ENV`, `SERVICE_VERSION` | Runtime identity |
| `REDIS_*`, `SESSION_CACHE_*`, `SESSION_COOKIE_*`, `USE_SINGLE_INSTANCE_CACHE` | Session cache and cookie |
| `ASSET_PATH`, `STATIC_CACHE_TIMEOUT` | Static assets |
| `HTTP_PROXY`, `ENABLE_SECURE_CONTEXT`, `TRUSTSTORE_ONE` | CDP egress and TLS |
| `ENABLE_METRICS`, `TRACING_HEADER`, `LOG_*` | Observability |

> **Security note.** `POC_PASSWORD` has a non-empty literal default committed in
> `src/config/config.js`, so the shared prototype password is readable in a public repository.
> The value is not recorded here. It must be treated as compromised and rotated wherever it was
> reused, including in `aqie-docanalysispoc-frontend`, whose final commit removed the same
> password from the working tree but not from history. The session cookie password also has a
> committed literal default inherited from the CDP template. The Azure, OpenAI and Redis
> credentials all default to empty and are not committed. The allow-list variables default to
> empty, so no personal email addresses are committed.

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

- [ ] **Confirm the clearance status of the committed Strategic Outline Case PDF** and remove it
      from the repository and its history if it is not published material.
- [ ] **Rotate the committed shared prototype password**, and confirm it was not reused
      elsewhere.
- [ ] What was the outcome of the proof of concept? No evaluation, benchmark or recommendation
      is recorded. The last commit refines the access allow-list, which suggests it was still in
      use by a small group in December 2025.
- [ ] Who were the intended users, and is the service still expected to be available to them?
      If not, it should be undeployed and the repository archived.
- [ ] Was an information governance assessment completed for uploading DEFRA business cases to
      hosted model endpoints?
- [ ] Should this work sit with AQIE at all? The subject matter is business case appraisal, and
      the `aqie-` prefix is now misleading.
