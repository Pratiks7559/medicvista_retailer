"""
Modern colorful sidebar with smooth animations and better UX.
"""
import tkinter as tk
from tkinter import ttk
from ...styles import COLORS, FONT


class ModernColorfulSidebar(tk.Frame):
    """Modern sidebar with accordion navigation, colorful accents, and smooth animations."""
    
    # Color scheme for sections
    SECTION_COLORS = {
        "Dashboard": "#2563eb",      # blue
        "Purchases": "#7c3aed",      # purple
        "Sales": "#059669",          # green
        "Inventory": "#d97706",      # amber
        "Reports": "#dc2626",        # red
        "Finance": "#0891b2",        # cyan
        "Other": "#6366f1",          # indigo
    }
    
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, bg=COLORS["sidebar_bg"], width=260, **kwargs)
        self.pack_propagate(False)
        self.app = app
        
        self._active_section = None
        self._active_item = None
        self._section_frames = {}
        self._item_buttons = {}
        
        self._build()
    
    def _build(self):
        """Build the sidebar."""
        # Header with logo
        self._build_header()
        
        # Navigation sections
        self._build_navigation()
        
        # Footer with logout
        self._build_footer()
    
    def _build_header(self):
        """Build sidebar header with branding."""
        header = tk.Frame(self, bg=COLORS["purple"], height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Logo emoji
        tk.Label(
            header,
            text="💊",
            font=("Segoe UI", 32),
            bg=COLORS["purple"],
            fg="white"
        ).pack(pady=(8, 0))
        
        tk.Label(
            header,
            text="MedicVista",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["purple"],
            fg="white"
        ).pack()
        
        # Separator
        separator = tk.Frame(self, bg=COLORS["border_color"], height=1)
        separator.pack(fill="x", pady=12)
    
    def _build_navigation(self):
        """Build navigation sections with accordion."""
        nav_frame = tk.Frame(self, bg=COLORS["sidebar_bg"])
        nav_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Define sections and their items
        sections = {
            "Purchases": [
                # ("Purchase Challan", "Purchase Challan"),  # hidden
                ("New Invoice", "New Invoice"),
                ("All Invoices", "Invoices"),
                ("Suppliers", "Suppliers"),
                # ("Purchase Return", "Purchase Return"),  # hidden
                ("Payment", "Payment"),
                ("Reorder Level", "Reorder Level"),
            ],
            "Sales": [
                # ("Sales Challan", "Sales Challan"),  # hidden
                ("New Sale", "Sales New Invoice"),
                ("All Sales", "Sales Invoices"),
                ("Customers", "Customers"),
                # ("Sales Return", "Sales Return"),  # hidden
                ("Receipt", "Receipt"),
                # ("Stock Issues", "Stock Issues"),  # hidden
            ],
            "Inventory": [
                ("Product List", "Product List"),
                ("All Inventory", "All Products Inventory"),
                ("Batch Report", "Batch-wise Report"),
                ("Stock Statement", "Stock Statement"),
                ("Transaction History", "Transaction History"),
            ],
            "Reports": [
                ("Sales Report", "Sales Report"),
                ("Purchase Report", "Purchases Report"),
                ("Financial", "Financial"),
                # ("Ledger", "Ledger"),  # hidden
            ],
            "Finance": [
                ("Accounts", "Finance"),
            ],
            "Other": [
                ("Retailer Requests", "Retailer Requests"),
            ],
        }
        
        # Create sections
        for section_name, items in sections.items():
            self._build_section(nav_frame, section_name, items)
    
    def _build_section(self, parent, section_name, items):
        """Build a navigation section."""
        color = self.SECTION_COLORS.get(section_name, COLORS["purple"])
        
        # Section header (clickable to expand/collapse)
        header_btn = tk.Button(
            parent,
            text=f"▼ {section_name}",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["sidebar_bg"],
            fg=color,
            bd=0,
            relief="flat",
            padx=12,
            pady=10,
            anchor="w",
            cursor="hand2",
            activebackground=COLORS["white2"],
            activeforeground=color
        )
        header_btn.pack(fill="x", padx=0, pady=0)
        
        # Content frame for items (collapsible)
        content_frame = tk.Frame(parent, bg=COLORS["sidebar_bg"])
        content_frame.pack(fill="x", padx=0, pady=0)
        
        self._section_frames[section_name] = {
            "button": header_btn,
            "frame": content_frame,
            "is_open": True
        }
        
        # Add items to section
        for item_label, screen_name in items:
            self._build_item(content_frame, section_name, item_label, screen_name, color)
        
        # Bind section header click
        header_btn.config(
            command=lambda: self._toggle_section(section_name)
        )
    
    def _build_item(self, parent, section_name, label, screen_name, color):
        """Build a navigation item."""
        item_btn = tk.Button(
            parent,
            text=f"  › {label}",
            font=("Segoe UI", 9),
            bg=COLORS["sidebar_bg"],
            fg=COLORS["sidebar_text"],
            bd=0,
            relief="flat",
            padx=12,
            pady=8,
            anchor="w",
            cursor="hand2",
            activebackground=COLORS["white2"],
            activeforeground=color
        )
        item_btn.pack(fill="x", padx=0, pady=0)
        
        # Store reference
        self._item_buttons[screen_name] = {
            "button": item_btn,
            "section": section_name,
            "color": color
        }
        
        # Hover effects
        def on_enter(e, btn=item_btn, col=color):
            btn.config(bg=COLORS["white2"], fg=col)
        
        def on_leave(e, btn=item_btn):
            if screen_name != self._active_item:
                btn.config(bg=COLORS["sidebar_bg"], fg=COLORS["sidebar_text"])
        
        item_btn.bind("<Enter>", on_enter)
        item_btn.bind("<Leave>", on_leave)
        
        # Click handler
        item_btn.config(command=lambda: self._select_item(screen_name, item_btn, color))
    
    def _toggle_section(self, section_name):
        """Toggle section expansion."""
        section = self._section_frames[section_name]
        is_open = section["is_open"]
        
        if is_open:
            section["frame"].pack_forget()
            section["button"].config(text=f"▶ {section_name}")
            section["is_open"] = False
        else:
            section["frame"].pack(fill="x", padx=0, pady=0, after=section["button"])
            section["button"].config(text=f"▼ {section_name}")
            section["is_open"] = True
    
    def _select_item(self, screen_name, btn, color):
        """Handle item selection."""
        # Deselect previous item
        if self._active_item and self._active_item in self._item_buttons:
            prev_btn = self._item_buttons[self._active_item]["button"]
            prev_btn.config(bg=COLORS["sidebar_bg"], fg=COLORS["sidebar_text"])
        
        # Select new item
        btn.config(bg=color, fg="white")
        self._active_item = screen_name
        
        # Trigger screen change in app
        if self.app and hasattr(self.app, "show_screen"):
            self.app.show_screen(screen_name)
    
    def _build_footer(self):
        """Build sidebar footer with user info and logout."""
        # Separator
        separator = tk.Frame(self, bg=COLORS["border_color"], height=1)
        separator.pack(fill="x", pady=8)
        
        # Footer frame
        footer = tk.Frame(self, bg=COLORS["sidebar_bg"])
        footer.pack(fill="x", padx=8, pady=8)
        
        # User info (placeholder)
        user_frame = tk.Frame(footer, bg=COLORS["white2"], relief="flat", bd=0)
        user_frame.pack(fill="x", padx=0, pady=(0, 8))
        
        tk.Label(
            user_frame,
            text="👤",
            font=("Segoe UI", 16),
            bg=COLORS["white2"],
            fg=COLORS["gray_text"]
        ).pack(side="left", padx=8, pady=8)
        
        user_info = tk.Frame(user_frame, bg=COLORS["white2"])
        user_info.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=8)
        
        tk.Label(
            user_info,
            text="User Name",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["white2"],
            fg=COLORS["dark_text"]
        ).pack(anchor="w")
        
        tk.Label(
            user_info,
            text="Admin",
            font=("Segoe UI", 8),
            bg=COLORS["white2"],
            fg=COLORS["gray_text"]
        ).pack(anchor="w")
        
        # Logout button
        logout_btn = tk.Button(
            footer,
            text="🚪 Logout",
            font=("Segoe UI", 9, "bold"),
            bg="#7f1d1d",
            fg="white",
            bd=0,
            relief="flat",
            padx=8,
            pady=6,
            anchor="center",
            cursor="hand2",
            activebackground="#991b1b",
            activeforeground="white"
        )
        logout_btn.pack(fill="x", padx=0, pady=(0, 0))
        
        # Logout click handler
        if self.app and hasattr(self.app, "do_logout"):
            logout_btn.config(command=self.app.do_logout)
    
    def set_active_screen(self, screen_name):
        """Set the active screen (called from app)."""
        if screen_name in self._item_buttons:
            btn = self._item_buttons[screen_name]["button"]
            color = self._item_buttons[screen_name]["color"]
            self._select_item(screen_name, btn, color)
            
            # Expand section if collapsed
            section_name = self._item_buttons[screen_name]["section"]
            if section_name in self._section_frames:
                if not self._section_frames[section_name]["is_open"]:
                    self._toggle_section(section_name)
