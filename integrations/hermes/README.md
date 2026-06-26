# Hermes Integration Notes

Runbook Forge does not assume undocumented Hermes APIs. The core is a standalone CLI and Python library. A Hermes-compatible workflow can treat it as a local tool that produces Markdown reports and reusable runbook skill drafts.

## Integration model

1. Hermes receives evidence or a request to triage a deployment or incident.
2. Hermes calls one of the CLI commands:
   - `runbook-forge analyze terraform-plan --input fixtures/terraform/plan_public_s3.json --output reports/terraform-review.md`
   - `runbook-forge analyze ecs-deploy --input fixtures/aws/ecs_failed_deploy.json --output reports/ecs-triage.md`
   - `runbook-forge analyze sqs-lambda --input fixtures/aws/sqs_lambda_backlog.json --output reports/sqs-lambda-triage.md`
3. Hermes reads the generated Markdown report.
4. When `.runbook_forge/patterns.json` shows the same fingerprint more than once, Hermes can call `runbook-forge propose-skill --from-report <report> --output <runbook>`.
5. Hermes stores or reviews the generated Markdown skill in its own skill registry.

## Safety contract

- Runbook Forge is recommend-only by default.
- Demo and tests use fake local fixtures.
- Read-only AWS adapters are isolated and optional.
- Write actions are represented only as proposed command text.
- Any action that changes AWS, Terraform state, deployments, scaling, IAM, networking, or data retention requires explicit human approval outside this tool.

## Procedural memory

The local `.runbook_forge/patterns.json` file tracks deterministic fingerprints derived from evidence type, likely cause, and affected system. Repeated fingerprints trigger recommendations to create or update a reusable runbook skill. This is the procedural memory loop Hermes can use to improve future CloudOps triage.
