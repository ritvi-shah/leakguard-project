from __future__ import annotations

import numpy as np
import pandas as pd

ZONES = {
    "North": {"population": 8200, "critical": ["North Hospital"], "length_km": 4.2},
    "Central": {"population": 12500, "critical": ["Central Hospital", "Metro Station"], "length_km": 6.8},
    "South": {"population": 5100, "critical": ["South Market"], "length_km": 5.4},
}

SENSORS = pd.DataFrame([
    ["S-101", "North", "North inlet", 52.0, 120.0],
    ["S-102", "North", "North outlet", 52.0, 120.0],
    ["S-103", "Central", "Central inlet", 52.0, 120.0],
    ["S-104", "Central", "Central outlet", 52.0, 120.0],
    ["S-105", "South", "South inlet", 52.0, 120.0],
    ["S-106", "South", "South outlet", 52.0, 120.0],
], columns=["sensor", "zone", "location", "baseline_pressure", "baseline_flow"])

INTERVENTIONS = pd.DataFrame([
    ["Monitor only", 0.00, 100.0, 100.0, "Continue observing the affected zone."],
    ["Isolate Central branch", 0.91, 96.0, 100.0, "Prepare isolation of the suspected Central branch."],
    ["Isolate secondary branch", 0.95, 82.0, 75.0, "Reduce loss while retaining most service."],
    ["Emergency isolation", 0.97, 61.0, 0.0, "Maximum containment; critical service may be interrupted."],
], columns=["action", "loss_reduction", "population_served_pct", "critical_service_pct", "description"])


def telemetry_for_scenario(name: str = "Hidden Leak") -> pd.DataFrame:
    if name == "Normal Network":
        pressure = [52.4, 51.8, 52.1, 51.9, 51.1, 50.6]
        flow = [118, 121, 119, 120, 109, 112]
    elif name == "Major Burst":
        pressure = [52.4, 51.8, 28.5, 26.8, 51.1, 50.6]
        flow = [118, 121, 225, 238, 109, 112]
    else:
        pressure = [52.4, 51.8, 34.5, 32.8, 51.1, 50.6]
        flow = [118, 121, 194, 202, 109, 112]
    df = SENSORS.copy()
    df["pressure"] = pressure
    df["flow"] = flow
    return add_features(df)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "baseline_pressure" not in out:
        out["baseline_pressure"] = out.groupby("zone")["pressure"].transform("median")
    if "baseline_flow" not in out:
        out["baseline_flow"] = out.groupby("zone")["flow"].transform("median")
    out["pressure_residual"] = out["pressure"] - out["baseline_pressure"]
    out["flow_deviation"] = out["flow"] - out["baseline_flow"]
    out["pressure_anomaly"] = out["pressure_residual"].abs() > 8
    out["flow_anomaly"] = out["flow_deviation"].abs() > 30
    out["multi_signal"] = out["pressure_anomaly"] & out["flow_anomaly"]
    return out


def live_simulation_points(scenario: str = "Hidden Leak", minutes: int = 60, step: int = 1) -> pd.DataFrame:
    target = telemetry_for_scenario(scenario)
    target_p = float(target.loc[target.zone == "Central", "pressure"].mean())
    target_f = float(target.loc[target.zone == "Central", "flow"].mean())
    rows = []
    for minute in range(0, minutes + 1, step):
        if scenario == "Normal Network":
            progress = 0.0
        elif scenario == "Major Burst":
            progress = np.clip((minute - 3) / 18.0, 0, 1)
        else:
            progress = np.clip((minute - 8) / 30.0, 0, 1)
        smooth = progress * progress * (3 - 2 * progress)
        wobble_p = np.sin(minute / 3.7) * (0.18 + 0.32 * smooth)
        wobble_f = np.cos(minute / 4.6) * (0.9 + 1.8 * smooth)
        pressure = 52.0 + (target_p - 52.0) * smooth + wobble_p
        flow = 120.0 + (target_f - 120.0) * smooth + wobble_f
        loss = max(0.0, (flow - 120.0) * 0.95 + max(0.0, 52.0 - pressure) * 3.2)
        p_drop = max(0.0, (52.0 - pressure) / 52.0 * 100)
        f_change = max(0.0, (flow - 120.0) / 120.0 * 100)
        multi_signal = p_drop >= 12 and f_change >= 20
        score = min(100.0, p_drop * 1.7 + f_change * 2.2 + (12 if multi_signal else 0))
        if score >= 68:
            status = "LEAK DETECTED"
        elif score >= 28:
            status = "WARNING"
        else:
            status = "MONITORING"
        rows.append([minute, pressure, flow, loss, p_drop, f_change, score, status])
    return pd.DataFrame(rows, columns=[
        "minute", "pressure", "flow", "estimated_loss_lpm", "pressure_drop_pct",
        "flow_change_pct", "risk_score", "status"
    ])


def zone_scores(df: pd.DataFrame) -> pd.DataFrame:
    working = add_features(df)
    rows = []
    for zone, meta in ZONES.items():
        z = working[working.zone == zone]
        if z.empty:
            rows.append({"zone": zone, "score": 0.0, "severity": "NO DATA", "pressure_drop_kpa": 0.0,
                         "flow_deviation_lpm": 0.0, "sensor_agreement": 0.0, "affected_population": meta["population"],
                         "critical_sites": ", ".join(meta["critical"]), "pipeline_km": meta["length_km"]})
            continue
        pressure_drop = max(0.0, float(-z.pressure_residual.min()))
        flow_dev = max(0.0, float(z.flow_deviation.max()))
        p_count = int(z.pressure_anomaly.sum())
        f_count = int(z.flow_anomaly.sum())
        agreement = float(z.multi_signal.mean())
        score = min(100.0, pressure_drop * 4.0 + flow_dev * 0.45 + p_count * 7 + f_count * 7 + agreement * 12)
        if score >= 70 or pressure_drop >= 15:
            severity = "CRITICAL"
        elif score >= 35 or pressure_drop >= 7:
            severity = "HIGH"
        elif score >= 15:
            severity = "MEDIUM"
        else:
            severity = "NORMAL"
        rows.append({
            "zone": zone, "score": round(score, 1), "severity": severity,
            "pressure_drop_kpa": round(pressure_drop, 1), "flow_deviation_lpm": round(flow_dev, 1),
            "sensor_agreement": round(agreement * 100, 0), "affected_population": meta["population"],
            "critical_sites": ", ".join(meta["critical"]), "pipeline_km": meta["length_km"],
        })
    return pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)


def evidence_for_zone(row, df_zone):
    p = min(1.0, float(row.pressure_drop_kpa) / 20)
    f = min(1.0, float(row.flow_deviation_lpm) / 100)
    agreement = min(1.0, float(row.sensor_agreement) / 100)
    persistence = 0.92 if row.score >= 50 else (0.72 if row.score >= 20 else 0.35)
    leak = min(0.99, 0.10 + 0.35 * p + 0.35 * f + 0.12 * persistence + 0.08 * agreement)
    sensor_fault = max(0.01, 0.55 - 0.45 * agreement)
    demand = max(0.01, 0.30 - 0.20 * f)
    valve = max(0.01, 0.20 - 0.12 * p)
    total = leak + sensor_fault + demand + valve
    return {"Leak": leak / total, "Sensor fault": sensor_fault / total, "Demand shift": demand / total, "Valve/pump event": valve / total}


def decision_from_evidence(evidence, score):
    leak = evidence["Leak"]
    if score < 15:
        return "MONITOR", "Evidence is weak; continue watching the network."
    if leak >= 0.62 and score >= 50:
        return "PREPARE RESPONSE", "Pressure and flow evidence agree strongly enough to prepare a field response."
    return "VERIFY", "An anomaly exists; collect another observation before field action."


def estimate_loss(row):
    flow_dev = row.get("flow_deviation_lpm", row.get("flow_deviation", 0))
    pressure_drop = row.get("pressure_drop_kpa", row.get("pressure_drop_m", max(0.0, row.get("baseline_pressure", 52.0) - row.get("pressure", 52.0))))
    return round(max(0, float(flow_dev)) * 0.95 + max(0, float(pressure_drop)) * 3.2, 1)


def simulate_intervention(df, zone_name, action):
    if action not in set(INTERVENTIONS["action"]):
        raise ValueError("Unknown intervention selected.")
    zone_df = add_features(df[df["zone"] == zone_name].copy())
    if zone_df.empty:
        raise ValueError("Selected zone has no telemetry.")
    intervention = INTERVENTIONS[INTERVENTIONS["action"] == action].iloc[0]
    reduction = float(intervention["loss_reduction"])
    service = float(intervention["critical_service_pct"]) / 100.0
    result = zone_df.copy()
    result["pressure_before"] = result["pressure"]
    result["flow_before"] = result["flow"]
    result["pressure_after"] = result["pressure"] + np.maximum(0, result["baseline_pressure"] - result["pressure"]) * (0.25 + 0.75 * reduction)
    result["pressure_after"] = np.minimum(result["baseline_pressure"] * 1.01, result["pressure_after"])
    excess_flow = np.maximum(0, result["flow"] - result["baseline_flow"])
    result["flow_after"] = result["flow"] - excess_flow * reduction
    result["flow_after"] = np.maximum(result["baseline_flow"] * (0.96 - 0.08 * (1 - service)), result["flow_after"])
    result["pressure_recovery"] = result["pressure_after"] - result["pressure_before"]
    zone_flow_dev = float(np.maximum(0, zone_df["flow"] - zone_df["baseline_flow"]).max())
    zone_pressure_drop = float(np.maximum(0, zone_df["baseline_pressure"] - zone_df["pressure"]).max())
    total_before = round(zone_flow_dev * 0.95 + zone_pressure_drop * 3.2, 1)
    pressure_drop_after = max(0.0, float((result["baseline_pressure"] - result["pressure_after"]).max()))
    residual_flow = max(0.0, float((result["flow_after"] - result["baseline_flow"]).max()))
    total_after = round(residual_flow * 0.95 + pressure_drop_after * 3.2, 1)
    summary = {
        "action": action, "zone": zone_name,
        "loss_before_lpm": total_before, "loss_after_lpm": total_after,
        "loss_reduction_pct": round(max(0, (total_before - total_after) / max(total_before, 1) * 100), 1),
        "critical_service_pct": round(float(intervention["critical_service_pct"]), 1),
        "max_pressure_recovery": round(float(result["pressure_recovery"].max()), 1),
        "description": intervention["description"],
    }
    return result, summary


def sensor_placement(df):
    zone = zone_scores(df)
    rows = []
    for _, r in zone.iterrows():
        for junction, reduction in [("J-17", 38), ("J-23", 27), ("J-31", 16)]:
            multiplier = 1.0 if r.zone == "Central" else 0.55
            rows.append([junction, r.zone, round(reduction * multiplier, 1)])
    return pd.DataFrame(rows, columns=["candidate", "zone", "uncertainty_reduction_pct"]).sort_values("uncertainty_reduction_pct", ascending=False).head(5)


def validation_scenarios():
    rows = []
    for name, expected_zone, expected_status in [
        ("Normal Network", "None", "MONITOR"),
        ("Hidden Leak", "Central", "ALERT"),
        ("Major Burst", "Central", "ALERT"),
    ]:
        df = telemetry_for_scenario(name)
        zones = zone_scores(df)
        top = zones.iloc[0]
        if name == "Normal Network":
            detected = top.score >= 15
            localized = top.zone == "Central" and top.score >= 35
        else:
            detected = top.score >= 35
            localized = top.zone == expected_zone
        rows.append([name, expected_zone, top.zone, "Yes" if detected else "No", "Yes" if localized else "No"])
    return pd.DataFrame(rows, columns=["Scenario", "Expected zone", "Top zone", "Alert triggered", "Zone localized"])


def generate_validation_case(rng, scenario, target_zone=None):
    """Create one controlled telemetry snapshot with known ground truth."""
    df = SENSORS.copy()
    pressure = df["baseline_pressure"].to_numpy(dtype=float).copy()
    flow = df["baseline_flow"].to_numpy(dtype=float).copy()
    pressure += rng.normal(0, 0.8, len(df))
    flow += rng.normal(0, 2.2, len(df))

    # Background operational variation and occasional single-sensor faults keep
    # the benchmark from becoming unrealistically clean.
    if rng.random() < 0.18:
        noise_zone = str(rng.choice([z for z in ZONES if z != target_zone])) if target_zone else str(rng.choice(list(ZONES)))
        nidx = df["zone"].eq(noise_zone).to_numpy()
        if rng.random() < 0.55:
            pressure[nidx] -= rng.uniform(4.0, 9.0)
        else:
            flow[nidx] += rng.uniform(15.0, 32.0)
    if rng.random() < 0.10:
        fault_idx = int(rng.integers(0, len(df)))
        pressure[fault_idx] -= rng.uniform(7.0, 13.0)

    if scenario in {"Hidden Leak", "Major Burst"}:
        zone = target_zone or "Central"
        idx = df["zone"].eq(zone).to_numpy()
        severity = rng.uniform(0.25, 1.0)
        if scenario == "Hidden Leak":
            pressure_drop = rng.uniform(7.0, 16.0) * severity
            flow_rise = rng.uniform(24.0, 75.0) * severity
        else:
            pressure_drop = rng.uniform(13.0, 27.0) * severity
            flow_rise = rng.uniform(55.0, 135.0) * severity
        pressure[idx] -= pressure_drop + rng.normal(0, 0.5, idx.sum())
        flow[idx] += flow_rise + rng.normal(0, 2.5, idx.sum())

    df["pressure"] = pressure
    df["flow"] = flow
    df["ground_truth"] = scenario != "Normal Network"
    df["ground_truth_zone"] = target_zone if scenario != "Normal Network" else "None"
    return add_features(df)


def validation_benchmark(seed=42, cases_per_class=300):
    """Evaluate the deterministic detector on reproducible controlled cases."""
    rng = np.random.default_rng(seed)
    rows = []
    zones = list(ZONES)
    for scenario in ["Normal Network", "Hidden Leak", "Major Burst"]:
        for _ in range(cases_per_class):
            target = None if scenario == "Normal Network" else str(rng.choice(zones))
            df = generate_validation_case(rng, scenario, target)
            scores = zone_scores(df)
            top = scores.iloc[0]
            if scenario == "Normal Network":
                alert = bool(top.score >= 35)
                localized = False
            else:
                alert = bool(top.score >= 35)
                localized = bool(top.zone == target)
            rows.append({
                "scenario": scenario,
                "ground_truth_alert": scenario != "Normal Network",
                "predicted_alert": alert,
                "target_zone": target or "None",
                "predicted_zone": top.zone if alert else "None",
                "localized": localized if scenario != "Normal Network" else False,
                "risk": float(top.score),
            })
    results = pd.DataFrame(rows)
    tp = int(((results.ground_truth_alert) & (results.predicted_alert)).sum())
    tn = int((~results.ground_truth_alert & ~results.predicted_alert).sum())
    fp = int((~results.ground_truth_alert & results.predicted_alert).sum())
    fn = int((results.ground_truth_alert & ~results.predicted_alert).sum())
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    fpr = fp / max(fp + tn, 1)
    positive = results[results.ground_truth_alert]
    localization = float(positive.localized.mean()) if len(positive) else 0.0
    metrics = {
        "cases": len(results),
        "positive_cases": len(positive),
        "normal_cases": int((~results.ground_truth_alert).sum()),
        "precision": precision,
        "recall": recall,
        "false_positive_rate": fpr,
        "localization_accuracy": localization,
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "seed": seed,
    }
    return results, metrics


def validation_method_comparison(seed=42, cases_per_class=300):
    """Compare LeakGuard's multi-signal detector with a pressure-only baseline on the same cases."""
    rng = np.random.default_rng(seed)
    rows = []
    for scenario in ["Normal Network", "Hidden Leak", "Major Burst"]:
        for _ in range(cases_per_class):
            target = None if scenario == "Normal Network" else str(rng.choice(list(ZONES)))
            df = generate_validation_case(rng, scenario, target)
            zones = zone_scores(df)
            top = zones.iloc[0]
            multi_alert = bool(top.score >= 35)
            # Pressure-only comparator: alert when the strongest zone pressure
            # drop reaches 8 kPa. This is deliberately simple and transparent.
            p_only = df.groupby("zone")["pressure_residual"].min().abs().sort_values(ascending=False)
            pressure_alert = bool((not p_only.empty) and p_only.iloc[0] >= 8.0)
            rows.append({
                "truth": scenario != "Normal Network",
                "multi": multi_alert,
                "pressure": pressure_alert,
            })
    r = pd.DataFrame(rows)
    out = []
    for label, col in [("LeakGuard multi-signal", "multi"), ("Pressure-only baseline", "pressure")]:
        truth = r.truth
        pred = r[col]
        tp = int((truth & pred).sum()); tn = int((~truth & ~pred).sum())
        fp = int((~truth & pred).sum()); fn = int((truth & ~pred).sum())
        out.append({
            "method": label,
            "precision": tp / max(tp + fp, 1),
            "recall": tp / max(tp + fn, 1),
            "false_positive_rate": fp / max(fp + tn, 1),
            "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        })
    return pd.DataFrame(out)
