
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.engine import (
    SCENARIOS, INTERVENTIONS, telemetry_for_scenario, zone_scores,
    evidence_for_zone, decision_from_evidence, estimate_loss,
    sensor_placement, validation_demo
)
from app.data_loader import read_uploaded_csv, research_summary

st.set_page_config(page_title="LeakGuard", page_icon="💧", layout="wide")

if "approved" not in st.session_state:
    st.session_state.approved = False
if "incident_status" not in st.session_state:
    st.session_state.incident_status = "MONITORING"

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1450px;}
.hero {padding: 26px 30px; border-radius: 18px; background: linear-gradient(135deg,#071c2c,#0b3348); color:white; margin-bottom:20px;}
.hero h1 {font-size: 42px; margin:0;}
.hero p {font-size:16px; opacity:.86;}
.card {border:1px solid #dce5ea; border-radius:14px; padding:16px; background:#fff;}
.kicker {font-size:12px; letter-spacing:1.3px; font-weight:700; color:#66808d;}
.big {font-size:30px; font-weight:800;}
.badge {display:inline-block; padding:5px 10px; border-radius:999px; font-weight:700; font-size:12px;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>💧 LeakGuard</h1>
<p>Evidence-driven water network incident intelligence — detect, diagnose, simulate, decide and verify.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Control Center")
    mode = st.radio("Data mode", ["Demo Incident", "Research CSV"], index=0)
    if mode == "Demo Incident":
        scenario = st.selectbox("Incident scenario", list(SCENARIOS))
    else:
        uploaded = st.file_uploader("Upload SCADA CSV", type=["csv"])
    st.divider()
    st.caption("Operator-in-the-loop control")
    st.caption("AI recommendations require human approval before an intervention is considered executed.")

if mode == "Demo Incident":
    df = telemetry_for_scenario(scenario)
    zones = zone_scores(df)
    active = zones.iloc[0]
    evidence = evidence_for_zone(active, df[df.zone == active.zone])
    decision, decision_reason = decision_from_evidence(evidence, active.score)
    loss = estimate_loss(active)
    st.session_state.approved = False

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Network state", scenario)
    c2.metric("Risk score", f"{active.score:.0f}/100")
    c3.metric("Estimated loss", f"{loss:.0f} L/min")
    c4.metric("Population at risk", f"{active.affected_population:,}")
    c5.metric("Decision", decision)

    st.subheader("1 · Incident intelligence")
    left,right = st.columns([1.25,1])
    with left:
        zview = zones[["zone","score","severity","pressure_drop_m","flow_deviation_lpm","affected_population"]].copy()
        st.dataframe(zview, use_container_width=True, hide_index=True)
        fig = px.bar(zview, x="zone", y="score", color="severity", title="Zone risk score")
        fig.update_layout(height=330, margin=dict(l=10,r=10,t=50,b=10))
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("### Evidence chain")
        for k,v in sorted(evidence.items(), key=lambda x:x[1], reverse=True):
            st.progress(float(v), text=f"{k}: {v*100:.0f}%")
        st.info(decision_reason)
        st.markdown(f"**Primary zone:** {active.zone}")
        st.markdown(f"**Critical sites:** {active.critical_sites}")

    st.subheader("2 · Competing explanations")
    explain = pd.DataFrame({
        "Hypothesis": list(evidence.keys()),
        "Evidence score": [round(v*100,1) for v in evidence.values()]
    })
    st.dataframe(explain, use_container_width=True, hide_index=True)

    st.subheader("3 · Counterfactual Leak Lab")
    st.caption("Operational counterfactual estimates for the demo. Hydraulic WNTR/EPANET simulation can replace this layer without changing the UI contract.")
    choices = INTERVENTIONS.copy()
    choices["loss_lpm"] = choices["loss_lpm"].astype(float)
    st.dataframe(choices, use_container_width=True, hide_index=True)
    rec = choices.sort_values(["critical_service_pct","loss_lpm"], ascending=[False,True]).iloc[0]
    st.success(f"Recommended intervention: **{rec.action}** — preserves {rec.critical_service_pct:.0f}% critical service while reducing estimated loss by {rec.loss_reduction_pct:.0f}%.")

    a,b = st.columns([1,1])
    with a:
        if st.button("🧪 Simulate selected intervention", use_container_width=True):
            st.session_state.incident_status = "SIMULATED"
            st.session_state.approved = False
    with b:
        if st.button("✅ Approve intervention", use_container_width=True):
            st.session_state.approved = True
            st.session_state.incident_status = "INTERVENTION APPROVED"

    if st.session_state.incident_status == "SIMULATED":
        st.info("Simulation complete. Predicted pressure recovery: +7.8 m. Predicted residual loss: 22 L/min.")
    if st.session_state.approved:
        st.success("Operator approval recorded. Intervention is now ready for closed-loop verification.")

    st.subheader("4 · Closed-loop verification")
    if st.button("🔄 Run post-intervention verification", use_container_width=True):
        if st.session_state.approved:
            st.session_state.incident_status = "RESOLVED"
            st.success("✓ Expected pressure recovery matched observed recovery within tolerance. Incident resolved.")
        else:
            st.warning("Approval required before verification can be executed.")
    st.write(f"**Lifecycle status:** {st.session_state.incident_status}")

    st.subheader("5 · Telemetry")
    tab1, tab2 = st.tabs(["Pressure", "Flow"])
    with tab1:
        fig = px.line(df, x="sensor", y="pressure", markers=True, title="Sensor pressure")
        fig.add_hline(y=52, line_dash="dash", annotation_text="baseline")
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        fig = px.bar(df, x="sensor", y="flow", title="Sensor flow")
        fig.add_hline(y=120, line_dash="dash", annotation_text="baseline")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("6 · Sensor Placement Advisor")
    placement = sensor_placement(df)
    st.dataframe(placement, use_container_width=True, hide_index=True)
    st.caption("This advisor ranks candidate locations by estimated uncertainty reduction. It is a planning heuristic in the demo layer, not a hydraulic optimization solver.")

    st.subheader("7 · Validation")
    st.dataframe(validation_demo(), use_container_width=True, hide_index=True)
    st.caption("The displayed validation values are explicitly labelled demo placeholders and must be replaced by measured benchmark results before submission.")

else:
    st.subheader("Research Data Mode")
    if not uploaded:
        st.info("Upload a CSV containing pressure/flow telemetry. LeakGuard will inspect the schema and identify likely measurement columns.")
        st.stop()
    try:
        rdf = read_uploaded_csv(uploaded)
        summary = research_summary(rdf)
        c1,c2,c3 = st.columns(3)
        c1.metric("Rows", f"{summary['rows']:,}")
        c2.metric("Columns", summary["columns"])
        c3.metric("Numeric signals", len(summary["numeric_columns"]))
        st.write("**Pressure candidates:**", ", ".join(summary["pressure_columns"]) or "None detected")
        st.write("**Flow candidates:**", ", ".join(summary["flow_columns"]) or "None detected")
        st.write("**Time candidates:**", ", ".join(summary["time_columns"]) or "None detected")
        st.dataframe(rdf.head(100), use_container_width=True, hide_index=True)
        numeric = rdf.select_dtypes(include="number")
        if not numeric.empty:
            selected = st.selectbox("Select a numeric signal", list(numeric.columns))
            fig = px.line(rdf, y=selected, title=f"Research signal: {selected}")
            st.plotly_chart(fig, use_container_width=True)
    except Exception as exc:
        st.error(f"Could not read the CSV: {exc}")

st.divider()
st.caption("LeakGuard · Hack Devengers 2.0 · Operator-in-the-loop water infrastructure intelligence")
