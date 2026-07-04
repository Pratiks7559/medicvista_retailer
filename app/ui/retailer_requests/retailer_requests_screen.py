"""
retailer_requests_screen.py
----------------------------
Retailer Requests screen — integrated with wholesaler sync.

Sync architecture:
  - RetailerSyncRunner runs in a daemon thread (started in application.py)
  - on_sync_complete callback fires via root.after(0, ...) on MAIN thread
  - All UI updates happen here on main thread — no direct widget access from thread
  - Status updates to wholesaler run in short-lived daemon threads
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging

from ...styles import COLORS

logger = logging.getLogger("retailer_sync")

# ── Colour palette ────────────────────────────────────────────────────────────
_BG       = COLORS["bg_light"]
_CARD     = "#ffffff"
_DARK     = "#1e293b"
_DARKER   = "#0f172a"
_BDR      = "#e2e8f0"
_MUTED    = "#64748b"
_TXT      = "#1e293b"

_CLR_CONN    = "#16a34a"   # green  — connected
_CLR_DISC    = "#dc2626"   # red    — disconnected
_CLR_CHECK   = "#d97706"   # amber  — checking

_STATUS_BG = {
    "Pending":    "#fef9c3",
    "Processing": "#dbeafe",
    "Processed":  "#dcfce7",
    "Failed":     "#fee2e2",
}
_STATUS_FG = {
    "Pending":    "#92400e",
    "Processing": "#1e40af",
    "Processed":  "#166534",
    "Failed":     "#991b1b",
}

def _btn(parent, text, bg, fg="#ffffff", cmd=None, padx=12, pady=5):
    b = tk.Button(parent, text=text, bg=bg, fg=fg,
                  font=("Segoe UI", 9, "bold"),
                  bd=0, relief="flat", padx=padx, pady=pady,
                  cursor="hand2", activebackground=bg,
                  activeforeground=fg, command=cmd)
    return b


class RetailerRequestsScreen(tk.Frame):
    """
    Existing Retailer Requests screen — now with full wholesaler sync integration.

    Wiring (done in __init__):
      1. Reads sync runner from app.sync_bridge (set in application.py)
      2. Sets runner.on_sync_complete = self._on_sync_result
      3. Starts runner thread if not already running
    """

    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=_BG, **kwargs)
        self.app = app_instance

        # Sync runner reference — may be None if wholesaler config missing
        self._runner  = None
        self._thread  = None

        self._build()
        self._init_sync()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        # ── Top header bar ────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=_DARK, padx=16, pady=12)
        hdr.pack(fill="x")

        tk.Label(hdr, text="Retailer Requests",
                 font=("Segoe UI", 15, "bold"),
                 fg="#f1f5f9", bg=_DARK).pack(side="left")

        # Sync Now button
        self._btn_sync = _btn(hdr, "  Sync Now", "#3b82f6",
                               cmd=self._on_sync_now, padx=14)
        self._btn_sync.pack(side="right", padx=(6, 0))

        # ── Status bar ────────────────────────────────────────────────────
        sb = tk.Frame(self, bg="#f1f5f9", padx=14, pady=8)
        sb.pack(fill="x")
        tk.Frame(self, bg=_BDR, height=1).pack(fill="x")

        # Connection dot + text
        self._dot = tk.Label(sb, text="●", font=("Segoe UI", 12),
                             fg=_CLR_CHECK, bg="#f1f5f9")
        self._dot.pack(side="left")

        self._lbl_conn = tk.Label(sb, text="Checking...",
                                  font=("Segoe UI", 9), fg=_MUTED, bg="#f1f5f9")
        self._lbl_conn.pack(side="left", padx=(4, 20))

        self._lbl_sync = tk.Label(sb, text="Last sync: never",
                                  font=("Segoe UI", 8), fg=_MUTED, bg="#f1f5f9")
        self._lbl_sync.pack(side="left")

        # Notification label — hidden until new requests arrive
        self._lbl_notify = tk.Label(sb, text="",
                                    font=("Segoe UI", 9, "bold"),
                                    fg="#166534", bg="#dcfce7",
                                    padx=10, pady=2)
        # Not packed yet — shown dynamically

        self._lbl_server = tk.Label(sb, text="Server: --",
                                    font=("Segoe UI", 8), fg="#94a3b8", bg="#f1f5f9")
        self._lbl_server.pack(side="right")

        # ── Action buttons row ────────────────────────────────────────────
        bar = tk.Frame(self, bg=_CARD, padx=14, pady=8)
        bar.pack(fill="x")
        tk.Frame(self, bg=_BDR, height=1).pack(fill="x")

        tk.Label(bar, text="Selected request:",
                 font=("Segoe UI", 9), fg=_MUTED, bg=_CARD).pack(side="left")

        self._btn_processing = _btn(bar, "  Mark Processing",
                                     "#1e40af", "#dbeafe",
                                     cmd=lambda: self._on_mark_status("PROCESSING"))
        self._btn_processing.pack(side="left", padx=(10, 4))

        self._btn_completed = _btn(bar, "  Mark Completed",
                                    "#166534", "#dcfce7",
                                    cmd=lambda: self._on_mark_status("COMPLETED"))
        self._btn_completed.pack(side="left", padx=(0, 4))

        self._btn_failed = _btn(bar, "  Mark Failed",
                                 "#991b1b", "#fee2e2",
                                 cmd=lambda: self._on_mark_status("FAILED"))
        self._btn_failed.pack(side="left", padx=(0, 4))

        self._btn_generate = _btn(bar, "  Generate Report",
                                   "#7c3aed",
                                   cmd=self._generate_report)
        self._btn_generate.pack(side="left", padx=(0, 4))

        # Status label (spinner text)
        self._status_var = tk.StringVar(value="")
        tk.Label(bar, textvariable=self._status_var,
                 font=("Segoe UI", 9), fg=_MUTED, bg=_CARD).pack(side="left", padx=8)

        # ── Treeview table ────────────────────────────────────────────────
        cols = ("#", "Req ID", "Type", "From", "To",
                "Status", "Created At", "Processed At", "Remarks")
        ws   = (35, 70, 100, 95, 95, 105, 145, 145, 200)

        tbl = tk.Frame(self, bg=_BG)
        tbl.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(tbl, orient="vertical")
        hsb = ttk.Scrollbar(tbl, orient="horizontal")

        self.tree = ttk.Treeview(tbl, columns=cols, show="headings",
                                  yscrollcommand=vsb.set,
                                  xscrollcommand=hsb.set,
                                  selectmode="browse")
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        for col, w in zip(cols, ws):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w,
                             anchor="w" if col in ("Type", "Remarks") else "center",
                             minwidth=30)

        for status, bg in _STATUS_BG.items():
            self.tree.tag_configure(status,
                                    background=bg,
                                    foreground=_STATUS_FG.get(status, _TXT))

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tbl.grid_rowconfigure(0, weight=1)
        tbl.grid_columnconfigure(0, weight=1)

    # ── Sync initialisation ───────────────────────────────────────────────────

    def _init_sync(self):
        # Option 1 — runner already created by application.py via SyncBridge
        bridge = getattr(self.app, "sync_bridge", None)
        if bridge and hasattr(bridge, "_runner") and bridge._runner:
            self._runner = bridge._runner
            # Set _tk_root so _fire_callback uses root.after() correctly
            self._runner._tk_root = self._find_root()
            # Add THIS screen as an additional sync listener
            # without removing application.py's existing _on_wholesaler_sync
            _existing = self._runner.on_sync_complete
            def _combined(result, _existing=_existing):
                if _existing:
                    try:
                        _existing(result)
                    except Exception:
                        pass
                try:
                    if self.winfo_exists():
                        self._on_sync_result(result)
                except Exception:
                    pass
            self._runner.on_sync_complete = _combined
            self._lbl_server.config(
                text=f"Server: {self._runner.config.get('server_url', '--')}  "
                     f"[{self._runner.config.get('server_mode', 'LOCAL')}]"
            )
            logger.info("RetailerRequestsScreen: wired to existing SyncBridge runner.")
            # Trigger immediate first sync so screen shows status right away
            self.after(500, lambda: self._runner.force_wake())
            return

        # Option 2 — bootstrap runner ourselves from config file
        import json, os, sys
        cfg_paths = [
            os.path.join(os.path.dirname(__file__),
                         "..", "..", "..", "retailer_sync",
                         "retailer_sync_config.json"),
            os.path.join(os.path.dirname(__file__),
                         "..", "..", "retailer_sync_config.json"),
        ]
        cfg_file = next((p for p in cfg_paths if os.path.exists(p)), None)
        if cfg_file:
            try:
                sync_dir = os.path.dirname(os.path.abspath(cfg_file))
                if sync_dir not in sys.path:
                    sys.path.insert(0, sync_dir)

                with open(cfg_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                config = {k: v for k, v in raw.items()
                          if not k.startswith("_comment")}

                # Always override api_key/retailer_id from _RETAILER_MAP
                # so config file placeholders never reach the server
                _rmap = getattr(self.app.__class__, '_RETAILER_MAP', {})
                _rid  = getattr(getattr(self.app, 'config_data', None), 'retailer_id', 0)
                if _rid and _rid in _rmap:
                    _, _api_key, _code = _rmap[_rid]
                    config['api_key']       = _api_key
                    config['retailer_id']   = _rid
                    config['retailer_code'] = _code

                # Abort if still placeholder
                if not config.get('api_key') or config['api_key'] == 'WILL_BE_SET_ON_LOGIN':
                    raise ValueError("api_key not set — login first")

                from retailer_sync_runner import RetailerSyncRunner
                self._runner = RetailerSyncRunner(
                    config=config,
                    on_sync_complete=self._on_sync_result,
                )
                # Set _tk_root for safe root.after() delivery
                self._runner._tk_root = self._find_root()
                self._thread = threading.Thread(
                    target=self._runner.run_forever,
                    name="RetailerSyncThread",
                    daemon=True,
                )
                self._thread.start()
                self._lbl_server.config(
                    text=f"Server: {config.get('server_url', '--')}  "
                         f"[{config.get('server_mode', 'LOCAL')}]"
                )
                logger.info("RetailerRequestsScreen: bootstrapped own sync runner.")
                self._find_root().protocol("WM_DELETE_WINDOW", self._on_app_close)
            except Exception as e:
                logger.warning("Could not start sync runner: %s", e)
                self._set_disconnected(f"Sync unavailable: {e}")
        else:
            self._set_disconnected("No wholesaler config found")

    def _find_root(self):
        w = self
        while w.master:
            w = w.master
        return w

    # ── on_show — called every time screen becomes visible ────────────────────

    def on_show(self):
        """Reload table from MySQL retailer_request table."""
        self._reload_table()

    # ── Table reload ──────────────────────────────────────────────────────────

    def _reload_table(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        try:
            rows = self.app.db.fetch_requests()
            for idx, r in enumerate(rows, 1):
                status = r.get("status", "Pending")
                tag = status if status in _STATUS_BG else "Pending"
                self.tree.insert("", "end", tags=(tag,), values=(
                    idx,
                    r.get("reference_id") or r.get("id", ""),
                    r.get("request_type", ""),
                    r.get("from_date", "") or "",
                    r.get("to_date", "") or "",
                    status,
                    str(r.get("created_at", "")) or "",
                    str(r.get("processed_at", "")) or "",
                    r.get("remarks", "") or "",
                ))
        except Exception as e:
            logger.error("RetailerRequestsScreen._reload_table: %s", e)

    # ── Sync result callback — ALWAYS called on main thread via after(0,...) ──

    def _on_sync_result(self, result: dict):
        """
        Called by RetailerSyncRunner after every sync cycle.
        The runner uses root.after(0, callback) so this is safe to update UI.
        """
        # Guard: widget may have been destroyed after logout
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        connected      = result.get("connected", False)
        last_sync      = result.get("last_sync_time")
        error          = result.get("error")
        new_requests   = result.get("new_requests", [])

        # Update connection indicator
        if connected:
            self._dot.config(fg=_CLR_CONN)
            self._lbl_conn.config(text="Connected")
        else:
            self._dot.config(fg=_CLR_DISC)
            self._lbl_conn.config(text="Disconnected")

        # Last sync time
        self._lbl_sync.config(
            text=f"Last sync: {last_sync}" if last_sync else "Last sync: never"
        )

        # Show [NEW] notification if new requests arrived
        if new_requests:
            count = len(new_requests)
            self._show_notification(f"[NEW] {count} new request(s) from wholesaler!")

        # Reload table from MySQL (works even when disconnected)
        self._reload_table()

        # Also push to app status bar if available
        if hasattr(self.app, "_conn_var"):
            if new_requests:
                self.app._conn_var.set(
                    f"[NEW] {len(new_requests)} request(s) from wholesaler"
                )
                self.after(5000, lambda: self.app._conn_var.set(
                    "[OK] Connection: OK" if connected else "[X] Disconnected"
                ))
            elif connected:
                self.app._conn_var.set("[OK] Connection: OK")
            else:
                msg = error[:60] if error else "failed"
                self.app._conn_var.set(f"[X] {msg}")

    def _show_notification(self, text: str):
        """Show green notification banner, auto-clear after 5 seconds."""
        self._lbl_notify.config(text=text)
        self._lbl_notify.pack(side="left", padx=(16, 0))
        self.after(5000, self._clear_notification)

    def _clear_notification(self):
        self._lbl_notify.config(text="")
        self._lbl_notify.pack_forget()

    def _set_disconnected(self, msg: str = "Disconnected"):
        self._dot.config(fg=_CLR_DISC)
        self._lbl_conn.config(text=msg[:60])

    # ── Button handlers ───────────────────────────────────────────────────────

    def _on_sync_now(self):
        """Force an immediate sync cycle — wakes the background thread."""
        if self._runner:
            self._btn_sync.config(state="disabled", text="Syncing...")
            self._dot.config(fg=_CLR_CHECK)
            self._lbl_conn.config(text="Syncing...")
            self._runner.force_wake()
            # Restore button after 3s regardless of result
            self.after(3000, lambda: self._btn_sync.config(
                state="normal", text="  Sync Now"
            ))
        else:
            # Fallback: use the app-level sync_service
            try:
                svc = getattr(self.app, "sync_service", None)
                if svc:
                    svc.sync_now()
            except Exception:
                pass
            self._reload_table()

    def _get_selected(self):
        """Return (iid, values_tuple) of selected row, or (None, None)."""
        sel = self.tree.focus()
        if not sel:
            return None, None
        return sel, self.tree.item(sel, "values")

    def _on_mark_status(self, new_status: str):
        """Mark selected request with new_status — sends to wholesaler in thread."""
        iid, vals = self._get_selected()
        if not vals:
            messagebox.showinfo("Select", "Select a request row first.", parent=self)
            return

        # Column layout: (#, Req ID=reference_id, Type, From, To, Status, ...)
        reference_id   = vals[1]   # column 1 = reference_id (wholesaler request_id)
        current_status = vals[5]   # column 5 = Status

        # Get the MySQL row id for local DB update
        mysql_id = None
        try:
            rows = self.app.db.query(
                "SELECT id FROM retailer_request WHERE reference_id=%s AND retailer_id=%s LIMIT 1",
                (reference_id, self.app.config_data.retailer_id)
            )
            if rows:
                mysql_id = rows[0]["id"]
        except Exception:
            pass

        ok = messagebox.askyesno(
            "Confirm",
            f"Request ID: {reference_id}\n"
            f"Current: {current_status}  ->  New: {new_status}\n\n"
            f"Confirm?",
            parent=self
        )
        if not ok:
            return

        self._push_status_threaded(
            int(reference_id) if reference_id else 0,
            mysql_id, new_status, iid, vals
        )

    def _push_status_threaded(self, reference_id, mysql_id,
                               new_status, iid, vals):
        """
        Send status update to wholesaler server in a daemon thread.
        Update MySQL and UI optimistically on main thread immediately.
        """
        # 1. Optimistic local update in MySQL right now
        try:
            self.app.db.update_request_status_by_reference(
                reference_id, new_status, self.app.config_data.retailer_id
            )
        except Exception as e:
            logger.warning("Local status update failed: %s", e)

        # 2. Optimistic UI update immediately
        _status_map = {
            "PENDING": "Pending", "PROCESSING": "Processing",
            "COMPLETED": "Processed", "FAILED": "Failed",
        }
        display_status = _status_map.get(new_status.upper(), new_status)
        new_vals = list(vals)
        new_vals[5] = display_status
        tag = display_status if display_status in _STATUS_BG else "Pending"
        try:
            self.tree.item(iid, values=new_vals, tags=(tag,))
        except Exception:
            pass

        # 3. Push to wholesaler server in background thread
        def _send():
            if self._runner:
                try:
                    self._runner.push_status_update(reference_id, new_status)
                except Exception as e:
                    logger.error("push_status_update failed: %s", e)

        threading.Thread(target=_send, daemon=True,
                         name="StatusPushThread").start()

    def _generate_report(self):
        """Fetch report data from wholesaler and generate PDF + Excel."""
        iid, vals = self._get_selected()
        if not vals:
            messagebox.showinfo("Select", "Select a Pending request first.",
                                parent=self)
            return

        mysql_id     = vals[1]
        current_status = vals[5]

        if current_status.lower() not in ("pending", "failed"):
            messagebox.showinfo("Info",
                                f"Request is already '{current_status}'.\n"
                                "Only Pending or Failed requests can be generated.",
                                parent=self)
            return

        # Get reference_id (wholesaler request_id)
        reference_id = None
        try:
            rows = self.app.db.query(
                "SELECT reference_id FROM retailer_request WHERE id=%s LIMIT 1",
                (mysql_id,)
            )
            if rows:
                reference_id = rows[0].get("reference_id")
        except Exception:
            pass

        if not reference_id:
            messagebox.showerror("Error",
                                 "No wholesaler Reference ID on this request.\n"
                                 "Cannot generate report.", parent=self)
            return

        if not self._runner:
            messagebox.showerror("Unavailable",
                                 "Wholesaler sync is not configured.", parent=self)
            return

        self._status_var.set(f"Generating report for #{reference_id}...")
        self._btn_generate.config(state="disabled")

        def _run():
            result = self._runner.fetch_and_generate(int(reference_id))
            # Schedule UI update back on main thread
            self.after(0, lambda: self._on_generate_done(reference_id, result))

        threading.Thread(target=_run, daemon=True,
                         name="GenerateReportThread").start()

    def _on_generate_done(self, reference_id: int, result: dict):
        """Called on main thread after generate completes."""
        self._status_var.set("")
        self._btn_generate.config(state="normal")

        if result.get("ok"):
            msg = (
                f"Report generated successfully!\n\n"
                f"PDF:   {result.get('pdf_path', 'N/A')}\n"
                f"Excel: {result.get('excel_path', 'N/A')}"
            )
            messagebox.showinfo("Done", msg, parent=self)
        else:
            messagebox.showerror(
                "Failed",
                f"Report generation failed:\n{result.get('error', 'Unknown error')}",
                parent=self
            )
        self._reload_table()

    # ── App close handler ─────────────────────────────────────────────────────

    def _on_app_close(self):
        """Stop runner cleanly before destroying root window."""
        if self._runner:
            try:
                self._runner.stop()
            except Exception:
                pass
        self._find_root().destroy()

    # ── Keyboard shortcut hooks ───────────────────────────────────────────────

    def kb_refresh(self):
        self._reload_table()

    def kb_search(self):
        pass

    def kb_new(self):
        self._on_sync_now()
