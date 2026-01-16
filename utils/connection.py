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
