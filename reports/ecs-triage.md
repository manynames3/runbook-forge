# Runbook Forge Report: ecs-deploy

## Executive summary
ECS deployment for checkout-api is not stable. Most likely cause: health check failure.

## Severity
high

## Affected system
prod-shared/checkout-api

## Evidence reviewed
- `ecs_fixture`: Loaded ECS deployment fixture from /Users/aiden/Documents/Codex/2026-06-26/files-mentioned-by-the-user-build/outputs/runbook-forge/fixtures/aws/ecs_failed_deploy.json.
- `github_actions`: Workflow deploy.yml run 884221 failed at wait-for-service-stability.
- `ecs_classifier`: health check failure: service checkout-api deregistered 2 targets in target-group checkout-blue because they failed ELB health checks.
- `ecs_classifier`: health check failure: Target 10.0.42.19:8080 is unhealthy: Health checks failed with code 503
- `ecs_classifier`: health check failure: Target 10.0.43.87:8080 is unhealthy: Health checks failed with code 503
- `ecs_classifier`: container crash: Container logs include crash-like output.
- `ecs_classifier`: container crash: Essential container in task exited
- `ecs_classifier`: container crash: Container app exited with code 1.

## Likely root cause
health check failure

## Risk / blast radius
User traffic may be routed to unhealthy tasks or capacity may remain below desired count.

## Findings
- No structured risk findings were generated for this report type.

## Recommended next actions
1. Describe ECS service (`read_only`): Confirm deployment rollout state, recent events, desired count, and running count.
   Proposed command: `aws ecs describe-services --cluster prod-shared --services checkout-api`
2. Inspect target health (`read_only`): Check load balancer target health before changing task definitions or deployment settings.
   Proposed command: `aws elbv2 describe-target-health --target-group-arn <target-group-arn>`
3. Prepare rollback plan (`propose_only`): Draft a rollback to the last known-good task definition, but do not execute it automatically.
   Proposed command: `aws ecs update-service --cluster prod-shared --service checkout-api --task-definition <previous-task-def>`
4. Execute rollback only after approval (`requires_human_approval`): Changing the ECS service task definition is a write action and must be manually approved.
   Proposed command: `aws ecs update-service --cluster prod-shared --service checkout-api --force-new-deployment`

## Human approval required before write actions
Yes. The following actions are recommend-only and must be manually approved: Execute rollback only after approval

## Related or newly proposed runbook skill
Pattern recurrence threshold met. Create or update reusable runbook skill `ecs_deploy_failure_triage`.

## Audit metadata
- Pattern fingerprint: `ecs-deploy::health-check-failure::prod-shared-checkout-api`
- Pattern seen count: `2`
- Proposed skill due to recurrence: `true`
- engine: `runbook-forge`
- generated_at: `2026-06-26T06:37:55.097403+00:00`
