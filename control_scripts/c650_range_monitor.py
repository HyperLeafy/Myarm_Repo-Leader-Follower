#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import time
import sys
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

def main():
    print("=== MyArm C650 Range Monitor ===")
    print("This script helps you find your desired offsets/limits.")
    print("Move the robot arm manually, and this script will record the Min/Max angles observed.")
    
    port = select_port("Select LEADER (C650) port:")
    try:
        mc = MyArmC(port, 1000000)
        print("Connected.")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    min_angles = [999.0] * 7
    max_angles = [-999.0] * 7
    
    print("\nReading angles... (Press Ctrl+C to stop and see final report)")
    print("-" * 60)
    print(f"{'Joint':<6} | {'Current':<10} | {'Min Observed':<12} | {'Max Observed':<12}")
    print("-" * 60)

    try:
        while True:
            angles = mc.get_joints_angle()
            if angles and len(angles) >= 6:
                # Ensure we handle up to 7 joints (arm + gripper)
                count = len(angles)
                
                # Update Min/Max
                for i in range(count):
                    if angles[i] < min_angles[i]: min_angles[i] = angles[i]
                    if angles[i] > max_angles[i]: max_angles[i] = angles[i]
                
                # Print real-time status (overwrite lines to keep terminal clean-ish)
                # Using carriage return \r and ANSI escape codes to move cursor up if possible, 
                # but simple print block is safer for all terminals.
                
                print(f"\033[{count+1}A") # Move cursor up 'count+1' lines
                for i in range(count):
                    print(f"J{i+1:<5} | {angles[i]:<10.2f} | {min_angles[i]:<12.2f} | {max_angles[i]:<12.2f}")
                
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n" + "-" * 60)
        print("Final Report:")
        print("-" * 60)
        print(f"{'Joint':<6} | {'Min':<10} | {'Max':<10}")
        count = len(angles) if 'angles' in locals() and angles else 6
        for i in range(count):
             # Handle case where no valid angle was ever read
            mn = min_angles[i] if min_angles[i] != 999.0 else "N/A"
            mx = max_angles[i] if max_angles[i] != -999.0 else "N/A"
            print(f"J{i+1:<5} | {mn:<10} | {mx:<10}")
            
    finally:
        try: mc._serial_port.close()
        except: pass

if __name__ == "__main__":
    main()
