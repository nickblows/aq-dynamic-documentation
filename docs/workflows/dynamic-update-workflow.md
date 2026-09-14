# Dynamic Update Workflow

## End-to-End Process

1. Check each tracked repository for new commits merged into `main` since that repo’s `last_analysed_main_commit`.
2. For each changed repository, interrogate merged changes and update the relevant service documentation folder.
3. After all changed repositories are documented, review and update `/docs/master/system-landscape.md` so component fit and data flow remain accurate.
4. Update draw.io diagrams based on the refreshed service and master documentation.
5. Update agent instructions if process clarifications or improvements are required for the next run.
6. Append/update the audit log with what changed, when, and why.

## Main-Branch Delta Rule

- Only analyse the `main` branch.
- Ignore feature branches, draft work, and unmerged pull requests.
- Define each repo’s analysis window as:
  - Start: `last_analysed_main_commit` (or initial baseline if null)
  - End: current `origin/main` HEAD

## Completion Criteria

- All changed repositories in catalog are updated
- Master landscape is aligned with per-service changes
- Diagrams reviewed and updated as needed
- Audit log updated with cycle summary
