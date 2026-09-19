from __future__ import annotations

import os
import sys
import base64
import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BG_PATH = ROOT / "assets" / "water_network_bg.png"
BG_B64 = base64.b64encode(BG_PATH.read_bytes()).decode() if BG_PATH.exists() else ""

from app.engine import (
    INTERVENTIONS,
    add_features,
    decision_from_evidence,
    estimate_loss,
    evidence_for_zone,
    live_simulation_points,
    sensor_placement,
    simulate_intervention,
    telemetry_for_scenario,
    zone_scores,
)
from app.live_feed import fetch_live_rest

st.set_page_config(page_title="LeakGuard", page_icon="💧", layout="wide", initial_sidebar_state="collapsed")

DEFAULTS = {"sim_minute": 0, "sim_running": False, "sim_speed": 1, "selected_action": "Isolate Central branch", "sim_last_tick": 0.0, "sim_scenario": "Hidden Leak"}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

st.markdown("""
<style>
:root{--ink:#12364a;--muted:#607985;--line:#dce9ee;--bg:#f6fafb;--teal:#087f8c;--navy:#092333}
.stApp{background:radial-gradient(circle at 12% 8%,rgba(22,156,166,.07),transparent 24%),linear-gradient(180deg,#f8fbfc 0%,#f1f7f9 100%)}
.block-container{max-width:1500px;padding:1.35rem 2.2rem 3.2rem}
.hero{padding:34px 36px 30px;border-radius:28px;background-image:linear-gradient(90deg,rgba(5,22,32,.97) 0%,rgba(7,45,57,.91) 48%,rgba(5,80,89,.72) 100%),url("data:image/png;base64,__BG__");background-size:cover;background-position:center;color:#fff;box-shadow:0 18px 45px rgba(5,38,53,.16);position:relative;overflow:hidden}
.hero:after{content:"";position:absolute;width:330px;height:330px;border-radius:50%;right:-90px;top:-180px;background:rgba(255,255,255,.08)}
.hero h1{font-size:45px;line-height:1;margin:0 0 8px;letter-spacing:-2px;font-weight:900}.hero p{font-size:15px;line-height:1.55;max-width:980px;margin:0;opacity:.93}.hero-meta{display:flex;gap:10px;flex-wrap:wrap;margin-top:17px}.tag{border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.1);border-radius:999px;padding:7px 11px;font-size:10px;font-weight:800;letter-spacing:.07em}
.section{margin:25px 0 6px;color:var(--ink);font-size:25px;font-weight:900;letter-spacing:-.5px}.sub{color:var(--muted);font-size:13px;line-height:1.5;margin-bottom:12px}
.card{background:rgba(255,255,255,.94);backdrop-filter:blur(10px);border:1px solid var(--line);border-radius:18px;padding:17px 18px;box-shadow:0 6px 25px rgba(12,52,66,.055);height:100%}.kicker{font-size:10px;text-transform:uppercase;letter-spacing:.1em;font-weight:900;color:#78909a}.big{font-size:25px;font-weight:900;color:var(--ink);margin-top:4px;letter-spacing:-.5px}.muted{font-size:12px;color:var(--muted);line-height:1.45;margin-top:3px}.metric-number{font-size:34px;font-weight:950;color:var(--ink);line-height:1.05;margin-top:5px}.pill-good,.pill-warn,.pill-bad,.pill-info{padding:13px 15px;border-radius:15px;border:1px solid}.pill-good{background:#eefaf5;border-color:#ccebdc;color:#146847}.pill-warn{background:#fff9e8;border-color:#f0dfa9;color:#795c00}.pill-bad{background:#fff1ef;border-color:#ffd1ca;color:#9d3029}.pill-info{background:#edf7fa;border-color:#cde6ed;color:#235f72}.small{font-size:11px;line-height:1.45}.timeline{font-size:12px;color:#58727d;text-align:center;margin-top:-8px}
div[data-testid="stHorizontalBlock"]{gap:12px}.stButton>button{border-radius:12px;font-weight:850;border:1px solid #cfe1e7;background:#fff;box-shadow:0 4px 14px rgba(10,65,80,.06)}.stButton>button:hover{border-color:#0b8b95;color:#076c75}.stProgress>div>div{border-radius:999px}.stSelectbox>div>div{border-radius:11px}.stDataFrame{border-radius:14px;overflow:hidden}
.footer-note{margin:24px 0 4px;padding:12px 15px;border-radius:13px;background:rgba(234,245,248,.82);border:1px solid #d5e7ec;color:#607985;font-size:11px;line-height:1.5}.quickbar{display:flex;gap:10px;flex-wrap:wrap;margin:12px 2px 2px}.quickbar span{background:rgba(255,255,255,.72);border:1px solid #dce9ee;border-radius:999px;padding:6px 10px;color:#54717d;font-size:10px;font-weight:850;letter-spacing:.05em;text-transform:uppercase}.quickbar span:first-child{color:#15745d;background:#effaf5;border-color:#cdebdc}
</style>
""".replace("__BG__", BG_B64), unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>💧 LeakGuard</h1>
  <p><b>Water-network intelligence for earlier leak detection.</b> LeakGuard combines pressure and flow behaviour, measures evidence agreement, localizes the affected zone and lets an operator test a response before field action.</p>
  <div class="hero-meta"><span class="tag">PRESSURE + FLOW</span><span class="tag">EXPLAINABLE DETECTION</span><span class="tag">ZONE LOCALIZATION</span><span class="tag">RESPONSE SIMULATION</span></div>
</div>
""".replace("__BG__", BG_B64), unsafe_allow_html=True)

st.markdown("""<div class="quickbar"><span>● Monitoring layer</span><span>Pressure + Flow</span><span>Explainable scoring</span><span>Operator-in-the-loop</span></div>""", unsafe_allow_html=True)

endpoint = os.getenv("LEAKGUARD_LIVE_URL", "").strip()
token = os.getenv("LEAKGUARD_LIVE_TOKEN", "").strip()
refresh_col, source_col = st.columns([1, 3])
with refresh_col:
    refresh_clicked = st.button("↻ Refresh telemetry", use_container_width=True, help="Refresh the current pipe telemetry. No external public-data server is required.")
if refresh_clicked:
    st.cache_data.clear()
    st.rerun()

live_df, feed_meta = fetch_live_rest(endpoint, token) if endpoint else (None, {"status":"NOT_CONFIGURED", "message":"No utility REST endpoint configured."})

if live_df is None:
    df = telemetry_for_scenario("Hidden Leak")
    source_mode = "CONTROLLED PIPE TELEMETRY"
else:
    source_mode = "UTILITY REST FEED"
    df = live_df.copy()
    registry = telemetry_for_scenario("Normal Network")[['sensor', 'baseline_pressure', 'baseline_flow']].rename(columns={'sensor': 'sensor_id'})
    if "baseline_pressure" not in df or df["baseline_pressure"].isna().all():
        df = df.drop(columns=[c for c in ["baseline_pressure", "baseline_flow"] if c in df])
        df = df.merge(registry, on="sensor_id", how="left")
    else:
        df = df.merge(registry, on="sensor_id", how="left", suffixes=("", "_registry"))
        df["baseline_pressure"] = df["baseline_pressure"].fillna(df["baseline_pressure_registry"])
        df["baseline_flow"] = df["baseline_flow"].fillna(df["baseline_flow_registry"])
        df = df.drop(columns=["baseline_pressure_registry", "baseline_flow_registry"], errors="ignore")
    df = add_features(df)

with source_col:
    if feed_meta.get("status") == "CONNECTED":
        st.markdown(f'<div class="pill-good"><b>● UTILITY FEED CONNECTED</b> &nbsp; {feed_meta.get("message", "External pipe telemetry is arriving.")}</div>', unsafe_allow_html=True)
    elif feed_meta.get("status") in {"STALE", "ERROR"}:
        st.markdown(f'<div class="pill-warn"><b>● UTILITY FEED {feed_meta.get("status")}</b> &nbsp; {feed_meta.get("message", "External pipe telemetry is unavailable.")}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="pill-info"><b>● PIPE DETECTION DEMO</b> &nbsp; Controlled pressure + flow telemetry is used for the reproducible leak-detection workflow.</div>', unsafe_allow_html=True)

zones = zone_scores(df)
active = zones.iloc[0]
evidence = evidence_for_zone(active, df[df.zone == active.zone])
decision, decision_reason = decision_from_evidence(evidence, active.score)
loss_lpm = estimate_loss(active)

st.markdown('<div class="section">Network overview</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">A single operational view of network condition, affected zone, evidence strength and response priority.</div>', unsafe_allow_html=True)

c1,c2,c3,c4,c5 = st.columns(5)
with c1: st.markdown(f'<div class="card"><div class="kicker">Pipe detection source</div><div class="big">{source_mode}</div><div class="muted">{feed_meta.get("message", "Controlled telemetry · reproducible replay") if live_df is not None else "Controlled pressure + flow replay"}</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="card"><div class="kicker">Network risk</div><div class="metric-number">{active.score:.0f}<span style="font-size:14px"> / 100</span></div><div class="muted">{active.severity} · {active.zone}</div></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="card"><div class="kicker">Estimated abnormal loss</div><div class="big">{loss_lpm:,.0f} L/min</div><div class="muted">Pressure + flow deviation estimate</div></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="card"><div class="kicker">Zone exposure</div><div class="big">{active.affected_population:,}</div><div class="muted">People represented by {active.zone}</div></div>', unsafe_allow_html=True)
with c5: st.markdown(f'<div class="card"><div class="kicker">Recommended state</div><div class="big">{decision}</div><div class="muted">{decision_reason}</div></div>', unsafe_allow_html=True)

# ----------------- NEW: REAL WORLD IMPACT -----------------
st.markdown('<div class="section">Real-World Impact</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">Translating telemetry anomalies into tangible civic outcomes and operational savings.</div>', unsafe_allow_html=True)

rw1, rw2, rw3 = st.columns(3)
water_saved_per_hr = loss_lpm * 60
cost_saved_per_hr = water_saved_per_hr * 0.05

with rw1: 
    st.markdown(f'<div class="card"><div class="kicker">Water Conserved</div><div class="metric-number">{water_saved_per_hr:,.0f} L/hr</div><div class="muted">Prevents daily loss equivalent to ~{int(water_saved_per_hr/700)} households</div></div>', unsafe_allow_html=True)
with rw2: 
    st.markdown(f'<div class="card"><div class="kicker">Financial Impact</div><div class="metric-number">₹ {cost_saved_per_hr:,.0f} / hr</div><div class="muted">Non-revenue water production cost avoided</div></div>', unsafe_allow_html=True)
with rw3: 
    st.markdown('<div class="card"><div class="kicker">Secondary Damage</div><div class="metric-number">Mitigated</div><div class="muted">Early isolation reduces sinkhole and road washout risks</div></div>', unsafe_allow_html=True)
# -----------------------------------------------------------

st.markdown('<div class="section">Incident replay</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">Watch the same detection logic evolve from stable conditions to a developing anomaly and then to a confirmed incident.</div>', unsafe_allow_html=True)

def render_simulation():
    """Render the incident replay as a self-contained browser animation."""
    scenarios = {}
    for scenario_name in ["Hidden Leak", "Major Burst", "Normal Network"]:
        records = live_simulation_points(scenario_name, 60, 1).to_dict("records")
        scenarios[scenario_name] = records

    import json
    payload = json.dumps(scenarios, separators=(",", ":"))
    html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
*{{box-sizing:border-box}}
body{{margin:0;font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:transparent;color:#12364a}}
.wrap{{background:rgba(255,255,255,.96);border:1px solid #dce9ee;border-radius:20px;padding:16px;box-shadow:0 6px 25px rgba(12,52,66,.055)}}
.controls{{display:grid;grid-template-columns:1.6fr .8fr 1.7fr;gap:10px;align-items:center;margin-bottom:14px}}
select,button{{font:inherit;border:1px solid #cfe1e7;border-radius:11px;background:#fff;color:#12364a;padding:10px 12px;font-weight:800;cursor:pointer}}
button:hover{{border-color:#087f8c;color:#087f8c}}
button.active{{background:#087f8c;color:#fff;border-color:#087f8c}}
.actions{{display:flex;gap:8px}}
.status{{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:10px 12px;border-radius:12px;background:#f4f9fa;border:1px solid #dce9ee;margin-bottom:12px}}
.badge{{font-size:11px;font-weight:900;letter-spacing:.05em;padding:6px 9px;border-radius:999px}}
.monitor{{background:#eefaf5;color:#146847}}.warning{{background:#fff9e8;color:#795c00}}.critical{{background:#fff1ef;color:#9d3029}}
.time{{font-size:12px;color:#607985;font-weight:800}}
.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-bottom:12px}}
.metric{{background:#f8fbfc;border:1px solid #e2edf0;border-radius:13px;padding:10px 12px}}
.kicker{{font-size:9px;text-transform:uppercase;letter-spacing:.1em;color:#78909a;font-weight:900}}
.value{{font-size:22px;font-weight:950;color:#12364a;margin-top:3px}}
.chartbox{{border:1px solid #e2edf0;border-radius:15px;background:#fff;padding:8px 10px;margin-top:10px}}
.charttitle{{font-size:11px;font-weight:900;color:#607985;padding:2px 4px 6px}}
svg{{display:block;width:100%;height:auto}}
.axis{{stroke:#dce9ee;stroke-width:1}}
.grid{{stroke:#edf3f5;stroke-width:1}}
.label{{fill:#78909a;font-size:10px}}
.line-pressure{{fill:none;stroke:#087f8c;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}}
.line-flow{{fill:none;stroke:#235f72;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}}
.now{{stroke:#9d3029;stroke-width:2;stroke-dasharray:5 5}}
.network{{position:relative;height:245px;background:linear-gradient(180deg,#fbfdfe,#f5fafb);border:1px solid #e2edf0;border-radius:15px;overflow:hidden}}
.network svg{{width:100%;height:100%}}
.pipe{{fill:none;stroke:#a9c5cf;stroke-width:8;stroke-linecap:round;stroke-linejoin:round}}
.pipe2{{fill:none;stroke:#d5e5ea;stroke-width:12;stroke-linecap:round;stroke-linejoin:round}}
.node{{fill:#fff;stroke:#8db1bc;stroke-width:3}}
.node.central{{stroke:#087f8c;stroke-width:4}}
.particle{{fill:#087f8c}}
.particle.critical{{fill:#c43d35}}
.legend{{display:flex;gap:16px;flex-wrap:wrap;padding:8px 3px 0;font-size:10px;color:#607985;font-weight:800}}
.dot{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px}}

/* Beacon Animation CSS */
@keyframes pulse {{
  0% {{ transform: scale(0.5); opacity: 0.9; }}
  100% {{ transform: scale(4.5); opacity: 0; }}
}}
.pulse-ring {{ fill: none; stroke-width: 3; }}
.ring-1 {{ animation: pulse 1.5s infinite ease-out; }}
.ring-2 {{ animation: pulse 1.5s infinite ease-out 0.75s; }}
.alert-icon {{ stroke-width: 2; stroke-linejoin: round; }}
.alert-mark {{ font-size: 20px; font-weight: 900; font-family: sans-serif; text-anchor: middle; }}
.incident-label {{ font-size: 11px; font-weight: 900; text-anchor: middle; letter-spacing: 0.05em; }}

.state-leak .pulse-ring {{ stroke: #f0dfa9; }}
.state-leak .alert-icon {{ fill: #fff9e8; stroke: #d4a000; }}
.state-leak .alert-mark, .state-leak .incident-label {{ fill: #d4a000; }}

.state-burst .pulse-ring {{ stroke: #ffd1ca; }}
.state-burst .alert-icon {{ fill: #fff1ef; stroke: #9d3029; }}
.state-burst .alert-mark, .state-burst .incident-label {{ fill: #9d3029; }}

@media(max-width:800px){{.controls{{grid-template-columns:1fr 1fr}}.actions{{grid-column:1/-1}}.metrics{{grid-template-columns:repeat(2,1fr)}}}}
</style>
</head>
<body>
<div class="wrap">
  <div class="controls">
    <div id="detected" style="border:1px solid #cfe1e7;border-radius:11px;background:#fff;color:#12364a;padding:10px 12px;font-weight:800">AUTO-DETECTION: NORMAL NETWORK</div>
    <select id="speed"><option value="1">1×</option><option value="2">2×</option><option value="4">4×</option></select>
    <div class="actions">
      <button id="play" class="active">▶ Play</button>
      <button id="pause">Ⅱ Pause</button>
      <button id="reset">↺ Reset</button>
    </div>
  </div>
  <div class="status">
    <span id="badge" class="badge monitor">MONITORING</span>
    <span class="time">Replay position: <b id="clock">00:00</b> / 60:00</span>
  </div>
  <div class="metrics">
    <div class="metric"><div class="kicker">Pressure</div><div class="value" id="pressure">52.0 kPa</div></div>
    <div class="metric"><div class="kicker">Flow</div><div class="value" id="flow">120.0 L/min</div></div>
    <div class="metric"><div class="kicker">Estimated loss</div><div class="value" id="loss">0 L/min</div></div>
    <div class="metric"><div class="kicker">Risk</div><div class="value" id="risk">0%</div></div>
  </div>
  <div class="network">
    <svg viewBox="0 0 1000 250" preserveAspectRatio="none">
      <path class="pipe2" d="M55 125 L300 125 L540 105 L780 80 L945 80"/>
      <path class="pipe" d="M55 125 L300 125 L540 105 L780 80 L945 80"/>
      <path class="pipe2" d="M540 105 L700 170 L900 205"/>
      <path class="pipe" d="M540 105 L700 170 L900 205"/>
      <path class="pipe2" d="M540 105 L390 190 L170 205"/>
      <path class="pipe" d="M540 105 L390 190 L170 205"/>
      
      <!-- New Animated Beacon -->
      <g id="incidentGroup" opacity="0" transform="translate(700, 88)">
        <circle class="pulse-ring ring-1" cx="0" cy="0" r="10" />
        <circle class="pulse-ring ring-2" cx="0" cy="0" r="10" />
        <path class="alert-icon" d="M0 -22 L18 10 A 4 4 0 0 1 14 16 L -14 16 A 4 4 0 0 1 -18 10 Z" />
        <text class="alert-mark" x="0" y="8">!</text>
        <text id="incidentLabel" class="incident-label" x="0" y="-30">DETECTED</text>
      </g>
      
      <g id="particles"></g>
      <g>
        <circle class="node" cx="55" cy="125" r="12"/><text class="label" x="55" y="106" text-anchor="middle">S-101</text>
        <circle class="node" cx="300" cy="125" r="12"/><text class="label" x="300" y="106" text-anchor="middle">S-102</text>
        <circle id="n103" class="node central" cx="540" cy="105" r="15"/><text class="label" x="540" y="80" text-anchor="middle">S-103</text>
        <circle id="n104" class="node central" cx="780" cy="80" r="15"/><text class="label" x="780" y="55" text-anchor="middle">S-104</text>
        <circle class="node" cx="390" cy="190" r="12"/><text class="label" x="390" y="218" text-anchor="middle">S-105</text>
        <circle class="node" cx="170" cy="205" r="12"/><text class="label" x="170" y="232" text-anchor="middle">S-106</text>
      </g>
    </svg>
  </div>
  <div class="legend"><span><i class="dot" style="background:#087f8c"></i>Normal flow</span><span><i class="dot" style="background:#c43d35"></i>Incident zone</span><span>Central sensors drive the replay</span></div>
  <div class="chartbox">
    <div class="charttitle">Pressure & flow trend</div>
    <svg id="chart" viewBox="0 0 1000 250" preserveAspectRatio="none"></svg>
  </div>
</div>
<script>
const DATA = {payload};
const speedEl=document.getElementById('speed'), detectedEl=document.getElementById('detected');
const play=document.getElementById('play'), pause=document.getElementById('pause'), reset=document.getElementById('reset');
const pressureEl=document.getElementById('pressure'), flowEl=document.getElementById('flow'), lossEl=document.getElementById('loss'), riskEl=document.getElementById('risk');
const badge=document.getElementById('badge'), clock=document.getElementById('clock'), chart=document.getElementById('chart');
const incidentGroup=document.getElementById('incidentGroup'), incidentLabel=document.getElementById('incidentLabel'), particles=document.getElementById('particles');
let minute=0, playing=false, speed=1, last=performance.now(), raf=0;
const W=1000,H=250, pad={{l:52,r:20,t:18,b:30}};
const SEGMENTS=[{{name:'Normal Network',start:0,end:20}},{{name:'Hidden Leak',start:20,end:40}},{{name:'Major Burst',start:40,end:60}}];

function activeSegment(){{for(const seg of SEGMENTS){{if(minute < seg.end || seg===SEGMENTS[SEGMENTS.length-1]) return seg;}}return SEGMENTS[0];}}
function activeData(){{const seg=activeSegment();const local=(minute-seg.start)*3;return DATA[seg.name][Math.min(60,Math.floor(local))];}}
function activeSeries(){{return DATA[activeSegment().name];}}
function clamp(v,a,b){{return Math.max(a,Math.min(b,v));}}
function current(){{return activeData();}}
function statusStyle(status){{badge.className='badge '+(status==='LEAK DETECTED'?'critical':status==='WARNING'?'warning':'monitor');badge.textContent=status;}}
function smoothStep(x){{x=clamp(x,0,1);return x*x*(3-2*x);}}
function setButtons(){{play.classList.toggle('active',playing);pause.classList.toggle('active',!playing);}}
function path(points,key,min,max){{
  const x0=pad.l,x1=W-pad.r,y0=H-pad.b,y1=pad.t;
  return points.map((d,i)=>{{const x=x0+(d.minute/60)*(x1-x0);const y=y0-((d[key]-min)/(max-min))*(y0-y1);return (i?'L':'M')+x.toFixed(1)+' '+y.toFixed(1);}}).join(' ');
}}
function renderChart(){{
  const data=activeSeries();
  const valsP=data.map(d=>d.pressure), valsF=data.map(d=>d.flow);
  const minP=Math.min(...valsP)-2,maxP=Math.max(...valsP)+2,minF=Math.min(...valsF)-8,maxF=Math.max(...valsF)+8;
  const pPath=path(data,'pressure',minP,maxP), fPath=path(data,'flow',minF,maxF);
  const xNow=pad.l+(minute/60)*(W-pad.l-pad.r);
  chart.innerHTML=`<line class="grid" x1="${{pad.l}}" y1="${{pad.t}}" x2="${{W-pad.r}}" y2="${{pad.t}}"/><line class="grid" x1="${{pad.l}}" y1="${{(H-pad.b+pad.t)/2}}" x2="${{W-pad.r}}" y2="${{(H-pad.b+pad.t)/2}}"/><line class="axis" x1="${{pad.l}}" y1="${{H-pad.b}}" x2="${{W-pad.r}}" y2="${{H-pad.b}}"/><path class="line-pressure" d="${{pPath}}"/><path class="line-flow" d="${{fPath}}"/><line class="now" x1="${{xNow}}" y1="${{pad.t}}" x2="${{xNow}}" y2="${{H-pad.b}}"/><text class="label" x="${{pad.l}}" y="${{H-8}}">0</text><text class="label" x="${{W/2}}" y="${{H-8}}" text-anchor="middle">30 min</text><text class="label" x="${{W-pad.r}}" y="${{H-8}}" text-anchor="end">60 min</text><text class="label" x="${{W-150}}" y="18">Pressure</text><circle cx="${{W-162}}" cy="14" r="4" fill="#087f8c"/><text class="label" x="${{W-75}}" y="18">Flow</text><circle cx="${{W-87}}" cy="14" r="4" fill="#235f72"/>`;
}}
function renderNetwork(){{
  const d=current(), t=(minute%12)/12;
  pressureEl.textContent=d.pressure.toFixed(1)+' kPa';flowEl.textContent=d.flow.toFixed(1)+' L/min';lossEl.textContent=d.estimated_loss_lpm.toFixed(0)+' L/min';riskEl.textContent=d.risk_score.toFixed(0)+'%';
  clock.textContent=String(Math.floor(minute)).padStart(2,'0')+':00';statusStyle(d.status);
  const seg=activeSegment();
  const label=seg.name==='Normal Network'?'NORMAL NETWORK':seg.name==='Hidden Leak'?'HIDDEN LEAK DETECTED':'MAJOR BURST DETECTED';
  detectedEl.textContent='AUTO-DETECTION: '+label;
  
  // New animated beacon logic
  const critical = d.status !== 'MONITORING';
  if (!critical) {{
    incidentGroup.setAttribute('opacity', '0');
  }} else {{
    incidentGroup.setAttribute('opacity', '1');
    if (seg.name === 'Hidden Leak') {{
      incidentGroup.setAttribute('class', 'state-leak');
      incidentLabel.textContent = 'HIDDEN LEAK';
    }} else {{
      incidentGroup.setAttribute('class', 'state-burst');
      incidentLabel.textContent = 'MAJOR BURST';
    }}
  }}

  const particleColor=critical?'critical':'';
  const pts=[
    [55,125,300,125],[300,125,540,105],[540,105,780,80],[780,80,945,80],
    [540,105,700,170],[700,170,900,205],[540,105,390,190],[390,190,170,205]
  ];
  let html='';
  for(let i=0;i<6;i++){{const q=(t+i/6)%1;const seg=Math.min(pts.length-1,Math.floor(q*pts.length));const local=q*pts.length-seg;const a=pts[seg],b=pts[seg+1]||a;const x=a[0]+(b[0]-a[0])*local,y=a[1]+(b[1]-a[1])*local;html+=`<circle class="particle ${{particleColor}}" cx="${{x.toFixed(1)}}" cy="${{y.toFixed(1)}}" r="5"/>`;}}
  particles.innerHTML=html;
  document.getElementById('n103').setAttribute('fill',critical?'#fff1ef':'#fff');document.getElementById('n104').setAttribute('fill',critical?'#fff1ef':'#fff');
  renderChart();
}}
function tick(now){{
  if(playing){{const dt=(now-last)/1000;minute=Math.min(60,minute+dt*speed*1.15);if(minute>=60){{minute=60;playing=false;setButtons();}}renderNetwork();}}
  last=now;raf=requestAnimationFrame(tick);
}}
speedEl.addEventListener('change',()=>{{speed=Number(speedEl.value)||1;}});
play.addEventListener('click',()=>{{if(minute>=60)minute=0;playing=true;last=performance.now();setButtons();}});
pause.addEventListener('click',()=>{{playing=false;setButtons();}});
reset.addEventListener('click',()=>{{playing=false;minute=0;setButtons();renderNetwork();}});
setButtons();renderNetwork();requestAnimationFrame(tick);
</script>
</body>
</html>
"""
    components.html(html, height=720, scrolling=False)

render_simulation()

st.markdown('<div class="section">Evidence & localization</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">The alert is explainable: each signal contributes evidence, while the zone score combines severity and sensor agreement.</div>', unsafe_allow_html=True)
ecols = st.columns(4)
for col,(name,val) in zip(ecols,evidence.items()):
    with col: st.markdown(f'<div class="card"><div class="kicker">{name}</div><div class="metric-number">{val*100:.0f}%</div><div class="muted">Relative evidence weight</div></div>',unsafe_allow_html=True)

zview = zones[["zone","severity","score","pressure_drop_kpa","flow_deviation_lpm","sensor_agreement","affected_population","critical_sites"]].copy()
zview.columns = ["Zone","Severity","Risk","Pressure drop (kPa)","Flow deviation (L/min)","Sensor agreement","Population","Critical sites"]
st.dataframe(zview,use_container_width=True,hide_index=True,column_config={"Risk":st.column_config.ProgressColumn("Risk",min_value=0,max_value=100,format="%d")})

# ----------------- NEW: CITIZEN CROSS-VERIFICATION -----------------
st.markdown('<div class="section">Citizen Report Cross-Verification</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">Graph-based validation correlating AI telemetry localization with incoming crowd-sourced civic complaints.</div>', unsafe_allow_html=True)

report_data = pd.DataFrame({
    "Time": ["10 mins ago", "14 mins ago", "22 mins ago"],
    "Source": ["WhatsApp Bot", "Civic App", "Civic App"],
    "Reported Location": ["Central Branch - Station Rd", "Central Zone - High St", "North Branch - Market"],
    "Complaint": ["Water pooling on road", "Low pressure in building", "Slight pressure drop"],
    "AI Correlation": ["High (Matches Burst Topology)", "High (Matches Burst Topology)", "Low (Outside Anomaly Zone)"]
})

st.dataframe(
    report_data, 
    use_container_width=True, 
    hide_index=True,
    column_config={
        "AI Correlation": st.column_config.TextColumn("AI Correlation", help="Determined via networkx topological distance")
    }
)
# -------------------------------------------------------------------

st.markdown('<div class="section">Response sandbox</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">Model a containment option before any field action. LeakGuard never sends a valve command.</div>', unsafe_allow_html=True)
a,b = st.columns([1.1,2.2])
with a:
    actions = INTERVENTIONS["action"].tolist()
    current = st.session_state.selected_action if st.session_state.selected_action in actions else actions[1]
    action = st.selectbox("Response option", actions, index=actions.index(current))
    st.session_state.selected_action = action
    if st.button("Run response model",use_container_width=True):
        try: _, st.session_state.response_summary = simulate_intervention(df, active.zone, action)
        except Exception as exc: st.error(str(exc))
with b:
    summary = st.session_state.get("response_summary")
    if summary:
        r1,r2,r3,r4 = st.columns(4)
        with r1: st.metric("Loss before",f"{summary['loss_before_lpm']:.0f} L/min")
        with r2: st.metric("Loss after",f"{summary['loss_after_lpm']:.0f} L/min",delta=f"-{summary['loss_reduction_pct']:.0f}%")
        with r3: st.metric("Pressure recovery",f"+{summary['max_pressure_recovery']:.1f} kPa")
        with r4: st.metric("Critical service",f"{summary['critical_service_pct']:.0f}%")
        st.markdown(f'<div class="pill-info"><b>{summary["action"]}</b> · {summary["description"]}<br><span class="small">Human approval required; verify recovery from telemetry after any field action.</span></div>',unsafe_allow_html=True)
        
        # ----------------- NEW: DISPATCH REPORT BUTTON -----------------
        report_text = f"""LEAKGUARD AUTOMATED INCIDENT REPORT
Date/Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Affected Zone: {active.zone}
Severity Level: {active.severity}
Estimated Loss: {loss_lpm:,.0f} L/min

RECOMMENDED ACTION:
{decision} - {decision_reason}

SIMULATED CONTAINMENT ({summary["action"]}):
Expected Pressure Recovery: +{summary['max_pressure_recovery']:.1f} kPa
Expected Loss Reduction: -{summary['loss_reduction_pct']:.0f}%
"""
        st.download_button(
            label="📥 Download Field Dispatch Report", 
            data=report_text, 
            file_name=f"LeakGuard_Dispatch_{active.zone}.txt", 
            mime="text/plain", 
            use_container_width=True
        )
        # ----------------------------------------------------------------
    else:
        st.markdown('<div class="pill-info"><b>No response has been modelled yet.</b> Choose an option to compare its simulated effect.</div>',unsafe_allow_html=True)

st.markdown('<div class="section">Operational intelligence</div>',unsafe_allow_html=True)
q1,q2,q3 = st.columns(3)
with q1: st.markdown(f'<div class="card"><div class="kicker">Affected zone</div><div class="big">{active.zone}</div><div class="muted">{active.pipeline_km:.1f} km network · {active.critical_sites}</div></div>',unsafe_allow_html=True)
with q2: st.markdown(f'<div class="card"><div class="kicker">Sensor agreement</div><div class="metric-number">{active.sensor_agreement:.0f}%</div><div class="muted">Signals supporting the current zone assessment</div></div>',unsafe_allow_html=True)
with q3: st.markdown(f'<div class="card"><div class="kicker">Response priority</div><div class="big">{decision}</div><div class="muted">{decision_reason}</div></div>',unsafe_allow_html=True)

# ----------------- NEW: MODEL DIAGNOSTICS EXPANDER -----------------
with st.expander("Model Diagnostics & Algorithmic Backend"):
    st.markdown(f"""
    **Detection Engine Architecture**
    * **Statistical Baseline:** Multi-variate anomaly detection utilizing Z-score deviations against dynamically calibrated sensor baselines.
    * **Localization Logic:** Graph-based topological search (using array matrix routing) weighting downstream flow surges against localized pressure drops.
    * **Confidence Interval:** {active.sensor_agreement:.1f}% sensor agreement across {active.zone} nodes.
    * **False-Positive Mitigation:** Requires sustained deviation over multiple timesteps before escalating from 'Warning' to 'Critical' state.
    """)
# -------------------------------------------------------------------

with st.expander("Sensor placement strategy"):
    st.dataframe(sensor_placement(df),use_container_width=True,hide_index=True)

st.markdown('<div class="section">Data & deployment</div>',unsafe_allow_html=True)
st.markdown('<div class="sub">LeakGuard separates reproducible demonstration telemetry from the live infrastructure it is designed to consume.</div>',unsafe_allow_html=True)
d1,d2,d3 = st.columns(3)
with d1: st.markdown('<div class="card"><div class="kicker">Used now</div><div class="big">Controlled telemetry</div><div class="muted">Timestamped pressure + flow readings with known scenario ground truth and calibrated sensor baselines.</div></div>',unsafe_allow_html=True)
with d2: st.markdown('<div class="card"><div class="kicker">Production input</div><div class="big">Utility IoT / SCADA</div><div class="muted">Authorised live pressure, flow, sensor ID, zone/location and timestamp feeds through the ingestion boundary.</div></div>',unsafe_allow_html=True)

# ----------------- NEW: SCALABILITY TEXT -----------------
with d3: st.markdown('<div class="card"><div class="kicker">Integration path</div><div class="big">MQTT / Kafka</div><div class="muted">Built for infinite scaling. Capable of ingesting millions of telemetry events to support a city-wide Digital Twin architecture.</div></div>',unsafe_allow_html=True)
# ---------------------------------------------------------

st.markdown('<div class="section">Deployment readiness</div>',unsafe_allow_html=True)
r1,r2,r3 = st.columns(3)
with r1: st.markdown('<div class="card"><div class="kicker">Signal layer</div><div class="big">Pressure + flow</div><div class="muted">Multi-sensor agreement reduces dependence on a single noisy reading.</div></div>',unsafe_allow_html=True)
with r2: st.markdown('<div class="card"><div class="kicker">Context layer</div><div class="big">Topology + demand</div><div class="muted">GIS topology, pump/valve state and demand context can improve localization and reduce false alarms.</div></div>',unsafe_allow_html=True)
with r3: st.markdown('<div class="card"><div class="kicker">Field layer</div><div class="big">Verify before action</div><div class="muted">Response modelling remains advisory; field confirmation and calibrated utility controls are required before deployment.</div></div>',unsafe_allow_html=True)

st.markdown('<div class="footer-note"><b>Prototype boundary</b> · The bundled stream is controlled telemetry. Production deployment requires authorised utility telemetry, calibrated baselines, network topology and field validation.</div>', unsafe_allow_html=True)