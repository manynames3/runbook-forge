"""Approval gates that keep all infrastructure-changing actions recommend-only."""

from __future__ import annotations

from runbook_forge.models import ActionMode, ApprovalGate, RecommendedAction


def read_only_action(title: str, description: str, command: str | None = None) -> RecommendedAction:
    return RecommendedAction(
        title=title,
        description=description,
        command=command,
        mode=ActionMode.READ_ONLY,
    )


def propose_only_action(
    title: str, description: str, command: str | None = None
) -> RecommendedAction:
    return RecommendedAction(
        title=title,
        description=description,
        command=command,
        mode=ActionMode.PROPOSE_ONLY,
    )


def approval_required_action(
    title: str, description: str, command: str | None = None
) -> RecommendedAction:
    return RecommendedAction(
        title=title,
        description=description,
        command=command,
        mode=ActionMode.REQUIRES_HUMAN_APPROVAL,
    )


def gate_for_write(reason: str) -> ApprovalGate:
    return ApprovalGate(
        mode=ActionMode.REQUIRES_HUMAN_APPROVAL,
        reason=reason,
    )


def gate_for_proposal(reason: str) -> ApprovalGate:
    return ApprovalGate(
        mode=ActionMode.PROPOSE_ONLY,
        reason=reason,
    )
