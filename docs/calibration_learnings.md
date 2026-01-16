# Calibration & Tuning Learnings

**Date**: 2026-01-08  
**Subject**: Tuning MyArm C650 (Leader) -> M750 (Follower) Teleoperation

This document captures the context, analysis, and solutions for the mapping issues encountered during the development of the Leader-Follower system.

## 1. The Symptoms

During initial testing of the `teleop_explicit.py` script, the following issues were observed:

1. **Joint 2 "Stuck" / "Opposite"**: The follower moved in the opposite direction to the leader and would stop/stick at certain angles.
2. **Joint 3 & 5 "Lazy"**: The follower moved in the correct direction but only covered ~50% of the movement range compared to the leader.
3. **Joint 1, 4, 6**: Worked perfectly (1:1 tracking).

## 2. The Analysis Logic

To debug this, we instituted a **Data-Driven Approach**:

1. **Logging**: We enabled `MonitorThread` to log CSV data to `data/processed/`.
2. **Analysis Script**: We ran `analysis_scripts/analyze_log.py` to compare Input vs Output ranges.

### Key Findings from Log `20260108_125145.csv`:

| Joint  | Input Range (Leader) | Output Range (Follower) | Ratio    | Diagnosis                                                                                                                                                              |
|:------ |:-------------------- |:----------------------- |:-------- |:---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **J2** | `[-78, 18]` (96°)    | `[48, 95]` (47°)        | **0.5x** | **Bias + Clip**. The output was clipped because the config limit `(-10, 180)` prevented it from matching the full input range. Also moving opposite (needs inversion). |
| **J3** | `~100°`              | `~48°`                  | **0.5x** | **Scaling**. The Follower limit was `(-90, 84)`, shrinking the mapping.                                                                                                |
| **J4** | `~100°`              | `~95°`                  | **1.0x** | **Perfect**. Limits matched physical capability.                                                                                                                       |
| **J5** | `~35°`               | `~32°`                  | **1.0x** | **Offset**. Input `[-14, 20]`, Output `[5, 37]`. Bias of +18°.                                                                                                         |

## 3. The Solutions

### A. Proportional Mapping Logic

We moved from "Angle Math" to "Percentage Math":

```python
# 1. Normalize Input to 0.0 - 1.0 based on C650 Limits
norm = (input - c_min) / (c_max - c_min)

# 2. Map Percentage to M750 Output Limits
output = map_value(norm, 0, 1, m_min, m_max)
```

*Why this helps*: It ensures that if the leader moves from *its* min to *its* max, the follower moves from *its* min to *its* max.

### B. Inversion (Joint 2 & 3)

* **Context**: The C650 and M750 have opposed motor mountings for J2/J3.
* **Fix**: We mapped `norm 0.0` -> `m_max` and `norm 1.0` -> `m_min` for these specific joints.

### C. Scaling Fix (Joint 3 & 5)

* **Problem**: The "Lazy" movement was because the **Output Range (M750 Limits)** in `config.py` was too narrow.
* **Fix**: We widened the M750 limits to `(-150, 150)`.
  * *Result*: A 10% movement on the Leader now corresponds to a larger movement on the Follower, fixing the "lazy" ratio.

### D. Safety Clamp (Joint 2)

* **Problem**: M750 Firmware crashes if J2 < -80.
* **Fix**: Hard limit in `config.py` set to `(-80, 80)`. Mapping logic clamps *after* calculation.

## 4. How to Tune in the Future

If a joint feels wrong (too fast, too slow, or offset):

1. **Run Teleop**: `uv run python control_scripts/teleop_explicit.py`
2. **Move the Joint**: Move the specific joint through its full range.
3. **Analyze**:
   * Run: `uv run python analysis_scripts/plot_joint.py --joint N`
   * Run: `uv run python analysis_scripts/analyze_log.py`
4. **Interpret**:
   * **Flatline on Green (Norm)**: Your **C650 Input Limits** are too narrow. Widen them in `config.py`.
   * **Flatline on Blue (Output)**: Your **M750 Output Limits** are clipping. Check if safe to widen.
   * **Slope too shallow**: Your **M750 Output Limits** are too narrow. Widen them to increase sensitivity.
   * **Slope too steep**: Your **M750 Output Limits** are too wide. Narrow them to decrease sensitivity.
