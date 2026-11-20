# draw.io Generation

Working folder for producing draw.io diagrams of the AQIE estate with
[next-ai-draw-io](https://github.com/DayuanJiang/next-ai-draw-io).

## Contents

| File | Purpose |
|---|---|
| [generation-config.yaml](generation-config.yaml) | Selection file — tick the services, external data sources and journeys to include |
| [prompts/](prompts/README.md) | One self-contained prompt per diagram, pasted into next-ai-draw-io |
| [open-questions.md](open-questions.md) | Open questions, refuted edges and decommissioned edges, for taking to the team |
| `*.drawio.xml` | XML returned by next-ai-draw-io, saved here for reuse and sharing |

## Last refreshed

2026-11-19, against the catalogues at that date: 41 repositories (15 Active, 9 Monitoring, 9
Inactive, 8 Archived), 65 integrations (29 internal, 32 external or platform, 4 datastore),
18 external systems, 6 decommissioned edges, 13 refuted edges and 39 open questions (oq-001
to oq-039). The config ticks 19 of the 41 repositories and 14 of the 18 external systems. No
integration is provisional or inferred, so no prompt asks for a dashed or dotted grey edge.

## Workflow

1. Open [generation-config.yaml](generation-config.yaml) and set `include: "[X]"` against everything you
   want in the diagram, including the external data sources in `external_systems`. Set
   `options.detail_level` to `low`, `medium` or `high`.
2. Ask the agent to regenerate the prompt files. It reads the config, then draws
   facts from [/docs/repository-catalog.yaml](../docs/repository-catalog.yaml),
   [/docs/integration-catalog.yaml](../docs/integration-catalog.yaml) and the service
   profiles under [/docs/services](../docs/services).
3. Paste **one** prompt file per next-ai-draw-io conversation and iterate in chat. One
   focused diagram per conversation gives markedly better results than one large prompt.
4. Save the returned XML here as `<diagram-id>.drawio.xml`, matching the prompt file name.

## Rules

- The config records selection only. Service and integration facts stay mastered in
  `/docs/*.yaml` — if something is wrong in the generated description, fix the catalogue.
- External systems are boundary nodes only: owner, data crossing the boundary and
  interface. Nothing internal to them is modelled.
- Uncertain integrations are still drawn, styled dashed/dotted grey per
  `confidence_styling` in the config, so unconfirmed edges are obvious in review. None is
  uncertain at 2026-11-19.
- The generated description carries authentication mechanisms and credential variable
  names only — never credential values, tokens or keys.
- Values from private deployment configuration (hostnames, URL suffixes, account names) are
  never quoted. Say only that a variable is set, unset or true or false, tagged "per CDP
  environment configuration".
