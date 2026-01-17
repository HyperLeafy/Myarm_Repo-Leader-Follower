from ast import arg
import threading
from argparse import _StoreFalseAction
from PIL._imaging import font
import os 
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont
from pymycobot import MyArmMControl


os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils.connection import list_serial_ports
except ImportError:
    print("Error: Could not import project modules.")
    sys.exit(1)

class JointController(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.root.title("M750 - Joint Controller")
        self.root.geometry("800x450")
        self.arm = None
        self.slider = []
        self.pack(fill="both", expand=True)
        self.create_widgets()
        self.ports = list_serial_ports()
        self.send_delay = 0.05
        self.debounce_id = None
        self.last_send_time = 0
        self.connect_status = False
        self.is_syncing = False
        

    def refresh_ports(self):
        ports = list_serial_ports()
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.set(ports[0])
        else:
            self.port_combo.set("No ports found")
        
    def connect_to_robot(self, port):
        try:
            self.arm = MyArmMControl(port)
            if self.arm:
                time.sleep(0.1)
                angles = self.fetch_angles()

                if angles is not None and len(angles) > 0:
                    self.connect_status = True
                    return True
                else:
                    self.arm = None
                    self.connect_status = False
                    return False
            else:
                self.arm = None
                self.connect_status = False
                return False
        except Exception as e:
            self.arm = None
            self.connect_status = False
            messagebox.showerror("Error", str(e))
            return False     

    def fetch_angles(self):
        if self.connect_status:
            angles = self.arm.get_angles()
            return angles
        else:
            return None

    # Debounce function to prevent sending too many requests to the robot
    def push_angles(self, speed = 60):
        ref_time = time.time()
        if self.connect_status:
            angles = self.slider
            self.arm.send_angles(angles, speed)
            if self.is_syncing and self.arm is None:
                return
            if time.time() - ref_time > self.send_delay:
                self._execute_push_angles()
                self.last_send_time = ref_time
            if self.debounce_id:
                self.root.after_cancel(self.debounce_id)

            self.debounce_id = self.root.after(100, lambda: self._push_angles_thread(speed))
    
    # Thread wrapper over function to send angles to the robot
    def _push_angles_thread(self, speed):
        threading.Thread(target=self._send_to_robot, arg=(speed,), daemon=True).start()
    
    # Function to send angles to the robot
    def _send_to_robot(self, speed):
        try:
            angles = [s.get() for s in self.slider]
            self.arm.send_angles(angles, speed)
        except Exception as e:
            print(f"Error sending angles: {e}")

    def sync_sliders(self,angles):
        angles = self.fetch_angles()
        if angles:
            # Writing data to angle buffer
            self.is_syncing = True          # Prevent slider buffer from updating while syncing  
            for i, angle in enumerate(angles):
                self.slider[i].set(angle)
            self.is_syncing = False         # Allow slider buffer to update
    
    def update_led(self):
        #Updates the LED color based on connection and power state.
        if not self.connect_status:
            color = "grey"      # No connection
        else:
            # Check robot power state via API
            if self.arm and self.arm.is_powered_on():
                color = "#00FF00"  # Bright Green (Power On)
            else:
                color = "#FF0000"  # Red (Connected but Power Off)
    
        self.status_led.itemconfig(self.led_circle, fill=color)
    
    def toggle_power(self):
        if self.connect_status and self.arm:
            try:
                if self.arm.is_power_on():
                    self.arm.power_off()
                    self.power_btn.config(bg="gray")
                else:
                    self.arm.power_on()
                    self.power_btn.config(bg="green")
                # Brief delay to allow hardware state to flip before we check it
                self.root.after(200, self.update_led)
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("Warning", "Connect to the robot first!")

    def toggle_connection(self):
        if not self.connect_status:
            port = self.port_combo.get()
            # Wrong Port selectin
            if not port or port == "No ports found":
                messagebox.showerror("Error", "Please select a port.")
                return
            # Success
            if self.connect_to_robot(port):
                print("Connection Success")
                if self.connect_status :
                    self.connect_btn.config(text="Disconnect", bg="#f44336", fg="white")
                    self.port_combo.config(state="disabled")

                    self.update_led()
                    angles = self.fetch_angles()
                    self.root.after(500, self.sync_sliders(angles))

                    messagebox.showinfo("Connected", f"Successfully linked to {port}")

            # Failure
            else:
                print("Connection Failed")
                self.connect_status = False
                self.connect_btn.config(text="Connect", bg="green", fg="white")
                self.port_combo.config(state="readonly")

                self.update_led()

                messagebox.showerror("Connection Failed", f"Could not communicate with M750 on {port}. Check the cable and ensure the robot is powered on.")
        # Disconnect
        else:
            print("Disconnecting from robot")
            self.arm = None
            self.connect_btn.config(text="Connect", fg="white", bg="green")
            self.port_combo.config(state="readonly")
            self.connect_status = False
            self.update_led()

    def create_widgets(self):
        # Port Section
        header_frame = tk.Frame(self, pady=20)
        header_frame.pack(fill="x", padx=20)

        # Port selection widget
        tk.Label(header_frame, text="PORT", font=("Helvetica", 24, "bold")).pack(side="left")
        self.port_combo = ttk.Combobox(header_frame, width=20, font=("Helvetica", 24), state="readonly")
        self.port_combo.pack(side="left", padx=10)
        self.refresh_ports()

        # Setting font for drop down
        drop_down_font = tkfont.Font(family="Helvetica", size=16, )
        self.port_combo.configure(font=drop_down_font)

        # Refresh Button
        refresh_btn = tk.Button(header_frame, text="Refresh", font=("Helvetica", 14, "bold"), command=self.refresh_ports, width=10)
        refresh_btn.pack(side="left", padx=5)

        # Connection Button
        self.connect_btn = tk.Button(header_frame, text="Connect", command=self.toggle_connection, font=("Helvetica", 14, "bold"), width=10, bg="green", fg="white")
        self.connect_btn.pack(side="left", padx=10)

        # Power button
        self.power_btn = tk.Button(header_frame, text="Power", command=self.toggle_power, font=("Helvetica", 14, "bold"), width=10, bg="green", fg="white")
        self.power_btn.pack(side="left", padx=10)

        # Status LED (The Signal)
        self.status_led = tk.Canvas(header_frame, width=20, height=20, highlightthickness=0)
        self.status_led.pack(side="left", padx=5)
        # Draw the initial grey circle
        self.led_circle = self.status_led.create_oval(2, 2, 18, 18, fill="grey")

        # Separator
        tk.Frame(self, height=2, bd=1, relief="sunken").pack(fill="x", padx=10, pady=5)
        
        # Controller Section
        grid_controller_frame = tk.Frame(self, pady=20)
        grid_controller_frame.pack(expand=True, fill="both", padx=10, pady=10)

        for i in range(7):
            row = i // 3
            col = i % 3

            joint_block = tk.Frame(grid_controller_frame, bg="#E0E0E0", padx=10, pady=10)
            joint_block.grid(row=row, column=col, padx=10, pady=10)

            joint_label = tk.Label(joint_block, text=f"Joint {i+1}", font=("Helvetica", 14, "bold"))
            joint_label.pack(side="left")

            joint_slider = tk.Scale(joint_block, from_=-180, to=180, orient="horizontal", showvalue=True, command=self.push_angles)
            joint_slider.pack(side="left")
            self.slider.append(joint_slider)

def main():
    try :
        root = tk.Tk()
        app = JointController(root)
        app.mainloop()

        app.after(1000, lambda: app.destroy())

    except Exception as e:
        messagebox.showerror("Error", str(e))
    
if __name__ == "__main__":
    main()