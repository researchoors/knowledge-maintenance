"""Tests for temporal validator."""

from pathlib import Path

from knowledge_maintenance.temporal_validator import (
    _check_component_kinds,
    _check_missing_components,
    _check_stale_edges,
    _check_stale_references,
    validate,
)


class TestStaleReferences:
    def test_no_stale_refs(self) -> None:
        components = [{"name": "coordinator", "root_path": "coordinator", "key_files": ["coordinator/src/main.rs"]}]
        codebase_files = {"coordinator", "coordinator/src/main.rs"}
        result = _check_stale_references(components, codebase_files)
        assert result == []

    def test_missing_root_path(self) -> None:
        components = [{"name": "coordinator", "root_path": "deleted-module", "key_files": []}]
        codebase_files: set[str] = set()
        result = _check_stale_references(components, codebase_files)
        assert len(result) == 1
        assert result[0].kind == "stale_reference"
        assert "deleted-module" in result[0].description

    def test_missing_key_file(self) -> None:
        components = [{"name": "coordinator", "root_path": "coordinator", "key_files": ["coordinator/src/gone.rs"]}]
        codebase_files = {"coordinator", "coordinator/src/main.rs"}
        result = _check_stale_references(components, codebase_files)
        assert len(result) == 1
        assert "gone.rs" in result[0].description


class TestStaleEdges:
    def test_valid_edges(self) -> None:
        edges = [{"source": "coordinator", "target": "crypto"}]
        result = _check_stale_edges(edges, {"coordinator", "crypto"}, set())
        assert result == []

    def test_edge_to_missing_target(self) -> None:
        edges = [{"source": "coordinator", "target": "deleted-lib"}]
        result = _check_stale_edges(edges, {"coordinator"}, set())
        assert len(result) == 1
        assert result[0].kind == "stale_edge"
        assert "deleted-lib" in result[0].description

    def test_edge_to_external_service(self) -> None:
        edges = [{"source": "coordinator", "target": "aws-s3"}]
        result = _check_stale_edges(edges, {"coordinator"}, {"aws-s3"})
        assert result == []

    def test_edge_from_missing_source(self) -> None:
        edges = [{"source": "phantom", "target": "crypto"}]
        result = _check_stale_edges(edges, {"crypto"}, set())
        assert len(result) == 1
        assert "phantom" in result[0].description


class TestComponentKinds:
    def test_matching_kinds(self) -> None:
        known = [{"name": "coordinator", "kind": "service"}]
        rediscovered = [{"name": "coordinator", "kind": "service"}]
        result = _check_component_kinds(known, rediscovered)
        assert result == []

    def test_kind_changed(self) -> None:
        known = [{"name": "worker", "kind": "library"}]
        rediscovered = [{"name": "worker", "kind": "service"}]
        result = _check_component_kinds(known, rediscovered)
        assert len(result) == 1
        assert result[0].kind == "misclassified_component"
        assert "library" in result[0].description and "service" in result[0].description


class TestMissingComponents:
    def test_no_missing(self) -> None:
        known = [{"name": "coordinator"}]
        rediscovered = [{"name": "coordinator"}]
        result = _check_missing_components(known, rediscovered)
        assert result == []

    def test_new_component_discovered(self) -> None:
        known = [{"name": "coordinator"}]
        rediscovered = [{"name": "coordinator"}, {"name": "new-service", "kind": "service"}]
        result = _check_missing_components(known, rediscovered)
        assert len(result) == 1
        assert result[0].kind == "missing_component"
        assert "new-service" in result[0].description


class TestFullValidation:
    def test_valid_artifacts(self, tmp_artifacts: Path, tmp_path: Path) -> None:
        """When codebase files match knowledge, validation passes."""
        # Create a fake repo with matching files
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "coordinator").mkdir()
        (repo / "coordinator" / "src").mkdir()
        (repo / "coordinator" / "src" / "main.rs").write_text("fn main() {}")
        (repo / "coordinator" / "src" / "lib.rs").write_text("pub mod foo;")
        (repo / "crypto").mkdir()
        (repo / "crypto" / "src").mkdir()
        (repo / "crypto" / "src" / "lib.rs").write_text("pub mod bar;")
        # Initialize as git repo so git ls-files works
        import subprocess

        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=repo,
            capture_output=True,
            check=True,
            env={
                "GIT_AUTHOR_NAME": "test",
                "GIT_AUTHOR_EMAIL": "test@test.com",
                "GIT_COMMITTER_NAME": "test",
                "GIT_COMMITTER_EMAIL": "test@test.com",
            },
        )

        report = validate(
            repo_path=repo,
            artifacts_dir=tmp_artifacts,
            commit_sha="abc123",
        )
        assert report.is_valid is True
        assert report.commit_sha == "abc123"

    def test_stale_root_detected(self, tmp_artifacts: Path, tmp_path: Path) -> None:
        """When a component root is missing from codebase, stale_reference is flagged."""
        repo = tmp_path / "repo"
        repo.mkdir()
        # Only create coordinator, not crypto
        (repo / "coordinator").mkdir()
        (repo / "coordinator" / "src").mkdir()
        (repo / "coordinator" / "src" / "main.rs").write_text("fn main() {}")
        (repo / "coordinator" / "src" / "lib.rs").write_text("pub mod foo;")

        import subprocess

        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=repo,
            capture_output=True,
            check=True,
            env={
                "GIT_AUTHOR_NAME": "test",
                "GIT_AUTHOR_EMAIL": "test@test.com",
                "GIT_COMMITTER_NAME": "test",
                "GIT_COMMITTER_EMAIL": "test@test.com",
            },
        )

        report = validate(
            repo_path=repo,
            artifacts_dir=tmp_artifacts,
            commit_sha="abc123",
        )
        assert report.is_valid is False
        assert any(d.kind == "stale_reference" and "crypto" in d.description for d in report.discrepancies)
