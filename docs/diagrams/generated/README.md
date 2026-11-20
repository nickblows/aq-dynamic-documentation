<!-- GENERATED FILE — DO NOT EDIT.
     Source: /docs/integration-catalog.yaml
     Regenerate: python3 scripts/generate_diagrams.py -->

# Generated Diagrams

_Generated 2026-11-19T20:10:05Z from `/docs/integration-catalog.yaml`._

All files in this folder are generated. Edit `/docs/integration-catalog.yaml` and re-run `python3 scripts/generate_diagrams.py`.

## Structural diagrams

- [System context](system-context.md) — all services, domains and external systems
- [Service dependencies](service-dependencies.md) — internal edges with endpoint detail

## Journey data flows


| Journey | Description |
|---|---|
| [Citizen: check air quality for a location](flow-citizen-check-air-quality.md) | The primary public journey on check-air-quality.service.gov.uk. |
| [Scheduled air quality data ingestion](flow-data-ingestion.md) | How measurement and forecast data enters the estate. Runs on cron schedules, not on user request. The UK-AIR sweep and the forecast feed in aqie-back-end are still written to MongoDB, but nothing has read them since the /measurements and /forecasts endpoints were removed. |
| [Citizen: download historic air quality data](flow-historic-data-download.md) | Two journeys share one service: by station (search, recent-readings tabs and per-pollutant downloads) and custom dataset (filters, then an extract job). A single-year extract downloads directly once the job completes; multi-year requests, and any job still running after three minutes, are emailed. |
| [Citizen: air quality alert subscription and delivery](flow-air-quality-alerts.md) | Subscription capture, verification, alert dispatch and opt-out. aqie-alert-back-end-service owns subscriber state; aqie-notify-service owns the messaging edge and is the only holder of the GOV.UK Notify key. SMS opt-out routes through the notify service and email opt-out through the front end (oq-005). |
| [Smoke control: appliance and fuel applications](flow-smoke-control.md) | Applications arrive asynchronously from DEFRA Forms over SQS, not through the AQIE frontend. The admin frontend is the caseworker review and certification interface and requires sign-in on every route. The public frontend calls routes the backend does not serve, so the public register may currently be broken (oq-006). The CDP Uploader import flow in the backend no longer completes, because its callback has been removed (oq-025). |
