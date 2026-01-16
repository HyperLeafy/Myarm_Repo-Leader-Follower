from pymycobot import MyArmC, MyArmMControl
# from utils import connection

import sys
import serial.tools.list_ports

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


M750_PORT = select_port("Select Port M750")

def list_limit():
    m750 = MyArmMControl(M750_PORT, 1000000)
    
    # realse all servo 
    m750.release_all_servos()

    for i in range(1,6):
        max_joint = m750.get_joint_max(i)
        min_joint = m750.get_joint_min(i)
        print(f"Joint {i}: Max={max_joint}, Min={min_joint}")
    # m750.serial_close()

def set_limits():
    m750 = MyArmMControl(M750_PORT, 1000000)
    
    # realse all servo 
    m750.release_all_servos()
    min_limit = [-165, -80, -100, -160, -90, -180, -118]
    max_limit = [165, 100, 80, 160, 120, 180, 2]
    for i in range(1,6):
        m750.set_joint_min(i, min_limit[i-1])
        m750.set_joint_max(i, max_limit[i-1])

if __name__ == "__main__":
    list_limit()
    # set_limits()
    # list_limit()


