"""
Modern UI components with enhanced styling, animations, and colorful design.
Replaces and extends the basic components in styles.py
"""
import tkinter as tk
from tkinter import ttk
import time
from typing import Callable, Optional

from .styles import COLORS, FONT, BTN

# ── Extended modern color palette ─────────────────────────────────────────────
MODERN_COLORS = {
    # Gradients (for backgrounds)
    "gradient_start": "#667eea",
    "gradient_end":   "#764ba2",
    
    # Glassmorphism
    "glass_light": "rgba(255, 255, 255, 0.1)",
    "glass_dark":  "rgba(0, 0, 0, 0.1)",
    
    # Enhanced shadows
    "shadow_sm": "#0a0e27",
    "shadow_md": "#010a1a",
    
    # Accent colors (vibrant)
    "accent_cyan":    "#06b6d4",
    "accent_pink":    "#ec4899",
    "accent_lime":    "#84cc16",
    "accent_violet":  "#a78bfa",
    
    # Micro-interactions
    "focus_glow": "shadow 0 0 0 3px rgba(102, 126, 234, 0.1)",
}

# ── Modern button styles with gradients ───────────────────────────────────────
MODERN_BUTTONS = {
    "primary":   {"bg": "#667eea", "hover": "#764ba2", "active": "#5647d4"},
    "success":   {"bg": "#10b981", "hover": "#059669", "active": "#047857"},
    "danger":    {"bg": "#f43f5e", "hover": "#e11d48", "active": "#be123c"},
    "warning":   {"bg": "#f59e0b", "hover": "#d97706", "active": "#b45309"},
    "info":      {"bg": "#06b6d4", "hover": "#0891b2", "active": "#0e7490"},
    "light":     {"bg": "#e2e8f0", "hover": "#cbd5e1", "active": "#94a3b8"},
    "dark":      {"bg": "#334155", "hover": "#1e293b", "active": "#0f172a"},
    "gradient":  {"bg": "#667eea", "hover": "#764ba2", "active": "#5647d4"},
    "purple":    {"bg": "#7c3aed", "hover": "#6d28d9", "active": "#5b21b6"},
    "secondary": {"bg": "#64748b", "hover": "#475569", "active": "#334155"},
}


class ModernButton(tk.Button):
    """Enhanced button with hover animations, shadows, and modern styling."""
    
    def __init__(self, parent, text, variant="primary", command=None, 
                 width=None, height=None, icon=None, **kwargs):
        self.variant = variant
        self.cfg = MODERN_BUTTONS.get(variant, MODERN_BUTTONS["primary"])
        self.hover_id = None
        
        super().__init__(
            parent,
            text=text,
            bg=self.cfg["bg"],
            fg="white",
            font=kwargs.pop("font", FONT["base"]),
            bd=0,
            relief="flat",
            padx=kwargs.pop("padx", 16),
            pady=kwargs.pop("pady", 10),
            activebackground=self.cfg["hover"],
            activeforeground="white",
            cursor="hand2",
            **kwargs
        )
        
        if width:
            self.config(width=width)
        if height:
            self.config(height=height)
        
        if command:
            self.config(command=command)
        
        # Bind hover and click effects
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<space>", lambda e: self.invoke())
    
    def _on_enter(self, event):
        """Smooth hover transition."""
        self.config(bg=self.cfg["hover"])
    
    def _on_leave(self, event):
        """Revert to normal state."""
        self.config(bg=self.cfg["bg"])
    
    def _on_press(self, event):
        """Active state on click."""
        self.config(bg=self.cfg["active"])
    
    def _on_release(self, event):
        """Return to hover/normal state."""
        self.config(bg=self.cfg["hover"] if self.winfo_containing(event.x_root, event.y_root) == self else self.cfg["bg"])


class ModernEntry(tk.Entry):
    """Enhanced entry widget with focus effects and placeholder support."""
    
    def __init__(self, parent, placeholder="", **kwargs):
        self.placeholder = placeholder
        self.placeholder_set = False
        self.show_char = kwargs.pop("show", "")
        
        super().__init__(
            parent,
            font=kwargs.pop("font", FONT["base"]),
            relief="solid",
            bd=1,
            bg=COLORS["input_bg"],
            fg=COLORS["dark_text"],
            insertbackground=COLORS["dark_text"],
            highlightthickness=2,
            highlightbackground=COLORS["border_color"],
            highlightcolor=COLORS["focus_ring"],
            show=self.show_char,
            **kwargs
        )
        
        if placeholder:
            self._set_placeholder()
        
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
    
    def _set_placeholder(self):
        """Set placeholder text."""
        if not self.get():
            self.insert(0, self.placeholder)
            self.config(fg=COLORS["gray_text"], show="")
            self.placeholder_set = True
    
    def _clear_placeholder(self):
        """Clear placeholder when user starts typing."""
        if self.placeholder_set:
            self.delete(0, tk.END)
            self.config(fg=COLORS["dark_text"], show=self.show_char)
            self.placeholder_set = False
    
    def _on_focus_in(self, event):
        """Handle focus in."""
        self._clear_placeholder()
        self.config(highlightcolor=COLORS["focus_ring"])
    
    def _on_focus_out(self, event):
        """Handle focus out."""
        if not self.get() and self.placeholder:
            self._set_placeholder()


class ModernLabel(tk.Label):
    """Enhanced label with typography variants."""
    
    def __init__(self, parent, text="", variant="normal", **kwargs):
        variants = {
            "h1":        {"font": FONT["h1"], "fg": COLORS["dark_text"]},
            "h2":        {"font": FONT["h2"], "fg": COLORS["dark_text"]},
            "h3":        {"font": FONT["h3"], "fg": COLORS["dark_text"]},
            "title":     {"font": ("Segoe UI", 16, "bold"), "fg": COLORS["dark_text"]},
            "subtitle":  {"font": ("Segoe UI", 12), "fg": COLORS["gray_text"]},
            "body":      {"font": FONT["base"], "fg": COLORS["dark_text"]},
            "caption":   {"font": FONT["sm"], "fg": COLORS["gray_text"]},
            "muted":     {"font": FONT["sm"], "fg": COLORS["muted"]},
            "success":   {"font": ("Segoe UI", 10, "bold"), "fg": COLORS["green"]},
            "danger":    {"font": ("Segoe UI", 10, "bold"), "fg": COLORS["red"]},
            "warning":   {"font": ("Segoe UI", 10, "bold"), "fg": COLORS["orange"]},
            "info":      {"font": ("Segoe UI", 10, "bold"), "fg": COLORS["blue_badge"]},
            "badge":     {"font": ("Segoe UI", 9, "bold"), "fg": COLORS["purple"]},
        }
        
        cfg = variants.get(variant, variants["body"])
        cfg.update(kwargs)
        
        super().__init__(
            parent,
            text=text,
            bg=kwargs.pop("bg", COLORS["bg_light"]),
            **{k: v for k, v in cfg.items() if k not in ("bg",)}
        )


class ModernFrame(ttk.Frame):
    """Card-like frame with shadow effect for grouping content."""
    
    def __init__(self, parent, title="", shadow=True, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(style="Card.TFrame")
        
        if title:
            header = ModernLabel(self, text=title, variant="h3")
            header.pack(fill="x", padx=16, pady=(16, 8))
        
        self.content = ttk.Frame(self, style="TFrame")
        self.content.pack(fill="both", expand=True, padx=16, pady=(0, 16))


class ModernCheckbutton(tk.Checkbutton):
    """Modern checkbox with enhanced styling."""
    
    def __init__(self, parent, text="", variable=None, **kwargs):
        super().__init__(
            parent,
            text=text,
            variable=variable,
            font=kwargs.pop("font", FONT["base"]),
            bg=COLORS["bg_light"],
            fg=COLORS["dark_text"],
            selectcolor=COLORS["bg_light"],
            activebackground=COLORS["bg_light"],
            activeforeground=COLORS["dark_text"],
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            **kwargs
        )


class ModernCombobox(ttk.Combobox):
    """Modern dropdown with styled appearance."""
    
    def __init__(self, parent, values=None, **kwargs):
        super().__init__(
            parent,
            values=values or [],
            state="readonly",
            font=kwargs.pop("font", FONT["base"]),
            **kwargs
        )


class StatusBadge(tk.Label):
    """Colored badge for status display."""
    
    STATUS_COLORS = {
        "active":      ("#10b981", "#ecfdf5"),
        "inactive":    ("#6b7280", "#f9fafb"),
        "pending":     ("#f59e0b", "#fefce8"),
        "completed":   ("#10b981", "#ecfdf5"),
        "failed":      ("#ef4444", "#fef2f2"),
        "warning":     ("#f59e0b", "#fffbeb"),
        "info":        ("#06b6d4", "#ecfdfd"),
    }
    
    def __init__(self, parent, text="", status="info", **kwargs):
        fg_color, bg_color = self.STATUS_COLORS.get(status, self.STATUS_COLORS["info"])
        
        super().__init__(
            parent,
            text=text,
            font=("Segoe UI", 9, "bold"),
            fg=fg_color,
            bg=bg_color,
            padx=8,
            pady=4,
            relief="flat",
            bd=0,
            **kwargs
        )


class AnimatedProgressBar(ttk.Progressbar):
    """Progress bar with smooth animation."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, mode="determinate", **kwargs)
        self._target = 0
        self._current = 0
    
    def set_animated(self, value: int, duration_ms: int = 500):
        """Animate progress to target value."""
        self._target = value
        self._current = self.get()
        steps = max(1, duration_ms // 16)  # ~60fps
        step_value = (self._target - self._current) / steps
        self._animate_step(step_value, steps)
    
    def _animate_step(self, step_value: float, remaining_steps: int):
        """Perform one animation step."""
        if remaining_steps > 0:
            self._current += step_value
            self.set(self._current)
            self.after(16, self._animate_step, step_value, remaining_steps - 1)


class PopupNotification(tk.Toplevel):
    """Toast-like notification popup."""
    
    def __init__(self, parent, title="", message="", notification_type="info", duration_ms=3000):
        super().__init__(parent)
        self.overrideredirect(True)
        
        # Colors based on type
        colors = {
            "success": ("#10b981", "#ecfdf5"),
            "error":   ("#ef4444", "#fef2f2"),
            "warning": ("#f59e0b", "#fffbeb"),
            "info":    ("#06b6d4", "#ecfdfd"),
        }
        
        fg_color, bg_color = colors.get(notification_type, colors["info"])
        
        # Main frame
        frame = tk.Frame(self, bg=bg_color, relief="solid", bd=1)
        frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Title
        if title:
            tk.Label(
                frame,
                text=title,
                font=("Segoe UI", 10, "bold"),
                fg=fg_color,
                bg=bg_color
            ).pack(anchor="w", padx=12, pady=(8, 2))
        
        # Message
        tk.Label(
            frame,
            text=message,
            font=("Segoe UI", 9),
            fg=fg_color,
            bg=bg_color,
            wraplength=300
        ).pack(anchor="w", padx=12, pady=(2, 8))
        
        # Position at bottom-right
        self.update_idletasks()
        x = parent.winfo_screenwidth() - self.winfo_width() - 20
        y = parent.winfo_screenheight() - self.winfo_height() - 20
        self.geometry(f"+{x}+{y}")
        
        # Auto-close
        if duration_ms > 0:
            self.after(duration_ms, self.destroy)


class LoadingSpinner(tk.Label):
    """Animated loading spinner."""
    
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            text=self.FRAMES[0],
            font=("Segoe UI", 20),
            fg=COLORS["purple"],
            bg=kwargs.pop("bg", COLORS["bg_light"]),
            **kwargs
        )
        self._frame_index = 0
        self._animate_id = None
    
    def start(self):
        """Start animation."""
        if self._animate_id is None:
            self._animate()
    
    def stop(self):
        """Stop animation."""
        if self._animate_id:
            self.after_cancel(self._animate_id)
            self._animate_id = None
    
    def _animate(self):
        """Animate to next frame."""
        self._frame_index = (self._frame_index + 1) % len(self.FRAMES)
        self.config(text=self.FRAMES[self._frame_index])
        self._animate_id = self.after(100, self._animate)


class SeparatorWithLabel(tk.Frame):
    """Visual separator with optional label."""
    
    def __init__(self, parent, label="", **kwargs):
        super().__init__(parent, bg=COLORS["bg_light"], **kwargs)
        
        if label:
            tk.Label(
                self,
                text=label,
                font=FONT["sm"],
                fg=COLORS["gray_text"],
                bg=COLORS["bg_light"]
            ).pack(side="left", padx=(0, 8))
        
        tk.Frame(self, bg=COLORS["border_color"], height=1).pack(
            side="left", fill="x", expand=True
        )


class HoverFrame(tk.Frame):
    """Frame with hover background effect."""
    
    def __init__(self, parent, hover_color=None, **kwargs):
        self.normal_bg = kwargs.pop("bg", COLORS["bg_light"])
        self.hover_color = hover_color or COLORS["white2"]
        
        super().__init__(parent, bg=self.normal_bg, **kwargs)
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        # Bind children's events
        self.bind_all("<Enter>", self._on_child_enter)
        self.bind_all("<Leave>", self._on_child_leave)
    
    def _on_enter(self, event):
        """Hover in."""
        self.config(bg=self.hover_color)
    
    def _on_leave(self, event):
        """Hover out."""
        if event.widget == self:
            self.config(bg=self.normal_bg)
    
    def _on_child_enter(self, event):
        """Child hover in."""
        if self._contains_widget(event.widget):
            self.config(bg=self.hover_color)
    
    def _on_child_leave(self, event):
        """Child hover out."""
        if not self._contains_widget(event.widget):
            self.config(bg=self.normal_bg)
    
    def _contains_widget(self, widget):
        """Check if frame contains widget."""
        try:
            return widget in self.winfo_children() or widget.master == self
        except:
            return False
