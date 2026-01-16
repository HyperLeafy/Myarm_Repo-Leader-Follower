#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import argparse
import csv
import glob
import os
import sys
import math

def get_latest_log_file(data_dir):
    files = glob.glob(os.path.join(data_dir, "teleop_log_*.csv"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def mean(data):
    if not data: return 0.0
    return sum(data) / len(data)

def main():
    parser = argparse.ArgumentParser(description="Analyze Teleop Log Data")
    parser.add_argument("--file", type=str, help="Path to CSV log file (optional)")
    args = parser.parse_args()

    if args.file:
        csv_file = args.file
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        data_dir = os.path.join(project_root, 'data', 'processed')
        csv_file = get_latest_log_file(data_dir)
        
    if not csv_file:
        print("No log files found.")
        sys.exit(1)

    print(f"Analyzing: {os.path.basename(csv_file)}")
    print("-" * 80)
    print(f"{'Joint':<6} | {'Bias (Out-In)':<15} | {'Input Range':<15} | {'Output Range':<15} | {'Norm Limits (0/1)':<15}")
    print("-" * 80)

    # Read All Data
    data = {} # {j_idx: {'in':[], 'out':[], 'norm':[]}}
    for i in range(1, 8):
        data[i] = {'in': [], 'out': [], 'norm': []}

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        row_count = 0
        for row in reader:
            row_count += 1
            for i in range(1, 8): # Joints 1-7
                try:
                    inp = float(row[f"Input_J{i}"])
                    
                    if i == 7:
                        out = float(row.get("Gripper_Out", 0))
                        norm = 0.0 # Gripper norm usually not logged as separate column in early versions
                    else:
                        out = float(row[f"Output_J{i}"])
                        norm = float(row[f"Norm_J{i}"])

                    data[i]['in'].append(inp)
                    data[i]['out'].append(out)
                    data[i]['norm'].append(norm)
                except (ValueError, KeyError):
                    continue

    # Computations
    for i in range(1, 7): # Arm Joints
        jdata = data[i]
        inputs = jdata['in']
        outputs = jdata['out']
        norms = jdata['norm']
        
        if not inputs: continue

        # Bias (Mean difference)
        diffs = [o - inp for o, inp in zip(outputs, inputs)]
        bias = mean(diffs)
        
        # Ranges
        in_min, in_max = min(inputs), max(inputs)
        out_min, out_max = min(outputs), max(outputs)
        in_range = f"[{in_min:.1f}, {in_max:.1f}]"
        out_range = f"[{out_min:.1f}, {out_max:.1f}]"
        
        # Saturation (Norm hitting 0 or 1)
        sat_count = sum(1 for n in norms if n <= 0.01 or n >= 0.99)
        sat_pct = (sat_count / len(norms)) * 100
        
        print(f"J{i:<5} | {bias:<15.2f} | {in_range:<15} | {out_range:<15} | {sat_pct:.1f}%")

    print("-" * 80)
    
    # Gripper
    g_inputs = data[7]['in']
    g_outputs = data[7]['out']
    if g_inputs:
         g_min, g_max = min(g_inputs), max(g_inputs)
         g_out_min, g_out_max = min(g_outputs), max(g_outputs)
         print(f"Grip   | N/A             | [{g_min:.1f}, {g_max:.1f}]     | [{g_out_min:.1f}, {g_out_max:.1f}]     | N/A")

if __name__ == "__main__":
    main()
