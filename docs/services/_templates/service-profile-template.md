# <service-name>

> One-line summary of what this service does and who it serves.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/<service-name>`](https://github.com/DEFRA/<service-name>) |
| Service domain | `Citizen` \| `Data` \| `Shared` |
| Service type | `<taxonomy value from repository-catalog.yaml>` |
| Lifecycle stage | `Production` \| `Beta` \| `Prototype/PoC` \| `Archived` |
| Primary language | `<language>` |
| Runtime | `<e.g. Node.js >=22, .NET 8>` |
| Default branch | `main` |
| Created (UTC) | `<YYYY-MM-DD>` |
| Last main commit (UTC) | `<YYYY-MM-DDTHH:MM:SSZ>` |
| Last analysed commit | `<sha>` |
| Last analysed (UTC) | `<YYYY-MM-DDTHH:MM:SSZ>` |
| Activity status | `Active` \| `Monitoring` \| `Inactive` |

## 2. Purpose and Responsibilities

**Does:**

- <responsibility>

**Does not:**

- <explicit scope boundary — what callers must go elsewhere for>

## 3. Architecture

- **Pattern:** <e.g. Hapi HTTP API + scheduled ingest workers>
- **Key components:**

| Component | Path | Responsibility |
|---|---|---|
| <name> | `src/...` | <what it does> |

## 4. API Surface

<Endpoints this service exposes. Omit the table if the service exposes none.>

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| `GET` | `/health` | Liveness probe | — | `{ message }` |

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| <service or external system> | `AQIE service` \| `External API` \| `Datastore` | `<path or protocol>` | <payload summary> | <mechanism, never values> |

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| <service> | `<path>` | <summary> |

> Inbound and outbound edges are mastered in `/docs/integration-catalog.yaml`.
> From a service profile, link to it as `../../../integration-catalog.yaml`.

## 7. Data

- **Stores:** <MongoDB collections, Redis usage, S3 buckets, etc.>
- **Key entities:** <domain objects and their shape at a summary level>
- **Retention / refresh:** <schedules, TTLs, cache windows>

## 8. Configuration

Environment variable **names** only — never record values.

| Variable | Purpose |
|---|---|
| `PORT` | HTTP listen port |

## 9. Hosting and Deployment

- **Platform:** <e.g. DEFRA CDP (AWS ECS Fargate)>
- **Container:** <base image, exposed port>
- **Environments:** <dev / test / perf-test / prod>
- **Pipelines:** <workflow files and triggers>

## 10. Observability

- **Logging:** <library and format>
- **Tracing:** <mechanism>
- **Metrics:** <mechanism>

## 11. Open Questions

- [ ] <item needing owner confirmation>
