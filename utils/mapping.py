import sys
import os

# Adjust path to import config from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def map_value(x, in_min, in_max, out_min, out_max):
    # Standard linear mapping
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def process_arm_angles(angles: list) -> list:
    """
    Process first 6 joints using Proportional Mapping.
    
    Logic:
    1. Input C650 Angle.
    2. Normalize to C650 Range (Min -> Max).
    3. Map to M750 Range (Min -> Max).
    
    INVERSION:
    Joints 2 and 3 (Indices 1 and 2) are physically inverted between C and M series.
    We handle this by mapping:
    C650 (Min -> Max)  ===>  M750 (Max -> Min)
    """
    if len(angles) < 6:
        return angles, []

    raw_angles = list(angles[:6])
    final_positions = []
    normalized_values = []

    for i in range(6):
        # 1. Get Input Limits & Calculate Normalization
        try:
            c_min, c_max = config.C650_LIMITS[i]
        except IndexError:
            c_min, c_max = -180, 180
            
        # Apply Input Offset (Calibration)
        input_offset = 0.0
        try:
             input_offset = config.C650_HOME_ANGLES[i]
        except IndexError:
             pass
        val = raw_angles[i] + input_offset
        
        # Normalize (0.0 to 1.0)
        # norm = (val - min) / (max - min)
        if c_max != c_min:
            norm = (val - c_min) / (c_max - c_min)
        else:
            norm = 0.5
            
        normalized_values.append(norm)

        # 2. Get Output Limits (Target)
        try:
            m_min, m_max = config.M750_LIMITS[i]
        except IndexError:
            m_min, m_max = -180, 180

        # 3. Determine Direction (Inversion)
        # Check M750_GAINS for direction (-1.0 means invert output range)
        inverted = False
        try:
            if config.M750_GAINS[i] < 0:
                inverted = True
        except:
            # Fallback for old config
            if i in [0, 5]: inverted = True # J1, J6 default invert
        
        if inverted:
            out_start = m_max
            out_end = m_min
        else:
            out_start = m_min
            out_end = m_max

        # 4. Map Normalized -> Output
        # output = norm * (out_range) + out_start
        target_angle = norm * (out_end - out_start) + out_start

        # 5. Apply Hard Safety Clamps
        safe_min = min(m_min, m_max)
        safe_max = max(m_min, m_max)
        
        if target_angle < safe_min: target_angle = safe_min
        if target_angle > safe_max: target_angle = safe_max
        
        final_positions.append(target_angle)

    return final_positions, normalized_values

def process_gripper(angle):
    """
    Map Leader gripper angle to 0-100 value.
    Uses proportional mapping from config.
    """
    # Use limits from C650 limits if available (Index 6), or specific constants if preferred.
    # User's config.py has LEADER_GRIPPER_CLOSED/OPEN constants.
    
    val = map_value(angle, config.LEADER_GRIPPER_CLOSED, config.LEADER_GRIPPER_OPEN, 0, 100)
    
    # Constrain
    if val < 0: val = 0
    if val > 100: val = 100
    
    return int(val)
