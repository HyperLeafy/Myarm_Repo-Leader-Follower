#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# --- Gripper Calibration ---
# Observed Joint 7 angles for the Leader (C650)
LEADER_GRIPPER_CLOSED = 10.89
LEADER_GRIPPER_OPEN = -88.76

# --- Resting Position Offsets (Input Calibration) ---
# "dt = -10" means Output is different. We can shift the Input so it maps correctly.
# If Follower is -10 deg compared to Leader, we can ADD -10 to the Home Angle (or subtract?)
# Let's adjust these to "Zero out" the difference.
# J1: -10, J3: -20, J5: -20 (Heuristic: Adding these to input zeroes)
# Tuned Offsets to align Leader "0" with Follower "0" (or Desired Pose).
# J5: User reported +25 deg discrepancy (Input too low). Offset = -25.
# J6: User reported -23 deg discrepancy (Input too high). Offset = +23.
C650_HOME_ANGLES = [0.0, 0.0, 0.0, 0.0, -25.0, 23.0]

# --- Joint Limits ---
# Min/Max tuples for each joint

# M750 Limits (Follower)
# TUNED based on User Feedback:
# J2: Reverted to (-80, 80) for safety (User had -10, 180 which might cause crash)
# J3: Widened to (-150, 150) to fix "moves little" scaling issue.
# J5: Widened to (-150, 150) to fix "not reaching max".
# Measured Hardware Limits (from get_joint_max/min):
# J1: +/- 165
# J2: -80, +100
# J3: -100, +80
# J4: +/- 160
# J5: -90, +120
# J6: +/- 179 (Assumed standard for J6)

# Software Limits (Hardware Safety Clamps)
M750_LIMITS = [
    (-165.0, 165.0),
    (-54.0, 100.0),
    (-100.0, 62.0),
    (-152.0, 155.0),
    (-90.0, 120.0),
    (-148.0, 162.0),
]

# Direct Scaling Gains (Input * Gain = Output)
# Use negative values to invert direction.
# Goal: 1:1 mapping (Gain=1.0) where possible.
M750_GAINS = [
    -1.0,  # J1: Inverted
    1.0,   # J2: 1:1
    1.0,   # J3: 1:1
    1.0,   # J4: 1:1
    1.0,   # J5: 1:1
    -1.0   # J6: Inverted
]

# C650 Limits (Leader Input Range)
# Used for input normalization (0% - 100%)
C650_LIMITS = [
    (-161.8, 152.49),
    (-198.2, 190.38),
    (-188.62, 183.2),
    (-164.61, 160.22),
    (-118.74, 75.41),
    (-145.28, 153.1),
    (-88.7, 10.89)
]