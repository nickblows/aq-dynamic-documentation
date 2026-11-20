<!-- GENERATED FILE — DO NOT EDIT.
     Source: /docs/integration-catalog.yaml
     Regenerate: python3 scripts/generate_diagrams.py -->

# Citizen: check air quality for a location

_Generated 2026-11-19T20:10:05Z from `/docs/integration-catalog.yaml`._

The primary public journey on check-air-quality.service.gov.uk.

```mermaid
sequenceDiagram
  autonumber
  actor Citizen as Citizen
  participant aqie_front_end as aqie-front-end
  participant os_names as os-names
  participant aqie_back_end as aqie-back-end
  participant ricardo_ukair as ricardo-ukair
  participant aqie_forecast_api as aqie-forecast-api
  Citizen->>aqie_front_end: Search a place name or postcode
  aqie_front_end->>os_names: GET /search/names/v1/find — resolve place to coordinates
  os_names->>aqie_front_end: Matched places with coordinates
  aqie_front_end->>aqie_back_end: GET /monitoringStationInfo — stations near coordinates
  aqie_back_end->>ricardo_ukair: POST /api/login_check, GET /api/site_meta_datas
  aqie_back_end->>ricardo_ukair: GET /api/pollutant_measurement_datas — 5 calls per station
  aqie_back_end->>aqie_front_end: Station metadata and current pollutant concentrations
  aqie_front_end->>aqie_forecast_api: GET /forecast — multi-day outlook and forecast summary
  aqie_forecast_api->>aqie_front_end: Forecast DAQI by day and region, and the forecast summary text
  aqie_front_end->>aqie_front_end: Calculate pollutant bands and map forecast days to bands and advice
  aqie_front_end->>Citizen: Rendered location page with DAQI, pollutants and forecast
```
