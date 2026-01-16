#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import argparse
import csv
import glob
import sys
import os
import numpy as np
from sklearn.linear_model import LinearRegression
from scipy.interpolate import interp1d

# Adjust path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import M750_LIMITS, C650_LIMITS
except ImportError:
    M750_LIMITS = [(-170, 170)]*6
    C650_LIMITS = [(-170, 170)]*6

def get_latest_file(directory, pattern):
    files = glob.glob(os.path.join(directory, pattern))
    if not files: return None
    return max(files, key=os.path.getmtime)

def read_csv(filepath, is_leader=False):
    if not os.path.exists(filepath):
        print(f"Error: File not found {filepath}")
        sys.exit(1)
        
    timestamps = []
    data = []
    
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return np.array([]), np.array([])
        
        start_time = None
        for row in reader:
            try:
                t = float(row[0])
                if start_time is None: start_time = t
                rel_t = t - start_time
                
                # J1-J6
                angles = [float(x) for x in row[1:7]]
                timestamps.append(rel_t)
                data.append(angles)
            except (ValueError, IndexError):
                continue
                
    return np.array(timestamps), np.array(data)

def suggest_limits(joint_idx, current_min, current_max, slope, intercept):
    """
    Desired: Output = Input
    Actual:  Output = m * Input + c
    
    We want to change limits so that the new mapping effectively cancels 'm' and 'c'.
    NewRange = OldRange / m
    NewCenter = OldCenter - c
    """
    if abs(slope) < 0.01: return current_min, current_max
    
    current_range = current_max - current_min
    new_range = current_range / slope
    
    center = (current_max + current_min) / 2
    new_center = center - intercept
    
    new_min = new_center - (new_range / 2)
    new_max = new_center + (new_range / 2)
    
    return round(new_min, 1), round(new_max, 1)

def main():
    parser = argparse.ArgumentParser(description="Auto-Tune M750 Limits based on Leader vs Baseline Logs")
    parser.add_argument("--leader", help="Leader Log (Input)")
    parser.add_argument("--baseline", help="Baseline Log (Target)")
    parser.add_argument("--single_file", help="Legacy: Use single file with Actual columns")
    args = parser.parse_args()

    # 1. Resolve Files
    if args.single_file:
        print("Single file mode not fully supported in this version. Use --leader and --baseline.")
        sys.exit(1)

    if args.leader:
        leader_file = args.leader
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        raw_dir = os.path.join(base_dir, 'data', 'raw')
        leader_file = get_latest_file(raw_dir, "c650_motion_*.csv")

    if args.baseline:
        base_file = args.baseline
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        traj_dir = os.path.join(base_dir, 'data', 'baselines')
        base_file = get_latest_file(traj_dir, "baseline_traj_*.csv")

    if not leader_file or not base_file:
        print("Error: Could not find log files.")
        sys.exit(1)

    print(f"Leader:   {os.path.basename(leader_file)}")
    print(f"Baseline: {os.path.basename(base_file)}")

    # 2. Read Data
    t_lead, d_lead = read_csv(leader_file, is_leader=True)
    t_base, d_base = read_csv(base_file, is_leader=False)

    if len(t_lead) == 0 or len(t_base) == 0:
        print("Error: Empty data.")
        sys.exit(1)

    # 3. Time Alignment & Interpolation
    dur_lead = t_lead[-1]
    dur_base = t_base[-1]
    
    print(f"Duration: Lead={dur_lead:.1f}s, Base={dur_base:.1f}s")
    
    # Scale Baseline Time to match Leader
    if dur_base > 0:
        scale = dur_lead / dur_base
        t_base_scaled = t_base * scale
    else:
        t_base_scaled = t_base

    # Resample Baseline to match Leader timestamps
    # This gives us pairs of (LeaderInput, BaselineTarget) at the same 'relative' time
    d_base_resampled = np.zeros_like(d_lead)
    
    for i in range(6):
        # Create interpolator for Baseline Joint i
        interp = interp1d(t_base_scaled, d_base[:, i], kind='linear', fill_value="extrapolate")
        d_base_resampled[:, i] = interp(t_lead)

    # 4. Regression & Tuning
    print("\n--- Calibration Results ---")
    print(f"{'J':<3} | {'Slope':<10} | {'Bias':<10} | {'Status'}")
    print("-" * 60)

    new_limits = []

    for i in range(6): # 0-5
        j_idx = i + 1
        X = d_lead[:, i].reshape(-1, 1) # Leader Input
        y = d_base_resampled[:, i]      # Baseline Target
        
        reg = LinearRegression().fit(X, y)
        m = reg.coef_[0]
        c = reg.intercept_
        r2 = reg.score(X, y)
        
        curr_min, curr_max = M750_LIMITS[i]
        
        # We want Map(Input) == Baseline
        # Current Logic: Output = Input (roughly, if normalized)
        # If we see Baseline = m*Input + c
        # We want to change Limits so that the Output closely matches (m*Input + c)
        
        # WAIT! The Mapping Logic ALREADY applies normalization.
        # We are comparing RAW Input (deg) vs RAW Baseline (deg).
        # But the Code does:
        #   Norm = (Input - InMin)/(InMax - InMin)
        #   Output = Norm * (OutMax - OutMin) + OutMin
        
        # So: Output = Input * (OutRange/InRange) + Constants
        # The observed Slope 'm' is effectively (OutRange/InRange).
        # If 'm' is not 1.0 (assuming ranges are roughly equal), we have a scaling mismatch.
        # Ideally, we want Output = Input (Slope 1.0) IF the robots were identical.
        # But here, we want Output to MATCH Baseline.
        # So we want the Config to produce the Baseline.
        
        # Strategy:
        # We calculated that the RELATIONSHIP between Input and "Perfect Output" is:
        # Target = m * Input + c
        # We need to set M750 Limits such that when we feed Input, we get Target.
        
        # Let's derive:
        # Target = (Input - InMin)/(InMax - InMin) * (NewOutMax - NewOutMin) + NewOutMin
        # Target = Input * [NewRange/InRange] + [NewOutMin - InMin*NewRange/InRange]
        
        # So:
        # m = NewRange / InRange
        # c = NewOutMin - InMin * m
        
        # Therefore:
        # NewRange = m * InRange
        # NewOutMin = c + InMin * m
        # NewOutMax = NewOutMin + NewRange
        
        in_min, in_max = C650_LIMITS[i]
        in_range = in_max - in_min
        
        target_range = m * in_range
        target_min = c + (in_min * m)
        target_max = target_min + target_range
        
        # Display
        print(f"J{j_idx:<2} | {m:<10.3f} | {c:<10.3f} | New Limits: ({target_min:.1f}, {target_max:.1f})")
        
        new_limits.append((round(target_min, 1), round(target_max, 1)))

    print("\n--- Recommended config.py Block ---")
    print("M750_LIMITS = [")
    for lim in new_limits:
        print(f"    {lim},")
    print("]")

if __name__ == "__main__":
    main()
