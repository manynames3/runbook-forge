# AGENTS.md

## Project purpose

Runbook Forge is a recommend-only CloudOps/SRE triage CLI that turns recurring failure patterns into reusable runbook skills. It is meant to demonstrate production-minded incident analysis, procedural memory, and safe human approval gates.

## Safety rules

- Do not execute real cloud write actions.
- Do not add auto-remediation against AWS.
- Keep AWS integrations read-only and mockable.
- Use fixtures and mocks for tests.
- Treat generated write commands as proposal text only.
- Redact secrets in reports, skills, and audit logs.

## Test commands

```bash
ruff check .
mypy src/runbook_forge
pytest
runbook-forge demo
```

Optional Docker smoke test when Docker is installed:

```bash
docker compose up --build
```

## Code style

- Use Python 3.11+ type hints.
- Keep modules small and purpose-specific.
- Prefer Pydantic models for structured report data.
- Keep CLI behavior deterministic and fixture-friendly.
- Avoid network calls in tests.
- Keep hosted demo changes static unless the user explicitly accepts recurring cost.

## Cloud action policy

All Terraform, AWS, deployment, IAM, networking, scaling, data retention, and rollback commands must stay in `propose_only` or `requires_human_approval` mode unless a future maintainer deliberately changes the safety model and documents it.
