from runbook_forge.safety.redaction import redact_text, redact_value


def test_redacts_common_secret_shapes() -> None:
    text = (
        "aws_access_key_id=AKIA1234567890ABCDEF "
        "password=hunter2 "
        "token=ghp_abcdefghijklmnopqrstuvwxyz123456 "
        "postgres://user:pass@example.test:5432/db"
    )

    redacted = redact_text(text)

    assert "AKIA1234567890ABCDEF" not in redacted
    assert "hunter2" not in redacted
    assert "ghp_" not in redacted
    assert "pass@example" not in redacted


def test_redacts_nested_values() -> None:
    value = {"env": {"DATABASE_URL": "postgres://user:pass@example.test/db"}}

    redacted = redact_value(value)

    assert redacted == {"env": {"DATABASE_URL": "postgres://CONNECTION_STRING_REDACTED"}}
