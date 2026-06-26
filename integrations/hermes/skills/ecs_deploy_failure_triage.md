# ECS Deployment Failure Triage Skill

## Skill name
ECS Deployment Failure Triage Skill

## When to use
Use this skill when an ECS service fails to reach steady state during CI/CD deployment.

## Inputs needed
- GitHub Actions or CI job failure output.
- ECS service events and task stop reasons.
- Target group health.
- Container logs.
- Current and previous task definitions.

## Investigation steps
1. Confirm cluster, service, deployment ID, and desired count.
2. Inspect service events for health check, image pull, placement, or capacity failures.
3. Inspect target group health and health check path.
4. Inspect stopped tasks and container exit codes.
5. Prepare rollback guidance to the last known-good task definition.

## Evidence to collect
- Failed CI step and deployment window.
- ECS event messages.
- Target health reason codes.
- Container logs around startup and health probe failures.

## Risk signals
- Failed load balancer health checks.
- Image tag mismatch between CI artifact and task definition.
- Task role access denied errors.
- Container exit codes or repeated restarts.
- Capacity provider or subnet placement failures.

## Safe remediation options
- Propose rollback to a previous task definition.
- Propose fixing the health check path, port, or startup dependency.
- Propose capacity or placement changes after confirming limits.

## Commands to propose, not execute
```bash
aws ecs describe-services --cluster <cluster> --services <service>
aws elbv2 describe-target-health --target-group-arn <target-group-arn>
aws ecs update-service --cluster <cluster> --service <service> --task-definition <previous-task-def>
```

## Approval requirements
Do not execute service updates, forced deployments, task definition changes, or capacity changes without explicit human approval.

## Rollback notes
Identify the last known-good task definition and verify target health after rollback.

## Example output
A triage report with likely root cause, ECS evidence, rollback guidance, and approval note.
