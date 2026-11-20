<!-- GENERATED FILE — DO NOT EDIT.
     Source: /docs/integration-catalog.yaml
     Regenerate: python3 scripts/generate_diagrams.py -->

# Smoke control: appliance and fuel applications

_Generated 2026-11-19T20:10:05Z from `/docs/integration-catalog.yaml`._

Applications arrive asynchronously from DEFRA Forms over SQS, not through the AQIE frontend. The admin frontend is the caseworker review and certification interface and requires sign-in on every route. The public frontend calls routes the backend does not serve, so the public register may currently be broken (oq-006). The CDP Uploader import flow in the backend no longer completes, because its callback has been removed (oq-025).

```mermaid
sequenceDiagram
  autonumber
  actor Applicant as Applicant
  participant defra_forms as defra-forms
  participant aqie_dc_backend as aqie-dc-backend
  participant MongoDB as MongoDB
  actor Caseworker as Caseworker
  participant aqie_dc_admin_frontend as aqie-dc-admin-frontend
  participant azure_entra as azure-entra
  actor Citizen as Citizen
  participant aqie_dc_frontend as aqie-dc-frontend
  Applicant->>defra_forms: Complete the appliance or fuel application form
  defra_forms->>aqie_dc_backend: SQS message on aqie-dc-queue
  aqie_dc_backend->>aqie_dc_backend: Long-poll (default every 15 min), store the message, map form fields, split repeaters
  aqie_dc_backend->>MongoDB: Create application and appliance or fuel records, delete the message once handled
  Caseworker->>aqie_dc_admin_frontend: Sign in
  aqie_dc_admin_frontend->>azure_entra: OIDC authorisation code flow
  aqie_dc_admin_frontend->>aqie_dc_backend: GET /applications/summary-by-status — read applications and items
  aqie_dc_admin_frontend->>aqie_dc_backend: PATCH .../technical-review and .../checks — record review decisions
  aqie_dc_admin_frontend->>aqie_dc_backend: PATCH /applications/{id}/complete — complete the application
  aqie_dc_admin_frontend->>aqie_dc_backend: PATCH /appliances/{id}/certification/{country} and /visibility — publish decisions
  Citizen->>aqie_dc_frontend: Search the published register
  aqie_dc_frontend->>aqie_dc_backend: GET /get-all/{type}, GET /get/{type}/{id} — not served (oq-006)
```
