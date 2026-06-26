"""SQS and Lambda backlog evidence loaders with no-write adapters."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from runbook_forge.safety.redaction import redact_value


class SQSLambdaReadOnlyProvider(Protocol):
    def backlog_snapshot(self, queue_name: str, lambda_name: str) -> dict[str, Any]:
        """Return read-only SQS and Lambda health data."""


class FixtureSQSLambdaProvider:
    def __init__(self, fixture_path: Path) -> None:
        self.fixture_path = fixture_path

    def backlog_snapshot(self, queue_name: str, lambda_name: str) -> dict[str, Any]:
        data = load_sqs_lambda_fixture(self.fixture_path)
        if data.get("queue_name") != queue_name or data.get("lambda_name") != lambda_name:
            data["fixture_warning"] = "Requested queue or Lambda did not match fixture metadata."
        return data


class Boto3SQSLambdaReadOnlyProvider:
    """Future adapter for read-only AWS calls. It intentionally exposes no write methods."""

    def __init__(self, region_name: str) -> None:
        import boto3  # type: ignore[import-not-found]

        self._sqs = boto3.client("sqs", region_name=region_name)
        self._lambda = boto3.client("lambda", region_name=region_name)

    def backlog_snapshot(self, queue_name: str, lambda_name: str) -> dict[str, Any]:
        queue_url = self._sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]
        attrs = self._sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=[
                "ApproximateNumberOfMessages",
                "ApproximateAgeOfOldestMessage",
            ],
        )
        function = self._lambda.get_function_configuration(FunctionName=lambda_name)
        return redact_value(_normalize_backlog_response(queue_name, lambda_name, attrs, function))


def load_sqs_lambda_fixture(path: Path) -> dict[str, Any]:
    return redact_value(json.loads(path.read_text(encoding="utf-8")))


def _normalize_backlog_response(
    queue_name: str,
    lambda_name: str,
    queue_attributes: dict[str, Any],
    lambda_configuration: dict[str, Any],
) -> dict[str, Any]:
    attrs = queue_attributes.get("Attributes", {})
    if not isinstance(attrs, dict):
        attrs = {}
    timeout_seconds = _int(lambda_configuration.get("Timeout"))
    return {
        "queue_name": queue_name,
        "lambda_name": lambda_name,
        "queue_depth": _int(attrs.get("ApproximateNumberOfMessages")),
        "oldest_message_age_seconds": _int(attrs.get("ApproximateAgeOfOldestMessage")),
        "dlq_message_count": 0,
        "lambda": {
            "errors_5m": 0,
            "throttles_5m": 0,
            "timeouts_5m": 0,
            "duration_p95_ms": 0,
            "timeout_ms": timeout_seconds * 1000,
            "reserved_concurrency": 0,
            "concurrent_executions": 0,
            "batch_size": 0,
        },
        "logs": [],
    }


def _int(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0
