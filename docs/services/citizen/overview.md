# Citizen Services

Citizen-facing interfaces across the AQIE estate. These present data; they do not own it.

## Domain characteristics

- All are Node.js services deployed as containers on DEFRA's Core Delivery Platform.
- Most use Hapi with Nunjucks templating and the GOV.UK Frontend design system.
  `aqie-demo-data-visualisations` and `aqie-maps-prototype` use Express instead.
- None hold authoritative data. At most they hold Redis session state.
- All obtain their data by calling Data domain services or external APIs.

## Services

| Service | Product line | Status | Profile |
|---|---|---|---|
| `aqie-front-end` | Check air quality | Active | [Profile](aqie-front-end/service-profile.md) |
| `aqie-maps-frontend` | Air quality maps | Active | [Profile](aqie-maps-frontend/service-profile.md) |
| `aqie-dataselector-frontend` | Historic data download | Active | [Profile](aqie-dataselector-frontend/service-profile.md) |
| `aqie-prtr-frontend` | Pollutant release register | Active | [Profile](aqie-prtr-frontend/service-profile.md) |
| `aqie-prtr-submissions-frontend` | PRTR submissions (scaffold, no function yet) | Active | [Profile](aqie-prtr-submissions-frontend/service-profile.md) |
| `aqie-dc-frontend` | Smoke control register (public) | Inactive | [Profile](aqie-dc-frontend/service-profile.md) |
| `aqie-dc-admin-frontend` | Smoke control register (caseworker) | Active | [Profile](aqie-dc-admin-frontend/service-profile.md) |
| `aqie-demo-data-visualisations` | Demonstration | Active | [Profile](aqie-demo-data-visualisations/service-profile.md) |
| `aqie-laqm-data-explorer` | Analytics support | Monitoring | [Profile](aqie-laqm-data-explorer/service-profile.md) |
| `aqie-maps-prototype` | Prototype (superseded) | Monitoring | [Profile](aqie-maps-prototype/service-profile.md) |
| `aqie-dc-poc-frontend` | Prototype scaffold | Archived | [Profile](aqie-dc-poc-frontend/service-profile.md) |
| `aqie-docanalysisawspoc-frontend` | Prototype (document analysis) | Inactive | [Profile](aqie-docanalysisawspoc-frontend/service-profile.md) |
| `aqie-docanalysispoc-frontend` | Prototype (superseded) | Inactive | [Profile](aqie-docanalysispoc-frontend/service-profile.md) |
| `AQIE-Citizen-Alpha` | Original alpha | Archived | [Profile](AQIE-Citizen-Alpha/service-profile.md) |

## Dependencies on other domains

| This service | Depends on |
|---|---|
| `aqie-front-end` | `aqie-back-end`, `aqie-forecast-api`, `aqie-alert-back-end-service`, `aqie-notify-service` |
| `aqie-maps-frontend` | `aqie-back-end`, `aqie-forecast-api`; browser link to `aqie-dataselector-frontend` |
| `aqie-dataselector-frontend` | `aqie-historicaldata-backend`, `aqie-location-backend`, `aqie-monitoringstation-backend`, `aqie-back-end` (recent station readings), the external LAQM Portal API; browser links to and from `aqie-maps-frontend` |
| `aqie-prtr-frontend` | `aqie-prtr-backend` |
| `aqie-prtr-submissions-frontend` | Nothing yet — a template scaffold with no backend client |
| `aqie-dc-frontend`, `aqie-dc-admin-frontend` | `aqie-dc-backend` |
| `aqie-demo-data-visualisations` | External APIs only (Ricardo UK-AIR API with its own credentials, postcodes.io). It no longer calls `aqie-back-end` |
| `aqie-laqm-data-explorer` | External LAQM Portal API only |

## Notes

- `aqie-dc-admin-frontend` is an internal staff tool rather than a citizen service. It is
  classified here because it is a frontend; reclassification is an open question. It now
  requires Microsoft Entra sign-in on every route, but applies no role or group check.
- `aqie-laqm-data-explorer` has no AQIE dependencies at all — it is a client of an
  external portal API.
- `aqie-prtr-submissions-frontend` is classified here by the estate's convention that every
  frontend sits in the Citizen domain, although its intended users are organisations
  submitting data rather than citizens.

Full detail per service is in each `service-profile.md`. Integration edges are mastered in
[`/docs/integration-catalog.yaml`](../../integration-catalog.yaml).
