# Ecs Deploy Failure Triage Skill

## Skill name
Ecs Deploy Failure Triage Skill

## When to use
Use this skill when Runbook Forge sees recurring `health check failure` signals for
`prod-shared/checkout-api` or a similar service.

## Inputs needed
- Latest CI/CD failure output.
- Service events and health status.
- Relevant logs, metrics, and deployment metadata.
- Current rollback target or last known-good release.

## Investigation steps
1. Confirm the affected system and deployment window.
2. Re-run read-only checks for service state, health checks, queue state, or Terraform plan details.
3. Compare new evidence with the prior fingerprint `ecs-deploy::health-check-failure::prod-shared-checkout-api`.
4. Identify whether this is the same failure mode or a nearby symptom.
5. Prepare proposed remediation text for human review.

## Evidence to collect
- Report severity: `high`.
- Affected system: `prod-shared/checkout-api`.
- Likely root cause: `health check failure`.
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
Runbook Forge should produce a concise triage report with severity `high`,
affected system `prod-shared/checkout-api`, likely root cause `health check failure`, evidence,
proposed commands, and an approval checklist.
