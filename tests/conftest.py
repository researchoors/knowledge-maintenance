"""Shared test fixtures."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_artifacts(tmp_path: Path) -> Path:
    """Create a minimal artifacts directory with components.json and graph.json."""
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()

    # service_discovery
    discovery_dir = artifacts / "service_discovery"
    discovery_dir.mkdir()
    components = [
        {
            "name": "coordinator",
            "kind": "service",
            "type": "rust-crate",
            "root_path": "coordinator",
            "key_files": ["coordinator/src/main.rs", "coordinator/src/lib.rs"],
        },
        {
            "name": "crypto",
            "kind": "library",
            "type": "rust-crate",
            "root_path": "crypto",
            "key_files": ["crypto/src/lib.rs"],
        },
    ]
    with open(discovery_dir / "components.json", "w") as f:
        json.dump({"components": components}, f)

    # dependency_graphs
    graph_dir = artifacts / "dependency_graphs"
    graph_dir.mkdir()
    graph = {
        "components": {c["name"]: c for c in components},
        "external_services": {"aws-s3": {"id": "aws-s3", "name": "AWS S3", "category": "object_storage"}},
        "edges": [
            {"source": "coordinator", "target": "crypto", "type": "depends_on"},
            {"source": "coordinator", "target": "aws-s3", "type": "integrates_with"},
        ],
    }
    with open(graph_dir / "graph.json", "w") as f:
        json.dump(graph, f)

    return artifacts


@pytest.fixture
def sample_discrepancy_data() -> dict:
    """Sample discrepancy data for model tests."""
    return {
        "kind": "stale_reference",
        "description": "File no longer exists",
        "location": "service_discovery/components.json",
        "severity": "high",
    }
