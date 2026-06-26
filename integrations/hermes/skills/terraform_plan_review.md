# Terraform Plan Review Skill

## Skill name
Terraform Plan Review Skill

## When to use
Use this skill before applying Terraform changes or when CI produces a Terraform plan with security, data, or cost risk.

## Inputs needed
- Terraform plan JSON from `terraform show -json`.
- Pull request context and changed modules.
- Environment, workspace, and deployment window.

## Investigation steps
1. Review public exposure signals for S3 and security groups.
2. Review IAM actions and resources for wildcard scope.
3. Review database replacements, deletes, or snapshot requirements.
4. Review expensive resources such as NAT Gateway.
5. Summarize blast radius and required approvals.

## Evidence to collect
- Resource address, type, and planned action.
- Before and after values for risky fields.
- Owner, environment, and exception ticket if present.

## Risk signals
- S3 public principals or disabled public access blocks.
- `0.0.0.0/0` or `::/0` ingress.
- IAM `*` actions or resources.
- RDS delete or replace actions.
- New NAT Gateway or high-egress design.

## Safe remediation options
- Narrow public access before apply.
- Replace wildcard IAM with least privilege.
- Defer destructive database changes until backup and rollback are verified.
- Use VPC endpoints where they fit traffic patterns.

## Commands to propose, not execute
```bash
terraform show -json plan.out > plan.json
terraform plan -out plan.out
terraform apply plan.out
```

## Approval requirements
Never execute `terraform apply` automatically. Require human approval for any infrastructure-changing command.

## Rollback notes
Capture current state, recent backups, and restore plan. Confirm state lock ownership before any rollback.

## Example output
A Markdown report with severity, risky resource addresses, evidence, blast radius, and an approval checklist.
