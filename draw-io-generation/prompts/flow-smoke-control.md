<!-- Generated from /draw-io-generation/generation-config.yaml on 2026-11-19.
     Facts sourced from /docs/integration-catalog.yaml.
     Detail level: medium. Paste this whole file into one next-ai-draw-io conversation. -->

# Prompt: Journey — smoke control appliance and fuel applications

Create a draw.io sequence diagram of the smoke control register journey. Applications
arrive asynchronously from DEFRA Forms over SQS, not through an AQIE frontend. The admin
frontend is the caseworker review and certification interface and requires Microsoft Entra
sign-in. Use exactly the participants and steps below, in order.

## Diagram conventions

- Sequence diagram, time flowing top to bottom, numbered steps.
- Participant fills:
  - Person — actor shape
  - Frontend — fill `#DAE8FC`, stroke `#6C8EBF`
  - Backend — fill `#D5E8D4`, stroke `#82B366`
  - External system — fill `#F5F5F5`, stroke `#666666`
  - Platform service — fill `#E1D5E7`, stroke `#9673A6`
  - Data store — fill `#FFF2CC`, stroke `#D6B656`, cylinder shape
- Solid arrows for confirmed calls, dashed grey `#999999` for anything marked provisional.
- Group the steps into three labelled blocks: `1. Application intake (asynchronous)`,
  `2. Caseworker review`, `3. Public register`.
- Add a legend box in the bottom-left.

## Participants

| Participant | Type |
|---|---|
| Applicant | Person |
| DEFRA Forms | External |
| aqie-dc-backend | Backend |
| MongoDB (register) | Data store |
| Caseworker | Person |
| aqie-dc-admin-frontend | Frontend |
| Microsoft Entra ID | External |
| Citizen | Person |
| aqie-dc-frontend | Frontend |
| CDP Uploader | Platform service — greyed side box, note only, no arrows |

## Steps

**Block 1: Application intake (asynchronous)**

1. Applicant → DEFRA Forms: complete the appliance or fuel application form
2. DEFRA Forms → aqie-dc-backend: message on the SQS application queue
3. aqie-dc-backend → aqie-dc-backend: long-poll (every 15 minutes by default, up to 10 messages per poll), store the raw message, map form field ids to domain fields, split multi-appliance repeaters
4. aqie-dc-backend → MongoDB (register): create application and appliance or fuel records; the SQS message is deleted only once it has been handled, and a failure leaves it on the queue for redelivery

**Block 2: Caseworker review**

5. Caseworker → aqie-dc-admin-frontend: sign in
6. aqie-dc-admin-frontend → Microsoft Entra ID: OIDC authorisation code flow
7. aqie-dc-admin-frontend → aqie-dc-backend: `GET /applications/summary-by-status` — read applications and items
8. aqie-dc-admin-frontend → aqie-dc-backend: `PATCH /appliances/{id}/technical-review` and `PATCH /appliances/{id}/technical-review/checks` — record review decisions (fuels have matching `/fuels/{id}` routes)
9. aqie-dc-admin-frontend → aqie-dc-backend: `PATCH /applications/{id}/complete` — complete the application
10. aqie-dc-admin-frontend → aqie-dc-backend: `PATCH /appliances/{id}/certification/{country}` and `PATCH /appliances/{id}/visibility` — publish decisions

**Block 3: Public register**

11. Citizen → aqie-dc-frontend: search the published register
12. aqie-dc-frontend → aqie-dc-backend: `GET /get-all/{type}`, `GET /get/{type}/{id}` — not served (oq-006)

## Notes to add to the diagram

- Draw step 12 in red with the note: "neither path is served by aqie-dc-backend on main
  (re-confirmed 2026-11-19), and the response shapes differ. The frontend has not changed
  since April while the backend API was reshaped — the public register journey is likely
  non-functional (oq-006, high severity)."
- Add a note on block 3: "how a fuel becomes live is unconfirmed — no fuel certification or
  visibility route exists, so the public fuel list may always be empty (oq-026)".
- Add a note on step 3: "queue ingest re-enters the service's own HTTP routes so queue and
  API writes share one validation path. Redrive, dead-letter handling and alerting for failed
  messages are unconfirmed (oq-027)".
- Add a note on aqie-dc-backend: "receives and deletes SQS messages only — it is not a
  producer, and it has no GOV.UK Notify dependency, so applicants are not notified by AQIE.
  The email to the devolved administrations is only a log-line stub (oq-024)".
- Add a note on steps 5 and 6: "sign-in is enforced on every route except the landing page,
  the health check, static assets and the three sign-in routes (since PR #19). Any signed-in
  account in the tenant is accepted — no group or role claim is checked (oq-021).
  SSO_ENABLED=false bypasses sign-in entirely (oq-020)".
- Add a note on steps 7 to 10: "an `x-api-key` header is sent on every call but
  aqie-dc-backend never validates it (oq-022). The reviewer's name and email travel in
  request bodies and are trusted by the backend. The multifuel change page sends a key the
  backend rejects (oq-023)".
- Beside the greyed CDP Uploader box, add the note: "aqie-dc-backend can start a bulk Excel
  register import through the CDP Uploader. The scan callback handler was removed in PR #123,
  so imports are scanned and stored but never imported, and no caller of the import routes
  was found (oq-025). The service has no applicant evidence upload. Not part of the journey
  above."
