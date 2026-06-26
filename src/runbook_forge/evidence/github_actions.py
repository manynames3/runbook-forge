"""GitHub Actions fixture loading."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from runbook_forge.safety.redaction import redact_value


def load_actions_fixture(path: Path) -> dict[str, Any]:
    return redact_value(json.loads(path.read_text(encoding="utf-8")))


def fetch_actions_run(
    repo: str,
    run_id: str,
    token: str | None = None,
    api_base: str = "https://api.github.com",
) -> dict[str, Any]:
    """Fetch one GitHub Actions run through the read-only REST API."""

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "runbook-forge",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{api_base}/repos/{repo}/actions/runs/{run_id}", headers=headers)
    try:
        with urlopen(request, timeout=20) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub Actions read failed: {exc.code} {detail}") from exc
    return redact_value(_normalize_actions_run(payload))


def _normalize_actions_run(payload: dict[str, Any]) -> dict[str, Any]:
    head_commit = payload.get("head_commit", {})
    if not isinstance(head_commit, dict):
        head_commit = {}
    return {
        "workflow": payload.get("name") or payload.get("workflow_id"),
        "run_id": str(payload.get("id", "")),
        "commit_sha": payload.get("head_sha") or head_commit.get("id"),
        "status": payload.get("status"),
        "conclusion": payload.get("conclusion"),
        "html_url": payload.get("html_url"),
        "created_at": payload.get("created_at"),
        "updated_at": payload.get("updated_at"),
        "failed_step": "see GitHub Actions job logs",
        "failure_message": _failure_message(payload),
    }


def _failure_message(payload: dict[str, Any]) -> str:
    conclusion = payload.get("conclusion") or "unknown"
    status = payload.get("status") or "unknown"
    return f"GitHub Actions run status={status}, conclusion={conclusion}."
