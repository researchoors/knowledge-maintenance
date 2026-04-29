"""Pydantic models for knowledge maintenance."""

from datetime import datetime

from pydantic import BaseModel, Field


class Discrepancy(BaseModel):
    """A single discrepancy found during temporal validation."""

    kind: str = Field(
        description="Category: stale_reference, stale_edge, misclassified_component, missing_component, stale_claim"
    )
    description: str = Field(description="Human-readable description of the discrepancy")
    location: str = Field(description="File, module, or component where the discrepancy was found")
    severity: str = Field(description="Severity level: low, medium, high, critical")


class ValidationReport(BaseModel):
    """Report produced after validating generated knowledge against the actual codebase."""

    timestamp: datetime = Field(description="When the validation was performed (UTC)")
    commit_sha: str = Field(description="The commit SHA being validated")
    discrepancies: list[Discrepancy] = Field(default_factory=list, description="All discrepancies found")
    is_valid: bool = Field(description="True when no discrepancies were found")


class CommitSnapshot(BaseModel):
    """A lightweight snapshot of a git commit."""

    commit_sha: str = Field(description="Full commit SHA")
    timestamp: datetime = Field(description="Commit author date")
    author: str = Field(description="Commit author name")
    message: str = Field(description="Commit message (first line)")
