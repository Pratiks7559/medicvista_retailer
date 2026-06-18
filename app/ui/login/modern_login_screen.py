import tkinter as tk
from ...styles import COLORS

BG      = "#f0f4ff"
CARD_BG = "#ffffff"
PURPLE  = "#6366f1"
PURPLE2 = "#4f46e5"
GRAY    = "#64748b"
MUTED   = "#94a3b8"
RED     = "#ef4444"
BORDER  = "#e2e8f0"


def _btn(parent, text, bg, hover, cmd):
    b = tk.Button(parent, text=text, bg=bg, fg="white",
                  font=("Segoe UI", 11, "bold"), bd=0, relief="flat",
                  cursor="hand2", activebackground=hover,
                  activeforeground="white", command=cmd)
    b.pack(fill="x", ipady=10)
    b.bind("<Enter>", lambda e: b.config(bg=hover))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def _entry(parent, var, show=""):
    f = tk.Frame(parent, bg=BORDER, bd=0)
    f.pack(fill="x", pady=(0, 4))
    inner = tk.Frame(f, bg=CARD_BG, bd=0)
    inner.pack(fill="x", padx=1, pady=1)
    e = tk.Entry(inner, textvariable=var, show=show,
                 font=("Segoe UI", 11), bg=CARD_BG, fg="#1e293b",
                 insertbackground=PURPLE, relief="flat", bd=0)
    e.pack(fill="x", ipady=9, padx=12)
    e.bind("<FocusIn>",  lambda ev: f.config(bg=PURPLE))
    e.bind("<FocusOut>", lambda ev: f.config(bg=BORDER))
    return e


class ModernLoginScreen(tk.Frame):
    def __init__(self, parent, app_instance=None, on_login=None, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.app      = app_instance
        self.on_login = on_login
        self._build()

    def _build(self):
        self.configure(bg=BG)

        # Left decorative panel
        left = tk.Frame(self, bg=PURPLE, width=420)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="💊", font=("Segoe UI", 64),
                 bg=PURPLE, fg="white").place(relx=0.5, rely=0.38, anchor="center")
        tk.Label(left, text="MedicVista", font=("Segoe UI", 26, "bold"),
                 bg=PURPLE, fg="white").place(relx=0.5, rely=0.52, anchor="center")
        tk.Label(left, text="Pharmacy ERP", font=("Segoe UI", 13),
                 bg=PURPLE, fg="#c7d2fe").place(relx=0.5, rely=0.59, anchor="center")
        tk.Label(left, text="Efficient · Reliable · Modern",
                 font=("Segoe UI", 10, "italic"),
                 bg=PURPLE, fg="#a5b4fc").place(relx=0.5, rely=0.65, anchor="center")
        tk.Label(left, text="© 2025 MedicVista", font=("Segoe UI", 8),
                 bg=PURPLE, fg="#a5b4fc").place(relx=0.5, rely=0.94, anchor="center")

        # Right login panel
        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        card = tk.Frame(right, bg=CARD_BG, bd=0,
                        highlightthickness=1, highlightbackground=BORDER)
        card.place(relx=0.5, rely=0.5, anchor="center", width=380)

        tk.Frame(card, bg=PURPLE, height=5).pack(fill="x")

        body = tk.Frame(card, bg=CARD_BG, padx=36, pady=32)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Welcome back 👋", font=("Segoe UI", 20, "bold"),
                 fg="#1e293b", bg=CARD_BG).pack(anchor="w")
        tk.Label(body, text="Sign in to your retailer account",
                 font=("Segoe UI", 10), fg=MUTED, bg=CARD_BG).pack(anchor="w", pady=(2, 24))

        tk.Label(body, text="Username", font=("Segoe UI", 9, "bold"),
                 fg=GRAY, bg=CARD_BG).pack(anchor="w", pady=(0, 4))
        self._var_user = tk.StringVar()
        self._e_user = _entry(body, self._var_user)

        tk.Frame(body, bg=BG, height=10).pack()

        tk.Label(body, text="Password", font=("Segoe UI", 9, "bold"),
                 fg=GRAY, bg=CARD_BG).pack(anchor="w", pady=(0, 4))
        self._var_pass = tk.StringVar()
        self._e_pass = _entry(body, self._var_pass, show="●")

        self._show_pw = tk.BooleanVar(value=False)
        tk.Checkbutton(body, text="Show password", variable=self._show_pw,
                       command=self._toggle_pw, font=("Segoe UI", 9),
                       fg=MUTED, bg=CARD_BG, selectcolor=CARD_BG,
                       activebackground=CARD_BG, bd=0,
                       highlightthickness=0, cursor="hand2").pack(anchor="w", pady=(6, 20))

        self._err_var = tk.StringVar()
        tk.Label(body, textvariable=self._err_var, font=("Segoe UI", 9),
                 fg=RED, bg=CARD_BG).pack(anchor="w", pady=(0, 8))

        _btn(body, "Sign In", PURPLE, PURPLE2, self._login)

        # Hint
        hint = tk.Frame(body, bg=CARD_BG)
        hint.pack(fill="x", pady=(16, 0))
        tk.Label(hint, text="retailer1=BSL Pharmacy  |  retailer2=MedPlus  |  retailer3=Apollo  |  retailer4=Wellness",
                 font=("Segoe UI", 8), fg=MUTED, bg=CARD_BG).pack(anchor="w")

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
