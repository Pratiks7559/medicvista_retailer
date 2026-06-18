import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from ...styles import COLORS


class ProfileScreen(tk.Frame):
    def __init__(self, parent, app_instance=None, **kwargs):
        super().__init__(parent, bg=COLORS["bg_light"], **kwargs)
        self.app = app_instance
        self._user_data = {}
        self._build()

    def _build(self):
        tk.Label(self, text="Retailer Profile", font=("Segoe UI", 16, "bold"),
                 fg=COLORS["dark_text"], bg=COLORS["bg_light"]).pack(anchor="w", pady=(0, 16))

        card = tk.Frame(self, bg=COLORS["white"], padx=28, pady=24)
        card.pack(fill="x", padx=0, pady=0)

        # Read-only fields
        ro_fields = [("Username", "username"), ("User Type", "user_type")]
        for label, key in ro_fields:
            row = tk.Frame(card, bg=COLORS["white"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, width=18, anchor="w", font=("Segoe UI", 10),
                     fg=COLORS["gray_text"], bg=COLORS["white"]).pack(side="left")
            var = tk.StringVar(value="—")
            setattr(self, f"_var_{key}", var)
            tk.Label(row, textvariable=var, font=("Segoe UI", 10, "bold"),
                     fg=COLORS["dark_text"], bg=COLORS["white"]).pack(side="left")

        ttk.Separator(card, orient="horizontal").pack(fill="x", pady=12)

        # Editable fields
        ed_fields = [("Contact", "user_contact"), ("Email", "email")]
        self._entries = {}
        for label, key in ed_fields:
            row = tk.Frame(card, bg=COLORS["white"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, width=18, anchor="w", font=("Segoe UI", 10),
                     fg=COLORS["gray_text"], bg=COLORS["white"]).pack(side="left")
            var = tk.StringVar()
            self._entries[key] = var
            tk.Entry(row, textvariable=var, font=("Segoe UI", 10), width=32,
                     relief="solid", bd=1, bg=COLORS["bg_light"],
                     fg=COLORS["dark_text"], insertbackground=COLORS["dark_text"]).pack(side="left")

        # Profile picture
        row = tk.Frame(card, bg=COLORS["white"])
        row.pack(fill="x", pady=4)
        tk.Label(row, text="Profile Picture", width=18, anchor="w", font=("Segoe UI", 10),
                 fg=COLORS["gray_text"], bg=COLORS["white"]).pack(side="left")
        self._var_profile_picture = tk.StringVar()
        tk.Entry(row, textvariable=self._var_profile_picture, font=("Segoe UI", 10),
                 width=24, relief="solid", bd=1, bg=COLORS["bg_light"],
                 fg=COLORS["dark_text"], insertbackground=COLORS["dark_text"],
                 state="readonly").pack(side="left")
        tk.Button(row, text="Browse", bg=COLORS["purple"], fg="white",
                  font=("Segoe UI", 9), bd=0, relief="flat", padx=8, pady=3,
                  cursor="hand2", command=self._browse_picture).pack(side="left", padx=6)

        ttk.Separator(card, orient="horizontal").pack(fill="x", pady=12)

        btn_row = tk.Frame(card, bg=COLORS["white"])
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="💾 Update Profile", bg=COLORS["green"], fg="white",
                  font=("Segoe UI", 10), bd=0, relief="flat", padx=16, pady=6,
                  cursor="hand2", command=self._update).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="🔑 Change Password", bg=COLORS["orange"], fg="white",
                  font=("Segoe UI", 10), bd=0, relief="flat", padx=16, pady=6,
                  cursor="hand2", command=self._change_password).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="⏻ Logout", bg=COLORS["logout_red"], fg="white",
                  font=("Segoe UI", 10), bd=0, relief="flat", padx=16, pady=6,
                  cursor="hand2", command=self._logout).pack(side="right")

    def on_show(self):
        if self.app and hasattr(self.app, "db"):
            try:
                rows = self.app.db.query(
                    "SELECT username, user_type, user_contact, email, profile_picture "
                    "FROM core_web_user WHERE id=%s LIMIT 1",
                    (self.app.config_data.retailer_id,))
                if rows:
                    self._user_data = rows[0]
                    self._var_username.set(rows[0].get("username", ""))
                    self._var_user_type.set(rows[0].get("user_type", ""))
                    self._entries["user_contact"].set(rows[0].get("user_contact", "") or "")
                    self._entries["email"].set(rows[0].get("email", "") or "")
                    self._var_profile_picture.set(rows[0].get("profile_picture", "") or "")
            except Exception:
                pass

    def _browse_picture(self):
        path = filedialog.askopenfilename(
            title="Select Profile Picture",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All Files", "*.*")])
        if path:
            self._var_profile_picture.set(path)

    def _update(self):
        if not self.app or not hasattr(self.app, "db"):
            return
        try:
            self.app.db.execute(
                "UPDATE core_web_user SET user_contact=%s, email=%s, profile_picture=%s WHERE id=%s",
                (self._entries["user_contact"].get().strip(),
                 self._entries["email"].get().strip(),
                 self._var_profile_picture.get().strip(),
                 self.app.config_data.retailer_id))
            messagebox.showinfo("Success", "Profile updated successfully.", parent=self)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _change_password(self):
        ChangePasswordDialog(self, self.app)

    def _logout(self):
        if self.app and hasattr(self.app, "close_app"):
            self.app.close_app()


class ChangePasswordDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("Change Password")
        self.geometry("360x260")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        frm = tk.Frame(self, padx=24, pady=20, bg=COLORS["white"])
        frm.pack(fill="both", expand=True)

        fields = [("Current Password", "_var_old"), ("New Password", "_var_new"),
                  ("Confirm New Password", "_var_confirm")]
        for label, attr in fields:
            tk.Label(frm, text=label, font=("Segoe UI", 10),
                     fg=COLORS["gray_text"], bg=COLORS["white"]).pack(anchor="w", pady=(6, 1))
            var = tk.StringVar()
            setattr(self, attr, var)
            tk.Entry(frm, textvariable=var, show="●", font=("Segoe UI", 10),
                     width=30, relief="solid", bd=1,
                     bg=COLORS["bg_light"], fg=COLORS["dark_text"],
                     insertbackground=COLORS["dark_text"]).pack(fill="x")

        btn = tk.Frame(frm, bg=COLORS["white"])
        btn.pack(fill="x", pady=(16, 0))
        tk.Button(btn, text="Update Password", bg=COLORS["green"], fg="white",
                  font=("Segoe UI", 10), bd=0, relief="flat", padx=14, pady=6,
                  cursor="hand2", command=self._save).pack(side="right")
        tk.Button(btn, text="Cancel", bg=COLORS["gray_text"], fg="white",
                  font=("Segoe UI", 10), bd=0, relief="flat", padx=10, pady=6,
                  cursor="hand2", command=self.destroy).pack(side="right", padx=8)

    def _save(self):
        old = self._var_old.get()
        new = self._var_new.get()
        confirm = self._var_confirm.get()
        if not old or not new:
            messagebox.showwarning("Validation", "All fields are required.", parent=self)
            return
        if new != confirm:
            messagebox.showwarning("Validation", "New passwords do not match.", parent=self)
            return
        if len(new) < 6:
            messagebox.showwarning("Validation", "Password must be at least 6 characters.", parent=self)
            return
        try:
            import hashlib
            hashed = hashlib.sha256(new.encode()).hexdigest()
            self.app.db.execute(
                "UPDATE core_web_user SET password=%s WHERE id=%s",
                (hashed, self.app.config_data.retailer_id))
            messagebox.showinfo("Success", "Password changed successfully.", parent=self)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
