import time
import sys
import serial.tools.list_ports
from pymycobot import MyArmC, MyArmMControl

# --- Configuration & Helper Functions ---

# Gripper mapping equation from official demo
gripper_angular_transformation_equations = lambda x: round((x - 0.08) / (-95.27 - 0.08) * (-123.13 + 1.23) - 1.23)

# Joint limits for M750
M750_limit_info = [
    (-170, 170),
    (-83, 83),
    (-90, 84),
    (-155, 153),
    (-91, 88),
    (-153, 153),
    (-118, 2)
]

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

def flexible_parameters(angles: list, rollback: bool = True) -> list:
    """
    Applies joint angle conversions. 
    Crucial for Leader-Follower mapping between C650 and M750.
    """
    if len(angles) != 7:
        return angles

    # Create a copy to avoid modifying the original list in place if that causes issues
    processed_angles = list(angles)

    if rollback is True:
        # 1. Map gripper angle
        processed_angles[-1] = gripper_angular_transformation_equations(processed_angles[-1])
        # 2. Invert joints 2 and 3 (index 1 and 2)
        processed_angles[1] *= -1
        processed_angles[2] *= -1

    # 3. Apply joint limits
    final_positions = []
    for i, angle in enumerate(processed_angles):
        min_angle, max_angle = M750_limit_info[i]
        if angle < min_angle:
            final_positions.append(min_angle)
        elif angle > max_angle:
            final_positions.append(max_angle)
        else:
            final_positions.append(angle)

    return final_positions

# --- Main Teleoperation Loop ---

def main():
    print("=== MyArm Leader-Follower USB Teleop ===")
    print("This script connects directly to both the Leader (C650) and Follower (M750).")
    
    # 1. Connect to Leader (C650)
    leader_port = select_port("Select LEADER (C650) port:")
    print(f"Connecting to Leader at {leader_port}...")
    try:
        leader = MyArmC(leader_port, 1000000) # Default baudrate usually 1M
        print("Leader connected.")
    except Exception as e:
        print(f"Failed to connect to Leader: {e}")
        return

    # 2. Connect to Follower (M750)
    follower_port = select_port("Select FOLLOWER (M750) port:")
    print(f"Connecting to Follower at {follower_port}...")
    try:
        # User requested MyArmMControl for better gripper support
        follower = MyArmMControl(follower_port, 1000000)
        print("Follower connected.")
        
        # Explicitly enable gripper as requested
        print("Enabling gripper...")
        follower.set_gripper_enabled()
        time.sleep(0.5)
        
    except Exception as e:
        print(f"Failed to connect to Follower: {e}")
        return

    print("\nStarting Teleop... Press Ctrl+C to stop.")
    
    # Track errors to avoid spamming
    error_count = 0 
    
    try:
        while True:
            try:
                # Read angles from Leader
                angles = leader.get_joints_angle()
                
                # Check if read was successful
                if angles is None or len(angles) == 0:
                    continue
                    
                # Check for invalid values (communication errors)
                if max(angles) > 200 or min(angles) < -200:
                    continue

                # Reset error count on successful read
                error_count = 0

                # Process angles (Mapping & Limits)
                target_angles = flexible_parameters(angles, rollback=True)

                # Send to Follower
                # Speed=50 is standard for teleop smoothness
                follower.write_angles(target_angles, 50) # MyArmMControl uses write_angles
                
                # Small delay to prevent flooding serial bus
                time.sleep(0.02)
                
            except OSError as e:
                # Handle "Input/output error" (Errno 5) transparently if possible
                if error_count < 5:
                    print(f"Serial Error (retrying): {e}")
                    error_count += 1
                    time.sleep(0.5)
                else:
                    raise e

    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Closing connections...")
        # Try/Except close in case they weren't open
        try: leader._serial_port.close() 
        except: pass
        try: follower._serial_port.close() 
        except: pass
        print("Done.")

if __name__ == "__main__":
    main()
