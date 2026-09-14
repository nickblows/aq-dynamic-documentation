# aq-dynamic-documentation

Dynamic documentation library for Air Quality services.

## Purpose

This repository stores service documentation only (no source code, no sensitive data) and is designed for repeatable AI-assisted updates.

## Documentation Structure

- `/docs/introduction.md` — repository scope and principles
- `/docs/master/system-landscape.md` — how all services fit together and data flow summary
- `/docs/repository-catalog.yaml` — tracked repositories and interrogation metadata
- `/docs/repositories/aqie-repository-inventory.md` — current AQIE repository inventory snapshot
- `/docs/services/citizen/` — Citizen primary service and sub-services
- `/docs/services/data/` — Data primary service and sub-services
- `/docs/services/_templates/` — reusable service documentation templates
- `/docs/workflows/dynamic-update-workflow.md` — end-to-end update process
- `/docs/agent-instructions/dynamic-update-instructions.md` — repeatable Copilot agent interrogation instructions
- `/docs/diagrams/drawio-guidelines.md` — draw.io generation and update guidance
- `/docs/diagrams/src/` — draw.io source (`.drawio` XML)
- `/docs/diagrams/export/` — rendered diagram assets (`.svg` / `.png`)
- `/docs/audit/audit-log.md` — update history and audit trail
- `/.github/workflows/refresh-aqie-repository-metadata.yml` — scheduled/manual AQIE metadata refresh
- `/.github/workflows/regenerate-drawio-exports.yml` — automated draw.io SVG export refresh

## Required Secret for Metadata Refresh

Add repository secret:

- `DEFRA_READONLY_PAT` — read-only token with DEFRA SSO authorization

## Operating Model

The update process compares each tracked repository’s `main` branch against its last analysed commit/time, updates relevant service documentation, refreshes system-level docs and diagrams, and records outcomes in the audit log.
