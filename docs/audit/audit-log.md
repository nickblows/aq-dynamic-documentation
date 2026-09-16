# Dynamic Documentation Audit Log

Record each update cycle in reverse chronological order.

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
