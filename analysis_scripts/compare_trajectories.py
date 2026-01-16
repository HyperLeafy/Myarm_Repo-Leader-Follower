#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import argparse
import csv
import sys
import os
import matplotlib.pyplot as plt
import numpy as np

# Adjust path to import mapping/config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import mapping

def read_csv(filepath, is_leader=False):
    """
    Reads CSV. Returns (timestamps, data_matrix).
    If is_leader=True, expects standard teleop inputs.
    If is_leader=False (Baseline), expects J1-J6 columns.
    """
    if not os.path.exists(filepath):
        print(f"Error: File not found {filepath}")
        sys.exit(1)
        
    timestamps = []
    data = []
    
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        
        # Simple header check/index finding could be added, but assuming standard format
        # Leader (c650_motion_logger): Time, J1...J6
        # Baseline (record_baseline): Time, J1...J6, Gripper
        
        start_time = None
        
        for row in reader:
            try:
                t = float(row[0])
                if start_time is None: start_time = t
                rel_t = t - start_time
                
                # J1 is usually col 1
                angles = [float(x) for x in row[1:7]]
                
                timestamps.append(rel_t)
                data.append(angles)
            except (ValueError, IndexError):
                continue
                
    return np.array(timestamps), np.array(data)

import glob

def get_latest_file(directory, pattern):
    files = glob.glob(os.path.join(directory, pattern))
    if not files: return None
    return max(files, key=os.path.getmtime)

def main():
    parser = argparse.ArgumentParser(description="Compare C650 Mapped Output vs M750 Baseline Truth")
    parser.add_argument("--leader", help="Path to Leader Log (C650 Input). Defaults to latest in data/raw/")
    parser.add_argument("--baseline", help="Path to Baseline Log (M750 Truth). Defaults to latest in data/baselines/")
    args = parser.parse_args()

    # Auto-resolve Leader File
    if args.leader:
        leader_file = args.leader
    else:
        # data/raw
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        raw_dir = os.path.join(base_dir, 'data', 'raw')
        leader_file = get_latest_file(raw_dir, "c650_motion_*.csv")
        if not leader_file:
            print(f"Error: No leader logs found in {raw_dir}")
            sys.exit(1)

    # Auto-resolve Baseline File
    if args.baseline:
        base_file = args.baseline
    else:
        # data/baselines
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        traj_dir = os.path.join(base_dir, 'data', 'baselines')
        base_file = get_latest_file(traj_dir, "baseline_traj_*.csv")
        if not base_file:
            print(f"Error: No baseline logs found in {traj_dir}")
            sys.exit(1)

    print(f"Loading Leader:   {os.path.basename(leader_file)}")
    t_leader, d_leader = read_csv(leader_file, is_leader=True)
    
    print(f"Loading Baseline: {os.path.basename(base_file)}")
    t_base, d_base = read_csv(base_file, is_leader=False)

    # Time Alignment Logic
    duration_leader = t_leader[-1] if len(t_leader) > 0 else 0
    duration_base = t_base[-1] if len(t_base) > 0 else 0
    
    print(f"Leader Duration:   {duration_leader:.2f}s")
    print(f"Baseline Duration: {duration_base:.2f}s")
    
    if duration_base > 0 and duration_leader > 0:
        scale = duration_leader / duration_base
        print(f"Scaling Baseline Time by factor: {scale:.3f} (to match Leader)")
        t_base_scaled = t_base * scale
    else:
        t_base_scaled = t_base

    print("Processing Leader Data through Mapping Logic...")
    predicted_output = []
    
    for row in d_leader:
        # Pass through current LIVE mapping logic
        mapped, _ = mapping.process_arm_angles(row)
        predicted_output.append(mapped)
        
    predicted_output = np.array(predicted_output)

    # Plotting
    print("Plotting Comparison...")
    fig, axes = plt.subplots(3, 2, figsize=(15, 10), sharex=True)
    axes = axes.flatten()
    
    for i in range(6):
        ax = axes[i]
        
        # Plot Baseline (Ground Truth) - Scaled Time
        ax.plot(t_base_scaled, d_base[:, i], 'g-', linewidth=2, alpha=0.6, label='Baseline (Truth)')
        
        # Plot Predicted (Simulated Follower)
        ax.plot(t_leader, predicted_output[:, i], 'b--', linewidth=1.5, label='Predicted Output')
        
        # Plot Input (Just for reference, maybe faint red?)
        # ax.plot(t_leader, d_leader[:, i], 'r:', linewidth=0.5, label='Raw Input')
        
        ax.set_title(f"Joint {i+1}")
        ax.set_ylabel("Angle (deg)")
        ax.grid(True)
        if i == 0:
            ax.legend(loc='upper right')

    fig.suptitle(f"Comparison: {os.path.basename(leader_file)} vs {os.path.basename(base_file)}", fontsize=16)
    plt.xlabel("Time (s) - Scaled to Leader Duration")
    # Headless fallback
    try:
        plt.show()
    except:
        output_img = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'comparison_result.png')
        plt.savefig(output_img)
        print(f"Saved comparison plot to: {output_img}")

if __name__ == "__main__":
    main()
