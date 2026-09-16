<!-- GENERATED FILE — DO NOT EDIT.
     Source: /docs/integration-catalog.yaml
     Regenerate: python3 scripts/generate_diagrams.py -->

# Citizen: download historic air quality data

_Generated 2026-09-15T13:13:57Z from `/docs/integration-catalog.yaml`._

Asynchronous extract journey — the citizen requests data and receives a download link by email.

```mermaid
sequenceDiagram
  autonumber
  actor Citizen as Citizen
  participant aqie_dataselector_frontend as aqie-dataselector-frontend
  participant aqie_location_backend as aqie-location-backend
  participant aqie_monitoringstation_backend as aqie-monitoringstation-backend
  participant aqie_back_end as aqie-back-end
  participant aqie_historicaldata_backend as aqie-historicaldata-backend
  participant AWS_S3 as AWS S3
  Citizen->>aqie_dataselector_frontend: Choose pollutants, years and locations
  aqie_dataselector_frontend->>aqie_location_backend: POST /osnameplaces — resolve location
  aqie_dataselector_frontend->>aqie_monitoringstation_backend: POST /monitoringstation — find stations
  aqie_monitoringstation_backend->>aqie_back_end: GET /monitoringStationInfo + /measurements
  aqie_dataselector_frontend->>aqie_historicaldata_backend: GET /AtomDataSelectionPollutantMaster
  aqie_dataselector_frontend->>aqie_historicaldata_backend: POST /AtomDataSelection — request extract
  aqie_historicaldata_backend->>aqie_dataselector_frontend: Job reference
  aqie_dataselector_frontend->>aqie_historicaldata_backend: POST /AtomDataSelectionJobStatus — poll
  aqie_historicaldata_backend->>AWS_S3: Stage generated extract
  aqie_dataselector_frontend->>aqie_historicaldata_backend: POST /AtomDataSelectionPresignedUrlMail
  aqie_historicaldata_backend->>Citizen: Email containing a pre-signed download link
```
