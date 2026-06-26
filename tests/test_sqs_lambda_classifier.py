from pathlib import Path

from runbook_forge.analysis.classifier import classify_sqs_lambda
from runbook_forge.models import Severity

ROOT = Path(__file__).resolve().parents[1]


def test_sqs_lambda_classifier_identifies_backlog_pressure() -> None:
    report = classify_sqs_lambda(ROOT / "fixtures/aws/sqs_lambda_backlog.json")

    assert report.severity == Severity.CRITICAL
    assert report.likely_root_cause == "Lambda throttling and timeout pressure"
    assert "payments-events" in report.affected_system
    assert any("dlq" in item.detail.lower() for item in report.evidence_reviewed)
