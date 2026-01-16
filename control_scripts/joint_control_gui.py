from argparse import _StoreFalseAction
from PIL._imaging import font
import os 
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
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
        self.root.geometry("750x450")
        self.arm = None
        self.connect_status = False
        self.slider = []
        self.pack(fill="both", expand=True)
        self.create_widgets()
        self.ports = list_serial_ports()

    def refresh_ports(self):
        ports = list_serial_ports()
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.set(ports[0])
        else:
            self.port_combo.set("No ports found")
     
    def fetch_angles(self):
        if self.connect_status:
            angles = self.arm.get_angles()
            return angles
        else:
            return None
    def toggle_connection(self):
        if self.arm is None:
            port = self.port_combo.get()
            if not port or port == "No ports found":
                messagebox.showerror("Error", "Please select a port.")
                return
            try:
                self.arm = MyArmMControl(port)
                if self.arm.is_powered_on() == 1:
                    self.connect_btn.config(text="Disconnect", bg="#f44336", fg="white")
                    self.connect_btn.config(state="disabled")
                    messagebox.showinfo("Success", f"M750 connected successfully on {port}")
                    self.connect_status = True
                else:
                    messagebox.showerror("Error", "M750 is not powered on.")
            except Exception as err:
                messagebox.showerror("Error", str(err))
        else:
            self.arm = None
            self.connect_btn.config(text="Connect", fg="white", bg="green")
            self.connect_btn.config(state="readonly")
            self.connect_status = False

    def create_widgets(self):
        # Port Section
        header_frame = tk.Frame(self, pady=20)
        header_frame.pack(fill="x", padx=20)

        # Port selection widget
        tk.Label(header_frame, text="PORT", font=("Arial", 24, "bold")).pack(side="left")
        self.port_combo = ttk.Combobox(header_frame, width=15, font=("Arial", 24), state="readonly")
        self.port_combo.pack(side="left", padx=10)
        self.refresh_ports()

        # Refresh Button
        refresh_btn = tk.Button(header_frame, text="Refresh", font=("Arial", 10, "bold"), command=self.refresh_ports, width=10)
        refresh_btn.pack(side="left", padx=5)

        # Connection Button
        self.connect_btn = tk.Button(header_frame, text="Connect", command=self.toggle_connection, font=("Arial", 10, "bold"), width=10, bg="green", fg="white")
        self.connect_btn.pack(side="left", padx=10)

        # Separator
        tk.Frame(self, height=2, bd=1, relief="sunken").pack(fill="x", padx=10, pady=5)
        
        # Controller Section
        grid_controller_frame = tk.Frame(self, pady=20)
        grid_controller_frame.pack(expand=True, fill="both", padx=10, pady=10)

        for i in range(7):
            row = i // 2
            col = i % 2

            joint_block = tk.Frame(grid_controller_frame, bg="#E0E0E0", padx=10, pady=10)
            joint_block.grid(row=row, column=col, padx=10, pady=10)

            joint_label = tk.Label(joint_block, text=f"Joint {i+1}", font=("Helvetica", 12, "bold"))
            joint_label.pack(side="left")

            joint_slider = tk.Scale(joint_block, from_=-180, to=180, orient="horizontal", showvalue=True)
            joint_slider.pack(side="left")


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