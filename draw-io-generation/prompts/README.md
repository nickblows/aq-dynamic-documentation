<!-- Generated from /draw-io-generation/generation-config.yaml on 2026-11-19.
     Regenerate by asking the agent to rebuild the draw.io prompt files. -->

# next-ai-draw-io prompts

One self-contained prompt per diagram. Paste **one file per conversation** into
[next-ai-draw-io](https://next-ai-drawio.jiang.jp/) — one focused diagram per conversation
gives markedly better results than a single large prompt. Save the returned XML in the
parent folder as `<diagram-id>.drawio.xml`.

Generated at detail level **medium** from the selection in
[generation-config.yaml](../generation-config.yaml).

## Structural diagrams

| Prompt | Shows |
|---|---|
| [system-context.md](system-context.md) | All 19 selected services grouped by product line, the 14 external systems they call, and all 46 connections |
| [data-flow.md](data-flow.md) | Five lanes from external sources through ingestion and storage out to citizens, with cadence on every ingestion edge (50 flows) |
| [service-dependencies.md](service-dependencies.md) | The 24 internal AQIE-to-AQIE calls with endpoint paths; externals excluded |

## Deep dives

| Prompt | Shows |
|---|---|
| [atom-feed-measurement-collection.md](atom-feed-measurement-collection.md) | How historic measurements are fetched live from the DEFRA UK-AIR Atom feed, one file per site per year, including the verified/unverified split, the direct download path and the emailed-link path. Generated at high detail. |

## Journey diagrams

| Prompt | Shows |
|---|---|
| [flow-citizen-check-air-quality.md](flow-citizen-check-air-quality.md) | The primary public journey on check-air-quality.service.gov.uk, with current readings read live from Ricardo |
| [flow-data-ingestion.md](flow-data-ingestion.md) | Four independent scheduled pipelines: Ricardo stations and DAQI, the UK-AIR SOS sweep, the UK-AIR forecast feed and the Met Office forecast files |
| [flow-historic-data-download.md](flow-historic-data-download.md) | By-station and custom-dataset journeys: direct download for a single-year extract, an emailed link for multi-year requests or jobs over three minutes |
| [flow-air-quality-alerts.md](flow-air-quality-alerts.md) | Subscription, verification, scheduled dispatch and opt-out |
| [flow-smoke-control.md](flow-smoke-control.md) | SQS intake from DEFRA Forms (polled every 15 minutes by default), caseworker review behind Microsoft Entra sign-in, and public register search (oq-006) |

## Certainty

Every prompt asks for the same styling so diagrams are comparable:

| Line style | Meaning |
|---|---|
| Solid black | Confirmed — endpoint and caller identified in non-test source on the default branch |
| Dashed grey | Provisional — indicated by configuration or naming, target not fully verified |
| Dotted grey | Inferred — assumed from architecture, requires owner confirmation |
| Amber | Reported by a service team but not yet evidenced in code or recorded in the catalogue |

At 2026-11-19 every integration in the catalogue is confirmed, so no prompt asks for a dashed
or dotted grey edge. The styles stay in each legend for edges added later. Refuted and
decommissioned edges are not drawn; they are listed in [open-questions.md](../open-questions.md).

Red notes mark connections that exist in code but appear broken. The full list of
uncertainties behind these markings is in [open-questions.md](../open-questions.md).
