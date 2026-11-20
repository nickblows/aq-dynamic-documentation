<!-- GENERATED FILE — DO NOT EDIT.
     Source: /docs/integration-catalog.yaml
     Regenerate: python3 scripts/generate_diagrams.py -->

# Citizen: download historic air quality data

_Generated 2026-11-19T20:10:05Z from `/docs/integration-catalog.yaml`._

Two journeys share one service: by station (search, recent-readings tabs and per-pollutant downloads) and custom dataset (filters, then an extract job). A single-year extract downloads directly once the job completes; multi-year requests, and any job still running after three minutes, are emailed.

```mermaid
sequenceDiagram
  autonumber
  actor Citizen as Citizen
  participant aqie_dataselector_frontend as aqie-dataselector-frontend
  participant aqie_location_backend as aqie-location-backend
  participant aqie_monitoringstation_backend as aqie-monitoringstation-backend
  participant aqie_back_end as aqie-back-end
  participant aqie_historicaldata_backend as aqie-historicaldata-backend
  participant laqm_portal as laqm-portal
  participant ukair_atom as ukair-atom
  participant AWS_S3 as AWS S3
  participant aqie_notify_service as aqie-notify-service
  participant govuk_notify as govuk-notify
  Citizen->>aqie_dataselector_frontend: By station: search a place name or postcode
  aqie_dataselector_frontend->>aqie_location_backend: POST /osnameplaces — resolve location
  aqie_dataselector_frontend->>aqie_monitoringstation_backend: POST /monitoringstation — find nearby stations
  aqie_monitoringstation_backend->>aqie_back_end: GET /monitoringStationInfo — station list
  aqie_dataselector_frontend->>aqie_back_end: GET /monitoringStationHistory — last 24 hours and 7 days
  aqie_dataselector_frontend->>aqie_historicaldata_backend: POST /AtomHistoryHourlydata — single-station download link
  Citizen->>aqie_dataselector_frontend: Custom dataset: choose pollutants, data sources and locations
  aqie_dataselector_frontend->>laqm_portal: GET /xapi/getLocalAuthorities/json — local authority list
  aqie_dataselector_frontend->>aqie_historicaldata_backend: GET region and agglomeration masters, POST /AtomDataSelection for station counts
  aqie_dataselector_frontend->>aqie_historicaldata_backend: POST /AtomDataSelection — create the extract job
  aqie_dataselector_frontend->>aqie_historicaldata_backend: POST /AtomDataSelectionJobStatus — poll every 2 s for up to 3 min
  aqie_historicaldata_backend->>ukair_atom: GET observation XML per site and year
  aqie_historicaldata_backend->>AWS_S3: Stage generated extract
  aqie_dataselector_frontend->>Citizen: Pre-signed download link once the job completes
  Citizen->>aqie_dataselector_frontend: Email path: enter an email address (multi-year or after 3 min)
  aqie_dataselector_frontend->>aqie_historicaldata_backend: POST /AtomEmailJobDataSelection — register the email job
  aqie_historicaldata_backend->>aqie_notify_service: POST /send-notification — background sweep re-runs the extract, then emails
  aqie_notify_service->>govuk_notify: Send the email
  govuk_notify->>Citizen: Email linking to the frontend page /download_emailreq/id/timestamp
  Citizen->>aqie_dataselector_frontend: Follow the link (rejected after 48 hours)
  aqie_dataselector_frontend->>aqie_historicaldata_backend: POST /AtomDataSelectionPresignedUrlMail — fresh pre-signed URL
  aqie_dataselector_frontend->>Citizen: Download page with the pre-signed link
```
