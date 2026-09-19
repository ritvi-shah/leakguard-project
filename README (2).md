# LeakGuard — Intelligent Water Pipe Leak Detection System

Real-time anomaly detection across water distribution networks, automated intervention recommendations, and live analytics — powered by multi-signal ML detection.

## Overview

LeakGuard is a full-stack water infrastructure monitoring platform that replaces reactive leak detection with proactive, AI-driven anomaly identification. It tracks pressure and flow telemetry across a segmented water distribution network in real time, monitors zone-based capacity across 3 monitored regions, and uses a machine learning detection engine to recommend — or automatically execute — dynamic interventions when pressure/flow anomalies, leaks, or burst incidents are detected.

**Dashboard (Streamlit)**  ←→  **Detection Engine (Python)**  ←→  **Simulation Data**

## Features

| Category | What It Does |
|----------|--------------|
| **Real-Time Detection** | Multi-signal anomaly detection (pressure + flow correlation) with 93.9% precision |
| **Live Dashboard** | Interactive Streamlit UI with metrics, charts, and incident replay simulation |
| **Scenario Simulation** | Automated progression: Normal Network → Hidden Leak → Major Burst (with 1x/2x/4x speed control) |
| **Zone Monitoring** | 3 water distribution zones (North, Central, South) with segment-specific tracking |
| **Risk Scoring** | Intelligent 0-100 risk scale based on pressure drop, flow deviation, and multi-signal agreement |
| **Intervention Engine** | 4-tier response matrix: Monitor Only → Isolate Central → Isolate Secondary → Emergency Isolation |
| **SLA Tracking** | Real-time SLA deadline monitoring with deviation alerts |
| **Validation Benchmark** | 900-case controlled test suite with 84.8% detection recall |
| **Reproducible Results** | Fixed random seed (42) for statistical consistency across runs |

## Architecture

```
┌──────────────────────────────────────────────────┐
│         DASHBOARD (Streamlit + React)             │
│  app/main.py — UI, controls, real-time charts    │
│  components — metrics cards, map, incident panel │
└───────────────────┬────────────────────────────────┘
                    │ Live Data Updates (5s polling)
┌───────────────────▼────────────────────────────────┐
│       DETECTION ENGINE (Python + Pandas)           │
│  app/engine.py — Multi-signal anomaly detection   │
│  anomaly logic — pressure/flow correlation        │
│  risk_scoring.py — 0-100 incident scoring         │
│  intervention.py — action recommendation logic    │
└──────────────┬──────────────┬──────────────────────┘
               │              │
          Scenario       Simulation Data
          Simulation     (CSV/JSON)
```

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-green.svg)
![Pandas](https://img.shields.io/badge/Pandas-2.2+-blueviolet.svg)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-1.5+-orange.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

## Backend Modules

| Module | Purpose |
|--------|---------|
| **engine.py** | Core multi-signal detection — baseline normalization, feature extraction, anomaly scoring, zone risk aggregation |
| **risk_scoring.py** | 0-100 incident risk scale (pressure drop % + flow deviation % + multi-signal bonus) |
| **intervention.py** | 4-tier action recommendation matrix (Monitor → Isolate Central → Isolate Secondary → Emergency) |
| **simulation.py** | 5-minute tick loop — scenario progression (Normal → Hidden Leak → Major Burst), telemetry generation, alert dispatch |
| **validation.py** | 900-case benchmark runner — precision/recall/F1 calculation, baseline comparison, reproducible results |

## Tech Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **UI Framework** | Streamlit | 1.40+ | Interactive web dashboard & real-time updates |
| **Data Processing** | Pandas | 2.2+ | Telemetry data manipulation & analysis |
| **Numerical Computing** | NumPy | 1.26+ | High-performance array operations |
| **Visualization** | Plotly | 5.24+ | Interactive charts & network visualization |
| **ML & Statistics** | Scikit-learn | 1.5+ | Anomaly detection algorithms |
| **Network I/O** | Requests | 2.32+ | HTTP API communication for data integration |

## Getting Started

### Prerequisites

- Python 3.9+
- pip or conda package manager
- Git

### 1. Clone and Install

```bash
git clone https://github.com/ritvi-shah/leakguard-project.git
cd leakguard-project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)

Create a `.env` file for custom settings:

```bash
# Dashboard settings
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true

# Data source (if using external APIs in future)
SENSOR_DATA_URL=http://localhost:8000/api/sensors
DATABASE_URL=postgresql://user:pass@localhost/leakguard
```

### 3. Run the Application

```bash
streamlit run app/main.py
```

Dashboard opens at **http://localhost:8501**

### 4. Optional: Run Validation Benchmark

```bash
# Verify 93.9% precision and 84.8% recall on 900-case test suite
python tests/test_engine.py
```

## Project Structure

```
leakguard-project/
├── app/
│   ├── main.py                 # Streamlit dashboard entry point
│   ├── engine.py               # Core detection engine
│   ├── data_loader.py          # Data preprocessing
│   ├── live_feed.py            # External data integration
│   └── __init__.py
│
├── tests/
│   └── test_engine.py          # Unit tests + benchmark validation
│
├── validation/
│   ├── README.md               # Methodology docs
│   ├── metrics.json            # Performance results
│   └── benchmark_results.csv   # 900-case benchmark data
│
├── assets/
│   └── water_network_bg.png    # Dashboard UI background
│
├── .streamlit/
│   └── config.toml             # Theme configuration
│
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Detection Algorithm

### Multi-Signal Approach

LeakGuard combines pressure and flow signals for high-confidence anomaly detection.

### Workflow

**Step 1: Baseline Establishment**
```
For each monitored zone:
  baseline_pressure = median(historical_pressure)
  baseline_flow = median(historical_flow)
```

**Step 2: Feature Extraction**
```
pressure_residual = current_pressure - baseline_pressure
flow_deviation = current_flow - baseline_flow
pressure_anomaly = |pressure_residual| > 8 PSI
flow_anomaly = |flow_deviation| > 30 GPM
```

**Step 3: Multi-Signal Correlation**
```
IF pressure_anomaly AND flow_anomaly THEN
  confidence = HIGH
  incident_probability = HIGH
ELSE IF pressure_anomaly XOR flow_anomaly THEN
  confidence = MEDIUM
  incident_probability = MEDIUM
ELSE
  confidence = LOW
  incident_probability = LOW
END IF
```

**Step 4: Risk Scoring**
```
risk_score = (pressure_drop_% × 1.7) + (flow_change_% × 2.2)
            + (multi_signal_bonus × 12)
risk_score = min(risk_score, 100)
```

**Step 5: Decision Output**
```
IF risk_score > threshold THEN
  generate_alert(zone, risk_level, recommended_action)
END IF
```

### Intervention Decision Matrix

**Available Response Actions with Impact Analysis:**

| Intervention | Water Loss Reduction | Service Coverage | Critical Infrastructure | Recommended For |
|--------------|----------------------|-------------------|------------------------|-----------------|
| **Monitor Only** | 0% | 100% | 100% | Early-stage incidents, continuous surveillance |
| **Isolate Central Branch** | 91% | 96% | 100% | Confirmed Central zone incidents |
| **Isolate Secondary Branch** | 95% | 82% | 75% | Significant incidents requiring partial service interruption |
| **Emergency Isolation** | 97% | 61% | 0% | Critical burst incidents, maximum containment priority |

**Decision Criteria**:
- Risk Score < 30: Monitor Only
- Risk Score 30-60: Isolate Secondary Branch
- Risk Score 60-85: Isolate Central Branch  
- Risk Score ≥ 85: Emergency Isolation

---

## Performance Validation & Benchmarking

### Experimental Methodology

**Test Dataset Composition:**
- **Total Samples**: 900 controlled telemetry snapshots
- **Ground Truth**: Explicitly generated with known incident states and zones
- **Reproducibility**: Fixed random seed (42) for statistical validity
- **Scenario Distribution**:
  - 300 Normal Network (baseline) cases
  - 300 Hidden Leak cases (distributed across 3 target zones)
  - 300 Major Burst cases (distributed across 3 target zones)

**Realistic Conditions:**
- Gaussian sensor noise simulation
- Background demand variation
- Single-sensor fault scenarios
- Multi-zone pressure/flow interactions

### Quantitative Results

**LeakGuard Multi-Signal Detection Performance:**

| Metric | Value | Interpretation |
|--------|-------|-----------------|
| **Precision** | 93.9% | 93.9% of detections are true positives |
| **Recall (Sensitivity)** | 84.8% | 84.8% of actual incidents are detected |
| **False-Positive Rate** | 11.0% | 11.0% of normal cases flagged as anomalies |
| **Specificity** | 89.0% | 89.0% of normal cases correctly identified |
| **F1-Score** | 0.892 | Harmonic mean of precision and recall |

**Comparative Analysis: Multi-Signal vs. Pressure-Only Baseline**

| Method | Precision | Recall | FPR | Improvement |
|--------|-----------|--------|-----|-------------|
| **LeakGuard (Multi-Signal)** | 93.9% | 84.8% | 11.0% | **Baseline** |
| **Pressure-Only** | 92.4% | 66.5% | 11.0% | -27.2% Recall |

**Key Finding**: Multi-signal correlation provides **27.2% improvement in detection recall** while maintaining equivalent precision, demonstrating the value of combined pressure-flow analysis.

## Simulation Scenarios

The dashboard auto-replays a complete water network incident cycle (1x/2x/4x speed control):

| Phase | Duration | Pressure | Flow | Status |
|-------|----------|----------|------|--------|
| **Normal Network** | 0-8 min | 52 PSI | 120 GPM | Baseline operation |
| **Hidden Leak** | 8-38 min | 52→34.5 PSI | 120→194 GPM | Gradual degradation, multi-signal detection triggers |
| **Major Burst** | 38+ min | 52→28.5 PSI | 120→225 GPM | Immediate alert, emergency isolation recommended |

**Controls:** Play, Pause, Reset, Speed (1x/2x/4x)

## Validation & Testing

```bash
# Run complete test suite + benchmark
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

**Benchmark Suite:**
- 900 controlled test cases with known ground truth
- 300 Normal Network + 300 Hidden Leak + 300 Major Burst
- Reproducible results (seed: 42)
- Precision: **93.9%** | Recall: **84.8%** | F1: **0.892**

## Database Schema

| Table | Columns |
|-------|---------|
| **warehouses** | id, name, lat, lng, capacity, current_load, status |
| **carriers** | id, name, reliability_score, vehicle_availability |
| **shipments** | id, origin_id, dest_id, carrier_id, status, priority, lat, lng, eta, sla_deadline |
| **sensors** | sensor_id, zone, location, baseline_pressure, baseline_flow |

## Monitored Zones

| Zone | Pipe Length | Population | Critical Sites |
|------|-------------|------------|-----------------|
| North | 4.2 km | 8,200 | North Hospital |
| Central | 6.8 km | 12,500 | Central Hospital, Metro Station |
| South | 5.4 km | 5,100 | South Market |

## Performance Metrics

Benchmarked on 900 controlled test cases (seed: 42):

| Metric | Value |
|--------|-------|
| Precision | 93.9% |
| Recall | 84.8% |
| F1-Score | 0.892 |
| False-Positive Rate | 11.0% |
| **vs. Pressure-Only Baseline** | **+27.2% Recall** |

## Author

**Ritvi Shah** — [@ritvi-shah](https://github.com/ritvi-shah)

## License

MIT — See LICENSE file for details.

---

**LeakGuard: Protecting water infrastructure through intelligent detection**
