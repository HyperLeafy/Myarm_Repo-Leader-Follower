#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
import os
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# Adjust path to import config/utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from pymycobot import MyArmMControl
    from utils import connection
except ImportError:
    print("Error: Could not import project modules.")
    sys.exit(1)

class SingleJointController:
    def __init__(self, master, robot, joint_id):
        self.master = master
        self.robot = robot
        self.joint_id = joint_id
        
        self.master.title(f"M750 Control - Joint {joint_id}")
        self.master.geometry("400x250")
        
        # 1. Get Firmware Limits
        try:
            self.min_limit = self.robot.get_joint_min(joint_id)
            self.max_limit = self.robot.get_joint_max(joint_id)
            print(f"Joint {joint_id} Limits: [{self.min_limit}, {self.max_limit}]")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read limits: {e}")
            self.min_limit = -180
            self.max_limit = 180

        # UI Setup
        self.create_widgets()
        
        # Start Live Update Loop (to show actual pos)
        self.running = True
        self.update_thread = threading.Thread(target=self.monitor_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
def main():
    root = tk.Tk()
    app = JointController(root)
    root.mainloop()

if __name__ == "__main__":
    main()
    def old_create_widgets(self):
        # Styles
        style = ttk.Style()
        style.configure("TLabel", font=("Helvetica", 12))
        
        # Header
        header = ttk.Label(self.master, text=f"Controlling Joint {self.joint_id}", font=("Helvetica", 16, "bold"))
        header.pack(pady=10)
        
        # Range Info
        range_lbl = ttk.Label(self.master, text=f"Firmware Limit: {self.min_limit:.1f}° to {self.max_limit:.1f}°")
        range_lbl.pack(pady=5)
        
        # Current Value Display
        self.current_val_var = tk.StringVar(value="Current: ---")
        curr_lbl = ttk.Label(self.master, textvariable=self.current_val_var, foreground="blue")
        curr_lbl.pack(pady=5)
        
        # Slider Container (for padding)
        slider_frame = ttk.Frame(self.master)
        slider_frame.pack(fill="x", padx=20, pady=20)
        
        # Slider
        # Note: scale from Min to Max
        self.slider_var = tk.DoubleVar()
        self.slider = tk.Scale(slider_frame, 
                               from_=self.min_limit, 
                               to=self.max_limit, 
                               orient='horizontal', 
                               variable=self.slider_var,
                               command=self.on_slider_change,
                               length=300,
                               resolution=0.1)
        self.slider.pack()
        
        # Release Button
        btn_rel = ttk.Button(self.master, text="RELEASE SERVOS", command=self.release_servos)
        btn_rel.pack(pady=10)

    def on_slider_change(self, val):
        angle = float(val)
        # Send command (Joint, Angle, Speed)
        # Speed 50 is moderate
        try:
            self.robot.send_angle(self.joint_id, angle, 80)
        except Exception as e:
            print(f"Send Error: {e}")

    def release_servos(self):
        print("Releasing servos...")
        self.robot.release_all_servos()

    def monitor_loop(self):
        while self.running:
            try:
                # Read actual angle
                angles = self.robot.get_angles()
                if angles and len(angles) >= self.joint_id:
                    actual = angles[self.joint_id - 1]
                    self.current_val_var.set(f"Actual: {actual:.2f}°")
                    
                    # Optional: Sync slider to actual if not being dragged?
                    # might cause fighting. Let's just monitor.
            except Exception:
                pass
            time.sleep(0.1)

    def on_close(self):
        self.running = False
        self.master.destroy()

def main():
    print("=== M750 Single Joint Control Board ===")
    
    # Connection
    port = connection.select_port("Select M750 Port:")
    try:
        robot = MyArmMControl(port, 115200) 
        # Note: M750 typical baudrate might be 1000000 or 115200. 
        # Previous scripts used 1000000. Let's try 1000000.
        robot = MyArmMControl(port, 1000000)
    except Exception as e:
        print(f"Connection Failed: {e}")
        return

    # Joint Selection
    while True:
        try:
            jid = input("Enter Joint ID to Control (1-6): ").strip()
            joint_id = int(jid)
            if 1 <= joint_id <= 6:
                break
            print("Invalid ID. 1-6.")
        except ValueError:
            print("Invalid Input.")

    # GUI Launch
    root = tk.Tk()
    app = SingleJointController(root, robot, joint_id)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
