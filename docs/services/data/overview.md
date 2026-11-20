# Data Services

Services that own data or broker access to it.

## Domain characteristics

- Mostly Hapi APIs over MongoDB, deployed as containers on DEFRA's Core Delivery Platform.
- `aqie-historicaldata-backend` is the one C#/.NET service in the estate, and it still targets
  .NET 8, which left Microsoft support on 10 November 2026.
- Ingesting services run scheduled jobs in the same process as their HTTP API, using
  `node-cron` with `mongo-locks` for distributed locking.
- Internal callers are trusted by network position rather than application authentication.

## Service categories

**Ingesting** — pull from upstream providers on a schedule:

| Service | Upstream source | Status | Profile |
|---|---|---|---|
| `aqie-back-end` | Ricardo UK-AIR (station cache and DAQI), the public UK-AIR SOS and forecast feed (orphaned output), postcodes.io; Met Office SFTP read on request | Active | [Profile](aqie-back-end/service-profile.md) |
| `aqie-forecast-api` | Met Office SFTP | Monitoring | [Profile](aqie-forecast-api/service-profile.md) |
| `aqie-alert-back-end-service` | Ricardo alert feeds, `aqie-forecast-api` | Monitoring | [Profile](aqie-alert-back-end-service/service-profile.md) |

**Brokering** — wrap an external API or aggregate other services:

| Service | Wraps | Status | Profile |
|---|---|---|---|
| `aqie-location-backend` | Ordnance Survey Names API | Active | [Profile](aqie-location-backend/service-profile.md) |
| `aqie-monitoringstation-backend` | `aqie-back-end` + `aqie-location-backend` | Active | [Profile](aqie-monitoringstation-backend/service-profile.md) |
| `aqie-notify-service` | GOV.UK Notify | Monitoring | [Profile](aqie-notify-service/service-profile.md) |

**Registry** — own a business dataset and its case lifecycle:

| Service | Dataset | Status | Profile |
|---|---|---|---|
| `aqie-dc-backend` | Exempt appliances and authorised fuels: applications, technical review and certification | Active | [Profile](aqie-dc-backend/service-profile.md) |
| `aqie-prtr-backend` | Industrial facility pollutant releases | Active | [Profile](aqie-prtr-backend/service-profile.md) |
| `aqie-historicaldata-backend` | Historic data extract jobs. Holds no measurements: it re-fetches them from the public UK-AIR download service on demand | Active | [Profile](aqie-historicaldata-backend/service-profile.md) |

**Prototype and archived:**

| Service | Status | Profile |
|---|---|---|
| `aqie-prtr-submissions-backend` | Active — template scaffold for a PRTR submissions service, no function yet | [Profile](aqie-prtr-submissions-backend/service-profile.md) |
| `aqie-dc-poc-backend` | Archived | [Profile](aqie-dc-poc-backend/service-profile.md) |
| `aqie-docanalysispoc-backend` | Inactive | [Profile](aqie-docanalysispoc-backend/service-profile.md) |
| `aqie-data-service-backend` | Archived — split into location and monitoring station backends | [Profile](aqie-data-service-backend/service-profile.md) |

## Shared dependencies

`aqie-back-end`, `aqie-location-backend`, `aqie-forecast-api` and `aqie-notify-service` each
serve more than one product line. `aqie-notify-service` is the only holder of the GOV.UK
Notify API key and therefore the only route by which any AQIE service can contact a citizen.

## Data acquisition

See [How data enters the estate](../../master/system-landscape.md#how-data-enters-the-estate)
for the seven independent ingestion routes and their cadences.

Full detail per service is in each `service-profile.md`. Integration edges are mastered in
[`/docs/integration-catalog.yaml`](../../integration-catalog.yaml).
