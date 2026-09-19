import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="LeakGuard | Water Intelligence",
    page_icon="💧",
    layout="wide"
)

# ---------- NETWORK DATA ----------

zones = {
    "North": {
        "sensors": ["S-101", "S-102"],
        "population": 4200,
        "critical_sites": ["North Clinic"],
    },
    "Central": {
        "sensors": ["S-103", "S-104"],
        "population": 7800,
        "critical_sites": ["Central Hospital", "City School"],
    },
    "South": {
        "sensors": ["S-105", "S-106"],
        "population": 5100,
        "critical_sites": ["South Market"],
    }
}

# ---------- INCIDENT SIMULATOR ----------

st.sidebar.title("💧 LeakGuard")
st.sidebar.caption("Water Network Incident Simulator")

scenario = st.sidebar.selectbox(
    "Select network scenario",
    [
        "Normal Network",
        "Hidden Leak",
        "Major Burst"
    ]
)

if scenario == "Normal Network":

    pressure_values = [52.4, 51.8, 52.1, 51.9, 51.1, 50.6]
    flow_values = [118, 121, 119, 120, 109, 112]

elif scenario == "Hidden Leak":

    pressure_values = [52.4, 51.8, 45.2, 44.7, 51.1, 50.6]
    flow_values = [118, 121, 148, 153, 109, 112]

else:

    pressure_values = [52.4, 51.8, 32.5, 31.8, 51.1, 50.6]
    flow_values = [118, 121, 205, 214, 109, 112]


sensors = pd.DataFrame({
    "Sensor": [
        "S-101",
        "S-102",
        "S-103",
        "S-104",
        "S-105",
        "S-106"
    ],
    "Zone": [
        "North",
        "North",
        "Central",
        "Central",
        "South",
        "South"
    ],
    "Pressure": pressure_values,
    "Flow": flow_values
})

# ---------- DETECTION ----------

baseline_pressure = 52.0

sensors["Pressure Residual"] = (
    sensors["Pressure"] - baseline_pressure
)

sensors["Anomaly"] = (
    sensors["Pressure Residual"].abs() > 8
)

anomaly_count = int(
    sensors["Anomaly"].sum()
)

# ---------- LOCALIZATION ----------

zone_scores = {}

for zone, information in zones.items():

    zone_sensors = sensors[
        sensors["Zone"] == zone
    ]

    pressure_drop = max(
        0,
        baseline_pressure -
        zone_sensors["Pressure"].mean()
    )

    anomaly_count_zone = int(
        zone_sensors["Anomaly"].sum()
    )

    score = (
        pressure_drop * 0.7
        + anomaly_count_zone * 5
    )

    zone_scores[zone] = score


suspected_zone = max(
    zone_scores,
    key=zone_scores.get
)

zone_score = zone_scores[suspected_zone]

central = sensors[
    sensors["Zone"] == suspected_zone
]

pressure_drop = max(
    0,
    baseline_pressure -
    central["Pressure"].mean()
)

# ---------- IMPACT ESTIMATION ----------

estimated_loss = round(
    pressure_drop * 12.5,
    1
)

confidence = min(
    99,
    round(
        72 + pressure_drop * 2.5,
        1
    )
)

affected_population = zones[
    suspected_zone
]["population"]

critical_sites = zones[
    suspected_zone
]["critical_sites"]

if pressure_drop >= 15:

    severity = "CRITICAL"

elif pressure_drop >= 7:

    severity = "HIGH"

elif pressure_drop > 0:

    severity = "MEDIUM"

else:

    severity = "NONE"


if scenario == "Normal Network":

    network_status = "NORMAL"

else:

    network_status = "INCIDENT DETECTED"


# ---------- HEADER ----------

st.title("💧 LeakGuard")

st.caption(
    "Water Network Intelligence & Incident Response"
)

st.markdown(
    f"""
    **Network Status:** `{network_status}`
    &nbsp;&nbsp; | &nbsp;&nbsp;
    **Scenario:** `{scenario}`
    &nbsp;&nbsp; | &nbsp;&nbsp;
    **Telemetry:** `{datetime.now().strftime("%H:%M:%S")}`
    """
)

st.divider()

# ---------- KPI CARDS ----------

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Network Status",
    network_status
)

c2.metric(
    "Estimated Loss",
    f"{estimated_loss} L/min"
)

c3.metric(
    "Localization Confidence",
    f"{confidence}%"
)

c4.metric(
    "Severity",
    severity
)

st.divider()

# ---------- INCIDENT ----------

if scenario == "Normal Network":

    st.success(
        "✅ No significant leak detected. "
        "Network telemetry is within the expected range."
    )

else:

    st.subheader("🚨 Active Incident")

    left, right = st.columns([1.5, 1])

    with left:

        st.markdown(
            f"""
            ### Suspected leak — {suspected_zone} Zone

            **Detection:** Pressure + flow anomaly

            **Pressure drop:** `{pressure_drop:.1f} m`

            **Estimated water loss:** `{estimated_loss} L/min`

            **Localization confidence:** `{confidence}%`

            **Incident severity:** `{severity}`
            """
        )

        if severity == "CRITICAL":

            st.error(
                "Immediate field response recommended. "
                "Potential major water loss detected."
            )

        elif severity == "HIGH":

            st.warning(
                "Dispatch a maintenance crew to "
                f"the {suspected_zone} Zone."
            )

        else:

            st.info(
                "Continue monitoring and verify "
                "the suspected anomaly."
            )

    with right:

        st.markdown("### Recommended Response")

        st.write("1. Acknowledge incident")
        st.write("2. Dispatch nearest crew")
        st.write(
            f"3. Inspect {suspected_zone} Zone"
        )
        st.write("4. Isolate affected segment")
        st.write("5. Confirm resolution")

        if st.button(
            "🚨 Acknowledge Incident",
            use_container_width=True
        ):

            st.success(
                "Incident acknowledged by operator."
            )


st.divider()

# ---------- IMPACT ----------

if scenario != "Normal Network":

    st.subheader("🌍 Estimated Network Impact")

    i1, i2, i3 = st.columns(3)

    i1.metric(
        "Population at Risk",
        f"{affected_population:,}"
    )

    i2.metric(
        "Critical Sites",
        len(critical_sites)
    )

    i3.metric(
        "Water at Risk",
        f"{estimated_loss} L/min"
    )

    st.markdown(
        f"""
        **Affected zone:** {suspected_zone}

        **Potentially affected critical locations:**
        """
    )

    for site in critical_sites:
        st.write(f"• {site}")


st.divider()

# ---------- LOCALIZATION ----------

st.subheader("📍 Leak Localization")

localization_data = pd.DataFrame({
    "Zone": list(zone_scores.keys()),
    "Detection Score": [
        round(score, 2)
        for score in zone_scores.values()
    ]
})

localization_data = localization_data.sort_values(
    "Detection Score",
    ascending=False
)

st.dataframe(
    localization_data,
    use_container_width=True,
    hide_index=True
)

if scenario != "Normal Network":

    st.success(
        f"🎯 Highest-confidence location: "
        f"**{suspected_zone} Zone**"
    )


st.divider()

# ---------- TELEMETRY ----------

st.subheader("📡 Network Telemetry")

display_data = sensors[
    [
        "Sensor",
        "Zone",
        "Pressure",
        "Flow",
        "Pressure Residual",
        "Anomaly"
    ]
].copy()

display_data["Pressure"] = display_data[
    "Pressure"
].round(1)

display_data["Pressure Residual"] = display_data[
    "Pressure Residual"
].round(1)

st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True
)

st.divider()

# ---------- PRESSURE ANALYSIS ----------

st.subheader("📉 Pressure Residual Analysis")

chart_data = sensors[
    ["Sensor", "Pressure Residual"]
].set_index("Sensor")

st.bar_chart(chart_data)

st.caption(
    "Large negative pressure residuals indicate "
    "a possible abnormal network condition."
)

st.divider()

# ---------- OPERATOR DECISION ----------

st.subheader("🧠 Operator Decision Support")

d1, d2, d3 = st.columns(3)

d1.metric(
    "Suspected Zone",
    suspected_zone if scenario != "Normal Network"
    else "None"
)

d2.metric(
    "Sensors Flagged",
    anomaly_count
)

d3.metric(
    "Response Priority",
    severity
)

if scenario != "Normal Network":

    st.info(
        f"LeakGuard recommends investigating the "
        f"**{suspected_zone} Zone** with **{severity}** "
        f"response priority. Approximately "
        f"**{estimated_loss} L/min** may be at risk."
    )

else:

    st.info(
        "LeakGuard is continuously monitoring "
        "network telemetry for abnormal conditions."
    )

st.divider()

st.caption(
    "LeakGuard • Hack Devengers 2.0"
)
