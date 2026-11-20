<!-- Generated from /draw-io-generation/generation-config.yaml on 2026-11-19.
     Facts sourced from /docs/integration-catalog.yaml.
     Detail level: medium, with full endpoint paths because this diagram exists to show them.
     Paste this whole file into one next-ai-draw-io conversation. -->

# Prompt: AQIE internal service dependencies

Create a draw.io dependency diagram of the internal service-to-service calls inside the
DEFRA Air Quality (AQIE) estate. External systems are deliberately out of scope — show
AQIE services only. Use exactly the components and calls below.

## Diagram conventions

- Orientation: left to right, frontends on the left, the services they call to the right.
- Group nodes into labelled containers by product line.
- Node fills:
  - Frontend — fill `#DAE8FC`, stroke `#6C8EBF`
  - Backend — fill `#D5E8D4`, stroke `#82B366`
- Edge styles carry certainty:
  - Confirmed call — solid line, black
  - Provisional call — dashed line, grey `#999999`, label suffixed `(provisional — to confirm)`
  - Every call below is confirmed, so draw all of them solid; keep both styles in the legend.
- Label each edge with the endpoint paths listed. Where an edge has more than five
  endpoints, show the first three and append `+N more`.
- Draw link-construction edges (no runtime HTTP call) as thin grey lines labelled
  `deep link only`.
- Add a legend box in the bottom-left.

## Context

All internal calls are HTTPS/REST and synchronous unless stated. They are trusted by
network position on DEFRA's Core Delivery Platform rather than by application
authentication, so there is no per-call credential to show. The one exception to flag is an
`x-api-key` header that aqie-dc-frontend and aqie-dc-admin-frontend send to aqie-dc-backend,
which the backend never checks.

## Components

**Core citizen service:** aqie-front-end (frontend), aqie-back-end (backend)

**Alerts:** aqie-alert-back-end-service, aqie-notify-service, aqie-forecast-api (all backend)

**Historic data and location:** aqie-dataselector-frontend (frontend),
aqie-historicaldata-backend, aqie-location-backend, aqie-monitoringstation-backend (backend)

**Smoke control:** aqie-dc-frontend, aqie-dc-admin-frontend (frontend), aqie-dc-backend (backend)

**Maps:** aqie-maps-frontend (frontend)

**PRTR:** aqie-prtr-frontend (frontend), aqie-prtr-backend (backend). The two submissions
scaffolds, aqie-prtr-submissions-frontend and aqie-prtr-submissions-backend, make no internal
calls and receive none (oq-032), so they are not shown.

## Calls

1. aqie-front-end → aqie-back-end
   `GET /monitoringStationInfo`
2. aqie-front-end → aqie-forecast-api
   `GET /forecast` — forecast DAQI values and the forecast summary narrative
3. aqie-front-end → aqie-alert-back-end-service
   `POST /setup-alert`, `DELETE /opt-out-email-alert`, `GET /aqsr-alert`, `GET /daqi-alert`, `GET /api/subscriptions/{contact}` — the last is SMS journey only and **not served**, see below
4. aqie-front-end → aqie-notify-service
   `POST /subscribe/generate-otp`, `POST /subscribe/validate-otp`, `POST /subscribe/generate-link`, `GET /subscribe/validate-link/{token}`
5. aqie-alert-back-end-service → aqie-notify-service
   `POST /send-notification` — every citizen message funnels through here
6. aqie-alert-back-end-service → aqie-forecast-api
   `GET /forecast` — scheduled batch
7. aqie-alert-back-end-service → aqie-front-end
   `GET /notify/unsubscribe-email-link` — deep link only
8. aqie-notify-service → aqie-alert-back-end-service
   `DELETE /opt-out-sms-alert`
9. aqie-notify-service → aqie-front-end
   `GET /notify/register/email-confirm-link` — deep link only
10. aqie-dataselector-frontend → aqie-historicaldata-backend
    `POST /AtomDataSelection`, `POST /AtomDataSelectionJobStatus`, `GET /AtomDataSelectionPollutantMaster` +7 more
11. aqie-dataselector-frontend → aqie-location-backend
    `POST /osnameplaces`
12. aqie-dataselector-frontend → aqie-monitoringstation-backend
    `POST /monitoringstation`, `GET /monitoringstation/by-location`
13. aqie-dataselector-frontend → aqie-back-end
    `GET /monitoringStationHistory`
14. aqie-dataselector-frontend → aqie-maps-frontend
    `GET /map`, `POST /map/view` — deep link only (link and form post in the citizen's browser)
15. aqie-maps-frontend → aqie-dataselector-frontend
    `POST /station-summary` — deep link only (form post from the citizen's browser)
16. aqie-historicaldata-backend → aqie-notify-service
    `POST /send-notification` — asynchronous, background email job
17. aqie-monitoringstation-backend → aqie-back-end
    `GET /monitoringStationInfo?with-closed=true&with-pollutants=1&stream=data` — also called on a schedule to refresh the stations cache
18. aqie-monitoringstation-backend → aqie-location-backend
    `POST /osnameplaces`
19. aqie-maps-frontend → aqie-back-end
    `GET /monitoringStations`, `GET /aurnData`, `GET /monitoringStationInfo`
20. aqie-maps-frontend → aqie-forecast-api
    `GET /forecast`
21. aqie-prtr-frontend → aqie-prtr-backend
    `GET /facilities/search`, `GET /facilities/nearby`, `GET /facilities/{id}/details` +6 more
22. aqie-prtr-backend → aqie-location-backend
    `POST /osnameplaces`
23. aqie-dc-admin-frontend → aqie-dc-backend
    `GET /applications/counts`, `GET /applications/summary-by-status?type={type}`, `GET /applications/{id}/summary?type={type}` +18 more — GET and PATCH only
24. aqie-dc-frontend → aqie-dc-backend
    `GET /get-all/{type}`, `GET /get/{type}/{id}` — **broken, see below**

## Points to flag on the diagram

- Draw call 24 in red with a warning note: "neither path is served by aqie-dc-backend on
  main (re-confirmed 2026-11-19), and the response shapes differ — the public register
  journey is likely non-functional (oq-006)".
- Draw the `GET /api/subscriptions/{contact}` endpoint on call 3 in red with the note: "SMS
  journey only — the alert backend registers no such route, so the call cannot succeed and
  fails open (oq-015)".
- aqie-location-backend is called by three services (calls 11, 18 and 22) across the historic
  data and PRTR product lines — make its shared role visually obvious. Add a note: "the
  partial-postcode rule appears to be dead code (oq-036)".
- aqie-notify-service is a convergence point: every outbound citizen message passes
  through it (calls 4, 5, 16).
- Add a note on calls 10 and 16: "the emailed download link is built by
  aqie-historicaldata-backend and passed to aqie-notify-service. Expiry policy is open: 48
  hours is enforced only in aqie-dataselector-frontend, against an unsigned timestamp, while
  the backend issues seven-day pre-signed URLs with no age check (oq-034, partly answered)".
- Calls 14 and 15 are links and form posts in the citizen's browser, not server calls. Add a
  note: "configured addresses must be reachable from a citizen's browser (oq-035)".
- Add a note on calls 23 and 24: "an x-api-key header is sent but never validated by
  aqie-dc-backend (oq-022)". On call 23 add: "the multifuel change page sends a key the
  backend rejects (oq-023)".
- Add a note on calls 12 and 17: "aqie-monitoringstation-backend returns HTTP 400 for upstream
  failures, and the data selector search page treats any failure as no stations (oq-028)".
- Add a note on call 19: "a station that stops meeting the data-capture rule keeps its old
  DAQI, which the map shows as current (oq-030). `GET /monitoringStationInfo` is reached only
  through a proxy route that nothing in the repository calls".
- Add a note on call 20: "the forecast view cannot be selected in the shipped interface, yet
  forecasts are fetched on every map load (oq-017)". Do not draw a call from
  aqie-maps-frontend to `GET /forecasts` on aqie-back-end: that endpoint was removed and its
  fallback is not reached in deployed environments (per CDP environment configuration).
- Note that DEFRA Forms feeds aqie-dc-backend over SQS. That edge is external and is shown
  on the system context and data flow diagrams, not here.
