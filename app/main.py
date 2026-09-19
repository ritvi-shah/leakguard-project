import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="LeakGuard | Water Network Intelligence",
    page_icon="💧",
    layout="wide"
)

# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>
    .main {
        background-color: #f6f8fb;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .hero {
        padding: 1.4rem 1.6rem;
        border-radius: 16px;
        background: linear-gradient(135deg, #0f172a, #164e63);
        color: white;
        margin-bottom: 1.5rem;
    }

    .hero h1 {
        margin-bottom: 0.2rem;
    }

    .hero p {
        opacity: 0.85;
        margin-bottom: 0;
    }

    .incident-card {
        padding: 1.2rem;
        border-radius: 14px;
        background: white;
        border: 1px solid #e5e7eb;
        margin-bottom: 1rem;
    }

    .small-label {
        color: #64748b;
        font-size: 0.85rem;
    }

    .big-value {
        font-size: 1.5rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# NETWORK MODEL
# ============================================================

zones = {
    "North": {
        "sensors": ["S-101", "S-102"],
        "population": 4200,
        "critical_sites": ["North Clinic"],
        "pipeline_length": 4.8
    },
    "Central": {
        "sensors": ["S-103", "S-104"],
        "population": 7800,
        "critical_sites": [
            "Central Hospital",
            "City School"
        ],
        "pipeline_length": 6.2
    },
    "South": {
        "sensors": ["S-105", "S-106"],
        "population": 5100,
        "critical_sites": ["South Market"],
        "pipeline_length": 5.4
    }
}

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("💧 LeakGuard")
st.sidebar.caption("Water Network Intelligence")

st.sidebar.divider()

scenario = st.sidebar.selectbox(
    "Simulation Scenario",
    [
        "Normal Network",
        "Hidden Leak",
        "Major Burst"
    ]
)

auto_refresh = st.sidebar.checkbox(
    "Live monitoring mode",
    value=False
)

st.sidebar.divider()

st.sidebar.markdown("### System")

st.sidebar.write("🟢 Telemetry: Connected")
st.sidebar.write("🟢 Detection Engine: Active")
st.sidebar.write("🟢 Network Model: Online")

# ============================================================
# SIMULATED TELEMETRY
# ============================================================

if scenario == "Normal Network":

    pressure_values = [
        52.4, 51.8, 52.1,
        51.9, 51.1, 50.6
    ]

    flow_values = [
        118, 121, 119,
        120, 109, 112
    ]

elif scenario == "Hidden Leak":

    pressure_values = [
        52.4, 51.8, 45.2,
        44.7, 51.1, 50.6
    ]

    flow_values = [
        118, 121, 148,
        153, 109, 112
    ]

else:

    pressure_values = [
        52.4, 51.8, 32.5,
        31.8, 51.1, 50.6
    ]

    flow_values = [
        118, 121, 205,
        214, 109, 112
    ]

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

# ============================================================
# ANOMALY DETECTION
# ============================================================

baseline_pressure = 52.0
baseline_flow = 120.0

sensors["Pressure Residual"] = (
    sensors["Pressure"] -
    baseline_pressure
)

sensors["Flow Deviation"] = (
    sensors["Flow"] -
    baseline_flow
)

sensors["Pressure Anomaly"] = (
    sensors["Pressure Residual"].abs() > 8
)

sensors["Flow Anomaly"] = (
    sensors["Flow Deviation"].abs() > 30
)

sensors["Anomaly"] = (
    sensors["Pressure Anomaly"] |
    sensors["Flow Anomaly"]
)

anomaly_count = int(
    sensors["Anomaly"].sum()
)

# ============================================================
# LEAK LOCALIZATION
# ============================================================

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

    flow_deviation = max(
        0,
        zone_sensors["Flow"].mean() -
        baseline_flow
    )

    pressure_anomalies = int(
        zone_sensors["Pressure Anomaly"].sum()
    )

    flow_anomalies = int(
        zone_sensors["Flow Anomaly"].sum()
    )

    score = (
        pressure_drop * 0.65
        + flow_deviation * 0.15
        + pressure_anomalies * 4
        + flow_anomalies * 3
    )

    zone_scores[zone] = round(
        score,
        2
    )

suspected_zone = max(
    zone_scores,
    key=zone_scores.get
)

zone_sensors = sensors[
    sensors["Zone"] == suspected_zone
]

pressure_drop = max(
    0,
    baseline_pressure -
    zone_sensors["Pressure"].mean()
)

flow_increase = max(
    0,
    zone_sensors["Flow"].mean() -
    baseline_flow
)

# ============================================================
# SEVERITY
# ============================================================

if scenario == "Normal Network":

    severity = "NONE"

elif pressure_drop >= 15:

    severity = "CRITICAL"

elif pressure_drop >= 7:

    severity = "HIGH"

else:

    severity = "MEDIUM"

# ============================================================
# WATER LOSS + CONFIDENCE
# ============================================================

estimated_loss = round(
    pressure_drop * 12.5 +
    flow_increase * 0.4,
    1
)

if scenario == "Normal Network":

    confidence = 96

else:

    confidence = min(
        99,
        round(
            70 +
            pressure_drop * 1.8 +
            flow_increase * 0.15
        )
    )

# ============================================================
# IMPACT
# ============================================================

affected_population = zones[
    suspected_zone
]["population"]

critical_sites = zones[
    suspected_zone
]["critical_sites"]

pipeline_length = zones[
    suspected_zone
]["pipeline_length"]

# ============================================================
# CREW RESPONSE
# ============================================================

crews = {
    "Crew Alpha": {
        "base": "North Depot",
        "distance": 2.4,
        "specialization": "Pipeline Repair"
    },

    "Crew Bravo": {
        "base": "Central Depot",
        "distance": 0.8,
        "specialization": "Emergency Response"
    },

    "Crew Charlie": {
        "base": "South Depot",
        "distance": 5.1,
        "specialization": "Pipeline Repair"
    }
}

available_crews = crews

recommended_crew = min(
    available_crews,
    key=lambda name:
    available_crews[name]["distance"]
)

crew_distance = crews[
    recommended_crew
]["distance"]

estimated_arrival = round(
    crew_distance * 3.5 + 5,
    1
)

if severity == "CRITICAL":

    isolation_action = (
        f"Immediately isolate the "
        f"{suspected_zone} distribution segment."
    )

    water_saved = round(
        estimated_loss * 0.90,
        1
    )

elif severity == "HIGH":

    isolation_action = (
        f"Prepare isolation of the "
        f"{suspected_zone} segment after inspection."
    )

    water_saved = round(
        estimated_loss * 0.70,
        1
    )

elif severity == "MEDIUM":

    isolation_action = (
        f"Verify telemetry in the "
        f"{suspected_zone} segment before isolation."
    )

    water_saved = round(
        estimated_loss * 0.40,
        1
    )

else:

    isolation_action = (
        "No isolation required. Continue monitoring."
    )

    water_saved = 0

# ============================================================
# HEADER
# ============================================================

status = (
    "NORMAL"
    if scenario == "Normal Network"
    else "INCIDENT DETECTED"
)

st.markdown(
    f"""
    <div class="hero">
        <h1>💧 LeakGuard</h1>
        <p>
            Water Network Intelligence & Incident Response
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

h1, h2, h3 = st.columns(3)

h1.metric(
    "Network Status",
    status
)

h2.metric(
    "Scenario",
    scenario
)

h3.metric(
    "Last Telemetry",
    datetime.now().strftime("%H:%M:%S")
)

# ============================================================
# KPI ROW
# ============================================================

st.divider()

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Estimated Water Loss",
    f"{estimated_loss} L/min"
)

k2.metric(
    "Localization Confidence",
    f"{confidence}%"
)

k3.metric(
    "Affected Population",
    f"{affected_population:,}"
    if scenario != "Normal Network"
    else "0"
)

k4.metric(
    "Incident Severity",
    severity
)

# ============================================================
# INCIDENT OVERVIEW
# ============================================================

st.divider()

if scenario == "Normal Network":

    st.success(
        "✅ Network operating normally. "
        "No significant leak pattern detected."
    )

else:

    st.subheader("🚨 Active Incident")

    a1, a2 = st.columns([1.5, 1])

    with a1:

        st.markdown(
            f"""
            <div class="incident-card">

            <h3>Suspected Leak — {suspected_zone} Zone</h3>

            <p>
            <span class="small-label">
            Detection Evidence
            </span>
            </p>

            <p>
            Pressure residual and flow deviation detected
            across sensors in the affected zone.
            </p>

            <p>
            <b>Pressure drop:</b>
            {pressure_drop:.1f} m
            </p>

            <p>
            <b>Flow increase:</b>
            {flow_increase:.1f} L/min
            </p>

            <p>
            <b>Detection confidence:</b>
            {confidence}%
            </p>

            </div>
            """,
            unsafe_allow_html=True
        )

    with a2:

        st.markdown("### 🎯 Recommended Priority")

        if severity == "CRITICAL":

            st.error(
                "CRITICAL — Immediate response"
            )

        elif severity == "HIGH":

            st.warning(
                "HIGH — Dispatch maintenance crew"
            )

        else:

            st.info(
                "MEDIUM — Verify anomaly"
            )

# ============================================================
# IMPACT ANALYSIS
# ============================================================

st.divider()

st.subheader("🌍 Network Impact")

i1, i2, i3, i4 = st.columns(4)

i1.metric(
    "Population at Risk",
    f"{affected_population:,}"
)

i2.metric(
    "Critical Sites",
    len(critical_sites)
)

i3.metric(
    "Pipeline Segment",
    f"{pipeline_length} km"
)

i4.metric(
    "Water at Risk",
    f"{estimated_loss} L/min"
)

if scenario != "Normal Network":

    st.markdown(
        "**Potentially affected critical locations:**"
    )

    for site in critical_sites:

        st.write(
            f"• {site}"
        )

# ============================================================
# LOCALIZATION
# ============================================================

st.divider()

st.subheader("📍 Leak Localization")

localization_data = pd.DataFrame({
    "Zone": list(zone_scores.keys()),
    "Detection Score": list(
        zone_scores.values()
    )
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

# ============================================================
# NETWORK VISUALIZATION
# ============================================================

st.divider()

st.subheader("🗺️ Network Zone Status")

map_data = pd.DataFrame({
    "Zone": [
        "North",
        "Central",
        "South"
    ],
    "Risk Score": [
        zone_scores["North"],
        zone_scores["Central"],
        zone_scores["South"]
    ]
})

st.bar_chart(
    map_data.set_index("Zone")
)

# ============================================================
# RESPONSE PLANNING
# ============================================================

st.divider()

st.subheader("👷 Response Planning")

if scenario == "Normal Network":

    st.info(
        "No field response is currently required."
    )

else:

    r1, r2, r3, r4 = st.columns(4)

    r1.metric(
        "Recommended Crew",
        recommended_crew
    )

    r2.metric(
        "Crew Distance",
        f"{crew_distance} km"
    )

    r3.metric(
        "Estimated Arrival",
        f"{estimated_arrival} min"
    )

    r4.metric(
        "Potential Water Saved",
        f"{water_saved} L/min"
    )

    st.markdown(
        f"""
        ### 🔧 Recommended Action

        **Dispatch:** {recommended_crew}

        **Specialization:**
        {crews[recommended_crew]["specialization"]}

        **Isolation plan:**
        {isolation_action}
        """
    )

    if st.button(
        "👷 Dispatch Recommended Crew",
        use_container_width=True
    ):

        st.success(
            f"{recommended_crew} dispatched to "
            f"{suspected_zone} Zone."
        )

# ============================================================
# INCIDENT LIFECYCLE
# ============================================================

st.divider()

st.subheader("📋 Incident Response Lifecycle")

if scenario == "Normal Network":

    lifecycle = pd.DataFrame({
        "Stage": [
            "Detection",
            "Localization",
            "Response",
            "Resolution"
        ],
        "Status": [
            "Monitoring",
            "Standby",
            "Not Required",
            "Not Required"
        ]
    })

else:

    lifecycle = pd.DataFrame({
        "Stage": [
            "Detection",
            "Localization",
            "Acknowledgement",
            "Crew Dispatch",
            "Isolation",
            "Resolution"
        ],
        "Status": [
            "✓ Complete",
            "✓ Complete",
            "Ready",
            "Ready",
            "Recommended",
            "Pending"
        ]
    })

st.dataframe(
    lifecycle,
    use_container_width=True,
    hide_index=True
)

# ============================================================
# TELEMETRY
# ============================================================

st.divider()

st.subheader("📡 Live Network Telemetry")

telemetry = sensors[
    [
        "Sensor",
        "Zone",
        "Pressure",
        "Flow",
        "Pressure Residual",
        "Flow Deviation",
        "Anomaly"
    ]
].copy()

telemetry[
    "Pressure"
] = telemetry[
    "Pressure"
].round(1)

telemetry[
    "Pressure Residual"
] = telemetry[
    "Pressure Residual"
].round(1)

telemetry[
    "Flow Deviation"
] = telemetry[
    "Flow Deviation"
].round(1)

st.dataframe(
    telemetry,
    use_container_width=True,
    hide_index=True
)

# ============================================================
# EVIDENCE
# ============================================================

st.divider()

st.subheader("🔎 Detection Evidence")

e1, e2 = st.columns(2)

with e1:

    st.markdown("### Pressure Residual")

    pressure_chart = sensors[
        ["Sensor", "Pressure Residual"]
    ].set_index("Sensor")

    st.bar_chart(
        pressure_chart
    )

with e2:

    st.markdown("### Flow Deviation")

    flow_chart = sensors[
        ["Sensor", "Flow Deviation"]
    ].set_index("Sensor")

    st.bar_chart(
        flow_chart
    )

st.caption(
    "LeakGuard combines pressure and flow behaviour "
    "to identify abnormal network conditions."
)

# ============================================================
# EXPLAINABILITY
# ============================================================

st.divider()

st.subheader("🧠 Why did LeakGuard flag this incident?")

if scenario == "Normal Network":

    st.info(
        "No incident explanation is required because "
        "the current telemetry remains within expected limits."
    )

else:

    reasons = []

    if pressure_drop > 0:

        reasons.append(
            f"Pressure dropped by {pressure_drop:.1f} m "
            f"in the {suspected_zone} zone."
        )

    if flow_increase > 0:

        reasons.append(
            f"Flow increased by {flow_increase:.1f} L/min "
            f"relative to the baseline."
        )

    if anomaly_count > 0:

        reasons.append(
            f"{anomaly_count} sensor readings crossed "
            "the anomaly threshold."
        )

    for reason in reasons:

        st.write(
            f"• {reason}"
        )

    st.success(
        f"These signals produce a localization confidence "
        f"of **{confidence}%** for the {suspected_zone} zone."
    )

# ============================================================
# OPERATOR SUMMARY
# ============================================================

st.divider()

st.subheader("🧑‍💻 Operator Summary")

if scenario == "Normal Network":

    st.info(
        "Continue monitoring. No immediate field action required."
    )

else:

    st.markdown(
        f"""
        **Incident:** Suspected pipeline leak

        **Location:** {suspected_zone} Zone

        **Severity:** {severity}

        **Water loss:** {estimated_loss} L/min

        **Population potentially affected:** {affected_population:,}

        **Recommended crew:** {recommended_crew}

        **Estimated arrival:** {estimated_arrival} min

        **Recommended action:** {isolation_action}
        """
    )

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "LeakGuard • Water Network Intelligence & Incident Response • "
    "Hack Devengers 2.0"
)
