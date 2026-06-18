from __future__ import annotations
import tkinter as tk
from tkinter import ttk


# ── Keyboard shortcut reference shown in Help dialog ─────────────────────────
SHORTCUT_HELP = [
    ("Screen Navigation (when no dialog open)", ""),
    ("F1",  "Purchase Invoices"),
    ("F2",  "Product List"),
    ("F3",  "Purchase Invoices"),
    ("F4",  "Sales Invoices"),
    ("F5",  "Refresh current screen"),
    ("F6",  "Stock Issues"),
    ("F7",  "Customers"),
    ("F8",  "Suppliers"),
    ("F9",  "Inventory"),
    ("F10", "Retailer Requests"),
    ("F12", "This Help"),
    ("Ctrl+Shift+C", "Open Customers"),
    ("Ctrl+Shift+I", "Open Inventory"),
    ("Ctrl+Shift+R", "Open Reports"),
    ("Ctrl+Shift+P", "Open Product List"),
    ("Ctrl+Shift+S", "Open Suppliers"),
    ("Ctrl+Shift+U", "Open Purchase Invoices"),
    ("Ctrl+Shift+A", "Open Sales Invoices"),
    ("", ""),
    ("Inside Dialogs (Purchase / Sales)", ""),
    ("F2",  "Save voucher"),
    ("F4",  "Add item to list"),
    ("Del", "Remove selected item"),
    ("Esc", "Close dialog"),
    ("", ""),
    ("List Actions", ""),
    ("Ctrl+N",  "New Invoice / Add Record"),
    ("Ctrl+F",  "Focus Search"),
    ("Ctrl+B",  "Open Financial Year Dropdown (Dashboard)"),
    ("Ctrl+R",  "Refresh list"),
    ("Ctrl+E",  "Export Excel"),
    ("Ctrl+P",  "Export PDF"),
    ("Ctrl+W",  "Add Payment"),
    ("Enter",   "Edit selected row"),
    ("Delete",  "Delete selected row"),
    ("", ""),
    ("Other", ""),
    ("Ctrl+L", "Close application"),
]


def install_shortcuts(root: tk.Tk, app) -> None:
    """Install all global keyboard shortcuts on the root window."""

    # ── Screen navigation (only when no Toplevel dialog is open) ──────────
    _bind_safe(root, "<F1>",  lambda: app.show_screen("Invoices"))
    _bind_safe(root, "<F2>",  lambda: app.show_screen("Product List"))
    _bind_safe(root, "<F3>",  lambda: app.show_screen("Invoices"))
    _bind_safe(root, "<F4>",  lambda: app.show_screen("Sales Invoices"))
    _bind_safe(root, "<F5>",  lambda: _dispatch(root, app, "refresh"))
    _bind_safe(root, "<F6>",  lambda: app.show_screen("Stock Issues"))
    _bind_safe(root, "<F7>",  lambda: app.show_screen("Customers"))
    _bind_safe(root, "<F8>",  lambda: app.show_screen("Suppliers"))
    _bind_safe(root, "<F9>",  lambda: app.show_screen("All Products Inventory"))
    _bind_safe(root, "<F10>", lambda: app.show_screen("Retailer Requests"))
    _bind(root, "<F12>", lambda: show_help(root))

    # ── CRUD actions ───────────────────────────────────────────────────────
    _bind(root, "<Control-n>", lambda: _dispatch(root, app, "new"))
    _bind(root, "<Control-N>", lambda: _dispatch(root, app, "new"))
    _bind(root, "<Control-s>", lambda: _dispatch(root, app, "save"))
    _bind(root, "<Control-S>", lambda: _dispatch(root, app, "save"))
    _bind(root, "<Control-d>", lambda: _dispatch(root, app, "delete"))
    _bind(root, "<Control-D>", lambda: _dispatch(root, app, "delete"))
    _bind(root, "<Control-f>", lambda: _dispatch(root, app, "search"))
    _bind(root, "<Control-F>", lambda: _dispatch(root, app, "search"))
    _bind(root, "<Control-b>", lambda: _dispatch(root, app, "fy_dropdown"))
    _bind(root, "<Control-B>", lambda: _dispatch(root, app, "fy_dropdown"))
    _bind(root, "<Control-r>", lambda: _dispatch(root, app, "refresh"))
    _bind(root, "<Control-R>", lambda: _dispatch(root, app, "refresh"))
    _bind(root, "<Control-e>", lambda: _dispatch(root, app, "export_excel"))
    _bind(root, "<Control-E>", lambda: _dispatch(root, app, "export_excel"))
    _bind(root, "<Control-p>", lambda: _dispatch(root, app, "export_pdf"))
    _bind(root, "<Control-P>", lambda: _dispatch(root, app, "export_pdf"))
    _bind(root, "<Control-w>", lambda: _dispatch(root, app, "add_payment"))
    _bind(root, "<Control-W>", lambda: _dispatch(root, app, "add_payment"))
    
    _bind_safe(root, "<Control-Shift-c>", lambda: app.show_screen("Customers"))
    _bind_safe(root, "<Control-Shift-C>", lambda: app.show_screen("Customers"))
    _bind_safe(root, "<Control-Shift-i>", lambda: app.show_screen("All Products Inventory"))
    _bind_safe(root, "<Control-Shift-I>", lambda: app.show_screen("All Products Inventory"))
    _bind_safe(root, "<Control-Shift-r>", lambda: app.show_screen("Reports"))
    _bind_safe(root, "<Control-Shift-R>", lambda: app.show_screen("Reports"))
    _bind_safe(root, "<Control-Shift-p>", lambda: app.show_screen("Product List"))
    _bind_safe(root, "<Control-Shift-P>", lambda: app.show_screen("Product List"))
    _bind_safe(root, "<Control-Shift-s>", lambda: app.show_screen("Suppliers"))
    _bind_safe(root, "<Control-Shift-S>", lambda: app.show_screen("Suppliers"))
    _bind_safe(root, "<Control-Shift-u>", lambda: app.show_screen("Invoices"))
    _bind_safe(root, "<Control-Shift-U>", lambda: app.show_screen("Invoices"))
    _bind_safe(root, "<Control-Shift-a>", lambda: app.show_screen("Sales Invoices"))
    _bind_safe(root, "<Control-Shift-A>", lambda: app.show_screen("Sales Invoices"))
    _bind_safe(root, "<Control-i>", lambda: _dispatch_ctrl_i(root, app))
    _bind_safe(root, "<Control-I>", lambda: _dispatch_ctrl_i(root, app))

    # ── Logout ─────────────────────────────────────────────────────────────
    _bind(root, "<Control-l>", lambda: app.close_app())
    _bind(root, "<Control-L>", lambda: app.close_app())

    # ── Treeview navigation ────────────────────────────────────────────────
    root.bind_all("<Return>",       _handle_return, add="+")
    root.bind_all("<Delete>",       _handle_delete, add="+")
    root.bind_all("<Control-Home>", _handle_tree_jump_first, add="+")
    root.bind_all("<Control-End>",  _handle_tree_jump_last, add="+")
    root.bind_all("<Up>",           _handle_entry_up, add="+")
    root.bind_all("<Down>",         _handle_entry_down, add="+")
    root.bind_all("<Left>",         _handle_entry_left, add="+")
    root.bind_all("<Right>",        _handle_entry_right, add="+")

    # ── Escape: close any open Toplevel ────────────────────────────────────
    root.bind_all("<Escape>", lambda e: _handle_escape(e, app), add="+")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _bind(root, key, fn):
    root.bind_all(key, lambda e, f=fn: f())


def _bind_safe(root, key, fn):
    """Bind only when no Toplevel dialog is currently open."""
    def _handler(e, f=fn):
        # If any grab is active (modal dialog is open), skip the global nav shortcut
        if root.grab_current() is not None:
            return
        f()
    root.bind_all(key, _handler)


def _try(app, method):
    fn = getattr(app, method, None)
    if callable(fn):
        fn()


def _dispatch(root, app, action: str):
    """Dispatch action to the currently visible/focused screen."""
    # Special handling for Ctrl+B - Open FY dropdown in navbar
    if action == "fy_dropdown":
        # Check if app has fy_combo in navbar
        if hasattr(app, 'fy_combo') and app.fy_combo:
            try:
                print("[SHORTCUT] Ctrl+B: Opening navbar FY dropdown")
                app.fy_combo.focus_set()
                app.fy_combo.focus_force()
                app.fy_combo.event_generate('<Button-1>')
                root.after(50, lambda: app.fy_combo.event_generate('<Down>'))
                return
            except Exception as e:
                print(f"[SHORTCUT] Error opening navbar FY dropdown: {e}")
        
        # Fallback: check if active screen has fy_combo (for DashboardScreen)
        active_screen = getattr(app, '_active_screen', None)
        if active_screen and hasattr(active_screen, 'fy_combo'):
            try:
                print("[SHORTCUT] Ctrl+B: Opening screen FY dropdown")
                active_screen.fy_combo.focus_set()
                active_screen.fy_combo.focus_force()
                active_screen.fy_combo.event_generate('<Button-1>')
                root.after(50, lambda: active_screen.fy_combo.event_generate('<Down>'))
                return
            except Exception as e:
                print(f"[SHORTCUT] Error opening screen FY dropdown: {e}")
    
    # Special handling for Ctrl+F on Dashboard
    if action == "search":
        # Check if we're on Dashboard screen
        active_screen = getattr(app, '_active_screen', None)
        if active_screen and hasattr(active_screen, 'fy_combo'):
            # We're on Dashboard - open FY dropdown instead of search
            try:
                active_screen.fy_combo.focus_set()
                active_screen.fy_combo.event_generate('<space>')
                return
            except Exception as e:
                print(f"Error opening FY dropdown: {e}")
    
    focused = root.focus_get()
    # walk up widget tree to find a screen with the action handler
    w = focused
    while w:
        handler = getattr(w, f"kb_{action}", None)
        if callable(handler):
            handler()
            return
        try:
            w = w.master
        except Exception:
            break
    # fall back to app-level
    handler = getattr(app, f"kb_{action}", None)
    if callable(handler):
        handler()


def _handle_return(event):
    widget = event.widget
    if isinstance(widget, ttk.Treeview):
        # trigger open/edit on selected row
        widget.event_generate("<<TreeviewOpen>>")
        return "break"
    if isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox, ttk.Spinbox)):
        # Tab-like forward navigation on Enter
        widget.tk_focusNext().focus_set()
        return "break"
    if isinstance(widget, tk.Button):
        widget.invoke()
        return "break"


def _handle_delete(event):
    widget = event.widget
    if isinstance(widget, ttk.Treeview):
        widget.event_generate("<<TreeviewDelete>>")
        return "break"


def _handle_tree_jump_first(event):
    widget = event.widget
    if isinstance(widget, ttk.Treeview):
        children = widget.get_children()
        if children:
            widget.selection_set(children[0])
            widget.focus(children[0])
            widget.see(children[0])
        return "break"


def _handle_tree_jump_last(event):
    widget = event.widget
    if isinstance(widget, ttk.Treeview):
        children = widget.get_children()
        if children:
            widget.selection_set(children[-1])
            widget.focus(children[-1])
            widget.see(children[-1])
        return "break"


def _handle_escape(event, app):
    # Close topmost Toplevel
    focused = event.widget
    w = focused
    while w:
        if isinstance(w, tk.Toplevel):
            w.destroy()
            return "break"
        try:
            w = w.master
        except Exception:
            break


def _dispatch_ctrl_i(root, app):
    focused = root.focus_get()
    w = focused
    while w:
        handler = getattr(w, "kb_ctrl_i", None)
        if callable(handler):
            handler()
            return "break"
        try:
            w = w.master
        except Exception:
            break
    app.show_screen("New Invoice")
    return "break"


def _handle_entry_up(event):
    widget = event.widget
    if isinstance(widget, (tk.Entry, ttk.Entry)):
        # If autocomplete listbox is open, don't hijack Up arrow
        # Let's check if the widget has a parent/master with _lb (Listbox) active
        # AutoSuggestEntry stores listbox in self._lb. Let's see if we can check it.
        parent = widget.master
        if hasattr(parent, "_lb") and parent._lb is not None:
            return # Let the listbox handle it
        
        prev_w = widget.tk_focusPrev()
        if prev_w:
            prev_w.focus_set()
            if isinstance(prev_w, (tk.Entry, ttk.Entry)):
                prev_w.select_range(0, tk.END)
                prev_w.icursor(tk.END)
        return "break"


def _handle_entry_down(event):
    widget = event.widget
    if isinstance(widget, (tk.Entry, ttk.Entry)):
        parent = widget.master
        if hasattr(parent, "_lb") and parent._lb is not None:
            return # Let the listbox handle it
            
        next_w = widget.tk_focusNext()
        if next_w:
            next_w.focus_set()
            if isinstance(next_w, (tk.Entry, ttk.Entry)):
                next_w.select_range(0, tk.END)
                next_w.icursor(tk.END)
        return "break"


def _handle_entry_left(event):
    widget = event.widget
    if isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox, ttk.Spinbox)):
        try:
            insert_pos = widget.index(tk.INSERT)
            if insert_pos == 0:
                prev_w = widget.tk_focusPrev()
                if prev_w:
                    prev_w.focus_set()
                    if isinstance(prev_w, (tk.Entry, ttk.Entry)):
                        prev_w.select_range(0, tk.END)
                        prev_w.icursor(tk.END)
                return "break"
        except Exception:
            pass


def _handle_entry_right(event):
    widget = event.widget
    if isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox, ttk.Spinbox)):
        try:
            insert_pos = widget.index(tk.INSERT)
            text_len = len(widget.get())
            if insert_pos == text_len:
                next_w = widget.tk_focusNext()
                if next_w:
                    next_w.focus_set()
                    if isinstance(next_w, (tk.Entry, ttk.Entry)):
                        next_w.select_range(0, tk.END)
                        next_w.icursor(tk.END)
                return "break"
        except Exception:
            pass


# ── Help dialog ───────────────────────────────────────────────────────────────

def show_help(parent):
    from .styles import COLORS, FONT
    win = tk.Toplevel(parent)
    win.title("Keyboard Shortcuts")
    win.geometry("480x540")
    win.resizable(False, True)
    win.configure(bg=COLORS["bg_light"])
    win.grab_set()
    win.bind("<Escape>", lambda e: win.destroy())
    win.bind("<F12>", lambda e: win.destroy())

    tk.Label(win, text="⌨  Keyboard Shortcuts", font=FONT["h2"],
             fg=COLORS["dark_text"], bg=COLORS["bg_light"]).pack(pady=(14, 6), padx=20, anchor="w")

    canvas = tk.Canvas(win, bg=COLORS["bg_light"], highlightthickness=0)
    vsb = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    canvas.pack(fill="both", expand=True, padx=12)

    frm = tk.Frame(canvas, bg=COLORS["bg_light"])
    canvas.create_window((0, 0), window=frm, anchor="nw")
    frm.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    from .styles import COLORS as C
    for key, desc in SHORTCUT_HELP:
        row = tk.Frame(frm, bg=C["bg_light"])
        row.pack(fill="x", pady=1)
        if not key and not desc:
            tk.Frame(row, bg=C["border_color"], height=1).pack(fill="x", pady=2)
            continue
        if not desc:  # section header
            tk.Label(row, text=f"  {key}", font=FONT["bold"],
                     fg=C["purple"], bg=C["bg_light"], anchor="w").pack(fill="x", padx=8, pady=(6, 2))
            continue
        tk.Label(row, text=key, font=FONT["mono"], fg=C["orange"],
                 bg=C["white"], width=16, anchor="w",
                 padx=8, pady=3).pack(side="left")
        tk.Label(row, text=desc, font=FONT["base"], fg=C["dark_text"],
                 bg=C["bg_light"], anchor="w").pack(side="left", padx=12)

    tk.Button(win, text="Close  (Esc)", bg=COLORS["gray_text"], fg="white",
              font=FONT["base"], bd=0, relief="flat", padx=16, pady=6,
              command=win.destroy).pack(pady=10)
