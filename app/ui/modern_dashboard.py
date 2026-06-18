"""
Modern, colorful dashboard with animated cards and stats.
"""
import tkinter as tk
from tkinter import ttk
from ...styles import COLORS, FONT
from ...modern_ui_components import (
    ModernButton, ModernLabel, ModernFrame, StatusBadge,
    AnimatedProgressBar, LoadingSpinner, SeparatorWithLabel, HoverFrame
)


class ModernStatsCard(tk.Frame):
    """Modern stats card with color accent, icon, and value."""
    
    def __init__(self, parent, title, value, subtitle="", icon="📊", color=None, **kwargs):
        self.color = color or COLORS["purple"]
        
        super().__init__(
            parent,
            bg=COLORS["white"],
            relief="flat",
            bd=0,
            **kwargs
        )
        
        # Color accent bar on left
        accent = tk.Frame(self, bg=self.color, width=5)
        accent.pack(side="left", fill="y")
        
        # Content area
        content = tk.Frame(self, bg=COLORS["white"], padx=16, pady=14)
        content.pack(side="left", fill="both", expand=True)
        
        # Title
        tk.Label(
            content,
            text=title,
            font=("Segoe UI", 10),
            fg=COLORS["gray_text"],
            bg=COLORS["white"]
        ).pack(anchor="w")
        
        # Value
        tk.Label(
            content,
            text=value,
            font=("Segoe UI", 22, "bold"),
            fg=COLORS["dark_text"],
            bg=COLORS["white"]
        ).pack(anchor="w", pady=(4, 0))
        
        # Subtitle
        if subtitle:
            tk.Label(
                content,
                text=subtitle,
                font=("Segoe UI", 9),
                fg=COLORS["muted"],
                bg=COLORS["white"]
            ).pack(anchor="w", pady=(2, 0))
        
        # Icon on right
        icon_label = tk.Label(
            self,
            text=icon,
            font=("Segoe UI", 28),
            fg=self.color,
            bg=COLORS["white"],
            padx=12
        )
        icon_label.pack(side="right", fill="y")
        
        # Hover effect
        for widget in [self, content, accent, icon_label]:
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        """Hover in effect."""
        self.config(bg=COLORS["white2"])
    
    def _on_leave(self, event):
        """Hover out effect."""
        self.config(bg=COLORS["white"])


class ModernDashboard(tk.Frame):
    """Modern dashboard with stats, charts, and recent activities."""
    
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=COLORS["bg_light"], **kwargs)
        self.app = app_instance
        self._build()
    
    def _build(self):
        """Build the dashboard."""
        # Main scrollable container
        main_frame = tk.Frame(self, bg=COLORS["bg_light"])
        main_frame.pack(fill="both", expand=True, padx=16, pady=16)
        
        # Header section
        self._build_header(main_frame)
        
        # Stats cards section
        self._build_stats(main_frame)
        
        # Action buttons
        self._build_actions(main_frame)
        
        # Recent activity section
        self._build_activity(main_frame)
    
    def _build_header(self, parent):
        """Build dashboard header."""
        header = tk.Frame(parent, bg=COLORS["bg_light"])
        header.pack(fill="x", pady=(0, 16))
        
        tk.Label(
            header,
            text="Dashboard",
            font=("Segoe UI", 26, "bold"),
            fg=COLORS["dark_text"],
            bg=COLORS["bg_light"]
        ).pack(side="left", anchor="w")
        
        tk.Label(
            header,
            text="Pharmacy Overview & Analytics",
            font=("Segoe UI", 11),
            fg=COLORS["gray_text"],
            bg=COLORS["bg_light"]
        ).pack(side="left", padx=(12, 0), anchor="w")
    
    def _build_stats(self, parent):
        """Build stats cards section."""
        stats_frame = tk.Frame(parent, bg=COLORS["bg_light"])
        stats_frame.pack(fill="x", pady=(0, 16))
        
        # Configure grid
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)
        
        # Stats data
        stats = [
            ("Total Products", "2,543", "Active SKUs", "💊", COLORS["blue_badge"]),
            ("Inventory Value", "₹45.2L", "+5.2% this month", "₹", COLORS["green"]),
            ("Low Stock", "127", "Needs attention", "⚠", COLORS["orange"]),
            ("Out of Stock", "23", "Reorder soon", "✖", COLORS["red"]),
        ]
        
        for col, (title, value, subtitle, icon, color) in enumerate(stats):
            card = ModernStatsCard(
                stats_frame,
                title=title,
                value=value,
                subtitle=subtitle,
                icon=icon,
                color=color
            )
            card.grid(row=0, column=col, sticky="nsew", padx=4, pady=4)
    
    def _build_actions(self, parent):
        """Build action buttons section."""
        actions_frame = tk.Frame(parent, bg=COLORS["bg_light"])
        actions_frame.pack(fill="x", pady=(0, 16))
        
        tk.Label(
            actions_frame,
            text="Quick Actions",
            font=("Segoe UI", 12, "bold"),
            fg=COLORS["dark_text"],
            bg=COLORS["bg_light"]
        ).pack(anchor="w", pady=(0, 8))
        
        # Action buttons
        buttons_frame = tk.Frame(actions_frame, bg=COLORS["bg_light"])
        buttons_frame.pack(fill="x")
        
        actions = [
            ("📊 Low Stock Report", COLORS["orange"], "warning"),
            ("📈 Sales Analytics", COLORS["green"], "success"),
            ("🔄 Sync Inventory", COLORS["blue_badge"], "info"),
            ("📋 Generate Invoice", COLORS["purple"], "primary"),
            ("📥 Import Stock", COLORS["accent_cyan"], "info"),
            ("📤 Export Report", COLORS["green"], "success"),
        ]
        
        for text, color, variant in actions:
            btn = ModernButton(
                buttons_frame,
                text=text,
                variant=variant,
                padx=12,
                pady=8,
                font=("Segoe UI", 9)
            )
            btn.pack(side="left", padx=(0, 8), pady=(0, 8))
    
    def _build_activity(self, parent):
        """Build recent activity section."""
        activity_frame = tk.Frame(parent, bg=COLORS["bg_light"])
        activity_frame.pack(fill="both", expand=True, pady=(0, 0))
        
        tk.Label(
            activity_frame,
            text="Recent Activity",
            font=("Segoe UI", 12, "bold"),
            fg=COLORS["dark_text"],
            bg=COLORS["bg_light"]
        ).pack(anchor="w", pady=(0, 12))
        
        # Activity card
        card_frame = tk.Frame(activity_frame, bg=COLORS["white"])
        card_frame.pack(fill="both", expand=True)
        
        # Sample activity items
        activities = [
            ("✅", "Stock Added", "2000 units of Paracetamol added to inventory", "10:30 AM", "active"),
            ("📝", "Invoice Created", "INV-2024-001 - ₹15,000", "9:45 AM", "info"),
            ("⚠", "Low Stock Alert", "Ibuprofen below 500 units", "8:20 AM", "warning"),
            ("❌", "Stock Issued", "1500 units of Cough Syrup issued", "7:15 AM", "inactive"),
        ]
        
        for idx, (icon, title, desc, time, status) in enumerate(activities):
            self._build_activity_item(card_frame, icon, title, desc, time, status, idx)
    
    def _build_activity_item(self, parent, icon, title, desc, time, status, idx):
        """Build individual activity item."""
        # Alternate row colors
        bg_color = COLORS["row_even"] if idx % 2 == 0 else COLORS["row_odd"]
        
        item = tk.Frame(parent, bg=bg_color, relief="flat", bd=0)
        item.pack(fill="x")
        
        # Icon
        tk.Label(
            item,
            text=icon,
            font=("Segoe UI", 16),
            bg=bg_color,
            fg=COLORS["gray_text"]
        ).pack(side="left", padx=12, pady=10)
        
        # Content
        content = tk.Frame(item, bg=bg_color)
        content.pack(side="left", fill="both", expand=True, pady=10)
        
        tk.Label(
            content,
            text=title,
            font=("Segoe UI", 10, "bold"),
            fg=COLORS["dark_text"],
            bg=bg_color
        ).pack(anchor="w")
        
        tk.Label(
            content,
            text=desc,
            font=("Segoe UI", 9),
            fg=COLORS["gray_text"],
            bg=bg_color
        ).pack(anchor="w", pady=(2, 0))
        
        # Time and status
        footer = tk.Frame(content, bg=bg_color)
        footer.pack(fill="x", pady=(4, 0))
        
        tk.Label(
            footer,
            text=time,
            font=("Segoe UI", 8),
            fg=COLORS["muted"],
            bg=bg_color
        ).pack(side="left")
        
        status_badge = StatusBadge(footer, text=status.upper(), status=status)
        status_badge.pack(side="right", padx=12)


class ModernDashboardScreen(tk.Frame):
    """Wrapper with scrollbar for the dashboard."""
    
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=COLORS["bg_light"], **kwargs)
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(self, bg=COLORS["bg_light"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS["bg_light"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack elements
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add dashboard content
        ModernDashboard(scrollable_frame, app_instance).pack(fill="both", expand=True)
