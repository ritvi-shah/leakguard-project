import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(
    page_title="LeakGuard | Water Intelligence",
    page_icon="💧",
    layout="wide"
)

# ---------- DATA ----------
np.random.seed(42)

sensors = pd.DataFrame({
    "Sensor": ["S-101", "S-102", "S-103", "S-104", "S-105", "S-106"],
    "Zone": ["North", "North", "Central", "Central", "South", "South"],
    "Pressure": [52.4, 51.8, 38.7, 39.2, 51.1, 50.6],
    "Flow": [118, 121, 167, 171, 109, 112],
})

# Simulated anomaly around Central zone
baseline_pressure = 52.0
sensors["Pressure Residual"] = sensors["Pressure"] - baseline_pressure
sensors["Anomaly"] = sensors["Pressure Residual"].abs() > 8

anomaly_count = int(sensors["Anomaly"].sum())

if anomaly_count == 0:
    network_status = "NORMAL"
    status_color = "green"
else:
    network_status = "LEAK SUSPECTED"
    status_color = "red"

central = sensors[sensors["Zone"] == "Central"].copy()
pressure_drop = max(0, baseline_pressure - central["Pressure"].mean())

estimated_loss = round(pressure_drop * 12.5, 1)
confidence = min(98, round(72 + pressure_drop * 2.5, 1))

if pressure_drop >= 10:
    severity = "CRITICAL"
elif pressure_drop >= 5:
    severity = "HIGH"
else:
    severity = "MEDIUM"

# ---------- HEADER ----------
st.title("💧 LeakGuard")
st.caption("Water Network Intelligence & Incident Response")

st.markdown(
    f"""
    **Network status:** :{status_color}[{network_status}]
    &nbsp;&nbsp; | &nbsp;&nbsp;
    **Last telemetry:** {datetime.now().strftime("%H:%M:%S")}
    """
)

# ---------- KPI CARDS ----------
c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Network Status",
    network_status
)

c2.metric(
    "Estimated Water Loss",
    f"{estimated_loss} L/min"
)

c3.metric(
    "Localization Confidence",
    f"{confidence}%"
)

c4.metric(
    "Incident Severity",
    severity
)

st.divider()

# ---------- INCIDENT ----------
st.subheader("🚨 Active Incident")

left, right = st.columns([1.4, 1])

with left:
    st.markdown(
        f"""
        ### Suspected leak — Central Zone

        **Detected through:** pressure + flow anomaly

        **Pressure drop:** `{pressure_drop:.1f} m`

        **Estimated water at risk:** `{estimated_loss} L/min`

        **Confidence:** `{confidence}%`

        **Recommended priority:** `{severity}`
        """
    )

    if severity == "CRITICAL":
        st.error("Immediate field inspection recommended.")
    elif severity == "HIGH":
        st.warning("Dispatch a maintenance crew for inspection.")
    else:
        st.info("Continue monitoring and verify telemetry.")

with right:
    st.markdown("### Suggested Response")

    st.write("1. Acknowledge incident")
    st.write("2. Dispatch nearest maintenance crew")
    st.write("3. Inspect Central Zone")
    st.write("4. Isolate affected segment if confirmed")
    st.write("5. Record resolution")

    if st.button("🚨 Acknowledge Incident", use_container_width=True):
        st.success("Incident acknowledged.")

st.divider()

# ---------- TELEMETRY ----------
st.subheader("📡 Live Network Telemetry")

display_data = sensors[
    ["Sensor", "Zone", "Pressure", "Flow", "Pressure Residual", "Anomaly"]
].copy()

display_data["Pressure"] = display_data["Pressure"].round(1)
display_data["Pressure Residual"] = display_data["Pressure Residual"].round(1)

st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True
)

st.divider()

# ---------- PRESSURE CHART ----------
st.subheader("📉 Pressure Residual Analysis")

chart_data = sensors[["Sensor", "Pressure Residual"]].set_index("Sensor")

st.bar_chart(chart_data)

st.caption(
    "Pressure residual = observed pressure − expected network baseline. "
    "Large negative residuals can indicate a possible leak or abnormal network condition."
)

st.divider()

# ---------- OPERATOR DECISION ----------
st.subheader("🧠 Operator Decision Support")

decision_col1, decision_col2, decision_col3 = st.columns(3)

decision_col1.metric(
    "Suspected Zone",
    "Central"
)

decision_col2.metric(
    "Sensors Flagged",
    anomaly_count
)

decision_col3.metric(
    "Response Priority",
    severity
)

st.info(
    "LeakGuard converts raw telemetry into an actionable incident: "
    "where to investigate, how severe the event may be, and what the operator should do next."
)

st.caption(
    "Hack Devengers 2.0 • LeakGuard Water Network Intelligence"
)
