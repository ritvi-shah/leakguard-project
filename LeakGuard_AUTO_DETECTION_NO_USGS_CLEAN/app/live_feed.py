"""Live telemetry ingestion boundary for LeakGuard.

The demo can run without credentials using the transparent prototype stream.
For deployment, set LEAKGUARD_LIVE_URL to a REST endpoint that returns either
one reading or a list of readings with timestamp, sensor_id, zone, pressure and flow.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

import pandas as pd
import requests


REQUIRED = ["timestamp", "sensor_id", "zone", "pressure", "flow"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_time(value: Any) -> datetime:
    if value is None:
        return _utc_now()
    dt = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(dt):
        return _utc_now()
    return dt.to_pydatetime()


def normalize_payload(payload: Any) -> pd.DataFrame:
    if isinstance(payload, dict):
        if isinstance(payload.get("data"), list):
            payload = payload["data"]
        elif isinstance(payload.get("readings"), list):
            payload = payload["readings"]
        else:
            payload = [payload]
    if not isinstance(payload, list):
        raise ValueError("Live endpoint must return a JSON object or list of readings.")

    rows = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        row = {
            "timestamp": _parse_time(item.get("timestamp") or item.get("time") or item.get("ts")),
            "sensor_id": item.get("sensor_id") or item.get("sensor") or item.get("id"),
            "zone": item.get("zone") or item.get("area") or "Unknown",
            "pressure": item.get("pressure"),
            "flow": item.get("flow"),
            "baseline_pressure": item.get("baseline_pressure"),
            "baseline_flow": item.get("baseline_flow"),
            "quality": item.get("quality", "unknown"),
            "lat": item.get("lat"),
            "lon": item.get("lon"),
        }
        if row["sensor_id"] is None or row["pressure"] is None or row["flow"] is None:
            continue
        rows.append(row)

    if not rows:
        raise ValueError("No valid telemetry readings found in live response.")
    df = pd.DataFrame(rows)
    df["pressure"] = pd.to_numeric(df["pressure"], errors="coerce")
    df["flow"] = pd.to_numeric(df["flow"], errors="coerce")
    df["baseline_pressure"] = pd.to_numeric(df["baseline_pressure"], errors="coerce")
    df["baseline_flow"] = pd.to_numeric(df["baseline_flow"], errors="coerce")
    df = df.dropna(subset=["pressure", "flow"])
    if df.empty:
        raise ValueError("Telemetry pressure/flow values are not numeric.")
    return df


def fetch_live_rest(url: str | None = None, token: str | None = None, timeout: int = 5) -> tuple[pd.DataFrame | None, dict]:
    url = url or os.getenv("LEAKGUARD_LIVE_URL", "").strip()
    token = token if token is not None else os.getenv("LEAKGUARD_LIVE_TOKEN", "").strip()
    if not url:
        return None, {"status": "NOT_CONFIGURED", "message": "No live telemetry endpoint configured."}

    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        df = normalize_payload(response.json())
        newest = pd.to_datetime(df["timestamp"], utc=True).max().to_pydatetime()
        age = max(0, (_utc_now() - newest).total_seconds())
        status = "CONNECTED" if age <= 60 else "STALE"
        return df, {"status": status, "message": f"HTTP telemetry · newest reading {age:.0f}s old", "age_seconds": age}
    except Exception as exc:
        return None, {"status": "ERROR", "message": f"Live feed error: {type(exc).__name__}: {exc}"}
