"""Local JSON-lines audit logging for generated reports and proposed skills."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runbook_forge.safety.redaction import redact_value


class AuditLogger:
    def __init__(self, path: Path = Path(".runbook_forge/audit.log")) -> None:
        self.path = path

    def log_event(self, event_type: str, metadata: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "metadata": redact_value(metadata),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")

