#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import argparse
import csv
import glob
import sys
import os
import datetime

# Adjust path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils import mapping
except ImportError:
    print("Error: Could not import utils.mapping")
    sys.exit(1)

def get_latest_file(directory, pattern):
    files = glob.glob(os.path.join(directory, pattern))
    if not files: return None
    return max(files, key=os.path.getmtime)

def main():
    parser = argparse.ArgumentParser(description="Process Raw C650 Log -> Mapped Teleop Log")
    parser.add_argument("--file", help="Path to Raw Log (defaults to latest in data/raw/)")
    args = parser.parse_args()

    # 1. Resolve Input File
    if args.file:
        input_file = args.file
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        raw_dir = os.path.join(base_dir, 'data', 'raw')
        input_file = get_latest_file(raw_dir, "c650_motion_*.csv")
        if not input_file:
            print(f"Error: No raw logs found in {raw_dir}")
            sys.exit(1)

    print(f"Processing: {os.path.basename(input_file)}")

    # 2. Setup Output File
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, 'data', 'processed')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"teleop_log_from_raw_{timestamp}.csv")

    print(f"{'Time':<8} | {'Joint':<5} | {'Input':<8} | {'Norm':<6} | {'Output':<8}")
    print("-" * 50)

    with open(input_file, 'r') as fin, open(output_file, 'w', newline='') as fout:
        reader = csv.DictReader(fin)
        writer = csv.writer(fout)
        
        # Header matching teleop_explicit.py format
        header = ["Timestamp"] + [f"Input_J{i}" for i in range(1, 7)] + \
                 ["Gripper_In"] + \
                 [f"Norm_J{i}" for i in range(1, 7)] + \
                 [f"Output_J{i}" for i in range(1, 7)] + \
                 ["Gripper_Out"]
        writer.writerow(header)
        
        count = 0
        for row in reader:
            try:
                t = row['Timestamp']
                inputs = [float(row[f"J{i}"]) for i in range(1, 7)]
                gripper_in = float(row.get('J7', 0))
                
                # Process
                outputs, norms = mapping.process_arm_angles(inputs)
                gripper_out = mapping.process_gripper(gripper_in)
                
                # Write
                out_row = [t] + \
                          [f"{x:.2f}" for x in inputs] + \
                          [f"{gripper_in:.2f}"] + \
                          [f"{x:.3f}" for x in norms] + \
                          [f"{x:.2f}" for x in outputs] + \
                          [f"{gripper_out}"]
                
                writer.writerow(out_row)
                
                # Print Table (Sampled freq to avoid spam, or just print J2/J3 critical ones?)
                # User wants to SEE values. Let's print J2 specifically as it was the focus.
                if count % 5 == 0: # 5Hz sample for display
                     print(f"{t[:6]:<8} | {'J2':<5} | {inputs[1]:<8.2f} | {norms[1]:<6.3f} | {outputs[1]:<8.2f}")
                
                count += 1
            except (ValueError, KeyError):
                continue

    print(f"Processed {count} rows.")
    print(f"Saved to: {output_file}")

if __name__ == "__main__":
    main()
