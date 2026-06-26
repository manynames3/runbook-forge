"""Severity helpers for combining risk findings."""

from __future__ import annotations

from runbook_forge.models import Severity

SEVERITY_RANK: dict[Severity, int] = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


def max_severity(values: list[Severity], default: Severity = Severity.LOW) -> Severity:
    if not values:
        return default
    return max(values, key=lambda severity: SEVERITY_RANK[severity])

