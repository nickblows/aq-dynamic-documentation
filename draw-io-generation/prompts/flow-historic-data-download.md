<!-- Generated from /draw-io-generation/generation-config.yaml on 2026-11-19.
     Facts sourced from /docs/integration-catalog.yaml.
     Detail level: medium. Paste this whole file into one next-ai-draw-io conversation. -->

# Prompt: Journey — citizen downloads historic air quality data

Create a draw.io sequence diagram of the historic data journey. Two journeys share one
service: by station (search, recent readings and per-pollutant downloads) and custom dataset
(filters, then an extract job). A single-year extract downloads directly once the job
completes; multi-year requests, and any job still running after three minutes, are emailed
a link instead. Use exactly the participants and steps below, in order.

## Diagram conventions

- Sequence diagram, time flowing top to bottom, numbered steps.
- Participant fills:
  - Person — actor shape
  - Frontend — fill `#DAE8FC`, stroke `#6C8EBF`
  - Backend — fill `#D5E8D4`, stroke `#82B366`
  - External system — fill `#F5F5F5`, stroke `#666666`
  - Data store — fill `#FFF2CC`, stroke `#D6B656`, cylinder shape
- Solid arrows for confirmed calls, dashed grey `#999999` for anything marked provisional.
  Every call below is confirmed, so draw all of them solid.
- Group the steps into three labelled blocks: `1. By station`,
  `2. Custom dataset — direct download` and `3. Email path`.
- Show the polling step as a loop block labelled `poll every 2 s, up to 3 min`.
- Add a legend box in the bottom-left.

## Participants

| Participant | Type |
|---|---|
| Citizen | Person |
| aqie-dataselector-frontend | Frontend |
| aqie-location-backend | Backend |
| aqie-monitoringstation-backend | Backend |
| aqie-back-end | Backend |
| LAQM Portal API | External |
| aqie-historicaldata-backend | Backend |
| DEFRA UK-AIR INSPIRE Atom | External |
| AWS S3 | Data store |
| aqie-notify-service | Backend |
| GOV.UK Notify | External |

## Steps

**Block 1: By station**

1. Citizen → aqie-dataselector-frontend: search a place name or postcode
2. aqie-dataselector-frontend → aqie-location-backend: `POST /osnameplaces` — resolve location
3. aqie-dataselector-frontend → aqie-monitoringstation-backend: `POST /monitoringstation` — find nearby stations
4. aqie-monitoringstation-backend → aqie-back-end: `GET /monitoringStationInfo` — station list
5. aqie-dataselector-frontend → aqie-back-end: `GET /monitoringStationHistory` — last 24 hours and 7 days for the chosen station
6. aqie-dataselector-frontend → aqie-historicaldata-backend: `POST /AtomHistoryHourlydata` — single-station download link

**Block 2: Custom dataset — direct download**

7. Citizen → aqie-dataselector-frontend: choose pollutants, data sources and locations
8. aqie-dataselector-frontend → aqie-historicaldata-backend: `GET /AtomDataSelectionPollutantMaster` and `POST /AtomDataSelectionPollutantDataSource` — selectable pollutants, and the data sources for the chosen pollutant
9. aqie-dataselector-frontend → LAQM Portal API: `GET /xapi/getLocalAuthorities/json` — local authority picker list
10. aqie-dataselector-frontend → aqie-historicaldata-backend: `GET /AtomDataSelectionRegionMaster`, `GET /AtomDataSelectionAgglomerationMaster`, and `POST /AtomDataSelection` with count parameters — live station count
11. aqie-dataselector-frontend → aqie-historicaldata-backend: `POST /AtomDataSelection` — create the extract job
12. aqie-historicaldata-backend → aqie-dataselector-frontend: job reference
13. Loop `poll every 2 s, up to 3 min`: aqie-dataselector-frontend → aqie-historicaldata-backend: `POST /AtomDataSelectionJobStatus`
14. aqie-historicaldata-backend → DEFRA UK-AIR INSPIRE Atom: fetch observation XML per site and year
15. aqie-historicaldata-backend → AWS S3: stage the generated extract
16. aqie-dataselector-frontend → Citizen: pre-signed download link once the job completes

**Block 3: Email path — multi-year requests, or a job still running after three minutes**

17. Citizen → aqie-dataselector-frontend: enter an email address
18. aqie-dataselector-frontend → aqie-historicaldata-backend: `POST /AtomEmailJobDataSelection` — register the email job; the backend answers `Success` and builds nothing yet
19. aqie-historicaldata-backend → aqie-notify-service: `POST /send-notification` — a background sweep re-runs the whole extract (Atom fetch, S3 upload), then sends the recipient, the Notify template id and the download link as personalisation
20. aqie-notify-service → GOV.UK Notify: send the email
21. GOV.UK Notify → Citizen: email linking to the frontend page `/download_emailreq/{id}/{timestamp}` (assumed: the link's base address is deployed configuration, the only matching route is on aqie-dataselector-frontend)
22. Citizen → aqie-dataselector-frontend: follow the link (rejected after 48 hours)
23. aqie-dataselector-frontend → aqie-historicaldata-backend: `POST /AtomDataSelectionPresignedUrlMail` — fresh pre-signed URL
24. aqie-dataselector-frontend → Citizen: download page with the pre-signed link

## Notes to add to the diagram

- Add a prominent note on aqie-historicaldata-backend: "holds no historic measurements.
  It re-fetches observation XML from the public DEFRA UK-AIR Atom service for every
  extract, and stores only job state and reference data."
- Add a note on step 14: "AURN site lists resolved from Ricardo UK-AIR; non-AURN from a
  station master list in MongoDB. Local authority selections use coordinates from the LAQM
  Portal to find sites within about five miles".
- Add a note on step 5: "AURN stations only — a station without an AURN site id never makes
  this call and shows 'not available'. aqie-back-end caches each site id and period for 15
  minutes".
- Add a note on steps 3 and 4: "aqie-monitoringstation-backend returns HTTP 400 for upstream
  failures, and the search page treats any failure as no stations (oq-028)".
- Add a note on step 19: "the background sweep runs at start-up and then every
  `TIME_INTERVAL` minutes (default 45). aqie-historicaldata-backend builds the link from the
  configured `EMAIL_BASEADDRESS`, the job id and the job's creation time in Unix
  milliseconds".
- Add a note on steps 21 to 23: "expiry policy is open (oq-034, partly answered). The 48-hour
  rule is checked only in aqie-dataselector-frontend, against an unsigned timestamp, while
  aqie-historicaldata-backend issues a fresh seven-day pre-signed URL for any known job
  reference and has no age check. The frontend checks that the URL responds before showing
  the download page".
- Add a note: "a station opened from aqie-maps-frontend arrives by browser form post to
  `POST /station-summary` and is looked up with `GET /monitoringstation/by-location`. The
  cross-link addresses must be reachable from a citizen's browser (oq-035)".
- Add a note on aqie-notify-service: "sole holder of the GOV.UK Notify key".
- Add a note: "this is the one C#/.NET service in the estate; the other services in this
  journey are Node.js".
