<!-- GENERATED FILE — DO NOT EDIT.
     Source: /docs/integration-catalog.yaml
     Regenerate: python3 scripts/generate_diagrams.py -->

# Generated Diagrams

_Generated 2026-09-15T13:13:57Z from `/docs/integration-catalog.yaml`._

All files in this folder are generated. Edit `/docs/integration-catalog.yaml` and re-run `python3 scripts/generate_diagrams.py`.

## Structural diagrams

- [System context](system-context.md) — all services, domains and external systems
- [Service dependencies](service-dependencies.md) — internal edges with endpoint detail

## Journey data flows


| Journey | Description |
|---|---|
| [Citizen: check air quality for a location](flow-citizen-check-air-quality.md) | The primary public journey on check-air-quality.service.gov.uk. |
| [Scheduled air quality data ingestion](flow-data-ingestion.md) | How measurement and forecast data enters the estate. Runs on cron schedules, not on user request. |
| [Citizen: download historic air quality data](flow-historic-data-download.md) | Asynchronous extract journey — the citizen requests data and receives a download link by email. |
| [Citizen: air quality alert subscription and delivery](flow-air-quality-alerts.md) | Subscription capture, verification, alert dispatch and opt-out. aqie-alert-back-end-service owns subscriber state; aqie-notify-service owns the messaging edge and is the only holder of the GOV.UK Notify key. |
| [Smoke control: appliance and fuel applications](flow-smoke-control.md) | Applications arrive asynchronously from DEFRA Forms over SQS, not through the AQIE frontend. The public frontend is read-only search; the admin frontend is the caseworker review interface. |
