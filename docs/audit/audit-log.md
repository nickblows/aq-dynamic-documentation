# Dynamic Documentation Audit Log

Record each update cycle in reverse chronological order.

### Run: `2026-11-19T00:00:00Z`

- Trigger: Operator request — establish which repositories have had updates merged into `main`
  since the documentation was last updated, and update the documentation to match.
- Agent/Operator: GitHub Copilot (coordinator) with nine parallel read-only analyst agents,
  one per repository group / nickblows
- Repositories checked: **41** (39 profiled, 2 new). Each profile's `Last analysed commit` was
  compared with the current default-branch head through the GitHub API. The comparison is now
  built into `scripts/update_aqie_repository_metadata.py`, which prints the delta list.
- Repositories changed (main deltas found): **12**, analysed at pinned head commits:
  `aqie-dc-admin-frontend` (492 commits since the recorded analysis), `aqie-dc-backend` (413),
  `aqie-dataselector-frontend` (167), `aqie-maps-frontend` (45), `aqie-historicaldata-backend`
  (42), `aqie-monitoringstation-backend` (24), `aqie-back-end` (23),
  `aqie-demo-data-visualisations` (13), `aqie-front-end` (5), `aqie-prtr-frontend` (3),
  `aqie-location-backend` (3) and `aqie-prtr-backend` (its recorded commit is not an ancestor of
  `main`, so no count).
  - **New repositories:** `aqie-prtr-submissions-frontend` and `aqie-prtr-submissions-backend`
    (template scaffolds, no function yet), profiled for the first time.
  - **Newly archived on GitHub:** `aqie-dc-poc-backend`, `aqie-dc-poc-frontend`.
  - **Now private on GitHub:** `aqie-performance-test`.
  - **No new commits:** the other 27 profiled repositories. Their profiles were re-checked only
    for activity status, archived flag and statements made stale by the changed repositories.
- Documentation files updated:
  - 14 service profiles: the 12 changed repositories (affected sections rewritten) and the 2 new
    ones (created). The profiles of unchanged repositories had their activity status recomputed
    at 2026-11-19, and those carrying statements made stale by the changes were corrected,
    including "not in the catalogue" notes about edges and repositories that the catalogues
    now record. All 41 pass the profile template check.
  - `/docs/integration-catalog.yaml`: 65 integrations (was 57), 18 external systems (was 17),
    6 decommissioned and 13 refuted edges (were 4 and 5), 39 open questions (were 19), datastore
    entries for 17 services (were 11). Evidence now carries line numbers on 14 edges that had
    none.
  - `/docs/audit/security-findings.md`: 18 earlier findings marked fixed or changed in place, 43
    new findings (39 to 81), retention list and next steps updated.
  - `/docs/master/system-landscape.md`, `/docs/master/measurements-data-flow.md`,
    `/docs/master/monitoring-station-info-data-flow.md`, the three domain overviews, `/README.md`.
  - `/docs/repository-catalog.yaml`, `/docs/repositories/aqie-repository-inventory.md`
    (regenerated), `/docs/diagrams/generated/` (regenerated; the smoke control, data ingestion and
    historic download journeys were rewritten in `/scripts/generate_diagrams.py`).
  - `/scripts/update_aqie_repository_metadata.py` (delta report, last-analysed columns read from
    the profiles, entries for the two new repositories).
  - `/docs/workflows/dynamic-update-workflow.md`, `/docs/agent-instructions/dynamic-update-instructions.md`
    (delta check, pinned commits, read-never-run, private-source policy, multi-analyst process).
  - `/draw-io-generation/` working folder (untracked): refreshed from the catalogue.
- Master documentation updated: `yes`
- Diagrams updated: `yes`
- Agent instruction updates: `yes`

#### Corrections to previously recorded content

Found while re-reading the code. Several were wrong in the 2026-09-15 baseline and are not
caused by the new commits.

- **Ricardo host (`oq-012`) reversed.** The earlier documents said production did not override
  the Ricardo staging defaults in `aqie-back-end`. Per CDP environment configuration all four URL
  variables are set in the service-wide defaults and none points at the supplier's staging host.
  The staging host survives as a code default only. Severity lowered from high to low.
- **`aqie-front-end`.** Two edges had no call sites (UK-AIR forecast summary, postcodes.io) and are
  now refuted. The front end computes its own DAQI bands rather than receiving them from
  `aqie-back-end`. Eight `/notify/*` pages the profile listed are not served. The sign-in gate is
  dead configuration. The unsubscribe link carries no token. Two HTTP verbs were wrong. The
  `USE_NEW_RICARDO_MEASUREMENTS_ENABLED` flag is vestigial rather than a broken rollback path
  (`oq-016`, now low).
- **`aqie-back-end`.** The provisional GOV.UK Notify edge was refuted (`oq-001` answered).
  `POLLUTANTS_SCHEDULE` is the public UK-AIR sweep, not a Ricardo job, and Met Office files are
  not stored in its database. The documents analysed in September were written from the
  pre-merge branch of PR #163, so some statements about it pre-dated the merge.
- **System landscape.** `aqie-location-backend` serves two product lines, not three. The
  Observability paragraph overstated tracing and metrics. The at-a-glance counts are now
  computed from the generated repository catalogue (archived flag and type), because the earlier
  "superseded" category had no stated rule.
- **Journeys.** The historic data download journey was wrong (it has a direct download as well as
  an email fallback). The ingestion journey attributed the UK-AIR sweep to Ricardo. The smoke
  control queue poll defaults to 15 minutes, not 5.
- **`aqie-demo-data-visualisations`.** The 2026-09-23 note that it "has no migration path" is
  superseded: its PR #15 (2026-10-07) removed both the `aqie-back-end` and the SOS dependency and
  it now calls Ricardo directly with its own credentials (`oq-018` answered).
- **Security findings.** 14, 17, 33, 35 (fixed), 4, 30 and part of 34 (fixed in source; old values
  remain in git history), 25 (now dead configuration).
- **Evidence.** The catalogue's evidence was completed with line numbers for 14 edges. Seven
  older edges in unchanged repositories still cite a file without lines.

#### Notes/Risks

- **Private sources were consulted.** To resolve existing open questions, six analysts read
  `DEFRA/cdp-app-config`, four read `DEFRA/cdp-app-deployments` and two opened
  `DEFRA/cdp-tenant-config` (nothing from the last is retained). Retained statements are limited
  to variable names and set, unset or true/false states and carry the phrase
  `per CDP environment configuration`. Deployment topology, sizing, release numbers and values
  were removed. The previous cycle had already used similar sources, including one quoted
  configuration block, which has been removed.
- **The security findings document is now much larger in a public repository** (81 findings,
  several about running services). Finding 71 is a possible live gateway key in a committed
  Postman collection. Owner confirmation and a decision on where such findings should live are
  outstanding.
- **Dependencies were installed by two analysts in the first attempt** (the run was killed by a
  machine reboot). The installed packages were scanned for known worm indicators (none), all
  `node_modules` folders were deleted, and a "read, never run" rule was added to the analyst
  brief and to the workflow.
- **Discovery limit.** The metadata script finds repositories with `aqie in:name`.
  `prtr-contacts-backend` and `aiqe-dataservice-test` fall outside it (`oq-033`).
- **`aqie-notify-service` will become `Inactive` in late November 2026** without a commit,
  although it is the only route by which any AQIE service contacts a citizen.
- Nothing from this cycle has been committed.

---

### Run: `2026-09-15T12:00:00Z`

- Trigger: Deep analysis and enrichment of the full AQIE estate
- Agent/Operator: Copilot Task Agent
- Repositories checked: **39** (all AQIE repositories, shallow clone of `main`)
- Repositories changed (main deltas found): n/a — full baseline analysis
- Documentation files updated:
  - `/docs/integration-catalog.yaml` (new)
  - `/docs/services/<domain>/<service>/service-profile.md` (39 new)
  - `/docs/services/shared/overview.md` (new)
  - `/docs/services/citizen/overview.md`, `/docs/services/data/overview.md` (rewritten)
  - `/docs/master/system-landscape.md` (rewritten)
  - `/docs/services/_templates/service-profile-template.md` (rewritten)
  - `/docs/audit/security-findings.md` (new)
  - `/docs/diagrams/generated/` (8 new generated files)
  - `/docs/agent-instructions/dynamic-update-instructions.md` (rewritten)
  - `/docs/workflows/dynamic-update-workflow.md` (rewritten)
  - `/docs/repository-catalog.yaml`, `/docs/repositories/aqie-repository-inventory.md` (regenerated)
  - `/scripts/generate_diagrams.py` (new)
  - `/scripts/update_aqie_repository_metadata.py` (corrected)
  - `/README.md`, `/docs/introduction.md`
  - Removed: `/docs/services/citizen/sub-services.md`, `/docs/services/data/sub-services.md`
    (superseded by domain overviews)
- Master documentation updated: `yes`
- Diagrams updated: `yes` — Mermaid diagrams now generated from the integration catalogue
- Agent instruction updates: `yes`

#### Corrections to previously recorded metadata

- **Repository count was wrong.** The catalog tracked 30 repositories; 39 exist. Discovery
  used the org listing endpoint, which missed archived and older repositories. Now uses the
  GitHub search API.
- **`connected_services` was fabricated.** Values were derived from a `family()` function
  that grouped repositories by name substring (`dc-`, `prtr`, `maps`), not from any code
  analysis. Replaced with evidence-backed edges read from the integration catalogue.
- **Domain classification was wrong for several services**, including `aqie-back-end`
  (listed `Shared`, is `Data`). Replaced name-based inference with an explicit override map.
- **`activity_status` did not distinguish archived repositories.** Added `Archived`.

#### Analysis outcome

- 53 integrations recorded with evidence, of which 26 are internal service-to-service edges.
- 16 external and platform systems identified.
- 5 previously assumed edges investigated and disproved, recorded under `refuted_edges`.
- 13 open questions raised for service owners.
- 38 security and information governance findings recorded separately.

#### Notes/Risks

- All documentation is derived from static analysis of public `main` branches and has **not
  been reviewed by service owners**. Treat open questions as genuinely open.
- Several findings are high severity, including credentials committed to public
  repositories and an admin interface where authentication is configured but not enforced.
  See `/docs/audit/security-findings.md`.
- The public smoke control register appears to have a broken frontend/backend contract
  (`oq-006`); this needs confirmation before it is treated as fact.

---

### Run: `2026-09-15T09:35:54Z`

- Trigger: Add README quick links for core documentation
- Agent/Operator: Copilot Task Agent
- Repositories checked: n/a (documentation enhancement run)
- Repositories changed (main deltas found): n/a
- Documentation files updated:
  - `/README.md`
  - `/docs/audit/audit-log.md`
- Master documentation updated: `no`
- Diagrams updated: `no`
- Agent instruction updates: `no`
- Notes/Risks:
  - Quick Links section added to speed first-time navigation.

---

### Run: `2026-09-15T08:43:52Z`

- Trigger: Improve README navigation with clickable document links
- Agent/Operator: Copilot Task Agent
- Repositories checked: n/a (documentation enhancement run)
- Repositories changed (main deltas found): n/a
- Documentation files updated:
  - `/README.md`
  - `/docs/audit/audit-log.md`
- Master documentation updated: `no`
- Diagrams updated: `no`
- Agent instruction updates: `no`
- Notes/Risks:
  - README document references are now clickable for quicker navigation.

---

### Run: `2026-09-14T15:59:03Z`

- Trigger: Expand README onboarding and overview content
- Agent/Operator: Copilot Task Agent
- Repositories checked: n/a (documentation enhancement run)
- Repositories changed (main deltas found): n/a
- Documentation files updated:
  - `/README.md`
  - `/docs/audit/audit-log.md`
- Master documentation updated: `no`
- Diagrams updated: `no` (existing rendered preview linked from README)
- Agent instruction updates: `no`
- Notes/Risks:
  - README now includes guided navigation and diagram preview for new users.

---

### Run: `2026-09-14T15:54:22Z`

- Trigger: Add automation for draw.io export regeneration
- Agent/Operator: Copilot Task Agent
- Repositories checked: n/a (workflow enhancement run)
- Repositories changed (main deltas found): n/a
- Documentation files updated:
  - `/.github/workflows/regenerate-drawio-exports.yml`
  - `/README.md`
  - `/docs/diagrams/drawio-guidelines.md`
  - `/docs/workflows/dynamic-update-workflow.md`
  - `/docs/audit/audit-log.md`
- Master documentation updated: `no`
- Diagrams updated: `no` (automation added; exports regenerate on workflow trigger)
- Agent instruction updates: `no`
- Notes/Risks:
  - Export automation depends on `rlespinasse/drawio-export-action@v2` availability.

---

### Run: `2026-09-14T15:47:15Z`

- Trigger: Implement automated AQIE metadata refresh using repository secret
- Agent/Operator: Copilot Task Agent
- Repositories checked: n/a (workflow/script scaffolding run)
- Repositories changed (main deltas found): n/a
- Documentation files updated:
  - `/.github/workflows/refresh-aqie-repository-metadata.yml`
  - `/scripts/update_aqie_repository_metadata.py`
  - `/README.md`
  - `/docs/workflows/dynamic-update-workflow.md`
  - `/docs/agent-instructions/dynamic-update-instructions.md`
  - `/docs/audit/audit-log.md`
- Master documentation updated: `no`
- Diagrams updated: `no`
- Agent instruction updates: `yes`
- Notes/Risks:
  - Workflow requires repository secret `DEFRA_READONLY_PAT`.
  - Connected services remain provisional until confirmed by service owners.

---

### Run: `2026-09-14T14:25:26Z`

- Trigger: AQIE repository inventory enrichment request
- Agent/Operator: Copilot Task Agent
- Repositories checked: 30 (AQIE-prefixed)
- Repositories changed (main deltas found): n/a (discovery + metadata enrichment run)
- Documentation files updated:
  - `/docs/repository-catalog.yaml`
  - `/docs/repositories/aqie-repository-inventory.md`
  - `/docs/agent-instructions/dynamic-update-instructions.md`
  - `/docs/workflows/dynamic-update-workflow.md`
  - `/docs/diagrams/drawio-guidelines.md`
  - `/docs/diagrams/src/aqie-service-landscape.drawio`
  - `/docs/diagrams/export/aqie-service-landscape.svg`
  - `/README.md`
- Master documentation updated: `no`
- Diagrams updated: `yes`
- Agent instruction updates: `yes`
- Notes/Risks:
  - Discovery source was public org repository search HTML.
  - `created_at_utc` remains null pending SSO-enabled API access.

---

## Run: `2026-09-23T00:00:00Z`

- Trigger: Operator request following merge-ready [aqie-back-end PR #163](https://github.com/DEFRA/aqie-back-end/pull/163),
  removing the redundant `/forecasts` and `/measurements` endpoints.
- Agent/Operator: GitHub Copilot / nickblows
- Repositories checked: `aqie-back-end` (branch `remove-redundant-endpoints`), `aqie-front-end`,
  `aqie-maps-frontend`, `aqie-maps-prototype`, `aqie-demo-data-visualisations`
- Repositories changed (main deltas found):
  - `aqie-back-end`: `/forecasts` and `/measurements` route plugins, controllers, read helpers
    and tests deleted; `src/api/router.js` registrations removed. **Scheduled ingestion
    retained** — `pollutantsScheduler` and `forecastScheduler` still registered in
    `src/api/server.js`.
  - Remaining registered routes: `health`, `metOfficeForecastRead`, `metOfficeForecastList`,
    `monitoringStationInfo`, `monitoringStations`, `aurnData`.
- Documentation files updated:
  - **New:** `/docs/master/monitoring-station-info-data-flow.md` — full trace of the current
    serving path, its consumers, and code-level findings.
  - `/docs/master/measurements-data-flow.md` — reframed as a decommission record; added
    "Residual breakage after removal".
  - `/docs/integration-catalog.yaml` — removed three live edges, added a `decommissioned_edges`
    section and `oq-016` to `oq-019`; revised `oq-014`.
  - `/docs/services/data/aqie-back-end/service-profile.md` — API surface and consumer tables.
  - Consumer profiles: `aqie-front-end`, `aqie-demo-data-visualisations`, `aqie-maps-frontend`,
    `aqie-data-service-backend`, `aqie-monitoringstation-backend`,
    `aqie-privatebeta-api-perftest`, `aqie-publicbeta-test`.
  - `/draw-io-generation/open-questions.md`, `prompts/flow-citizen-check-air-quality.md`,
    `prompts/service-dependencies.md`.
  - `/scripts/generate_diagrams.py` and `README.md`.
- Master documentation updated: `yes`
- Diagrams updated: `yes` — all seven regenerated from the catalogue; no residual references
  to the removed endpoints remain in `/docs/diagrams/generated/`.
- Agent instruction updates: `no`
- Notes/Risks (history; several statements below were superseded by the run of 2026-11-19):
  - **PR #163 was approved but still open at time of analysis.** Documentation was updated to
    reflect the post-merge state. Re-verify against `main` after merge. *It merged on
    2026-09-23 and was re-verified on 2026-11-19.*
  - **Ingest pipelines are now orphaned.** `measurements` and `forecasts` collections are
    written hourly with no reader (`oq-019`).
  - **`USE_NEW_RICARDO_MEASUREMENTS_ENABLED=false` is now a broken rollback path** in
    `aqie-front-end` (`oq-016`). *Superseded: the flag is vestigial and the old URL is
    unreachable at runtime.*
  - **`aqie-demo-data-visualisations` has no migration path** — it depended on the
    feature-of-interest mapping, which `/monitoringStationInfo` does not publish (`oq-018`).
    *Superseded: the demo stopped using `aqie-back-end` altogether (its PR #15).*
  - Production `aqie-back-end` configuration does not override the
    `uk-air-api.staging.rcdo.co.uk` Ricardo defaults. Now higher impact, since
    `/monitoringStationInfo` is the sole citizen data path. Unconfirmed — see `oq-012`.
    *Superseded: per CDP environment configuration it does override them.*
  - All repositories analysed were on feature branches, not `main`.

---

## Entry Template

### Run: `<YYYY-MM-DDTHH:MM:SSZ>`

- Trigger:
- Agent/Operator:
- Repositories checked:
- Repositories changed (main deltas found):
- Documentation files updated:
- Master documentation updated: `<yes/no>`
- Diagrams updated: `<yes/no>`
- Agent instruction updates: `<yes/no>`
- Notes/Risks:

---
