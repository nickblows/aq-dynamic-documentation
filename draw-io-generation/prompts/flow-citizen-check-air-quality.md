<!-- Generated from /draw-io-generation/generation-config.yaml on 2026-11-19.
     Facts sourced from /docs/integration-catalog.yaml.
     Detail level: medium. Paste this whole file into one next-ai-draw-io conversation. -->

# Prompt: Journey — citizen checks air quality for a location

Create a draw.io sequence diagram of the primary public journey on
check-air-quality.service.gov.uk. Use exactly the participants and steps below, in order.

## Diagram conventions

- Sequence diagram, time flowing top to bottom, numbered steps.
- Participant fills:
  - Person — actor shape
  - Frontend — fill `#DAE8FC`, stroke `#6C8EBF`
  - Backend — fill `#D5E8D4`, stroke `#82B366`
  - External system — fill `#F5F5F5`, stroke `#666666`
- Solid arrows for confirmed calls, dashed grey `#999999` for anything marked provisional.
- Return messages as dashed arrows back to the caller.
- Add a legend box in the bottom-left.

## Participants

| Participant | Type |
|---|---|
| Citizen | Person |
| aqie-front-end | Frontend |
| Ordnance Survey Names API | External |
| aqie-back-end | Backend |
| Ricardo UK-AIR API | External |
| aqie-forecast-api | Backend |

## Steps

1. Citizen → aqie-front-end: search a place name or postcode
2. aqie-front-end → Ordnance Survey Names API: `GET /search/names/v1/find` — resolve place to coordinates
3. Ordnance Survey Names API → aqie-front-end: matched places with coordinates
4. aqie-front-end → aqie-back-end: `GET /monitoringStationInfo` — stations near coordinates
5. aqie-back-end → Ricardo UK-AIR API: `POST /api/login_check`, then `GET /api/site_meta_datas`
6. aqie-back-end → Ricardo UK-AIR API: `GET /api/pollutant_measurement_datas` — five calls per
   station, one per pollutant. Draw this as a loop container labelled
   `for each station × each of 5 pollutants`
7. aqie-back-end → aqie-front-end: station metadata and current pollutant concentrations
8. aqie-front-end → aqie-forecast-api: `GET /forecast` — multi-day outlook
9. aqie-forecast-api → aqie-front-end: forecast DAQI by day and region, plus the forecast summary narrative
10. aqie-front-end → Citizen: rendered location page with DAQI, pollutants and forecast

## Notes to add to the diagram

- Add a note on aqie-back-end: "reads current readings live from Ricardo UK-AIR on every
  request — one site list call plus five calls per station, with no response cache and no
  timeout or retry (oq-031)". The scheduled station and DAQI ingest is a separate pipeline and
  is not part of this journey.
- Add a note on aqie-front-end: "holds Redis session and response cache only; no
  authoritative data. It works out the DAQI bands itself from the concentrations".
- Add a note on step 9: "the national forecast narrative comes from aqie-forecast-api — the
  front end does not call the UK-AIR website".
- Northern Ireland postcodes take a different path: aqie-front-end obtains a
  client-credentials token from Microsoft Entra ID and calls Ordnance Survey Places (NI).
  There is no postcodes.io fallback. Show this as a side note rather than extra steps.
