<!-- GENERATED FILE — DO NOT EDIT.
     Source: /docs/integration-catalog.yaml
     Regenerate: python3 scripts/generate_diagrams.py -->

# Scheduled air quality data ingestion

_Generated 2026-11-19T20:10:05Z from `/docs/integration-catalog.yaml`._

How measurement and forecast data enters the estate. Runs on cron schedules, not on user request. The UK-AIR sweep and the forecast feed in aqie-back-end are still written to MongoDB, but nothing has read them since the /measurements and /forecasts endpoints were removed.

```mermaid
sequenceDiagram
  autonumber
  participant Scheduler as Scheduler
  participant aqie_back_end as aqie-back-end
  participant ricardo_ukair as ricardo-ukair
  participant postcodes_io as postcodes-io
  participant MongoDB as MongoDB
  participant defra_sos as defra-sos
  participant ukair_website as ukair-website
  participant aqie_forecast_api as aqie-forecast-api
  participant met_office_sftp as met-office-sftp
  Scheduler->>aqie_back_end: Cron trigger (MONITORING_STATIONS_SCHEDULE and at start-up, AURN_SCHEDULE)
  aqie_back_end->>ricardo_ukair: POST /api/login_check — obtain bearer token
  ricardo_ukair->>aqie_back_end: Bearer token
  aqie_back_end->>ricardo_ukair: GET /api/site_meta_datas, /api/pollutant_metadatas — stations and instrument dates
  aqie_back_end->>postcodes_io: GET /postcodes — resolve station local authority
  aqie_back_end->>MongoDB: Replace the monitoringStations cache
  aqie_back_end->>ricardo_ukair: GET /api/pollutant_measurement_datas — yesterday and today, five stations at a time
  aqie_back_end->>MongoDB: Upsert per-station DAQI (aurnMeasurements)
  Scheduler->>aqie_back_end: Cron trigger (POLLUTANTS_SCHEDULE hourly, FORECAST_SCHEDULE)
  aqie_back_end->>defra_sos: GET site listing, then SOS GetObservation for each site
  aqie_back_end->>ukair_website: GET /assets/rss/forecast.xml
  aqie_back_end->>MongoDB: Write measurements and forecasts — no reader since PR 163
  Scheduler->>aqie_forecast_api: Cron trigger (FORECAST_SCHEDULE)
  aqie_forecast_api->>met_office_sftp: SFTP poll configured directory
  met_office_sftp->>aqie_forecast_api: Forecast files
  aqie_forecast_api->>MongoDB: Persist parsed forecast documents
```
