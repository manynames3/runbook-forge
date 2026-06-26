from pathlib import Path

from typer.testing import CliRunner

from runbook_forge.cli import app

ROOT = Path(__file__).resolve().parents[1]


def test_cli_analyze_terraform_plan_smoke(tmp_path) -> None:  # type: ignore[no-untyped-def]
    output = tmp_path / "terraform-review.md"
    memory = tmp_path / "patterns.json"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "analyze",
            "terraform-plan",
            "--input",
            str(ROOT / "fixtures/terraform/plan_public_s3.json"),
            "--output",
            str(output),
            "--memory",
            str(memory),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output.exists()
    assert "Terraform plan introduces high-risk infrastructure changes" in output.read_text(
        encoding="utf-8"
    )


def test_cli_propose_skill_smoke(tmp_path) -> None:  # type: ignore[no-untyped-def]
    report = tmp_path / "report.md"
    output = tmp_path / "skill.md"
    report.write_text(
        """# Runbook Forge Report: ecs-deploy

## Severity
high

## Affected system
prod-shared/checkout-api

## Likely root cause
health check failure

## Related or newly proposed runbook skill
Related skill: `ecs_deploy_failure_triage`.

## Audit metadata
- Pattern fingerprint: `ecs-deploy::health-check-failure::prod-shared-checkout-api`
""",
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "propose-skill",
            "--from-report",
            str(report),
            "--output",
            str(output),
            "--audit-log",
            str(tmp_path / "audit.log"),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output.exists()
    assert "Ecs Deploy Failure Triage Skill" in output.read_text(encoding="utf-8")


def test_cli_collect_requires_live_opt_in(tmp_path) -> None:  # type: ignore[no-untyped-def]
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "collect",
            "github-actions",
            "--repo",
            "manynames3/runbook-forge",
            "--run-id",
            "1",
            "--output",
            str(tmp_path / "actions.json"),
        ],
    )

    assert result.exit_code != 0
    assert "Live collection is opt-in" in result.output
