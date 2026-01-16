#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import time
import sys
import os

# Import from local modules
# (Assuming running from project root or control_scripts folder, adjusting path if needed)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymycobot import MyArmC, MyArmMControl
from utils import connection, mapping

import threading

import csv
import datetime

class MonitorThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.running = True
        self.latest_data = {}
        
        # Setup CSV logging
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            'data', 'processed', 
            f'teleop_log_{timestamp}.csv'
        )
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        with open(self.log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            header = ["Timestamp"] + [f"Input_J{i}" for i in range(1, 7)] + \
                     ["Gripper_In"] + \
                     [f"Norm_J{i}" for i in range(1, 7)] + \
                     [f"Cmd_Output_J{i}" for i in range(1, 7)] + \
                     ["Gripper_Out"]
            writer.writerow(header)

    def stop(self):
        self.running = False

    def update(self, raw_in, mapped_arm, gripper_val, norm_vals):
        self.latest_data = {
            'raw': raw_in,
            'arm': mapped_arm,
            'gripper': gripper_val,
            'norm': norm_vals
        }

    def run(self):
        print(f"Monitor Thread Started. Logging to: {os.path.basename(self.log_file)}")
        while self.running:
            d = self.latest_data
            if not d:
                time.sleep(0.5)
                continue

            # Console Output (Dashboard)
            os.system('cls' if os.name == 'nt' else 'clear')
            print("=== Teleop Monitor (Input -> Norm -> Output) ===")
            print(f"  Input:         {[round(x,1) for x in d.get('raw', [])[:6]]}")
            print(f"  Norm (%):      {[round(x*100,0) for x in d.get('norm', [])]}")
            print(f"  Cmd Output:    {[round(x,1) for x in d.get('arm', [])]}")
            print(f"  Gripper:       In={d.get('raw', [])[6] if len(d.get('raw', []))>6 else 0} -> Out={d.get('gripper', 0)}")
            print("-" * 60)
            
            # CSV Logging
            try:
                with open(self.log_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    row = [datetime.datetime.now().strftime("%H:%M:%S.%f")] + \
                          [f"{x:.2f}" for x in d.get('raw', [])[:6]] + \
                          [f"{d.get('raw', [])[6]:.2f}" if len(d.get('raw', []))>6 else "0"] + \
                          [f"{x:.3f}" for x in d.get('norm', [])] + \
                          [f"{x:.2f}" for x in d.get('arm', [])] + \
                          [f"{d.get('gripper', 0)}"]
                    writer.writerow(row)
            except Exception as e:
                pass # Don't crash on logging error
            
            time.sleep(0.2)

def main():
    print("=== MyArm Leader-Follower (Teleop Explicit) ===")
    
    # 1. Connect to Leader (C650)
    leader_port = connection.select_port("Select LEADER (C650) port:")
    try:
        leader = MyArmC(leader_port, 1000000)
        print("Leader connected.")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    # 2. Connect to Follower (M750)
    follower_port = connection.select_port("Select FOLLOWER (M750) port:")
    try:
        follower = MyArmMControl(follower_port, 1000000)
        print("Follower connected.")
        follower.set_gripper_enabled()
        time.sleep(0.5)
    except Exception as e:
        print(f"Failed to connect: {e}")
        return
    
    # 3. Start Monitor Thread (Display & Logging)
    monitor = MonitorThread()
    monitor.start()

    print("\nStarting Teleop... Press Ctrl+C to stop.")
    
    try:
        while True:
            try:
                # Read 7 angles from Leader (6 arm + 1 gripper)
                angles = leader.get_joints_angle()
                
                if not angles or len(angles) < 7:
                    continue
                
                if max(angles) > 200 or min(angles) < -200:
                    continue

                # 1. Arm Control (First 6 joints)
                arm_angles, norm_vals = mapping.process_arm_angles(angles)
                follower.write_angles(arm_angles, 40)
                
                # 2. Gripper Control (7th joint)
                gripper_raw = angles[6]
                gripper_val = mapping.process_gripper(gripper_raw)
                
                follower.set_gripper_value(gripper_val, 50)
                
                # Update Monitor
                monitor.update(angles, arm_angles, gripper_val, norm_vals)

                time.sleep(0.02)
                
            except OSError as e:
                 time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopping...")
        monitor.running = False
    finally:
        try: leader._serial_port.close() 
        except: pass
        try: follower._serial_port.close() 
        except: pass

if __name__ == "__main__":
    main()