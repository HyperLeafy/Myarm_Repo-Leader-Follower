
#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
import os
import json
import time
from datetime import datetime

# Adjust path to import config from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pymycobot import MyArmMControl
from utils import connection

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'baselines.json')

def load_baselines():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_baselines(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Saved to {DATA_FILE}")

import csv

def record_trajectory(m750):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = os.path.dirname(DATA_FILE) # data/
    traj_dir = os.path.join(base_dir, 'baselines')
    os.makedirs(traj_dir, exist_ok=True)
    
    filename = os.path.join(traj_dir, f"baseline_traj_{timestamp}.csv")
    
    print(f"\n--- Trajectory Mode ---")
    print(f"Recording to: {filename}")
    print("Press Ctrl+C to STOP recording.")
    print("Starting in 3 seconds...")
    time.sleep(3)
    print("GO!")
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "J1", "J2", "J3", "J4", "J5", "J6", "Gripper"])
        
        start_time = time.time()
        try:
            while True:
                angles = m750.get_angles()
                if not isinstance(angles, list) or len(angles) < 6:
                     # print(f"Invalid angles: {angles}")
                     time.sleep(0.01)
                     continue
                
                # Try to get gripper
                gripper = 0
                try:
                    gripper = m750.get_gripper_value()
                except:
                    pass

                t = time.time() - start_time
                row = [f"{t:.4f}"] + angles + [gripper]
                writer.writerow(row)
                
                print(f"\rRecording... T={t:.1f}s | J1={angles[0]:.2f}", end="")
                time.sleep(0.1) # 10Hz
                
        except KeyboardInterrupt:
            print(f"\nSaved {filename}")

def main():
    print("=== MyArm M750 Baseline Recorder ===")
    print("Select Mode:")
    print("1. Static Poses (Save single snapshots to JSON)")
    print("2. Trajectory Stream (Record continuous CSV to data/baselines/)")
    
    mode = input("Enter Mode (1 or 2): ").strip()
    
    port = connection.select_port("Select M750 (Follower) Port:")
    try:
        m750 = MyArmMControl(port, 1000000)
        print("Connected.")
        
        m750.release_all_servos()
        print("Servos Released. You can move the arm now.")
        time.sleep(1)
        
    except Exception as e:
        print(f"Connection Failed: {e}")
        return

    if mode == '2':
        record_trajectory(m750)
    else:
        # Static Mode
        baselines = load_baselines()

        try:
            while True:
                angles = m750.get_angles()
                if not angles:
                    print("Failed to read angles. Retrying...")
                    time.sleep(0.5)
                    continue
                    
                print(f"\rCurrent Angles: {[round(a, 2) for a in angles]}", end="")
                
                cmd = input("\n[Enter Name] to save, [q] to quit: ").strip()
                if cmd.lower() == 'q':
                    break
                
                if cmd:
                    angles = m750.get_angles()
                    entry = {
                        "timestamp": datetime.now().isoformat(),
                        "angles": angles,
                        "desc": cmd
                    }
                    baselines[cmd] = entry
                    save_baselines(baselines)
                    print(f"Saved pose '{cmd}': {angles}")
                
        except KeyboardInterrupt:
            print("\nExiting...")
    
    try:
        m750._serial_port.close()
    except:
        pass

if __name__ == "__main__":
    main()
