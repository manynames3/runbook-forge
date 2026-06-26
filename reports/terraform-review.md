# Runbook Forge Report: terraform-plan

## Executive summary
Runbook Forge found 6 risk signal(s) in the Terraform plan.

## Severity
critical

## Affected system
terraform-plan

## Evidence reviewed
- `terraform_plan`: Reviewed 6 planned resource changes from /Users/aiden/Documents/Codex/2026-06-26/files-mentioned-by-the-user-build/outputs/runbook-forge/fixtures/terraform/plan_public_s3.json. (/Users/aiden/Documents/Codex/2026-06-26/files-mentioned-by-the-user-build/outputs/runbook-forge/fixtures/terraform/plan_public_s3.json)

## Likely root cause
Terraform plan introduces high-risk infrastructure changes

## Risk / blast radius
Objects in the bucket could become publicly readable if paired with permissive ACLs or policies. Anonymous users may gain bucket or object access depending on policy actions. Internet-origin traffic can reach the attached workload on the allowed ports.

## Findings
### S3 public access protections are disabled
- ID: `tf-s3-public-access-block-disabled`
- Severity: `high`
- Affected resource: `aws_s3_bucket_public_access_block.assets`
- Blast radius: Objects in the bucket could become publicly readable if paired with permissive ACLs or policies.
- Recommendation: Keep all public access block controls enabled unless a documented exception is approved.
- Approval gate: `requires_human_approval` - Terraform apply can change cloud infrastructure and requires review.
- Evidence:
- `terraform_plan`: Public access block fields disabled: block_public_acls, block_public_policy, ignore_public_acls, restrict_public_buckets. (aws_s3_bucket_public_access_block.assets)
### S3 bucket policy allows public principal
- ID: `tf-s3-public-policy`
- Severity: `critical`
- Affected resource: `aws_s3_bucket_policy.assets`
- Blast radius: Anonymous users may gain bucket or object access depending on policy actions.
- Recommendation: Remove public principals or require a reviewed exception with explicit business justification.
- Approval gate: `requires_human_approval` - Terraform apply can change cloud infrastructure and requires review.
- Evidence:
- `terraform_plan`: Bucket policy contains an Allow statement for principal '*'. (aws_s3_bucket_policy.assets)
### Security group ingress is open to the internet
- ID: `tf-sg-world-ingress`
- Severity: `critical`
- Affected resource: `aws_security_group_rule.web_ssh`
- Blast radius: Internet-origin traffic can reach the attached workload on the allowed ports.
- Recommendation: Restrict ingress to known CIDR ranges, load balancer security groups, or private networking.
- Approval gate: `requires_human_approval` - Terraform apply can change cloud infrastructure and requires review.
- Evidence:
- `terraform_plan`: Ingress allows ['0.0.0.0/0'] on ports 22-22. (aws_security_group_rule.web_ssh)
### IAM policy uses wildcard permissions
- ID: `tf-iam-wildcard`
- Severity: `high`
- Affected resource: `aws_iam_policy.worker`
- Blast radius: A compromised principal may gain broad access beyond the intended workload boundary.
- Recommendation: Replace wildcards with least-privilege actions and scoped resources.
- Approval gate: `requires_human_approval` - Terraform apply can change cloud infrastructure and requires review.
- Evidence:
- `terraform_plan`: Policy contains wildcard actions and wildcard resources. (aws_iam_policy.worker)
### RDS database has a destructive plan action
- ID: `tf-rds-destructive-change`
- Severity: `critical`
- Affected resource: `aws_db_instance.orders`
- Blast radius: Database replacement or deletion can cause data loss, downtime, and restore work.
- Recommendation: Require backup verification, maintenance window approval, and rollback plan before apply.
- Approval gate: `requires_human_approval` - Terraform apply can change cloud infrastructure and requires review.
- Evidence:
- `terraform_plan`: Plan actions are ['delete', 'create']; target database is orders-prod. (aws_db_instance.orders)
### NAT Gateway creation can increase recurring cost
- ID: `tf-nat-gateway-cost`
- Severity: `medium`
- Affected resource: `aws_nat_gateway.main`
- Blast radius: Hourly NAT Gateway charges and data processing charges can materially affect monthly spend.
- Recommendation: Confirm expected egress volume and whether private endpoints are a better fit.
- Approval gate: `requires_human_approval` - Terraform apply can change cloud infrastructure and requires review.
- Evidence:
- `terraform_plan`: Plan creates an AWS NAT Gateway. (aws_nat_gateway.main)

## Recommended next actions
1. Review plan JSON (`read_only`): Inspect the generated plan and confirm all risky resources have owners and rollback notes.
   Proposed command: `terraform show -json plan.out > plan.json`
2. Block apply until risk owner approves (`requires_human_approval`): Do not apply this plan until public access, IAM, database, and cost findings are accepted or fixed.
   Proposed command: `terraform apply plan.out`

## Human approval required before write actions
Yes. The following actions are recommend-only and must be manually approved: Block apply until risk owner approves

## Related or newly proposed runbook skill
Related skill: `terraform_plan_review`. Recurrence threshold has not been met yet.

## Audit metadata
- Pattern fingerprint: `terraform-plan::terraform-plan-introduces-high-risk-infrastructure-changes::terraform-plan`
- Pattern seen count: `1`
- Proposed skill due to recurrence: `false`
- engine: `runbook-forge`
- generated_at: `2026-06-26T06:37:55.095609+00:00`
