"""Markdown rendering for Runbook Forge reports."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from runbook_forge.models import ActionMode, AnalysisReport
from runbook_forge.safety.redaction import redact_text


def render_report(report: AnalysisReport) -> str:
    lines = [
        f"# Runbook Forge Report: {report.report_type}",
        "",
        "## Executive summary",
        report.executive_summary,
        "",
        "## Severity",
        report.severity.value,
        "",
        "## Affected system",
        report.affected_system,
        "",
        "## Evidence reviewed",
    ]
    lines.extend(_evidence_lines(report.evidence_reviewed))
    lines.extend(
        [
            "",
            "## Likely root cause",
            report.likely_root_cause,
            "",
            "## Risk / blast radius",
            report.risk_blast_radius,
            "",
            "## Findings",
        ]
    )
    if report.findings:
        for finding in report.findings:
            lines.extend(
                [
                    f"### {finding.title}",
                    f"- ID: `{finding.id}`",
                    f"- Severity: `{finding.severity.value}`",
                    f"- Affected resource: `{finding.affected_resource}`",
                    f"- Blast radius: {finding.blast_radius}",
                    f"- Recommendation: {finding.recommendation}",
                    f"- Approval gate: `{finding.approval.mode.value}` - {finding.approval.reason}",
                    "- Evidence:",
                ]
            )
            lines.extend(_evidence_lines(finding.evidence))
    else:
        lines.append("- No structured risk findings were generated for this report type.")
    lines.extend(
        [
            "",
            "## Recommended next actions",
        ]
    )
    for index, action in enumerate(report.recommended_actions, start=1):
        lines.append(f"{index}. {action.title} (`{action.mode.value}`): {action.description}")
        if action.command:
            lines.append(f"   Proposed command: `{action.command}`")
    approval_actions = [
        action
        for action in report.recommended_actions
        if action.mode == ActionMode.REQUIRES_HUMAN_APPROVAL
    ]
    lines.extend(
        [
            "",
            "## Human approval required before write actions",
            (
                "Yes. The following actions are recommend-only and must be manually approved: "
                + ", ".join(action.title for action in approval_actions)
                if approval_actions
                else "No write action is recommended by this report."
            ),
            "",
            "## Related or newly proposed runbook skill",
            _related_skill_text(report),
            "",
            "## Audit metadata",
            f"- Pattern fingerprint: `{report.pattern_fingerprint}`",
            f"- Pattern seen count: `{report.pattern_seen_count}`",
            f"- Proposed skill due to recurrence: `{str(report.proposed_skill).lower()}`",
        ]
    )
    for key, value in sorted(report.audit_metadata.items()):
        lines.append(f"- {key}: `{value}`")
    return redact_text("\n".join(lines).rstrip() + "\n")


def write_report(report: AnalysisReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report(report), encoding="utf-8")


def _evidence_lines(items: Sequence[object]) -> list[str]:
    lines: list[str] = []
    for item in items:
        source = getattr(item, "source", "unknown")
        detail = getattr(item, "detail", "")
        locator = getattr(item, "locator", None)
        suffix = f" ({locator})" if locator else ""
        lines.append(f"- `{source}`: {detail}{suffix}")
    return lines or ["- No evidence recorded."]


def _related_skill_text(report: AnalysisReport) -> str:
    skill = report.related_runbook_skill or "none"
    if report.proposed_skill:
        return (
            f"Pattern recurrence threshold met. Create or update reusable runbook skill `{skill}`."
        )
    return f"Related skill: `{skill}`. Recurrence threshold has not been met yet."
