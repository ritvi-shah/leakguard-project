# LeakGuard - Auto Detection / No USGS

This build uses the controlled replay only; no USGS/live external telemetry is required.

Incident Replay behavior:
- Play automatically progresses through Normal Network -> Hidden Leak -> Major Burst.
- There is no manual incident-selection dropdown.
- Play, Pause, Reset, and 1x/2x/4x speed controls are included.
- Pressure, flow, estimated loss, risk, network particles, detection state, and chart update during replay.

Important: use the `app/main.py` from this ZIP. This build contains the fixed JavaScript chart rendering code and does not contain the previous `pad` NameError.
