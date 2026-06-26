from runbook_forge.analysis.pattern_memory import PatternMemory, fingerprint_for


def test_pattern_memory_detects_recurrence(tmp_path) -> None:  # type: ignore[no-untyped-def]
    memory = PatternMemory(tmp_path / "patterns.json")

    first = memory.record("ecs-deploy", "health check failure", "prod-shared/checkout-api")
    second = memory.record("ecs-deploy", "health check failure", "prod-shared/checkout-api")

    assert first.count == 1
    assert second.count == 2
    assert memory.should_propose_skill(second)
    assert second.fingerprint == fingerprint_for(
        "ecs-deploy", "health check failure", "prod-shared/checkout-api"
    )
