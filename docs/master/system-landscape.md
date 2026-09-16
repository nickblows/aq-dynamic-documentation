# Air Quality System Landscape

The authoritative overview of how AQIE services fit together. Structural detail is
mastered in [`/docs/integration-catalog.yaml`](../integration-catalog.yaml); diagrams under
[`/docs/diagrams/generated/`](../diagrams/generated/README.md) are generated from it.

## Contents

- [At a glance](#at-a-glance)
- [Product lines](#product-lines)
- [Service domains](#service-domains)
- [How data enters the estate](#how-data-enters-the-estate)
- [Shared building blocks](#shared-building-blocks)
- [Cross-cutting patterns](#cross-cutting-patterns)
- [System context diagram](#system-context-diagram)
- [Known structural issues](#known-structural-issues)

## At a glance

| Measure | Value |
|---|---|
| Repositories tracked | 39 |
| Runtime services (non-test, non-archived) | 21 |
| Quality and performance test repositories | 9 |
| Archived or superseded repositories | 9 |
| Evidence-backed integrations | 53 |
| Internal service-to-service edges | 26 |
| External and platform systems depended on | 16 |

## Product lines

AQIE is not one service. It is five largely independent product lines that share a
platform, a data backbone and a set of conventions.

| Product line | Citizen entry point | Backing services |
|---|---|---|
| **Check air quality** | `aqie-front-end` (check-air-quality.service.gov.uk) | `aqie-back-end`, `aqie-forecast-api`, `aqie-alert-back-end-service`, `aqie-notify-service` |
| **Air quality maps** | `aqie-maps-frontend` | `aqie-back-end`, `aqie-forecast-api` |
| **Historic data download** | `aqie-dataselector-frontend` | `aqie-historicaldata-backend`, `aqie-location-backend`, `aqie-monitoringstation-backend` |
| **Smoke control register** | `aqie-dc-frontend`, `aqie-dc-admin-frontend` | `aqie-dc-backend` (fed by DEFRA Forms over SQS) |
| **Pollutant release register (PRTR)** | `aqie-prtr-frontend` | `aqie-prtr-backend`, `aqie-location-backend` |

Only the first two share a data source. The smoke control register and PRTR are
functionally separate products that happen to live under the AQIE prefix.

## Service domains

### Citizen domain

Citizen-facing interfaces. All are Node.js, most use Hapi with Nunjucks templating and the
GOV.UK Frontend design system, and all are deployed as containers on DEFRA's Core Delivery
Platform. They hold no authoritative data of their own — at most Redis session state.

`aqie-front-end` is the flagship. `aqie-dc-admin-frontend` is the exception to the "citizen"
label: it is an internal caseworker tool and is classified here only because it is a frontend.

### Data domain

Services that own data or broker access to it. Most are Hapi APIs over MongoDB;
`aqie-historicaldata-backend` is the one C#/.NET service in the estate.

A useful distinction within this domain:

- **Ingesting services** hold scheduled jobs that pull from upstream providers —
  `aqie-back-end`, `aqie-forecast-api`, `aqie-alert-back-end-service`.
- **Brokering services** wrap an external API or aggregate other AQIE services and hold
  little or no authoritative state — `aqie-location-backend`, `aqie-monitoringstation-backend`.
- **Registry services** own a business dataset and its case lifecycle —
  `aqie-dc-backend`, `aqie-prtr-backend`.

### Shared domain

Quality and performance test harnesses, plus repositories that do not sit cleanly in either
domain. These exercise the estate but are not part of it at runtime.

## How data enters the estate

There is no single ingestion pipeline. Five independent routes bring data in:

| Route | Mechanism | Cadence | Destination |
|---|---|---|---|
| Ricardo UK-AIR API | HTTPS with bearer token | Cron (`AURN_SCHEDULE`, `POLLUTANTS_SCHEDULE`, `MONITORING_STATIONS_SCHEDULE`) | `aqie-back-end` MongoDB |
| Met Office forecast | SFTP with SSH key | Cron (`FORECAST_SCHEDULE`) | `aqie-forecast-api` and `aqie-back-end` MongoDB |
| Ricardo alert feeds | HTTPS with bearer token | Scheduled | `aqie-alert-back-end-service` MongoDB |
| DEFRA Forms submissions | AWS SQS long poll | Every 5 minutes | `aqie-dc-backend` MongoDB |
| Ricardo PRTR export | **Manual TSV load by an operator** | Ad hoc | `aqie-prtr-backend` MongoDB |

The PRTR route is the weakest link: it is a break-glass command-line ingest with no
scheduler, queue or webhook trigger. See open question `oq-010`.

Ordnance Survey, postcodes.io and the LAQM Portal are queried on demand rather than ingested.

## Shared building blocks

Four services are depended on by more than one product line and are the closest thing the
estate has to shared infrastructure:

- **`aqie-back-end`** — the measurement and station data API. Four consumers.
- **`aqie-location-backend`** — place-name resolution over the Ordnance Survey Names API.
  Three consumers. A single point of failure for location search across three product lines.
- **`aqie-forecast-api`** — forecast data. Three consumers.
- **`aqie-notify-service`** — the only holder of the GOV.UK Notify API key, and therefore the
  only route by which any AQIE service can contact a citizen.

Note that `aqie-location-backend` and `aqie-notify-service` are both classified `Monitoring`
(no commits for 91–180 days) despite being critical shared dependencies of `Active` services.

## Cross-cutting patterns

**Platform.** Every runtime service is a container on DEFRA's Core Delivery Platform, running
on AWS ECS, reachable internally at `https://<service>.<env>.cdp-int.defra.cloud`. An
alternative gateway form, `https://ephemeral-protected.api.<env>.cdp-int.defra.cloud/<service>/<path>`,
appears in configuration across several services and is used for protected,
API-key-authenticated access.

**Service-to-service trust.** Internal calls generally rely on network position rather than
application-level authentication. Where an `x-api-key` header is sent it is frequently not
validated by the receiving service.

**Observability.** Consistently `pino` logging in ECS format, `@defra/hapi-tracing` for trace
propagation, and `aws-embedded-metrics` for CloudWatch metrics.

**Templating lineage.** Most repositories are forks of the CDP Node.js frontend or backend
template, which is why scaffold `/example` routes survive in several production services.

**Progressive enhancement.** `aqie-dataselector-frontend` maintains a parallel set of
no-JavaScript routes so the historic data journey works without client-side scripting.

## System context diagram

See [`/docs/diagrams/generated/system-context.md`](../diagrams/generated/system-context.md)
for the full generated view, and
[`/docs/diagrams/generated/service-dependencies.md`](../diagrams/generated/service-dependencies.md)
for internal edges with endpoint-level detail.

Journey-level sequence diagrams:

- [Citizen: check air quality for a location](../diagrams/generated/flow-citizen-check-air-quality.md)
- [Scheduled air quality data ingestion](../diagrams/generated/flow-data-ingestion.md)
- [Citizen: download historic air quality data](../diagrams/generated/flow-historic-data-download.md)
- [Citizen: air quality alert subscription and delivery](../diagrams/generated/flow-air-quality-alerts.md)
- [Smoke control: appliance and fuel applications](../diagrams/generated/flow-smoke-control.md)

## Known structural issues

Recorded here because they affect the shape of the architecture, not just one service.
Each is tracked as an open question in the integration catalogue.

1. **The public smoke control register contract does not match** (`oq-006`). `aqie-dc-frontend`
   calls paths that `aqie-dc-backend` no longer serves.
2. **Two different Ricardo hosts are configured as production defaults** across two services
   (`oq-012`).
3. **PRTR data ingest is manual** with no scheduled trigger (`oq-010`).
4. **Unsubscribe is asymmetric** — SMS opt-out routes through `aqie-notify-service`, email
   opt-out routes through `aqie-front-end` (`oq-005`).
5. **Critical shared services are classified `Monitoring`** while their consumers are `Active`.
6. **Dead configuration propagates between repositories** through copy-paste, creating the
   appearance of integrations that do not exist. Five such claims are recorded and disproved
   under `refuted_edges` in the integration catalogue.

Security findings are recorded separately in
[`/docs/audit/security-findings.md`](../audit/security-findings.md).
