"""Generate reusable Markdown runbook skills from triage reports."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path

from runbook_forge.safety.redaction import redact_text


@dataclass(frozen=True)
class SkillWriteResult:
    output_path: Path
    changed: bool
    diff_path: Path | None = None


def generate_skill_from_report(
    report_path: Path, output_path: Path, diff_path: Path | None = None
) -> SkillWriteResult:
    report_text = report_path.read_text(encoding="utf-8")
    fields = _extract_report_fields(report_text)
    body = render_skill(fields)
    previous = output_path.read_text(encoding="utf-8") if output_path.exists() else None
    changed = previous != body
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(redact_text(body), encoding="utf-8")
    written_diff_path = _write_diff(previous, body, output_path, diff_path)
    return SkillWriteResult(output_path=output_path, changed=changed, diff_path=written_diff_path)


def render_skill(fields: dict[str, str]) -> str:
    skill_name = fields.get("skill_name") or _slug_to_title(
        fields.get("related_skill", "incident_triage")
    )
    affected = fields.get("affected_system", "affected service")
    root_cause = fields.get("likely_root_cause", "unknown recurring failure pattern")
    severity = fields.get("severity", "unknown")
    return f"""# {skill_name}

## Skill name
{skill_name}

## When to use
Use this skill when Runbook Forge sees recurring `{root_cause}` signals for
`{affected}` or a similar service.

## Inputs needed
- Latest CI/CD failure output.
- Service events and health status.
- Relevant logs, metrics, and deployment metadata.
- Current rollback target or last known-good release.

## Investigation steps
1. Confirm the affected system and deployment window.
2. Re-run read-only checks for service state, health checks, queue state, or Terraform plan details.
3. Compare new evidence with the prior fingerprint `{fields.get("fingerprint", "unknown")}`.
4. Identify whether this is the same failure mode or a nearby symptom.
5. Prepare proposed remediation text for human review.

## Evidence to collect
- Report severity: `{severity}`.
- Affected system: `{affected}`.
- Likely root cause: `{root_cause}`.
- Current evidence snippets from logs, CI, AWS read-only APIs, and repository docs.

## Risk signals
- Repeated fingerprint count greater than one.
- Production service health degradation or deployment instability.
- Public exposure, broad IAM scope, destructive infrastructure changes, or message backlog growth.

## Safe remediation options
- Prefer rollback to a known-good artifact when user impact is active.
- Prefer narrowing or reverting risky infrastructure diffs before apply.
- Prefer scaling or timeout changes only after reviewing traffic, retries, and downstream limits.

## Commands to propose, not execute
```bash
# Read-only examples
aws ecs describe-services --cluster <cluster> --services <service>
aws lambda get-function-configuration --function-name <function>
aws sqs get-queue-attributes --queue-url <queue-url> --attribute-names All

# Write examples must remain proposals until a human approves them
aws ecs update-service --cluster <cluster> --service <service> --task-definition <previous-task-def>
aws lambda update-event-source-mapping --uuid <uuid> --batch-size <value>
terraform apply plan.out
```

## Approval requirements
Runbook Forge must not execute write actions. Any command that changes AWS,
Terraform state, deployment state, scaling, IAM, networking, or data retention
requires explicit human approval.

## Rollback notes
- Capture the current state before proposing changes.
- Identify the last known-good task definition, Lambda configuration, Terraform
  state, or queue redrive settings.
- Include blast radius, expected impact, and verification steps in the approval request.

## Example output
Runbook Forge should produce a concise triage report with severity `{severity}`,
affected system `{affected}`, likely root cause `{root_cause}`, evidence,
proposed commands, and an approval checklist.
"""


def _extract_report_fields(report_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    fields["severity"] = _section_value(report_text, "Severity")
    fields["affected_system"] = _section_value(report_text, "Affected system")
    fields["likely_root_cause"] = _section_value(report_text, "Likely root cause")
    related_section = _section_value(report_text, "Related or newly proposed runbook skill")
    skill_match = re.search(r"`([^`]+)`", related_section)
    if skill_match:
        fields["related_skill"] = skill_match.group(1)
        fields["skill_name"] = _slug_to_title(skill_match.group(1))
    fingerprint_match = re.search(r"Pattern fingerprint: `([^`]+)`", report_text)
    if fingerprint_match:
        fields["fingerprint"] = fingerprint_match.group(1)
    return fields


def _section_value(report_text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=\n## |\Z)",
        re.DOTALL | re.MULTILINE,
    )
    match = pattern.search(report_text)
    if not match:
        return ""
    body = match.group("body").strip()
    return body.splitlines()[0].strip() if body else ""


def _slug_to_title(value: str) -> str:
    words = re.sub(r"[^a-zA-Z0-9]+", " ", value).strip().split()
    return " ".join(word.capitalize() for word in words) + " Skill"


def _write_diff(
    previous: str | None, current: str, output_path: Path, diff_path: Path | None
) -> Path | None:
    if previous is None or previous == current:
        return None
    target = diff_path or output_path.with_suffix(output_path.suffix + ".diff")
    target.parent.mkdir(parents=True, exist_ok=True)
    diff = unified_diff(
        previous.splitlines(keepends=True),
        current.splitlines(keepends=True),
        fromfile=f"{output_path.name}:previous",
        tofile=f"{output_path.name}:proposed",
    )
    target.write_text("".join(diff), encoding="utf-8")
    return target
