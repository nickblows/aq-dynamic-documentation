<!-- GENERATED FILE — DO NOT EDIT.
     Source: /docs/integration-catalog.yaml
     Regenerate: python3 scripts/generate_diagrams.py -->

# Scheduled air quality data ingestion

_Generated 2026-09-15T13:13:57Z from `/docs/integration-catalog.yaml`._

How measurement and forecast data enters the estate. Runs on cron schedules, not on user request.

```mermaid
sequenceDiagram
  autonumber
  participant Scheduler as Scheduler
  participant aqie_back_end as aqie-back-end
  participant ricardo_ukair as ricardo-ukair
  participant postcodes_io as postcodes-io
  participant MongoDB as MongoDB
  participant aqie_forecast_api as aqie-forecast-api
  participant met_office_sftp as met-office-sftp
  Scheduler->>aqie_back_end: Cron trigger (AURN_SCHEDULE, POLLUTANTS_SCHEDULE, MONITORING_STATIONS_SCHEDULE)
  aqie_back_end->>ricardo_ukair: POST /api/login_check — obtain bearer token
  ricardo_ukair->>aqie_back_end: Bearer token
  aqie_back_end->>ricardo_ukair: GET /api/site_meta_datas, /api/pollutant_metadatas
  aqie_back_end->>ricardo_ukair: GET /api/pollutant_measurement_datas
  ricardo_ukair->>aqie_back_end: Station metadata and pollutant time series
  aqie_back_end->>postcodes_io: GET /postcodes — resolve station local authority
  aqie_back_end->>MongoDB: Upsert stations, pollutants and measurements
  Scheduler->>aqie_forecast_api: Cron trigger (FORECAST_SCHEDULE)
  aqie_forecast_api->>met_office_sftp: SFTP poll configured directory
  met_office_sftp->>aqie_forecast_api: Forecast files
  aqie_forecast_api->>MongoDB: Persist parsed forecast documents
```
