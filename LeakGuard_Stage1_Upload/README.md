
# LeakGuard 💧

LeakGuard is an evidence-driven water-network incident intelligence prototype.

## Core workflow

Detect → Diagnose → Localize → Explain → Quantify → Simulate → Decide → Approve → Verify

## Features

- Multi-signal pressure/flow anomaly detection
- Competing-cause reasoning: leak, sensor fault, demand shift, valve/pump event
- ACT / VERIFY / ABSTAIN decision layer
- Zone localization and impact analysis
- Counterfactual intervention comparison
- Operator approval workflow
- Closed-loop post-intervention verification
- Sensor placement advisor
- Research CSV ingestion
- Validation dashboard
- Modular architecture ready for hydraulic digital-twin integration

## Important technical honesty

The current Counterfactual Lab and Sensor Placement Advisor are operational decision-model prototypes, not full hydraulic solvers. The UI is intentionally designed so a WNTR/EPANET hydraulic engine can be integrated later.

The validation table in Demo Mode contains placeholder values and must not be presented as measured benchmark performance. Replace it with measured results before claiming accuracy.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app/main.py
```

Streamlit's official documentation uses `streamlit run <file>` to start a local server.

## Suggested demo

1. Open Demo Incident.
2. Select **Major Burst**.
3. Show the evidence chain.
4. Open Counterfactual Leak Lab.
5. Simulate the recommended intervention.
6. Approve it.
7. Run post-intervention verification.
8. Switch to Research CSV and upload telemetry.

## Data

Large benchmark datasets should not be committed to this repository. Use a prepared sample or download the benchmark separately and cite the source.

For research benchmarking, BattLeDIM/L-Town provides SCADA measurements and a network model:
https://battledim.ucy.ac.cy/
