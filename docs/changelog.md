# Project Changelog & Objective History

This document tracks the major changes, pivots, and milestones in the **MyArm-Control** project.

## 1. Project Initialization & Setup
- **Objective**: Establish a Python environment for controlling Elephant Robotics MyArm C650 and M750 robots.
- **Action**: 
    - Created project structure with `uv` package manager and Python 3.10.
    - Added `pymycobot` dependency.
    - Created initial `connection_test.py` to verify serial connectivity.

## 2. Pivot: Network to USB Teleoperation
- **Initial Plan**: Use existing TCP/Socket-based demo scripts from `pymycobot`.
- **Change**: User requested a strictly **USB-based** solution (no network).
- **Implementation**: 
    - Created `control_scripts/teleop_usb.py`.
    - Implemented a direct "Leader-Follower" loop: Read C650 angles -> Process -> Write M750 angles.
    - Removed all socket/server logic.

## 3. Debugging: Gripper Control & Limits
- **Issue**: Gripper (Joint 7) was not moving, and the robots had "weird mapping".
- **Fixes**:
    1.  **Switch to `MyArmMControl`**: The standard `MyArmM` class lacked specific gripper commands. Switched follower instantiation to `MyArmMControl` to access `set_gripper_value()` and `set_gripper_enabled()`.
    2.  **Explicit Control Script**: Created `teleop_explicit.py` to separate 6-axis arm control (`write_angles`) from gripper control (`set_gripper_value`).
    3.  **Joint 2 Crash**: identified that the M750 firmware rejects angles < -80 on Joint 2. Added software clamping `(-80, 80)` to prevent `ValueError` crashes.
    4.  **Gripper Mapping**: Implemented a linear map from the Leader's range (approx -88 to 10) to the Follower's input range (0-100).

## 4. Calibration Tools
- **Objective**: Allow user to define "Resting Position" and find actual limits.
- **Implementation**:
    - Created `control_scripts/c650_range_monitor.py` & `M750_range_monitor.py` to display real-time Min/Max angles.
    - Added logic to `teleop_explicit.py` to subtract `C650_HOME_ANGLES` from readings, allowing a custom zero-point.

## 5. Refactoring & Modularity
- **Objective**: Clean up the code and centralize configuration.
- **Implementation**:
    - **`config.py`**: Central file for Limits, Offsets, and Gripper constants.
    - **`utils/mapping.py`**: Extracted robot math, inversion, and clamping logic.
    - **`utils/connection.py`**: Extracted serial port selection logic.
    - **`c650_motion_logger.py`**: Added a script to record trajectories to CSV.
    - **Final Teleop Script**: `teleop_explicit.py` now acts as a clean entry point importing these modules.
