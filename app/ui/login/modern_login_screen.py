# import tkinter as tk
# from ...styles import COLORS

# BG      = "#f0f4ff"
# CARD_BG = "#ffffff"
# PURPLE  = "#6366f1"
# PURPLE2 = "#4f46e5"
# GRAY    = "#64748b"
# MUTED   = "#94a3b8"
# RED     = "#ef4444"
# BORDER  = "#e2e8f0"


# def _btn(parent, text, bg, hover, cmd):
#     b = tk.Button(parent, text=text, bg=bg, fg="white",
#                   font=("Segoe UI", 11, "bold"), bd=0, relief="flat",
#                   cursor="hand2", activebackground=hover,
#                   activeforeground="white", command=cmd)
#     b.pack(fill="x", ipady=10)
#     b.bind("<Enter>", lambda e: b.config(bg=hover))
#     b.bind("<Leave>", lambda e: b.config(bg=bg))
#     return b


# def _entry(parent, var, show=""):
#     f = tk.Frame(parent, bg=BORDER, bd=0)
#     f.pack(fill="x", pady=(0, 4))
#     inner = tk.Frame(f, bg=CARD_BG, bd=0)
#     inner.pack(fill="x", padx=1, pady=1)
#     e = tk.Entry(inner, textvariable=var, show=show,
#                  font=("Segoe UI", 11), bg=CARD_BG, fg="#1e293b",
#                  insertbackground=PURPLE, relief="flat", bd=0)
#     e.pack(fill="x", ipady=9, padx=12)
#     e.bind("<FocusIn>",  lambda ev: f.config(bg=PURPLE))
#     e.bind("<FocusOut>", lambda ev: f.config(bg=BORDER))
#     return e


# class ModernLoginScreen(tk.Frame):
#     def __init__(self, parent, app_instance=None, on_login=None, **kwargs):
#         super().__init__(parent, bg=BG, **kwargs)
#         self.app      = app_instance
#         self.on_login = on_login
#         self._build()

#     def _build(self):
#         self.configure(bg=BG)

#         # Left decorative panel
#         left = tk.Frame(self, bg=PURPLE, width=420)
#         left.pack(side="left", fill="y")
#         left.pack_propagate(False)

#         tk.Label(left, text="💊", font=("Segoe UI", 64),
#                  bg=PURPLE, fg="white").place(relx=0.5, rely=0.38, anchor="center")
#         tk.Label(left, text="MedicVista", font=("Segoe UI", 26, "bold"),
#                  bg=PURPLE, fg="white").place(relx=0.5, rely=0.52, anchor="center")
#         tk.Label(left, text="Pharmacy ERP", font=("Segoe UI", 13),
#                  bg=PURPLE, fg="#c7d2fe").place(relx=0.5, rely=0.59, anchor="center")
#         tk.Label(left, text="Efficient · Reliable · Modern",
#                  font=("Segoe UI", 10, "italic"),
#                  bg=PURPLE, fg="#a5b4fc").place(relx=0.5, rely=0.65, anchor="center")
#         tk.Label(left, text="© 2025 MedicVista", font=("Segoe UI", 8),
#                  bg=PURPLE, fg="#a5b4fc").place(relx=0.5, rely=0.94, anchor="center")

#         # Right login panel
#         right = tk.Frame(self, bg=BG)
#         right.pack(side="left", fill="both", expand=True)

#         card = tk.Frame(right, bg=CARD_BG, bd=0,
#                         highlightthickness=1, highlightbackground=BORDER)
#         card.place(relx=0.5, rely=0.5, anchor="center", width=380)

#         tk.Frame(card, bg=PURPLE, height=5).pack(fill="x")

#         body = tk.Frame(card, bg=CARD_BG, padx=36, pady=32)
#         body.pack(fill="both", expand=True)

#         tk.Label(body, text="Welcome back 👋", font=("Segoe UI", 20, "bold"),
#                  fg="#1e293b", bg=CARD_BG).pack(anchor="w")
#         tk.Label(body, text="Sign in to your retailer account",
#                  font=("Segoe UI", 10), fg=MUTED, bg=CARD_BG).pack(anchor="w", pady=(2, 24))

#         tk.Label(body, text="Username", font=("Segoe UI", 9, "bold"),
#                  fg=GRAY, bg=CARD_BG).pack(anchor="w", pady=(0, 4))
#         self._var_user = tk.StringVar()
#         self._e_user = _entry(body, self._var_user)

#         tk.Frame(body, bg=BG, height=10).pack()

#         tk.Label(body, text="Password", font=("Segoe UI", 9, "bold"),
#                  fg=GRAY, bg=CARD_BG).pack(anchor="w", pady=(0, 4))
#         self._var_pass = tk.StringVar()
#         self._e_pass = _entry(body, self._var_pass, show="●")

#         self._show_pw = tk.BooleanVar(value=False)
#         tk.Checkbutton(body, text="Show password", variable=self._show_pw,
#                        command=self._toggle_pw, font=("Segoe UI", 9),
#                        fg=MUTED, bg=CARD_BG, selectcolor=CARD_BG,
#                        activebackground=CARD_BG, bd=0,
#                        highlightthickness=0, cursor="hand2").pack(anchor="w", pady=(6, 20))

#         self._err_var = tk.StringVar()
#         tk.Label(body, textvariable=self._err_var, font=("Segoe UI", 9),
#                  fg=RED, bg=CARD_BG).pack(anchor="w", pady=(0, 8))

#         _btn(body, "Sign In", PURPLE, PURPLE2, self._login)

#         # Hint
#         hint = tk.Frame(body, bg=CARD_BG)
#         hint.pack(fill="x", pady=(16, 0))
#         tk.Label(hint, text="retailer1=BSL Pharmacy  |  retailer2=MedPlus  |  retailer3=Apollo  |  retailer4=Wellness",
#                  font=("Segoe UI", 8), fg=MUTED, bg=CARD_BG).pack(anchor="w")

#         self._e_user.bind("<Return>", lambda e: self._e_pass.focus_set())
#         self._e_pass.bind("<Return>", lambda e: self._login())
#         self.after(100, self._e_user.focus_set)

#     def _toggle_pw(self):
#         self._e_pass.config(show="" if self._show_pw.get() else "●")

#     def _login(self):
#         username = self._var_user.get().strip()
#         password = self._var_pass.get()
#         self._err_var.set("")

#         if not username:
#             self._err_var.set("⚠ Username is required.")
#             self._e_user.focus_set()
#             return
#         if not password:
#             self._err_var.set("⚠ Password is required.")
#             self._e_pass.focus_set()
#             return

#         # Authenticate against database
#         retailer_id, full_name, error = self._authenticate(username, password)
#         if error:
#             self._err_var.set(f"⚠ {error}")
#             self._var_pass.set("")
#             self._e_pass.focus_set()
#             return

#         # Success — fire callback with (username, password, retailer_id, full_name)
#         if self.on_login:
#             self.on_login(username, password, retailer_id, full_name)
#         elif self.app and hasattr(self.app, "do_login"):
#             self.app.do_login(username, password, retailer_id, full_name)

#     def _authenticate(self, username: str, password: str):
#         """
#         Returns (retailer_id, full_name, None) on success,
#                 (None, None, error_message) on failure.
#         """
#         try:
#             import pymysql
#             from ...config import load_config
#             cfg = load_config()
#             conn = pymysql.connect(
#                 host=cfg.db_host, port=cfg.db_port,
#                 user=cfg.db_user, password=cfg.db_password,
#                 database=cfg.db_name, charset="utf8mb4",
#                 connect_timeout=5,
#             )
#             with conn.cursor() as cur:
#                 cur.execute(
#                     "SELECT retailer_id, full_name FROM retailer_users "
#                     "WHERE username=%s AND password=%s AND is_active=1 LIMIT 1",
#                     (username, password),
#                 )
#                 row = cur.fetchone()
#             conn.close()
#             if row:
#                 return row[0], row[1] or username, None
#             return None, None, "Invalid username or password."
#         except Exception as e:
#             return None, None, f"DB error: {e}"


import tkinter as tk
from ...styles import COLORS


# -----------------------------------------------------------------------------
# Visual theme
# -----------------------------------------------------------------------------
FONT = "Segoe UI"

BG = "#f5f7ff"
CARD_BG = "#ffffff"
INPUT_BG = "#fbfcff"
PURPLE = "#635bff"
PURPLE_DARK = "#5148e8"
PURPLE_SOFT = "#eeedff"
NAVY = "#18223b"
TEXT = "#25304a"
GRAY = "#667085"
MUTED = "#98a2b3"
RED = "#e5484d"
BORDER = "#e5e7f0"
BORDER_FOCUS = "#b9b5ff"
WHITE = "#ffffff"


# Keep the helper API intact; only its visual presentation is enhanced.
def _btn(parent, text, bg, hover, cmd):
    b = tk.Button(
        parent,
        text=text,
        bg=bg,
        fg=WHITE,
        font=(FONT, 11, "bold"),
        bd=0,
        relief="flat",
        cursor="hand2",
        activebackground=hover,
        activeforeground=WHITE,
        highlightthickness=0,
        padx=14,
        pady=0,
        command=cmd,
    )
    b.pack(fill="x", ipady=11)
    b.bind("<Enter>", lambda e: b.config(bg=hover))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def _entry(parent, var, show=""):
    """Create a clean, focus-aware input without changing its behavior."""
    border = tk.Frame(parent, bg=BORDER, bd=0, highlightthickness=0)
    border.pack(fill="x", pady=(0, 4))

    inner = tk.Frame(border, bg=INPUT_BG, bd=0)
    inner.pack(fill="x", padx=1, pady=1)

    e = tk.Entry(
        inner,
        textvariable=var,
        show=show,
        font=(FONT, 11),
        bg=INPUT_BG,
        fg=TEXT,
        insertbackground=PURPLE,
        selectbackground=PURPLE_SOFT,
        selectforeground=TEXT,
        relief="flat",
        bd=0,
        highlightthickness=0,
    )
    e.pack(fill="x", ipady=10, padx=13)

    def focus_in(_event):
        border.config(bg=BORDER_FOCUS)
        inner.config(bg=WHITE)
        e.config(bg=WHITE)

    def focus_out(_event):
        border.config(bg=BORDER)
        inner.config(bg=INPUT_BG)
        e.config(bg=INPUT_BG)

    e.bind("<FocusIn>", focus_in)
    e.bind("<FocusOut>", focus_out)
    return e


class ModernLoginScreen(tk.Frame):
    def __init__(self, parent, app_instance=None, on_login=None, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.app = app_instance
        self.on_login = on_login
        self._build()

    def _build(self):
        self.configure(bg=BG)

        # Left decorative panel
        left = tk.Frame(self, bg=PURPLE, width=420)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        # Subtle decorative shapes keep the panel lively without affecting layout.
        tk.Frame(left, bg="#716bff", width=170, height=170).place(
            relx=1.0, rely=0.0, anchor="ne"
        )
        tk.Frame(left, bg="#5b53ef", width=120, height=120).place(
            relx=0.0, rely=1.0, anchor="sw"
        )

        brand = tk.Frame(left, bg=PURPLE)
        brand.place(relx=0.5, rely=0.43, anchor="center")

        tk.Label(
            brand,
            text="✦",
            font=(FONT, 48, "bold"),
            bg=PURPLE,
            fg=WHITE,
        ).pack(pady=(0, 8))
        tk.Label(
            brand,
            text="MedicVista",
            font=(FONT, 27, "bold"),
            bg=PURPLE,
            fg=WHITE,
        ).pack()
        tk.Label(
            brand,
            text="PHARMACY ERP",
            font=(FONT, 10, "bold"),
            bg=PURPLE,
            fg="#d8d6ff",
        ).pack(pady=(8, 0))
        tk.Label(
            brand,
            text="Efficient  ·  Reliable  ·  Modern",
            font=(FONT, 10, "italic"),
            bg=PURPLE,
            fg="#c6c3ff",
        ).pack(pady=(12, 0))

        tk.Label(
            left,
            text="© 2025 MedicVista",
            font=(FONT, 8),
            bg=PURPLE,
            fg="#c6c3ff",
        ).place(relx=0.5, rely=0.94, anchor="center")

        # Right login panel
        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        card = tk.Frame(
            right,
            bg=CARD_BG,
            bd=0,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=BORDER,
        )
        card.place(relx=0.5, rely=0.5, anchor="center", width=410)

        # Accent bar
        tk.Frame(card, bg=PURPLE, height=6).pack(fill="x")

        body = tk.Frame(card, bg=CARD_BG, padx=38, pady=34)
        body.pack(fill="both", expand=True)

        tk.Label(
            body,
            text="Welcome back",
            font=(FONT, 22, "bold"),
            fg=NAVY,
            bg=CARD_BG,
        ).pack(anchor="w")
        tk.Label(
            body,
            text="Sign in to your retailer account",
            font=(FONT, 10),
            fg=GRAY,
            bg=CARD_BG,
        ).pack(anchor="w", pady=(5, 27))

        tk.Label(
            body,
            text="USERNAME",
            font=(FONT, 8, "bold"),
            fg=GRAY,
            bg=CARD_BG,
        ).pack(anchor="w", pady=(0, 6))
        self._var_user = tk.StringVar()
        self._e_user = _entry(body, self._var_user)

        tk.Frame(body, bg=CARD_BG, height=13).pack()

        tk.Label(
            body,
            text="PASSWORD",
            font=(FONT, 8, "bold"),
            fg=GRAY,
            bg=CARD_BG,
        ).pack(anchor="w", pady=(0, 6))
        self._var_pass = tk.StringVar()
        self._e_pass = _entry(body, self._var_pass, show="●")

        self._show_pw = tk.BooleanVar(value=False)
        tk.Checkbutton(
            body,
            text="Show password",
            variable=self._show_pw,
            command=self._toggle_pw,
            font=(FONT, 9),
            fg=GRAY,
            bg=CARD_BG,
            selectcolor=CARD_BG,
            activebackground=CARD_BG,
            activeforeground=TEXT,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        ).pack(anchor="w", pady=(7, 21))

        self._err_var = tk.StringVar()
        tk.Label(
            body,
            textvariable=self._err_var,
            font=(FONT, 9),
            fg=RED,
            bg=CARD_BG,
            wraplength=330,
            justify="left",
        ).pack(anchor="w", pady=(0, 9))

        _btn(body, "Sign In", PURPLE, PURPLE_DARK, self._login)

        # Hint
        hint = tk.Frame(body, bg=PURPLE_SOFT, padx=12, pady=10)
        hint.pack(fill="x", pady=(19, 0))
        tk.Label(
            hint,
            text="Demo access",
            font=(FONT, 8, "bold"),
            fg=PURPLE_DARK,
            bg=PURPLE_SOFT,
        ).pack(anchor="w")
        tk.Label(
            hint,
            text=(
                "retailer1=BSL Pharmacy  |  retailer2=MedPlus  |  "
                "retailer3=Apollo  |  retailer4=Wellness"
            ),
            font=(FONT, 8),
            fg=GRAY,
            bg=PURPLE_SOFT,
            wraplength=330,
            justify="left",
        ).pack(anchor="w", pady=(3, 0))

        self._e_user.bind("<Return>", lambda e: self._e_pass.focus_set())
        self._e_pass.bind("<Return>", lambda e: self._login())
        self.after(100, self._e_user.focus_set)

    def _toggle_pw(self):
        self._e_pass.config(show="" if self._show_pw.get() else "●")

    def _login(self):
        username = self._var_user.get().strip()
        password = self._var_pass.get()
        self._err_var.set("")

        if not username:
            self._err_var.set("⚠ Username is required.")
            self._e_user.focus_set()
            return
        if not password:
            self._err_var.set("⚠ Password is required.")
            self._e_pass.focus_set()
            return

        # Authenticate against database
        retailer_id, full_name, error = self._authenticate(username, password)
        if error:
            self._err_var.set(f"⚠ {error}")
            self._var_pass.set("")
            self._e_pass.focus_set()
            return

        # Success — fire callback with (username, password, retailer_id, full_name)
        if self.on_login:
            self.on_login(username, password, retailer_id, full_name)
        elif self.app and hasattr(self.app, "do_login"):
            self.app.do_login(username, password, retailer_id, full_name)

    def _authenticate(self, username: str, password: str):
        """
        Returns (retailer_id, full_name, None) on success,
                (None, None, error_message) on failure.
        """
        try:
            import pymysql
            from ...config import load_config
            cfg = load_config()
            conn = pymysql.connect(
                host=cfg.db_host, port=cfg.db_port,
                user=cfg.db_user, password=cfg.db_password,
                database=cfg.db_name, charset="utf8mb4",
                connect_timeout=5,
            )
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT retailer_id, full_name FROM retailer_users "
                    "WHERE username=%s AND password=%s AND is_active=1 LIMIT 1",
                    (username, password),
                )
                row = cur.fetchone()
            conn.close()
            if row:
                return row[0], row[1] or username, None
            return None, None, "Invalid username or password."
        except Exception as e:
            return None, None, f"DB error: {e}"
