#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import argparse
import csv
import glob
import os
import sys
import matplotlib.pyplot as plt

def get_latest_log_file(data_dir):
    files = glob.glob(os.path.join(data_dir, "teleop_log_*.csv"))
    if not files:
        return None
    # Sort by modification time
    return max(files, key=os.path.getmtime)

def main():
    parser = argparse.ArgumentParser(description="Plot Joint Data from Teleop Logs")
    parser.add_argument("--joint", type=int, required=True, help="Joint ID (1-7)")
    parser.add_argument("--file", type=str, help="Path to CSV log file (optional, defaults to latest)")
    args = parser.parse_args()

    joint_idx = args.joint
    if not (1 <= joint_idx <= 7):
        print("Error: Joint ID must be between 1 and 7")
        sys.exit(1)

    # Resolve File
    if args.file:
        csv_file = args.file
    else:
        # Default to data/processed
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        data_dir = os.path.join(project_root, 'data', 'raw')
        # dynamically takes the latest file
        # csv_file = get_latest_log_file(data_dir)
        
        # give hardcoded file path
        csv_file = os.path.join(data_dir, 'c650_motion_20260108_171714.csv')
        
        if not csv_file:
            print(f"No log files found in {data_dir}")
            sys.exit(1)

    print(f"Plotting Joint {joint_idx} from: {csv_file}")

    # Data Containers
    timestamps = []
    inputs = []
    outputs = []
    norms = []
    
    # Column Names
    col_input = f"Input_J{joint_idx}"
    # Column Names (will be redefined based on format detection)
    col_norm = f"Norm_J{joint_idx}"
    
    # Read Data
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        
        # Detect Format
        mode = "PROCESSED"
        if f"Input_J{joint_idx}" in fields:
            col_input = f"Input_J{joint_idx}"
            col_output = f"Output_J{joint_idx}" if f"Output_J{joint_idx}" in fields else None
            col_norm = f"Norm_J{joint_idx}" if f"Norm_J{joint_idx}" in fields else None
             # Gripper special case
            if joint_idx == 7:
                 col_output = 'Gripper_Out' if 'Gripper_Out' in fields else None
        elif f"J{joint_idx}" in fields:
            mode = "RAW"
            col_input = f"J{joint_idx}"
            col_output = None
            col_norm = None
        else:
            print(f"Error: Could not find columns for Joint {joint_idx}. Available: {fields}")
            sys.exit(1)
            
        print(f"Format: {mode}. plotting...")

        for row in reader:
            try:
                # Timestamp handling (Raw uses 'Timestamp', Processed uses 'Timestamp')
                # But raw values are float seconds, Processed values are usually HH:MM:SS string or float?
                # Let's try float conversion, if fails, try string parse?
                t_raw = row['Timestamp']
                try:
                    t = float(t_raw)
                except ValueError:
                    # Parse HH:MM:SS.fff
                    # Assuming today's date? Or just index?
                    t = float(len(timestamps)) * 0.1 # Fallback
                
                inp = float(row[col_input])
                
                if col_output:
                    outputs.append(float(row[col_output]))
                if col_norm:
                    norms.append(float(row[col_norm]))
                
                timestamps.append(t)
                inputs.append(inp)
                
            except ValueError:
                continue

    # Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # 1. Angles
    ax1.plot(timestamps, inputs, label=f'Input (Joint {joint_idx})', color='red')
    if outputs:
        ax1.plot(timestamps, outputs, label=f'Output (M750)', color='blue')
          
    ax1.set_ylabel('Angle (deg)')
    ax1.set_title(f'Joint {joint_idx} Analysis')
    ax1.legend()
    ax1.grid(True)
    
    # 2. Normalized
    if norms:
        ax2.plot(timestamps, norms, label='Normalized (0.0 - 1.0)', color='green')
        ax2.set_ylabel('Norm Factor')
        ax2.set_ylim(-0.1, 1.1)
        ax2.axhline(0, color='black', linestyle='--', alpha=0.3)
        ax2.axhline(1, color='black', linestyle='--', alpha=0.3)
        ax2.legend()
        ax2.grid(True)
    else:
        ax2.text(0.5, 0.5, "No Normalized Data in Raw Log", ha='center', va='center')
    
    ax2.set_xlabel('Time (s)')
    
    # Headless fallback
    try:
        plt.show()
    except:
        out_img = os.path.join(os.path.dirname(csv_file), f"plot_j{joint_idx}.png")
        plt.savefig(out_img)
        print(f"Saved plot to {out_img}")

if __name__ == "__main__":
    main()
