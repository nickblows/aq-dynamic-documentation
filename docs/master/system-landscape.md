# Air Quality System Landscape

## Overview

This document explains how the Air Quality services fit together at a platform level.

## Service Domains

### Citizen Services

Citizen-facing capabilities and interaction channels.

### Data Services

Data ingestion, processing, analytics, and distribution capabilities.

## Cross-Service Data Flow (Master Summary)

1. Data is collected/ingested by Data services.
2. Data is processed, validated, and made available through Data domain components.
3. Citizen services consume relevant datasets/APIs to present user-facing features.
4. Operational and support integrations exchange metadata/events as required.

> Keep this summary aligned with detailed service docs and diagrams after every update cycle.

## Documentation Dependencies

- Service detail pages under `/docs/services/**`
- Repository metadata in `/docs/repository-catalog.yaml`
- Diagram guidance in `/docs/diagrams/drawio-guidelines.md`
