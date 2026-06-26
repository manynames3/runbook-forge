from pathlib import Path

from runbook_forge.analysis.classifier import classify_ecs_deploy
from runbook_forge.analysis.report_writer import write_report
from runbook_forge.analysis.skill_generator import generate_skill_from_report

ROOT = Path(__file__).resolve().parents[1]


def test_skill_generation_from_report(tmp_path) -> None:  # type: ignore[no-untyped-def]
    report = classify_ecs_deploy(ROOT / "fixtures/aws/ecs_failed_deploy.json")
    report_path = tmp_path / "ecs-report.md"
    skill_path = tmp_path / "ecs-skill.md"
    write_report(report, report_path)

    generate_skill_from_report(report_path, skill_path)

    generated = skill_path.read_text(encoding="utf-8")
    assert "# Ecs Deploy Failure Triage Skill" in generated
    assert "Commands to propose, not execute" in generated
    assert "must not execute write actions" in generated
