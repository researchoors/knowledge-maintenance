"""Tests for pydantic models."""

from datetime import UTC, datetime

from knowledge_maintenance.models import CommitSnapshot, Discrepancy, ValidationReport


class TestDiscrepancy:
    def test_create_from_dict(self, sample_discrepancy_data: dict) -> None:
        d = Discrepancy(**sample_discrepancy_data)
        assert d.kind == "stale_reference"
        assert d.severity == "high"

    def test_serialization_roundtrip(self, sample_discrepancy_data: dict) -> None:
        d = Discrepancy(**sample_discrepancy_data)
        json_str = d.model_dump_json()
        d2 = Discrepancy.model_validate_json(json_str)
        assert d2 == d

    def test_all_severity_levels(self) -> None:
        for severity in ("low", "medium", "high", "critical"):
            d = Discrepancy(kind="test", description="test", location="test", severity=severity)
            assert d.severity == severity


class TestValidationReport:
    def test_valid_report(self) -> None:
        report = ValidationReport(
            timestamp=datetime.now(UTC),
            commit_sha="abc123",
            discrepancies=[],
            is_valid=True,
        )
        assert report.is_valid is True
        assert len(report.discrepancies) == 0

    def test_invalid_report_with_discrepancies(self, sample_discrepancy_data: dict) -> None:
        d = Discrepancy(**sample_discrepancy_data)
        report = ValidationReport(
            timestamp=datetime.now(UTC),
            commit_sha="abc123",
            discrepancies=[d],
            is_valid=False,
        )
        assert report.is_valid is False
        assert len(report.discrepancies) == 1

    def test_serialization_roundtrip(self, sample_discrepancy_data: dict) -> None:
        d = Discrepancy(**sample_discrepancy_data)
        report = ValidationReport(
            timestamp=datetime.now(UTC),
            commit_sha="abc123",
            discrepancies=[d],
            is_valid=False,
        )
        json_str = report.model_dump_json()
        report2 = ValidationReport.model_validate_json(json_str)
        assert report2.commit_sha == report.commit_sha
        assert len(report2.discrepancies) == 1


class TestCommitSnapshot:
    def test_create_and_serialize(self) -> None:
        snap = CommitSnapshot(
            commit_sha="abc1234",
            timestamp=datetime.now(UTC),
            author="Ethan",
            message="feat: add new module",
        )
        assert snap.author == "Ethan"
        data = snap.model_dump()
        assert data["commit_sha"] == "abc1234"
