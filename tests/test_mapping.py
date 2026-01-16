#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
import os
import csv
import glob
import pytest

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import mapping
import config

def test_limits_compliance():
    """
    Verify that ALMOST ANY input angle from the C650
    maps to a safe angle for the M750.
    """
    print("\n--- Testing Synthetic Extremes ---")
    
    # Test cases: [Min, Zero, Max] for C650 limits
    test_inputs = [
        [-180] * 6, # Extreme Low
        [0] * 6,    # Zero
        [180] * 6,  # Extreme High
        # Actual C650 limits from config
        [lim[0] for lim in config.C650_LIMITS[:6]], 
        [lim[1] for lim in config.C650_LIMITS[:6]],
    ]

    for i, raw_angles in enumerate(test_inputs):
        mapped, _ = mapping.process_arm_angles(raw_angles)
        
        # Check each joint
        for j in range(6):
            val = mapped[j]
            m_min, m_max = config.M750_LIMITS[j]
            
            # Check soft limits (with tiny floating point tolerance)
            safe_min = min(m_min, m_max) - 0.01
            safe_max = max(m_min, m_max) + 0.01
            
            # Pytest assertion: Shows detailed diff on failure
            assert safe_min <= val <= safe_max, \
                f"Joint {j+1} mapped value {val} out of bounds {config.M750_LIMITS[j]} for input {raw_angles[j]}"
            
    print("Synthetic checks passed.")

def test_raw_data_compliance():
    """
    If raw log files exist in data/raw/, read them and strictly check 
    that every single recorded frame maps to a safe value.
    """
    print("\n--- Testing Raw Log Data ---")
    
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'raw')
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    if not csv_files:
        pytest.skip(f"No CSV logs found in {data_dir}. Skipping data test.")
        return

    for csv_file in csv_files:
        print(f"Testing file: {os.path.basename(csv_file)}")
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader, None) # Skip header
            
            row_count = 0
            for row in reader:
                row_count += 1
                try:
                    # Convert J1-J6 to float
                    raw_angles = [float(x) for x in row[1:7]]
                    
                    mapped, _ = mapping.process_arm_angles(raw_angles)
                    
                    for j in range(6):
                        val = mapped[j]
                        m_min, m_max = config.M750_LIMITS[j]
                        safe_min = min(m_min, m_max) - 0.01
                        safe_max = max(m_min, m_max) + 0.01
                        
                        assert safe_min <= val <= safe_max, \
                            f"Row {row_count} in {os.path.basename(csv_file)}: Joint {j+1} unsafe! Input {raw_angles[j]} -> {val}"
                            
                except ValueError:
                    continue # Skip malformed rows
                except IndexError:
                    continue
            
            print(f"  Verified {row_count} frames.")
