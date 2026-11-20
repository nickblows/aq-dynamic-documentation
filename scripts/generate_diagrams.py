#!/usr/bin/env python3
"""Generate Mermaid architecture diagrams from docs/integration-catalog.yaml.

The catalogue is the single source of truth for edges. Everything written into
docs/diagrams/generated/ is derived and must not be hand-edited.
"""

from __future__ import annotations

import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "docs/integration-catalog.yaml"
REPO_CATALOG = ROOT / "docs/repository-catalog.yaml"
OUT_DIR = ROOT / "docs/diagrams/generated"

BANNER = (
    "<!-- GENERATED FILE — DO NOT EDIT.\n"
    "     Source: /docs/integration-catalog.yaml\n"
    "     Regenerate: python3 scripts/generate_diagrams.py -->\n"
)

# Interaction style per edge kind.
LINK_STYLE = {
    "synchronous": "-->",
    "asynchronous": "-.->",
    "scheduled-batch": "==>",
    "user-redirect": "-.->",
    "outbound-link": "-.->",
}


def node_id(name: str) -> str:
    return re.sub(r"[^0-9A-Za-z_]", "_", name)


def label(name: str) -> str:
    return name.replace("aqie-", "")


def load() -> tuple[dict, dict]:
    catalog = yaml.safe_load(CATALOG.read_text())
    repos = yaml.safe_load(REPO_CATALOG.read_text()) if REPO_CATALOG.exists() else {"repositories": []}
    return catalog, repos


def domain_of(repos: dict) -> dict[str, str]:
    return {r["service_name"]: r.get("service_domain", "Shared") for r in repos.get("repositories", [])}


def edge_line(i: dict) -> str:
    arrow = LINK_STYLE.get(i.get("interaction", "synchronous"), "-->")
    eps = i.get("endpoints") or []
    if eps:
        text = "<br/>".join(f"{e['method']} {e['path']}" for e in eps[:4])
        if len(eps) > 4:
            text += f"<br/>+{len(eps) - 4} more"
    else:
        text = i.get("protocol", "")
    return f'    {node_id(i["source"])} {arrow}|"{text}"| {node_id(i["target"])}'


def write(path: Path, title: str, body: str, intro: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    content = f"{BANNER}\n# {title}\n\n_Generated {stamp} from `/docs/integration-catalog.yaml`._\n\n"
    if intro:
        content += intro + "\n\n"
    content += body + "\n"
    path.write_text(content)
    print(f"wrote {path.relative_to(ROOT)}")


# --- diagram builders -------------------------------------------------------

def system_context(catalog: dict, domains: dict[str, str]) -> None:
    ext = {e["id"]: e for e in catalog["external_systems"]}
    integrations = catalog["integrations"]

    services = sorted({i["source"] for i in integrations} | {
        i["target"] for i in integrations if i.get("target_kind") == "aqie-service"
    })
    citizen = [s for s in services if domains.get(s) == "Citizen"]
    data = [s for s in services if domains.get(s) == "Data"]
    shared = [s for s in services if domains.get(s) not in ("Citizen", "Data")]

    lines = ["```mermaid", "graph LR"]
    for name, members in (("Citizen domain", citizen), ("Data domain", data), ("Shared", shared)):
        if not members:
            continue
        lines.append(f'  subgraph {node_id(name)}["{name}"]')
        for s in members:
            lines.append(f'    {node_id(s)}["{label(s)}"]')
        lines.append("  end")

    used_ext = sorted({i["target"] for i in integrations if i.get("target_kind") in ("external", "platform")})
    if used_ext:
        lines.append('  subgraph externals["External and platform systems"]')
        for e in used_ext:
            lines.append(f'    {node_id(e)}[["{ext.get(e, {}).get("name", e)}"]]')
        lines.append("  end")

    for i in integrations:
        lines.append(edge_line(i))

    lines.append("  classDef citizen fill:#d4e6f7,stroke:#1d70b8,color:#0b0c0c;")
    lines.append("  classDef data fill:#d8eeda,stroke:#00703c,color:#0b0c0c;")
    lines.append("  classDef shared fill:#fff3d4,stroke:#946b00,color:#0b0c0c;")
    lines.append("  classDef ext fill:#eeeeee,stroke:#505a5f,color:#0b0c0c;")
    if citizen:
        lines.append("  class " + ",".join(node_id(s) for s in citizen) + " citizen;")
    if data:
        lines.append("  class " + ",".join(node_id(s) for s in data) + " data;")
    if shared:
        lines.append("  class " + ",".join(node_id(s) for s in shared) + " shared;")
    if used_ext:
        lines.append("  class " + ",".join(node_id(s) for s in used_ext) + " ext;")
    lines.append("```")

    write(
        OUT_DIR / "system-context.md",
        "AQIE System Context",
        "\n".join(lines),
        "Every AQIE service with a confirmed integration, grouped by domain, with the "
        "external and platform systems they depend on. Edge labels show the endpoints used.\n\n"
        "Arrow meaning: solid = synchronous request, thick = scheduled batch, dotted = "
        "asynchronous or user-redirect.",
    )


def service_dependencies(catalog: dict) -> None:
    internal = [i for i in catalog["integrations"] if i.get("target_kind") == "aqie-service"]
    lines = ["```mermaid", "graph TD"]
    nodes = sorted({i["source"] for i in internal} | {i["target"] for i in internal})
    for n in nodes:
        lines.append(f'  {node_id(n)}["{label(n)}"]')
    for i in internal:
        lines.append(edge_line(i))
    lines.append("```")

    rows = ["| Source | Target | Interaction | Endpoints | Data exchanged | Confidence |", "|---|---|---|---|---|---|"]
    for i in sorted(internal, key=lambda x: (x["source"], x["target"])):
        eps = i.get("endpoints") or []
        ep_txt = "<br/>".join(f"`{e['method']} {e['path']}`" for e in eps) or "—"
        data_txt = "<br/>".join(e.get("data", "") for e in eps) or i.get("data_exchanged", "—")
        rows.append(
            f'| `{i["source"]}` | `{i["target"]}` | {i.get("interaction", "—")} | {ep_txt} | {data_txt} | `{i.get("confidence", "—")}` |'
        )

    write(
        OUT_DIR / "service-dependencies.md",
        "AQIE Service-to-Service Dependencies",
        "\n".join(lines) + "\n\n## Edge detail\n\n" + "\n".join(rows),
        "Internal AQIE edges only. External systems are excluded to keep the "
        "ownership boundary clear — see the system context diagram for those.",
    )


def data_flows(catalog: dict) -> None:
    """Sequence diagrams for the principal end-to-end journeys."""
    journeys = {
        "citizen-check-air-quality": {
            "title": "Citizen: check air quality for a location",
            "desc": "The primary public journey on check-air-quality.service.gov.uk.",
            "steps": [
                ("Citizen", "aqie-front-end", "Search a place name or postcode"),
                ("aqie-front-end", "os-names", "GET /search/names/v1/find — resolve place to coordinates"),
                ("os-names", "aqie-front-end", "Matched places with coordinates"),
                ("aqie-front-end", "aqie-back-end", "GET /monitoringStationInfo — stations near coordinates"),
                ("aqie-back-end", "ricardo-ukair", "POST /api/login_check, GET /api/site_meta_datas"),
                ("aqie-back-end", "ricardo-ukair", "GET /api/pollutant_measurement_datas — 5 calls per station"),
                ("aqie-back-end", "aqie-front-end", "Station metadata and current pollutant concentrations"),
                ("aqie-front-end", "aqie-forecast-api", "GET /forecast — multi-day outlook and forecast summary"),
                ("aqie-forecast-api", "aqie-front-end", "Forecast DAQI by day and region, and the forecast summary text"),
                ("aqie-front-end", "aqie-front-end", "Calculate pollutant bands and map forecast days to bands and advice"),
                ("aqie-front-end", "Citizen", "Rendered location page with DAQI, pollutants and forecast"),
            ],
        },
        "data-ingestion": {
            "title": "Scheduled air quality data ingestion",
            "desc": (
                "How measurement and forecast data enters the estate. Runs on cron schedules, "
                "not on user request. The UK-AIR sweep and the forecast feed in aqie-back-end "
                "are still written to MongoDB, but nothing has read them since the "
                "/measurements and /forecasts endpoints were removed."
            ),
            "steps": [
                ("Scheduler", "aqie-back-end", "Cron trigger (MONITORING_STATIONS_SCHEDULE and at start-up, AURN_SCHEDULE)"),
                ("aqie-back-end", "ricardo-ukair", "POST /api/login_check — obtain bearer token"),
                ("ricardo-ukair", "aqie-back-end", "Bearer token"),
                ("aqie-back-end", "ricardo-ukair", "GET /api/site_meta_datas, /api/pollutant_metadatas — stations and instrument dates"),
                ("aqie-back-end", "postcodes-io", "GET /postcodes — resolve station local authority"),
                ("aqie-back-end", "MongoDB", "Replace the monitoringStations cache"),
                ("aqie-back-end", "ricardo-ukair", "GET /api/pollutant_measurement_datas — yesterday and today, five stations at a time"),
                ("aqie-back-end", "MongoDB", "Upsert per-station DAQI (aurnMeasurements)"),
                ("Scheduler", "aqie-back-end", "Cron trigger (POLLUTANTS_SCHEDULE hourly, FORECAST_SCHEDULE)"),
                ("aqie-back-end", "defra-sos", "GET site listing, then SOS GetObservation for each site"),
                ("aqie-back-end", "ukair-website", "GET /assets/rss/forecast.xml"),
                ("aqie-back-end", "MongoDB", "Write measurements and forecasts — no reader since PR 163"),
                ("Scheduler", "aqie-forecast-api", "Cron trigger (FORECAST_SCHEDULE)"),
                ("aqie-forecast-api", "met-office-sftp", "SFTP poll configured directory"),
                ("met-office-sftp", "aqie-forecast-api", "Forecast files"),
                ("aqie-forecast-api", "MongoDB", "Persist parsed forecast documents"),
            ],
        },
        "historic-data-download": {
            "title": "Citizen: download historic air quality data",
            "desc": (
                "Two journeys share one service: by station (search, recent-readings tabs and "
                "per-pollutant downloads) and custom dataset (filters, then an extract job). "
                "A single-year extract downloads directly once the job completes; multi-year "
                "requests, and any job still running after three minutes, are emailed."
            ),
            "steps": [
                ("Citizen", "aqie-dataselector-frontend", "By station: search a place name or postcode"),
                ("aqie-dataselector-frontend", "aqie-location-backend", "POST /osnameplaces — resolve location"),
                ("aqie-dataselector-frontend", "aqie-monitoringstation-backend", "POST /monitoringstation — find nearby stations"),
                ("aqie-monitoringstation-backend", "aqie-back-end", "GET /monitoringStationInfo — station list"),
                ("aqie-dataselector-frontend", "aqie-back-end", "GET /monitoringStationHistory — last 24 hours and 7 days"),
                ("aqie-dataselector-frontend", "aqie-historicaldata-backend", "POST /AtomHistoryHourlydata — single-station download link"),
                ("Citizen", "aqie-dataselector-frontend", "Custom dataset: choose pollutants, data sources and locations"),
                ("aqie-dataselector-frontend", "laqm-portal", "GET /xapi/getLocalAuthorities/json — local authority list"),
                ("aqie-dataselector-frontend", "aqie-historicaldata-backend", "GET region and agglomeration masters, POST /AtomDataSelection for station counts"),
                ("aqie-dataselector-frontend", "aqie-historicaldata-backend", "POST /AtomDataSelection — create the extract job"),
                ("aqie-dataselector-frontend", "aqie-historicaldata-backend", "POST /AtomDataSelectionJobStatus — poll every 2 s for up to 3 min"),
                ("aqie-historicaldata-backend", "ukair-atom", "GET observation XML per site and year"),
                ("aqie-historicaldata-backend", "AWS S3", "Stage generated extract"),
                ("aqie-dataselector-frontend", "Citizen", "Pre-signed download link once the job completes"),
                ("Citizen", "aqie-dataselector-frontend", "Email path: enter an email address (multi-year or after 3 min)"),
                ("aqie-dataselector-frontend", "aqie-historicaldata-backend", "POST /AtomEmailJobDataSelection — register the email job"),
                ("aqie-historicaldata-backend", "aqie-notify-service", "POST /send-notification — background sweep re-runs the extract, then emails"),
                ("aqie-notify-service", "govuk-notify", "Send the email"),
                ("govuk-notify", "Citizen", "Email linking to the frontend page /download_emailreq/id/timestamp"),
                ("Citizen", "aqie-dataselector-frontend", "Follow the link (rejected after 48 hours)"),
                ("aqie-dataselector-frontend", "aqie-historicaldata-backend", "POST /AtomDataSelectionPresignedUrlMail — fresh pre-signed URL"),
                ("aqie-dataselector-frontend", "Citizen", "Download page with the pre-signed link"),
            ],
        },
        "air-quality-alerts": {
            "title": "Citizen: air quality alert subscription and delivery",
            "desc": (
                "Subscription capture, verification, alert dispatch and opt-out. "
                "aqie-alert-back-end-service owns subscriber state; aqie-notify-service "
                "owns the messaging edge and is the only holder of the GOV.UK Notify key. "
                "SMS opt-out routes through the notify service and email opt-out through "
                "the front end (oq-005)."
            ),
            "steps": [
                ("Citizen", "aqie-front-end", "Choose alert locations and contact method"),
                ("aqie-front-end", "aqie-notify-service", "POST /subscribe/generate-otp or /subscribe/generate-link"),
                ("aqie-notify-service", "govuk-notify", "Send one-time code or magic link"),
                ("govuk-notify", "Citizen", "Verification code or link"),
                ("Citizen", "aqie-front-end", "Enter the code or follow the link"),
                ("aqie-front-end", "aqie-notify-service", "POST /subscribe/validate-otp or GET /subscribe/validate-link/{token}"),
                ("aqie-notify-service", "aqie-front-end", "Verification result and pending subscription"),
                ("aqie-front-end", "aqie-alert-back-end-service", "GET /api/subscriptions/{contact} — SMS only, not served (oq-015)"),
                ("aqie-front-end", "aqie-alert-back-end-service", "POST /setup-alert"),
                ("aqie-alert-back-end-service", "MongoDB", "Persist subscriber record (USERS)"),
                ("aqie-alert-back-end-service", "aqie-notify-service", "POST /send-notification — confirmation message"),
                ("Scheduler", "aqie-alert-back-end-service", "Scheduled alert detection run"),
                ("aqie-alert-back-end-service", "ricardo-ukair", "GET /api/daqi_alerts, /api/aqsr_alerts"),
                ("aqie-alert-back-end-service", "aqie-forecast-api", "GET /forecast — forecast-based conditions"),
                ("aqie-alert-back-end-service", "aqie-notify-service", "POST /send-notification per matched subscriber"),
                ("aqie-notify-service", "govuk-notify", "Deliver alert with unsubscribe deep link"),
                ("govuk-notify", "Citizen", "Email or SMS alert"),
                ("Citizen", "govuk-notify", 'Reply "STOP" by SMS'),
                ("aqie-notify-service", "govuk-notify", "GET /process-sms-replies — collect inbound replies"),
                ("aqie-notify-service", "aqie-alert-back-end-service", "DELETE /opt-out-sms-alert"),
                ("Citizen", "aqie-front-end", "Email opt-out: follow the unsubscribe link (plain address in the link, no token — oq-038)"),
                ("aqie-front-end", "aqie-alert-back-end-service", "DELETE /opt-out-email-alert — removes the whole subscriber record"),
            ],
        },
        "smoke-control": {
            "title": "Smoke control: appliance and fuel applications",
            "desc": (
                "Applications arrive asynchronously from DEFRA Forms over SQS, not through "
                "the AQIE frontend. The admin frontend is the caseworker review and "
                "certification interface and requires sign-in on every route. The public "
                "frontend calls routes the backend does not serve, so the public register "
                "may currently be broken (oq-006). The CDP Uploader import flow in the "
                "backend no longer completes, because its callback has been removed (oq-025)."
            ),
            "steps": [
                ("Applicant", "defra-forms", "Complete the appliance or fuel application form"),
                ("defra-forms", "aqie-dc-backend", "SQS message on aqie-dc-queue"),
                ("aqie-dc-backend", "aqie-dc-backend", "Long-poll (default every 15 min), store the message, map form fields, split repeaters"),
                ("aqie-dc-backend", "MongoDB", "Create application and appliance or fuel records, delete the message once handled"),
                ("Caseworker", "aqie-dc-admin-frontend", "Sign in"),
                ("aqie-dc-admin-frontend", "azure-entra", "OIDC authorisation code flow"),
                ("aqie-dc-admin-frontend", "aqie-dc-backend", "GET /applications/summary-by-status — read applications and items"),
                ("aqie-dc-admin-frontend", "aqie-dc-backend", "PATCH .../technical-review and .../checks — record review decisions"),
                ("aqie-dc-admin-frontend", "aqie-dc-backend", "PATCH /applications/{id}/complete — complete the application"),
                ("aqie-dc-admin-frontend", "aqie-dc-backend", "PATCH /appliances/{id}/certification/{country} and /visibility — publish decisions"),
                ("Citizen", "aqie-dc-frontend", "Search the published register"),
                ("aqie-dc-frontend", "aqie-dc-backend", "GET /get-all/{type}, GET /get/{type}/{id} — not served (oq-006)"),
            ],
        },
    }

    index_rows = ["| Journey | Description |", "|---|---|"]
    for slug, j in journeys.items():
        actors: list[str] = []
        for a, b, _ in j["steps"]:
            for x in (a, b):
                if x not in actors:
                    actors.append(x)
        lines = ["```mermaid", "sequenceDiagram", "  autonumber"]
        for a in actors:
            kind = "actor" if a in ("Citizen", "Applicant", "Caseworker") else "participant"
            lines.append(f'  {kind} {node_id(a)} as {a}')
        for src, dst, msg in j["steps"]:
            lines.append(f'  {node_id(src)}->>{node_id(dst)}: {msg}')
        lines.append("```")
        write(OUT_DIR / f"flow-{slug}.md", j["title"], "\n".join(lines), j["desc"])
        index_rows.append(f'| [{j["title"]}](flow-{slug}.md) | {j["desc"]} |')

    write(OUT_DIR / "README.md", "Generated Diagrams", "\n".join(index_rows),
          "All files in this folder are generated. Edit `/docs/integration-catalog.yaml` "
          "and re-run `python3 scripts/generate_diagrams.py`.\n\n"
          "## Structural diagrams\n\n"
          "- [System context](system-context.md) — all services, domains and external systems\n"
          "- [Service dependencies](service-dependencies.md) — internal edges with endpoint detail\n\n"
          "## Journey data flows\n")


def main() -> int:
    if not CATALOG.exists():
        print(f"missing {CATALOG}", file=sys.stderr)
        return 1
    catalog, repos = load()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    domains = domain_of(repos)
    system_context(catalog, domains)
    service_dependencies(catalog)
    data_flows(catalog)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
