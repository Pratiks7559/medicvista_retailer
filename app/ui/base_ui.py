import tkinter as tk
from tkinter import ttk
from datetime import datetime

from ..styles import COLORS

class BaseUI(ttk.Frame):
    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.app = app_instance
        self.parent = parent
        self.pack(fill="both", expand=True)

        self.sidebar_width_collapsed = 70
        self.sidebar_width_expanded = 260
        self.is_sidebar_expanded = False

        self._create_widgets()
        self._setup_layout()
        self._bind_events()

    def _create_widgets(self):
        # Main container for the entire UI
        self.main_container = ttk.Frame(self, style="TFrame")
        self.main_container.pack(fill="both", expand=True)

        # --- Sidebar ---
        self.sidebar_frame = ttk.Frame(self.main_container, style="Sidebar.TFrame", width=self.sidebar_width_collapsed)
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False) # Prevent sidebar from resizing to fit content

        # Sidebar content frame for padding and internal layout
        self.sidebar_content_frame = ttk.Frame(self.sidebar_frame, style="Sidebar.TFrame", padding=(10, 10, 10, 0))
        self.sidebar_content_frame.pack(fill="both", expand=True)

        # User Profile Section
        self.user_profile_frame = ttk.Frame(self.sidebar_content_frame, style="Sidebar.TFrame")
        self.user_profile_frame.pack(fill="x", pady=(0, 10))

        # Placeholder for avatar (can be replaced with image later)
        self.user_avatar_label = ttk.Label(self.user_profile_frame, text="👤", font=("Inter", 20),
                                           foreground=COLORS["sidebar_text"], background=COLORS["sidebar_bg_start"])
        self.user_avatar_label.pack(side="left", padx=(0, 5))

        self.user_info_frame = ttk.Frame(self.user_profile_frame, style="Sidebar.TFrame")
        self.user_info_frame.pack(side="left", fill="x", expand=True)

        self.user_name_label = ttk.Label(self.user_info_frame, text="User Name", font=("Inter", 10, "bold"),
                                         foreground=COLORS["sidebar_text"], background=COLORS["sidebar_bg_start"])
        self.user_name_label.pack(anchor="w")

        self.user_type_label = ttk.Label(self.user_info_frame, text="User Type", font=("Inter", 8),
                                         foreground=COLORS["sidebar_text_muted"], background=COLORS["sidebar_bg_start"])
        self.user_type_label.pack(anchor="w")

        # Navigation Menu Frame
        self.nav_menu_frame = ttk.Frame(self.sidebar_content_frame, style="Sidebar.TFrame")
        self.nav_menu_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.nav_buttons_frame = ttk.Frame(self.nav_menu_frame, style="Sidebar.TFrame")
        self.nav_buttons_frame.pack(fill="both", expand=True)

        self.nav_buttons: dict[str, ttk.Button] = {}
        nav_items = [
            ("Dashboard", "F1", "Dashboard"),
            ("Product Master", "F2", "Product Master"),
            ("Purchase", "F3", "Purchase"),
            ("Sales", "F4", "Sales"),
            ("Invoice", "Ctrl+I", "Invoice"),
            ("Stock Management", "F5", "Stock Management"),
            ("Reports", "F6", "Reports"),
            ("Retailer Requests", "F7", "Retailer Requests"),
            ("Settings", "F8", "Settings"),
        ]

        for name, shortcut, screen_name in nav_items:
            button = ttk.Button(
                self.nav_buttons_frame,
                text=f"{shortcut}  {name}",
                command=lambda s=screen_name: self.app.show_screen(s),
                style="Sidebar.TButton"
            )
            button.pack(fill="x", pady=1)
            self.nav_buttons[screen_name] = button

        # Sidebar Footer (Logout)
        self.sidebar_footer_frame = ttk.Frame(self.sidebar_content_frame, style="Sidebar.TFrame")
        self.sidebar_footer_frame.pack(fill="x", pady=(10, 0))

        self.logout_button = ttk.Button(
            self.sidebar_footer_frame,
            text="Logout",
            command=self.app.close_app, # Or a dedicated logout function
            style="Danger.TButton" # Using Danger style for logout
        )
        self.logout_button.pack(fill="x")

        # --- Main Content Area ---
        self.main_content_area = ttk.Frame(self.main_container, style="TFrame")
        self.main_content_area.pack(side="left", fill="both", expand=True)

        # --- Navbar ---
        self.navbar_frame = ttk.Frame(self.main_content_area, style="Navbar.TFrame", height=56)
        self.navbar_frame.pack(fill="x")
        self.navbar_frame.pack_propagate(False) # Prevent navbar from resizing to fit content

        # Navbar Left: Sidebar Toggle and Brand
        self.navbar_left_frame = ttk.Frame(self.navbar_frame, style="Navbar.TFrame")
        self.navbar_left_frame.pack(side="left", padx=10)

        self.sidebar_toggle_button = ttk.Button(
            self.navbar_left_frame,
            text="☰", # Hamburger icon
            command=self.toggle_sidebar,
            style="Navbar.TButton"
        )
        self.sidebar_toggle_button.pack(side="left", padx=(0, 10))

        # Brand Logo and Text
        self.brand_frame = ttk.Frame(self.navbar_left_frame, style="Navbar.TFrame")
        self.brand_frame.pack(side="left")

        # Placeholder for logo image
        self.logo_label = ttk.Label(self.brand_frame, text="💊", font=("Inter", 20, "bold"),
                                    foreground=COLORS["navbar_text"], background=COLORS["navbar_bg_start"])
        self.logo_label.pack(side="left", padx=(0, 5))

        self.brand_text_label = ttk.Label(self.brand_frame, text="MedicVista", font=("Inter", 14, "bold"),
                                          foreground=COLORS["navbar_text"], background=COLORS["navbar_bg_start"])
        self.brand_text_label.pack(side="left")

        # Navbar Right: Year Filter and User Dropdown
        self.navbar_right_frame = ttk.Frame(self.navbar_frame, style="Navbar.TFrame")
        self.navbar_right_frame.pack(side="right", padx=10)

        # Year Filter (Placeholder for now)
        self.year_filter_button = ttk.Button(
            self.navbar_right_frame,
            text="FY 2023-24 ▼",
            command=self._show_year_filter_dropdown, # To be implemented
            style="Navbar.TButton"
        )
        self.year_filter_button.pack(side="left", padx=(0, 10))

        # User Dropdown (Placeholder for now)
        self.user_dropdown_button = ttk.Button(
            self.navbar_right_frame,
            text="👤 User ▼",
            command=self._show_user_dropdown, # To be implemented
            style="Navbar.TButton"
        )
        self.user_dropdown_button.pack(side="left")

        # --- Main Content Frame (where screens will be displayed) ---
        self.content_frame = ttk.Frame(self.main_content_area, style="TFrame", padding=15)
        self.content_frame.pack(fill="both", expand=True)

        # --- Status Bar ---
        self.status_bar = ttk.Frame(self.main_content_area, style="Panel.TFrame", padding=(10, 6))
        self.status_bar.pack(fill="x", side="bottom")

        self.connection_var = tk.StringVar(value="Connection: not checked")
        self.sync_var = tk.StringVar(value="Last sync: never")
        self.status_var = tk.StringVar(value="Ready")

        ttk.Label(self.status_bar, textvariable=self.connection_var, style="Muted.TLabel").pack(side="left", padx=(0, 18))
        ttk.Label(self.status_bar, textvariable=self.sync_var, style="Muted.TLabel").pack(side="left", padx=(0, 18))
        ttk.Label(self.status_bar, textvariable=self.status_var, style="Muted.TLabel").pack(side="left")

    def _setup_layout(self):
        # Initial state of sidebar
        self.sidebar_frame.config(width=self.sidebar_width_collapsed)
        self.user_info_frame.pack_forget() # Hide user info initially
        self.logout_button.config(text="⏏") # Icon for collapsed state
        self.sidebar_toggle_button.config(text="☰") # Ensure toggle button is correct

    def _bind_events(self):
        # Bind resize event to adjust sidebar if needed (though pack_propagate handles much)
        self.parent.bind("<Configure>", self._on_parent_resize)

    def _on_parent_resize(self, event):
        # This can be used for more complex responsive logic if needed
        pass

    def toggle_sidebar(self):
        if self.is_sidebar_expanded:
            self.sidebar_frame.config(width=self.sidebar_width_collapsed)
            self.user_info_frame.pack_forget()
            self.user_avatar_label.pack(side="left", padx=(0, 0)) # Adjust padding for icon-only
            for name, button in self.nav_buttons.items():
                button.config(text=self._get_nav_icon(name)) # Show only icon
            self.logout_button.config(text="⏏") # Logout icon
            self.brand_text_label.pack_forget() # Hide brand text
            self.logo_label.pack(side="left", padx=(0,0)) # Adjust logo padding
        else:
            self.sidebar_frame.config(width=self.sidebar_width_expanded)
            self.user_avatar_label.pack(side="left", padx=(0, 5)) # Restore padding
            self.user_info_frame.pack(side="left", fill="x", expand=True)
            for name, button in self.nav_buttons.items():
                button.config(text=self._get_nav_text(name)) # Show text and shortcut
            self.logout_button.config(text="Logout") # Full text
            self.logo_label.pack(side="left", padx=(0, 5)) # Restore logo padding
            self.brand_text_label.pack(side="left") # Show brand text

        self.is_sidebar_expanded = not self.is_sidebar_expanded
        self.parent.update_idletasks() # Update layout immediately

    def _get_nav_icon(self, name):
        # Map screen names to simple icons for collapsed sidebar
        icons = {
            "Dashboard": "🏠",
            "Product Master": "📦",
            "Purchase": "🛒",
            "Sales": "📈",
            "Invoice": "🧾",
            "Stock Management": "📊",
            "Reports": " رپورٹس", # Using a generic report icon
            "Retailer Requests": "✉️",
            "Settings": "⚙️",
        }
        return icons.get(name, "❓") # Default icon

    def _get_nav_text(self, name):
        # Map screen names to full text with shortcut
        texts = {
            "Dashboard": "F1  Dashboard",
            "Product Master": "F2  Product Master",
            "Purchase": "F3  Purchase",
            "Sales": "F4  Sales",
            "Invoice": "Ctrl+I  Invoice",
            "Stock Management": "F5  Stock Management",
            "Reports": "F6  Reports",
            "Retailer Requests": "F7  Retailer Requests",
            "Settings": "F8  Settings",
        }
        return texts.get(name, name)

    def _show_year_filter_dropdown(self):
        # Placeholder for year filter dropdown logic
        print("Show year filter dropdown")

    def _show_user_dropdown(self):
        # Placeholder for user dropdown logic
        print("Show user dropdown")

    def set_user_info(self, username, user_type):
        self.user_name_label.config(text=username)
        self.user_type_label.config(text=user_type)

    def set_connection_status(self, status_text):
        self.connection_var.set(status_text)

    def set_sync_status(self, sync_time: datetime | None):
        sync_text = sync_time.strftime("%d-%m-%Y %H:%M:%S") if sync_time else "never"
        self.sync_var.set(f"Last sync: {sync_text}")

    def set_app_status(self, message):
        self.status_var.set(message)
