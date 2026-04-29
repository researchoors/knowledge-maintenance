"""Temporal validator — compare generated knowledge against the actual codebase.

Runs deterministic checks (no LLM) to find:
- stale_references: files/modules referenced in knowledge but removed from codebase
- stale_edges: dependency/call edges pointing to non-existent components
- misclassified_components: component kinds that don't match re-discovered kinds
- missing_components: new components in the codebase not present in knowledge
"""

import json
import subprocess
from datetime import UTC
from pathlib import Path

from knowledge_maintenance.models import Discrepancy, ValidationReport


def _get_codebase_files(repo_path: Path) -> set[str]:
    """Get all tracked files in the repository via git ls-files."""
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        cwd=repo_path,
        check=True,
    )
    return {f for f in result.stdout.strip().splitlines() if f}


def _load_components(artifacts_dir: Path) -> list[dict]:
    """Load components from service_discovery/components.json."""
    path = artifacts_dir / "service_discovery" / "components.json"
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("components", [])
    if isinstance(data, list):
        return data
    return []


def _load_edges(artifacts_dir: Path) -> list[dict]:
    """Load edges from dependency_graphs/graph.json."""
    path = artifacts_dir / "dependency_graphs" / "graph.json"
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    return data.get("edges", [])


def _check_stale_references(
    components: list[dict], codebase_files: set[str]
) -> list[Discrepancy]:
    """Detect knowledge entries that reference files/modules absent from the codebase."""
    discrepancies: list[Discrepancy] = []
    for comp in components:
        root = comp.get("root_path", "")
        if root and root not in codebase_files and not any(
            f.startswith(root.rstrip("/") + "/") for f in codebase_files
        ):
            discrepancies.append(
                Discrepancy(
                    kind="stale_reference",
                    description=f"Component '{comp['name']}' root_path '{root}' no longer exists in codebase",
                    location=f"service_discovery/components.json::{comp['name']}",
                    severity="high",
                )
            )
        for key_file in comp.get("key_files", []):
            if key_file not in codebase_files:
                discrepancies.append(
                    Discrepancy(
                        kind="stale_reference",
                        description=f"Component '{comp['name']}' key_file '{key_file}' no longer exists",
                        location=f"service_discovery/components.json::{comp['name']}::{key_file}",
                        severity="medium",
                    )
                )
    return discrepancies


def _check_stale_edges(
    edges: list[dict], component_names: set[str], external_ids: set[str]
) -> list[Discrepancy]:
    """Detect dependency edges that reference non-existent targets."""
    discrepancies: list[Discrepancy] = []
    valid_targets = component_names | external_ids
    for edge in edges:
        source = edge.get("source", "")
        target = edge.get("target", "")
        if source and source not in component_names:
            discrepancies.append(
                Discrepancy(
                    kind="stale_edge",
                    description=f"Edge source '{source}' not found in components",
                    location=f"dependency_graphs/graph.json::{source}->{target}",
                    severity="high",
                )
            )
        if target and target not in valid_targets:
            discrepancies.append(
                Discrepancy(
                    kind="stale_edge",
                    description=f"Edge target '{target}' not found in components or external services",
                    location=f"dependency_graphs/graph.json::{source}->{target}",
                    severity="medium",
                )
            )
    return discrepancies


def _check_component_kinds(
    known_components: list[dict], rediscovered_components: list[dict]
) -> list[Discrepancy]:
    """Detect components whose kind classification has changed."""
    discrepancies: list[Discrepancy] = []
    rediscovered_kinds = {c["name"]: c.get("kind", "unknown") for c in rediscovered_components}
    for comp in known_components:
        name = comp["name"]
        known_kind = comp.get("kind", "unknown")
        if name in rediscovered_kinds and known_kind != rediscovered_kinds[name]:
            discrepancies.append(
                Discrepancy(
                    kind="misclassified_component",
                    description=(
                        f"Component '{name}' classified as '{known_kind}'"
                        f" but re-discovery found '{rediscovered_kinds[name]}'"
                    ),
                    location=f"service_discovery/components.json::{name}",
                    severity="medium",
                )
            )
    return discrepancies


def _check_missing_components(
    known_components: list[dict], rediscovered_components: list[dict]
) -> list[Discrepancy]:
    """Detect new components in the codebase that are not present in knowledge."""
    discrepancies: list[Discrepancy] = []
    known_names = {c["name"] for c in known_components}
    for comp in rediscovered_components:
        if comp["name"] not in known_names:
            discrepancies.append(
                Discrepancy(
                    kind="missing_component",
                    description=f"Component '{comp['name']}' exists in codebase but not in knowledge graph",
                    location="service_discovery/components.json",
                    severity="low",
                )
            )
    return discrepancies


def validate(
    *,
    repo_path: Path,
    artifacts_dir: Path,
    commit_sha: str,
    rediscovered_components: list[dict] | None = None,
) -> ValidationReport:
    """Run all temporal validation checks and return a ValidationReport.

    If rediscovered_components is provided, uses it for kind/diff checks.
    Otherwise, only runs file and edge checks against the existing knowledge.
    """
    from datetime import datetime

    codebase_files = _get_codebase_files(repo_path)
    known_components = _load_components(artifacts_dir)
    edges = _load_edges(artifacts_dir)

    component_names = {c["name"] for c in known_components}
    # Load external service IDs from graph
    graph_path = artifacts_dir / "dependency_graphs" / "graph.json"
    external_ids: set[str] = set()
    if graph_path.exists():
        with open(graph_path) as f:
            graph_data = json.load(f)
        for svc in graph_data.get("external_services", {}).values():
            if isinstance(svc, dict) and "id" in svc:
                external_ids.add(svc["id"])

    discrepancies: list[Discrepancy] = []
    discrepancies.extend(_check_stale_references(known_components, codebase_files))
    discrepancies.extend(_check_stale_edges(edges, component_names, external_ids))

    if rediscovered_components is not None:
        discrepancies.extend(_check_component_kinds(known_components, rediscovered_components))
        discrepancies.extend(_check_missing_components(known_components, rediscovered_components))

    return ValidationReport(
        timestamp=datetime.now(UTC),
        commit_sha=commit_sha,
        discrepancies=discrepancies,
        is_valid=len(discrepancies) == 0,
    )
