# aq-dynamic-documentation

Dynamic documentation library for Air Quality services.

## Table of Contents

- [Quick Links](#quick-links)
- [Service Summary](#service-summary)
- [Repository Purpose](#repository-purpose)
- [What Is Dynamic Documentation?](#what-is-dynamic-documentation)
- [System Landscape Diagram](#system-landscape-diagram)
- [Start Here (New Users)](#start-here-new-users)
- [Documentation Map](#documentation-map)
- [How Updates Work](#how-updates-work)
- [Automation in This Repository](#automation-in-this-repository)
- [Security and Data Rules](#security-and-data-rules)
- [Conventions and Metadata](#conventions-and-metadata)

> **Note:** documentation in this repository is derived from analysis of public `main`
> branches. It has not yet been reviewed by service owners. Open questions are tracked in
> [`/docs/integration-catalog.yaml`](docs/integration-catalog.yaml) and findings requiring
> urgent attention are in [`/docs/audit/security-findings.md`](docs/audit/security-findings.md).

## Quick Links

- [Introduction](docs/introduction.md)
- [System Landscape](docs/master/system-landscape.md) — start here for the big picture
- [Integration Catalogue](docs/integration-catalog.yaml) — every service connection and what data crosses it
- [Generated Diagrams](docs/diagrams/generated/README.md) — context, dependency and journey diagrams
- [AQIE Repository Inventory](docs/repositories/aqie-repository-inventory.md)
- [Repository Catalog](docs/repository-catalog.yaml)
- [Security Findings](docs/audit/security-findings.md)
- [Dynamic Update Workflow](docs/workflows/dynamic-update-workflow.md)

## Service Summary

This repository documents the AQIE Air Quality service estate: 39 repositories across the
Citizen, Data and Shared domains, with a service profile for every one covering purpose,
architecture, API surface, integrations, data stores, configuration and hosting.

| Measure | Value |
|---|---|
| Repositories tracked | 39 |
| Service profiles | 39 |
| Evidence-backed integrations | 53 |
| Internal service-to-service edges | 26 |
| External and platform systems | 16 |

## Repository Purpose

This repository stores service documentation only (no source code, no sensitive data) and is designed for repeatable AI-assisted updates.

## What Is Dynamic Documentation?

“Dynamic documentation” means this library is continuously refreshable from repository metadata and merged `main` branch changes, so documentation stays current without manual re-discovery each time.

## System Landscape Diagram

Generated from the integration catalogue and rendered natively by GitHub:

- [System context](docs/diagrams/generated/system-context.md) — all services, domains and external systems
- [Service dependencies](docs/diagrams/generated/service-dependencies.md) — internal edges with endpoint detail

Journey data flows:

- [Citizen: check air quality](docs/diagrams/generated/flow-citizen-check-air-quality.md)
- [Scheduled data ingestion](docs/diagrams/generated/flow-data-ingestion.md)
- [Historic data download](docs/diagrams/generated/flow-historic-data-download.md)
- [Air quality alerts](docs/diagrams/generated/flow-air-quality-alerts.md)
- [Smoke control applications](docs/diagrams/generated/flow-smoke-control.md)

A curated draw.io poster is also maintained for presentation use:

- Source XML: [`/docs/diagrams/src/aqie-service-landscape.drawio`](docs/diagrams/src/aqie-service-landscape.drawio)
- Rendered asset: [`/docs/diagrams/export/aqie-service-landscape.svg`](docs/diagrams/export/aqie-service-landscape.svg)

## Start Here (New Users)

1. Read [`/docs/master/system-landscape.md`](docs/master/system-landscape.md) for the estate overview
2. Look at [`/docs/diagrams/generated/system-context.md`](docs/diagrams/generated/system-context.md)
3. Pick a product line and read its journey diagram under [`/docs/diagrams/generated/`](docs/diagrams/generated/README.md)
4. Open the relevant domain overview: [Citizen](docs/services/citizen/overview.md), [Data](docs/services/data/overview.md) or [Shared](docs/services/shared/overview.md)
5. Read the `service-profile.md` for the specific service you care about
6. Check [`/docs/integration-catalog.yaml`](docs/integration-catalog.yaml) for exact endpoints and evidence
7. Review [`/docs/workflows/dynamic-update-workflow.md`](docs/workflows/dynamic-update-workflow.md) before making updates

## Documentation Map

| Path | Purpose |
|---|---|
| [`/docs/introduction.md`](docs/introduction.md) | Repository scope and principles |
| [`/docs/master/system-landscape.md`](docs/master/system-landscape.md) | How the estate fits together, product lines, ingestion routes, structural issues |
| [`/docs/integration-catalog.yaml`](docs/integration-catalog.yaml) | **Source of truth** for every integration edge, with evidence |
| [`/docs/repository-catalog.yaml`](docs/repository-catalog.yaml) | Generated repository metadata |
| [`/docs/repositories/aqie-repository-inventory.md`](docs/repositories/aqie-repository-inventory.md) | Generated inventory table |
| [`/docs/services/citizen/overview.md`](docs/services/citizen/overview.md) | Citizen domain index |
| [`/docs/services/data/overview.md`](docs/services/data/overview.md) | Data domain index |
| [`/docs/services/shared/overview.md`](docs/services/shared/overview.md) | Test, performance and archived repositories |
| `/docs/services/<domain>/<service>/service-profile.md` | Full profile per service (39 of these) |
| [`/docs/services/_templates/service-profile-template.md`](docs/services/_templates/service-profile-template.md) | Profile template |
| [`/docs/diagrams/generated/`](docs/diagrams/generated/README.md) | Generated Mermaid diagrams — do not hand-edit |
| [`/docs/diagrams/drawio-guidelines.md`](docs/diagrams/drawio-guidelines.md) | draw.io poster governance |
| [`/docs/audit/security-findings.md`](docs/audit/security-findings.md) | Security and information governance findings |
| [`/docs/audit/audit-log.md`](docs/audit/audit-log.md) | Change history |

## How Updates Work

At a high level:

1. Check tracked repositories for merged updates on `main`
2. Refresh per-repository metadata (including activity status)
3. Update impacted domain/sub-service documents
4. Update master landscape and data-flow narratives
5. Regenerate diagrams
6. Record the run in the audit log

Detailed process: [`/docs/workflows/dynamic-update-workflow.md`](docs/workflows/dynamic-update-workflow.md)

## Automation in This Repository

### Scripts

| Script | Purpose |
|---|---|
| [`/scripts/update_aqie_repository_metadata.py`](scripts/update_aqie_repository_metadata.py) | Discovers AQIE repositories via the GitHub search API and regenerates `/docs/repository-catalog.yaml` and `/docs/repositories/aqie-repository-inventory.md`. Connections are read from the integration catalogue, never guessed from repository names. |
| [`/scripts/generate_diagrams.py`](scripts/generate_diagrams.py) | Regenerates every Mermaid diagram under `/docs/diagrams/generated/` from `/docs/integration-catalog.yaml`. |

Both require `PyYAML`. The metadata script requires `GITHUB_TOKEN` or `DEFRA_READONLY_PAT`.

```bash
GITHUB_TOKEN=$(gh auth token) python3 scripts/update_aqie_repository_metadata.py
python3 scripts/generate_diagrams.py
```

### Workflows

- [`/.github/workflows/refresh-aqie-repository-metadata.yml`](.github/workflows/refresh-aqie-repository-metadata.yml)
- [`/.github/workflows/regenerate-drawio-exports.yml`](.github/workflows/regenerate-drawio-exports.yml)

### Required Secret for Metadata Refresh

Add repository secret:

- `DEFRA_READONLY_PAT` — read-only token with DEFRA SSO authorization

## Security and Data Rules

- Documentation repository only
- No service source code
- No credentials, tokens or secret values in committed files — environment variable **names** only
- Main branch analysis only (ignore feature branch/unmerged work)
- Every integration claim must cite evidence (repository, file, line). Claims without
  evidence are marked `provisional`; claims that were checked and disproved are recorded
  under `refuted_edges` so they are not reintroduced.

## Conventions and Metadata

**Service type taxonomy** (`type` in the repository catalog):

- Core Frontend Service
- Core Backend Service
- Auxilary Frontend
- Auxilary Backend Service
- Demo Service
- Prototype Service (including PoC)
- Quality/Test Service
- Data/Analytics Support Service

**Activity status** is derived from the default-branch head commit timestamp:
`Active` within 90 days, `Monitoring` within 180 days, `Inactive` beyond that, and
`Archived` where the repository is archived on GitHub.

**Integration confidence** (`confidence` in the integration catalogue):

| Level | Meaning |
|---|---|
| `confirmed` | Caller and endpoint identified in non-test source on the default branch |
| `provisional` | Indicated by a configuration key or naming, target not fully verified |
| `inferred` | Assumed from topology; requires owner confirmation |

Test fixtures and mock URLs are not accepted as evidence. Domain and type classification
for known services is held in an explicit override map in the metadata script rather than
inferred from repository names.
