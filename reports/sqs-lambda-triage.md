# Runbook Forge Report: sqs-lambda

## Executive summary
SQS/Lambda pipeline has backlog pressure. Suspected bottleneck: Lambda throttling and timeout pressure.

## Severity
critical

## Affected system
payments-events -> payments-event-worker

## Evidence reviewed
- `sqs_lambda_fixture`: Loaded SQS/Lambda fixture from /Users/aiden/Documents/Codex/2026-06-26/files-mentioned-by-the-user-build/outputs/runbook-forge/fixtures/aws/sqs_lambda_backlog.json.
- `sqs`: Queue depth 18234 and oldest message age 6120 seconds.
- `sqs_lambda_classifier`: Lambda throttling: Lambda had 28 throttles in the last 5 minutes.
- `sqs_lambda_classifier`: Lambda throttling: Concurrent executions 5 are at reserved concurrency 5.
- `sqs_lambda_classifier`: timeout too low: p95 duration 28600 ms, timeout 30000 ms, timeouts in 5m 11.
- `sqs_lambda_classifier`: poison messages: DLQ contains 143 messages.
- `sqs_lambda_classifier`: batch size/concurrency mismatch: Queue depth 18234, reserved concurrency 5, batch size 10.
- `sqs_lambda_classifier`: downstream dependency failures: Logs mention downstream 5xx or dependency failures.

## Likely root cause
Lambda throttling and timeout pressure

## Risk / blast radius
Message processing delay can breach freshness SLOs and increase duplicate processing or DLQ volume.

## Findings
- No structured risk findings were generated for this report type.

## Recommended next actions
1. Inspect queue attributes (`read_only`): Confirm approximate queue depth, oldest message age, and DLQ pressure.
   Proposed command: `aws sqs get-queue-attributes --queue-url <payments-events-url> --attribute-names All`
2. Inspect Lambda concurrency and errors (`read_only`): Review concurrency, throttles, errors, and timeout metrics before proposing changes.
   Proposed command: `aws lambda get-function-configuration --function-name payments-event-worker`
3. Propose concurrency adjustment (`propose_only`): Prepare a concurrency or event-source mapping change only as text for human review.
   Proposed command: `aws lambda put-function-concurrency --function-name payments-event-worker --reserved-concurrent-executions <value>`
4. Apply Lambda or queue changes only after approval (`requires_human_approval`): Concurrency, timeout, redrive, and batch-size changes can change production behavior.
   Proposed command: `aws lambda update-event-source-mapping --uuid <uuid> --batch-size <value>`

## Human approval required before write actions
Yes. The following actions are recommend-only and must be manually approved: Apply Lambda or queue changes only after approval

## Related or newly proposed runbook skill
Related skill: `sqs_lambda_backlog_triage`. Recurrence threshold has not been met yet.

## Audit metadata
- Pattern fingerprint: `sqs-lambda::lambda-throttling-and-timeout-pressure::payments-events-payments-event-worker`
- Pattern seen count: `1`
- Proposed skill due to recurrence: `false`
- engine: `runbook-forge`
- generated_at: `2026-06-26T06:37:55.097926+00:00`
