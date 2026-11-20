# Air Quality System Landscape

The authoritative overview of how AQIE services fit together. Structural detail is
mastered in [`/docs/integration-catalog.yaml`](../integration-catalog.yaml); diagrams under
[`/docs/diagrams/generated/`](../diagrams/generated/README.md) are generated from it.
Last reconciled with the default branches on 2026-11-19.

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
| Repositories tracked | 41 |
| Runtime and prototype services (not test, not archived) | 24 |
| Quality and performance test repositories (not archived) | 9 |
| Archived repositories | 8 |
| Evidence-backed integrations | 61 |
| Internal service-to-service edges | 29 |
| External and platform systems depended on | 17 |

## Product lines

AQIE is not one service. It is five largely independent product lines that share a
platform, a data backbone and a set of conventions.

| Product line | Citizen entry point | Backing services |
|---|---|---|
| **Check air quality** | `aqie-front-end` (check-air-quality.service.gov.uk) | `aqie-back-end`, `aqie-forecast-api`, `aqie-alert-back-end-service`, `aqie-notify-service` |
| **Air quality maps** | `aqie-maps-frontend` | `aqie-back-end`, `aqie-forecast-api`; hands users over to the historic data download by a browser link |
| **Historic data download** | `aqie-dataselector-frontend` | `aqie-historicaldata-backend`, `aqie-location-backend`, `aqie-monitoringstation-backend`, `aqie-back-end` (recent station readings), the LAQM Portal; links back to the maps |
| **Smoke control register** | `aqie-dc-frontend`, `aqie-dc-admin-frontend` | `aqie-dc-backend` (fed by DEFRA Forms over SQS) |
| **Pollutant release register (PRTR)** | `aqie-prtr-frontend` | `aqie-prtr-backend`, `aqie-location-backend` |

The first two share a data source, and the historic data download now reads recent station
readings from the same back end. The smoke control register and PRTR are functionally
separate products that happen to live under the AQIE prefix. Two new PRTR submissions
repositories, `aqie-prtr-submissions-frontend` and `aqie-prtr-submissions-backend`, are
template scaffolds with no function yet and no connection to the register or to each other
(`oq-032`).

## Service domains

### Citizen domain

Citizen-facing interfaces. All are Node.js, most use Hapi with Nunjucks templating and the
GOV.UK Frontend design system, and all are deployed as containers on DEFRA's Core Delivery
Platform. They hold no authoritative data of their own — at most Redis session state.

`aqie-front-end` is the flagship. `aqie-dc-admin-frontend` is the exception to the "citizen"
label: it is an internal caseworker tool and is classified here only because it is a frontend.

### Data domain

Services that own data or broker access to it. Most are Hapi APIs over MongoDB;
`aqie-historicaldata-backend` is the one C#/.NET service in the estate, and it still targets
.NET 8, which left Microsoft support on 10 November 2026 (security finding 47).

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

There is no single ingestion pipeline. Seven independent routes bring data in:

| Route | Mechanism | Cadence | Destination |
|---|---|---|---|
| Ricardo UK-AIR API (AURN stations and measurements) | HTTPS with bearer token | Cron (`AURN_SCHEDULE` every 30 minutes, `MONITORING_STATIONS_SCHEDULE` every 6 hours), plus live calls on each `/monitoringStationInfo` request | `aqie-back-end` MongoDB (station cache and per-station DAQI) |
| Public UK-AIR site, hourly sweep of the Sensor Observation Service | HTTPS, no authentication | Cron (`POLLUTANTS_SCHEDULE`, hourly) | `aqie-back-end` MongoDB (`measurements`, `historicalMeasurements`), which nothing has read since PR #163 (`oq-019`) |
| Public UK-AIR forecast RSS feed | HTTPS, no authentication | Cron (`FORECAST_SCHEDULE`, hourly from 05:00 to 10:00) and at start-up | `aqie-back-end` MongoDB (`forecasts`, `historicalForecasts`), also unread since PR #163 |
| Met Office forecast files | SFTP with SSH key | Polled on a schedule (`FORECAST_SCHEDULE`) by `aqie-forecast-api`; `aqie-back-end` can also read the share on request and stores nothing | `aqie-forecast-api` MongoDB |
| Ricardo alert feeds | HTTPS with bearer token | Scheduled | `aqie-alert-back-end-service` MongoDB |
| DEFRA Forms submissions | AWS SQS long poll | Every 15 minutes by default (`AWS_SQS_POLL_INTERVAL_MINUTES`; the default was 5) | `aqie-dc-backend` MongoDB |
| PRTR data | Ricardo PRTR export loaded by a manual TSV command (one-shot by its own description); annual dataset XML files reach S3 through the CDP Uploader | Ad hoc | `aqie-prtr-backend` MongoDB and S3 |

The PRTR route is the weakest link: there is no scheduler, queue or webhook trigger, and the
process that uploads the XML files is not identified in any repository. See open question
`oq-010`.

Ordnance Survey, postcodes.io, the LAQM Portal and the UK-AIR Atom download service are
queried on demand rather than ingested.

## Shared building blocks

Four services are depended on by more than one product line and are the closest thing the
estate has to shared infrastructure:

- **`aqie-back-end`** — the measurement and station data API. Four runtime consumers: the
  front end, the maps frontend, `aqie-monitoringstation-backend` and the dataselector
  frontend (recent station readings). The maps prototype also calls it; the demonstration
  prototype no longer does.
- **`aqie-location-backend`** — place-name resolution over the Ordnance Survey Names API.
  Three consumers (`aqie-dataselector-frontend`, `aqie-monitoringstation-backend` and
  `aqie-prtr-backend`) across two product lines. A single point of failure for location
  search in the historic data download and PRTR.
- **`aqie-forecast-api`** — forecast data. Three consumers.
- **`aqie-notify-service`** — the only holder of the GOV.UK Notify API key, and therefore the
  only route by which any AQIE service can contact a citizen. Three consumers: the alert
  backend, the front end and `aqie-historicaldata-backend` (emailed extract links).

Note that `aqie-notify-service` is classified `Monitoring` (no commits since 28 May 2026, so
it becomes `Inactive` in late November 2026 without one) despite being a critical shared
dependency of `Active` services. `aqie-location-backend` is now `Active`.

## Cross-cutting patterns

**Platform.** Every runtime service is a container on DEFRA's Core Delivery Platform, running
on AWS ECS, reachable internally at `https://<service>.<env>.cdp-int.defra.cloud`. An
alternative gateway form, `https://ephemeral-protected.api.<env>.cdp-int.defra.cloud/<service>/<path>`,
appears in configuration across several services and is used for protected,
API-key-authenticated access.

**Service-to-service trust.** Internal calls generally rely on network position rather than
application-level authentication. Where an `x-api-key` header is sent it is frequently not
validated by the receiving service; the clearest case is the key both smoke control
frontends send to `aqie-dc-backend`, which never reads it (`oq-022`).

**Observability.** Consistently `pino` logging in ECS format. Trace propagation
(`@defra/hapi-tracing`) and CloudWatch metrics (`aws-embedded-metrics`) come from the CDP
template and are not wired in every service: `aqie-back-end` carries the code but registers
neither.

**Templating lineage.** Most repositories are forks of the CDP Node.js frontend or backend
template, which is why scaffold `/example` routes survive in several production services.
The two PRTR submissions repositories are little more than the unmodified template.

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
   calls paths that `aqie-dc-backend` no longer serves. Still open at 2026-11-19, and the
   backend's own routes are unauthenticated for writes (`oq-022`).
2. **The code default for the Ricardo host in `aqie-back-end` is the supplier's staging
   host**, although production configuration overrides it (`oq-012`, now low). Removing any
   of the four URL variables would silently select staging.
3. **PRTR data ingest has no scheduled trigger**, and the process that uploads the annual XML
   files is not identified (`oq-010`).
4. **Unsubscribe is asymmetric** — SMS opt-out routes through `aqie-notify-service`, email
   opt-out routes through `aqie-front-end` (`oq-005`) — and the email link carries the plain
   address with no token (`oq-038`).
5. **A critical shared service is classified `Monitoring`** (`aqie-notify-service`) while its
   consumers are `Active`.
6. **Dead configuration propagates between repositories** through copy-paste, creating the
   appearance of integrations that do not exist. Thirteen claimed edges are recorded and
   disproved under `refuted_edges` in the integration catalogue; several came from settings
   that nothing reads (the front end's UK-AIR summary and postcodes.io settings, the back
   end's Notify setting).
7. **Two scheduled ingests write data nothing reads.** Since the `/measurements` and
   `/forecasts` endpoints were removed (PR #163), `aqie-back-end` still runs the UK-AIR
   sweep and the forecast RSS fetch (`oq-019`).
8. **Repositories outside the discovery filter.** `prtr-contacts-backend` and
   `aiqe-dataservice-test` do not match `aqie in:name` and are not in this set (`oq-033`).

Security findings are recorded separately in
[`/docs/audit/security-findings.md`](../audit/security-findings.md).
