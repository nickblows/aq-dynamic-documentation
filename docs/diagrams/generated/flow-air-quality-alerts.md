<!-- GENERATED FILE — DO NOT EDIT.
     Source: /docs/integration-catalog.yaml
     Regenerate: python3 scripts/generate_diagrams.py -->

# Citizen: air quality alert subscription and delivery

_Generated 2026-09-15T13:13:57Z from `/docs/integration-catalog.yaml`._

Subscription capture, verification, alert dispatch and opt-out. aqie-alert-back-end-service owns subscriber state; aqie-notify-service owns the messaging edge and is the only holder of the GOV.UK Notify key.

```mermaid
sequenceDiagram
  autonumber
  actor Citizen as Citizen
  participant aqie_front_end as aqie-front-end
  participant aqie_notify_service as aqie-notify-service
  participant govuk_notify as govuk-notify
  participant aqie_alert_back_end_service as aqie-alert-back-end-service
  participant MongoDB as MongoDB
  participant Scheduler as Scheduler
  participant ricardo_ukair as ricardo-ukair
  participant aqie_forecast_api as aqie-forecast-api
  Citizen->>aqie_front_end: Choose alert locations and contact method
  aqie_front_end->>aqie_notify_service: POST /subscribe/generate-otp or /subscribe/generate-link
  aqie_notify_service->>govuk_notify: Send one-time code or magic link
  govuk_notify->>Citizen: Verification code or link
  Citizen->>aqie_front_end: Enter the code or follow the link
  aqie_front_end->>aqie_notify_service: POST /subscribe/validate-otp or GET /subscribe/validate-link/{uuid}
  aqie_notify_service->>aqie_front_end: Verification result and pending subscription
  aqie_front_end->>aqie_alert_back_end_service: POST /setup-alert
  aqie_alert_back_end_service->>MongoDB: Persist subscriber record (USERS)
  aqie_alert_back_end_service->>aqie_notify_service: POST /send-notification — confirmation message
  Scheduler->>aqie_alert_back_end_service: Scheduled alert detection run
  aqie_alert_back_end_service->>ricardo_ukair: GET /api/daqi_alerts, /api/aqsr_alerts
  aqie_alert_back_end_service->>aqie_forecast_api: GET /forecast — forecast-based conditions
  aqie_alert_back_end_service->>aqie_notify_service: POST /send-notification per matched subscriber
  aqie_notify_service->>govuk_notify: Deliver alert with unsubscribe deep link
  govuk_notify->>Citizen: Email or SMS alert
  Citizen->>govuk_notify: Reply "STOP" by SMS
  aqie_notify_service->>govuk_notify: GET /process-sms-replies — collect inbound replies
  aqie_notify_service->>aqie_alert_back_end_service: DELETE /opt-out-sms-alert
```
