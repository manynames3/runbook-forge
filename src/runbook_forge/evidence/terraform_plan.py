"""Terraform plan JSON parsing and high-risk change detection helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runbook_forge.models import ApprovalGate, EvidenceItem, RiskFinding, Severity
from runbook_forge.safety.approval_gate import gate_for_write
from runbook_forge.safety.redaction import redact_value


def load_plan(path: Path) -> dict[str, Any]:
    return redact_value(json.loads(path.read_text(encoding="utf-8")))


def resource_changes(plan: dict[str, Any]) -> list[dict[str, Any]]:
    changes = plan.get("resource_changes", [])
    return changes if isinstance(changes, list) else []


def detect_terraform_findings(plan: dict[str, Any]) -> list[RiskFinding]:
    findings: list[RiskFinding] = []
    for change in resource_changes(plan):
        resource_type = str(change.get("type", ""))
        address = str(change.get("address", "unknown"))
        change_body = change.get("change", {})
        after = change_body.get("after", {}) if isinstance(change_body, dict) else {}
        before = change_body.get("before", {}) if isinstance(change_body, dict) else {}
        actions = change_body.get("actions", []) if isinstance(change_body, dict) else []
        if not isinstance(after, dict):
            after = {}
        if not isinstance(before, dict):
            before = {}
        if not isinstance(actions, list):
            actions = []

        findings.extend(_detect_s3_public_exposure(resource_type, address, after))
        findings.extend(_detect_security_group_world_ingress(resource_type, address, after))
        findings.extend(_detect_iam_wildcards(resource_type, address, after))
        findings.extend(_detect_rds_destructive(resource_type, address, before, actions))
        findings.extend(_detect_nat_gateway_cost(resource_type, address, actions))
    return findings


def _finding(
    finding_id: str,
    title: str,
    severity: Severity,
    affected_resource: str,
    detail: str,
    blast_radius: str,
    recommendation: str,
    approval: ApprovalGate | None = None,
) -> RiskFinding:
    return RiskFinding(
        id=finding_id,
        title=title,
        severity=severity,
        affected_resource=affected_resource,
        evidence=[
            EvidenceItem(
                source="terraform_plan",
                detail=detail,
                locator=affected_resource,
            )
        ],
        blast_radius=blast_radius,
        recommendation=recommendation,
        approval=approval
        or gate_for_write("Terraform apply can change cloud infrastructure and requires review."),
    )


def _detect_s3_public_exposure(
    resource_type: str, address: str, after: dict[str, Any]
) -> list[RiskFinding]:
    findings: list[RiskFinding] = []
    if resource_type == "aws_s3_bucket_public_access_block":
        public_keys = [
            "block_public_acls",
            "block_public_policy",
            "ignore_public_acls",
            "restrict_public_buckets",
        ]
        disabled = [key for key in public_keys if after.get(key) is False]
        if disabled:
            findings.append(
                _finding(
                    "tf-s3-public-access-block-disabled",
                    "S3 public access protections are disabled",
                    Severity.HIGH,
                    address,
                    f"Public access block fields disabled: {', '.join(disabled)}.",
                    (
                        "Objects in the bucket could become publicly readable if paired "
                        "with permissive ACLs or policies."
                    ),
                    (
                        "Keep all public access block controls enabled unless a "
                        "documented exception is approved."
                    ),
                )
            )
    if resource_type == "aws_s3_bucket_acl" and str(after.get("acl", "")).startswith("public"):
        findings.append(
            _finding(
                "tf-s3-public-acl",
                "S3 bucket ACL grants public access",
                Severity.HIGH,
                address,
                f"Bucket ACL is set to {after.get('acl')}.",
                "Bucket data may be exposed to anonymous internet users.",
                "Replace public ACLs with private ACLs and scoped IAM or bucket policies.",
            )
        )
    if resource_type == "aws_s3_bucket_policy":
        policy = _parse_policy(after.get("policy"))
        if _policy_has_public_principal(policy):
            findings.append(
                _finding(
                    "tf-s3-public-policy",
                    "S3 bucket policy allows public principal",
                    Severity.CRITICAL,
                    address,
                    "Bucket policy contains an Allow statement for principal '*'.",
                    "Anonymous users may gain bucket or object access depending on policy actions.",
                    (
                        "Remove public principals or require a reviewed exception with "
                        "explicit business justification."
                    ),
                )
            )
    return findings


def _detect_security_group_world_ingress(
    resource_type: str, address: str, after: dict[str, Any]
) -> list[RiskFinding]:
    findings: list[RiskFinding] = []
    ingress_rules: list[dict[str, Any]] = []
    if resource_type == "aws_security_group":
        raw_ingress = after.get("ingress", [])
        if isinstance(raw_ingress, list):
            ingress_rules = [rule for rule in raw_ingress if isinstance(rule, dict)]
    elif resource_type in {"aws_security_group_rule", "aws_vpc_security_group_ingress_rule"}:
        is_ingress = after.get("type") == "ingress" or resource_type.endswith("_ingress_rule")
        if is_ingress:
            ingress_rules = [after]

    for rule in ingress_rules:
        cidrs = _extract_cidrs(rule)
        if "0.0.0.0/0" in cidrs or "::/0" in cidrs:
            from_port = rule.get("from_port", rule.get("from_port", "all"))
            to_port = rule.get("to_port", rule.get("to_port", "all"))
            severity = Severity.CRITICAL if from_port in {22, 3389} else Severity.HIGH
            findings.append(
                _finding(
                    "tf-sg-world-ingress",
                    "Security group ingress is open to the internet",
                    severity,
                    address,
                    f"Ingress allows {cidrs} on ports {from_port}-{to_port}.",
                    "Internet-origin traffic can reach the attached workload on the allowed ports.",
                    (
                        "Restrict ingress to known CIDR ranges, load balancer security "
                        "groups, or private networking."
                    ),
                )
            )
    return findings


def _detect_iam_wildcards(
    resource_type: str, address: str, after: dict[str, Any]
) -> list[RiskFinding]:
    if "iam" not in resource_type:
        return []
    policy = _parse_policy(after.get("policy") or after.get("assume_role_policy"))
    if not policy:
        return []
    wildcard_actions, wildcard_resources = _policy_has_wildcards(policy)
    if not wildcard_actions and not wildcard_resources:
        return []
    parts = []
    if wildcard_actions:
        parts.append("wildcard actions")
    if wildcard_resources:
        parts.append("wildcard resources")
    return [
        _finding(
            "tf-iam-wildcard",
            "IAM policy uses wildcard permissions",
            Severity.HIGH,
            address,
            f"Policy contains {' and '.join(parts)}.",
            "A compromised principal may gain broad access beyond the intended workload boundary.",
            "Replace wildcards with least-privilege actions and scoped resources.",
        )
    ]


def _detect_rds_destructive(
    resource_type: str, address: str, before: dict[str, Any], actions: list[Any]
) -> list[RiskFinding]:
    if resource_type not in {"aws_db_instance", "aws_rds_cluster"}:
        return []
    if "delete" not in actions:
        return []
    replacement = "create" in actions
    database_id = before.get("identifier") or before.get("cluster_identifier") or address
    return [
        _finding(
            "tf-rds-destructive-change",
            "RDS database has a destructive plan action",
            Severity.CRITICAL,
            address,
            f"Plan actions are {actions}; target database is {database_id}.",
            "Database replacement or deletion can cause data loss, downtime, and restore work.",
            (
                "Require backup verification, maintenance window approval, and "
                "rollback plan before apply."
                if replacement
                else "Require explicit deletion approval and backup validation before apply."
            ),
        )
    ]


def _detect_nat_gateway_cost(
    resource_type: str, address: str, actions: list[Any]
) -> list[RiskFinding]:
    if resource_type != "aws_nat_gateway" or "create" not in actions:
        return []
    return [
        _finding(
            "tf-nat-gateway-cost",
            "NAT Gateway creation can increase recurring cost",
            Severity.MEDIUM,
            address,
            "Plan creates an AWS NAT Gateway.",
            (
                "Hourly NAT Gateway charges and data processing charges can materially "
                "affect monthly spend."
            ),
            "Confirm expected egress volume and whether private endpoints are a better fit.",
        )
    ]


def _extract_cidrs(rule: dict[str, Any]) -> list[str]:
    cidrs: list[str] = []
    for key in ("cidr_blocks", "ipv6_cidr_blocks"):
        value = rule.get(key, [])
        if isinstance(value, list):
            cidrs.extend(str(item) for item in value)
    for key in ("cidr_ipv4", "cidr_ipv6"):
        value = rule.get(key)
        if value:
            cidrs.append(str(value))
    return cidrs


def _parse_policy(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _statements(policy: dict[str, Any]) -> list[dict[str, Any]]:
    statements = policy.get("Statement", [])
    if isinstance(statements, dict):
        return [statements]
    if isinstance(statements, list):
        return [statement for statement in statements if isinstance(statement, dict)]
    return []


def _policy_has_public_principal(policy: dict[str, Any]) -> bool:
    for statement in _statements(policy):
        if statement.get("Effect") != "Allow":
            continue
        principal = statement.get("Principal")
        if principal == "*":
            return True
        if isinstance(principal, dict) and principal.get("AWS") == "*":
            return True
    return False


def _policy_has_wildcards(policy: dict[str, Any]) -> tuple[bool, bool]:
    wildcard_actions = False
    wildcard_resources = False
    for statement in _statements(policy):
        actions = _as_list(statement.get("Action"))
        resources = _as_list(statement.get("Resource"))
        wildcard_actions = wildcard_actions or any(_contains_wildcard(item) for item in actions)
        wildcard_resources = wildcard_resources or any(item == "*" for item in resources)
    return wildcard_actions, wildcard_resources


def _as_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _contains_wildcard(value: str) -> bool:
    return value == "*" or value.endswith(":*") or "*" in value
