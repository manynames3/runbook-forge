from pathlib import Path

from runbook_forge.analysis.classifier import classify_terraform_plan
from runbook_forge.models import Severity

ROOT = Path(__file__).resolve().parents[1]


def test_terraform_risk_detection_finds_requested_patterns() -> None:
    report = classify_terraform_plan(ROOT / "fixtures/terraform/plan_public_s3.json")

    finding_ids = {finding.id for finding in report.findings}

    assert report.severity == Severity.CRITICAL
    assert "tf-s3-public-access-block-disabled" in finding_ids
    assert "tf-s3-public-policy" in finding_ids
    assert "tf-sg-world-ingress" in finding_ids
    assert "tf-iam-wildcard" in finding_ids
    assert "tf-rds-destructive-change" in finding_ids
    assert "tf-nat-gateway-cost" in finding_ids
