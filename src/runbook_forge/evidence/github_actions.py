"""GitHub Actions fixture loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runbook_forge.safety.redaction import redact_value


def load_actions_fixture(path: Path) -> dict[str, Any]:
    return redact_value(json.loads(path.read_text(encoding="utf-8")))

