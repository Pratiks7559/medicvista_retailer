import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import random

# Use shared styling tokens from the app theme (styling-only changes)
from ..styles import COLORS, status_color


# ============================================================================
# Design System - Modern CSS-like Styling
# ============================================================================

class DesignTokens:
    """Centralized design system with CSS-like variables"""
    
    # Color Palette - Modern Glassmorphism Theme
    COLORS = {
        # Base colors
        'primary': '#6366f1',      # Indigo
        'primary-dark': '#4f46e5',
        'primary-light': '#818cf8',
        'secondary': '#8b5cf6',    # Purple
        'accent': '#06b6d4',       # Cyan
        'success': '#10b981',      # Emerald
        'warning': '#f59e0b',      # Amber
        'error': '#ef4444',        # Red
        'info': '#3b82f6',         # Blue
        
        # Neutral colors
        'gray-50': '#f9fafb',
        'gray-100': '#f3f4f6',
        'gray-200': '#e5e7eb',
        'gray-300': '#d1d5db',
        'gray-400': '#9ca3af',
        'gray-500': '#6b7280',
        'gray-600': '#4b5563',
        'gray-700': '#374151',
        'gray-800': '#1f2937',
        'gray-900': '#111827',
        
        # Theme specific
        'bg-primary': '#0f172a',      # Slate-900
        'bg-secondary': '#1e293b',    # Slate-800
        'bg-tertiary': '#334155',     # Slate-700
        'surface': '#1e293b',
        'surface-hover': '#334155',
        'border': '#334155',
        'border-light': '#475569',
        'white': '#ffffff',
    }
    
    # Typography
    TYPOGRAPHY = {
        'font-family': 'Inter, Segoe UI, Helvetica Neue, Arial',
        'font-mono': 'JetBrains Mono, Consolas, Courier New',
        'sizes': {
            'xs': 10,
            'sm': 11,
            'base': 12,
            'lg': 14,
            'xl': 16,
            '2xl': 18,
            '3xl': 20,
            '4xl': 24,
            '5xl': 28,
        },
        'weights': {
            'normal': 'normal',
            'medium': 'bold',
            'semibold': 'bold',
            'bold': 'bold',
        }
    }
    
    # Spacing (8px grid system)
    SPACING = {
        '0': 0, 'px': 1, '0.5': 2, '1': 4, '1.5': 6, '2': 8, '2.5': 10,
        '3': 12, '3.5': 14, '4': 16, '5': 20, '6': 24, '7': 28, '8': 32,
        '9': 36, '10': 40, '11': 44, '12': 48, '14': 56, '16': 64,
    }
    
    # Border radius
    RADIUS = {
        'none': 0,
        'sm': 4,
        'base': 6,
        'md': 8,
        'lg': 12,
        'xl': 16,
        '2xl': 20,
        '3xl': 24,
        'full': 100,
    }
    
    # Shadows
    SHADOWS = {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'base': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        'glow': '0 0 20px rgba(99, 102, 241, 0.3)',
    }
    
    # Animations
    ANIMATIONS = {
        'transition-fast': 150,
        'transition-normal': 200,
        'transition-slow': 300,
        'ease': 'ease-out',
    }


class ModernStyle:
    """CSS-like style manager for tkinter widgets"""
    
    @staticmethod
    def apply_glassmorphism(widget, bg_opacity=0.8):
        """Apply glassmorphism effect"""
        widget.configure(
            bg=DesignTokens.COLORS['surface'],
            relief='flat'
        )
        
    @staticmethod
    def apply_gradient(widget, color1, color2, horizontal=True):
        """Simulate gradient background"""
        # Note: tkinter doesn't support true gradients, this is a simulation
        widget.configure(bg=color1)
        
    @staticmethod
    def configure_treeview_style():
        """Configure advanced Treeview styling"""
        style = ttk.Style()
        
        # Custom treeview style
        style.configure(
            "Modern.Treeview",
            background=DesignTokens.COLORS['bg-secondary'],
            foreground=DesignTokens.COLORS['gray-100'],
            fieldbackground=DesignTokens.COLORS['bg-secondary'],
            borderwidth=0,
            font=(DesignTokens.TYPOGRAPHY['font-family'], 
                  DesignTokens.TYPOGRAPHY['sizes']['base']),
            rowheight=40,
        )
        
        style.configure(
            "Modern.Treeview.Heading",
            background=DesignTokens.COLORS['bg-tertiary'],
            foreground=DesignTokens.COLORS['gray-200'],
            borderwidth=0,
            font=(DesignTokens.TYPOGRAPHY['font-family'], 
                  DesignTokens.TYPOGRAPHY['sizes']['sm'],
                  DesignTokens.TYPOGRAPHY['weights']['semibold']),
            padding=(12, 8),
        )
        
        # Hover effect
        style.map(
            "Modern.Treeview",
            background=[
                ('selected', DesignTokens.COLORS['primary']),
                ('hover', DesignTokens.COLORS['surface-hover']),
            ],
            foreground=[
                ('selected', DesignTokens.COLORS['gray-50']),
            ]
        )
        
        return style


# ============================================================================
# Advanced UI Components
# ============================================================================

class AnimatedButton(tk.Button):
    """Button with hover animations and ripple effect"""
    
    def __init__(self, parent, text="", variant="primary", size="md", 
                 icon=None, command=None, **kwargs):
        
        self.variant = variant
        self.size = size
        self.icon = icon
        self.is_hovered = False
        self.ripple_animation = None
        
        # Color mapping
        colors = {
            'primary': (DesignTokens.COLORS['primary'], 
                       DesignTokens.COLORS['primary-dark'],
                       DesignTokens.COLORS['primary-light']),
            'secondary': (DesignTokens.COLORS['secondary'],
                         DesignTokens.COLORS['primary-dark'],
                         DesignTokens.COLORS['primary-light']),
            'success': (DesignTokens.COLORS['success'],
                       '#0e9f6e', '#34d399'),
            'danger': (DesignTokens.COLORS['error'],
                      '#dc2626', '#f87171'),
            'warning': (DesignTokens.COLORS['warning'],
                       '#d97706', '#fbbf24'),
            'outline': (DesignTokens.COLORS['bg-secondary'],
                       DesignTokens.COLORS['surface-hover'],
                       DesignTokens.COLORS['border-light']),
        }
        
        self.bg_color, self.hover_color, self.active_color = colors.get(
            variant, colors['primary']
        )
        
        # Size configuration
        sizes = {
            'sm': (8, 4, DesignTokens.TYPOGRAPHY['sizes']['sm']),
            'md': (12, 6, DesignTokens.TYPOGRAPHY['sizes']['base']),
            'lg': (16, 8, DesignTokens.TYPOGRAPHY['sizes']['lg']),
        }
        padx, pady, font_size = sizes.get(size, sizes['md'])
        
        # Prepare display text
        display_text = f" {text}" if icon else text
        if icon:
            display_text = f"{icon} {text}"
        
        super().__init__(
            parent,
            text=display_text,
            command=command,
            font=(DesignTokens.TYPOGRAPHY['font-family'], font_size,
                  DesignTokens.TYPOGRAPHY['weights']['medium']),
            bg=self.bg_color,
            fg=DesignTokens.COLORS['gray-100'],
            activebackground=self.hover_color,
            activeforeground=DesignTokens.COLORS['white'],
            cursor="hand2",
            relief="flat",
            padx=padx,
            pady=pady,
            bd=0,
            **kwargs
        )
        
        # Apply border for outline variant
        if variant == 'outline':
            self.configure(
                highlightbackground=DesignTokens.COLORS['border'],
                highlightcolor=DesignTokens.COLORS['primary'],
                highlightthickness=1,
            )
        
        # Bind events
        self.bind("<Enter>", self.on_hover_enter)
        self.bind("<Leave>", self.on_hover_leave)
        self.bind("<Button-1>", self.on_click)
        
        # Apply corner radius (simulated)
        self._apply_corner_radius()
    
    def on_hover_enter(self, event):
        """Handle hover enter with smooth transition"""
        self.is_hovered = True
        self.configure(bg=self.hover_color)
        if self.variant == 'outline':
            self.configure(highlightbackground=self.active_color)
    
    def on_hover_leave(self, event):
        """Handle hover leave"""
        self.is_hovered = False
        self.configure(bg=self.bg_color)
        if self.variant == 'outline':
            self.configure(highlightbackground=DesignTokens.COLORS['border'])
    
    def on_click(self, event):
        """Handle click with ripple effect simulation"""
        original_bg = self.cget('bg')
        self.configure(bg=self.active_color)
        self.after(100, lambda: self.configure(bg=original_bg))
    
    def _apply_corner_radius(self):
        """Apply rounded corners using tkinter's capabilities"""
        # Note: Full rounded corners require custom drawing or ttk
        pass


class GradientFrame(tk.Canvas):
    """Frame with gradient background effect"""
    
    def __init__(self, parent, color1, color2, direction="horizontal", **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self.color1 = color1
        self.color2 = color2
        self.direction = direction
        self.bind("<Configure>", self._draw_gradient)
    
    def _draw_gradient(self, event=None):
        """Draw gradient background"""
        self.delete("gradient")
        width = self.winfo_width()
        height = self.winfo_height()
        
        if self.direction == "horizontal":
            for i in range(width):
                ratio = i / width
                color = self._interpolate_color(self.color1, self.color2, ratio)
                self.create_line(i, 0, i, height, fill=color, tags="gradient")
        else:
            for i in range(height):
                ratio = i / height
                color = self._interpolate_color(self.color1, self.color2, ratio)
                self.create_line(0, i, width, i, fill=color, tags="gradient")
        
        self.lower("gradient")
    
    def _interpolate_color(self, color1, color2, ratio):
        """Interpolate between two colors"""
        # Convert hex to RGB
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        
        return f"#{r:02x}{g:02x}{b:02x}"


class StatCard(tk.Frame):
    """Enhanced statistic card with animations and micro-interactions"""
    
    def __init__(self, parent, title, value, icon, color, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.title = title
        self.value = value
        self.icon = icon
        self.color = color
        self.animation_progress = 0
        
        self.configure(
            bg=DesignTokens.COLORS['bg-secondary'],
            relief="flat",
            cursor="hand2"
        )
        
        self._build_ui()
        self._bind_hover_effects()
        self._animate_value(0, value)
    
    def _build_ui(self):
        """Build the card UI"""
        # Left accent bar
        self.accent = tk.Frame(self, bg=self.color, width=4)
        self.accent.pack(side="left", fill="y")
        
        # Content container
        self.content = tk.Frame(self, bg=DesignTokens.COLORS['bg-secondary'])
        self.content.pack(side="left", fill="both", expand=True, 
                         padx=DesignTokens.SPACING['4'], 
                         pady=DesignTokens.SPACING['4'])
        
        # Title
        self.title_label = tk.Label(
            self.content,
            text=self.title,
            font=(DesignTokens.TYPOGRAPHY['font-family'], 
                  DesignTokens.TYPOGRAPHY['sizes']['sm']),
            fg=DesignTokens.COLORS['gray-400'],
            bg=DesignTokens.COLORS['bg-secondary']
        )
        self.title_label.pack(anchor="w")
        
        # Value label with animation
        self.value_label = tk.Label(
            self.content,
            text="0",
            font=(DesignTokens.TYPOGRAPHY['font-family'], 
                  DesignTokens.TYPOGRAPHY['sizes']['4xl'],
                  DesignTokens.TYPOGRAPHY['weights']['bold']),
            fg=COLORS["dark_text"],
            bg=COLORS['white2']

        )
        self.value_label.pack(anchor="w", pady=(DesignTokens.SPACING['1'], 0))
        
        # Icon
        self.icon_label = tk.Label(
            self,
            text=self.icon,
            font=("Segoe UI Emoji", 28),
            fg=self.color,
            bg=DesignTokens.COLORS['bg-secondary']
        )
        self.icon_label.pack(side="right", padx=DesignTokens.SPACING['4'])
        
        # Trend indicator (simulated)
        self.trend = tk.Label(
            self.content,
            text="↑ 12%",
            font=(DesignTokens.TYPOGRAPHY['font-family'], 
                  DesignTokens.TYPOGRAPHY['sizes']['xs']),
            fg=DesignTokens.COLORS['success'],
            bg=DesignTokens.COLORS['bg-secondary']
        )
        self.trend.pack(anchor="w", pady=(DesignTokens.SPACING['2'], 0))
    
    def _bind_hover_effects(self):
        """Bind hover animations"""
        def on_enter(e):
            self.configure(bg=COLORS['white2'])
            self.content.configure(bg=COLORS['white2'])
            self.title_label.configure(bg=COLORS['white2'])
            self.value_label.configure(bg=COLORS['white2'])
            self.icon_label.configure(bg=COLORS['white2'])
            self.trend.configure(bg=COLORS['white2'])

            # Scale animation
            self.icon_label.configure(font=("Segoe UI Emoji", 32))
        
        def on_leave(e):
            self.configure(bg=DesignTokens.COLORS['bg-secondary'])
            self.content.configure(bg=DesignTokens.COLORS['bg-secondary'])
            self.title_label.configure(bg=DesignTokens.COLORS['bg-secondary'])
            self.value_label.configure(bg=COLORS['white2'])
            self.icon_label.configure(bg=DesignTokens.COLORS['bg-secondary'])
            self.trend.configure(bg=DesignTokens.COLORS['bg-secondary'])

            self.icon_label.configure(font=("Segoe UI Emoji", 28))
        
        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)
        self.content.bind("<Enter>", on_enter)
        self.content.bind("<Leave>", on_leave)
    
    def _animate_value(self, start, end, step=0):
        """Animate value counting"""
        if step <= 20:
            current = start + (end - start) * (step / 20)
            self.value_label.config(text=f"{int(current):,}")
            self.after(20, lambda: self._animate_value(start, end, step + 1))
        else:
            self.value_label.config(text=f"{end:,}")
    
    def update_value(self, new_value):
        """Update card value with animation"""
        current = int(self.value_label.cget('text').replace(',', ''))
        self._animate_value(current, new_value)


class SearchBar(tk.Frame):
    """Advanced search bar with debouncing and suggestions"""
    
    def __init__(self, parent, on_search, on_clear, **kwargs):
        super().__init__(parent, bg=DesignTokens.COLORS['bg-primary'], **kwargs)
        
        self.on_search = on_search
        self.on_clear = on_clear
        self.search_timer = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Build search bar UI"""
        # Container with border
        self.container = tk.Frame(
            self,
            bg=DesignTokens.COLORS['bg-secondary'],
            relief="flat",
            bd=1,
            highlightbackground=DesignTokens.COLORS['border'],
            highlightthickness=1
        )
        self.container.pack(fill="x")
        
        # Search icon
        self.icon_label = tk.Label(
            self.container,
            text="🔍",
            font=("Segoe UI Emoji", 12),
            fg=DesignTokens.COLORS['gray-400'],
            bg=DesignTokens.COLORS['bg-secondary']
        )
        self.icon_label.pack(side="left", padx=(10, 5), pady=8)
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_text_changed)
        
        self.entry = tk.Entry(
            self.container,
            textvariable=self.search_var,
            font=(DesignTokens.TYPOGRAPHY['font-family'], 
                  DesignTokens.TYPOGRAPHY['sizes']['base']),
            bg=DesignTokens.COLORS['bg-secondary'],
            fg=DesignTokens.COLORS['gray-100'],
            insertbackground=DesignTokens.COLORS['primary'],
            relief="flat",
            bd=0
        )
        self.entry.pack(side="left", fill="x", expand=True, pady=8)
        
        # Clear button
        self.clear_btn = tk.Label(
            self.container,
            text="✕",
            font=("Segoe UI", 10, "bold"),
            fg=DesignTokens.COLORS['gray-500'],
            bg=DesignTokens.COLORS['bg-secondary'],
            cursor="hand2"
        )
        self.clear_btn.pack(side="right", padx=10)
        self.clear_btn.bind("<Button-1>", self.clear_search)
        
        # Search button
        self.search_btn = AnimatedButton(
            self,
            text="Search",
            variant="primary",
            size="sm"
        )
        self.search_btn.pack(side="right", padx=(10, 0))
        self.search_btn.configure(command=self.trigger_search)
        
        # Bind events
        self.entry.bind("<Return>", lambda e: self.trigger_search())
    
    def on_text_changed(self, *args):
        """Handle text change with debouncing"""
        if self.search_timer:
            self.after_cancel(self.search_timer)
        
        text = self.search_var.get()
        if text:
            self.clear_btn.configure(fg=DesignTokens.COLORS['gray-300'])
            self.search_timer = self.after(500, self.trigger_search)
        else:
            self.clear_btn.configure(fg=DesignTokens.COLORS['gray-500'])
    
    def trigger_search(self):
        """Trigger search callback"""
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.on_search(self.search_var.get())
    
    def clear_search(self, event=None):
        """Clear search input"""
        self.search_var.set("")
        self.entry.focus()
        self.on_clear()


class ModernTable(ttk.Treeview):
    """Advanced data table with sorting, filtering, and row animations"""
    
    def __init__(self, parent, columns, **kwargs):
        self.columns = columns
        self.sort_column = None
        self.sort_reverse = False
        self.row_tags = {}
        
        # Configure style
        ModernStyle.configure_treeview_style()
        
        super().__init__(
            parent,
            columns=columns,
            show="headings",
            style="Modern.Treeview",
            **kwargs
        )
        
        self._configure_columns()
        self._bind_events()
    
    def _configure_columns(self):
        """Configure column settings"""
        column_configs = {
            "Name": {"width": 180, "anchor": "w"},
            "Company": {"width": 140, "anchor": "w"},
            "Packing": {"width": 100, "anchor": "center"},
            "Category": {"width": 120, "anchor": "center"},
            "Stock": {"width": 80, "anchor": "center"},
            "Expiry": {"width": 110, "anchor": "center"},
            "Rates": {"width": 150, "anchor": "e"},
            "Value": {"width": 120, "anchor": "e"},
            "Status": {"width": 120, "anchor": "center"},
        }
        
        for col in self.columns:
            config = column_configs.get(col, {"width": 100, "anchor": "center"})
            self.heading(col, text=col, command=lambda c=col: self.sort_by(c))
            self.column(col, width=config["width"], anchor=config["anchor"])
        
        # Configure status colors
        self.tag_configure('critical', background='#450a0a', foreground='#f87171')
        self.tag_configure('warning', background='#422006', foreground='#fbbf24')
        self.tag_configure('normal', background='#052e16', foreground='#4ade80')
        self.tag_configure('hover', background=DesignTokens.COLORS['surface-hover'])
    
    def _bind_events(self):
        """Bind interactive events"""
        self.bind("<Motion>", self.on_hover)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Double-1>", self.on_double_click)
    
    def on_hover(self, event):
        """Handle row hover"""
        item = self.identify_row(event.y)
        if item:
            # Clear previous hover
            for prev in self.tag_has('hover'):
                self.tag_remove('hover', prev)
            self.tag_add('hover', item)
    
    def on_leave(self, event):
        """Handle mouse leave"""
        for item in self.tag_has('hover'):
            self.tag_remove('hover', item)
    
    def on_double_click(self, event):
        """Handle double click on row"""
        item = self.identify_row(event.y)
        if item:
            values = self.item(item)['values']
            # Emit event or trigger callback
            print(f"Selected: {values}")
    
    def sort_by(self, column):
        """Sort table by column"""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
        
        self.sort_column = column
        
        # Get all items
        items = [(self.set(item, column), item) for item in self.get_children('')]
        
        # Sort items
        items.sort(reverse=self.sort_reverse, key=lambda x: x[0].lower())
        
        # Reorder
        for index, (_, item) in enumerate(items):
            self.move(item, '', index)
        
        # Update heading indicators
        for col in self.columns:
            text = col
            if col == column:
                text += ' ↓' if not self.sort_reverse else ' ↑'
            self.heading(col, text=text)
    
    def add_row(self, values, tag='normal'):
        """Add row with animation effect"""
        item = self.insert('', 'end', values=values, tags=(tag,))
        self.see(item)
        return item
    
    def clear_rows(self):
        """Clear all rows"""
        for item in self.get_children():
            self.delete(item)


# ============================================================================
# Main Dashboard Screen
# ============================================================================

class DashboardScreen(tk.Frame):
    """Enhanced dashboard with modern UI/UX"""
    
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=DesignTokens.COLORS['bg-primary'], **kwargs)
        self.app = app_instance
        self.stat_cards = {}
        self.table = None
        self.search_bar = None
        
        self._build_ui()
        self._setup_keyboard_shortcuts()
    
    def _build_ui(self):
        """Build complete dashboard UI"""
        # Header with gradient
        self._build_header()
        
        # Quick action bar
        self._build_action_bar()
        
        # Statistics cards
        self._build_stat_cards()
        
        # Search and filter section
        self._build_search_section()
        
        # Data table
        self._build_data_table()
        
        # Floating action button
        self._build_fab()
    
    def _build_header(self):
        """Build simple header section"""
        header_frame = tk.Frame(self, bg="#f9fafb")
        header_frame.pack(fill="x", pady=(0, DesignTokens.SPACING['6']))
        
        # Title section
        title_container = tk.Frame(header_frame, bg="#f9fafb")
        title_container.pack(side="left", padx=20, pady=20)
        
        self.title_label = tk.Label(
            title_container,
            text="Dashboard",
            font=("Segoe UI", 24, "bold"),
            fg="#111827",
            bg="#f9fafb"
        )
        self.title_label.pack(anchor="w")
        
        self.subtitle_label = tk.Label(
            title_container,
            text="Pharmacy Inventory Management System",
            font=("Segoe UI", 12),
            fg="#6b7280",
            bg="#f9fafb"
        )
        self.subtitle_label.pack(anchor="w", pady=(4, 0))
        
        # Info label showing current FY from navbar
        if hasattr(self.app, 'fy_var') and self.app.fy_var:
            fy_info = tk.Label(
                header_frame,
                text=f"📅 FY: {self.app.fy_var.get()}",
                font=("Segoe UI", 10),
                fg="#6366f1",
                bg="#e0e7ff",
                padx=12,
                pady=6
            )
            fy_info.pack(side="right", padx=20)
    
    def _update_time(self):
        """Update time display"""
        now = datetime.now()
        self.time_label.config(text=now.strftime("%A, %B %d, %Y • %I:%M %p"))
        self.after(1000, self._update_time)
    
    def _build_action_bar(self):
        """Build quick action buttons"""
        action_bar = tk.Frame(self, bg=DesignTokens.COLORS['bg-primary'])
        action_bar.pack(fill="x", pady=(0, DesignTokens.SPACING['6']))
        
        actions = [
            ("🔄 Update Stock", "warning", self.update_stock),
            ("📊 Batch Report", "info", self.batch_report),
            ("🗑️ Clear Cache", "secondary", self.clear_cache),
            ("📈 Analytics", "primary", self.show_analytics),
        ]
        
        for text, variant, command in actions:
            btn = AnimatedButton(
                action_bar,
                text=text,
                variant=variant,
                size="sm",
                command=command
            )
            btn.pack(side="left", padx=DesignTokens.SPACING['1'])
        
        # Export buttons on the right
        export_frame = tk.Frame(action_bar, bg=DesignTokens.COLORS['bg-primary'])
        export_frame.pack(side="right")
        
        export_actions = [
            ("📊 Excel", "success", self.export_excel),
            ("📄 PDF", "danger", self.export_pdf),
        ]
        
        for text, variant, command in export_actions:
            btn = AnimatedButton(
                export_frame,
                text=text,
                variant=variant,
                size="sm",
                command=command
            )
            btn.pack(side="left", padx=DesignTokens.SPACING['1'])
    
    def _build_stat_cards(self):
        """Build statistics cards with animations"""
        cards_frame = tk.Frame(self, bg=DesignTokens.COLORS['bg-primary'])
        cards_frame.pack(fill="x", pady=(0, DesignTokens.SPACING['6']))
        
        # Configure grid
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1)
        
        stats = [
            ("Total Products", 0, "💊", DesignTokens.COLORS['primary']),
            ("Inventory Value", 0, "💰", DesignTokens.COLORS['success']),
            ("Low Stock Items", 0, "⚠️", DesignTokens.COLORS['warning']),
            ("Out of Stock", 0, "🚫", DesignTokens.COLORS['error']),
        ]
        
        for i, (title, value, icon, color) in enumerate(stats):
            card = StatCard(
                cards_frame,
                title=title,
                value=value,
                icon=icon,
                color=color
            )
            card.grid(row=0, column=i, padx=DesignTokens.SPACING['2'], 
                     pady=DesignTokens.SPACING['2'], sticky="nsew")
            self.stat_cards[title.lower()] = card
    
    def _build_search_section(self):
        """Build search and filter section"""
        search_container = tk.Frame(self, bg=DesignTokens.COLORS['bg-primary'])
        search_container.pack(fill="x", pady=(0, DesignTokens.SPACING['4']))
        
        # Search bar
        self.search_bar = SearchBar(
            search_container,
            on_search=self.perform_search,
            on_clear=self.reset_search
        )
        self.search_bar.pack(side="left", expand=True, fill="x",
                            padx=(0, DesignTokens.SPACING['4']))
        
        # Filter dropdown
        filter_frame = tk.Frame(search_container, bg=DesignTokens.COLORS['bg-primary'])
        filter_frame.pack(side="right")
        
        tk.Label(
            filter_frame,
            text="Filter by:",
            font=(DesignTokens.TYPOGRAPHY['font-family'], 
                  DesignTokens.TYPOGRAPHY['sizes']['sm']),
            fg=DesignTokens.COLORS['gray-400'],
            bg=DesignTokens.COLORS['bg-primary']
        ).pack(side="left", padx=(0, DesignTokens.SPACING['2']))
        
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_var,
            values=["All", "Low Stock", "Out of Stock", "Expiring Soon"],
            state="readonly",
            width=15
        )
        filter_combo.pack(side="left")
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filter())
    
    def _build_data_table(self):
        """Build enhanced data table"""
        table_container = tk.Frame(self, bg=DesignTokens.COLORS['bg-primary'])
        table_container.pack(fill="both", expand=True)
        
        # Create scrollbars
        v_scrollbar = ttk.Scrollbar(table_container, orient="vertical")
        h_scrollbar = ttk.Scrollbar(table_container, orient="horizontal")
        
        # Create table
        columns = ["Name", "Company", "Packing", "Category", "Stock", 
                  "Expiry", "Rates", "Value", "Status"]
        
        self.table = ModernTable(
            table_container,
            columns=columns,
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        
        # Configure scrollbars
        v_scrollbar.config(command=self.table.yview)
        h_scrollbar.config(command=self.table.xview)
        
        # Layout
        self.table.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
    
    def _build_fab(self):
        """Build floating action button"""
        self.fab = tk.Button(
            self,
            text="➕",
            font=("Segoe UI", 20),
            bg=DesignTokens.COLORS['primary'],
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=self.add_new_product
        )
        self.fab.place(relx=0.95, rely=0.9, anchor="se",
                      width=60, height=60)
        
        # Add hover effect
        def on_enter(e):
            self.fab.configure(bg=DesignTokens.COLORS['primary-dark'])
            self.fab.configure(font=("Segoe UI", 22))
        
        def on_leave(e):
            self.fab.configure(bg=DesignTokens.COLORS['primary'])
            self.fab.configure(font=("Segoe UI", 20))
        
        self.fab.bind("<Enter>", on_enter)
        self.fab.bind("<Leave>", on_leave)
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        def on_f1(event):
            if self.search_bar and self.search_bar.entry:
                self.search_bar.entry.focus()
        
        def on_f5(event):
            self.refresh_data()
        
        def on_escape(event):
            if self.search_bar:
                self.search_bar.clear_search()
        
        self.bind("<F1>", on_f1)
        self.bind("<F5>", on_f5)
        self.bind("<Escape>", on_escape)
        
        # Note: Ctrl+B for FY dropdown is handled globally in shortcuts.py
    
    def _setup_fy_shortcuts(self):
        """Financial Year shortcut info - handled globally by shortcuts.py"""
        # Ctrl+B binding is handled in shortcuts.py _dispatch function
        # This ensures it works properly with the global shortcut system
        print("Dashboard: FY shortcuts ready (Ctrl+B handled globally)")
    
    def perform_search(self, query):
        """Perform search with animation"""
        self.refresh_data(query)
    
    def reset_search(self):
        """Reset search and refresh"""
        self.refresh_data()
    
    def apply_filter(self):
        """Apply filter to table data"""
        filter_type = self.filter_var.get()
        if filter_type != "All":
            # Filter logic here
            pass
    
    def refresh_data(self, search_query=""):
        """Refresh dashboard data with animations"""
        try:
            # Get financial year filter from NAVBAR (app level)
            if hasattr(self.app, 'current_fy_start') and self.app.current_fy_start:
                fy_start = self.app.current_fy_start
                fy_end = self.app.current_fy_end
                print(f"[DASHBOARD] Using navbar FY: {fy_start} to {fy_end}")
            else:
                # Fallback to own FY dropdown
                fy_start, fy_end = self.get_financial_year_filter()
                print(f"[DASHBOARD] Using own FY: {fy_start} to {fy_end}")
            
            # Fetch dashboard stats with FY filter
            data = self.app.db.fetch_dashboard(fy_start, fy_end)
            print(f"[DASHBOARD] Data fetched: {data}")
            
            self.stat_cards['total products'].update_value(data.get("products", 0))
            self.stat_cards['inventory value'].update_value(data.get("value", 0))
            self.stat_cards['low stock items'].update_value(data.get("low_stock", 0))
            self.stat_cards['out of stock'].update_value(data.get("out_stock", 0))
            
            # Fetch and display inventory
            rows = self.app.db.fetch_inventory(search_query)
            self.table.clear_rows()
            
            for row in rows:
                status = row.get("status", "")
                if status == "low_stock":
                    tag = "warning"
                elif status == "out_stock":
                    tag = "critical"
                else:
                    tag = "normal"
                
                self.table.add_row((
                    row.get("name", ""),
                    row.get("company", ""),
                    row.get("packing", ""),
                    row.get("category", ""),
                    row.get("stock", ""),
                    row.get("expiry", ""),
                    row.get("rates", ""),
                    row.get("value", ""),
                    status
                ), tag)
        
        except Exception as e:
            print(f"Error refreshing data: {e}")
            import traceback
            traceback.print_exc()
    
    # Action methods
    def update_stock(self):
        """Update stock action"""
        print("Update stock clicked")
    
    def batch_report(self):
        """Generate batch report"""
        print("Batch report clicked")
    
    def clear_cache(self):
        """Clear cache"""
        print("Cache cleared")
    
    def show_analytics(self):
        """Show analytics dashboard"""
        print("Analytics clicked")
    
    def export_excel(self):
        """Export to Excel"""
        print("Exporting to Excel...")
    
    def export_pdf(self):
        """Export to PDF"""
        print("Exporting to PDF...")
    
    def add_new_product(self):
        """Add new product"""
        print("Add new product clicked")
    
    def on_show(self):
        """Public method to refresh data"""
        self.refresh_data()
    
    def _generate_financial_years(self):
        """Generate financial year options from 2012-13 to current year"""
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # If current month is before April, financial year hasn't started yet
        if current_month < 4:
            end_year = current_year
        else:
            end_year = current_year + 1
        
        fy_list = []
        for year in range(2012, end_year):
            fy_list.append(f"{year}-{year+1}")
        
        return list(reversed(fy_list))  # Latest first
    
    def _get_current_financial_year(self):
        """Get current financial year"""
        now = datetime.now()
        if now.month >= 4:
            return f"{now.year}-{now.year+1}"
        else:
            return f"{now.year-1}-{now.year}"
    
    def _set_current_fy_dates(self):
        """Set start and end dates for selected financial year"""
        if self.fy_var is None:
            return
        fy = self.fy_var.get()
        if '-' in fy:
            start_year, end_year = fy.split('-')
            self.current_fy_start = f"{start_year}-04-01"
            self.current_fy_end = f"{end_year}-03-31"
    
    def _on_fy_change(self, event=None):
        """Handle financial year change"""
        self._set_current_fy_dates()
        self.refresh_data()
    
    def get_financial_year_filter(self):
        """Get current financial year date range for SQL queries"""
        return self.current_fy_start, self.current_fy_end