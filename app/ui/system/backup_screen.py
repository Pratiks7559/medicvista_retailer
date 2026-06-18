import os
import tkinter as tk
from tkinter import ttk, messagebox
from ...styles import COLORS, FONT
from ...backup_utils import create_database_backup

BG   = "#0f172a"
CARD = "#1e293b"
TXT  = "#f1f5f9"
MUT  = "#94a3b8"
BDR  = "#334155"
PUR  = "#667eea"
GRN  = "#22c55e"
RED  = "#ef4444"
BLU  = "#3b82f6"


class BackupScreen(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.app = app_instance
        self._build()

    def _build(self):
        # ── Title ────────────────────────────────────────────────────────
        tr = tk.Frame(self, bg=BG)
        tr.pack(fill="x", pady=(0, 14))
        tk.Label(tr, text="⚙  System Tools", font=("Segoe UI", 18, "bold"),
                 fg=TXT, bg=BG).pack(side="left")
        tk.Label(tr, text="Database Backup & Logs", font=("Segoe UI", 10),
                 fg=MUT, bg=BG).pack(side="left", padx=(10, 0), pady=(6, 0))

        # ── Control Panel Card ──────────────────────────────────────────
        ctrl_card = tk.Frame(self, bg=CARD, relief="flat", highlightthickness=1, highlightbackground=BDR)
        ctrl_card.pack(fill="x", pady=(0, 14))
        
        # Left accent bar
        tk.Frame(ctrl_card, bg=PUR, width=4).pack(side="left", fill="y")
        
        body = tk.Frame(ctrl_card, bg=CARD, padx=20, pady=16)
        body.pack(fill="both", expand=True)
        
        tk.Label(body, text="Database Backup Control Panel", font=("Segoe UI", 12, "bold"),
                 fg=TXT, bg=CARD).pack(anchor="w", pady=(0, 6))
        tk.Label(body, text="Create a physical SQL backup of your entire pharmacy ERP database. Backups are stored in the local 'backups' folder and registered in the database backup log table.",
                 font=("Segoe UI", 9), fg=MUT, bg=CARD, wraplength=700, justify="left").pack(anchor="w", pady=(0, 14))
        
        btn_bar = tk.Frame(body, bg=CARD)
        btn_bar.pack(fill="x")
        
        # Create Backup Button
        self.btn_backup = tk.Button(
            btn_bar, text="🚀  Create Database Backup Now", font=("Segoe UI", 10, "bold"),
            bg=GRN, fg="white", bd=0, relief="flat", padx=16, pady=8, cursor="hand2",
            activebackground="#16a34a", activeforeground="white",
            command=self._trigger_backup
        )
        self.btn_backup.pack(side="left", padx=(0, 10))
        self.btn_backup.bind("<Enter>", lambda e: self.btn_backup.config(bg="#16a34a"))
        self.btn_backup.bind("<Leave>", lambda e: self.btn_backup.config(bg=GRN))
        
        # Open Folder Button
        self.btn_folder = tk.Button(
            btn_bar, text="📂  Open Backups Folder", font=("Segoe UI", 10),
            bg=BLU, fg="white", bd=0, relief="flat", padx=14, pady=8, cursor="hand2",
            activebackground="#2563eb", activeforeground="white",
            command=self._open_backups_folder
        )
        self.btn_folder.pack(side="left", padx=10)
        self.btn_folder.bind("<Enter>", lambda e: self.btn_folder.config(bg="#2563eb"))
        self.btn_folder.bind("<Leave>", lambda e: self.btn_folder.config(bg=BLU))

        # Refresh Logs Button
        self.btn_refresh = tk.Button(
            btn_bar, text="↻  Refresh Logs", font=("Segoe UI", 10),
            bg=CARD, fg=TXT, bd=1, relief="solid", highlightthickness=0, highlightbackground=BDR,
            padx=14, pady=7, cursor="hand2",
            activebackground=BDR, activeforeground=TXT,
            command=self.on_show
        )
        self.btn_refresh.pack(side="right")
        self.btn_refresh.bind("<Enter>", lambda e: self.btn_refresh.config(bg=BDR))
        self.btn_refresh.bind("<Leave>", lambda e: self.btn_refresh.config(bg=CARD))

        # ── Logs List Card ──────────────────────────────────────────────
        logs_hdr = tk.Frame(self, bg=BG)
        logs_hdr.pack(fill="x", pady=(0, 6))
        tk.Label(logs_hdr, text="Backup History Log", font=("Segoe UI", 13, "bold"),
                 fg=TXT, bg=BG).pack(side="left")
        
        # Treeview Frame
        frm = tk.Frame(self, bg=BG)
        frm.pack(fill="both", expand=True)
        
        cols = ("#", "Date & Time", "Backup Filename", "File Size", "Backup Path", "Status")
        widths = (50, 160, 220, 100, 320, 100)
        
        vsb = ttk.Scrollbar(frm, orient="vertical")
        hsb = ttk.Scrollbar(frm, orient="horizontal")
        
        self.tree = ttk.Treeview(
            frm, columns=cols, show="headings",
            yscrollcommand=vsb.set, xscrollcommand=hsb.set, selectmode="browse"
        )
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="w" if col in ("Backup Filename", "Backup Path") else "center")
            
        self.tree.tag_configure("Success", background="#052e16", foreground="#4ade80")
        self.tree.tag_configure("Failed",  background="#450a0a", foreground="#f87171")
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frm.grid_rowconfigure(0, weight=1)
        frm.grid_columnconfigure(0, weight=1)

    def on_show(self):
        """Fetch and render backup logs."""
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            rows = self.app.db.fetch_backups()
            for idx, r in enumerate(rows, 1):
                status = r.get("status", "Success")
                tag = "Success" if status.lower() == "success" else "Failed"
                self.tree.insert("", "end", values=(
                    idx,
                    str(r.get("backup_date", "")),
                    r.get("backup_filename", ""),
                    r.get("file_size", "0 KB"),
                    r.get("backup_path", ""),
                    status
                ), tags=(tag,))
        except Exception as e:
            print(f"Error loading backups logs: {e}")

    def _trigger_backup(self):
        """Trigger database backup process."""
        self.btn_backup.config(state="disabled", text="⏳  Backing up database...")
        self.update_idletasks()
        
        def done():
            self.btn_backup.config(state="normal", text="🚀  Create Database Backup Now")
            self.on_show()
            
        create_database_backup(self.app, self, on_complete=done)

    def _open_backups_folder(self):
        """Open the backups directory in OS file explorer."""
        backup_dir = os.path.abspath("backups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        try:
            os.startfile(backup_dir)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}", parent=self)
