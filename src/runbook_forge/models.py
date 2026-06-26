"""Typed domain models shared by analyzers, reports, and safety controls."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionMode(StrEnum):
    READ_ONLY = "read_only"
    PROPOSE_ONLY = "propose_only"
    REQUIRES_HUMAN_APPROVAL = "requires_human_approval"


class EvidenceItem(BaseModel):
    source: str
    detail: str
    locator: str | None = None
    redacted: bool = False


class ApprovalGate(BaseModel):
    mode: ActionMode
    reason: str


class RecommendedAction(BaseModel):
    title: str
    description: str
    mode: ActionMode = ActionMode.PROPOSE_ONLY
    command: str | None = None


class RiskFinding(BaseModel):
    id: str
    title: str
    severity: Severity
    affected_resource: str
    evidence: list[EvidenceItem]
    blast_radius: str
    recommendation: str
    approval: ApprovalGate


class AnalysisReport(BaseModel):
    report_type: str
    severity: Severity
    affected_system: str
    executive_summary: str
    evidence_reviewed: list[EvidenceItem]
    likely_root_cause: str
    risk_blast_radius: str
    findings: list[RiskFinding] = Field(default_factory=list)
    recommended_actions: list[RecommendedAction] = Field(default_factory=list)
    related_runbook_skill: str | None = None
    pattern_fingerprint: str
    pattern_seen_count: int = 1
    proposed_skill: bool = False
    audit_metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def with_timestamp(cls, **data: Any) -> AnalysisReport:
        audit_metadata = dict(data.pop("audit_metadata", {}))
        audit_metadata.setdefault("generated_at", datetime.now(UTC).isoformat())
        audit_metadata.setdefault("engine", "runbook-forge")
        return cls(audit_metadata=audit_metadata, **data)


class PatternRecord(BaseModel):
    fingerprint: str
    evidence_type: str
    likely_cause: str
    affected_system: str
    count: int = 0
    first_seen: str
    last_seen: str
