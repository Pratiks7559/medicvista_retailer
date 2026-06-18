from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# ============================================================================
# Design System
# ============================================================================

class ColorScheme(Enum):
    """Modern color scheme with light/dark mode support"""
    PRIMARY = "#6366f1"      # Indigo
    PRIMARY_DARK = "#4f46e5"
    PRIMARY_LIGHT = "#818cf8"
    SECONDARY = "#8b5cf6"    # Purple
    SUCCESS = "#10b981"      # Emerald
    WARNING = "#f59e0b"      # Amber
    DANGER = "#ef4444"       # Red
    INFO = "#3b82f6"         # Blue
    
    # Neutrals
    WHITE = "#ffffff"
    GRAY_50 = "#f9fafb"
    GRAY_100 = "#f3f4f6"
    GRAY_200 = "#e5e7eb"
    GRAY_300 = "#d1d5db"
    GRAY_400 = "#9ca3af"
    GRAY_500 = "#6b7280"
    GRAY_600 = "#4b5563"
    GRAY_700 = "#374151"
    GRAY_800 = "#1f2937"
    GRAY_900 = "#111827"
    
    # Semantic aliases
    BACKGROUND = GRAY_50
    SURFACE = WHITE
    BORDER = GRAY_200
    TEXT_PRIMARY = GRAY_900
    TEXT_SECONDARY = GRAY_600
    TEXT_MUTED = GRAY_500
    
    @classmethod
    def get_status_color(cls, status: str) -> str:
        """Get color based on status string"""
        status_map = {
            # Positive statuses
            'paid': cls.SUCCESS.value,
            'in_stock': cls.SUCCESS.value,
            'active': cls.SUCCESS.value,
            'completed': cls.SUCCESS.value,
            
            # Warning statuses
            'pending': cls.WARNING.value,
            'partial': cls.WARNING.value,
            'low_stock': cls.WARNING.value,
            'expiring': cls.WARNING.value,
            
            # Negative statuses
            'overdue': cls.DANGER.value,
            'out_of_stock': cls.DANGER.value,
            'expired': cls.DANGER.value,
            'failed': cls.DANGER.value,
        }
        return status_map.get(status.lower(), cls.TEXT_SECONDARY.value)


@dataclass(frozen=True)
class Typography:
    """Typography system with responsive font sizes"""
    FAMILY = "Inter, Segoe UI, Helvetica Neue, Arial"
    MONO_FAMILY = "JetBrains Mono, Consolas, Courier New"
    
    # Scale using major second ratio (1.125)
    XS = (FAMILY, 10)
    SM = (FAMILY, 11)
    BASE = (FAMILY, 12)
    LG = (FAMILY, 14)
    XL = (FAMILY, 16)
    XXL = (FAMILY, 18)
    XXXL = (FAMILY, 20, "bold")
    
    # Semantic variants
    H1 = (FAMILY, 28, "bold")
    H2 = (FAMILY, 24, "bold")
    H3 = (FAMILY, 20, "bold")
    H4 = (FAMILY, 18, "bold")
    BODY = BASE
    CAPTION = SM
    BUTTON = (FAMILY, 12, "bold")
    LABEL = SM
    CODE = (MONO_FAMILY, 11)


class Spacing:
    """Consistent spacing system (8px grid)"""
    XXS = 2
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32
    XXXL = 48
    
    # Semantic spacing
    CARD_PADDING = LG
    SECTION_GAP = XL
    ELEMENT_GAP = SM
    BUTTON_PADDING_H = LG
    BUTTON_PADDING_V = XS
    INPUT_HEIGHT = 36


class Elevation:
    """Shadow system for depth"""
    NONE = ""
    SM = "0 1px 2px 0 rgb(0 0 0 / 0.05)"
    MD = "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)"
    LG = "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)"
    XL = "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)"


# ============================================================================
# Enhanced UI Components
# ============================================================================

class ModernButton(tk.Button):
    """Modern button with animations and multiple variants"""
    
    class Variant(Enum):
        PRIMARY = "primary"
        SECONDARY = "secondary"
        SUCCESS = "success"
        DANGER = "danger"
        WARNING = "warning"
        INFO = "info"
        OUTLINE = "outline"
        GHOST = "ghost"
    
    def __init__(
        self,
        parent,
        text: str = "",
        variant: Union[Variant, str] = Variant.PRIMARY,
        command: Optional[Callable] = None,
        size: str = "md",
        full_width: bool = False,
        icon: Optional[str] = None,
        **kwargs
    ):
        self.variant = variant if isinstance(variant, self.Variant) else self.Variant(variant)
        self.size = size
        self.full_width = full_width
        
        # Configure colors based on variant
        self._configure_colors()
        
        super().__init__(
            parent,
            text=text,
            command=command,
            font=self._get_font(),
            cursor="hand2",
            relief="flat",
            bd=0,
            **self._get_style_kwargs(),
            **kwargs
        )
        
        self._setup_hover_effects()
        self._setup_keyboard_bindings()
        
        if full_width:
            self.pack(fill=X, padx=Spacing.SM, pady=Spacing.XS)
    
    def _configure_colors(self):
        """Set colors based on variant"""
        colors = {
            self.Variant.PRIMARY: (ColorScheme.PRIMARY.value, ColorScheme.PRIMARY_DARK.value),
            self.Variant.SECONDARY: (ColorScheme.SECONDARY.value, ColorScheme.PRIMARY_DARK.value),
            self.Variant.SUCCESS: (ColorScheme.SUCCESS.value, "#0e9f6e"),
            self.Variant.DANGER: (ColorScheme.DANGER.value, "#dc2626"),
            self.Variant.WARNING: (ColorScheme.WARNING.value, "#d97706"),
            self.Variant.INFO: (ColorScheme.INFO.value, "#2563eb"),
            self.Variant.OUTLINE: (ColorScheme.WHITE.value, ColorScheme.GRAY_100.value),
            self.Variant.GHOST: ("transparent", ColorScheme.GRAY_100.value),
        }
        
        self.bg_color, self.hover_color = colors.get(self.variant, colors[self.Variant.PRIMARY])
        self.fg_color = ColorScheme.TEXT_PRIMARY.value if self.variant in [self.Variant.OUTLINE, self.Variant.GHOST] else ColorScheme.WHITE.value
        self.active_color = self.hover_color
    
    def _get_style_kwargs(self) -> dict:
        """Get style-specific keyword arguments"""
        base_kwargs = {
            "bg": self.bg_color,
            "fg": self.fg_color,
            "activebackground": self.hover_color,
            "activeforeground": self.fg_color,
        }
        
        if self.variant == self.Variant.OUTLINE:
            base_kwargs.update({
                "highlightbackground": ColorScheme.BORDER.value,
                "highlightcolor": self.bg_color,
                "highlightthickness": 1,
            })
        
        return base_kwargs
    
    def _get_font(self):
        """Get font based on size"""
        sizes = {
            "sm": Typography.SM,
            "md": Typography.BUTTON,
            "lg": Typography.LG,
        }
        return sizes.get(self.size, Typography.BUTTON)
    
    def _setup_hover_effects(self):
        """Add hover animation effects"""
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        """Handle mouse enter"""
        self.config(bg=self.hover_color)
        if self.variant == self.Variant.OUTLINE:
            self.config(bg=self.hover_color, fg=ColorScheme.WHITE.value)
    
    def _on_leave(self, event):
        """Handle mouse leave"""
        self.config(bg=self.bg_color)
        if self.variant == self.Variant.OUTLINE:
            self.config(bg=self.bg_color, fg=self.fg_color)
    
    def _setup_keyboard_bindings(self):
        """Enable keyboard activation"""
        self.bind("<space>", lambda e: self.invoke())
        self.bind("<Return>", lambda e: self.invoke())


class ModernCard(tk.Frame):
    """Card component with elevation and rounded corners"""
    
    def __init__(
        self,
        parent,
        padding: int = Spacing.LG,
        elevation: str = Elevation.MD,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.configure(
            bg=ColorScheme.SURFACE.value,
            relief="flat",
            bd=0
        )
        
        self.padding = padding
        self._apply_elevation(elevation)
        
        # Inner container for content
        self.content = tk.Frame(self, bg=ColorScheme.SURFACE.value)
        self.content.pack(fill=BOTH, expand=True, padx=padding, pady=padding)
    
    def _apply_elevation(self, elevation: str):
        """Apply shadow effect (simulated with borders for tkinter)"""
        if elevation != Elevation.NONE:
            # Simulate shadow with subtle border
            self.configure(
                highlightbackground=ColorScheme.BORDER.value,
                highlightcolor=ColorScheme.BORDER.value,
                highlightthickness=1
            )


class ModernEntry(tk.Frame):
    """Enhanced entry with label, validation, and error states"""
    
    def __init__(
        self,
        parent,
        label: str = "",
        textvariable: Optional[tk.Variable] = None,
        placeholder: str = "",
        validator: Optional[Callable] = None,
        error_message: str = "",
        **kwargs
    ):
        super().__init__(parent, bg=ColorScheme.BACKGROUND.value)
        
        self.validator = validator
        self.error_message = error_message
        
        # Label
        if label:
            self.label = tk.Label(
                self,
                text=label,
                font=Typography.LABEL,
                fg=ColorScheme.TEXT_SECONDARY.value,
                bg=ColorScheme.BACKGROUND.value
            )
            self.label.pack(anchor=W, pady=(0, Spacing.XS))
        
        # Entry
        self.entry = tb.Entry(
            self,
            textvariable=textvariable,
            font=Typography.BASE,
            bootstyle="light"
        )
        self.entry.pack(fill=X, ipady=Spacing.XS)
        
        # Placeholder handling
        if placeholder:
            self._setup_placeholder(placeholder)
        
        # Error label
        self.error_label = tk.Label(
            self,
            text="",
            font=Typography.CAPTION,
            fg=ColorScheme.DANGER.value,
            bg=ColorScheme.BACKGROUND.value
        )
        
        # Bind validation
        if validator:
            self.entry.bind("<FocusOut>", self._validate)
            self.entry.bind("<KeyRelease>", lambda e: self.clear_error())
    
    def _setup_placeholder(self, placeholder: str):
        """Add placeholder text functionality"""
        self.placeholder = placeholder
        self.entry.insert(0, placeholder)
        self.entry.config(fg=ColorScheme.GRAY_400.value)
        
        def on_focus_in(event):
            if self.entry.get() == placeholder:
                self.entry.delete(0, END)
                self.entry.config(fg=ColorScheme.TEXT_PRIMARY.value)
        
        def on_focus_out(event):
            if not self.entry.get():
                self.entry.insert(0, placeholder)
                self.entry.config(fg=ColorScheme.GRAY_400.value)
        
        self.entry.bind("<FocusIn>", on_focus_in)
        self.entry.bind("<FocusOut>", on_focus_out)
    
    def _validate(self, event=None):
        """Validate entry content"""
        if self.validator and not self.validator(self.get()):
            self.show_error()
            return False
        return True
    
    def show_error(self):
        """Show error message"""
        self.error_label.config(text=self.error_message)
        self.error_label.pack(anchor=W, pady=(Spacing.XS, 0))
        self.entry.config(bootstyle="danger")
    
    def clear_error(self):
        """Clear error state"""
        self.error_label.pack_forget()
        self.entry.config(bootstyle="light")
    
    def get(self) -> str:
        """Get entry value"""
        value = self.entry.get()
        if hasattr(self, 'placeholder') and value == self.placeholder:
            return ""
        return value
    
    def set(self, value: str):
        """Set entry value"""
        self.entry.delete(0, END)
        self.entry.insert(0, value)
        self.entry.config(fg=ColorScheme.TEXT_PRIMARY.value)


class ModernBadge(tk.Label):
    """Badge component for status indicators"""
    
    def __init__(
        self,
        parent,
        text: str,
        variant: str = "default",
        **kwargs
    ):
        colors = {
            "default": (ColorScheme.GRAY_100.value, ColorScheme.GRAY_700.value),
            "primary": (ColorScheme.PRIMARY.value, ColorScheme.WHITE.value),
            "success": (ColorScheme.SUCCESS.value, ColorScheme.WHITE.value),
            "warning": (ColorScheme.WARNING.value, ColorScheme.WHITE.value),
            "danger": (ColorScheme.DANGER.value, ColorScheme.WHITE.value),
            "info": (ColorScheme.INFO.value, ColorScheme.WHITE.value),
        }
        
        bg_color, fg_color = colors.get(variant, colors["default"])
        
        super().__init__(
            parent,
            text=text,
            font=Typography.CAPTION,
            bg=bg_color,
            fg=fg_color,
            padx=Spacing.SM,
            pady=Spacing.XXS,
            **kwargs
        )
        
        # Rounded corners effect
        self.configure(relief="flat")


class DataTable(ttk.Treeview):
    """Enhanced data table with sorting and styling"""
    
    def __init__(self, parent, columns: list, **kwargs):
        super().__init__(
            parent,
            columns=columns,
            show="headings",
            selectmode="browse",
            **kwargs
        )
        
        self._setup_styling()
        self._setup_sorting()
        
        # Configure columns
        for col in columns:
            self.heading(col, text=col.title(), command=lambda c=col: self._sort_by(c))
            self.column(col, width=100, anchor=W)
    
    def _setup_styling(self):
        """Apply modern styling to table"""
        style = ttk.Style()
        style.configure(
            "Custom.Treeview",
            background=ColorScheme.WHITE.value,
            foreground=ColorScheme.TEXT_PRIMARY.value,
            rowheight=Spacing.XL,
            fieldbackground=ColorScheme.WHITE.value,
            font=Typography.BASE
        )
        style.configure(
            "Custom.Treeview.Heading",
            background=ColorScheme.GRAY_50.value,
            foreground=ColorScheme.TEXT_SECONDARY.value,
            font=Typography.LABEL,
            relief="flat"
        )
        style.map(
            "Custom.Treeview",
            background=[("selected", ColorScheme.PRIMARY.value)],
            foreground=[("selected", ColorScheme.WHITE.value)]
        )
        
        self.configure(style="Custom.Treeview")
        
        # Add hover effect
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", self._on_leave)
    
    def _setup_sorting(self):
        """Setup column sorting"""
        self.sort_column = None
        self.sort_reverse = False
    
    def _sort_by(self, column: str):
        """Sort table by column"""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
        
        self.sort_column = column
        
        # Get all items
        items = [(self.set(item, column), item) for item in self.get_children("")]
        
        # Sort items
        items.sort(reverse=self.sort_reverse, key=lambda x: x[0].lower())
        
        # Reorder
        for index, (_, item) in enumerate(items):
            self.move(item, "", index)
        
        # Update heading indicator
        for col in self["columns"]:
            text = col.title()
            if col == column:
                text += " ↓" if not self.sort_reverse else " ↑"
            self.heading(col, text=text)
    
    def _on_motion(self, event):
        """Highlight row on hover"""
        item = self.identify_row(event.y)
        if item:
            self.tk.call(self._w, "tag", "configure", "hover", background=ColorScheme.GRAY_100.value)
            self.tag_configure("hover", background=ColorScheme.GRAY_100.value)
            # Remove previous hover
            for existing in self.tag_has("hover"):
                self.tag_remove("hover", existing)
            self.tag_add("hover", item)
    
    def _on_leave(self, event):
        """Remove hover highlight"""
        for item in self.tag_has("hover"):
            self.tag_remove("hover", item)


class Toast:
    """Toast notification system"""
    
    def __init__(self, parent):
        self.parent = parent
        self.active_toasts = []
    
    def show(
        self,
        message: str,
        variant: str = "info",
        duration: int = 3000
    ):
        """Show a toast notification"""
        colors = {
            "success": ColorScheme.SUCCESS.value,
            "error": ColorScheme.DANGER.value,
            "warning": ColorScheme.WARNING.value,
            "info": ColorScheme.INFO.value,
        }
        
        toast = tk.Toplevel(self.parent)
        toast.title("")
        toast.configure(bg=colors.get(variant, ColorScheme.GRAY_700.value))
        
        # Remove window decorations
        toast.overrideredirect(True)
        
        # Position at bottom right
        toast.update_idletasks()
        x = self.parent.winfo_x() + self.parent.winfo_width() - toast.winfo_width() - Spacing.LG
        y = self.parent.winfo_y() + self.parent.winfo_height() - toast.winfo_height() - Spacing.LG - (len(self.active_toasts) * 60)
        toast.geometry(f"+{x}+{y}")
        
        # Content
        label = tk.Label(
            toast,
            text=message,
            font=Typography.BASE,
            bg=colors.get(variant, ColorScheme.GRAY_700.value),
            fg=ColorScheme.WHITE.value,
            padx=Spacing.LG,
            pady=Spacing.SM
        )
        label.pack()
        
        # Auto-destroy
        toast.after(duration, lambda: self._destroy_toast(toast))
        self.active_toasts.append(toast)
    
    def _destroy_toast(self, toast):
        """Remove toast and reposition others"""
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
            toast.destroy()
            self._reposition_toasts()
    
    def _reposition_toasts(self):
        """Reposition remaining toasts"""
        for i, toast in enumerate(self.active_toasts):
            toast.update_idletasks()
            x = self.parent.winfo_x() + self.parent.winfo_width() - toast.winfo_width() - Spacing.LG
            y = self.parent.winfo_y() + self.parent.winfo_height() - toast.winfo_height() - Spacing.LG - (i * 60)
            toast.geometry(f"+{x}+{y}")


# ============================================================================
# Backward-compatibility shims — imported by application.py and other modules
# ============================================================================

COLORS = {
    "purple":             ColorScheme.PRIMARY.value,
    "purple_dark":        ColorScheme.PRIMARY_DARK.value,
    "purple_hover":       ColorScheme.PRIMARY_LIGHT.value,
    "purple_sep":         "#334155",
    "green":              ColorScheme.SUCCESS.value,
    "green_dark":         "#16a34a",
    "orange":             ColorScheme.WARNING.value,
    "orange_dark":        "#d97706",
    "red":                ColorScheme.DANGER.value,
    "red_dark":           "#dc2626",
    "blue_badge":         ColorScheme.INFO.value,
    "blue_dark":          "#2563eb",
    "teal":               "#14b8a6",
    "bg_light":           ColorScheme.GRAY_50.value,
    "white":              ColorScheme.WHITE.value,
    "white2":             ColorScheme.GRAY_100.value,
    "heading_bg":         ColorScheme.GRAY_200.value,
    "border_color":       ColorScheme.GRAY_300.value,
    "input_bg":           ColorScheme.WHITE.value,
    "row_odd":            ColorScheme.WHITE.value,
    "row_even":           ColorScheme.GRAY_50.value,
    "row_hover":          ColorScheme.GRAY_200.value,
    "focus_ring":         "#c7d2fe",
    "dark_text":          ColorScheme.GRAY_900.value,
    "gray_text":          ColorScheme.GRAY_600.value,
    "muted":              ColorScheme.GRAY_500.value,
    "navbar_bg":          ColorScheme.WHITE.value,
    "navbar_bg_start":    ColorScheme.WHITE.value,
    "navbar_text":        ColorScheme.GRAY_900.value,
    "sidebar_bg":         ColorScheme.GRAY_50.value,
    "sidebar_bg_start":   ColorScheme.GRAY_50.value,
    "sidebar_text":       ColorScheme.GRAY_900.value,
    "sidebar_text_muted": ColorScheme.GRAY_500.value,
    "sidebar_muted":      ColorScheme.GRAY_500.value,
    "green_btn":          ColorScheme.SUCCESS.value,
    "orange_btn":         ColorScheme.WARNING.value,
    "logout_red":         "#7f1d1d",
    "logout_red_h":       "#991b1b",
}

FONT = {
    "base":  Typography.BASE,
    "sm":    Typography.SM,
    "lg":    Typography.LG,
    "xl":    Typography.XL,
    "h1":    Typography.H1,
    "h2":    Typography.H2,
    "h3":    Typography.H3,
    "mono":  Typography.CODE,
    "label": Typography.LABEL,
    "bold":  ("Segoe UI", 10, "bold"),
}

BTN = {
    "primary":   {"bg": COLORS["purple"],     "hover": COLORS["purple_hover"]},
    "success":   {"bg": COLORS["green"],      "hover": COLORS["green_dark"]},
    "danger":    {"bg": COLORS["red"],        "hover": COLORS["red_dark"]},
    "warning":   {"bg": COLORS["orange"],     "hover": COLORS["orange_dark"]},
    "info":      {"bg": COLORS["blue_badge"], "hover": COLORS["blue_dark"]},
    "secondary": {"bg": COLORS["gray_text"],  "hover": COLORS["muted"]},
    "teal":      {"bg": COLORS["teal"],       "hover": "#0f9488"},
}


def make_button(parent, text, variant="primary", command=None,
                padx=14, pady=6, width=None, font=None, **kwargs) -> tk.Button:
    cfg = BTN.get(variant, BTN["primary"])
    f = font or FONT["base"]
    kw = dict(text=text, bg=cfg["bg"], fg="white", font=f,
              bd=0, relief="flat", padx=padx, pady=pady,
              activebackground=cfg["hover"], activeforeground="white",
              cursor="hand2")
    if width:
        kw["width"] = width
    kw.update(kwargs)
    if command:
        kw["command"] = command
    btn = tk.Button(parent, **kw)
    btn.bind("<Enter>", lambda e: btn.config(bg=cfg["hover"]))
    btn.bind("<Leave>", lambda e: btn.config(bg=cfg["bg"]))
    btn.bind("<space>", lambda e: btn.invoke())
    return btn


def make_entry(parent, textvariable=None, width=24, **kwargs) -> tk.Entry:
    return tk.Entry(parent, textvariable=textvariable, font=FONT["base"],
                    width=width, relief="solid", bd=1,
                    bg=COLORS["input_bg"], fg=COLORS["dark_text"],
                    insertbackground=COLORS["dark_text"],
                    highlightthickness=2,
                    highlightbackground=COLORS["border_color"],
                    highlightcolor=COLORS["focus_ring"],
                    **kwargs)


def make_label(parent, text="", variant="normal", **kwargs) -> tk.Label:
    variants = {
        "normal":  {"font": FONT["base"],  "fg": COLORS["dark_text"]},
        "muted":   {"font": FONT["sm"],    "fg": COLORS["gray_text"]},
        "heading": {"font": FONT["h2"],    "fg": COLORS["dark_text"]},
        "h3":      {"font": FONT["h3"],    "fg": COLORS["dark_text"]},
        "success": {"font": FONT["bold"],  "fg": COLORS["green"]},
        "danger":  {"font": FONT["bold"],  "fg": COLORS["red"]},
        "warning": {"font": FONT["bold"],  "fg": COLORS["orange"]},
        "badge":   {"font": FONT["sm"],    "fg": COLORS["purple"]},
    }
    cfg = variants.get(variant, variants["normal"])
    cfg.update(kwargs)
    return tk.Label(parent, text=text, bg=kwargs.get("bg", COLORS["bg_light"]), **{
        k: v for k, v in cfg.items() if k != "bg"
    })


def status_color(status: str) -> str:
    return ColorScheme.get_status_color(status)


def apply_style(root: tk.Tk):
    style = tb.Style(theme="litera")
    style.configure(".", font=FONT["base"],
                    background=COLORS["bg_light"],
                    foreground=COLORS["dark_text"])
    style.configure("TFrame", background=COLORS["bg_light"])
    style.configure("Card.TFrame", background=COLORS["white"])
    style.configure("TLabel",
                    background=COLORS["bg_light"],
                    foreground=COLORS["dark_text"],
                    font=FONT["base"])
    style.configure("Treeview",
                    rowheight=30,
                    font=FONT["base"],
                    background=COLORS["white"],
                    fieldbackground=COLORS["white"],
                    foreground=COLORS["dark_text"],
                    bordercolor=COLORS["border_color"],
                    relief="flat")
    style.configure("Treeview.Heading",
                    font=FONT["bold"],
                    background=COLORS["white2"],
                    foreground=COLORS["dark_text"],
                    relief="flat",
                    padding=(10, 8))
    style.map("Treeview",
              background=[("selected", COLORS["purple"])],
              foreground=[("selected", "white")])
    style.configure("TEntry",
                    fieldbackground=COLORS["input_bg"],
                    foreground=COLORS["dark_text"],
                    insertcolor=COLORS["dark_text"],
                    bordercolor=COLORS["border_color"],
                    lightcolor=COLORS["focus_ring"],
                    darkcolor=COLORS["border_color"])
    style.map("TEntry",
              bordercolor=[("focus", COLORS["focus_ring"])],
              lightcolor=[("focus", COLORS["focus_ring"])])
    style.configure("TCombobox",
                    fieldbackground=COLORS["input_bg"],
                    foreground=COLORS["dark_text"],
                    selectbackground=COLORS["purple"],
                    arrowcolor=COLORS["gray_text"])
    style.map("TCombobox",
              fieldbackground=[("readonly", COLORS["input_bg"])],
              foreground=[("readonly", COLORS["dark_text"])],
              bordercolor=[("focus", COLORS["focus_ring"])])
    style.configure("TScrollbar",
                    background=COLORS["border_color"],
                    troughcolor=COLORS["bg_light"],
                    arrowcolor=COLORS["gray_text"])
    style.configure("TSeparator", background=COLORS["border_color"])
    return style


# ============================================================================
# Main Application Class
# ============================================================================

class ModernApplication:
    """Base application class with modern theming and components"""
    
    def __init__(self, title: str = "Modern Application", size: str = "1200x800"):
        self.root = tb.Window(themename="litera")
        self.root.title(title)
        self.root.geometry(size)
        self.root.configure(bg=ColorScheme.BACKGROUND.value)
        
        # Initialize components
        self.toast = Toast(self.root)
        
        # Apply global styling
        self._apply_global_styling()
        
        # Create main container
        self.main_container = tk.Frame(self.root, bg=ColorScheme.BACKGROUND.value)
        self.main_container.pack(fill=BOTH, expand=True)
    
    def _apply_global_styling(self):
        """Apply global styles to all widgets"""
        style = ttk.Style()
        style.theme_use("litera")
        
        # Configure ttk widgets
        style.configure("TFrame", background=ColorScheme.BACKGROUND.value)
        style.configure("TLabel", background=ColorScheme.BACKGROUND.value, font=Typography.BASE)
        style.configure("TButton", font=Typography.BUTTON)
    
    def create_header(self, title: str, subtitle: str = "") -> tk.Frame:
        """Create a modern header section"""
        header = tk.Frame(self.main_container, bg=ColorScheme.WHITE.value, height=80)
        header.pack(fill=X, pady=(0, Spacing.LG))
        header.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header,
            text=title,
            font=Typography.H2,
            fg=ColorScheme.TEXT_PRIMARY.value,
            bg=ColorScheme.WHITE.value
        )
        title_label.pack(side=LEFT, padx=Spacing.XL, pady=Spacing.LG)
        
        # Subtitle
        if subtitle:
            subtitle_label = tk.Label(
                header,
                text=subtitle,
                font=Typography.CAPTION,
                fg=ColorScheme.TEXT_MUTED.value,
                bg=ColorScheme.WHITE.value
            )
            subtitle_label.pack(side=LEFT, padx=(0, Spacing.XL))
        
        return header
    
    def create_sidebar(self, width: int = 250) -> tk.Frame:
        """Create a sidebar navigation panel"""
        sidebar = tk.Frame(
            self.main_container,
            bg=ColorScheme.GRAY_50.value,
            width=width,
            relief="flat",
            bd=0
        )
        sidebar.pack(side=LEFT, fill=Y, padx=(0, Spacing.LG))
        sidebar.pack_propagate(False)
        
        return sidebar
    
    def create_content_area(self) -> tk.Frame:
        """Create the main content area"""
        content = tk.Frame(self.main_container, bg=ColorScheme.BACKGROUND.value)
        content.pack(side=LEFT, fill=BOTH, expand=True)
        return content
    
    def run(self):
        """Start the application"""
        self.root.mainloop()


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Create application
    app = ModernApplication("Modern UI Demo", "1400x900")
    
    # Create header
    header = app.create_header("Dashboard", "Welcome back, User")
    
    # Create sidebar
    sidebar = app.create_sidebar(260)
    
    # Sidebar navigation items
    nav_items = ["Dashboard", "Analytics", "Settings", "Profile"]
    for item in nav_items:
        btn = ModernButton(
            sidebar,
            text=item,
            variant=ModernButton.Variant.GHOST,
            full_width=True
        )
        btn.pack(pady=Spacing.XS)
    
    # Create content area
    content = app.create_content_area()
    
    # Welcome card
    welcome_card = ModernCard(content, padding=Spacing.XL)
    welcome_card.pack(fill=X, pady=Spacing.MD)
    
    tk.Label(
        welcome_card.content,
        text="Welcome to Modern UI",
        font=Typography.H3,
        fg=ColorScheme.TEXT_PRIMARY.value,
        bg=ColorScheme.SURFACE.value
    ).pack(anchor=W)
    
    tk.Label(
        welcome_card.content,
        text="This is a modern, highly-styled UI framework built with tkinter",
        font=Typography.BODY,
        fg=ColorScheme.TEXT_SECONDARY.value,
        bg=ColorScheme.SURFACE.value
    ).pack(anchor=W, pady=(Spacing.XS, 0))
    
    # Form card
    form_card = ModernCard(content, padding=Spacing.XL)
    form_card.pack(fill=X, pady=Spacing.MD)
    
    tk.Label(
        form_card.content,
        text="Contact Form",
        font=Typography.H4,
        fg=ColorScheme.TEXT_PRIMARY.value,
        bg=ColorScheme.SURFACE.value
    ).pack(anchor=W, pady=(0, Spacing.MD))
    
    # Form fields
    name_entry = ModernEntry(form_card.content, label="Full Name", placeholder="Enter your name")
    name_entry.pack(fill=X, pady=(0, Spacing.MD))
    
    email_entry = ModernEntry(form_card.content, label="Email Address", placeholder="user@example.com")
    email_entry.pack(fill=X, pady=(0, Spacing.MD))
    
    # Buttons
    button_frame = tk.Frame(form_card.content, bg=ColorScheme.SURFACE.value)
    button_frame.pack(fill=X, pady=(Spacing.MD, 0))
    
    def on_submit():
        app.toast.show(f"Welcome, {name_entry.get()}!", "success")
    
    ModernButton(
        button_frame,
        text="Submit",
        variant=ModernButton.Variant.PRIMARY,
        command=on_submit
    ).pack(side=LEFT, padx=(0, Spacing.SM))
    
    ModernButton(
        button_frame,
        text="Cancel",
        variant=ModernButton.Variant.SECONDARY
    ).pack(side=LEFT)
    
    # Badges demo
    badge_frame = ModernCard(content, padding=Spacing.LG)
    badge_frame.pack(fill=X)
    
    tk.Label(
        badge_frame.content,
        text="Status Badges",
        font=Typography.H4,
        fg=ColorScheme.TEXT_PRIMARY.value,
        bg=ColorScheme.SURFACE.value
    ).pack(anchor=W, pady=(0, Spacing.MD))
    
    badge_container = tk.Frame(badge_frame.content, bg=ColorScheme.SURFACE.value)
    badge_container.pack()
    
    for status, variant in [("Success", "success"), ("Warning", "warning"), ("Error", "danger"), ("Info", "info")]:
        ModernBadge(badge_container, text=status, variant=variant).pack(side=LEFT, padx=Spacing.XS)
    
    # Run the application
    app.run()