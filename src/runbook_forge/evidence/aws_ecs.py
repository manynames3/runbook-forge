"""ECS deployment evidence loaders with fixture-first and boto3-compatible interfaces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from runbook_forge.safety.redaction import redact_value


class ECSReadOnlyProvider(Protocol):
    def service_snapshot(self, cluster: str, service: str) -> dict[str, Any]:
        """Return read-only ECS service data for classification."""


class FixtureECSProvider:
    def __init__(self, fixture_path: Path) -> None:
        self.fixture_path = fixture_path

    def service_snapshot(self, cluster: str, service: str) -> dict[str, Any]:
        data = load_ecs_fixture(self.fixture_path)
        if data.get("cluster") != cluster or data.get("service") != service:
            data["fixture_warning"] = "Requested service did not match fixture metadata."
        return data


class Boto3ECSReadOnlyProvider:
    """Small adapter for future live read-only checks. Not used by tests or demo."""

    def __init__(self, region_name: str) -> None:
        import boto3  # type: ignore[import-not-found]

        self._ecs = boto3.client("ecs", region_name=region_name)

    def service_snapshot(self, cluster: str, service: str) -> dict[str, Any]:
        response = self._ecs.describe_services(cluster=cluster, services=[service])
        return redact_value(response)


def load_ecs_fixture(path: Path) -> dict[str, Any]:
    return redact_value(json.loads(path.read_text(encoding="utf-8")))

