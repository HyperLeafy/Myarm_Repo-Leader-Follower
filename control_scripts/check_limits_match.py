#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
import os
import time

# Adjust path to import config/utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from pymycobot import MyArmMControl
    from utils import connection
    import config
except ImportError:
    print("Error: Could not import project modules.")
    sys.exit(1)

def main():
    print("=== Configuration vs Firmware Verification ===")
    
    # 1. Load Config Limits
    cfg_limits = config.M750_LIMITS
    print(f"Loaded {len(cfg_limits)} limits from config.py")
    
    # 2. Connect to Robot
    port = connection.select_port("Select M750 Port:")
    try:
        m750 = MyArmMControl(port, 1000000)
    except Exception as e:
        print(f"Connection Failed: {e}")
        return

    print("\nChecking Limits...")
    print(f"{'Joint':<6} | {'Config (Min, Max)':<20} | {'Firmware (Min, Max)':<20} | {'Status':<10}")
    print("-" * 65)
    
    all_match = True
    
    for i in range(6):
        joint_id = i + 1
        
        # Config values
        c_val1, c_val2 = cfg_limits[i]
        c_min = min(c_val1, c_val2)
        c_max = max(c_val1, c_val2)
        
        # Firmware values
        try:
            f_min = m750.get_joint_min(joint_id)
            f_max = m750.get_joint_max(joint_id)
        except Exception as e:
            print(f"J{joint_id:<5} | Error reading firmware: {e}")
            continue
            
        # Compare (Tolerance of 1 degree)
        match_min = abs(c_min - f_min) <= 1.0
        match_max = abs(c_max - f_max) <= 1.0
        
        status = "OK" if (match_min and match_max) else "MISMATCH"
        if status == "MISMATCH": all_match = False
        
        color = "\033[92m" if status == "OK" else "\033[91m"
        reset = "\033[0m"
        
        print(f"J{joint_id:<5} | ({c_min:>6.1f}, {c_max:>6.1f})      | ({f_min:>6.1f}, {f_max:>6.1f})      | {color}{status}{reset}")

    print("-" * 65)
    if all_match:
        print("\nSUCCESS: Firmware limits match configuration.")
    else:
        print("\nWARNING: Some limits do not match! The robot may stop before reaching config limits, or config assumes unreachable range.")

if __name__ == "__main__":
    main()
