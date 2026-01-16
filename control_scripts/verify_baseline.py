#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
import os
import json
import time

# Adjust path to import config from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pymycobot import MyArmC
from utils import connection, mapping

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'baselines.json')

def load_baselines():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def main():
    print("=== MyArm Baseline Verifier (Leader Only) ===")
    
    baselines = load_baselines()
    if not baselines:
        print(f"No baselines found in {DATA_FILE}. Run record_baseline.py first.")
        return

    print("\nAvailable Baselines:")
    keys = list(baselines.keys())
    for i, k in enumerate(keys):
        print(f"{i+1}: {k} (rec: {baselines[k]['timestamp']})")
        
    try:
        idx = int(input("\nSelect Pose Number to Verify: ")) - 1
        target_name = keys[idx]
        target_angles = baselines[target_name]['angles']
        print(f"Selected Target: {target_name}")
        print(f"Target Values (M750): {[round(x, 2) for x in target_angles]}")
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    # Connect to Leader
    port = connection.select_port("Select C650 (Leader) Port:")
    try:
        leader = MyArmC(port, 1000000)
    except Exception as e:
        print(f"Connection Failed: {e}")
        return

    print("\nStarting Verification Loop...")
    print("Move the Leader to the physical pose corresponding to the target.")
    print("Watch the ERROR (Mapped - Target). Goal is 0.0.")
    print("-" * 60)
    
    try:
        while True:
            # Read Leader
            raw_angles = leader.get_joints_angle()
            if not raw_angles or len(raw_angles) < 6:
                continue

            # Process using LIVE config/mapping logic
            mapped_angles, norm_vals = mapping.process_arm_angles(raw_angles)
            
            # Compare
            # We match first 6 joints. Target might have 7 if it included gripper? 
            # Usually baselines has whatever get_joints_angle returned.
            
            print(f"\r[ {target_name} ] ERROR:", end="")
            for i in range(6):
                if i >= len(target_angles): break
                
                target = target_angles[i]
                current = mapped_angles[i]
                err = current - target
                
                # Colorize logic? Just text for now.
                print(f" J{i+1}:{err:>6.1f}", end="|")
                
            sys.stdout.flush()
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        leader._serial_port.close()

if __name__ == "__main__":
    main()
