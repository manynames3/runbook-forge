"""Local procedural memory for repeated incident fingerprints."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from runbook_forge.models import PatternRecord


def normalize_part(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "unknown"


def fingerprint_for(evidence_type: str, likely_cause: str, affected_system: str) -> str:
    parts = [evidence_type, likely_cause, affected_system]
    return "::".join(normalize_part(part) for part in parts)


class PatternMemory:
    def __init__(self, path: Path = Path(".runbook_forge/patterns.json")) -> None:
        self.path = path

    def record(self, evidence_type: str, likely_cause: str, affected_system: str) -> PatternRecord:
        now = datetime.now(UTC).isoformat()
        fingerprint = fingerprint_for(evidence_type, likely_cause, affected_system)
        records = self._load()
        if fingerprint in records:
            record = records[fingerprint]
            record.count += 1
            record.last_seen = now
        else:
            record = PatternRecord(
                fingerprint=fingerprint,
                evidence_type=evidence_type,
                likely_cause=likely_cause,
                affected_system=affected_system,
                count=1,
                first_seen=now,
                last_seen=now,
            )
        records[fingerprint] = record
        self._save(records)
        return record

    @staticmethod
    def should_propose_skill(record: PatternRecord) -> bool:
        return record.count > 1

    def _load(self) -> dict[str, PatternRecord]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return {key: PatternRecord.model_validate(value) for key, value in raw.items()}

    def _save(self, records: dict[str, PatternRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {key: record.model_dump(mode="json") for key, record in sorted(records.items())}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

