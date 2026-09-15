# Copilot Agent Instructions: Dynamic Documentation Update

## Objective

Run a repeatable, consistent update of Air Quality documentation using repository deltas from `main` only.

## Inputs

- `/docs/repository-catalog.yaml`
- `/docs/repositories/aqie-repository-inventory.md`
- Existing service docs in `/docs/services/**`
- Master doc `/docs/master/system-landscape.md`
- Diagram guidance `/docs/diagrams/drawio-guidelines.md`
- Audit file `/docs/audit/audit-log.md`
- Repository secret: `DEFRA_READONLY_PAT` (SSO-enabled read-only metadata access)

## Required Rules

1. Do not store service source code in this repository.
2. Do not store credentials, tokens, or sensitive data.
3. Analyse merged changes from `main` branch only.
4. For each repository, update `last_analysed_at_utc` and `last_analysed_main_commit` after successful documentation update.
5. Keep metadata fields populated: `type`, `connected_services`, `last_modified_at_utc`, and `activity_status`.

## Repeatable Procedure

1. Load `/docs/repository-catalog.yaml`.
2. For each repository entry:
   - Fetch current `origin/main` HEAD commit.
   - Compare with `last_analysed_main_commit`.
   - If no delta, mark as unchanged for this run.
   - If delta exists, interrogate merged changes in that commit range.
   - Refresh metadata:
     - `last_modified_at_utc`: latest available `main` branch modification timestamp
     - `activity_status` using catalog rule:
       - `Active` if updated in <=90 days
       - `Monitoring` if updated in 91-180 days
       - `Inactive` if updated in >180 days
     - `type` from taxonomy in catalog
     - `connected_services` from confirmed dependencies/integrations
3. Update the relevant service docs (overview and/or sub-service profiles) with:
   - Functional change summary
   - Technology/architecture/hosting impact
   - Integration/data flow impact
4. Update `/docs/master/system-landscape.md` for cross-service effects.
5. Update draw.io diagram sources/exports according to latest architecture/data flow understanding.
   - Update source XML in `/docs/diagrams/src/*.drawio`
   - Regenerate rendered exports in `/docs/diagrams/export/*.svg` (and/or `.png`)
6. Update `/docs/repository-catalog.yaml` timestamps/commits for repositories processed.
7. Append a new run entry in `/docs/audit/audit-log.md`.

## Output Expectations

- Consistent formatting and section ordering
- Clear commit-range traceability per changed repository
- No references to unmerged/feature branch work
