# LeakGuard controlled validation

This benchmark is a reproducible controlled test of the implemented rule-based pressure/flow detector. It is not a field trial and is not a claim of production performance.

- 900 telemetry snapshots
- 300 Normal Network cases
- 300 Hidden Leak cases
- 300 Major Burst cases
- 3 possible target zones for incident cases
- Gaussian sensor noise plus occasional background demand variation and single-sensor faults
- Fixed random seed: 42

Ground truth is known because each case is generated with an explicit scenario and, for incident cases, an explicit target zone.

## Method comparison

The validation also compares the multi-signal detector with a transparent pressure-only baseline on the same 900 controlled cases. The comparison is intended to measure the value of combining pressure, flow and sensor agreement; it is not a field-performance claim.

With seed 42 and 300 cases per class:

| Method | Precision | Recall | False-positive rate |
|---|---:|---:|---:|
| LeakGuard multi-signal | 93.9% | 84.8% | 11.0% |
| Pressure-only baseline | 92.4% | 66.5% | 11.0% |

The live USGS public-water feed shown in the dashboard is not part of this benchmark. The benchmark evaluates only the pipe-network detection engine against controlled telemetry with known ground truth.
