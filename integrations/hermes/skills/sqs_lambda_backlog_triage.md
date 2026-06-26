# SQS/Lambda Backlog Triage Skill

## Skill name
SQS/Lambda Backlog Triage Skill

## When to use
Use this skill when SQS queue depth or oldest message age grows while Lambda consumers report errors, throttles, or timeouts.

## Inputs needed
- SQS queue depth and oldest message age.
- DLQ message count.
- Lambda errors, throttles, timeouts, duration, concurrency, and batch size.
- Recent logs and downstream dependency status.

## Investigation steps
1. Confirm queue depth, oldest message age, and DLQ pressure.
2. Check Lambda throttles, reserved concurrency, and concurrent executions.
3. Compare p95 duration with timeout.
4. Inspect logs for poison messages and downstream failures.
5. Propose concurrency, timeout, batch, or redrive changes for human review.

## Evidence to collect
- Queue metrics and event-source mapping configuration.
- Lambda error and throttle metrics.
- DLQ samples after redaction.
- Dependency status and retry behavior.

## Risk signals
- Oldest message age breaching freshness SLO.
- DLQ count increasing.
- Lambda throttles at reserved concurrency.
- Duration near timeout.
- Downstream 5xx errors.

## Safe remediation options
- Propose temporary concurrency increase after checking downstream limits.
- Propose timeout or batch-size tuning.
- Propose DLQ inspection and redrive plan.
- Propose dependency rollback or circuit breaker work.

## Commands to propose, not execute
```bash
aws sqs get-queue-attributes --queue-url <queue-url> --attribute-names All
aws lambda get-function-configuration --function-name <function>
aws lambda put-function-concurrency --function-name <function> --reserved-concurrent-executions <value>
aws lambda update-event-source-mapping --uuid <uuid> --batch-size <value>
```

## Approval requirements
Any change to concurrency, timeout, batch size, redrive policy, or queue retention requires explicit human approval.

## Rollback notes
Record prior event-source mapping and Lambda configuration before proposing changes.

## Example output
A backlog triage report with severity, suspected bottleneck, safe next checks, and proposed commands as text only.
