from pathlib import Path

from runbook_forge.analysis.classifier import classify_ecs_deploy
from runbook_forge.models import ActionMode, Severity

ROOT = Path(__file__).resolve().parents[1]


def test_ecs_classifier_identifies_health_check_failure() -> None:
    report = classify_ecs_deploy(ROOT / "fixtures/aws/ecs_failed_deploy.json")

    assert report.severity == Severity.HIGH
    assert report.likely_root_cause == "health check failure"
    assert report.affected_system == "prod-shared/checkout-api"
    assert any("health check" in item.detail.lower() for item in report.evidence_reviewed)
    assert any(
        action.mode == ActionMode.REQUIRES_HUMAN_APPROVAL
        for action in report.recommended_actions
    )
