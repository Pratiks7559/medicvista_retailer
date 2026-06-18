from __future__ import annotations
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb

from .styles import COLORS, apply_style
from .db import Database
from .config import load_config
from .sync import SyncService
from .ui.components.sidebar import AccordionSidebar
from .ui.dashboard_screen import DashboardScreen
from .ui.inventory.inventory_screen import InventoryScreen
from .ui.inventory.batch_wise_screen import BatchWiseScreen
from .ui.inventory.date_wise_screen import DateWiseScreen
from .ui.inventory.stock_statement_screen import StockStatementScreen
from .ui.inventory.transaction_history_screen import TransactionHistoryScreen
from .ui.product.product_screen import ProductScreen
from .ui.purchase.purchase_screen import PurchaseScreen
from .ui.purchase.reorder_level_screen import ReorderLevelScreen
from .ui.purchase.reorder_level_screen import ReorderLevelScreen
from .ui.sales.sales_screen import SalesScreen
from .ui.reports.reports_screen import ReportsScreen
from .ui.reports.financial_report_screen import FinancialReportScreen
from .ui.supplier.supplier_screen import SupplierScreen
from .ui.customer.customer_screen import CustomerScreen
from .ui.retailer_requests.retailer_requests_screen import RetailerRequestsScreen
from .ui.challan.challan_screen import ChallanScreen
from .ui.returns.returns_screen import ReturnsScreen
from .ui.stock_issue.stock_issue_screen import StockIssueScreen
from .ui.receipts.receipts_screen import ReceiptsScreen
from .ui.ledger.ledger_screen import LedgerScreen
from .ui.system.backup_screen import BackupScreen

# Retailer sync bridge (wholesaler API integration)
try:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'retailer_sync'))
    from retailer_sync_bridge import SyncBridge
    from retailer_sync_runner import _load_config as _load_sync_config
    _SYNC_AVAILABLE = True
except Exception:
    _SYNC_AVAILABLE = False


class RetailerDesktopApp(tb.Window):
    def __init__(self):
        super().__init__(themename="litera")
        self.title("MedicVista Pharmacy")
        self.state("zoomed")

        self._base_config = load_config()
        apply_style(self)

        self._current_user: str = ""
        self._current_retailer_name: str = ""

        # Show login screen first
        self._login_frame = None
        self._main_built = False
        self._main_widgets: list[tk.Widget] = []
        self._show_login()

    def _show_login(self):
        from .ui.login.modern_login_screen import ModernLoginScreen
        if self._login_frame:
            try:
                self._login_frame.destroy()
            except Exception:
                pass
        self._login_frame = ModernLoginScreen(
            self, app_instance=self, on_login=self._on_login_success
        )
        self._login_frame.pack(fill="both", expand=True)

    # Retailer ID → (store_name, api_key, retailer_code) mapping
    # Must match wholesaler ERP RetailerMaster exactly
    _RETAILER_MAP = {
        1: ("BSL Pharmacy",      "RTL001_TEST_KEY", "RTL001"),
        2: ("MedPlus Retail",    "RTL002_TEST_KEY", "RTL002"),
        3: ("Apollo Pharmacy",   "RTL003_TEST_KEY", "RTL003"),
        4: ("Wellness Forever",  "RTL004_TEST_KEY", "RTL004"),
    }

    def _on_login_success(self, username: str, password: str, retailer_id: int, full_name: str):
        """Called by the login screen after successful DB authentication."""
        # Lookup correct store_name and api_key for this retailer_id
        store_name, api_key, retailer_code = self._RETAILER_MAP.get(
            retailer_id,
            (full_name or f"Store {retailer_id}", f"RTL{retailer_id:03d}_TEST_KEY", f"RTL{retailer_id:03d}")
        )
        self._current_user = store_name
        self._current_retailer_name = store_name

        # Rebuild config with the authenticated retailer_id and correct store_name
        from dataclasses import replace
        self.config_data = replace(
            self._base_config,
            retailer_id=retailer_id,
            store_name=store_name,
        )
        self.db = Database(self.config_data)

        # Remove login frame and build the main app
        if self._login_frame:
            self._login_frame.destroy()
            self._login_frame = None

        self.screens: dict[str, tk.Frame] = {}
        self._active_screen: tk.Frame | None = None
        self.last_sync_at = None
        self._conn_var = tk.StringVar(value="● Connection: checking…")
        self._sync_var = tk.StringVar(value="Last sync: never")
        self._main_widgets: list[tk.Widget] = []   # track widgets to destroy on logout
        
        # Financial Year tracking
        self.current_fy_start = None
        self.current_fy_end = None

        self._build_navbar()
        self._build_main()
        self._build_statusbar()

        self.sync_service = SyncService(self, self.db, self.config_data.poll_seconds)

        self._main_built = True

        # Wholesaler sync bridge — MUST be created BEFORE _register_screens()
        # so RetailerRequestsScreen._init_sync() can find it via app.sync_bridge
        self.sync_bridge = None
        if _SYNC_AVAILABLE:
            try:
                import os
                _cfg_path = os.path.join(
                    os.path.dirname(__file__), '..', '..', '..', 'retailer_sync',
                    'retailer_sync_config.json'
                )
                _sync_cfg = _load_sync_config(_cfg_path)
                # ✅ CRITICAL FIX: Override api_key, retailer_id, retailer_code
                # with the currently logged-in retailer's values.
                # Without this, every retailer would send RTL001's key and
                # BSL Pharmacy would always show Online in the wholesaler ERP.
                _sync_cfg = dict(_sync_cfg)
                _sync_cfg['api_key']       = api_key
                _sync_cfg['retailer_id']   = retailer_id
                _sync_cfg['retailer_code'] = retailer_code
                # Safety guard: never start sync with placeholder/neutral values
                if not api_key or api_key == 'WILL_BE_SET_ON_LOGIN' or retailer_id == 0:
                    raise ValueError(f"Invalid sync config for retailer_id={retailer_id}")
                self.sync_bridge = SyncBridge(self, _sync_cfg, mysql_db=self.db)
                self.sync_bridge.on_update = self._on_wholesaler_sync
                if hasattr(self.sync_bridge, '_runner') and self.sync_bridge._runner:
                    self.sync_bridge._runner._tk_root = self
            except Exception as _e:
                import logging
                logging.getLogger(__name__).warning("SyncBridge init failed: %s", _e)

        self._register_screens()

        # Start sync bridge immediately (before screens so _init_sync finds live runner)
        if self.sync_bridge:
            self.sync_bridge.start()

        self.show_screen("Invoices")
        self.after(500, self.sync_service.start)
        self.protocol("WM_DELETE_WINDOW", self.close_app)

        # Install global keyboard shortcuts
        from .shortcuts import install_shortcuts
        install_shortcuts(self, self)

    # ── Navbar ────────────────────────────────────────────────────────────────
    def _build_navbar(self):
        from datetime import datetime
        
        NAV_BG = "#0f172a"
        nav = tk.Frame(self, bg=NAV_BG, height=52)
        nav.pack(fill="x", side="top")
        nav.pack_propagate(False)
        self._main_widgets.append(nav)

        # Left — brand
        left = tk.Frame(nav, bg=NAV_BG)
        left.pack(side="left", padx=14)
        tk.Label(left, text="💊", font=("Segoe UI", 18), bg=NAV_BG,
                 fg="#667eea").pack(side="left")
        tk.Label(left, text=" MedicVista Pharmacy", font=("Segoe UI", 14, "bold"),
                 bg=NAV_BG, fg="#f1f5f9").pack(side="left")

        # Right — FY + user
        right = tk.Frame(nav, bg=NAV_BG)
        right.pack(side="right", padx=14)

        # Financial Year Dropdown (WORKING VERSION)
        fy_container = tk.Frame(right, bg="#1e3a5f", relief="flat")
        fy_container.pack(side="left", padx=(0, 8))
        
        tk.Label(
            fy_container,
            text="📅",
            font=("Segoe UI", 11),
            bg="#1e3a5f",
            fg="#93c5fd",
            padx=5,
            pady=4
        ).pack(side="left")
        
        # Generate FY list
        def generate_fy_list():
            current_year = datetime.now().year
            current_month = datetime.now().month
            if current_month < 4:
                end_year = current_year
            else:
                end_year = current_year + 1
            # Add 2 more future years to allow invoices dated ahead
            end_year += 2
            fy_list = []
            for year in range(2012, end_year):
                fy_list.append(f"{year}-{year+1}")
            return list(reversed(fy_list))
        
        def get_current_fy():
            now = datetime.now()
            if now.month >= 4:
                return f"{now.year}-{now.year+1}"
            else:
                return f"{now.year-1}-{now.year}"
        
        self.fy_var = tk.StringVar(value=get_current_fy())
        self.fy_combo = ttk.Combobox(
            fy_container,
            textvariable=self.fy_var,
            values=generate_fy_list(),
            state="readonly",
            width=10,
            font=("Segoe UI", 9)
        )
        self.fy_combo.pack(side="left", padx=5, pady=4)
        self.fy_combo.bind("<<ComboboxSelected>>", lambda e: self._on_fy_change())
        
        # Initialize FY dates
        self._initialize_fy_dates()
        
        # Hint label
        tk.Label(
            fy_container,
            text="Ctrl+B",
            font=("Segoe UI", 7),
            bg="#1e3a5f",
            fg="#64748b",
            padx=3
        ).pack(side="left")

        sep = tk.Frame(right, bg="#334155", width=1)
        sep.pack(side="left", fill="y", pady=8, padx=4)

        user_btn = tk.Label(right, text=f"👤 {self._current_user}",
                            font=("Segoe UI", 9, "bold"), bg="#1e293b",
                            fg="#e2e8f0", padx=10, pady=4, cursor="hand2")
        user_btn.pack(side="left", padx=4)

        logout_btn = tk.Label(right, text="⏻ Logout",
                              font=("Segoe UI", 8, "bold"), bg="#7f1d1d",
                              fg="#fca5a5", padx=8, pady=4, cursor="hand2")
        logout_btn.pack(side="left", padx=(8, 0))
        logout_btn.bind("<Button-1>", lambda e: self._do_logout())

        help_btn = tk.Label(right, text="⌨ F12=Shortcuts",
                            font=("Segoe UI", 8), bg="#1e3a5f",
                            fg="#93c5fd", padx=8, pady=4, cursor="hand2",
                            takefocus=True)
        help_btn.pack(side="left", padx=(8, 0))
        help_btn.bind("<Button-1>", lambda e: self._show_shortcuts())
        help_btn.bind("<Return>",   lambda e: self._show_shortcuts())

        # Bottom border line
        border = tk.Frame(self, bg="#334155", height=1)
        border.pack(fill="x", side="top")
        self._main_widgets.append(border)
    
    def _on_fy_change(self):
        """Handle financial year change from navbar"""
        selected_fy = self.fy_var.get()
        print(f"[NAVBAR] Financial Year changed to: {selected_fy}")
        
        # Calculate FY dates
        if '-' in selected_fy:
            start_year, end_year = selected_fy.split('-')
            self.current_fy_start = f"{start_year}-04-01"
            self.current_fy_end = f"{end_year}-03-31"
            print(f"[NAVBAR] FY Range: {self.current_fy_start} to {self.current_fy_end}")
        
        # Refresh active screen if it has refresh_data or on_show method
        if self._active_screen:
            # Update Dashboard screen FY if it's active
            if hasattr(self._active_screen, 'fy_var') and hasattr(self._active_screen, 'refresh_data'):
                # Sync dashboard's FY with navbar FY
                self._active_screen.fy_var.set(selected_fy)
                self._active_screen._set_current_fy_dates()
                self._active_screen.refresh_data()
                print(f"[NAVBAR] Dashboard refreshed with FY: {selected_fy}")
            elif hasattr(self._active_screen, 'on_show'):
                # For other screens, just call on_show
                try:
                    self._active_screen.on_show()
                    print(f"[NAVBAR] Screen refreshed: {type(self._active_screen).__name__}")
                except Exception as e:
                    print(f"[NAVBAR] Error refreshing screen: {e}")
    
    def _initialize_fy_dates(self):
        """Initialize financial year dates on startup"""
        selected_fy = self.fy_var.get()
        if '-' in selected_fy:
            start_year, end_year = selected_fy.split('-')
            self.current_fy_start = f"{start_year}-04-01"
            self.current_fy_end = f"{end_year}-03-31"
            print(f"[NAVBAR] Initial FY: {selected_fy} ({self.current_fy_start} to {self.current_fy_end})")

    # ── Main body (sidebar LEFT + content RIGHT) ──────────────────────────────
    def _build_main(self):
        self.main_frame = tk.Frame(self, bg=COLORS["bg_light"])
        self.main_frame.pack(fill="both", expand=True)
        self._main_widgets.append(self.main_frame)

        self.sidebar = AccordionSidebar(self.main_frame, self)
        self.sidebar.pack(side="left", fill="y")

        # Vertical separator
        tk.Frame(self.main_frame, bg="#334155", width=1).pack(side="left", fill="y")

        self.content_area = tk.Frame(self.main_frame, bg=COLORS["bg_light"])
        self.content_area.pack(side="left", fill="both", expand=True)

    # ── Status bar ─────────────────────────────────────────────────────────────
    def _build_statusbar(self):
        sep = tk.Frame(self, bg="#334155", height=1)
        sep.pack(fill="x", side="bottom")
        self._main_widgets.append(sep)
        bar = tk.Frame(self, bg="#0f172a", height=26)
        bar.pack(fill="x", side="bottom")
        self._main_widgets.append(bar)
        bar.pack_propagate(False)
        tk.Label(bar, textvariable=self._conn_var, bg="#0f172a",
                 fg="#64748b", font=("Segoe UI", 8)).pack(side="left", padx=12)
        tk.Label(bar, textvariable=self._sync_var, bg="#0f172a",
                 fg="#64748b", font=("Segoe UI", 8)).pack(side="left", padx=6)
        tk.Label(bar, text="MedicVista v1.0", bg="#0f172a",
                 fg="#334155", font=("Segoe UI", 8)).pack(side="right", padx=12)


    # ── Register all screens (one instance each, hidden until shown) ───────────
    def _register_screens(self):
        screen_map: list[tuple[str, type]] = [
            ("Dashboard",                DashboardScreen),
            # Purchases
            ("Purchase Challan",         ChallanScreen),
            ("New Invoice",              PurchaseScreen),
            ("Invoices",                 PurchaseScreen),
            ("Reorder Level",            ReorderLevelScreen),
            ("Suppliers",                SupplierScreen),
            ("Returns",                  ReturnsScreen),  # Single instance for both
            ("Payment",                  ReceiptsScreen),
            ("Reorder Level",            ReorderLevelScreen),
            # Sales
            ("Sales Challan",            ChallanScreen),
            ("Sales New Invoice",        SalesScreen),
            ("Sales Invoices",           SalesScreen),
            ("Customers",                CustomerScreen),
            ("Receipt",                  ReceiptsScreen),
            ("Stock Issues",             StockIssueScreen),
            # Inventory
            ("Product List",             ProductScreen),
            ("All Products Inventory",   InventoryScreen),
            ("All Products Inventory 2", InventoryScreen),
            ("Batch-wise Report",        BatchWiseScreen),
            ("Date-wise Report",         DateWiseScreen),
            ("Stock Statement",          StockStatementScreen),
            ("Transaction History",      TransactionHistoryScreen),
            # Reports
            ("Sales Report",             ReportsScreen),
            ("Customer Wise Sales",      ReportsScreen),
            ("Purchases Report",         ReportsScreen),
            ("Reports",                  ReportsScreen),
            ("Financial Report",         FinancialReportScreen),
            ("Ledger",                   LedgerScreen),
            # Other
            ("Retailer Requests",        RetailerRequestsScreen),
            ("Database Backup",          BackupScreen),
        ]
        for name, cls in screen_map:
            if name not in self.screens:
                try:
                    self.screens[name] = cls(self.content_area, self)
                except Exception as e:
                    print(f"Screen init error [{name}]: {e}")

    # ── Show / hide screens ────────────────────────────────────────────────────
    def show_screen(self, name: str):
        # Sidebar actions that should open dialogs directly.
        if name == "New Invoice":
            from .ui.purchase.purchase_invoice_dialog import PurchaseInvoiceDialog
            PurchaseInvoiceDialog(self.content_area, self, on_saved=self.refresh_invoice_views)
            return

        if name == "Sales New Invoice":
            from .ui.sales.sales_invoice_dialog import SalesInvoiceDialog
            SalesInvoiceDialog(self.content_area, self, on_saved=self.refresh_invoice_views)
            return

        # Returns mode is controlled by the ReturnsScreen itself.
        set_returns_mode = None
        if name == "Purchase Return":
            set_returns_mode = "purchase"
        elif name == "Sales Return":
            set_returns_mode = "sales"

        aliases = {
            "Sales":       "Sales Report",
            "Purchases":   "Purchases Report",
        }
        name = aliases.get(name, name)

        # Map both Purchase Return and Sales Return to same screen instance
        screen_key = name
        if name in ("Purchase Return", "Sales Return"):
            screen_key = "Returns"

        for s in self.screens.values():
            s.pack_forget()

        screen = self.screens.get(screen_key)
        if screen:
            if isinstance(screen, ReturnsScreen) and set_returns_mode:
                screen._switch(set_returns_mode)
            screen.pack(fill="both", expand=True, padx=20, pady=14)
            self._active_screen = screen
            if hasattr(screen, "set_screen_name"):
                screen.set_screen_name(name)
            if hasattr(screen, "on_show"):
                try:
                    screen.on_show()
                except Exception as e:
                    print(f"on_show error [{name}]: {e}")

        else:
            ph = tk.Frame(self.content_area, bg=COLORS["white"])
            ph.pack(fill="both", expand=True, padx=20, pady=14)
            tk.Label(ph, text=f"{name}\n\nComing soon", font=("Inter", 18, "bold"),
                     fg=COLORS["gray_text"], bg=COLORS["white"]).pack(expand=True)

    def kb_new(self):
        """Dispatch Ctrl+N to the active screen."""
        screen = self._active_screen_instance()
        if screen and hasattr(screen, "kb_new"):
            screen.kb_new()

    def kb_search(self):
        screen = self._active_screen_instance()
        if screen and hasattr(screen, "kb_search"):
            screen.kb_search()

    def kb_refresh(self):
        screen = self._active_screen_instance()
        if screen and hasattr(screen, "kb_refresh"):
            screen.kb_refresh()
        elif screen and hasattr(screen, "on_show"):
            screen.on_show()

    def _active_screen_instance(self):
        """Return the currently visible screen instance."""
        if self._active_screen and self._active_screen.winfo_ismapped():
            return self._active_screen
        for s in self.screens.values():
            if s.winfo_ismapped():
                self._active_screen = s
                return s
        return None

    def refresh_invoice_views(self):
        """Refresh purchase and sales invoice listing screens after a dialog save."""
        for screen_name in ("Invoices", "Sales Invoices"):
            screen = self.screens.get(screen_name)
            if screen and hasattr(screen, "on_show"):
                try:
                    screen.on_show()
                except Exception as e:
                    print(f"refresh_invoice_views error [{screen_name}]: {e}")

    def sync_now(self):
        try:
            self.sync_service.run_once()
        except Exception:
            pass

    def go_back_or_close(self):
        pass  # handled by Escape → Toplevel close in shortcuts

    def current_action(self, action: str):
        """Legacy hook kept for compatibility."""
        pass

    def refresh_current(self):
        self.kb_refresh()

    def toggle_sidebar(self):
        if self.sidebar.winfo_ismapped():
            self.sidebar.pack_forget()
        else:
            self.sidebar.pack(side="left", fill="y", before=self.content_area)

    def set_connection_status(self, text: str):
        self._conn_var.set(text)

    def set_sync_status(self, dt):
        self._sync_var.set(f"Last sync: {dt.strftime('%d-%m-%Y %H:%M') if dt else 'never'}")

    def set_status(self, text: str):
        self._conn_var.set(text)

    def set_connection_state(self, connected: bool, message: str = ""):
        if connected:
            self._conn_var.set("● Connection: OK")
        else:
            self._conn_var.set(f"● Connection: {message[:60] if message else 'failed'}")

    def on_sync_complete(self, processed: int):
        self.set_sync_status(self.last_sync_at)
        if processed:
            self._conn_var.set(f"● Synced {processed} request(s)")
        else:
            self._conn_var.set("● Connection: OK")

    def process_request(self, request: dict):
        """Process a single retailer request — extend as needed."""
        pass

    def _show_shortcuts(self):
        from .shortcuts import show_help
        show_help(self)

    def _on_wholesaler_sync(self, result: dict):
        """Called on main thread after every wholesaler sync cycle."""
        connected  = result.get('connected', False)
        new_count  = len(result.get('new_requests', []))
        last_sync  = result.get('last_sync_time')
        error      = result.get('error')

        # Update status bar connection indicator
        if connected:
            self._conn_var.set(f"[OK] Connected to wholesaler")
        else:
            msg = error[:50] if error else 'Disconnected'
            self._conn_var.set(f"[X] Wholesaler: {msg}")

        # Update last sync time
        if last_sync:
            self._sync_var.set(f"Last sync: {last_sync}")

        # Notify Retailer Requests screen directly with full result
        screen = self.screens.get("Retailer Requests")
        if screen and hasattr(screen, '_on_sync_result'):
            try:
                screen._on_sync_result(result)
            except Exception:
                pass
        elif screen and hasattr(screen, 'on_show'):
            try:
                screen.on_show()
            except Exception:
                pass

        # Show notification in status bar for new requests
        if new_count:
            self._conn_var.set(f"[NEW] {new_count} new request(s) from wholesaler!")
            self.after(5000, lambda: self._conn_var.set(
                "[OK] Connected to wholesaler" if connected else "[X] Wholesaler: Disconnected"
            ))

    def _do_logout(self):
        """Stop services, destroy only main UI widgets, then show login screen."""
        # Detach sync callbacks FIRST — before any widget is destroyed
        # so no after(0, ...) fires on a dead widget
        bridge = getattr(self, "sync_bridge", None)
        if bridge and hasattr(bridge, "_runner") and bridge._runner:
            try:
                bridge._runner.on_sync_complete = lambda *a, **kw: None
            except Exception:
                pass
        screen = getattr(self, "screens", {}).get("Retailer Requests")
        if screen and getattr(screen, "_runner", None):
            try:
                screen._runner.on_sync_complete = lambda *a, **kw: None
            except Exception:
                pass

        if hasattr(self, "sync_service"):
            try:
                self.sync_service.stop()
            except Exception:
                pass
        if bridge:
            try:
                bridge.stop()
            except Exception:
                pass
        # Destroy only the tracked main UI frames (navbar, main_frame, statusbar)
        for widget in getattr(self, "_main_widgets", []):
            try:
                widget.destroy()
            except Exception:
                pass
        self._main_widgets = []
        self._main_built = False
        self._current_user = ""
        self.screens = {}
        self._active_screen = None
        self._login_frame = None
        self._show_login()

    def close_app(self):
        if hasattr(self, "sync_service"):
            self.sync_service.stop()
        # Stop wholesaler sync runner cleanly
        bridge = getattr(self, "sync_bridge", None)
        if bridge:
            try:
                bridge.stop()
            except Exception:
                pass
        # Also stop any runner owned directly by the screen
        screen = self.screens.get("Retailer Requests")
        if screen and getattr(screen, "_runner", None):
            try:
                screen._runner.stop()
            except Exception:
                pass
        self.destroy()
