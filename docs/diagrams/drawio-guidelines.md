# draw.io Diagram Guidance

## Purpose

Keep architecture and data-flow diagrams synchronised with documentation updates.

## Inputs for Diagram Updates

- Updated service docs under `/docs/services/**`
- Updated master landscape doc
- Repository delta summaries from latest interrogation cycle

## Diagram Update Rules

1. Preserve existing layout where possible; make careful incremental edits.
2. Reflect only confirmed merged changes from `main`.
3. Keep naming aligned with service documentation.
4. Update connectors/arrows to match latest data flow.
5. Remove deprecated components only when confirmed by repository changes.

## Recommended Files

- Source diagrams: `/docs/diagrams/src/*.drawio`
- Exported outputs: `/docs/diagrams/export/*.svg` (or `.png`)

## Regeneration Requirement

On every documentation update cycle:

1. Update `.drawio` source files first.
2. Regenerate rendered exports (`.svg` minimum) from updated source.
3. Commit both source and rendered files together.

## Automation

- Workflow: `/.github/workflows/regenerate-drawio-exports.yml`
- Trigger: push changes to `/docs/diagrams/src/*.drawio` or manual dispatch
- Output target: `/docs/diagrams/export/*.svg`

## Quality Checklist

- Every changed service represented correctly
- Data direction and integration labels reviewed
- No orphan nodes or stale dependencies
