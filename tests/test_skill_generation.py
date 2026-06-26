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

    result = generate_skill_from_report(report_path, skill_path)

    generated = skill_path.read_text(encoding="utf-8")
    assert result.changed
    assert result.diff_path is None
    assert "# Ecs Deploy Failure Triage Skill" in generated
    assert "Commands to propose, not execute" in generated
    assert "must not execute write actions" in generated


def test_skill_generation_writes_update_diff(tmp_path) -> None:  # type: ignore[no-untyped-def]
    report = classify_ecs_deploy(ROOT / "fixtures/aws/ecs_failed_deploy.json")
    report_path = tmp_path / "ecs-report.md"
    skill_path = tmp_path / "ecs-skill.md"
    write_report(report, report_path)
    skill_path.write_text("# Old Skill\n\nManual draft.\n", encoding="utf-8")

    result = generate_skill_from_report(report_path, skill_path)

    assert result.changed
    assert result.diff_path == skill_path.with_suffix(".md.diff")
    assert result.diff_path.exists()
    diff_text = result.diff_path.read_text(encoding="utf-8")
    assert "--- ecs-skill.md:previous" in diff_text
    assert "+++ ecs-skill.md:proposed" in diff_text
