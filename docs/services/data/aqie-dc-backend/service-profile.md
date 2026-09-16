# aqie-dc-backend

> The system of record for smoke control domestic combustion. Holds the registers of exempt
> appliances and authorised fuels, receives applications submitted through DEFRA Forms, and
> serves the register and the caseworker technical review workflow over an internal HTTP API.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-dc-backend`](https://github.com/DEFRA/aqie-dc-backend) |
| Service domain | `Data` |
| Service type | `Auxilary Backend Service` |
| Lifecycle stage | `Beta` |
| Primary language | JavaScript |
| Runtime | Node.js `>=24` (ES modules), pinned to `v24.11.1` in `.nvmrc` |
| Default branch | `main` |
| Created (UTC) | `2026-01-26` |
| Last main commit (UTC) | `2026-09-14T15:26:12Z` |
| Last analysed commit | `f9b87b10` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

Domestic combustion ("DC") is the smoke control regime: appliances that may lawfully be used
in a smoke control area, and fuels that may lawfully be burned in one. This service owns that
data and the process that decides what goes into it.

**Does:**

- Holds the **appliance register** — manufacturer, model, appliance type, nominal thermal
  output, permitted fuels, multifuel capability, variant relationships, and the separate
  certification status for England, Scotland, Wales and Northern Ireland.
- Holds the **fuel register** — manufacturer or reseller, fuel description and composition,
  sulphur content, bagging and manufacturing process, rebrand lineage, and the same four
  country certification statuses.
- Receives applications from the DEFRA Forms service by polling an AWS SQS queue, maps the
  opaque form field identifiers into domain fields, and creates the application and its
  linked appliance or fuel items.
- Runs the **application lifecycle**: an application is created as `new`, moved to
  `in_progress` when a caseworker starts it, and only moves to `complete` once every linked
  item has reached a final technical review outcome.
- Runs the **technical review workflow** for each item: four documentation checks (test
  reports, technical drawings, conformity mark, instruction manual) and three listing checks
  (appliance details, permitted fuels, additional conditions). An item cannot be accepted
  until every check has passed; it can be rejected at any point.
- Provides public-facing search over the registers, and caseworker-facing reads that group an
  application's items by technical review status.
- Proxies bulk register imports through the shared CDP Uploader so spreadsheets are
  virus-scanned before the service reads them from S3 and loads them into MongoDB.
- Publishes an OpenAPI description of its own routes via `hapi-swagger`.

**Does not:**

- Render any user interface. The public register is presented by `aqie-dc-frontend`; the
  caseworker screens are `aqie-dc-admin-frontend`.
- Collect applications from applicants. Application capture is done by the DEFRA Forms
  service; this service only consumes the resulting submission messages.
- Authenticate or authorise end users. Caseworker identity is established by
  `aqie-dc-admin-frontend` against Microsoft Entra ID and passed to this service only as a
  `reviewedBy` name and email on the payload — see Section 11.
- Scan uploaded files for malware. That is the platform's CDP Uploader.
- Hold any air quality measurement, forecast or monitoring station data — that is
  `aqie-back-end`, `aqie-forecast-api` and `aqie-monitoringstation-backend`. Domestic
  combustion shares no data with the air quality reporting estate.
- Send notifications. There is no GOV.UK Notify or `aqie-notify-service` integration in this
  repository.

## 3. Architecture

**Pattern:** Hapi HTTP API with a long-polling AWS SQS consumer registered as a Hapi plugin in
the same process. The consumer does not write to MongoDB directly — it re-enters the service's
own routes through `server.inject`, so ingest and API writes share one validation path.

| Component | Path | Responsibility |
|---|---|---|
| Server composition | `src/server.js` | Registers the SQS consumer, Swagger, Mongo pool, tracing, secure context and the router |
| Router | `src/plugins/router.js` | Wires all route modules; hosts the CDP Uploader proxy route and the Excel template directory |
| Appliance routes | `src/routes/appliances/` | Appliance CRUD, public search, technical review read and write, per-check recording |
| Fuel routes | `src/routes/fuels/` | Fuel CRUD and public search |
| Application routes | `src/routes/applications/` | Application creation, listing, counts, search, summaries and lifecycle transitions |
| SQS message routes | `src/routes/sqs-messages/` | Persists the raw and mapped form submission for audit and replay |
| Upload callback | `src/routes/upload-callback.js` | Receives the CDP Uploader scan result and triggers the spreadsheet import |
| Admin import | `src/routes/admin-import.js` | Initiates an upload session with the CDP Uploader and polls its status |
| SQS consumer plugin | `src/plugins/sqs-consumer.js` | Background polling loop with an `AbortController` tied to server shutdown |
| SQS client | `src/sqs/client.js` | Resolves the queue URL, long-polls, batch-deletes, decides appliance vs fuel |
| SQS field mapper | `src/sqs/mapper.js` | Translates DEFRA Forms field identifiers into domain field names |
| SQS repeater splitter | `src/sqs/repeater.js` | Splits a multi-appliance submission into one item per appliance |
| SQS dispatcher | `src/sqs/dispatcher.js` | Calls the service's own routes via `server.inject` |
| Controllers | `src/controllers/` | MongoDB read and write logic for appliances, fuels, applications and reviews |
| Schemas | `src/common/schemas/` | Joi definitions for appliance, fuel, application and audit action |
| Review rules | `src/common/helpers/review-status.js` | Defines the check groups and when an item or application is review-complete |
| Uploader helper | `src/common/helpers/cdp-uploader.js` | Builds the initiate payload and the environment-specific callback URL |
| S3 helper | `src/common/helpers/s3-download.js` | Downloads the scanned file to a temporary path and cleans it up |
| Migrations and imports | `src/migrations/` | Excel import, template generation and seed data scripts |
| Config | `src/config.js` | `convict` schema for all endpoints, buckets and connection details |

## 4. API Surface

The service exposes 33 routes. The gateway strips the `/aqie-dc-backend` prefix before
requests reach the service, which is why the uploader proxy route is registered at the bare
path.

**Appliance register**

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/api/appliances/search` | Public appliance search | Search and filter terms | Matching appliance records |
| `GET` | `/appliances` | Full appliance list | — | Appliance collection |
| `POST` | `/appliances` | Create an appliance | Appliance payload | Created appliance |
| `GET` | `/appliances/{id}` | Single appliance | `id` | Appliance record |
| `PATCH` | `/appliances/{id}` | Update an appliance | Partial appliance payload | Updated appliance |
| `DELETE` | `/appliances/{id}` | Remove an appliance | `id` | Deletion outcome |

**Fuel register**

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/api/fuels/search` | Public fuel search | Search and filter terms | Matching fuel records |
| `GET` | `/fuels` | Full fuel list | — | Fuel collection |
| `POST` | `/fuels` | Create a fuel | Fuel payload | Created fuel |
| `GET` | `/fuels/{fuelId}` | Single fuel | `fuelId` | Fuel record |
| `PATCH` | `/fuels/{fuelId}` | Update a fuel | Partial fuel payload | Updated fuel |
| `DELETE` | `/fuels/{fuelId}` | Remove a fuel | `fuelId` | Deletion outcome |

**Application and case lifecycle**

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `POST` | `/applications` | Create an application with its linked items | Application payload | Created application |
| `GET` | `/applications` | Full application list | — | Application collection |
| `GET` | `/applications/counts` | Case counts by status, for the caseworker dashboard | — | Counts by status |
| `GET` | `/applications/search` | Application search | Filter criteria | Matching applications |
| `GET` | `/applications/summary` | Applications with a per-case item summary | — | Application list with item summaries |
| `GET` | `/applications/{applicationId}` | Single application; `groupBy=techReviewStatus` returns its items split into accepted and rejected | `applicationId`, optional `groupBy` | Application with linked items |
| `GET` | `/applications/{applicationId}/summary` | Item summary for one application | `applicationId`, optional `type` | Item names and review statuses |
| `PATCH` | `/applications/{id}/in-progress` | Mark the case as started by a caseworker | Reviewer identity | Updated application |
| `PATCH` | `/applications/{id}/complete` | Close the case once every item is reviewed | Reviewer identity | Updated application |

**Technical review**

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/appliances/{id}/technical-review` | Review state and outstanding checks for one appliance | `id` | Appliance with review checks and status |
| `PATCH` | `/appliances/{id}/technical-review` | Record the reviewer decision (`in_review`, `accepted`, `rejected`) | Status and reviewer identity | Updated review |
| `PATCH` | `/appliances/{id}/technical-review/checks` | Record a single documentation or listing check result, optionally with the field values that check confirms | Check name, pass or fail, optional field data | Updated review |

**Ingest, upload and platform**

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `POST` | `/sqs-messages` | Persists a consumed form submission — raw body, parsed body and mapped payload | Submission record | Stored record |
| `POST` | `/admin/import/initiate` | Starts a CDP Uploader session for a bulk register import | Entity types to import | `uploadId`, upload URL, status URL |
| `GET` | `/admin/import/status` | Polls the CDP Uploader for scan and upload progress | `statusUrl` | Uploader status |
| `POST` | `/upload-and-scan/{uploadId}` | Streams the file straight through to the CDP Uploader | File stream | Uploader response |
| `POST` | `/upload-callback` | Receives the scan outcome and runs the spreadsheet import | Upload status, metadata, form, rejected file count | Import result |
| `GET` | `/templates/{file*}` | Serves blank Excel import templates | `file` | Template file |
| `GET` | `/health` | Liveness probe | — | Status payload |
| `GET` | `/example`, `/example/{exampleId}` | CDP template scaffolding, not domain routes | — | Example payload |

> `/appliances/{id}/technical-review/checks` is the only write path the caseworker screens use
> for check results. For the permitted fuels check the backend applies the appliance field
> updates and the check result in a single update, so the two cannot drift apart.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| CDP Uploader | Platform service | `POST /initiate` | Bucket, prefix, callback URL, allowed MIME types, size limit and entity metadata out; `uploadId`, upload URL and status URL back | Platform-internal network |
| CDP Uploader | Platform service | `POST /upload-and-scan/{uploadId}` (proxied) | File stream passed through unparsed | Platform-internal network |
| CDP Uploader | Platform service | Status URL poll | Upload and scan progress | Platform-internal network |
| AWS SQS | Datastore / queue | Long poll of queue `aqie-dc-queue` (batch of 10, 10s wait, 5 minute loop interval) | DEFRA Forms submissions in; batch delete on success | IAM task role |
| AWS S3 | Datastore | Object read of the bucket and key supplied in the uploader callback | Scanned spreadsheet downloaded to a temporary file, then deleted | IAM task role |
| MongoDB | Datastore | Driver connection | Appliances, fuels, applications, consumed messages | `MONGO_URI` |

**Evidence for the queue name:** `src/sqs/client.js` — `GetQueueUrlCommand` with a hardcoded
`QueueName` of `aqie-dc-queue`; the `config.get('aws.queueName')` alternative is commented out.

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| `aqie-dc-admin-frontend` | `GET /applications/summary`, `GET /applications/counts`, `GET /applications/{id}?groupBy=techReviewStatus`, `GET /applications/{id}/summary`, `PATCH /applications/{id}/complete`, `GET /appliances/{id}/technical-review`, `PATCH /appliances/{id}/technical-review`, `PATCH /appliances/{id}/technical-review/checks` | Case lists and counts, appliance review state, check results and reviewer decisions |
| `aqie-dc-frontend` | `GET /get-all/{type}`, `GET /get/{type}/{id}` | Register listings and single register entries — **but these paths are not served by the current `main`**, see Section 11 |
| CDP Uploader | `POST /upload-callback` | Scan outcome, S3 bucket and key, and the entity metadata supplied at initiate |
| DEFRA Forms (indirectly) | AWS SQS queue `aqie-dc-queue` | Appliance and fuel certification applications |

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).
> The SQS consumer edge and the DEFRA Forms source are **not yet present** in that catalogue.

## 7. Data

- **Store:** MongoDB (`MONGO_DATABASE`, default `aqie-dc-backend`), with `mongo-locks`
  available for distributed locking.
- **Collections:**
  - `Appliances` — one document per appliance model under consideration or certified.
  - `Fuels` — one document per authorised or applied-for fuel.
  - `Applications` — the case wrapper; `type` is `appliance` or `fuel` and determines which
    collection holds its items.
  - `SqsMessages` — the raw form body, the parsed body and the mapped payload for every
    consumed submission, keyed by SQS message id.
- **Key entities:**
  - *Application* — `type`, server-generated `id`, DEFRA Forms `referenceNumber` and
    `submittedAt`, `status` (`new` | `in_progress` | `complete`), the linked items,
    `reviewedBy` and `reviewedAt`.
  - *Appliance* — identifier matching `APP-…`, applicant company name, UK or overseas address
    (UK addresses may carry a UPRN from the form's address finder), contact name, email,
    optional alternative email and a validated UK or international phone number, model name
    and number, appliance type, variant flag and the appliance it varies from, nominal output
    in kW, multifuel flag, permitted fuels, declaration, caseworker-entered test results
    (rated and low tested output, rated and low smoke emission output), additional conditions,
    instruction and servicing manual references, legacy register fields, the `technicalReview`
    block, and four independent country certification blocks.
  - *Fuel* — applicant company and contact details, responsible person, fuel description,
    composition, weight, sulphur content, manufacturing process and quality system, bagging
    and complaints handling, rebrand lineage (original manufacturer, original name, what
    changed, resell brand), brand names, declaration, plus the same `technicalReview` and
    four country certification blocks.
  - *Country certification* — `status` (`new`, `awaiting_decision`, `certified`, `revoked`,
    `rejected`), who decided it and when, and the first and last certification dates. England,
    Scotland, Wales and Northern Ireland are tracked separately because the four
    administrations certify independently.
  - *Audit action* — an append-only record of certification changes, technical review
    transitions and appliance create, update and publish events, each naming the person and
    timestamp.
- **Refresh:** event-driven. There are no cron schedules. New data arrives either from the SQS
  poll (every five minutes, with a ten second long poll) or from an operator-initiated
  spreadsheet import.
- **Uploads:** files are written by the CDP Uploader to `CDP_UPLOADER_S3_BUCKET` under
  `CDP_UPLOADER_S3_PREFIX`, limited to 10 MB and to Excel MIME types. The service downloads
  the scanned object to a temporary file, imports it, and deletes the temporary file in a
  `finally` block.
- **Retention:** no TTL index, archival rule or deletion policy is defined anywhere in the
  repository. See Section 11.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `PORT`, `HOST` | HTTP listener (defaults to port 3001) |
| `NODE_ENV`, `ENVIRONMENT`, `SERVICE_VERSION` | Runtime identity; `ENVIRONMENT` also selects the CDP environment used to build internal URLs |
| `MONGO_URI`, `MONGO_DATABASE` | MongoDB connection |
| `MONGO_RETRY_WRITES`, `MONGO_READ_PREFERENCE` | Mongo driver overrides |
| `CDP_UPLOADER_URL` | CDP Uploader base URL; defaults to the internal address for the current environment |
| `CDP_UPLOADER_S3_BUCKET`, `CDP_UPLOADER_S3_PREFIX` | Destination for scanned uploads |
| `CDP_UPLOADER_MAX_FILE_SIZE`, `CDP_UPLOADER_ALLOWED_MIME_TYPES` | Upload constraints enforced by the uploader |
| `CDP_X_API_KEY` | CDP API key — declared but not read by any runtime code, see Section 11 |
| `AWS_REGION`, `SQS_ENDPOINT` | SQS client region and endpoint (LocalStack locally) |
| `HTTP_PROXY` | CDP egress proxy |
| `TRACING_HEADER` | Name of the CDP request tracing header |
| `ENABLE_METRICS` | CloudWatch embedded metrics toggle |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |

For local development only, `src/config.js` additionally loads a `local.json` file when
`ENVIRONMENT` is `local`. That file is not present in the repository.

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`;
  production entrypoint `node src`.
- **Internal address:** `https://aqie-dc-backend.<env>.cdp-int.defra.cloud`. The callback URL
  registered with the CDP Uploader is derived from this pattern at runtime.
- **Gateway path:** reached externally through
  `https://ephemeral-protected.api.<env>.cdp-int.defra.cloud/aqie-dc-backend`, per the
  Postman collection held in `postman/`.
- **Environments:** `local`, `infra-dev`, `management`, `dev`, `test`, `perf-test`,
  `ext-test`, `prod` (enumerated in the config schema).
- **Local development:** `compose.yml` provides MongoDB, Redis and LocalStack. Redis appears
  only in the compose file — the service itself does not open a Redis connection.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — lint, test and quality gate on PR
  - `.github/workflows/publish.yml` — build and publish on push to `main`
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish
- **Operator scripts:** `npm run import:appliances`, `import:fuels`, `import:both`,
  `import:generate-templates` and `import:test` run the spreadsheet import directly against
  the database, bypassing the uploader.

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, formatted with `@elastic/ecs-pino-format` in
  production. Authorisation headers, cookies and response headers are redacted in production.
- **Tracing:** `@defra/hapi-tracing`, propagating the header named in `TRACING_HEADER`
  (default `x-cdp-request-id`).
- **Metrics:** `aws-embedded-metrics` (CloudWatch EMF), gated by `ENABLE_METRICS`.
- **Auditing:** `@defra/cdp-auditing` is a declared dependency.
- **Shutdown:** `hapi-pulse` for graceful draining; the SQS consumer aborts its long poll and
  destroys the SQS client on the server `stop` event.
- **API description:** `hapi-swagger` serves generated documentation, currently still carrying
  the CDP template title "Simple CRUD API for items".

## 11. Open Questions

- [ ] **The SQS queue is not in the integration catalogue.** Confirm that `aqie-dc-queue` is
      fed by the DEFRA Forms service and add the edge. The consumer keys on the form slug
      `get-a-solid-fuel-certified-for-use-in-smoke-control-areas`; anything else is treated as
      an appliance application.
- [ ] **The queue name is hardcoded** in `src/sqs/client.js` rather than read from config, and
      is not environment-qualified. Confirm whether every CDP environment really shares one
      queue name, and whether the config-driven alternative should be restored.
- [ ] **`CDP_X_API_KEY` is accepted but never checked.** Both frontends send an `x-api-key`
      header on every backend call, but no route in this service reads or validates it and no
      Hapi auth strategy is registered. Confirm whether the gateway enforces the key, or
      whether every route is effectively unauthenticated within the CDP network.
- [ ] **`/upload-callback` is explicitly `auth: false`** with a comment that uploader callbacks
      do not yet support auth. Confirm the compensating control that stops an arbitrary
      in-network caller from triggering a register import by posting a crafted callback naming
      a bucket and key of their choosing.
- [ ] `aqie-dc-frontend` calls `GET /get-all/{type}` and `GET /get/{type}/{id}`, which this
      service does not expose on `main`. Confirm whether the public frontend is currently
      broken against this backend, or whether it is pinned to an older deployment.
- [ ] The reviewer identity on `PATCH /applications/{id}/complete` and the technical review
      routes is supplied by the caller as a name and email. Confirm whether the backend should
      independently verify the caseworker's identity rather than trusting the frontend.
- [ ] Confirm the retention and archival policy for `SqsMessages`, which holds submitted
      applicant contact details indefinitely.
- [ ] The `xlsx` dependency is installed from `https://cdn.sheetjs.com/...tgz` rather than the
      npm registry, so it is outside normal registry auditing. Confirm this is a deliberate,
      reviewed decision.
- [ ] `src/config.js` carries a hardcoded default S3 bucket name for the dev environment.
      Confirm whether the default should instead be empty and required from configuration.
- [ ] `GET /example` and `/example/{exampleId}` are unremoved CDP template routes. Confirm
      they can be deleted.

