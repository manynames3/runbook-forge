"""Incident classifiers for Terraform, ECS deployments, and SQS/Lambda backlogs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runbook_forge.analysis.pattern_memory import fingerprint_for
from runbook_forge.analysis.risk_engine import max_severity
from runbook_forge.evidence.aws_ecs import load_ecs_fixture
from runbook_forge.evidence.aws_sqs_lambda import load_sqs_lambda_fixture
from runbook_forge.evidence.terraform_plan import (
    detect_terraform_findings,
    load_plan,
    resource_changes,
)
from runbook_forge.models import AnalysisReport, EvidenceItem, RecommendedAction, Severity
from runbook_forge.safety.approval_gate import (
    approval_required_action,
    propose_only_action,
    read_only_action,
)


def classify_terraform_plan(path: Path) -> AnalysisReport:
    plan = load_plan(path)
    findings = detect_terraform_findings(plan)
    severity = max_severity([finding.severity for finding in findings], default=Severity.LOW)
    likely_root_cause = (
        "Terraform plan introduces high-risk infrastructure changes"
        if findings
        else "No high-risk Terraform pattern detected"
    )
    affected_system = "terraform-plan"
    evidence = [
        EvidenceItem(
            source="terraform_plan",
            detail=f"Reviewed {len(resource_changes(plan))} planned resource changes from {path}.",
            locator=str(path),
        )
    ]
    action_list: list[RecommendedAction] = [
        read_only_action(
            "Review plan JSON",
            (
                "Inspect the generated plan and confirm all risky resources have owners "
                "and rollback notes."
            ),
            "terraform show -json plan.out > plan.json",
        ),
        approval_required_action(
            "Block apply until risk owner approves",
            (
                "Do not apply this plan until public access, IAM, database, and cost "
                "findings are accepted or fixed."
            ),
            "terraform apply plan.out",
        ),
    ]
    summary = (
        f"Runbook Forge found {len(findings)} risk signal(s) in the Terraform plan."
        if findings
        else "Runbook Forge did not find configured high-risk Terraform patterns."
    )
    report = AnalysisReport.with_timestamp(
        report_type="terraform-plan",
        severity=severity,
        affected_system=affected_system,
        executive_summary=summary,
        evidence_reviewed=evidence,
        likely_root_cause=likely_root_cause,
        risk_blast_radius=_blast_radius_for_findings(findings),
        findings=findings,
        recommended_actions=action_list,
        related_runbook_skill="terraform_plan_review",
        pattern_fingerprint=fingerprint_for("terraform-plan", likely_root_cause, affected_system),
    )
    return report


def classify_ecs_deploy(path: Path) -> AnalysisReport:
    data = load_ecs_fixture(path)
    service = str(data.get("service", "unknown-service"))
    cluster = str(data.get("cluster", "unknown-cluster"))
    affected_system = f"{cluster}/{service}"
    signals = _ecs_signals(data)
    likely_root_cause = _best_ecs_cause(signals)
    severity = (
        Severity.HIGH
        if likely_root_cause != "No dominant ECS deployment failure signal"
        else Severity.LOW
    )
    evidence = _ecs_evidence(data, signals, path)
    actions = [
        read_only_action(
            "Describe ECS service",
            "Confirm deployment rollout state, recent events, desired count, and running count.",
            f"aws ecs describe-services --cluster {cluster} --services {service}",
        ),
        read_only_action(
            "Inspect target health",
            (
                "Check load balancer target health before changing task definitions "
                "or deployment settings."
            ),
            "aws elbv2 describe-target-health --target-group-arn <target-group-arn>",
        ),
        propose_only_action(
            "Prepare rollback plan",
            (
                "Draft a rollback to the last known-good task definition, but do not "
                "execute it automatically."
            ),
            (
                f"aws ecs update-service --cluster {cluster} --service {service} "
                "--task-definition <previous-task-def>"
            ),
        ),
        approval_required_action(
            "Execute rollback only after approval",
            (
                "Changing the ECS service task definition is a write action and must "
                "be manually approved."
            ),
            (
                f"aws ecs update-service --cluster {cluster} --service {service} "
                "--force-new-deployment"
            ),
        ),
    ]
    summary = (
        f"ECS deployment for {service} is not stable. Most likely cause: {likely_root_cause}."
    )
    return AnalysisReport.with_timestamp(
        report_type="ecs-deploy",
        severity=severity,
        affected_system=affected_system,
        executive_summary=summary,
        evidence_reviewed=evidence,
        likely_root_cause=likely_root_cause,
        risk_blast_radius=(
            "User traffic may be routed to unhealthy tasks or capacity may remain "
            "below desired count."
        ),
        findings=[],
        recommended_actions=actions,
        related_runbook_skill="ecs_deploy_failure_triage",
        pattern_fingerprint=fingerprint_for("ecs-deploy", likely_root_cause, affected_system),
    )


def classify_sqs_lambda(path: Path) -> AnalysisReport:
    data = load_sqs_lambda_fixture(path)
    queue_name = str(data.get("queue_name", "unknown-queue"))
    lambda_name = str(data.get("lambda_name", "unknown-lambda"))
    affected_system = f"{queue_name} -> {lambda_name}"
    signals = _sqs_lambda_signals(data)
    likely_root_cause = _best_sqs_lambda_cause(signals)
    severity = _sqs_lambda_severity(data, signals)
    evidence = _sqs_lambda_evidence(data, signals, path)
    actions = [
        read_only_action(
            "Inspect queue attributes",
            "Confirm approximate queue depth, oldest message age, and DLQ pressure.",
            f"aws sqs get-queue-attributes --queue-url <{queue_name}-url> --attribute-names All",
        ),
        read_only_action(
            "Inspect Lambda concurrency and errors",
            "Review concurrency, throttles, errors, and timeout metrics before proposing changes.",
            f"aws lambda get-function-configuration --function-name {lambda_name}",
        ),
        propose_only_action(
            "Propose concurrency adjustment",
            "Prepare a concurrency or event-source mapping change only as text for human review.",
            (
                f"aws lambda put-function-concurrency --function-name {lambda_name} "
                "--reserved-concurrent-executions <value>"
            ),
        ),
        approval_required_action(
            "Apply Lambda or queue changes only after approval",
            "Concurrency, timeout, redrive, and batch-size changes can change production behavior.",
            "aws lambda update-event-source-mapping --uuid <uuid> --batch-size <value>",
        ),
    ]
    return AnalysisReport.with_timestamp(
        report_type="sqs-lambda",
        severity=severity,
        affected_system=affected_system,
        executive_summary=(
            f"SQS/Lambda pipeline has backlog pressure. Suspected bottleneck: {likely_root_cause}."
        ),
        evidence_reviewed=evidence,
        likely_root_cause=likely_root_cause,
        risk_blast_radius=(
            "Message processing delay can breach freshness SLOs and increase duplicate "
            "processing or DLQ volume."
        ),
        findings=[],
        recommended_actions=actions,
        related_runbook_skill="sqs_lambda_backlog_triage",
        pattern_fingerprint=fingerprint_for("sqs-lambda", likely_root_cause, affected_system),
    )


def _blast_radius_for_findings(findings: list[Any]) -> str:
    if not findings:
        return "No configured high-risk blast radius detected in this fixture."
    return " ".join(finding.blast_radius for finding in findings[:3])


def _ecs_signals(data: dict[str, Any]) -> dict[str, list[str]]:
    signals: dict[str, list[str]] = {
        "image tag mismatch": [],
        "health check failure": [],
        "task role permission issue": [],
        "container crash": [],
        "insufficient capacity": [],
    }
    github = data.get("github_actions", {})
    if isinstance(github, dict):
        deployed_image = str(github.get("image", ""))
        expected_image = str(data.get("task_definition_image", ""))
        if deployed_image and expected_image and deployed_image != expected_image:
            signals["image tag mismatch"].append(
                f"GitHub Actions deployed {deployed_image}, task definition has {expected_image}."
            )
        if "image" in str(github.get("failure_message", "")).lower():
            signals["image tag mismatch"].append(str(github.get("failure_message")))

    for event in _string_list(data.get("ecs_service_events")):
        event_lower = event.lower()
        if "health check" in event_lower or "unhealthy" in event_lower:
            signals["health check failure"].append(event)
        if (
            "unable to place" in event_lower
            or "insufficient" in event_lower
            or "capacity" in event_lower
        ):
            signals["insufficient capacity"].append(event)

    for target in _dict_list(data.get("target_group_health")):
        reason = str(target.get("reason", ""))
        if str(target.get("status", "")).lower() == "unhealthy" or "health" in reason.lower():
            signals["health check failure"].append(
                f"Target {target.get('target')} is {target.get('status')}: {reason}"
            )

    all_logs = "\n".join(_string_list(data.get("container_logs"))).lower()
    if "accessdenied" in all_logs or "not authorized" in all_logs:
        signals["task role permission issue"].append(
            "Container logs include an authorization failure."
        )
    if "traceback" in all_logs or "panic" in all_logs or "exited" in all_logs:
        signals["container crash"].append("Container logs include crash-like output.")

    for task in _dict_list(data.get("tasks")):
        stopped_reason = str(task.get("stopped_reason", ""))
        if stopped_reason:
            signals["container crash"].append(stopped_reason)
        for container in _dict_list(task.get("containers")):
            exit_code = container.get("exit_code")
            if isinstance(exit_code, int) and exit_code != 0:
                signals["container crash"].append(
                    f"Container {container.get('name')} exited with code {exit_code}."
                )
    return {key: value for key, value in signals.items() if value}


def _best_ecs_cause(signals: dict[str, list[str]]) -> str:
    priority = [
        "image tag mismatch",
        "health check failure",
        "task role permission issue",
        "container crash",
        "insufficient capacity",
    ]
    for cause in priority:
        if signals.get(cause):
            return cause
    return "No dominant ECS deployment failure signal"


def _ecs_evidence(
    data: dict[str, Any], signals: dict[str, list[str]], path: Path
) -> list[EvidenceItem]:
    evidence = [
        EvidenceItem(source="ecs_fixture", detail=f"Loaded ECS deployment fixture from {path}.")
    ]
    github = data.get("github_actions", {})
    if isinstance(github, dict):
        evidence.append(
            EvidenceItem(
                source="github_actions",
                detail=(
                    f"Workflow {github.get('workflow')} run {github.get('run_id')} "
                    f"failed at {github.get('failed_step')}."
                ),
            )
        )
    for cause, details in signals.items():
        for detail in details[:3]:
            evidence.append(EvidenceItem(source="ecs_classifier", detail=f"{cause}: {detail}"))
    return evidence


def _sqs_lambda_signals(data: dict[str, Any]) -> dict[str, list[str]]:
    lambda_data = data.get("lambda", {})
    if not isinstance(lambda_data, dict):
        lambda_data = {}
    signals: dict[str, list[str]] = {
        "Lambda throttling": [],
        "timeout too low": [],
        "poison messages": [],
        "batch size/concurrency mismatch": [],
        "downstream dependency failures": [],
    }
    throttles = _int(lambda_data.get("throttles_5m"))
    if throttles > 0:
        signals["Lambda throttling"].append(
            f"Lambda had {throttles} throttles in the last 5 minutes."
        )
    reserved = _int(lambda_data.get("reserved_concurrency"))
    concurrent = _int(lambda_data.get("concurrent_executions"))
    if reserved and concurrent >= reserved:
        signals["Lambda throttling"].append(
            f"Concurrent executions {concurrent} are at reserved concurrency {reserved}."
        )
    p95 = _int(lambda_data.get("duration_p95_ms"))
    timeout = _int(lambda_data.get("timeout_ms"))
    timeouts = _int(lambda_data.get("timeouts_5m"))
    if timeouts > 0 or (timeout > 0 and p95 >= int(timeout * 0.8)):
        signals["timeout too low"].append(
            f"p95 duration {p95} ms, timeout {timeout} ms, timeouts in 5m {timeouts}."
        )
    dlq_count = _int(data.get("dlq_message_count"))
    if dlq_count > 0:
        signals["poison messages"].append(f"DLQ contains {dlq_count} messages.")
    queue_depth = _int(data.get("queue_depth"))
    batch_size = _int(lambda_data.get("batch_size"))
    if queue_depth > 1000 and reserved and batch_size and reserved * batch_size < 100:
        signals["batch size/concurrency mismatch"].append(
            f"Queue depth {queue_depth}, reserved concurrency {reserved}, batch size {batch_size}."
        )
    logs = "\n".join(_string_list(data.get("logs"))).lower()
    if "503" in logs or "connection refused" in logs or "dependency" in logs:
        signals["downstream dependency failures"].append(
            "Logs mention downstream 5xx or dependency failures."
        )
    return {key: value for key, value in signals.items() if value}


def _best_sqs_lambda_cause(signals: dict[str, list[str]]) -> str:
    if signals.get("Lambda throttling") and signals.get("timeout too low"):
        return "Lambda throttling and timeout pressure"
    for cause in [
        "poison messages",
        "Lambda throttling",
        "timeout too low",
        "downstream dependency failures",
        "batch size/concurrency mismatch",
    ]:
        if signals.get(cause):
            return cause
    return "No dominant SQS/Lambda backlog signal"


def _sqs_lambda_severity(data: dict[str, Any], signals: dict[str, list[str]]) -> Severity:
    age = _int(data.get("oldest_message_age_seconds"))
    dlq = _int(data.get("dlq_message_count"))
    if age >= 3600 or dlq >= 100:
        return Severity.CRITICAL
    if signals:
        return Severity.HIGH
    return Severity.LOW


def _sqs_lambda_evidence(
    data: dict[str, Any], signals: dict[str, list[str]], path: Path
) -> list[EvidenceItem]:
    evidence = [
        EvidenceItem(source="sqs_lambda_fixture", detail=f"Loaded SQS/Lambda fixture from {path}."),
        EvidenceItem(
            source="sqs",
            detail=(
                f"Queue depth {data.get('queue_depth')} and oldest message age "
                f"{data.get('oldest_message_age_seconds')} seconds."
            ),
        ),
    ]
    for cause, details in signals.items():
        for detail in details[:3]:
            evidence.append(
                EvidenceItem(source="sqs_lambda_classifier", detail=f"{cause}: {detail}")
            )
    return evidence


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _int(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0
