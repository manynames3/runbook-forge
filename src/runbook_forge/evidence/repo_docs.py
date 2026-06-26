"""Repository documentation helpers for future incident context enrichment."""

from __future__ import annotations

from pathlib import Path

from runbook_forge.safety.redaction import redact_text


def collect_markdown_summaries(root: Path, limit: int = 5) -> list[str]:
    summaries: list[str] = []
    for path in sorted(root.rglob("*.md")):
        if any(part.startswith(".") for part in path.parts):
            continue
        first_lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[:6]
        summaries.append(f"{path}: {redact_text(' '.join(first_lines))}")
        if len(summaries) >= limit:
            break
    return summaries

