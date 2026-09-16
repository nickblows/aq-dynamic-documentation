<!-- GENERATED FILE — DO NOT EDIT.
     Source: /docs/integration-catalog.yaml
     Regenerate: python3 scripts/generate_diagrams.py -->

# Smoke control: appliance and fuel applications

_Generated 2026-09-15T13:13:57Z from `/docs/integration-catalog.yaml`._

Applications arrive asynchronously from DEFRA Forms over SQS, not through the AQIE frontend. The public frontend is read-only search; the admin frontend is the caseworker review interface.

```mermaid
sequenceDiagram
  autonumber
  actor Applicant as Applicant
  participant defra_forms as defra-forms
  participant aqie_dc_backend as aqie-dc-backend
  participant MongoDB as MongoDB
  participant cdp_uploader as cdp-uploader
  participant AWS_S3 as AWS S3
  actor Caseworker as Caseworker
  participant aqie_dc_admin_frontend as aqie-dc-admin-frontend
  participant azure_entra as azure-entra
  actor Citizen as Citizen
  participant aqie_dc_frontend as aqie-dc-frontend
  Applicant->>defra_forms: Complete the smoke control application form
  defra_forms->>aqie_dc_backend: SQS message on aqie-dc-queue
  aqie_dc_backend->>aqie_dc_backend: Long-poll every 5 min, map form fields, split repeaters
  aqie_dc_backend->>MongoDB: Create application and appliance or fuel records
  aqie_dc_backend->>cdp_uploader: POST /initiate then /upload-and-scan/{uploadId}
  cdp_uploader->>aqie_dc_backend: POST /upload-callback — scan outcome with bucket and key
  aqie_dc_backend->>AWS_S3: Read scanned evidence
  Caseworker->>aqie_dc_admin_frontend: Sign in
  aqie_dc_admin_frontend->>azure_entra: OIDC authorisation code flow
  aqie_dc_admin_frontend->>aqie_dc_backend: Retrieve application case records
  aqie_dc_admin_frontend->>aqie_dc_backend: PATCH /appliances/{id}/technical-review
  Citizen->>aqie_dc_frontend: Search the published register
  aqie_dc_frontend->>aqie_dc_backend: GET /get-all/{type}, GET /get/{type}/{id}
```
