<!-- Generated from /draw-io-generation/generation-config.yaml on 2026-11-19.
     Facts sourced from /docs/integration-catalog.yaml.
     Detail level: medium. Paste this whole file into one next-ai-draw-io conversation. -->

# Prompt: Journey — scheduled air quality data ingestion

Create a draw.io sequence diagram showing how measurement and forecast data enters the
DEFRA Air Quality estate. These run on cron schedules, never on user request. Four independent
pipelines are shown: Ricardo stations and DAQI, the UK-AIR site and observation sweep, the
UK-AIR forecast feed, and the Met Office forecast files. Use exactly the participants and
steps below, in order.

## Diagram conventions

- Sequence diagram, time flowing top to bottom, numbered steps.
- Participant fills:
  - Scheduler — fill `#E1D5E7`, stroke `#9673A6`
  - Backend — fill `#D5E8D4`, stroke `#82B366`
  - External system — fill `#F5F5F5`, stroke `#666666`
  - Data store — fill `#FFF2CC`, stroke `#D6B656`, cylinder shape
- Solid arrows for confirmed calls, dashed grey `#999999` for anything marked provisional.
  Every call below is confirmed, so draw all of them solid.
- Group the steps into four labelled blocks: `1. Stations and DAQI (Ricardo)`,
  `2. UK-AIR site and observation sweep (SOS)`, `3. UK-AIR forecast feed (RSS)` and
  `4. Forecasts (Met Office SFTP)`.
- Add a legend box in the bottom-left.

## Participants

| Participant | Type |
|---|---|
| Scheduler (cron) | Scheduler |
| aqie-back-end | Backend |
| Ricardo UK-AIR API | External |
| postcodes.io | External |
| MongoDB (aqie-back-end) | Data store |
| DEFRA Sensor Observation Service (SOS) | External |
| DEFRA UK-AIR website | External |
| aqie-forecast-api | Backend |
| Met Office forecast SFTP | External |
| MongoDB (aqie-forecast-api) | Data store |

## Steps

**Block 1: Stations and DAQI (Ricardo)**

1. Scheduler (cron) → aqie-back-end: cron trigger — `MONITORING_STATIONS_SCHEDULE` (every 6 hours by default, and once at start-up) for the station refresh, `AURN_SCHEDULE` (every 30 minutes by default) for the DAQI recalculation
2. aqie-back-end → Ricardo UK-AIR API: `POST /api/login_check` — obtain bearer token
3. Ricardo UK-AIR API → aqie-back-end: bearer token
4. aqie-back-end → Ricardo UK-AIR API: `GET /api/site_meta_datas`, `GET /api/pollutant_metadatas` — stations and instrument dates
5. aqie-back-end → postcodes.io: `GET /postcodes` — resolve station local authority
6. aqie-back-end → MongoDB (aqie-back-end): replace the `monitoringStations` cache
7. aqie-back-end → Ricardo UK-AIR API: `GET /api/pollutant_measurement_datas` — yesterday and today, five stations at a time
8. aqie-back-end → MongoDB (aqie-back-end): upsert per-station DAQI (`aurnMeasurements`)

**Block 2: UK-AIR site and observation sweep (SOS) — output unread since PR #163**

9. Scheduler (cron) → aqie-back-end: cron trigger — `POLLUTANTS_SCHEDULE` (hourly by default; cron only, no run at start-up)
10. aqie-back-end → DEFRA Sensor Observation Service (SOS): `GET /data/API/site-process-featureofinterest-by-region` — site and feature-of-interest listing for each of 16 regions
11. aqie-back-end → DEFRA Sensor Observation Service (SOS): `GET /sos-ukair/service?service=AQD&version=1.0.0&request=GetObservation` — one `GetObservation` per pollutant per site
12. aqie-back-end → MongoDB (aqie-back-end): write `measurements` and `historicalMeasurements` — nothing reads them since PR #163

**Block 3: UK-AIR forecast feed (RSS) — output unread since PR #163**

13. Scheduler (cron) → aqie-back-end: cron trigger — `FORECAST_SCHEDULE` (hourly from 05:00 to 10:00 by default, and once at start-up)
14. aqie-back-end → DEFRA UK-AIR website: `GET /assets/rss/forecast.xml`
15. DEFRA UK-AIR website → aqie-back-end: RSS items with location, publication date and a short per-day forecast
16. aqie-back-end → MongoDB (aqie-back-end): write `forecasts` and `historicalForecasts` — nothing reads them since PR #163

**Block 4: Forecasts (Met Office SFTP)**

17. Scheduler (cron) → aqie-forecast-api: cron trigger (`FORECAST_SCHEDULE`, daily by default, with in-day retries on `FORECAST_RETRY_INTERVAL`)
18. aqie-forecast-api → Met Office forecast SFTP: poll the configured directory over SFTP
19. Met Office forecast SFTP → aqie-forecast-api: forecast files
20. aqie-forecast-api → MongoDB (aqie-forecast-api): persist parsed forecast documents

## Notes to add to the diagram

- Add a note on the four blocks: "independent pipelines — no data passes between them".
- Add a grey note spanning blocks 2 and 3: "both write to MongoDB, but nothing has read the
  output since the `/measurements` and `/forecasts` endpoints were removed (PR #163). Retire
  the schedulers and collections? (oq-019)".
- Add a side note on aqie-back-end, drawn greyed outside the blocks: "also reads Met Office
  forecast files over SFTP on request (`GET /sftp/files`, `GET /sftp/file/{filename}`) — not
  scheduled, not stored, no consumer recorded".
- Add a note on steps 7 and 8: "a station that fails the 75% data-capture rule is skipped and
  keeps its previous record (oq-030). Whether Ricardo honours the date parameters sent in
  step 7 is unconfirmed (oq-029)".
- Add a grey note on step 2: "the code default for the four Ricardo URL variables is the
  supplier's staging host, so removing a variable would silently select staging (oq-012,
  partly answered, low severity)".
- Add a note: "aqie-back-end ingest jobs take a lock by inserting into a `locks` collection
  with a one-hour expiry, so only one instance runs a job; the start-up station refresh takes
  no lock. aqie-forecast-api takes a `mongo-locks` distributed lock before each run".
