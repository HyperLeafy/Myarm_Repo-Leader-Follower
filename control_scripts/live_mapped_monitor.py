#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
import os
import time
import numpy as np

# Adjust path to import config/utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from pymycobot import MyArmC
    from utils import connection, mapping
except ImportError:
    print("Error: Could not import project modules.")
    sys.exit(1)

def main():
    print("=== MyArm C650 Live Mapping Monitor ===")
    print("Connecting to Leader...")
    
    port = connection.select_port("Select C650 Leader Port:")
    try:
        leader = MyArmC(port, 1000000)
        print("Connected.")
    except Exception as e:
        print(f"Connection Failed: {e}")
        return
        
    print("\nStarting Monitoring loop... (Ctrl+C to Stop)")
    
    try:
        while True:
            angles = leader.get_joints_angle()
            
            if angles and len(angles) >= 6:
                # Process
                outputs, norms = mapping.process_arm_angles(angles)
                
                # Clear Screen / Move Cursor Home (ANSI)
                # print("\033[H\033[J", end="") # Clear whole screen? Might flicker.
                # Just print a few newlines or specific clear?
                # Let's simple use "Move Cursor to Top-Left" + clear if easy, 
                # or just print a large block of text.
                # Better: Clear screen once at start, then just overwrite? 
                # Simple approach for now: clear command.
                os.system('cls' if os.name == 'nt' else 'clear')

                print("=== C650 -> M750 Live Mapping ===")
                print(f"{'Joint':<5} | {'Input (C650)':<12} | {'Norm (0-1)':<10} | {'Output (M750)':<13}")
                print("-" * 50)
                
                for i in range(6):
                    j_in = angles[i]
                    j_norm = norms[i]
                    j_out = outputs[i]
                    
                    # Highlights?
                    # If norm is clamped (0 or 1), maybe bold?
                    
                    print(f"J{i+1:<4} | {j_in:<12.2f} | {j_norm:<10.3f} | {j_out:<13.2f}")
                    
                print("-" * 50)
                print(f"Time: {time.time():.2f}")
                
            time.sleep(0.1) # 10Hz Refresh
            
    except KeyboardInterrupt:
        print("\nStopped.") 
            
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()
