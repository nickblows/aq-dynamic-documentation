# aqie-docanalysispoc-backend

> The summarisation engine of the document analysis proof of concept. Takes document text or an
> uploaded file reference and returns a large language model summary.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-docanalysispoc-backend`](https://github.com/DEFRA/aqie-docanalysispoc-backend) |
| Service domain | `Data` |
| Service type | `Prototype Service (including PoC)` |
| Lifecycle stage | `Prototype/PoC` |
| Primary language | JavaScript |
| Runtime | Node.js `>=22.16.0` (ES modules) |
| Default branch | `main` |
| Created (UTC) | `2025-07-22` |
| Last main commit (UTC) | `2025-10-29T16:35:46Z` |
| Last analysed commit | `74bfe45d` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Inactive` |

## 2. Purpose and Responsibilities

> **Inactive prototype.** The shared backend for both document analysis front ends. Not
> superseded — nothing replaced it, the proof of concept simply stopped. Not formally archived
> on GitHub. Do not deploy.

**The document analysis proof of concept.** Three repositories created within a week in July
2025 explored whether a large language model could review and summarise DEFRA business case
documents. Despite the `aqie-` prefix, the subject matter is not air quality — the prompts
appraise business cases against HM Treasury Green Book guidance and produce Red Team,
investment committee and executive briefing outputs. This repository is the engine shared by
`aqie-docanalysispoc-frontend` (17 July) and `aqie-docanalysisawspoc-frontend` (23 July).

**Does:**

- Accepts document text and returns a generated summary.
- Retrieves an uploaded file from S3 by request identifier and extracts its text.
- Supports two model back ends, selected by the `USE_DIRECT_API` flag: Azure OpenAI (a GPT-4
  family model) and AWS Bedrock (an Anthropic Claude 3 Sonnet model), using LangChain
  community integrations and the AWS Bedrock runtime SDK.

**Does not:**

- Authenticate callers. It relies entirely on the CDP internal network and the sign-in
  implemented by the front ends.
- Persist documents, summaries or an audit trail. Each request is independent.

The final commit, "increase token size to 15000", is a fair summary of where the work stopped:
the team was still tuning context limits when the proof of concept ended.

## 3. Architecture

- **Pattern:** Hapi HTTP API on the CDP Node.js backend template, with a service layer wrapping
  two interchangeable model providers.

| Component | Path | Responsibility |
|---|---|---|
| Document routes | `src/routes/documents.js`, `summaryroute.js` | Summarisation entry points |
| S3 route | `src/routes/s3route.js` | Fetches an uploaded file by request identifier |
| OpenAI service | `src/services/openai-service.js` | Model selection; Azure OpenAI and Bedrock Claude |
| PDF service | `src/services/pdf-service.js` | Text extraction from PDFs |
| Helpers | `src/services/helper/` | `getS3data`, `summarizetext` |
| Config | `src/config.js` | `convict` schema |

## 4. API Surface

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness probe |
| `GET` \| `POST` | `/summarize` | Summarise supplied document text, with a model selector |
| `POST` | `/api/documents/summarize` | Alternative summarisation route |
| `GET` | `/api/documents/test`, `/test` | Development probes |
| `GET` | `/getS3/{requestId}` | Retrieve and extract an uploaded document from S3 |
| `GET` | `/`, `/example`, `/example/{exampleId}` | Unmodified CDP template routes |

Two overlapping route families reached `main`, which is typical of prototype code and worth
noting if anyone revives this work.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| Azure OpenAI | External API | `AI_OPEN_API_URL` (a `tradeplatform-ai` Azure resource) | Document text in; summary out | `OPEN_AI_KEY` |
| AWS Bedrock | External API | `BEDROCK_API_URL`, Bedrock runtime SDK | Document text in; summary out | `BEARER_TOKEN_BEDROCK` or IAM role |
| AWS S3 | Datastore | SDK | Reads uploaded documents | IAM role |

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| `aqie-docanalysispoc-frontend` | `POST /summarize?model=` | Extracted document text in; summary out |
| `aqie-docanalysisawspoc-frontend` | Summarisation and S3 retrieval routes | Uploaded document reference in; summary out |

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** AWS S3 for uploaded documents, read only. Redis appears in the local compose file
  but is not used by the service.
- **Key entities:** document text and generated summaries, both transient.
- **Retention / refresh:** none defined. Document text is transmitted to third-party model
  endpoints on every request.

## 8. Configuration

Variable **names** only.

| Variable | Purpose |
|---|---|
| `AI_OPEN_API_URL`, `OPEN_AI_KEY`, `OPENAI_MODEL` | Azure OpenAI endpoint, key and model |
| `BEDROCK_API_URL`, `BEARER_TOKEN_BEDROCK` | AWS Bedrock endpoint and token |
| `USE_DIRECT_API` | Selects between the two model providers |
| `AWS_REGION`, `AWS_S3_BUCKET_NAME` | S3 location for uploaded documents |
| `ENABLE_CORS`, `CORS_ORIGIN` | Cross-origin access for the front ends |
| `PORT`, `HOST`, `NODE_ENV`, `ENVIRONMENT`, `SERVICE_VERSION` | Runtime identity |
| `HTTP_PROXY`, `ENABLE_SECURE_CONTEXT`, `TRUSTSTORE_ONE` | CDP egress and TLS |
| `ENABLE_METRICS`, `TRACING_HEADER`, `LOG_*` | Observability |

Both model credentials default to empty, so no key is committed. The S3 bucket name is
committed as a non-empty default; that is an identifier rather than a secret, but it does
disclose infrastructure naming in a public repository.

## 9. Hosting and Deployment

- **Platform:** DEFRA CDP on AWS ECS, `dev` only.
- **Container:** CDP Node.js base images, entrypoint `node src`.
- **Pipelines:** the standard CDP set — `check-pull-request.yml`, `publish.yml`,
  `publish-hotfix.yml`, with SonarQube analysis.

## 10. Observability

- **Logging:** `pino` with `@elastic/ecs-pino-format`.
- **Tracing:** `@defra/hapi-tracing`.
- **Metrics:** `aws-embedded-metrics`.

## 11. Open Questions

- [ ] What was the outcome of the proof of concept? Neither model provider is recorded as
      preferred, and there is no evaluation, no benchmark and no recommendation in the
      repository.
- [ ] Was there an information governance or data protection assessment covering DEFRA business
      case text being sent to Azure OpenAI and AWS Bedrock? This is the question most worth
      answering before anyone reuses this code.
- [ ] Which Azure subscription owns the `tradeplatform-ai` resource, and was AQIE authorised to
      use it?
- [ ] Should the repository be archived on GitHub to stop Dependabot and scheduled scans
      running against dead prototype code?
- [ ] Is any of this work being carried forward under another team, given the subject matter is
      business case appraisal rather than air quality?
