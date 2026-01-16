#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import time
import sys
import csv
import os
import datetime
import serial.tools.list_ports
from pymycobot import MyArmC

def list_serial_ports():
    return [p.device for p in serial.tools.list_ports.comports()]

def select_port(prompt):
    ports = list_serial_ports()
    if not ports:
        print("No serial ports found!")
        sys.exit(1)
    
    print(f"\n{prompt}")
    for i, p in enumerate(ports):
        print(f"  {i+1}: {p}")
        
    while True:
        try:
            choice = input("Select port number: ")
            idx = int(choice) - 1
            if 0 <= idx < len(ports):
                return ports[idx]
        except ValueError:
            pass
        print("Invalid selection. Try again.")

def ensure_data_dir():
    # Ensure data/raw directory exists relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_dir = os.path.join(project_root, 'data', 'raw')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def main():
    print("=== MyArm C650 Motion Logger ===")
    print("Records joint angles to CSV.")

    # 1. Connect
    port = select_port("Select LEADER (C650) port:")
    try:
        leader = MyArmC(port, 1000000)
        print("Connected.")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    # 2. Setup File
    data_dir = ensure_data_dir()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(data_dir, f"c650_motion_{timestamp}.csv")
    
    print(f"Logging to: {filename}")
    print("Press Ctrl+C to stop recording.")

    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Header: Timestamp, J1, J2, J3, J4, J5, J6, Gripper
            writer.writerow(['Timestamp', 'J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7'])
            
            start_time = time.time()
            
            print(f"Logging started at {datetime.datetime.now().strftime('%H:%M:%S')}")
            
            while True:
                angles = leader.get_joints_angle()
                
                # Validation
                if not isinstance(angles, list):
                    # print(f"\r[Warn] Read returned non-list: {angles}", end="")
                    time.sleep(0.05)
                    continue
                    
                if len(angles) < 7:
                    # print(f"\r[Warn] Incomplete data: {angles}", end="")
                    time.sleep(0.05)
                    continue

                current_time = time.time() - start_time
                row = [f"{current_time:.4f}"] + [f"{a:.2f}" for a in angles]
                writer.writerow(row)
                csvfile.flush() # CRITICAL: Ensure data hits disk
                
                # Feedback
                print(f"\rTime: {current_time:.2f}s | Angles: {[int(a) for a in angles[:6]]}", end="")
                    
                time.sleep(0.05) # 20Hz logging

    except KeyboardInterrupt:
        print(f"\n\nStopping... Saved to {filename}")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        try: leader._serial_port.close()
        except: pass

if __name__ == "__main__":
    main()
