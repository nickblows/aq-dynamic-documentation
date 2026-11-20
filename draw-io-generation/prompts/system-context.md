<!-- Generated from /draw-io-generation/generation-config.yaml on 2026-11-19.
     Facts sourced from /docs/repository-catalog.yaml and /docs/integration-catalog.yaml.
     Detail level: medium. Paste this whole file into one next-ai-draw-io conversation. -->

# Prompt: AQIE system context

Create a draw.io system context diagram of the DEFRA Air Quality (AQIE) service estate
using exactly the components and connections below. Do not invent any component or
connection that is not listed.

## Diagram conventions

- Orientation: left to right. External data sources on the left, AQIE services in the
  middle grouped by product line, citizen-facing outputs on the right.
- Put each product line in its own labelled container.
- Node fills:
  - Citizen-facing frontend — fill `#DAE8FC`, stroke `#6C8EBF`
  - Backend service — fill `#D5E8D4`, stroke `#82B366`
  - External system — fill `#F5F5F5`, stroke `#666666`
  - Platform service — fill `#E1D5E7`, stroke `#9673A6`
- Edge styles carry certainty:
  - Confirmed integration — solid line, black
  - Provisional integration — dashed line, grey `#999999`, label suffixed `(provisional — to confirm)`
  - Inferred integration — dotted line, grey `#999999`, label suffixed `(inferred — to confirm)`
- Add a legend box in the bottom-left explaining the fills and the three line styles. Every
  connection below is confirmed, so draw all of them solid black; the legend still explains
  all three styles.
- Keep edge labels short: say what data crosses the edge, not how.

## Context

AQIE runs on DEFRA's Core Delivery Platform (CDP). Frontends hold no authoritative data —
they call backend services, which either own a dataset or broker an external API. Internal
service-to-service calls are trusted by network position rather than application
authentication.

## Components

### Core citizen service

| Component | Kind | Role | Stores |
|---|---|---|---|
| aqie-front-end | Frontend | Public "Check air quality" GOV.UK service | Redis (session and response caches only) |
| aqie-back-end | Backend | Caches Ricardo station data and per-station DAQI; reads Ricardo live for current readings and station history | MongoDB |

### Air quality alerts

| Component | Kind | Role | Stores |
|---|---|---|---|
| aqie-alert-back-end-service | Backend | Owns alert subscriber state and decides when an alert is due | MongoDB |
| aqie-notify-service | Backend | Sole holder of the GOV.UK Notify key — the only route to contact a citizen | MongoDB |
| aqie-forecast-api | Backend | Collects Met Office forecast files and serves forecast data and the forecast summary | MongoDB |

### Historic data and location

| Component | Kind | Role | Stores |
|---|---|---|---|
| aqie-dataselector-frontend | Frontend | Citizen UI for finding stations, viewing recent readings and requesting historic extracts | Redis (session only) |
| aqie-historicaldata-backend | Backend | Builds historic measurement extracts (C#/.NET) | MongoDB, AWS S3 |
| aqie-location-backend | Backend | Brokers Ordnance Survey place-name search | MongoDB (template scaffolding only, no application data) |
| aqie-monitoringstation-backend | Backend | Finds stations near a place by combining station and location data | MongoDB (stations cache) |

### Smoke control register

| Component | Kind | Role | Stores |
|---|---|---|---|
| aqie-dc-frontend | Frontend | Public read-only register search | Redis (session only) |
| aqie-dc-admin-frontend | Frontend | Internal caseworker review interface; Microsoft Entra sign-in enforced | Redis (session only) |
| aqie-dc-backend | Backend | Owns appliance/fuel registers and case lifecycle | MongoDB, AWS SQS (consumed only) |

### Air quality maps

| Component | Kind | Role | Stores |
|---|---|---|---|
| aqie-maps-frontend | Frontend | Interactive map over station DAQI and forecast data | Redis (session cache engine only, nothing stored) |

### Pollutant release and transfer register

| Component | Kind | Role | Stores |
|---|---|---|---|
| aqie-prtr-frontend | Frontend | Citizen search over industrial pollutant releases | Redis (session cache only) |
| aqie-prtr-backend | Backend | Owns the industrial facility release dataset | MongoDB, AWS S3 (read-only: lists and pre-signs annual dataset files) |
| aqie-prtr-submissions-frontend | Frontend | CDP template scaffold for a PRTR submissions service; no submission feature yet | Redis (session cache only) |
| aqie-prtr-submissions-backend | Backend | CDP template scaffold for a PRTR submissions service; health and example routes only | MongoDB (template collections only) |

Draw `aqie-prtr-submissions-frontend` and `aqie-prtr-submissions-backend` as unconnected nodes
inside the PRTR container with the note "template scaffold — no connection to any other
service (oq-032)". They share the `aqie-prtr-` name with the register services, but no
connection exists between any of the four.

### Analytics and reporting

| Component | Kind | Role | Stores |
|---|---|---|---|
| aqie-laqm-data-explorer | Frontend | Explorer over the external LAQM Portal API | — |
| aqie-kpi-metrics-dashboard | Frontend | Standalone KPI dashboard — no backend, no AQIE data source | Browser localStorage |

Draw `aqie-kpi-metrics-dashboard` as an unconnected node inside the analytics container with
the note "no data source — calculates client-side from an uploaded spreadsheet".

### External systems (boundary nodes only — do not model their internals)

| Component | Owner | Data crossing the boundary |
|---|---|---|
| Ricardo UK-AIR API | Ricardo Energy & Environment for DEFRA | Monitoring station metadata, pollutant measurements, DAQI and summary alerts |
| Met Office forecast SFTP | Met Office (hosting service operator to be confirmed) | Air quality forecast files |
| DEFRA UK-AIR website | DEFRA | Forecast RSS feed |
| DEFRA Sensor Observation Service (SOS) | DEFRA | Site and feature-of-interest listings and hourly observations |
| DEFRA UK-AIR INSPIRE Atom | DEFRA | Historic observation XML per site and year |
| LAQM Portal API | Operator unconfirmed (oq-007) | Local authority reference data, diffusion tube and AQMA data |
| DEFRA Forms | DEFRA Forms team | Smoke control application submissions |
| Ordnance Survey Names API | Ordnance Survey | Place-name and gazetteer search results |
| Ordnance Survey Places (NI) | Ordnance Survey | Northern Ireland postcode and address lookup |
| postcodes.io | Ideal Postcodes | Station coordinates to local authority |
| GOV.UK Notify | GDS | Outbound alert and verification emails and SMS |
| OpenFreeMap | Third party | Browser-side vector map tiles (acceptable as a production dependency? oq-008) |
| Microsoft Entra ID | DEFRA IT | Staff sign-in tokens, and a client-credentials token for the NI lookup |
| CDP Uploader | DEFRA Core Delivery Platform | Virus-scanned file upload; the scan callback to aqie-dc-backend no longer has a handler (platform service) |

## Connections

All are confirmed. No connection is provisional or inferred at 2026-11-19.

**Core citizen service**

1. aqie-front-end → aqie-back-end: current pollutant readings and station detail for the searched location
2. aqie-front-end → aqie-forecast-api: multi-day forecast DAQI and the forecast summary narrative
3. aqie-front-end → Ordnance Survey Names API: place name to coordinates
4. aqie-front-end → Microsoft Entra ID: client-credentials token for the NI lookup
5. aqie-front-end → Ordnance Survey Places (NI): NI postcode lookup
6. aqie-back-end → Ricardo UK-AIR API: station metadata, pollutant metadata and measurements for per-station DAQI — scheduled batch (by default stations every 6 hours and at start-up, DAQI every 30 minutes)
7. aqie-back-end → Ricardo UK-AIR API: live readings for current conditions and station history — synchronous, on every request, label `live per request` (1 + 5N upstream calls for N stations, no timeout or retry — oq-031)
8. aqie-back-end → postcodes.io: station coordinates to local authority — scheduled batch, during the station refresh
9. aqie-back-end → Met Office forecast SFTP: forecast files read on request — not scheduled, not stored, no consumer recorded
10. aqie-back-end → DEFRA Sensor Observation Service (SOS): hourly sweep of site listings and observations — scheduled batch, output unread since PR #163 (oq-019)
11. aqie-back-end → DEFRA UK-AIR website: forecast RSS feed — scheduled batch, output unread since PR #163 (oq-019)

**Alerts**

12. aqie-front-end → aqie-alert-back-end-service: create and remove subscriptions; alert content
13. aqie-front-end → aqie-notify-service: verify email or mobile before subscribing
14. aqie-alert-back-end-service → Ricardo UK-AIR API: DAQI and summary report alerts — scheduled batch
15. aqie-alert-back-end-service → aqie-forecast-api: forecast DAQI for alert conditions — scheduled batch
16. aqie-alert-back-end-service → aqie-notify-service: send message per matched subscriber
17. aqie-alert-back-end-service → aqie-front-end: unsubscribe and location deep links (link construction, not a runtime call)
18. aqie-notify-service → GOV.UK Notify: emails and SMS out; inbound SMS replies back
19. aqie-notify-service → aqie-alert-back-end-service: SMS "STOP" reply triggers opt-out
20. aqie-notify-service → aqie-front-end: email verification deep link (link construction)
21. aqie-forecast-api → Met Office forecast SFTP: poll and parse forecast files — scheduled batch

**Historic data and location**

22. aqie-dataselector-frontend → aqie-historicaldata-backend: extract selection, job status, download link
23. aqie-dataselector-frontend → aqie-location-backend: place-name resolution
24. aqie-dataselector-frontend → aqie-monitoringstation-backend: stations near the selected location, and one station by coordinates
25. aqie-dataselector-frontend → aqie-back-end: hourly history and summary figures for a station page
26. aqie-dataselector-frontend → LAQM Portal API: local authority picker list
27. aqie-historicaldata-backend → DEFRA UK-AIR INSPIRE Atom: historic observation XML, fetched per extract
28. aqie-historicaldata-backend → Ricardo UK-AIR API: AURN site metadata
29. aqie-historicaldata-backend → LAQM Portal API: local authority areas and diffusion tube data
30. aqie-historicaldata-backend → aqie-notify-service: email the extract download link — asynchronous
31. aqie-location-backend → Ordnance Survey Names API: gazetteer search
32. aqie-monitoringstation-backend → aqie-back-end: station metadata, also refreshed on a schedule into a local stations cache
33. aqie-monitoringstation-backend → aqie-location-backend: resolve location to coordinates

**Smoke control**

34. DEFRA Forms → aqie-dc-backend: application submissions over AWS SQS — asynchronous, long-polled every 15 minutes by default
35. aqie-dc-backend → CDP Uploader: bulk register import upload and scan status — register import only, and the scan callback no longer has a handler (oq-025)
36. aqie-dc-admin-frontend → aqie-dc-backend: case records, technical review decisions, certification and visibility (GET and PATCH only)
37. aqie-dc-admin-frontend → Microsoft Entra ID: staff sign-in over OIDC
38. aqie-dc-frontend → aqie-dc-backend: public register search — label this `register search (paths not served — see oq-006)`

**Maps**

39. aqie-maps-frontend → aqie-back-end: stations and AURN DAQI for the map layer
40. aqie-maps-frontend → aqie-forecast-api: forecast data for the map
41. aqie-maps-frontend → OpenFreeMap: vector base map tiles, fetched by the browser
42. aqie-dataselector-frontend → aqie-maps-frontend: browser link and form post to the map — user redirect, not a server call
43. aqie-maps-frontend → aqie-dataselector-frontend: browser form post to open a station's data page — user redirect, not a server call

**PRTR**

44. aqie-prtr-frontend → aqie-prtr-backend: facility search, detail and annual reports
45. aqie-prtr-backend → aqie-location-backend: place-name resolution

**Analytics**

46. aqie-laqm-data-explorer → LAQM Portal API: local authority, diffusion tube and AQMA data

## Points to flag on the diagram

- No connection is unconfirmed, so no edge is dashed or dotted grey. aqie-back-end has no
  notification code (oq-001, answered), so GOV.UK Notify is reached only through
  aqie-notify-service.
- Edge 38 (aqie-dc-frontend → aqie-dc-backend) is confirmed as a call, but the paths it
  calls are not served by the backend. Add a small red warning note next to it (oq-006).
- aqie-notify-service is the only holder of the GOV.UK Notify key. Make that visually
  obvious — every citizen message funnels through it (edges 13, 16 and 30).
- Edges 10 and 11 write data that nothing reads since PR #163. Add a small grey note:
  "output unread — oq-019". Edge 9 is read on request, not scheduled and not stored.
- Edge 12 includes an SMS-journey call, `GET /api/subscriptions/{contact}`, that the alert
  backend does not serve. Add a small red note: "one route not served, call fails open
  (oq-015)".
- Edges 36 and 38 send an `x-api-key` header that aqie-dc-backend never validates. Add a small
  note: "key not checked by the backend (oq-022)".
- aqie-dc-admin-frontend enforces Microsoft Entra sign-in (since PR #19). Add a note: "any
  signed-in account in the tenant is accepted (oq-021); SSO_ENABLED=false bypasses sign-in
  (oq-020)".
- Edge 35 is register import only. Add a small grey note: "import no longer completes — callback
  removed (oq-025)".
- Edges 17, 20, 42 and 43 are links or form posts in the citizen's browser, not server calls.
  Label them `deep link only`. For 42 and 43 add the note "addresses must be reachable from a
  citizen's browser (oq-035)".
