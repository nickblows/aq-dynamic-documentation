  <!-- Generated from /draw-io-generation/generation-config.yaml on 2026-11-19.
      Facts sourced from /docs/repository-catalog.yaml and /docs/integration-catalog.yaml.
      Detail level: medium. Paste this whole file into one next-ai-draw-io conversation. -->

  # Prompt: AQIE data flow

  Create a draw.io data flow diagram showing how air quality data enters the DEFRA Air
  Quality (AQIE) estate, where it is stored, and how it reaches citizens. Use exactly the
  components and flows below. Do not invent any component or flow that is not listed.

  ## Diagram conventions

  - Orientation: strictly left to right, in five labelled vertical lanes:
    `1. External data sources` → `2. Ingest and own` → `3. Broker and aggregate` →
    `4. Serve` → `5. Consumers`.
  - Node fills:
    - External source — fill `#F5F5F5`, stroke `#666666`
    - Backend service — fill `#D5E8D4`, stroke `#82B366`
    - Frontend service — fill `#DAE8FC`, stroke `#6C8EBF`
    - Data store — fill `#FFF2CC`, stroke `#D6B656`, cylinder shape
    - People — actor shape
  - Edge styles carry certainty:
    - Confirmed flow — solid line, black
    - Provisional flow — dashed line, grey `#999999`, label suffixed `(provisional — to confirm)`
    - Every flow below is confirmed, so draw all of them solid; keep both styles in the legend.
  - Label every ingestion edge with the data that crosses it and its cadence
    (`scheduled` or `on demand`).
  - Add a legend box in the bottom-left explaining the fills and line styles.

  ## Key principle to convey

  There are several independent ingestion routes, not one pipeline. Nothing flows between
  them. aqie-back-end caches only the station list and per-station DAQI, and reads current
  readings live from Ricardo on every request. Historic data is not derived from any of this —
  it is re-fetched from DEFRA UK-AIR on demand for every extract.

  ## Lane 1 — External data sources

  | Source | Data supplied |
  |---|---|
  | Ricardo UK-AIR API | Station metadata, pollutant measurements, DAQI and summary alerts |
  | Met Office forecast SFTP | Air quality forecast files |
  | DEFRA UK-AIR website | Forecast RSS feed |
  | DEFRA Sensor Observation Service (SOS) | Site and feature-of-interest listings and hourly observations |
  | DEFRA UK-AIR INSPIRE Atom | Historic observation XML, per site and per year |
  | LAQM Portal API | Local authority reference data, diffusion tube and AQMA data |
  | DEFRA Forms | Smoke control application submissions |
  | Ordnance Survey Names API | Place-name and gazetteer search |
  | Ordnance Survey Places (NI) | Northern Ireland postcode and address lookup |
  | postcodes.io | Station coordinates to local authority |

  ## Lane 2 — Ingest and own

  | Service | Owns | Store |
  |---|---|---|
  | aqie-back-end | Station cache and per-station DAQI. Also writes UK-AIR SOS and forecast RSS data that nothing reads (oq-019) | MongoDB |
  | aqie-forecast-api | Parsed Met Office forecasts | MongoDB |
  | aqie-alert-back-end-service | Alert subscribers and dispatch state | MongoDB |
  | aqie-historicaldata-backend | Extract jobs and reference data only | MongoDB, AWS S3 |
  | aqie-dc-backend | Appliance and fuel registers, applications and review history | MongoDB, AWS SQS (consumed only) |
  | aqie-prtr-backend | Industrial facility release records, loaded by an offline TSV ingest | MongoDB, AWS S3 (read-only) |
  | aqie-prtr-submissions-backend | Nothing yet — CDP template scaffold, no connections (oq-032) | MongoDB (template collections only) |

  ## Lane 3 — Broker and aggregate

  | Service | Function | Store |
  |---|---|---|
  | aqie-location-backend | Brokers Ordnance Survey place-name search | MongoDB (template scaffolding only, no application data) |
  | aqie-monitoringstation-backend | Combines station and location data; caches the station list | MongoDB (stations cache) |
  | aqie-notify-service | Sole holder of the GOV.UK Notify key | MongoDB |

  ## Lane 4 — Serve

  aqie-front-end, aqie-maps-frontend, aqie-dataselector-frontend, aqie-prtr-frontend,
  aqie-dc-frontend, aqie-dc-admin-frontend, aqie-laqm-data-explorer, and
  aqie-prtr-submissions-frontend (CDP template scaffold — no data flows to or from it, oq-032).

  ## Lane 5 — Consumers

  Citizen (actor), Caseworker (actor), GOV.UK Notify (email and SMS delivery).

  ## Flows

  **Ingestion — scheduled**

  1. Ricardo UK-AIR API → aqie-back-end: station metadata, pollutant metadata and measurements for per-station DAQI — scheduled (`MONITORING_STATIONS_SCHEDULE` every 6 hours and at start-up, `AURN_SCHEDULE` every 30 minutes, by default)
  2. postcodes.io → aqie-back-end: local authority for station coordinates — scheduled, during the station refresh
  3. DEFRA SOS → aqie-back-end: site and feature-of-interest listings and hourly observations — scheduled (`POLLUTANTS_SCHEDULE`, hourly by default); output unread since PR #163 (oq-019)
  4. DEFRA UK-AIR website → aqie-back-end: forecast RSS feed — scheduled (`FORECAST_SCHEDULE`, hourly from 05:00 to 10:00 by default, and at start-up); output unread since PR #163 (oq-019)
  5. Met Office forecast SFTP → aqie-forecast-api: forecast files, polled and parsed — scheduled (`FORECAST_SCHEDULE`, daily by default)
  6. Ricardo UK-AIR API → aqie-alert-back-end-service: DAQI and air quality summary report alerts — scheduled
  7. DEFRA Forms → aqie-dc-backend: application submissions over AWS SQS — asynchronous, long-polled every 15 minutes by default

  **Ingestion — on demand**

  8. Ricardo UK-AIR API → aqie-back-end: current readings and station history, read live on every request (1 + 5N calls for `/monitoringStationInfo`) — on demand
  9. Met Office forecast SFTP → aqie-back-end: forecast files read through the service's own `/sftp` routes — on demand; not stored, no consumer recorded
  10. DEFRA UK-AIR INSPIRE Atom → aqie-historicaldata-backend: historic observation XML, re-fetched for every extract — on demand
  11. Ricardo UK-AIR API → aqie-historicaldata-backend: AURN site metadata — on demand
  12. LAQM Portal API → aqie-historicaldata-backend: local authority areas and diffusion tube data — on demand
  13. LAQM Portal API → aqie-dataselector-frontend: local authority picker list — on demand (12-hour in-process cache)
  14. LAQM Portal API → aqie-laqm-data-explorer: local authority, diffusion tube and AQMA data — on demand
  15. Ordnance Survey Names API → aqie-location-backend: gazetteer matches — on demand
  16. Ordnance Survey Names API → aqie-front-end: gazetteer matches — on demand
  17. Ordnance Survey Places (NI) → aqie-front-end: NI postcode matches — on demand

  **Persistence**

  18. aqie-back-end → MongoDB: replace the station cache and upsert per-station DAQI (`monitoringStations`, `aurnMeasurements`); also write `measurements`, `historicalMeasurements`, `forecasts` and `historicalForecasts`, which nothing reads since PR #163 (oq-019)
  19. aqie-forecast-api → MongoDB: persist parsed forecast documents
  20. aqie-alert-back-end-service → MongoDB: subscriber records and dispatch state
  21. aqie-monitoringstation-backend → MongoDB: stations cache, refreshed from aqie-back-end (`STATIONS_SYNC_SCHEDULE`, every 6 hours by default and at start-up)
  22. aqie-historicaldata-backend → MongoDB: extract job documents and reference data — no measurements
  23. aqie-historicaldata-backend → AWS S3: stage generated extract files, and read the two reference spreadsheets
  24. aqie-dc-backend → MongoDB: applications, appliances, fuels and review history
  25. aqie-prtr-backend → AWS S3: read-only — lists the annual dataset XML files and issues time-limited pre-signed download URLs. Nothing in the PRTR repositories writes to the bucket, and who uploads the files is open (oq-010)

  **Serving**

  26. aqie-back-end → aqie-front-end: current pollutant readings and station detail (the front end derives the DAQI bands itself)
  27. aqie-back-end → aqie-maps-frontend: stations and AURN DAQI for the map layer
  28. aqie-back-end → aqie-dataselector-frontend: hourly history and summary figures for a station page
  29. aqie-back-end → aqie-monitoringstation-backend: full station dataset, also pulled on a schedule into the stations cache
  30. aqie-forecast-api → aqie-front-end: multi-day forecast DAQI and the forecast summary narrative
  31. aqie-forecast-api → aqie-maps-frontend: forecast data for the map
  32. aqie-forecast-api → aqie-alert-back-end-service: forecast DAQI for alert conditions
  33. aqie-location-backend → aqie-dataselector-frontend, aqie-monitoringstation-backend, aqie-prtr-backend: resolved place names
  34. aqie-monitoringstation-backend → aqie-dataselector-frontend: stations near the selected location, and one station by coordinates
  35. aqie-historicaldata-backend → aqie-dataselector-frontend: extract job status and download link
  36. aqie-prtr-backend → aqie-prtr-frontend: facility search results, detail and report links
  37. AWS S3 → aqie-prtr-frontend: annual dataset XML, streamed to the citizen through the pre-signed URL
  38. aqie-dc-backend → aqie-dc-frontend: published register records — the routes the frontend calls are not served (oq-006)
  39. aqie-dc-backend → aqie-dc-admin-frontend: application case records for review
  40. aqie-maps-frontend → aqie-dataselector-frontend: selected station coordinates and name, by browser form post — on demand (oq-035)
  41. aqie-dataselector-frontend → aqie-maps-frontend: station coordinates and site id, by browser link or form post — on demand (oq-035)

  **Out to people**

  42. aqie-front-end → Citizen: location page with DAQI, pollutants and forecast
  43. aqie-maps-frontend → Citizen: interactive air quality map
  44. aqie-dataselector-frontend → Citizen: station readings, historic extract selection and download
  45. aqie-prtr-frontend → Citizen: industrial pollutant release records
  46. aqie-dc-frontend → Citizen: smoke control register search (likely non-functional, oq-006)
  47. aqie-dc-admin-frontend → Caseworker: application review interface
  48. aqie-alert-back-end-service → aqie-notify-service → GOV.UK Notify → Citizen: air quality alerts by email and SMS
  49. aqie-historicaldata-backend → aqie-notify-service → GOV.UK Notify → Citizen: extract download link by email, for multi-year requests and jobs still running after three minutes
  50. AWS S3 → Citizen: generated extract, downloaded by the browser through the pre-signed URL (aqie-dataselector-frontend first checks that the URL responds)

  ## Points to flag on the diagram

  - Annotate aqie-historicaldata-backend with "holds no historic measurements — re-fetches
    from UK-AIR per extract".
  - Annotate aqie-notify-service with "sole holder of the GOV.UK Notify key".
  - No flow is unconfirmed, so no flow is dashed grey. aqie-back-end has no notification code
    (oq-001, answered), so GOV.UK Notify is reached only through aqie-notify-service.
  - Flows 3 and 4, and the second half of flow 18, are written but never read since PR #163.
    Add a small grey note: "output unread — oq-019". Flow 9 is on request only, not stored.
  - Flow 38 is confirmed as a call but the routes are not served. Add a small red note:
    "likely non-functional — oq-006".
  - Add a note on flow 25: "read-only; who uploads the annual files is unknown (oq-010)".
  - Flow 7: add a note "failed messages stay on the queue; redrive and dead-letter handling
    unconfirmed (oq-027)". aqie-dc-backend only consumes the queue and has no S3 store.
  - Flow 49: add a note "the link is built by aqie-historicaldata-backend and passed to
    aqie-notify-service. Expiry policy is open: 48 hours is enforced only in
    aqie-dataselector-frontend, against an unsigned timestamp, while the backend issues
    seven-day pre-signed URLs with no age check (oq-034, partly answered)".
  - Flows 40 and 41 are browser links and form posts, not server calls. Label them
    `deep link only`.
  - Draw aqie-prtr-submissions-frontend and aqie-prtr-submissions-backend unconnected, with
    the note "template scaffold — no data flows (oq-032)".
