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


@dataclass
class Repo:
    name: str
    html_url: str
    created_at: str | None
    default_branch: str
    main_last_modified_at: str | None


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
    n = name.lower()
    if "poc" in n or "prototype" in n:
        return "Prototype Service (including PoC)"
    if "demo" in n:
        return "Demo Service"
    if "perftest" in n or n.endswith("-test") or "journey-tests" in n:
        return "Quality/Test Service"
    if name == "aqie-front-end":
        return "Core Frontend Service"
    if name == "aqie-back-end":
        return "Core Backend Service"
    if "frontend" in n or "front-end" in n:
        return "Auxilary Frontend"
    if "backend" in n or "api" in n or "service" in n:
        return "Auxilary Backend Service"
    if "dashboard" in n or "explorer" in n or "visualisation" in n:
        return "Data/Analytics Support Service"
    return "Auxilary Backend Service"


def domain(name: str) -> str:
    n = name.lower()
    if "frontend" in n or "front-end" in n or "maps" in n or "dashboard" in n or "explorer" in n:
        return "Citizen"
    if "backend" in n or "api" in n or "notify" in n or "monitoringstation" in n or "historicaldata" in n:
        return "Data"
    if "test" in n or "perftest" in n:
        return "Shared"
    return "Shared"


def family(name: str) -> str:
    n = name.lower()
    if "dc-" in n:
        return "dc"
    if "prtr" in n:
        return "prtr"
    if "privatebeta" in n:
        return "privatebeta"
    if "maps" in n:
        return "maps"
    if "docanalysis" in n:
        return "docanalysis"
    if name in ("aqie-front-end", "aqie-back-end"):
        return "core"
    return name


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
    page = 1
    raw_repos: list[dict[str, Any]] = []
    while True:
        url = f"https://api.github.com/orgs/DEFRA/repos?type=public&per_page=100&page={page}"
        batch = api_get(url, token)
        if not batch:
            break
        raw_repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    aqie_raw = [r for r in raw_repos if r.get("name", "").lower().startswith("aqie")]
    aqie_raw.sort(key=lambda r: r["name"])

    repos: list[Repo] = []
    for repo in aqie_raw:
        repo_name = repo["name"]
        default_branch = repo.get("default_branch", "main")
        branch_url = f"https://api.github.com/repos/DEFRA/{quote(repo_name)}/branches/{quote(default_branch)}"
        branch = api_get(branch_url, token)
        main_last_modified = (
            branch.get("commit", {})
            .get("commit", {})
            .get("committer", {})
            .get("date")
        )
        repos.append(
            Repo(
                name=repo_name,
                html_url=repo.get("html_url", f"https://github.com/DEFRA/{repo_name}"),
                created_at=repo.get("created_at"),
                default_branch=default_branch,
                main_last_modified_at=main_last_modified,
            )
        )
    return repos


def write_catalog(repos: list[Repo], now: datetime) -> None:
    fams: dict[str, list[str]] = {}
    for repo in repos:
        fams.setdefault(family(repo.name), []).append(repo.name)

    lines: list[str] = []
    lines.extend(
        [
            "catalog_version: 3",
            f'updated_at_utc: "{now.strftime("%Y-%m-%dT%H:%M:%SZ")}"',
            'analysis_branch_policy: "main-only"',
            "discovery:",
            '  source_url: "https://api.github.com/orgs/DEFRA/repos"',
            '  source_org: "DEFRA"',
            '  source_query: "name starts with aqie"',
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
            '  status: "provisional-until-confirmed"',
            "repositories:",
        ]
    )

    for repo in repos:
        connected = [x for x in fams[family(repo.name)] if x != repo.name]
        lines.extend(
            [
                f'  - service_domain: "{domain(repo.name)}"',
                f'    service_name: "{repo.name}"',
                f'    type: "{classify(repo.name)}"',
                f'    repository_url: "{repo.html_url}"',
                f'    default_branch: "{repo.default_branch}"',
                f'    created_at_utc: "{repo.created_at}"' if repo.created_at else "    created_at_utc: null",
                (
                    f'    last_modified_at_utc: "{repo.main_last_modified_at}"'
                    if repo.main_last_modified_at
                    else "    last_modified_at_utc: null"
                ),
                f'    activity_status: "{activity_status(repo.main_last_modified_at, now)}"',
                "    last_analysed_at_utc: null",
                "    last_analysed_main_commit: null",
                "    connected_services_provisional: true",
                "    connected_services:",
            ]
        )
        if connected:
            for service in connected:
                lines.append(f'      - "{service}"')
        else:
            lines.append('      - "none-confirmed"')
        lines.extend(
            [
                "    documentation_path: null",
                "    metadata_notes:",
                '      - "Connections are provisional until service owners confirm integration mapping."',
            ]
        )

    CATALOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_inventory(repos: list[Repo], now: datetime) -> None:
    fams: dict[str, list[str]] = {}
    for repo in repos:
        fams.setdefault(family(repo.name), []).append(repo.name)

    lines = [
        "# DEFRA AQIE Repository Inventory",
        "",
        "Source query: `https://api.github.com/orgs/DEFRA/repos` (filter: names starting with `aqie`)",
        f"",
        f"Generated at: `{now.strftime('%Y-%m-%dT%H:%M:%SZ')}`",
        "",
        "_Connected services are provisional until confirmed._",
        "",
        "| Repository | Domain | Type | Created (UTC) | Last Modified (Main, UTC) | Active Status | Connected Services (Provisional) |",
        "|---|---|---|---|---|---|---|",
    ]
    for repo in repos:
        connections = [x for x in fams[family(repo.name)] if x != repo.name]
        lines.append(
            f"| [{repo.name}]({repo.html_url}) | {domain(repo.name)} | {classify(repo.name)} "
            f"| {repo.created_at or ''} | {repo.main_last_modified_at or ''} | "
            f"{activity_status(repo.main_last_modified_at, now)} | "
            f"{', '.join(connections) if connections else 'none-confirmed'} |"
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
