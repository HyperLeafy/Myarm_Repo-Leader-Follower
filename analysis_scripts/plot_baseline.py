#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import argparse
import csv
import glob
import sys
import os
import matplotlib.pyplot as plt
import numpy as np

def get_latest_file(directory, pattern):
    files = glob.glob(os.path.join(directory, pattern))
    if not files: return None
    return max(files, key=os.path.getmtime)

def read_baseline_csv(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File not found {filepath}")
        sys.exit(1)
        
    timestamps = []
    data = [] # List of [J1...J6, Gripper]
    
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
                
                angles = [float(x) for x in row[1:8]] # J1-J6 + Gripper
                timestamps.append(rel_t)
                data.append(angles)
            except (ValueError, IndexError):
                continue
                
    return np.array(timestamps), np.array(data)

def main():
    parser = argparse.ArgumentParser(description="Plot M750 Baseline Trajectories")
    parser.add_argument("--file", help="Path to Baseline Log (defaults to latest)")
    args = parser.parse_args()

    # Auto-resolve File
    if args.file:
        base_file = args.file
    else:
        # data/baselines
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        traj_dir = os.path.join(base_dir, 'data', 'baselines')
        base_file = get_latest_file(traj_dir, "baseline_traj_*.csv")
        if not base_file:
            print(f"Error: No baseline logs found in {traj_dir}")
            sys.exit(1)

    print(f"Plotting: {os.path.basename(base_file)}")
    t, d = read_baseline_csv(base_file)
    
    if len(t) == 0:
        print("Error: No data found.")
        sys.exit(1)

    # Plotting
    fig, axes = plt.subplots(4, 2, figsize=(15, 12), sharex=True)
    axes = axes.flatten()
    
    # 0-5 for Joints, 6 for Gripper
    for i in range(7):
        ax = axes[i]
        
        label = f"Joint {i+1}" if i < 6 else "Gripper"
        color = 'g' # Green for Baseline
        
        ax.plot(t, d[:, i], color=color, linewidth=2)
        ax.set_title(label)
        ax.set_ylabel("Angle" if i < 6 else "Value")
        ax.grid(True)

    # Hide 8th empty subplot
    axes[7].axis('off')

    fig.suptitle(f"Baseline Trajectory: {os.path.basename(base_file)}", fontsize=16)
    plt.xlabel("Time (s)")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save or Show? Let's show, but fail gracefully if headless
    try:
        plt.show()
    except:
        output_img = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'baseline_plot.png')
        plt.savefig(output_img)
        print(f"Saved plot to: {output_img}")

if __name__ == "__main__":
    main()
