import tkinter as tk
from tkinter import ttk, messagebox
from ...styles import COLORS
from ...modern_ui_components import ModernButton, ModernEntry, ModernFrame, ModernLabel


class LoginScreen(tk.Frame):
    def __init__(self, parent, app_instance=None, on_login=None, **kwargs):
        super().__init__(parent, bg=COLORS["bg_light"], **kwargs)
        self.app = app_instance
        self.on_login = on_login
        self._build()

    def _build(self):
        container = tk.Frame(self, bg=COLORS["bg_light"])
        container.place(relx=0.5, rely=0.5, anchor="center")

        ModernLabel(container, text="💊 MedicVista", variant="h1",
                    fg=COLORS["purple"], bg=COLORS["bg_light"]).grid(row=0, column=0, columnspan=2, pady=(0, 4))
        ModernLabel(container, text="Pharmacy Management System", variant="subtitle",
                    fg=COLORS["gray_text"], bg=COLORS["bg_light"]).grid(row=1, column=0, columnspan=2, pady=(0, 24))

        card = ModernFrame(container, title="Login")
        card.grid(row=2, column=0, columnspan=2, padx=6, pady=6)

        ModernLabel(card.content, text="Username", variant="subtitle",
                    bg=COLORS["white"]).grid(row=0, column=0, sticky="w", pady=(0, 6))
        self._var_user = tk.StringVar()
        ModernEntry(card.content, textvariable=self._var_user, width=30,
                    placeholder="Enter your username").grid(row=1, column=0, pady=(0, 16))

        ModernLabel(card.content, text="Password", variant="subtitle",
                    bg=COLORS["white"]).grid(row=2, column=0, sticky="w", pady=(0, 6))
        self._var_pass = tk.StringVar()
        self._pass_entry = ModernEntry(card.content, textvariable=self._var_pass,
                                       width=30, show="●",
                                       placeholder="Enter your password")
        self._pass_entry.grid(row=3, column=0, pady=(0, 12))

        self._show_pw = tk.BooleanVar(value=False)
        tk.Checkbutton(card, text="Show password", variable=self._show_pw,
                       command=self._toggle_pw, font=("Segoe UI", 9),
                       fg=COLORS["gray_text"], bg=COLORS["white"],
                       selectcolor=COLORS["white"], activebackground=COLORS["white"]).grid(
            row=4, column=0, sticky="w", pady=(0, 18))

        ModernButton(card.content, text="Login", variant="primary",
                     width=26, command=self._login).grid(row=5, column=0)

        self._pass_entry.bind("<Return>", lambda e: self._login())

    def _toggle_pw(self):
        self._pass_entry.config(show="" if self._show_pw.get() else "●")

    def _login(self):
        username = self._var_user.get().strip()
        password = self._var_pass.get()
        if not username or not password:
            messagebox.showwarning("Login", "Username and password are required.", parent=self)
            return
        if self.on_login:
            self.on_login(username, password)
        elif self.app and hasattr(self.app, "do_login"):
            self.app.do_login(username, password)
