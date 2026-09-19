from app.engine import (
    telemetry_for_scenario,
    validation_benchmark,
    zone_scores,
    evidence_for_zone,
    decision_from_evidence,
)


def test_scenarios_localize_central():
    for scenario in ("Hidden Leak", "Major Burst"):
        scores = zone_scores(telemetry_for_scenario(scenario))
        assert scores.iloc[0]["zone"] == "Central"
        assert scores.iloc[0]["score"] >= 35


def test_normal_network_has_no_alert():
    scores = zone_scores(telemetry_for_scenario("Normal Network"))
    assert scores.iloc[0]["score"] < 35


def test_benchmark_is_reproducible_and_nontrivial():
    results, metrics = validation_benchmark()
    assert len(results) == 900
    assert 0.80 <= metrics["recall"] <= 0.90
    assert 0.90 <= metrics["precision"] <= 0.98
    assert 0.05 <= metrics["false_positive_rate"] <= 0.15
    assert 0.90 <= metrics["localization_accuracy"] <= 1.0


def test_explanation_and_decision():
    df = telemetry_for_scenario("Hidden Leak")
    scores = zone_scores(df)
    row = scores.iloc[0]
    evidence = evidence_for_zone(row, df[df.zone == row.zone])
    assert abs(sum(evidence.values()) - 1.0) < 1e-9
    decision, _ = decision_from_evidence(evidence, row.score)
    assert decision in {"PREPARE RESPONSE", "VERIFY", "MONITOR"}
