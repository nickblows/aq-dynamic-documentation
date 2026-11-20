<!-- Generated from /draw-io-generation/generation-config.yaml on 2026-11-19.
     Facts sourced from /docs/services/data/aqie-historicaldata-backend/service-profile.md
     and /docs/integration-catalog.yaml, except where marked "reported, not yet evidenced".
     Detail level: high. Paste this whole file into one next-ai-draw-io conversation. -->

# Prompt: How historic measurement data is collected from the DEFRA UK-AIR Atom feed

Create a draw.io pipeline diagram showing how `aqie-historicaldata-backend` collects historic
air quality measurements from the DEFRA UK-AIR INSPIRE Atom download service in real time.
Use exactly the components and steps below. Do not invent any component or step.

## The single most important message

**AQIE stores no historic measurement data.** `aqie-historicaldata-backend` holds only job
state and reference data. Every extract re-fetches observation XML from the public DEFRA
UK-AIR Atom download service, one file per site per year, at the moment the citizen asks for
it. Availability of historic data is therefore governed entirely by UK-AIR, not by AQIE.

Make this unmissable: put it in a banner note at the top of the diagram, and label the
MongoDB store explicitly as "job state and reference data only — no measurements".

## Diagram conventions

- Orientation: left to right, with five labelled phase containers:
  `1. Selection` → `2. Resolve sites` → `3. Fetch Atom feed` → `4. Parse and classify` →
  `5. Build and deliver extract`.
- Node fills:
  - Frontend — fill `#DAE8FC`, stroke `#6C8EBF`
  - Backend service or internal component — fill `#D5E8D4`, stroke `#82B366`
  - External system — fill `#F5F5F5`, stroke `#666666`
  - Data store — fill `#FFF2CC`, stroke `#D6B656`, cylinder shape
  - Decision — diamond, fill `#FFFFFF`, stroke `#666666`
  - Person — actor shape
- Edge and node certainty:
  - Confirmed in code — solid line, black
  - Reported by the team but not yet evidenced in code — solid line, amber `#D79B00` fill
    `#FFE6CC`, label suffixed `(reported — to confirm)`
  - Provisional — dashed line, grey `#999999`
- Draw the per-site-per-year fetch as an explicit loop container labelled
  `for each site × each year in the selection`.
- Add a legend box in the bottom-left covering the fills, the line styles and the amber
  "reported — to confirm" convention.

## Components

| Component | Type | Notes |
|---|---|---|
| Citizen | Person | |
| aqie-dataselector-frontend | Frontend | Selection UI: pollutants, years, locations, networks |
| aqie-historicaldata-backend | Backend | C#/.NET; the only .NET service in the estate |
| `AtomDataSelectionStationService` | Internal component | Resolves which sites the selection covers |
| `AtomFeedFetchServiceBase` | Internal component | Builds the UK-AIR path, issues the request, handles response codes |
| `AtomFeedHelper` | Internal component | OM/SWE observation parsing and pollutant identifier extraction |
| CSV/ZIP export | Internal component | `HourlyAtomFeedExportCSV`, `DailyAtomFeedExportCSV`, `AnnualAtomFeedExportCSV`, `DataSelectionHourlyAtomFeedExportCSV` |
| Ricardo UK-AIR API | External | AURN site metadata and pollutant coverage — **metadata only, never measurements** |
| LAQM Portal API | External | Local authority areas and diffusion tube data — metadata only |
| DEFRA UK-AIR Atom download service | External | `uk-air.defra.gov.uk` — the actual measurements |
| MongoDB | Data store | Job documents and reference collections only |
| AWS S3 | Data store | Generated CSV/ZIP extracts and source reference spreadsheets |
| aqie-notify-service | Backend | Sends the email that carries the download link; the link itself is built by `aqie-historicaldata-backend` |
| GOV.UK Notify | External | Email delivery |

## Phase 1 — Selection

1. Citizen → aqie-dataselector-frontend: choose pollutants, years, region and data source
2. aqie-dataselector-frontend → aqie-historicaldata-backend: `POST /AtomDataSelection`
3. Decision — `count request or download request?`
   - Count: return station or network count immediately, journey ends
   - Download: continue. A single-year extract takes the direct route below; a multi-year
     request, or a direct download still running after three minutes, takes the email route
     in phase 5 (Path B), where nothing is built until a background sweep picks the job up
4. aqie-historicaldata-backend → MongoDB: create a job document in `aqie_csvexport_jobs`
   (direct route)
5. aqie-historicaldata-backend → aqie-dataselector-frontend: job reference returned
6. Note on the job: queued on an unbounded in-process channel, so the job is bound to the
   container that accepted it; job state itself is durable in MongoDB

## Phase 2 — Resolve which sites to ask for

7. `AtomDataSelectionStationService` → Ricardo UK-AIR API: `POST /api/login_check` then
   `GET /api/site_meta_datas?with-closed=true&with-pollutants=1` — AURN site metadata
8. `AtomDataSelectionStationService` → MongoDB: read `aqie_atom_non_aurn_networks_station_details`
   for non-AURN sites
9. `AtomDataSelectionLocalAuthoritiesService` → LAQM Portal API: local authority areas and
   diffusion tube data, with OS grid-reference conversion, so that sites within about five
   miles of the authority can be selected
10. `AtomDataSelectionStationBoundryService` → bundled GeoJSON boundaries: region containment
    test to filter sites to the selected region
11. Output: the list of site × year combinations the extract needs

Annotate this phase: "metadata only — neither Ricardo nor LAQM supplies measurements". Add a
second note on step 7: "no caching — every AURN selection and every region or agglomeration
master call logs in and downloads the full site list again".

## Phase 3 — Fetch the Atom feed (loop: for each site × each year)

12. Decision — `which path?`
    - AURN sites, and non-AURN networks 10, 11 and 13 (listed under the non-AURN source but
      fetched from the auto path) → `auto` branch
    - Other non-AURN networks → `non-auto` branch (data selection journey only)
13. `AtomFeedFetchServiceBase` → DEFRA UK-AIR Atom download service:
    `GET data/atom-dls/observations/auto/GB_FixedObservations_{year}_{siteID}.xml`
    or `GET data/atom-dls/observations/non-auto/GB_FixedObservations_{year}_{siteID}.xml`
    — public endpoint, no authentication. The single-station journey uses the auto path only.
14. Decision on the response:
    - `200` → INSPIRE Air Quality XML returned, continue to parsing
    - `304 Not Modified`, `404 Not Found`, `428` or any other non-success response → logged
      and treated as an empty result, **not an error**
15. Annotate the loop: "one HTTP request per site per year, issued one at a time, on every
    extract — nothing is cached as measurement history. This is why extracts are
    asynchronous jobs."

## Phase 4 — Parse and classify

16. `AtomFeedHelper`: parse OGC `om:OM_Observation` members from the INSPIRE XML
17. `AtomFeedHelper`: extract the observed-property identifier from each observation
18. `AtomFeedHelper` → MongoDB: match the identifier against
    `aqie_atom_non_aurn_networks_pollutant_master`
19. `AtomFeedHelper`: split the SWE data array into measurement rows
20. **Decision — `verified or unverified record?`** Draw this in amber as
    `(reported — to confirm)`. The feed carries both verified and unverified measurements and
    the service differentiates them using information supplied in the feed. Show two labelled
    outputs from this decision, `verified` and `unverified`, both flowing into the export step.
21. Add an amber note next to step 20: "Reported by the service team. The classification flag
    and how it is surfaced to the citizen are not yet recorded in the documentation — confirm
    the field name, the rule, and whether unverified rows are labelled, filtered or annotated
    in the output."

## Phase 5 — Build and deliver the extract

22. CSV/ZIP export: map observations to pollutants and build the extract file, period-specific
    (hourly, daily, annual)
23. aqie-historicaldata-backend → AWS S3: upload the artefact under a key derived from the
    selection
24. aqie-historicaldata-backend → MongoDB: write the pre-signed URL onto the job document —
    valid for 604800 seconds (seven days)
25. Path A — direct download, for a single-year extract: aqie-dataselector-frontend →
    aqie-historicaldata-backend `POST /AtomDataSelectionJobStatus`, polled every 2 seconds for
    up to 3 minutes in the browser journey, until the state is `Completed`; the citizen then
    follows the result URL. A job still running after 3 minutes moves to Path B.
26. Path B — email, for multi-year requests and for jobs still running after three minutes:
    - aqie-dataselector-frontend → aqie-historicaldata-backend: `POST /AtomEmailJobDataSelection`
      with the selection and the recipient's email address; the backend records a `Pending`
      job in `aqie_csvemailexport_jobs` and answers `Success`. Nothing is built yet
    - A hosted sweep runs at start-up and then every `TIME_INTERVAL` minutes (default 45). It
      claims each pending job, rebuilds the whole extract from the stored criteria (phases 2 to
      4 again), uploads it to S3 and marks the job `Completed` or `Failed`
    - aqie-historicaldata-backend → aqie-notify-service: `POST /send-notification` with the
      recipient, the Notify template id and the download link as personalisation.
      `aqie-historicaldata-backend` builds the link from the configured `EMAIL_BASEADDRESS`,
      the job id and the job's creation time in Unix milliseconds. The base address is deployed
      configuration, assumed to point at the `aqie-dataselector-frontend` page
      `/download_emailreq/{id}/{timestamp}`; the timestamp is not signed
    - aqie-notify-service → GOV.UK Notify → Citizen: email containing the download link
    - Citizen follows the link: aqie-dataselector-frontend rejects it after 48 hours (checked
      against the unsigned timestamp), posts the job reference to aqie-historicaldata-backend
      `POST /AtomDataSelectionPresignedUrlMail`, receives a fresh seven-day pre-signed URL,
      checks that it responds and sends the browser to it

## Points to flag on the diagram

- Banner at the top: "No historic measurements are stored in AQIE. Every extract is fetched
  live from DEFRA UK-AIR."
- Amber callout on the verified/unverified decision, as described in step 21.
- Note next to the UK-AIR node: "single point of dependency — if UK-AIR is unavailable or a
  site-year is missing, the extract silently returns nothing for that site".
- Note next to Ricardo and LAQM: "metadata only".
- Note on the job queue: "in-process channel is per-container; a queued job cannot be picked
  up by another container".
- Note on Path B: "the email sweep rebuilds the whole extract; it does not reuse a direct
  download".
- Note on the emailed link: "expiry policy is open (oq-034, partly answered). The 48-hour
  rule is checked only in aqie-dataselector-frontend, against an unsigned timestamp, while
  aqie-historicaldata-backend issues a fresh seven-day pre-signed URL for any known job
  reference and has no age check".
- Note next to `aqie-back-end`, drawn as a greyed-out box outside all phases: "not involved in
  extracts — it serves recent readings read live from Ricardo, while extracts come from the
  UK-AIR Atom service. The two read the same monitoring network by different publication
  routes, so they can legitimately disagree".
