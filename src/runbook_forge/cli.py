"""Typer CLI for Runbook Forge."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from runbook_forge.analysis.classifier import (
    classify_ecs_deploy,
    classify_sqs_lambda,
    classify_terraform_plan,
)
from runbook_forge.analysis.pattern_memory import PatternMemory
from runbook_forge.analysis.report_writer import write_report
from runbook_forge.analysis.skill_generator import generate_skill_from_report
from runbook_forge.models import AnalysisReport
from runbook_forge.safety.audit_log import AuditLogger

app = typer.Typer(help="Runbook Forge: recommend-only CloudOps triage and runbook generation.")
analyze_app = typer.Typer(help="Analyze fixture-backed CloudOps evidence.")
app.add_typer(analyze_app, name="analyze")

InputPath = Annotated[Path, typer.Option("--input", exists=True, readable=True)]
OutputPath = Annotated[Path, typer.Option("--output")]
MemoryPath = Annotated[Path, typer.Option("--memory")]
ReportPath = Annotated[Path, typer.Option("--from-report", exists=True, readable=True)]
AuditLogPath = Annotated[Path, typer.Option("--audit-log")]
DEFAULT_MEMORY = Path(".runbook_forge/patterns.json")
DEFAULT_AUDIT_LOG = Path(".runbook_forge/audit.log")


@analyze_app.command("terraform-plan")
def analyze_terraform_plan(
    input: InputPath,
    output: OutputPath,
    memory: MemoryPath = DEFAULT_MEMORY,
) -> None:
    """Analyze Terraform plan JSON for public exposure, IAM, destructive, and cost risks."""

    _run_analysis(classify_terraform_plan, input, output, memory)


@analyze_app.command("ecs-deploy")
def analyze_ecs_deploy(
    input: InputPath,
    output: OutputPath,
    memory: MemoryPath = DEFAULT_MEMORY,
) -> None:
    """Analyze ECS deployment failure fixture evidence."""

    _run_analysis(classify_ecs_deploy, input, output, memory)


@analyze_app.command("sqs-lambda")
def analyze_sqs_lambda(
    input: InputPath,
    output: OutputPath,
    memory: MemoryPath = DEFAULT_MEMORY,
) -> None:
    """Analyze SQS/Lambda backlog fixture evidence."""

    _run_analysis(classify_sqs_lambda, input, output, memory)


@app.command("propose-skill")
def propose_skill(
    from_report: ReportPath,
    output: OutputPath,
    audit_log: AuditLogPath = DEFAULT_AUDIT_LOG,
) -> None:
    """Generate a reusable Markdown runbook skill from a report."""

    generate_skill_from_report(from_report, output)
    AuditLogger(audit_log).log_event(
        "skill_proposed",
        {"from_report": str(from_report), "output": str(output), "mode": "propose_only"},
    )
    typer.echo(f"Wrote proposed runbook skill to {output}")


@app.command()
def demo() -> None:
    """Run the local demo with fake fixtures and generate reports plus a proposed skill."""

    root = _project_root()
    memory = root / ".runbook_forge" / "patterns.json"
    reports = root / "reports"
    runbooks = root / "runbooks"
    terraform_report = reports / "terraform-review.md"
    ecs_report = reports / "ecs-triage.md"
    sqs_report = reports / "sqs-lambda-triage.md"
    _run_analysis(
        classify_terraform_plan,
        root / "fixtures/terraform/plan_public_s3.json",
        terraform_report,
        memory,
    )
    _run_analysis(
        classify_ecs_deploy,
        root / "fixtures/aws/ecs_failed_deploy.json",
        ecs_report,
        memory,
    )
    # Replay the same fixture once so the demo visibly exercises recurrence detection.
    _run_analysis(
        classify_ecs_deploy,
        root / "fixtures/aws/ecs_failed_deploy.json",
        ecs_report,
        memory,
    )
    _run_analysis(
        classify_sqs_lambda,
        root / "fixtures/aws/sqs_lambda_backlog.json",
        sqs_report,
        memory,
    )
    skill_path = runbooks / "ecs_deploy_failure_triage.md"
    generate_skill_from_report(ecs_report, skill_path)
    AuditLogger(root / ".runbook_forge/audit.log").log_event(
        "demo_completed",
        {
            "reports": [str(terraform_report), str(ecs_report), str(sqs_report)],
            "proposed_skill": str(skill_path),
        },
    )
    typer.echo("Demo complete.")
    typer.echo(f"- {terraform_report}")
    typer.echo(f"- {ecs_report}")
    typer.echo(f"- {sqs_report}")
    typer.echo(f"- {skill_path}")


def _run_analysis(
    classifier: Callable[[Path], AnalysisReport],
    input_path: Path,
    output_path: Path,
    memory_path: Path,
) -> AnalysisReport:
    report = classifier(input_path)
    memory = PatternMemory(memory_path)
    record = memory.record(report.report_type, report.likely_root_cause, report.affected_system)
    report.pattern_fingerprint = record.fingerprint
    report.pattern_seen_count = record.count
    report.proposed_skill = memory.should_propose_skill(record)
    write_report(report, output_path)
    AuditLogger(memory_path.parent / "audit.log").log_event(
        "report_generated",
        {
            "report_type": report.report_type,
            "input": str(input_path),
            "output": str(output_path),
            "fingerprint": record.fingerprint,
            "count": record.count,
            "proposed_skill": report.proposed_skill,
        },
    )
    typer.echo(f"Wrote {report.report_type} report to {output_path}")
    return report


def _project_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "fixtures").exists():
        return cwd
    for parent in Path(__file__).resolve().parents:
        if (parent / "fixtures").exists():
            return parent
    return cwd


def main() -> None:
    app()


if __name__ == "__main__":
    main()
