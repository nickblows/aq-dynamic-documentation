#!/usr/bin/env python3
"""Refresh AQIE repository catalog and inventory from DEFRA GitHub metadata."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "docs/repository-catalog.yaml"
INVENTORY_PATH = ROOT / "docs/repositories/aqie-repository-inventory.md"
INTEGRATION_CATALOG_PATH = ROOT / "docs/integration-catalog.yaml"

# Curated classification. Name-based heuristics produced wrong domains and
# invented connections, so anything known is stated explicitly here and the
# heuristics below are only a fallback for newly discovered repositories.
SERVICE_OVERRIDES: dict[str, tuple[str, str]] = {
    # repo name: (service_domain, type)
    "aqie-front-end": ("Citizen", "Core Frontend Service"),
    "aqie-back-end": ("Data", "Core Backend Service"),
    "aqie-forecast-api": ("Data", "Auxilary Backend Service"),
    "aqie-location-backend": ("Data", "Auxilary Backend Service"),
    "aqie-monitoringstation-backend": ("Data", "Auxilary Backend Service"),
    "aqie-historicaldata-backend": ("Data", "Auxilary Backend Service"),
    "aqie-alert-back-end-service": ("Data", "Auxilary Backend Service"),
    "aqie-notify-service": ("Data", "Auxilary Backend Service"),
    "aqie-dataselector-frontend": ("Citizen", "Auxilary Frontend"),
    "aqie-maps-frontend": ("Citizen", "Auxilary Frontend"),
    "aqie-maps-prototype": ("Citizen", "Prototype Service (including PoC)"),
    "aqie-dc-frontend": ("Citizen", "Auxilary Frontend"),
    "aqie-dc-admin-frontend": ("Citizen", "Auxilary Frontend"),
    "aqie-dc-backend": ("Data", "Auxilary Backend Service"),
    "aqie-dc-poc-frontend": ("Citizen", "Prototype Service (including PoC)"),
    "aqie-dc-poc-backend": ("Data", "Prototype Service (including PoC)"),
    "aqie-prtr-frontend": ("Citizen", "Auxilary Frontend"),
    "aqie-prtr-backend": ("Data", "Auxilary Backend Service"),
    "aqie-demo-data-visualisations": ("Citizen", "Demo Service"),
    "aqie-laqm-data-explorer": ("Citizen", "Data/Analytics Support Service"),
    "aqie-kpi-metrics-dashboard": ("Shared", "Data/Analytics Support Service"),
    "aqie-docanalysispoc-frontend": ("Citizen", "Prototype Service (including PoC)"),
    "aqie-docanalysisawspoc-frontend": ("Citizen", "Prototype Service (including PoC)"),
    "aqie-docanalysispoc-backend": ("Data", "Prototype Service (including PoC)"),
    "aqie-data-service-backend": ("Data", "Auxilary Backend Service"),
    "AQIE-Citizen-Alpha": ("Citizen", "Prototype Service (including PoC)"),
}


@dataclass
class Repo:
    name: str
    html_url: str
    created_at: str | None
    default_branch: str
    main_last_modified_at: str | None
    archived: bool = False
    description: str | None = None
    language: str | None = None


def api_get(url: str, token: str) -> Any:
    req = Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "aq-dynamic-documentation-agent")
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"GitHub API error {exc.code} for {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error for {url}: {exc}") from exc


def classify(name: str) -> str:
    if name in SERVICE_OVERRIDES:
        return SERVICE_OVERRIDES[name][1]
    n = name.lower()
    if "poc" in n or "prototype" in n:
        return "Prototype Service (including PoC)"
    if "demo" in n:
        return "Demo Service"
    if "perftest" in n or "perf-" in n or n.endswith("-test") or "journey-tests" in n:
        return "Quality/Test Service"
    if "frontend" in n or "front-end" in n:
        return "Auxilary Frontend"
    if "backend" in n or "api" in n or "service" in n:
        return "Auxilary Backend Service"
    if "dashboard" in n or "explorer" in n or "visualisation" in n:
        return "Data/Analytics Support Service"
    return "Auxilary Backend Service"


def domain(name: str) -> str:
    if name in SERVICE_OVERRIDES:
        return SERVICE_OVERRIDES[name][0]
    n = name.lower()
    if "perftest" in n or "perf-" in n or "test" in n:
        return "Shared"
    if "frontend" in n or "front-end" in n:
        return "Citizen"
    if "backend" in n or "api" in n or "service" in n:
        return "Data"
    return "Shared"


def load_confirmed_connections() -> dict[str, set[str]]:
    """Read evidence-backed edges from the integration catalogue.

    Falls back to an empty mapping when the catalogue is absent so metadata
    refresh still works; connections are then reported as unconfirmed rather
    than guessed from repository names.
    """
    if not INTEGRATION_CATALOG_PATH.exists():
        return {}
    try:
        import yaml
    except ImportError:
        print("PyYAML not installed; connections will be reported as unconfirmed.", file=sys.stderr)
        return {}

    data = yaml.safe_load(INTEGRATION_CATALOG_PATH.read_text(encoding="utf-8")) or {}
    edges: dict[str, set[str]] = {}
    for item in data.get("integrations", []):
        if item.get("target_kind") != "aqie-service":
            continue
        src, tgt = item.get("source"), item.get("target")
        if not src or not tgt:
            continue
        edges.setdefault(src, set()).add(tgt)
        edges.setdefault(tgt, set()).add(src)
    return edges


def activity_status(last_modified: str | None, now: datetime) -> str:
    if not last_modified:
        return "Unknown"
    dt = datetime.fromisoformat(last_modified.replace("Z", "+00:00"))
    days = (now - dt).days
    if days <= 90:
        return "Active"
    if days <= 180:
        return "Monitoring"
    return "Inactive"


def fetch_repositories(token: str) -> list[Repo]:
    """Discover AQIE repositories via the search API.

    The org listing endpoint was previously used but silently missed archived
    and older repositories, so the catalogue under-reported the estate.
    """
    page = 1
    raw_repos: dict[str, dict[str, Any]] = {}
    while True:
        url = (
            "https://api.github.com/search/repositories"
            f"?q=org:DEFRA+aqie+in:name&per_page=100&page={page}"
        )
        payload = api_get(url, token)
        items = payload.get("items", [])
        if not items:
            break
        for item in items:
            if item.get("name", "").lower().startswith("aqie"):
                raw_repos[item["name"]] = item
        if len(items) < 100 or page >= 10:
            break
        page += 1

    repos: list[Repo] = []
    for repo_name in sorted(raw_repos):
        repo = raw_repos[repo_name]
        default_branch = repo.get("default_branch", "main")
        branch_url = f"https://api.github.com/repos/DEFRA/{quote(repo_name)}/branches/{quote(default_branch)}"
        try:
            branch = api_get(branch_url, token)
            main_last_modified = (
                branch.get("commit", {}).get("commit", {}).get("committer", {}).get("date")
            )
        except RuntimeError:
            main_last_modified = repo.get("pushed_at")
        repos.append(
            Repo(
                name=repo_name,
                html_url=repo.get("html_url", f"https://github.com/DEFRA/{repo_name}"),
                created_at=repo.get("created_at"),
                default_branch=default_branch,
                main_last_modified_at=main_last_modified,
                archived=bool(repo.get("archived")),
                description=repo.get("description"),
                language=repo.get("language"),
            )
        )
    return repos


def write_catalog(repos: list[Repo], now: datetime) -> None:
    connections = load_confirmed_connections()
    known = {r.name for r in repos}

    lines: list[str] = []
    lines.extend(
        [
            "catalog_version: 4",
            f'updated_at_utc: "{now.strftime("%Y-%m-%dT%H:%M:%SZ")}"',
            'analysis_branch_policy: "main-only"',
            "discovery:",
            '  source_url: "https://api.github.com/search/repositories?q=org:DEFRA+aqie+in:name"',
            '  source_org: "DEFRA"',
            '  source_query: "aqie in:name"',
            f'  discovered_at_utc: "{now.strftime("%Y-%m-%dT%H:%M:%SZ")}"',
            "type_taxonomy:",
            '  - "Core Frontend Service"',
            '  - "Core Backend Service"',
            '  - "Auxilary Frontend"',
            '  - "Auxilary Backend Service"',
            '  - "Demo Service"',
            '  - "Prototype Service (including PoC)"',
            '  - "Quality/Test Service"',
            '  - "Data/Analytics Support Service"',
            "activity_status_rule:",
            "  active_days_max: 90",
            "  monitoring_days_max: 180",
            '  basis: "default branch head commit timestamp"',
            "connected_services_rule:",
            '  source: "/docs/integration-catalog.yaml"',
            '  basis: "evidence-backed edges only; empty means no integration evidence found"',
            "repositories:",
        ]
    )

    for repo in repos:
        connected = sorted(connections.get(repo.name, set()) & known)
        lines.extend(
            [
                f'  - service_domain: "{domain(repo.name)}"',
                f'    service_name: "{repo.name}"',
                f'    type: "{classify(repo.name)}"',
                f'    repository_url: "{repo.html_url}"',
                f'    default_branch: "{repo.default_branch}"',
                f'    archived: {"true" if repo.archived else "false"}',
                f'    primary_language: "{repo.language}"' if repo.language else "    primary_language: null",
                f'    created_at_utc: "{repo.created_at}"' if repo.created_at else "    created_at_utc: null",
                (
                    f'    last_modified_at_utc: "{repo.main_last_modified_at}"'
                    if repo.main_last_modified_at
                    else "    last_modified_at_utc: null"
                ),
                f'    activity_status: "{"Archived" if repo.archived else activity_status(repo.main_last_modified_at, now)}"',
                "    last_analysed_at_utc: null",
                "    last_analysed_main_commit: null",
            ]
        )
        if connected:
            lines.append("    connected_services:")
            for service in connected:
                lines.append(f'      - "{service}"')
        else:
            lines.append("    connected_services: []")
        doc_path = f"/docs/services/{domain(repo.name).lower()}/{repo.name}/service-profile.md"
        lines.append(f'    documentation_path: "{doc_path}"')

    CATALOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_inventory(repos: list[Repo], now: datetime) -> None:
    connections = load_confirmed_connections()
    known = {r.name for r in repos}

    lines = [
        "# DEFRA AQIE Repository Inventory",
        "",
        "Discovery query: `org:DEFRA aqie in:name` via the GitHub search API.",
        "",
        f"Generated at: `{now.strftime('%Y-%m-%dT%H:%M:%SZ')}`",
        "",
        "Connected services are taken from evidence-backed edges in",
        "[`/docs/integration-catalog.yaml`](../integration-catalog.yaml). An empty cell means no",
        "integration evidence was found on the default branch, not that the service is isolated.",
        "",
        "| Repository | Domain | Type | Language | Created (UTC) | Last Main Commit (UTC) | Status | Connected Services |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for repo in repos:
        connected = sorted(connections.get(repo.name, set()) & known)
        status = "Archived" if repo.archived else activity_status(repo.main_last_modified_at, now)
        lines.append(
            f"| [{repo.name}]({repo.html_url}) | {domain(repo.name)} | {classify(repo.name)} "
            f"| {repo.language or '—'} | {(repo.created_at or '')[:10]} | {(repo.main_last_modified_at or '')[:19]} | "
            f"{status} | {', '.join(connected) if connected else '—'} |"
        )

    INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("DEFRA_READONLY_PAT")
    if not token:
        print("Missing token. Set GITHUB_TOKEN or DEFRA_READONLY_PAT.", file=sys.stderr)
        return 1
    now = datetime.now(UTC)
    repos = fetch_repositories(token)
    write_catalog(repos, now)
    write_inventory(repos, now)
    print(f"Updated metadata for {len(repos)} repositories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
