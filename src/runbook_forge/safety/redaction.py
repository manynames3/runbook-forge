"""Secret redaction utilities for evidence, reports, and audit logs."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS_ACCESS_KEY_REDACTED"),
    (re.compile(r"\bASIA[0-9A-Z]{16}\b"), "AWS_SESSION_KEY_REDACTED"),
    (re.compile(r"\bghp_[A-Za-z0-9_]{20,}\b"), "GITHUB_TOKEN_REDACTED"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"), "GITHUB_TOKEN_REDACTED"),
    (
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
            re.DOTALL,
        ),
        "PRIVATE_KEY_REDACTED",
    ),
    (
        re.compile(
            r"(?i)\b(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*['\"]?[^'\"\s,]+"
        ),
        r"\1=REDACTED",
    ),
    (
        re.compile(r"(?i)\b(postgres(?:ql)?|mysql|mongodb|redis)://[^\s\"']+"),
        r"\1://CONNECTION_STRING_REDACTED",
    ),
)


def redact_text(value: str) -> str:
    redacted = value
    for pattern, replacement in SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Mapping):
        return {key: redact_value(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray | str):
        return [redact_value(item) for item in value]
    return value

