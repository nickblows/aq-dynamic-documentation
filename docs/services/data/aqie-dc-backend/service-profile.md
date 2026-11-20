# aqie-dc-backend

> The system of record for smoke control domestic combustion. Holds the registers of exempt
> appliances and authorised fuels, receives applications submitted through DEFRA Forms, and
> serves the register, the caseworker technical review and certification workflow, and an audit
> history over an internal HTTP API.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-dc-backend`](https://github.com/DEFRA/aqie-dc-backend) |
| Service domain | `Data` |
| Service type | `Auxilary Backend Service` |
| Lifecycle stage | `Beta` |
| Primary language | JavaScript |
| Runtime | Node.js `>=24` (ES modules). `.nvmrc` pins `v24.11.1` for CI; the container parent image is `node24.22.1` |
| Default branch | `main` |
| Created (UTC) | `2026-01-26` |
| Last main commit (UTC) | `2026-11-17T13:57:09Z` |
| Last analysed commit | `49f950cd` |
| Last analysed (UTC) | `2026-11-19T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

Domestic combustion ("DC") is the smoke control regime: appliances that may lawfully be used
in a smoke control area, and fuels that may lawfully be burned in one. This service owns that
data and the process that decides what goes into it.

**Does:**

- Holds the **appliance register** — manufacturer, model, appliance type (including "other"
  types), variant relationships, nominal thermal output, multifuel capability, permitted fuels,
  additional conditions, instruction manual details, caseworker-entered test results, and the
  separate certification status for England, Scotland, Wales and Northern Ireland. Each
  appliance carries a derived overall status (`pending`, `live`, `hidden` or `rejected`) and a
  public visibility switch. Records migrated from the legacy register are flagged
  `isLegacyRecord` and carry a `legacy` block.
- Holds the **fuel register** — manufacturer or rebrander, responsible person, brand names,
  supplier type (Manufacture or Rebrand), fuel description and composition, sulphur content,
  manufacturing process and quality control, bagging and complaints handling, rebrand lineage
  (original manufacturer, original name, what changed), test results, and the same four country
  certification blocks, derived status and visibility switch.
- Receives appliance and fuel applications from the DEFRA Forms service by polling an AWS SQS
  queue, stores each raw message, maps the opaque form field identifiers into domain fields, and
  creates the application and its linked appliance or fuel items. A message leaves the queue only
  once it has been handled.
- Runs the **application lifecycle**: an application is created as `new`, moved to
  `in_progress` when a caseworker starts it, and only moves to `complete` once every linked
  item has reached a final technical review outcome. Completion records each item's outcome,
  moves accepted items' undecided countries to `awaiting_decision` and re-derives each item's
  overall status.
- Runs the **technical review workflow** for each item. Appliances: four documentation checks
  (test reports, technical drawings, conformity mark, instruction manual) and three listing
  checks (appliance details, permitted fuels, additional conditions). Fuels: two documentation
  checks (manufacturer letter, test results) and two listing checks (fuel details, fuel
  description), of which the required set depends on the supplier type. The first recorded check
  moves an item from `new` to `in_review`. An item cannot be accepted until every required
  check has passed; it can be rejected at any point.
- Records **country certification decisions** for appliances (certify or uncertify, with the
  deciding user) and recalculates the appliance status. Decisions are entered by caseworkers on
  behalf of the four administrations.
- Lets a caseworker show or hide an accepted, certified appliance on the public list.
- Keeps an **audit history** of review outcomes, certification decisions, public list changes
  and, for migrated records, legacy events. It is readable per appliance, newest first.
- Provides read routes for the public register (lists return `live` items only) and for
  caseworkers: case counts, applications grouped by status, per-application item summaries and
  an admin appliance search and detail view.
- Starts CDP Uploader sessions and proxies the upload, and polls upload status, for bulk
  register imports. The service no longer processes the scanned file — see Section 11. Loading
  legacy register data is now an operator-run command line import.
- Publishes an OpenAPI description of its own routes via `hapi-swagger`.

**Does not:**

- Render any user interface. The public register is presented by `aqie-dc-frontend`; the
  caseworker screens are `aqie-dc-admin-frontend`.
- Collect applications from applicants. Application capture is done by the DEFRA Forms
  service; this service only consumes the resulting submission messages.
- Authenticate or authorise anyone. No route is protected and no Hapi authentication strategy
  is registered. Caseworker identity is established by `aqie-dc-admin-frontend` against
  Microsoft Entra ID and passed to this service only as a `reviewedBy` or `decidedBy` name and
  email on the payload, which is trusted — see Section 11.
- Scan uploaded files for malware. That is the platform's CDP Uploader.
- Hold any air quality measurement, forecast or monitoring station data — that is
  `aqie-back-end`, `aqie-forecast-api` and `aqie-monitoringstation-backend`. Domestic
  combustion shares no data with the air quality reporting estate.
- Send notifications. There is no GOV.UK Notify or `aqie-notify-service` integration in this
  repository. The email to the devolved administrations that completing an application is meant
  to trigger is a stub that writes a log line only.
- Take decisions from the devolved administrations directly. The emailed decision link is not
  built; caseworkers (the code comments name HETAS as the reviewing body) record decisions on
  their behalf.

## 3. Architecture

**Pattern:** Hapi HTTP API with a long-polling AWS SQS consumer registered as a Hapi plugin in
the same process (registered last, started on the server `start` event). The consumer creates
applications by re-entering the service's own `POST /applications` route through
`server.inject`, so ingest and API writes share one validation path. It stores and updates the
raw message record by calling the SQS message controller directly, not through a route.
Controllers hold all MongoDB access; routes validate input with Joi and map results to status
codes through a shared handler.

| Component | Path | Responsibility |
|---|---|---|
| Server composition | `src/server.js` | Registers Swagger, request logging and tracing, secure context, graceful shutdown, the Mongo plugin, the router and, last, the SQS consumer |
| Router | `src/plugins/router.js` | Wires all route modules and hosts the CDP Uploader proxy route |
| Appliance routes | `src/routes/appliances/` | Appliance CRUD, admin search and detail, technical review read and write, per-check recording, certification decision, public visibility, action history |
| Appliance type route | `src/routes/appliance-types/` | Lookup of appliance types, optionally by primary flag |
| Fuel routes | `src/routes/fuels/` | Fuel CRUD, search, technical review read and write, per-check recording |
| Application routes | `src/routes/applications/` | Application creation, listing, counts, search, summaries and lifecycle transitions |
| Admin import | `src/routes/admin-import.js` | Initiates an upload session with the CDP Uploader and polls its status |
| SQS message route (unregistered) | `src/routes/sqs-messages/` | Dead code: the route module is not registered by the router |
| SQS consumer plugin | `src/plugins/sqs-consumer.js` | Background polling loop, interval from configuration, `AbortController` tied to server shutdown |
| SQS client | `src/sqs/client.js` | Resolves the queue URL, long-polls, handles each message, deletes only handled messages in a batch, decides appliance or fuel |
| SQS field mapper | `src/sqs/mapper.js` | Translates DEFRA Forms field identifiers into domain field names for appliances and fuels |
| SQS repeater splitter | `src/sqs/repeater.js` | Splits a multi-appliance submission into one item per appliance |
| SQS dispatcher | `src/sqs/dispatcher.js` | Calls `POST /applications` via `server.inject`; stores and marks message records through the controller |
| Controllers | `src/controllers/` | Appliances, fuels, applications, appliance and fuel review, application review (start and complete), appliance certification, action history, appliance types and SQS messages |
| Schemas | `src/common/schemas/` | Joi definitions for appliance, fuel, application and audit action, plus payload schemas for test reports, instruction manual, fuel test results and fuel description |
| Status rules | `src/common/helpers/item-status.js`, `review-status.js`, `certification.js` | Check groups and when an item or application is review-complete; derives the overall item status from review, country certification and visibility; country certification statuses and transitions |
| Audit helper | `src/common/helpers/action-history.js` | Appends an entry to the `Actions` collection; failures are logged and never block the change |
| Uploader helper | `src/common/helpers/cdp-uploader.js` | Builds the initiate payload, including the callback URL, and polls a status URL |
| Mongo plugin | `src/common/helpers/mongodb.js` | Connects, creates indexes and, on first start, creates the register, application and appliance type collections |
| Import tooling | `src/migrations/excel-importer.js`, `import-cli.js`, `src/common/helpers/entity-config.js` | Operator-run command line import of a legacy spreadsheet (`exceljs`); field mapping lives in `entity-config.js` |
| Config | `src/config.js` | `convict` schema for all endpoints, buckets, queue and connection details |

## 4. API Surface

The service registers 38 routes in `src/plugins/router.js`, plus the documentation routes that
`hapi-swagger` adds. **No route is authenticated or authorised.** No Hapi authentication
strategy is registered, `CDP_X_API_KEY` is never read, and the only `auth` setting in the code
is an explicit `auth: false` on the uploader proxy route. The gateway strips the
`/aqie-dc-backend` prefix before requests reach the service, which is why the uploader proxy
route is registered at the bare path. Not-found results return `404`; an action refused because
its preconditions are not met (for example completing an application before every item is
reviewed) returns `409`.

**Appliance register**

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/appliances` | Public list: appliances whose status is `live` | — | Summaries: name, id, manufacturer, permitted fuels, type, model number, countries certified in |
| `GET` | `/appliances/{id}` | One appliance, the whole stored record, whatever its status | `id` | Record plus countries certified in, name, manufacturer and full address |
| `POST` | `/appliances` | Create an appliance; validation problems are logged, not rejected | Appliance payload | `id` of the created appliance (`201`) |
| `PATCH` | `/appliances/{id}` | Update appliance fields; technical review, country certification, visibility and status fields are refused | Partial appliance payload | Updated appliance |
| `DELETE` | `/appliances/{id}` | Remove an appliance | `id` | Deletion outcome |
| `GET` | `/appliance-types` | Appliance types, filtered by the primary flag | `isPrimary` (required) | Array of types |
| `GET` | `/admin/appliances/search` | Admin search; only appliances from completed applications or legacy records | Optional `q` (up to 50 characters), comma-separated `status`, `page`, `limit` (up to 100) | Id, name and status per appliance, with pagination |
| `GET` | `/admin/appliances/{id}` | Admin view of one appliance | `id` | Model name and number, application id, certification per country, overall status, whether visibility can be changed, visibility, technical review, manuals, legacy block |
| `GET` | `/api/admin/appliances/{id}/action-history` | Audit history, newest first | `id`, `page` | Ten entries per page (id, description, who, when) with pagination |
| `PATCH` | `/appliances/{id}/certification/{country}` | Record a country decision; `country` is `england`, `scotland`, `wales` or `northern-ireland`. Allowed moves: `awaiting_decision` to either outcome, `certified` and `uncertified` either way | `certified` or `uncertified`, and `decidedBy` name and email | Updated appliance with recalculated status |
| `PATCH` | `/appliances/{id}/visibility` | Show or hide on the public list. Refused (`409`) unless the technical review is accepted and the appliance is certified in at least one country | `isVisibleToPublic`, `reviewedBy` | Success flag |

**Fuel register**

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/fuels` | Public list: fuels whose status is `live` | — | Summaries: name, id, manufacturer, countries certified in, last certified date |
| `GET` | `/fuels/{fuelId}` | One fuel, the whole stored record, whatever its status | `fuelId` | Record plus countries certified in, last certified date, name, manufacturer and full address |
| `GET` | `/api/fuels/search` | Search by brand name, additional brand names or company. Not filtered by status | `q` (2 to 50 characters), `page`, `limit` | Fuel summaries with pagination |
| `POST` | `/fuels` | Create a fuel; validation problems are logged, not rejected | Fuel payload | `fuelId` of the created fuel (`201`) |
| `PATCH` | `/fuels/{fuelId}` | Update fuel fields, including partial fuel description and rebrand lineage; status fields are refused | Partial fuel payload | Updated fuel |
| `DELETE` | `/fuels/{fuelId}` | Remove a fuel | `fuelId` | Deletion outcome |

**Application and case lifecycle**

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `POST` | `/applications` | Create an application with its linked items in one transaction, falling back to direct writes where transactions are unavailable. Validation problems become warnings and never block | Application payload | Created application (`201`), with `validationWarnings` when there are any |
| `GET` | `/applications` | Every application, newest first | — | Application collection |
| `GET` | `/applications/counts` | Dashboard counts for appliances and fuels: new, in progress, and completed records | — | Counts |
| `GET` | `/applications/search` | Search by status, reviewer or id | `q` (2 to 50 characters), `page`, `limit` | Matching applications with pagination |
| `GET` | `/applications/summary-by-status` | Uncompleted applications of one type, as `new` and `inProgress`, with linked item names | `type` (`appliance` or `fuel`) | Two arrays of applications with items |
| `GET` | `/applications/{applicationId}` | One application with its items; `groupBy=techReviewStatus` returns the items split into accepted and rejected and says whether review is complete. Falls back to a legacy record lookup | `applicationId`, optional `groupBy` | Application with linked items |
| `GET` | `/applications/{applicationId}/summary` | Company and contact details and each item's technical review state | `applicationId`, `type` (required) | Company, contact and item review statuses |
| `PATCH` | `/applications/{id}/in-progress` | Mark the case as started by a caseworker | `reviewedBy` name and email | Status, reviewer, time |
| `PATCH` | `/applications/{id}/complete` | Close the case once every item is accepted or rejected (`409` otherwise) | `reviewedBy` name and email | Status, reviewer, time |

**Technical review**

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/appliances/{id}/technical-review` | Review state and outstanding checks for one appliance | `id` | The fields the review screens need, plus outstanding check names |
| `PATCH` | `/appliances/{id}/technical-review` | Accept or reject. Accepting is refused (`409`) until every check has passed | `accepted` or `rejected`, optional `reviewedBy` | Id, status, time |
| `PATCH` | `/appliances/{id}/technical-review/checks` | Record one check result, optionally with the field values it confirms (permitted fuels, additional conditions, test reports, instruction manual) | Check name, result, optional data | Id, check, result |
| `GET` | `/fuels/{fuelId}/technical-review` | Review state and outstanding checks for one fuel, without contact details | `fuelId` | The fields the review screens need, plus outstanding check names |
| `PATCH` | `/fuels/{fuelId}/technical-review` | Accept or reject a fuel, on the same rule | `accepted` or `rejected`, optional `reviewedBy` | Fuel id, status, time |
| `PATCH` | `/fuels/{fuelId}/technical-review/checks` | Record one fuel check; test results are required with the test results check; a check that does not apply to the supplier type is refused | Check name, result, optional data | Fuel id, check, result |

**Import, upload and platform**

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `POST` | `/admin/import/initiate` | Starts a CDP Uploader session for a register import | `entities`: `appliances` and or `fuels` | `uploadId`, upload URL (prefixed with the service name outside local), status URL |
| `GET` | `/admin/import/status` | Polls whatever URL it is given for upload and scan progress | `statusUrl` (any URI) | Uploader status |
| `POST` | `/upload-and-scan/{uploadId}` | Streams the file straight through to the CDP Uploader (`auth: false`) | File stream up to `CDP_UPLOADER_MAX_FILE_SIZE` | Uploader response |
| `GET` | `/health` | Liveness probe | — | `{ message }` |
| `GET` | `/example`, `/example/{exampleId}` | CDP template scaffolding, not domain routes | — | Example payload |

> `/appliances/{id}/technical-review/checks` and its fuel equivalent are the only write paths
> the caseworker screens use for check results. Where a check carries field values, the backend
> writes those values and the check result in a single update, so the two cannot drift apart.
> The decision routes derive the item's overall status afterwards.

> No longer served: `POST /upload-callback` and `POST /sqs-messages` (removed or unregistered),
> `GET /templates/{file*}`, `GET /applications/summary` (now `summary-by-status`) and
> `GET /api/appliances/search` (now `GET /admin/appliances/search`, which is not public).
> `aqie-dc-frontend` calls `/get-all/{type}` and `/get/{type}/{id}`, which this service does not
> serve — see Section 11.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| CDP Uploader | Platform service | `POST /initiate` | Bucket, prefix, callback URL, allowed MIME types, size limit and entity metadata out; `uploadId`, upload URL and status URL back | Platform-internal network |
| CDP Uploader | Platform service | `POST /upload-and-scan/{uploadId}` (proxied from the caller) | File stream passed through unparsed | Platform-internal network |
| CDP Uploader | Platform service | `GET` of the status URL supplied by the caller | Upload and scan progress | Platform-internal network |
| AWS SQS | Datastore / queue | Long poll of the queue named by `AWS_SQS_QUEUE_NAME` (default `aqie-dc-queue`): up to 10 messages, 10 second wait, one poll per interval (default 15 minutes); batch delete of handled messages | DEFRA Forms submissions in; handled messages deleted | IAM task role |
| MongoDB | Datastore | Driver connection | Appliances, fuels, applications, consumed messages, audit actions, appliance types | `MONGO_URI` |

The service no longer reads from AWS S3: the object read and the scan-outcome callback were
removed on 2026-10-27. The bucket named in configuration is the uploader's destination only.

**Evidence:** `src/sqs/client.js` (queue lookup lines 34-42, receive 47-57, delete 129-136),
`src/plugins/sqs-consumer.js` (interval 11-31), `src/config.js` (lines 182-210) for the queue
and `src/common/helpers/cdp-uploader.js` (lines 53 and 81) for the only outbound HTTP calls.
The consumer only receives and deletes; no send command exists.

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| `aqie-dc-admin-frontend` | 21 method and path pairs, all served: `GET /applications/counts`, `GET /applications/summary-by-status?type=`, `GET /applications/{id}` (also with `groupBy=techReviewStatus`), `GET /applications/{id}/summary?type=`, `PATCH /applications/{id}/in-progress`, `PATCH /applications/{id}/complete`, `GET /admin/appliances/search`, `GET /admin/appliances/{id}`, `GET /api/admin/appliances/{id}/action-history`, `GET /appliances/{id}`, `PATCH /appliances/{id}`, `GET` and `PATCH /appliances/{id}/technical-review`, `PATCH /appliances/{id}/technical-review/checks`, `PATCH /appliances/{id}/certification/{country}`, `PATCH /appliances/{id}/visibility`, `GET /appliance-types`, `PATCH /fuels/{fuelId}`, `GET` and `PATCH /fuels/{fuelId}/technical-review`, `PATCH /fuels/{fuelId}/technical-review/checks` | Case lists and counts, appliance and fuel records, review state, check results, certification and visibility decisions, reviewer identity. Only `GET` and `PATCH` are used |
| `aqie-dc-frontend` | `GET /get-all/{type}`, `GET /get/{type}/{id}` | Register listings and single register entries — **but these paths are not served by the current `main`**, see Section 11 |
| CDP Uploader | Previously `POST /upload-callback` | The callback route no longer exists, but initiate still registers its URL — see Section 11 |
| DEFRA Forms (indirectly) | AWS SQS queue `aqie-dc-queue` | Appliance and fuel certification applications |

No caller was found for the import routes, the upload proxy, `POST` and `DELETE` routes,
`GET /applications`, `GET /applications/search`, `GET /appliances`, `GET /fuels` or
`GET /api/fuels/search`.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Store:** MongoDB (`MONGO_DATABASE`, default `aqie-dc-backend`), with `mongo-locks`
  available for distributed locking. It is the only datastore the service reads and writes.
  Redis appears only in `compose.yml` and the service opens no Redis connection; SQS is a queue
  the service consumes; the service has no S3 client.
- **Collections** (the register, application and appliance type collections are created on
  first start if missing; unique indexes on `id`, an index on application `status`, and
  indexes on the audit history by item and time):
  - `Appliances` — one document per appliance model under consideration or certified.
  - `Fuels` — one document per authorised or applied-for fuel.
  - `Applications` — the case wrapper; `type` is `appliance` or `fuel` and determines which
    collection holds its items.
  - `SqsMessages` — one record per consumed submission, keyed by SQS message id: the raw form
    body, when it was sent and received, whether it has been processed, and on failure the
    reason and time or any validation warnings.
  - `Actions` — the audit history of appliances and fuels.
  - `ApplianceTypes` — appliance type values with a primary flag. The collection is created
    empty; nothing in the repository populates it.
- **Identifiers:** applications, appliances and fuels share one format — a four-digit random
  prefix, a hyphen and a sequence number continuing from the last record. The id also serves as
  the display identifier.
- **Key entities:**
  - *Application* — `type`, server-generated `id`, DEFRA Forms `referenceNumber` and
    `submittedAt`, `status` (`new` | `in_progress` | `complete`), `reviewedBy` and
    `reviewedAt`. Items point back to it by `applicationId`.
  - *Appliance* — applicant company name, UK or overseas address (UK addresses may carry a
    UPRN from the form's address finder), contact name, email, optional alternative email and
    a validated UK or international phone number, model name and number, appliance type and
    "other" appliance type, variant flag and the appliance it varies from, nominal output in
    kW, multifuel flag, permitted fuels, whether wood may be burned, declaration,
    caseworker-entered test results (rated output, tested output and smoke emission output at
    rated and low), additional conditions, instruction manual details, legacy servicing
    manual details, a `legacy` block (comments, legacy appliance and application ids,
    linked application ids), the `technicalReview` block, four independent country
    certification blocks, `isVisibleToPublic` (default true), `isLegacyRecord`, and the
    derived `applianceStatus`.
  - *Fuel* — applicant company and contact details, responsible person, fuel bagging,
    complaints system flag, supplier type (`Manufacture` or `Rebrand`), brand name and
    additional brand names, rebrand lineage (original manufacturer, original name, whether
    changed or mixed, what changed), fuel description (appearance, weight, composition,
    sulphur content), manufacturing process and quality control, caseworker-entered test results
    (smoke emission and sulphur content), declaration, the same `technicalReview`,
    certification, visibility and legacy flags, and the derived `fuelStatus`.
  - *Technical review* — `status` (`new`, `in_review`, `accepted`, `rejected`), who decided
    and when, and a `true`, `false` or `null` (not yet reviewed) result for each documentation
    and listing check.
  - *Country certification* — `status` (`new`, `awaiting_decision`, `certified`,
    `uncertified`), who decided it and when, and the first and last certification dates.
    England, Scotland, Wales and Northern Ireland are tracked separately because the four
    administrations certify independently. The API reports `new` as `awaiting_decision`.
  - *Overall item status* — `pending`, `live`, `hidden` or `rejected`, recalculated whenever a
    review decision, certification decision, visibility change or application completion
    occurs. Rejected review gives `rejected`; any certified country gives `live`, or `hidden`
    if the item has been hidden from the public; no certified country but at least one
    uncertified gives `hidden`; all countries undecided gives `pending`.
  - *Audit action* — an append-only record with a generated id, the item, the action, a
    description, the country where relevant, who did it (a user, the system or a government)
    and when. Written for review outcomes at application completion, the "sent to
    governments" step, certification decisions made on behalf of an administration, changes
    onto or off the public list, and migrated legacy events. A failure to write an entry is
    logged and never blocks the change it describes.
- **Refresh:** event-driven. There are no cron schedules. New data arrives either from the SQS
  poll (one poll per interval, default every 15 minutes, with a ten second long poll and at
  most ten messages) or from an operator running the command line import.
- **Legacy import:** `src/migrations/import-cli.js` reads a local `.xlsx` file and upserts
  appliances (or fuels) by identifier. The appliance mapping marks records `isLegacyRecord`,
  fills the `legacy` block, derives certification per country and seeds audit entries from the
  legacy dates. The fuel mapping still produces the earlier field names (`fuelId`,
  `manufacturerName`, `fuelName`) and does not match the current fuel schema.
- **Uploads:** files are written by the CDP Uploader to `CDP_UPLOADER_S3_BUCKET` under
  `CDP_UPLOADER_S3_PREFIX`, limited to 10 MB and to Excel MIME types. The service no longer
  reads or deletes them.
- **Retention:** no TTL index, archival rule or deletion policy is defined anywhere in the
  repository. `SqsMessages` keeps the raw submission, including applicant contact details, and
  `Actions` keeps reviewer names and emails, both indefinitely. See Section 11.

## 8. Configuration

Variable names only — values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `PORT`, `HOST` | HTTP listener. The config default is port 3001; the container image sets `PORT` to 3000 unless overridden |
| `NODE_ENV`, `ENVIRONMENT`, `SERVICE_VERSION` | Runtime identity; `ENVIRONMENT` also selects the CDP environment used to build internal URLs |
| `MONGO_URI`, `MONGO_DATABASE` | MongoDB connection |
| `MONGO_RETRY_WRITES`, `MONGO_READ_PREFERENCE` | Mongo driver overrides |
| `CDP_UPLOADER_URL` | CDP Uploader base URL; defaults to the internal address for the current environment |
| `CDP_UPLOADER_S3_BUCKET`, `CDP_UPLOADER_S3_PREFIX` | Destination the uploader writes scanned uploads to; the bucket default is a hardcoded development bucket name |
| `CDP_UPLOADER_MAX_FILE_SIZE`, `CDP_UPLOADER_ALLOWED_MIME_TYPES` | Upload constraints enforced by the uploader and by the proxy route's payload limit |
| `CDP_X_API_KEY` | CDP API key — declared but not read by any runtime code, see Section 11 |
| `AWS_REGION` | SQS client region |
| `AWS_SQS_ENDPOINT` | SQS endpoint; defaults to a LocalStack address, so a deployed environment must override it (renamed from `SQS_ENDPOINT`) |
| `AWS_SQS_QUEUE_NAME` | Queue to consume; default `aqie-dc-queue` |
| `AWS_SQS_POLL_INTERVAL_MINUTES` | Wait between polls; default 15, must be a positive number |
| `HTTP_PROXY` | CDP egress proxy |
| `TRACING_HEADER` | Name of the CDP request tracing header |
| `ENABLE_METRICS` | CloudWatch embedded metrics toggle (nothing currently emits a metric) |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT` | Logging |

For local development only, `src/config.js` additionally loads a `local.json` file when
`ENVIRONMENT` is `local`. That file is not present in the repository. `compose.yml` also sets
`LOCALSTACK_ENDPOINT` and the LocalStack placeholder AWS credential variables; the service does
not read `LOCALSTACK_ENDPOINT`.

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS.
- **Container:** multi-stage build from `defradigital/node-development` to `defradigital/node`
  (parent image `3.2.4-node24.22.1`); production entrypoint `node src`; `npm ci --omit=dev`, so
  development dependencies such as `exceljs` are not in the production image.
- **Internal address:** `https://aqie-dc-backend.<env>.cdp-int.defra.cloud`. The callback URL
  registered with the CDP Uploader is derived from this pattern at runtime.
- **Gateway path:** reached externally through
  `https://ephemeral-protected.api.<env>.cdp-int.defra.cloud/aqie-dc-backend`, per the
  Postman collection held in `postman/` (the collection's request list is out of date).
- **Environments:** `local`, `infra-dev`, `management`, `dev`, `test`, `perf-test`,
  `ext-test`, `prod` (enumerated in the config schema).
- **Local development:** `compose.yml` provides MongoDB, Redis and LocalStack. Redis appears
  only in the compose file — the service itself does not open a Redis connection.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` — on pull requests to `main` or `minimal`: format
    check, lint, tests, `npm audit` at critical level, a Docker build and the SonarCloud scan
  - `.github/workflows/publish.yml` — on push to `main`: tests, then build and publish with the
    CDP build action, then SonarCloud
  - `.github/workflows/publish-hotfix.yml` — manual hotfix publish
- **Operator tooling:** `node src/migrations/import-cli.js --file <path> --type
  <appliances|fuels|both>` imports a legacy spreadsheet straight into the database, bypassing
  the uploader. There are no npm scripts for it.

## 10. Observability

- **Logging:** `pino` via `hapi-pino`, formatted with `@elastic/ecs-pino-format` in
  production. Authorisation headers, cookies and response headers are redacted in production;
  `/health` requests are not logged.
- **Tracing:** `@defra/hapi-tracing`, propagating the header named in `TRACING_HEADER`
  (default `x-cdp-request-id`).
- **Metrics:** `aws-embedded-metrics` (CloudWatch EMF), gated by `ENABLE_METRICS`. A counter
  helper exists but no code calls it.
- **Auditing:** business actions are recorded in the `Actions` collection (Section 7).
  `@defra/cdp-auditing` is a declared dependency that is not imported.
- **Shutdown:** `hapi-pulse` for graceful draining; the SQS consumer aborts its long poll and
  destroys the SQS client on the server `stop` event.
- **API description:** `hapi-swagger` serves generated documentation, currently still carrying
  the CDP template description "Simple CRUD API for items".

## 11. Open Questions

- [ ] **The public register is still not served (`oq-006`, high).** `aqie-dc-frontend` calls
      `GET /get-all/{type}` and `GET /get/{type}/{id}`; this service registers neither, and has
      no catch-all route (re-verified 2026-11-19 at `49f950cd`; the frontend is unchanged since
      April). The nearest routes, `GET /appliances` and `GET /fuels`, return `live` items only
      and the appliance summary has `permittedFuels` where the frontend reads `fuels`, so
      changing only the paths would not fix the appliance list. The public appliance search
      (`/api/appliances/search`) no longer exists. Confirm whether the public register is
      broken in every environment, and which side will change.
- [ ] **Is the web import flow meant to be retired?** (catalogue `oq-025`) The scan-outcome callback and the S3 read
      were removed on 2026-10-27, but `POST /admin/import/initiate` still registers a callback
      URL that no longer exists, so an upload started through it is scanned and stored but never
      imported or cleaned up. Neither frontend calls the import routes. Remove the three
      import and proxy routes, or restore a handler?
- [ ] **`GET /admin/import/status` fetches whatever URL it is given** and returns the JSON it
      receives; the only check is that the value is a URI. Confirm it should be limited to the
      uploader host, or removed with the flow above.
- [ ] **The email to the devolved administrations is not built.** (catalogue `oq-024`) Completing an application
      writes a "Sent to governments for approval" history entry and moves each accepted item's
      undecided countries to `awaiting_decision`, but the send is a log line only. How will
      the administrations be told to decide, and by what mechanism (GOV.UK Notify would make
      the refuted Notify edge real)?
- [ ] **How does a fuel become `live`?** (catalogue `oq-026`) Appliances have certification and visibility routes;
      fuels have neither, and `PATCH /fuels/{fuelId}` refuses status fields. Until that exists,
      `GET /fuels` returns only fuels that were `live` by other means.
- [ ] **The fuel legacy import mapping is out of date.** It still produces `fuelId`,
      `manufacturerName` and `fuelName`, which do not match the current fuel schema or routes.
      Is the fuel migration planned?
- [ ] **Queue configuration after the rename.** (catalogue `oq-027`) The endpoint variable is now `AWS_SQS_ENDPOINT`
      (was `SQS_ENDPOINT`) and defaults to a LocalStack address. Confirm every CDP environment
      was updated and that `AWS_SQS_QUEUE_NAME` is correct for each. Confirm too that a
      15 minute default (was 5) is intended: at most ten messages are handled per poll and the
      loop sleeps the whole interval even when more are waiting.
- [ ] **Dead-letter handling.** (catalogue `oq-027`) Failed messages are now left on the queue rather than deleted.
      Confirm the queue has a redrive policy or dead-letter queue and an alert; neither is
      visible in this repository.
- [ ] **`CDP_X_API_KEY` is accepted but never checked.** (catalogue `oq-022`) Both frontends send an `x-api-key`
      header on every backend call, but no route in this service reads or validates it and no
      Hapi auth strategy is registered. Confirm whether the gateway enforces the key, or
      whether every route is effectively unauthenticated within the CDP network.
- [ ] **Reviewer and decision identity is trusted.** `reviewedBy` and `decidedBy` (name and
      email) come from the request body on the application, technical review, visibility and
      certification routes and are written into the audit history. Should the backend verify
      the caseworker independently of the frontend?
- [ ] **Unused write and delete routes are open.** `DELETE /appliances/{id}`,
      `DELETE /fuels/{fuelId}`, `POST /appliances` and `POST /fuels` are used by neither
      frontend (the admin client issues only `GET` and `PATCH`). Can they be removed?
- [ ] **By-id reads return the whole record.** `GET /appliances/{id}` and `GET /fuels/{fuelId}`
      ignore item status and include applicant contact details. Before the public frontend is
      repointed, confirm a public projection that excludes both.
- [ ] Confirm the retention and archival policy for `SqsMessages` (raw submissions, including
      applicant contact details) and `Actions` (reviewer names and emails), both kept
      indefinitely.
- [ ] Nothing in the repository populates `ApplianceTypes`. Who does, and does
      `GET /appliance-types` return an empty list until then?
- [ ] `src/config.js` carries a hardcoded default S3 bucket name for the dev environment, and
      the service no longer reads S3. Confirm the default can be empty or removed.
- [ ] `GET /example` and `/example/{exampleId}` are unremoved CDP template routes, and the
      Swagger description still reads "Simple CRUD API for items". Confirm they can be deleted
      or updated.
- [ ] Several production dependencies are declared but never imported (`@aws-sdk/client-s3`,
      `@aws-sdk/credential-providers`, `@defra/cdp-auditing`, `aws4`, `date-fns`,
      `google-libphonenumber`, `https-proxy-agent`, `node-fetch`), and the metrics helper has
      no caller. Confirm they can be removed.
