<!-- GENERATED FILE — DO NOT EDIT.
     Source: /docs/integration-catalog.yaml
     Regenerate: python3 scripts/generate_diagrams.py -->

# Citizen: check air quality for a location

_Generated 2026-09-15T13:13:57Z from `/docs/integration-catalog.yaml`._

The primary public journey on check-air-quality.service.gov.uk.

```mermaid
sequenceDiagram
  autonumber
  actor Citizen as Citizen
  participant aqie_front_end as aqie-front-end
  participant os_names as os-names
  participant aqie_back_end as aqie-back-end
  participant aqie_forecast_api as aqie-forecast-api
  participant ukair_website as ukair-website
  Citizen->>aqie_front_end: Search a place name or postcode
  aqie_front_end->>os_names: GET /search/names/v1/find — resolve place to coordinates
  os_names->>aqie_front_end: Matched places with coordinates
  aqie_front_end->>aqie_back_end: GET /monitoringStationInfo — stations near coordinates
  aqie_back_end->>aqie_front_end: Station metadata and pollutants measured
  aqie_front_end->>aqie_back_end: GET /measurements — current pollutant concentrations
  aqie_back_end->>aqie_front_end: Concentrations and DAQI bands
  aqie_front_end->>aqie_forecast_api: GET /forecast — multi-day outlook
  aqie_forecast_api->>aqie_front_end: Forecast DAQI by day and region
  aqie_front_end->>ukair_website: GET /ajax/forecast_text_summary.php
  ukair_website->>aqie_front_end: National forecast narrative
  aqie_front_end->>Citizen: Rendered location page with DAQI, pollutants and forecast
```
