# Copilot Agent Instructions: Dynamic Documentation Update

## Objective

Run a repeatable, evidence-based update of AQIE documentation using repository deltas from
`main` only.

## Inputs

- `/docs/integration-catalog.yaml` — **source of truth for all integration edges**
- `/docs/repository-catalog.yaml` — generated repository metadata
- `/docs/repositories/aqie-repository-inventory.md` — generated inventory
- `/docs/services/<domain>/<service>/service-profile.md` — one per repository
- `/docs/master/system-landscape.md` — estate overview
- `/docs/diagrams/generated/` — generated, never hand-edited
- `/docs/audit/audit-log.md` and `/docs/audit/security-findings.md`
- Repository secret `DEFRA_READONLY_PAT`, or a local `gh auth token`

## Non-negotiable rules

1. **No service source code** in this repository. Describe behaviour; never paste
   implementations. Endpoint paths and identifier names are fine.
2. **No secret values.** Environment variable **names** only. If a credential is discovered
   in a service repository, record the location in `/docs/audit/security-findings.md` and
   never reproduce the value.
3. **Analyse `main` only.** Ignore feature branches and unmerged pull requests.
4. **Every integration needs evidence** — repository, file and line, from non-test source.
   Test fixtures and mock URLs are not evidence.
5. **Never guess connections from repository names.** This produced materially wrong output
   in earlier versions of this repository.
6. **Never hand-edit `/docs/diagrams/generated/`.** Change the catalogue and regenerate.
7. **Read, never run.** Do not install dependencies, build, boot or test any repository you
   are analysing, and do not execute anything from it. Establish routes, configuration and
   call sites by reading the source.
8. **Public sources first.** Private deployment-configuration repositories may be read,
   read-only, only to settle an existing open question that depends on deployed values.
   Record variable names and yes/no or set/unset facts only; never values, non-public
   hostnames, account identifiers or deployment topology (releases, instance counts, sizing).
   Tag each such statement with the exact phrase `per CDP environment configuration`. If in
   doubt, leave it out and raise an open question.
9. **Pin the analysis point.** Record each repository's HEAD SHA at the start of the cycle and
   analyse exactly that commit. Commits that land later belong to the next cycle.

## Evidence standard

| Confidence | When to use |
|---|---|
| `confirmed` | Caller and endpoint found in non-test source on `main` |
| `provisional` | Config key or naming suggests it, target not verified |
| `inferred` | Assumed from topology; must carry an open question |

If a claimed edge is investigated and disproved, move it to `refuted_edges` with the reason
and the date checked. Do not silently delete it — recording the negative result stops it
being reintroduced.

Watch for **dead configuration**: AQIE repositories are forked from shared templates and
from each other, so config keys frequently survive without any call site. Always confirm a
key is actually read before treating it as an integration.

## Repeatable procedure

### 1. Refresh metadata

```bash
GITHUB_TOKEN=$(gh auth token) python3 scripts/update_aqie_repository_metadata.py
```

This rewrites the repository catalog and inventory. New repositories appear automatically;
add them to `SERVICE_OVERRIDES` in the script if the inferred domain or type is wrong. The
script keeps each repository's analysed commit and time by reading them from the metadata
table of its service profile, and prints the repositories whose default-branch HEAD differs
from that commit.

### 2. Identify changed repositories

Use the lists printed in step 1: repositories with new commits on the default branch, and
repositories with no profile. No delta means no analysis for that repository this cycle, but
recompute `Activity status` in every profile against the cycle date, and check whether any
repository has been archived or has changed visibility. Related repositories with other names
are not discovered automatically (see `oq-033`).

### 3. Analyse each changed repository

Clone into a scratch directory outside the workspace (a partial clone is enough). Check out
the pinned SHA. For each repository, establish:

- HTTP routes or endpoints exposed
- Outbound calls and external systems, with file and line evidence
- Environment variable names
- Data stores, collections and retention
- Hosting, container and pipeline detail
- Source-tree component map

### 4. Update the integration catalogue first

Add, amend or refute edges in `/docs/integration-catalog.yaml` **before** touching prose.
Everything downstream derives from it.

Two conventions keep the file and the generated output intact:

- The catalogue uses CRLF line endings. Edit it with a tool that preserves them and makes
  targeted replacements, never with a script that rewrites the whole file.
- Do not put a pipe character in an endpoint `path`. The diagram generator copies paths into
  Markdown tables and Mermaid labels, where a pipe splits the cell. Use a placeholder such as
  `{type}` and name the allowed values in `data`.

### 5. Update the service profile

Rewrite the affected `service-profile.md` against
`/docs/services/_templates/service-profile-template.md`. Sections 5 and 6 must agree with
the catalogue. Refresh the metadata table, including `last_analysed_commit`.

### 6. Update domain overviews and the landscape

Reflect new services, changed dependencies and any new structural issues.

### 7. Regenerate diagrams

```bash
python3 scripts/generate_diagrams.py
```

Update the journey definitions inside the script if a user journey has changed shape. Then
read the regenerated tables and edge labels: a stray pipe in an endpoint path, or a `#` or a
semicolon in a Mermaid sequence message, breaks rendering.

### 8. Record the cycle

Append to `/docs/audit/audit-log.md`. Add any new security or information governance
findings to `/docs/audit/security-findings.md`.

## Output expectations

- Consistent section ordering from the template
- Commit-range traceability per changed repository
- No references to unmerged or feature-branch work
- Unknowns stated explicitly as open questions rather than guessed
- British English, GOV.UK-style plain English
