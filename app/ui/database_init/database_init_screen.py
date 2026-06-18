"""
Database Initialization UI Screen
Provides a visual interface for initializing and checking database setup
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Color scheme
BG = "#0f172a"
CARD = "#1e293b"
TXT = "#f1f5f9"
MUT = "#94a3b8"
BDR = "#334155"
PUR = "#667eea"
GRN = "#22c55e"
ORG = "#f59e0b"
RED = "#ef4444"
BLU = "#3b82f6"


class DatabaseInitScreen(tk.Frame):
    """Screen for database initialization and verification"""

    def __init__(self, parent, db_instance, on_complete: Optional[Callable] = None, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.db = db_instance
        self.on_complete = on_complete
        self.is_running = False
        self._build()

    def _build(self):
        """Build the UI"""
        # Header
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=16, pady=(20, 10))

        tk.Label(
            header, text="Database Setup",
            font=("Segoe UI", 20, "bold"),
            fg=TXT, bg=BG
        ).pack(anchor="w")

        tk.Label(
            header, text="Initialize and verify database tables",
            font=("Segoe UI", 11),
            fg=MUT, bg=BG
        ).pack(anchor="w", pady=(4, 0))

        # Main content
        content = tk.Frame(self, bg=BG)
        content.pack(fill="both", expand=True, padx=16, pady=10)

        # Status frame
        status_frame = tk.Frame(content, bg=CARD, relief="solid", bd=1)
        status_frame.pack(fill="x", pady=(0, 16))

        status_header = tk.Frame(status_frame, bg=CARD)
        status_header.pack(fill="x", padx=12, pady=12)

        tk.Label(
            status_header, text="📊 Database Status",
            font=("Segoe UI", 12, "bold"),
            fg=TXT, bg=CARD
        ).pack(anchor="w")

        self.status_var = tk.StringVar(value="Ready to initialize")
        tk.Label(
            status_frame, textvariable=self.status_var,
            font=("Segoe UI", 10),
            fg=MUT, bg=CARD, wraplength=600, justify="left"
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        progress_bar = ttk.Progressbar(
            status_frame, variable=self.progress_var,
            maximum=100, mode='determinate', length=300
        )
        progress_bar.pack(fill="x", padx=12, pady=(0, 12))

        # Tables verification
        tables_frame = tk.Frame(content, bg=CARD, relief="solid", bd=1)
        tables_frame.pack(fill="both", expand=True, pady=(0, 16))

        tk.Label(
            tables_frame, text="📋 Critical Tables",
            font=("Segoe UI", 12, "bold"),
            fg=TXT, bg=CARD, padx=12, pady=(12, 8)
        ).pack(anchor="w")

        # Scrollable tables list
        list_frame = tk.Frame(tables_frame, bg=CARD)
        list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.tables_text = tk.Text(
            list_frame, height=8, width=60,
            bg="#0f172a", fg=TXT, font=("Courier", 9),
            yscrollcommand=scrollbar.set, relief="solid", bd=1
        )
        self.tables_text.pack(fill="both", expand=True)
        scrollbar.config(command=self.tables_text.yview)
        self.tables_text.config(state="disabled")

        # Critical tables to check
        self.critical_tables = [
            "core_invoicemaster",
            "core_salesmaster",
            "contra_entry",
            "challan1"
        ]

        # Buttons
        btn_frame = tk.Frame(content, bg=BG)
        btn_frame.pack(fill="x")

        self.init_btn = tk.Button(
            btn_frame, text="🔧 Initialize Database",
            font=("Segoe UI", 10, "bold"),
            bg=PUR, fg="white", relief="flat", bd=0,
            padx=16, pady=10, cursor="hand2",
            command=self.start_initialization
        )
        self.init_btn.pack(side="left", padx=(0, 8))

        self.verify_btn = tk.Button(
            btn_frame, text="✓ Verify Tables",
            font=("Segoe UI", 10),
            bg=GRN, fg="white", relief="flat", bd=0,
            padx=16, pady=10, cursor="hand2",
            command=self.verify_tables
        )
        self.verify_btn.pack(side="left")

        # Initial verification
        self.verify_tables()

    def update_status(self, message: str, progress: Optional[float] = None):
        """Update status message and progress"""
        self.status_var.set(message)
        if progress is not None:
            self.progress_var.set(progress)
        self.update()

    def add_table_info(self, table: str, exists: bool, status: str = ""):
        """Add table status to the list"""
        self.tables_text.config(state="normal")
        icon = "✓" if exists else "✗"
        color_tag = "success" if exists else "error"
        self.tables_text.tag_config("success", foreground=GRN)
        self.tables_text.tag_config("error", foreground=RED)
        self.tables_text.insert("end", f"{icon} {table:<30}", color_tag)
        if status:
            self.tables_text.insert("end", f" ({status})", "info")
        self.tables_text.insert("end", "\n")
        self.tables_text.config(state="disabled")
        self.tables_text.see("end")
        self.update()

    def verify_tables(self):
        """Verify if critical tables exist"""
        self.tables_text.config(state="normal")
        self.tables_text.delete("1.0", "end")
        self.tables_text.config(state="disabled")

        self.update_status("Checking database tables...", 0)
        threading.Thread(target=self._verify_tables_worker, daemon=True).start()

    def _verify_tables_worker(self):
        """Worker thread for table verification"""
        try:
            all_exist = True
            for i, table in enumerate(self.critical_tables):
                try:
                    exists = self.db.table_exists(table)
                    self.add_table_info(table, exists)
                    if not exists:
                        all_exist = False
                except Exception as e:
                    logger.error(f"Error checking table {table}: {e}")
                    self.add_table_info(table, False, f"Error: {str(e)[:30]}")
                    all_exist = False

                progress = ((i + 1) / len(self.critical_tables)) * 50
                self.update_status(f"Checking table {i + 1}/{len(self.critical_tables)}", progress)

            if all_exist:
                self.update_status("✓ All critical tables exist!", 100)
            else:
                self.update_status("✗ Some tables are missing. Click 'Initialize Database' to create them.", 50)

        except Exception as e:
            logger.error(f"Verification error: {e}")
            self.update_status(f"✗ Error during verification: {str(e)[:60]}", 0)

    def start_initialization(self):
        """Start database initialization"""
        if self.is_running:
            messagebox.showwarning("Info", "Initialization is already running")
            return

        if messagebox.askyesno(
            "Confirm",
            "This will create/update database tables.\nContinue?"
        ):
            self.is_running = True
            self.init_btn.config(state="disabled")
            self.verify_btn.config(state="disabled")
            threading.Thread(target=self._initialize_worker, daemon=True).start()

    def _initialize_worker(self):
        """Worker thread for database initialization"""
        try:
            self.tables_text.config(state="normal")
            self.tables_text.delete("1.0", "end")
            self.tables_text.config(state="disabled")

            self.update_status("Reading SQL setup script...", 5)

            # Load SQL script
            sql_file = Path(__file__).parent.parent.parent / "setup_database.sql"
            if not sql_file.exists():
                self.update_status(f"✗ SQL script not found: {sql_file}", 0)
                return

            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Parse and execute statements
            statements = [
                s.strip() for s in sql_content.split(';')
                if s.strip() and not s.strip().startswith('--')
            ]

            self.update_status(f"Executing {len(statements)} SQL statements...", 10)

            success_count = 0
            for i, statement in enumerate(statements):
                try:
                    lines = [
                        l for l in statement.split('\n')
                        if l.strip() and not l.strip().startswith('--')
                    ]
                    if not lines:
                        continue

                    statement_clean = '\n'.join(lines)
                    self.db.execute(statement_clean)
                    success_count += 1

                    # Log success
                    if 'CREATE TABLE' in statement_clean.upper():
                        table_name = self._extract_table_name(statement_clean)
                        self.add_table_info(table_name, True)
                    elif 'INSERT' in statement_clean.upper():
                        self.add_table_info("Data inserted", True)
                    elif 'ALTER' in statement_clean.upper():
                        self.add_table_info("Table altered", True)

                    progress = 10 + ((i + 1) / len(statements)) * 80
                    self.update_status(
                        f"Executing statement {i + 1}/{len(statements)}",
                        progress
                    )

                except Exception as e:
                    logger.warning(f"Statement {i + 1} error: {e}")
                    self.add_table_info(f"Statement {i + 1}", False, str(e)[:30])

            self.update_status(f"Execution complete. Verifying tables...", 90)

            # Verify tables after initialization
            all_exist = True
            for table in self.critical_tables:
                try:
                    exists = self.db.table_exists(table)
                    if not exists:
                        all_exist = False
                except:
                    all_exist = False

            if all_exist:
                self.update_status("✓ Database initialization successful!", 100)
                messagebox.showinfo(
                    "Success",
                    f"Database initialized successfully!\n\n"
                    f"Executed {success_count} statements.\n"
                    f"All critical tables are now ready."
                )
                if self.on_complete:
                    self.on_complete()
            else:
                self.update_status("⚠ Some tables may not have been created.", 90)
                messagebox.showwarning(
                    "Partial Success",
                    "Database initialization completed,\nbut some tables may be missing."
                )

        except Exception as e:
            logger.error(f"Initialization error: {e}")
            self.update_status(f"✗ Error: {str(e)[:60]}", 0)
            messagebox.showerror("Error", f"Initialization failed:\n{str(e)[:200]}")

        finally:
            self.is_running = False
            self.init_btn.config(state="normal")
            self.verify_btn.config(state="normal")

    @staticmethod
    def _extract_table_name(statement: str) -> str:
        """Extract table name from CREATE TABLE statement"""
        try:
            parts = statement.upper().split()
            if 'CREATE' in parts and 'TABLE' in parts:
                idx = parts.index('TABLE')
                if idx + 1 < len(parts):
                    table = parts[idx + 1]
                    if 'NOT' in parts[idx + 1:idx + 3]:
                        table = parts[idx + 3]
                    return table.replace('`', '')
        except:
            pass
        return 'Unknown'
