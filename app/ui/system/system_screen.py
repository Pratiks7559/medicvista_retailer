import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *

class SystemScreen(tb.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app_instance

        tb.Label(self, text="Settings", font=("Inter", 18, "bold")).pack(pady=20, anchor=W)

        info_frame = tb.Frame(self, padding=20, bootstyle="light")
        info_frame.pack(fill=X)

        tb.Label(info_frame, text=f"Retailer ID: {self.app.config.retailer_id}", bootstyle="light").pack(anchor=W)
        tb.Label(info_frame, text=f"Store Name: {self.app.config.store_name}", bootstyle="light").pack(anchor=W)
        tb.Label(info_frame, text=f"DB Host: {self.app.config.db_host}", bootstyle="light").pack(anchor=W)
        tb.Label(info_frame, text=f"Sync Interval: {self.app.config.poll_seconds}s", bootstyle="light").pack(anchor=W)

    def on_show(self):
        pass
