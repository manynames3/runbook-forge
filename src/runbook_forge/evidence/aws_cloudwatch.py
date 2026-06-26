"""CloudWatch-style log loading helpers for local fixture data."""

from __future__ import annotations

from pathlib import Path

from runbook_forge.safety.redaction import redact_text


def load_log_lines(path: Path) -> list[str]:
    return [redact_text(line.rstrip()) for line in path.read_text(encoding="utf-8").splitlines()]

