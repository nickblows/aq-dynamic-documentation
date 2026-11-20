<!-- Generated from /draw-io-generation/generation-config.yaml on 2026-11-19.
     Facts sourced from /docs/integration-catalog.yaml.
     Detail level: medium. Paste this whole file into one next-ai-draw-io conversation. -->

# Prompt: Journey — air quality alert subscription and delivery

Create a draw.io sequence diagram covering alert subscription, verification, scheduled
alert dispatch and opt-out. Use exactly the participants and steps below, in order.

## Diagram conventions

- Sequence diagram, time flowing top to bottom, numbered steps.
- Participant fills:
  - Person — actor shape
  - Scheduler — fill `#E1D5E7`, stroke `#9673A6`
  - Frontend — fill `#DAE8FC`, stroke `#6C8EBF`
  - Backend — fill `#D5E8D4`, stroke `#82B366`
  - External system — fill `#F5F5F5`, stroke `#666666`
  - Data store — fill `#FFF2CC`, stroke `#D6B656`, cylinder shape
- Solid arrows for confirmed calls, dashed grey `#999999` for anything marked provisional.
- Group the steps into three labelled blocks: `1. Subscribe and verify`,
  `2. Detect and dispatch`, `3. Opt out`.
- Add a legend box in the bottom-left.

## Participants

| Participant | Type |
|---|---|
| Citizen | Person |
| aqie-front-end | Frontend |
| aqie-notify-service | Backend |
| GOV.UK Notify | External |
| aqie-alert-back-end-service | Backend |
| MongoDB (subscribers) | Data store |
| Scheduler (cron) | Scheduler |
| Ricardo UK-AIR API | External |
| aqie-forecast-api | Backend |

## Steps

**Block 1: Subscribe and verify**

1. Citizen → aqie-front-end: choose alert locations and contact method
2. aqie-front-end → aqie-notify-service: `POST /subscribe/generate-otp` or `POST /subscribe/generate-link`
3. aqie-notify-service → GOV.UK Notify: send one-time code or magic link
4. GOV.UK Notify → Citizen: verification code or link
5. Citizen → aqie-front-end: enter the code or follow the link
6. aqie-front-end → aqie-notify-service: `POST /subscribe/validate-otp` or `GET /subscribe/validate-link/{token}`
7. aqie-notify-service → aqie-front-end: verification result and pending subscription
8. aqie-front-end → aqie-alert-back-end-service: `POST /setup-alert`
9. aqie-alert-back-end-service → MongoDB (subscribers): persist subscriber record (USERS)
10. aqie-alert-back-end-service → aqie-notify-service: `POST /send-notification` — confirmation message

**Block 2: Detect and dispatch**

11. Scheduler (cron) → aqie-alert-back-end-service: scheduled alert detection run
12. aqie-alert-back-end-service → Ricardo UK-AIR API: `GET /api/daqi_alerts`, `GET /api/aqsr_alerts`
13. aqie-alert-back-end-service → aqie-forecast-api: `GET /forecast` — forecast-based conditions
14. aqie-alert-back-end-service → aqie-notify-service: `POST /send-notification` per matched subscriber
15. aqie-notify-service → GOV.UK Notify: deliver alert with unsubscribe deep link
16. GOV.UK Notify → Citizen: email or SMS alert

**Block 3: Opt out**

17. Citizen → GOV.UK Notify: reply "STOP" by SMS
18. aqie-notify-service → GOV.UK Notify: collect inbound SMS replies (background poller; `GET /process-sms-replies` triggers it manually)
19. aqie-notify-service → aqie-alert-back-end-service: `DELETE /opt-out-sms-alert`
20. Citizen → aqie-front-end: follow the unsubscribe link in an email (`GET /notify/unsubscribe-email-link`, address carried as a plain query parameter) and confirm
21. aqie-front-end → aqie-alert-back-end-service: `DELETE /opt-out-email-alert`

## Notes to add to the diagram

- Add a note on aqie-alert-back-end-service: "owns subscriber state (USERS collection)".
- Add a note on aqie-notify-service: "owns the messaging edge only, and is the sole holder
  of the GOV.UK Notify key — no other AQIE service can contact a citizen". aqie-back-end has
  no notification code (oq-001, answered), so it is not a participant.
- Add a note spanning block 3, in amber: "opt-out is asymmetric — SMS routes through
  aqie-notify-service, email routes through aqie-front-end. Confirm this is intended
  (oq-005)."
- Add a red side note beside step 8, not a numbered step: "SMS journey only — aqie-front-end
  also calls `GET /api/subscriptions/{contact}` on aqie-alert-back-end-service to count the
  number's subscriptions for the maximum-locations check. The alert backend registers no such
  route, so the call cannot succeed and fails open (oq-015)".
- Add a note on steps 15 and 20: "the unsubscribe link carries the plain email address, with
  no token or signature, so anyone who knows an address can unsubscribe it (oq-038)".
