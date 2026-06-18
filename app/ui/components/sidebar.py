"""Modern light colorful sidebar with fixed scroll, login/logout, active tracking."""
import tkinter as tk
from tkinter import ttk

from ...styles import COLORS, FONT

# ── Light sidebar palette ─────────────────────────────────────────────────────
S = {
    "bg":         "#ffffff",
    "border":     "#e2e8f0",
    "hdr_bg":     "#6366f1",     # indigo-500
    "hdr_fg":     "#ffffff",
    "user_bg":    "#eef2ff",     # indigo-50
    "user_fg":    "#3730a3",
    "sec_bg":     "#f8fafc",
    "sec_fg":     "#1e293b",
    "sec_hover":  "#e0e7ff",
    "sec_active": "#6366f1",
    "sub_bg":     "#f1f5f9",
    "sub_fg":     "#475569",
    "sub_hover":  "#dbeafe",
    "sub_active": "#3b82f6",
    "sub_act_fg": "#1e40af",
    "sep":        "#e2e8f0",
    "logout_bg":  "#fff1f2",
    "logout_fg":  "#be123c",
    "logout_h":   "#ffe4e6",
    "login_bg":   "#f0fdf4",
    "login_fg":   "#166534",
    "login_h":    "#dcfce7",
    "muted":      "#94a3b8",
    "badge_bg":   "#fee2e2",
    "badge_fg":   "#dc2626",
}

# Section definitions: (icon, label, color_accent, [(label, screen_name), ...])
NAV_SECTIONS = [
    ("#7c3aed", "🛒", "Purchases",   "#7c3aed", [
        ("New Invoice",       "New Invoice"),
        ("All Invoices",      "Invoices"),
        ("Reorder Level",     "Reorder Level"),
        ("Suppliers",         "Suppliers"),
        ("Purchase Return",   "Purchase Return"),
        ("Payment",           "Payment"),
    ]),
    ("#059669", "🏪", "Sales",       "#059669", [
        ("New Sale",          "Sales New Invoice"),
        ("All Sales",         "Sales Invoices"),
        ("Customers",         "Customers"),
        ("Sales Return",      "Sales Return"),
        ("Receipt",           "Receipt"),
    ]),
    ("#d97706", "📦", "Inventory",   "#d97706", [
        ("Product List",      "Product List"),
        ("All Inventory",     "All Products Inventory"),
        ("Batch Report",      "Batch-wise Report"),
        ("Date-wise Report",  "Date-wise Report"),
        ("Stock Statement",   "Stock Statement"),
        ("Transaction History", "Transaction History"),
    ]),
    ("#dc2626", "📊", "Reports",     "#dc2626", [
        ("Sales Report",      "Sales Report"),
        ("Purchase Report",   "Purchases Report"),
        ("Financial Report",  "Financial Report"),
        ("Ledger",            "Ledger"),
    ]),
    ("#0891b2", "⚙", "Retailer Requests", "#0891b2", [
        ("Retailer Requests", "Retailer Requests"),
    ]),
    ("#6366f1", "💾", "System Tools", "#6366f1", [
        ("Database Backup", "Database Backup"),
    ]),
]


class AccordionSidebar(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, bg=S["bg"], width=220, **kwargs)
        self.app = app
        self.pack_propagate(False)
        self._sections     = {}       # key → dict
        self._active_btn   = None     # currently highlighted sub-item
        self._open_key     = None     # currently open section
        self._logged_in    = True

        self._build_header()
        self._build_scrollable_nav()
        self._build_footer()

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self, bg=S["hdr_bg"])
        hdr.pack(fill="x", side="top")

        # Brand row
            

        # User pill
        up = tk.Frame(hdr, bg=S["user_bg"],
                      highlightthickness=1, highlightbackground="#c7d2fe")
        up.pack(fill="x", padx=10, pady=(0, 12), ipady=6)
        # Avatar circle
        av = tk.Canvas(up, width=34, height=34, bg=S["user_bg"],
                       highlightthickness=0)
        av.pack(side="left", padx=(10, 8))
        av.create_oval(2, 2, 32, 32, fill=S["hdr_bg"], outline="")
        av.create_text(17, 17, text="MV", fill="white",
                       font=("Segoe UI", 9, "bold"))
        uc = tk.Frame(up, bg=S["user_bg"])
        uc.pack(side="left")
        user_name = getattr(self.app, '_current_user', '') or 'Admin User'
        tk.Label(uc, text=user_name, font=("Segoe UI", 9, "bold"),
                 bg=S["user_bg"], fg=S["user_fg"]).pack(anchor="w")
        self._role_lbl = tk.Label(uc, text="\u25cf Online", font=("Segoe UI", 7),
                                   bg=S["user_bg"], fg="#16a34a")
        self._role_lbl.pack(anchor="w")

        tk.Frame(self, bg=S["sep"], height=1).pack(fill="x", side="top")

    # ── Scrollable nav area ───────────────────────────────────────────────────

    def _build_scrollable_nav(self):
        # Fixed (no scrolling): keep the sidebar height stable.
        # This prevents the UI from looking like it "scrolls down".
        outer = tk.Frame(self, bg=S["bg"])
        outer.pack(fill="both", expand=True, side="top")

        # Use a simple frame instead of canvas+scrollbar.
        self._nav_frame = tk.Frame(outer, bg=S["bg"])
        self._nav_frame.pack(fill="both", expand=True, side="top")

        self._populate_nav()

        # Ensure footer/buttons remain visible.
        self._nav_frame.pack_propagate(False)


    # Canvas/scroll handlers are kept for compatibility with older versions.
    # Sidebar is now fixed-height (no scrolling).
    def _on_frm_cfg(self, e):
        pass

    def _on_cvs_cfg(self, e):
        pass

    def _on_wheel(self, e):
        pass


    def _populate_nav(self):
        for entry in NAV_SECTIONS:
            accent, icon, title, color, subs = entry
            self._add_section(icon, title, color, subs)

    def _add_section(self, icon, title, color, subs):
        key = title
        wrap = tk.Frame(self._nav_frame, bg=S["bg"])
        wrap.pack(fill="x", pady=(2, 0))

        # Section header button
        hdr = tk.Frame(wrap, bg=S["bg"], cursor="hand2")
        hdr.pack(fill="x")

        # Color accent left bar
        bar = tk.Frame(hdr, bg=color, width=4)
        bar.pack(side="left", fill="y")

        content = tk.Frame(hdr, bg=S["bg"])
        content.pack(side="left", fill="x", expand=True, padx=(8, 0), pady=8)

        icon_lbl = tk.Label(content, text=icon, font=("Segoe UI", 12),
                            bg=S["bg"], fg=color)
        icon_lbl.pack(side="left", padx=(0, 6))

        title_lbl = tk.Label(content, text=title, font=("Segoe UI", 10, "bold"),
                              bg=S["bg"], fg=S["sec_fg"], anchor="w")
        title_lbl.pack(side="left", fill="x", expand=True)

        chev = tk.Label(hdr, text="›", font=("Segoe UI", 13, "bold"),
                        bg=S["bg"], fg=S["muted"], padx=10)
        chev.pack(side="right")

        # Sub-menu frame (hidden initially)
        sub_wrap = tk.Frame(wrap, bg=S["sub_bg"])
        left_line = tk.Frame(sub_wrap, bg=color, width=3)
        left_line.pack(side="left", fill="y")
        sub_inner = tk.Frame(sub_wrap, bg=S["sub_bg"])
        sub_inner.pack(side="left", fill="both", expand=True)

        for label, screen in subs:
            btn = tk.Button(sub_inner, text=f"  {label}",
                            font=("Segoe UI", 9), bg=S["sub_bg"],
                            fg=S["sub_fg"], anchor="w", cursor="hand2",
                            padx=16, pady=7, relief="flat", bd=0,
                            activebackground=S["sub_hover"],
                            activeforeground=S["sub_act_fg"],
                            takefocus=True)
            btn.pack(fill="x")
            btn.bind("<Enter>",    lambda e, b=btn: b.config(bg=S["sub_hover"]))
            btn.bind("<Leave>",    lambda e, b=btn, k=key: self._sub_leave(b, k))
            btn.bind("<FocusIn>",  lambda e, b=btn: b.config(bg=S["sub_hover"]))
            btn.bind("<FocusOut>", lambda e, b=btn, k=key: self._sub_leave(b, k))
            btn.bind("<Button-1>", lambda e, s=screen, b=btn: self._click(s, b))
            btn.bind("<Return>",   lambda e, s=screen, b=btn: self._click(s, b))
            btn.bind("<space>",    lambda e, s=screen, b=btn: self._click(s, b))
            btn.bind("<MouseWheel>", self._on_wheel)

        # hover on header
        for w in [hdr, content, icon_lbl, title_lbl, chev, bar]:
            w.bind("<Enter>",    lambda e, k=key: self._hdr_hover(k, True))
            w.bind("<Leave>",    lambda e, k=key: self._hdr_hover(k, False))
            w.bind("<Button-1>", lambda e, k=key: self._toggle(k))
            w.bind("<MouseWheel>", self._on_wheel)

        self._sections[key] = {
            "wrap": wrap, "hdr": hdr, "bar": bar,
            "content": content, "icon": icon_lbl,
            "title": title_lbl, "chev": chev,
            "sub_wrap": sub_wrap, "sub_inner": sub_inner,
            "color": color, "open": False,
        }

    def _sub_leave(self, btn, key):
        """Restore sub-item bg unless it's the active one."""
        if btn is self._active_btn:
            d = self._sections.get(key, {})
            btn.config(bg=d.get("color", S["sub_active"]),
                       fg="white")
        else:
            btn.config(bg=S["sub_bg"], fg=S["sub_fg"])

    def _hdr_hover(self, key, entering):
        d = self._sections.get(key, {})
        if not d:
            return
        bg = S["sec_hover"] if entering else S["bg"]
        for w in ["hdr", "content", "icon", "title", "chev"]:
            try:
                d[w].config(bg=bg)
            except Exception:
                pass

    def _toggle(self, key):
        d = self._sections.get(key, {})
        if not d:
            return

        # Close previously open section
        if self._open_key and self._open_key != key:
            od = self._sections.get(self._open_key, {})
            if od:
                od["sub_wrap"].pack_forget()
                od["chev"].config(text="›")
                od["open"] = False

        if d["open"]:
            d["sub_wrap"].pack_forget()
            d["chev"].config(text="›")
            d["open"] = False
            self._open_key = None
        else:
            d["sub_wrap"].pack(fill="x", after=d["hdr"])
            d["chev"].config(text="⌄")
            d["open"] = True
            self._open_key = key

        self._nav_frame.update_idletasks()

    def _click(self, screen, btn):
        # Reset previous active
        if self._active_btn and self._active_btn is not btn:
            try:
                self._active_btn.config(bg=S["sub_bg"], fg=S["sub_fg"])
            except Exception:
                pass
        # Find which section owns this btn and use its color
        color = S["sub_active"]
        for d in self._sections.values():
            try:
                if btn in d["sub_inner"].winfo_children():
                    color = d["color"]
                    break
            except Exception:
                pass
        btn.config(bg=color, fg="white")
        self._active_btn = btn
        self.app.show_screen(screen)

    # ── Footer: logout + login ────────────────────────────────────────────────

    def _build_footer(self):
        tk.Frame(self, bg=S["sep"], height=1).pack(fill="x", side="bottom")

        footer = tk.Frame(self, bg=S["bg"])
        footer.pack(fill="x", side="bottom")

        # Logout button
        self._logout_btn = tk.Button(
            footer, text="  🔓  Logout",
            font=("Segoe UI", 9, "bold"),
            bg=S["logout_bg"], fg=S["logout_fg"],
            bd=0, relief="flat", anchor="w",
            padx=14, pady=9, cursor="hand2",
            activebackground=S["logout_h"],
            activeforeground=S["logout_fg"],
            command=self._logout)
        self._logout_btn.pack(fill="x")
        self._logout_btn.bind("<Enter>",
            lambda e: self._logout_btn.config(bg=S["logout_h"]))
        self._logout_btn.bind("<Leave>",
            lambda e: self._logout_btn.config(bg=S["logout_bg"]))

        # Login button (hidden by default, shown after logout)
        self._login_btn = tk.Button(
            footer, text="  🔐  Login",
            font=("Segoe UI", 9, "bold"),
            bg=S["login_bg"], fg=S["login_fg"],
            bd=0, relief="flat", anchor="w",
            padx=14, pady=9, cursor="hand2",
            activebackground=S["login_h"],
            activeforeground=S["login_fg"],
            command=self._login)
        self._login_btn.bind("<Enter>",
            lambda e: self._login_btn.config(bg=S["login_h"]))
        self._login_btn.bind("<Leave>",
            lambda e: self._login_btn.config(bg=S["login_bg"]))

    def _logout(self):
        from tkinter import messagebox
        if not messagebox.askyesno("Logout", "Are you sure you want to logout?", parent=self):
            return
        # Delegate fully to the app's logout handler which tears down
        # all main widgets and navigates back to the real login page.
        if hasattr(self.app, "_do_logout"):
            self.app._do_logout()

    def _login(self):
        # Navigate to the real login page — no popup.
        if hasattr(self.app, "_do_logout"):
            self.app._do_logout()
