from pymycobot.myarm import MyArm
import serial.tools.list_ports

def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"Found port: {port.device}")

def main():
    print("Checking dependencies...")
    try:
        import pymycobot
        import numpy
        print("Dependencies imported successfully.")
    except ImportError as e:
        print(f"Failed to import dependencies: {e}")
        return

    print("Listing available serial ports:")
    list_serial_ports()

    # Uncomment the following lines to connect to a real robot
    port = "/dev/ttyACM0"  # Replace with your actual port
    baud = 1000000
    try:
        mc = MyArm(port, baud)
        print("Connected to MyArm!")
        print(mc.get_angles())
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    main()
