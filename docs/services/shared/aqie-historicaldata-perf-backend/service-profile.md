# aqie-historicaldata-perf-backend

> A March 2025 fork of `aqie-historicaldata-backend`, created so that performance testing could
> run against a disposable copy of the historic data API. Archived within weeks.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-historicaldata-perf-backend`](https://github.com/DEFRA/aqie-historicaldata-perf-backend) |
| Service domain | `Shared` |
| Service type | `Quality/Test Service` |
| Lifecycle stage | `Archived` |
| Primary language | C# |
| Runtime | .NET 8 (ASP.NET Core minimal API) |
| Default branch | `main` |
| Created (UTC) | `2025-03-17` |
| Last main commit (UTC) | `2025-03-27T10:27:22Z` |
| Last analysed commit | `8af8680` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Archived` |

## 2. Purpose and Responsibilities

> **Archived.** A performance-test copy of `aqie-historicaldata-backend`. Not superseded — the
> service it copied is still live. Retained for historical reference. Do not deploy.

**The `*-perf-*` pattern.** This is one of four throwaway forks created within two hours of
each other on 17 March 2025 so that load could be driven without touching shared environments;
the others are `aqie-location-perf-backend`, `aqie-monitorstation-perf-backend` and
`aqie-dataselector-perf-frontend`. See
[`aqie-location-perf-backend`](../aqie-location-perf-backend/service-profile.md) for the full
description of the pattern.

**Does:**

- Reproduces the hourly historic data slice of `aqie-historicaldata-backend` as it stood in
  March 2025: Atom feed endpoints serving hourly pollutant measurements, with S3 used for
  generated extracts and Hangfire for background jobs.

**Does not:**

- Cover the full production surface. The production service exposes the data selection and
  emailed-extract endpoints (`AtomDataSelection*`, `AtomEmailJobDataSelection`,
  `AtomHistoryexceedence` and others); this fork has only the hourly data endpoints plus a
  health check. Those features were added to the production service after the fork was taken,
  so this repository is a useful snapshot of the March 2025 state.
- Contain any load-testing harness, scenario definitions or results.

## 3. Architecture

- **Pattern:** ASP.NET Core minimal API with endpoint classes, Hangfire background jobs
  (in-memory storage), MongoDB for reference data and S3 for extract files.

| Component | Path | Responsibility |
|---|---|---|
| Atom endpoints | `AqieHistoricaldataPerfBackend/Atomfeed/Endpoints/` | Route registration |
| Atom services | `AqieHistoricaldataPerfBackend/Atomfeed/Services/` | Measurement retrieval, CSV generation, S3 upload |
| Mongo client | `AqieHistoricaldataPerfBackend/Utils/Mongo/` | MongoDB connection factory |
| Tests | `AqieHistoricaldataPerfBackend.Test/` | xUnit tests using an ephemeral MongoDB |

## 4. API Surface

| Method | Path | Purpose |
|---|---|---|
| `GET` | `AtomHistoryHealthchecks` | Liveness probe |
| `GET` \| `POST` | `AtomHistoryHourlydata` | Hourly historic pollutant measurements |
| `GET` | `AtomHistoryHourlydata/{name}` | Hourly data for a named station |
| `GET` \| `POST` | `example`, `example/{name}` | Unmodified CDP template routes |

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| DEFRA UK-AIR | External | `https://uk-air.defra.gov.uk/` | Historic measurement source referenced from start-up configuration | Not recorded in the repository |
| EIONET vocabulary | External (reference) | `dd.eionet.europa.eu/vocabulary/aq/pollutant/*` | Pollutant identifier URIs embedded in Atom feed output | None |
| AWS S3 | Datastore | SDK | Generated CSV extracts | IAM role |
| MongoDB | Datastore | Driver connection | Reference data | Connection string from `appsettings` |

## 6. Consumed By (Inbound Dependencies)

None recorded. `aqie-dataselector-perf-frontend` points at the **production**
`aqie-historicaldata-backend` host, not at this fork.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** MongoDB for reference data; AWS S3 for generated extract files.
- **Key entities:** hourly pollutant measurements by station and pollutant.
- **Retention / refresh:** none defined in the repository. Hangfire uses in-memory storage, so
  job state is lost on restart.

## 8. Configuration

Configuration is held in `appsettings.json` and `appsettings.Development.json` rather than
environment variables. Keys cover the MongoDB connection, the UK-AIR source, the S3 bucket and
Serilog logging levels. No secret values are committed.

## 9. Hosting and Deployment

- **Platform:** DEFRA CDP on AWS ECS, intended for the `perf-test` environment.
- **Container:** multi-stage build from `mcr.microsoft.com/dotnet/sdk:8.0` to
  `mcr.microsoft.com/dotnet/aspnet:8.0`; ports 80, 443 and 8085 exposed.
- **Pipelines:** the standard CDP set for .NET — `check-pull-request.yml`, `publish.yml`,
  `publish-hotfix.yml`, plus a reusable `sonarcloud.yml`.

## 10. Observability

- **Logging:** Serilog with `Elastic.CommonSchema.Serilog` formatting and client, environment
  and request enrichers.
- **Tracing:** header propagation via `Microsoft.AspNetCore.HeaderPropagation`.
- **Metrics:** none beyond platform defaults.

## 11. Open Questions

- [ ] Where are the load-test scripts and results? Historic data extraction is the most
      load-sensitive journey in the estate, so the findings are worth recovering if they exist.
- [ ] Was this fork deployed and driven, or was the exercise run against the production
      service? The frontend fork points at production hosts.
- [ ] Confirm the repository can be deleted. It is a stale partial copy of a live .NET service
      and will not receive dependency patches.
