"""Purchase Payment Dialog — Supplier-wise payment with distribution & overpayment advance."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import re

from ...styles import FONT

P = {
    "bg": "#f0f9ff", "card": "#ffffff", "border": "#bae6fd",
    "head_bg": "#0ea5e9", "head_fg": "#ffffff", "lbl": "#0c4a6e",
    "input_bg": "#ffffff", "input_fg": "#0f172a", "input_brd": "#7dd3fc",
    "focus": "#0ea5e9", "green": "#16a34a", "green_lt": "#dcfce7",
    "red": "#dc2626", "red_lt": "#fee2e2", "orange": "#d97706",
    "orange_lt": "#fef3c7", "purple": "#7c3aed", "purple_lt": "#ede9fe",
    "muted": "#64748b", "row_a": "#f0f9ff", "row_b": "#ffffff",
    "paid_bg": "#dcfce7", "paid_fg": "#15803d",
    "pend_bg": "#fef3c7", "pend_fg": "#b45309",
}

MODES = ["Cash", "Cheque", "Bank Transfer", "UPI", "Card", "NEFT", "RTGS"]


def _fmt(v):
    try:
        return f"Rs {float(v):,.2f}"
    except Exception:
        return "Rs 0.00"


class DateEntry(tk.Frame):
    def __init__(self, parent, textvariable=None, width=13, **kw):
        super().__init__(parent, bg=kw.get("bg", P["card"]))
        self._var = textvariable or tk.StringVar(value=date.today().isoformat())
        self._entry = tk.Entry(self, textvariable=self._var, font=FONT["base"],
                               width=width, relief="solid", bd=1,
                               bg=P["input_bg"], fg=P["input_fg"],
                               insertbackground=P["input_fg"],
                               highlightthickness=2,
                               highlightbackground=P["input_brd"],
                               highlightcolor=P["focus"])
        self._entry.pack(side="left")
        tk.Button(self, text="📅", font=("Segoe UI", 9),
                  bg=P["head_bg"], fg="white", relief="flat", bd=0,
                  padx=5, pady=2, cursor="hand2",
                  command=self._pick).pack(side="left", padx=(2, 0))
        self._entry.bind("<FocusOut>", self._normalize)
        self._entry.bind("<Return>", self._normalize)

    def get(self): return self._var.get()
    def set(self, v): self._var.set(v)
    def focus(self): self._entry.focus_set()

    def _normalize(self, e=None):
        v = self._var.get().strip()
        for pat, fn in [
            (r"^(\d{2})[/\-\.](\d{2})[/\-\.](\d{4})$",
             lambda m: f"{m.group(3)}-{m.group(2)}-{m.group(1)}"),
            (r"^(\d{4})[/\-\.](\d{2})[/\-\.](\d{2})$",
             lambda m: f"{m.group(1)}-{m.group(2)}-{m.group(3)}"),
        ]:
            m = re.match(pat, v)
            if m:
                self._var.set(fn(m))
                return

    def _pick(self):
        _CalPop(self, self._var)


class _CalPop(tk.Toplevel):
    def __init__(self, parent, var):
        super().__init__(parent)
        self.var = var
        self.overrideredirect(True)
        self.configure(bg=P["border"])
        try:
            y, mo, d = map(int, var.get().split("-"))
        except Exception:
            t = date.today(); y, mo, d = t.year, t.month, t.day
        self._y = y; self._m = mo; self._d = d
        self._build()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty() + parent.winfo_height() + 2
        self.geometry(f"+{px}+{py}")
        self.grab_set()
        self.bind("<Escape>", lambda e: self.destroy())
        self.focus_force()

    def _build(self):
        nav = tk.Frame(self, bg=P["head_bg"], padx=4, pady=4)
        nav.pack(fill="x")
        tk.Button(nav, text=" < ", bg=P["head_bg"], fg="white",
                  relief="flat", bd=0, font=FONT["bold"],
                  cursor="hand2", command=self._prev).pack(side="left")
        self._lbl = tk.Label(nav, bg=P["head_bg"], fg="white",
                             font=FONT["bold"], width=16)
        self._lbl.pack(side="left", expand=True)
        tk.Button(nav, text=" > ", bg=P["head_bg"], fg="white",
                  relief="flat", bd=0, font=FONT["bold"],
                  cursor="hand2", command=self._next).pack(side="right")
        self._grid = tk.Frame(self, bg=P["card"], padx=4, pady=4)
        self._grid.pack()
        self._draw()

    def _draw(self):
        import calendar
        for w in self._grid.winfo_children():
            w.destroy()
        for i, d in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
            tk.Label(self._grid, text=d, font=FONT["sm"], width=3,
                     bg=P["card"], fg=P["muted"]).grid(row=0, column=i, padx=1, pady=1)
        self._lbl.config(text=f"{calendar.month_abbr[self._m]}  {self._y}")
        for r, week in enumerate(calendar.monthcalendar(self._y, self._m), 1):
            for c, day in enumerate(week):
                if day == 0:
                    tk.Label(self._grid, text="", bg=P["card"], width=3).grid(row=r, column=c)
                    continue
                sel = day == self._d
                bg = P["head_bg"] if sel else (P["row_a"] if r % 2 else P["row_b"])
                fg = "white" if sel else P["lbl"]
                tk.Button(self._grid, text=str(day), width=3, relief="flat",
                          bg=bg, fg=fg, font=FONT["sm"], cursor="hand2",
                          activebackground=P["focus"], activeforeground="white",
                          command=lambda d=day: self._sel(d)).grid(
                    row=r, column=c, padx=1, pady=1)

    def _prev(self):
        self._m -= 1
        if self._m == 0: self._m = 12; self._y -= 1
        self._draw()

    def _next(self):
        self._m += 1
        if self._m == 13: self._m = 1; self._y += 1
        self._draw()

    def _sel(self, day):
        self.var.set(f"{self._y}-{self._m:02d}-{day:02d}")
        self.destroy()


class PurchasePaymentDialog(tk.Toplevel):
    """Supplier-wise payment: auto-distributes oldest invoice first, stores overpayment as advance."""

    def __init__(self, parent, app, invoice_id: int, invoice_no: str, on_saved=None,
                 preselect_supplier_id=None, preselect_supplier_name=""):
        super().__init__(parent)
        self.app = app
        self.db = app.db
        self.invoice_id = invoice_id
        self.invoice_no = invoice_no
        self.on_saved = on_saved
        self._supplier_id = preselect_supplier_id
        self._supplier_name = preselect_supplier_name
        self._pending_invoices = []
        self._bulk_vars = []
        self._sup_var = tk.StringVar(value=preselect_supplier_name)

        self.title("Purchase Payment")
        self.state("zoomed")
        self.resizable(True, True)
        self.configure(bg=P["bg"])
        self.grab_set()
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Control-s>", lambda e: self._save_single())

        self._build()
        self._all_suppliers = self.db.get_suppliers_list()
        self._sup_combo["values"] = [s["supplier_name"] for s in self._all_suppliers]
        if self._supplier_name:
            self._sup_var.set(self._supplier_name)
        self._init_supplier()

    def _build(self):
        hdr = tk.Frame(self, bg=P["head_bg"], height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  Purchase Payment", font=FONT["h3"],
                 bg=P["head_bg"], fg="white").pack(side="left", padx=12)
        tk.Label(hdr, text="Ctrl+S = Save  |  Esc = Close",
                 font=FONT["sm"], bg=P["head_bg"], fg="#bae6fd").pack(side="left", padx=10)
        tk.Button(hdr, text="Esc  Close", bg="#0369a1", fg="white",
                  font=FONT["sm"], relief="flat", bd=0, padx=12, pady=4,
                  cursor="hand2", command=self.destroy).pack(side="right", padx=8, pady=8)

        # Supplier selector bar
        sel_bar = tk.Frame(self, bg=P["card"], pady=8,
                           highlightthickness=1, highlightbackground=P["border"])
        sel_bar.pack(fill="x", padx=12, pady=(4, 0))
        tk.Label(sel_bar, text="Select Supplier:", font=FONT["bold"],
                 bg=P["card"], fg=P["lbl"]).pack(side="left", padx=(12, 6))
        self._sup_combo = ttk.Combobox(sel_bar, textvariable=self._sup_var,
                                        font=FONT["base"], width=32, state="normal")
        self._sup_combo.pack(side="left", padx=(0, 8))
        self._sup_combo.bind("<<ComboboxSelected>>", self._on_supplier_select)
        self._sup_combo.bind("<Return>", self._on_supplier_select)
        self._sup_combo.bind("<KeyRelease>", self._filter_supplier_list)
        tk.Button(sel_bar, text="Load", font=FONT["sm"],
                  bg=P["head_bg"], fg="white", relief="flat", bd=0,
                  padx=10, pady=3, cursor="hand2",
                  command=self._on_supplier_select).pack(side="left")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=12, pady=8)
        tab1 = tk.Frame(nb, bg=P["bg"])
        tab2 = tk.Frame(nb, bg=P["bg"])
        tab3 = tk.Frame(nb, bg=P["bg"])
        nb.add(tab1, text="  Single Payment  ")
        nb.add(tab2, text="  Bulk Payment  ")
        nb.add(tab3, text="  Payment History  ")
        self._build_single(tab1)
        self._build_bulk(tab2)
        self._build_history(tab3)

    def _card(self, parent, title, accent=None):
        f = tk.Frame(parent, bg=P["card"], relief="flat",
                     highlightthickness=1, highlightbackground=P["border"])
        f.pack(fill="x", padx=10, pady=(8, 4))
        tk.Frame(f, bg=accent or P["head_bg"], height=4).pack(fill="x")
        inner = tk.Frame(f, bg=P["card"], padx=16, pady=12)
        inner.pack(fill="x")
        if title:
            tk.Label(inner, text=title, font=FONT["bold"],
                     bg=P["card"], fg=accent or P["head_bg"]).grid(
                row=0, column=0, columnspan=6, sticky="w", pady=(0, 8))
        return inner

    def _ent(self, parent, var, w=18):
        return tk.Entry(parent, textvariable=var, font=FONT["base"], width=w,
                        relief="solid", bd=1, bg=P["input_bg"], fg=P["input_fg"],
                        insertbackground=P["input_fg"], highlightthickness=2,
                        highlightbackground=P["input_brd"], highlightcolor=P["focus"])

    def _lrow(self, frm, r, label, widget):
        tk.Label(frm, text=label, font=FONT["sm"], bg=P["card"],
                 fg=P["lbl"]).grid(row=r, column=0, sticky="w", pady=4, padx=(0, 10))
        if isinstance(widget, tk.Widget):
            widget.grid(row=r, column=1, sticky="w", pady=4, padx=(0, 20))
        else:
            tk.Label(frm, text=str(widget), font=FONT["bold"],
                     bg=P["card"], fg=P["lbl"]).grid(row=r, column=1, sticky="w", pady=4)

    def _build_single(self, parent):
        s = self._card(parent, "Supplier Summary", P["purple"])
        self._lbl_supplier = tk.Label(s, font=FONT["bold"], bg=P["card"], fg=P["lbl"])
        self._lbl_pending_count = tk.Label(s, font=FONT["bold"], bg=P["card"], fg=P["orange"])
        self._lbl_total_pending = tk.Label(s, font=FONT["bold"], bg=P["card"], fg=P["red"])
        self._lbl_advance = tk.Label(s, font=FONT["bold"], bg=P["card"], fg=P["green"])
        self._lrow(s, 1, "Supplier", self._lbl_supplier)
        self._lrow(s, 2, "Pending Invoices", self._lbl_pending_count)
        self._lrow(s, 3, "Total Pending Amount", self._lbl_total_pending)
        self._lrow(s, 4, "Advance Credit", self._lbl_advance)

        f = self._card(parent, "Record Payment  (auto-distributes oldest invoice first)", P["green"])
        self._var_date = tk.StringVar(value=date.today().isoformat())
        self._var_amount = tk.StringVar(value="0")
        self._var_mode = tk.StringVar(value="Cash")
        self._var_ref = tk.StringVar()
        self._var_notes = tk.StringVar()
        self._lrow(f, 1, "Payment Date *", DateEntry(f, textvariable=self._var_date, bg=P["card"]))
        self._lrow(f, 2, "Amount *", self._ent(f, self._var_amount, 16))
        tk.Label(f, text="Mode *", font=FONT["sm"], bg=P["card"],
                 fg=P["lbl"]).grid(row=3, column=0, sticky="w", pady=4, padx=(0, 10))
        ttk.Combobox(f, textvariable=self._var_mode, values=MODES,
                     font=FONT["base"], width=18, state="readonly").grid(
            row=3, column=1, sticky="w", pady=4)
        self._lrow(f, 4, "Reference No", self._ent(f, self._var_ref, 20))
        self._lrow(f, 5, "Notes", self._ent(f, self._var_notes, 28))
        self._dist_preview = tk.StringVar(value="")
        tk.Label(f, textvariable=self._dist_preview, font=FONT["sm"],
                 bg=P["card"], fg=P["muted"], wraplength=600, justify="left").grid(
            row=6, column=0, columnspan=4, sticky="w", pady=(4, 0))
        self._var_amount.trace_add("write", lambda *a: self._update_dist_preview())

        btn = tk.Frame(parent, bg=P["bg"])
        btn.pack(fill="x", padx=10, pady=8)
        tk.Button(btn, text="Ctrl+S   Save Payment", font=FONT["base"],
                  bg=P["green"], fg="white", relief="flat", bd=0,
                  padx=20, pady=8, cursor="hand2",
                  command=self._save_single).pack(side="right", padx=(6, 0))
        tk.Button(btn, text="Pay Full Pending", font=FONT["base"],
                  bg=P["orange"], fg="white", relief="flat", bd=0,
                  padx=14, pady=8, cursor="hand2",
                  command=self._fill_full).pack(side="right", padx=6)
        tk.Button(btn, text="Esc  Cancel", font=FONT["base"],
                  bg=P["muted"], fg="white", relief="flat", bd=0,
                  padx=14, pady=8, cursor="hand2",
                  command=self.destroy).pack(side="right")

    def _build_bulk(self, parent):
        info = tk.Frame(parent, bg=P["bg"], padx=10, pady=6)
        info.pack(fill="x")
        tk.Label(info, text="Enter custom amount per invoice. Unchecked invoices are skipped.",
                 font=FONT["sm"], bg=P["bg"], fg=P["muted"]).pack(side="left")
        tk.Button(info, text="Refresh", font=FONT["sm"],
                  bg=P["head_bg"], fg="white", relief="flat", bd=0,
                  padx=10, pady=3, cursor="hand2",
                  command=self._load_bulk).pack(side="right")

        cols_frm = tk.Frame(parent, bg=P["head_bg"])
        cols_frm.pack(fill="x", padx=10)
        for txt, w in [("Sel", 3), ("Invoice No", 14), ("Date", 12),
                       ("Total", 10), ("Paid", 10), ("Balance", 10), ("Pay Amount", 12)]:
            tk.Label(cols_frm, text=txt, font=FONT["bold"],
                     bg=P["head_bg"], fg="white", width=w, anchor="w",
                     padx=4, pady=6).pack(side="left")

        wrap = tk.Frame(parent, bg=P["bg"])
        wrap.pack(fill="both", expand=True, padx=10, pady=4)
        canvas = tk.Canvas(wrap, bg=P["bg"], highlightthickness=0)
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self._bulk_inner = tk.Frame(canvas, bg=P["bg"])
        self._bulk_canvas = canvas
        self._bulk_window = canvas.create_window((0, 0), window=self._bulk_inner, anchor="nw")
        self._bulk_inner.bind("<Configure>",
                              lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(self._bulk_window, width=e.width))
        canvas.bind("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        bf = tk.Frame(parent, bg=P["card"],
                      highlightthickness=1, highlightbackground=P["border"])
        bf.pack(fill="x", padx=10, pady=4)
        bfi = tk.Frame(bf, bg=P["card"], padx=12, pady=8)
        bfi.pack(fill="x")
        tk.Label(bfi, text="Payment Date *", font=FONT["sm"],
                 bg=P["card"], fg=P["lbl"]).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self._bulk_date_var = tk.StringVar(value=date.today().isoformat())
        DateEntry(bfi, textvariable=self._bulk_date_var,
                  bg=P["card"]).grid(row=0, column=1, sticky="w", padx=(0, 16), pady=4)
        tk.Label(bfi, text="Mode *", font=FONT["sm"],
                 bg=P["card"], fg=P["lbl"]).grid(row=0, column=2, sticky="w", padx=(0, 8), pady=4)
        self._bulk_mode_var = tk.StringVar(value="Cash")
        ttk.Combobox(bfi, textvariable=self._bulk_mode_var, values=MODES,
                     font=FONT["base"], width=14, state="readonly").grid(
            row=0, column=3, sticky="w", padx=(0, 16), pady=4)
        tk.Label(bfi, text="Reference", font=FONT["sm"],
                 bg=P["card"], fg=P["lbl"]).grid(row=0, column=4, sticky="w", padx=(0, 8))
        self._bulk_ref_var = tk.StringVar()
        tk.Entry(bfi, textvariable=self._bulk_ref_var, font=FONT["base"],
                 width=14, relief="solid", bd=1,
                 bg=P["input_bg"], fg=P["input_fg"]).grid(row=0, column=5, sticky="w")
        self._bulk_total_lbl = tk.StringVar(value="Total to Pay: Rs 0.00")
        tk.Label(bfi, textvariable=self._bulk_total_lbl, font=FONT["bold"],
                 bg=P["card"], fg=P["green"]).grid(
            row=1, column=0, columnspan=4, sticky="w", pady=(4, 0))
        tk.Button(bfi, text="Pay Selected Invoices", font=FONT["base"],
                  bg=P["green"], fg="white", relief="flat", bd=0,
                  padx=16, pady=6, cursor="hand2",
                  command=self._save_bulk).grid(row=1, column=4, columnspan=2, sticky="e", pady=4)

    def _build_history(self, parent):
        hdr = tk.Frame(parent, bg=P["bg"], padx=10, pady=6)
        hdr.pack(fill="x")
        tk.Label(hdr, text="All payments for this supplier's invoices",
                 font=FONT["sm"], bg=P["bg"], fg=P["muted"]).pack(side="left")
        tk.Button(hdr, text="Refresh", font=FONT["sm"],
                  bg=P["head_bg"], fg="white", relief="flat", bd=0,
                  padx=10, pady=3, cursor="hand2",
                  command=self._load_history).pack(side="right")
        cols = ("#", "Invoice No", "Date", "Amount", "Mode", "Reference")
        widths = (40, 130, 110, 100, 110, 150)
        frm = tk.Frame(parent, bg=P["bg"])
        frm.pack(fill="both", expand=True, padx=10, pady=4)
        vsb = ttk.Scrollbar(frm, orient="vertical")
        self._hist_tree = ttk.Treeview(frm, columns=cols, show="headings",
                                        yscrollcommand=vsb.set, selectmode="browse")
        vsb.config(command=self._hist_tree.yview)
        for col, w in zip(cols, widths):
            self._hist_tree.heading(col, text=col)
            self._hist_tree.column(col, width=w, anchor="center", minwidth=40)
        self._hist_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._hist_tree.bind("<Delete>", lambda e: self._delete_payment())
        df = tk.Frame(parent, bg=P["bg"], padx=10, pady=4)
        df.pack(fill="x")
        tk.Button(df, text="Delete Selected Payment", font=FONT["sm"],
                  bg=P["red"], fg="white", relief="flat", bd=0,
                  padx=12, pady=5, cursor="hand2",
                  command=self._delete_payment).pack(side="right")
        tk.Label(df, text="Del = delete selected",
                 font=FONT["sm"], bg=P["bg"], fg=P["muted"]).pack(side="left")

    # ── Data loading ──────────────────────────────────────────────────────────

    def _init_supplier(self):
        try:
            if self.invoice_id and not self._supplier_id:
                inv = self.db.get_invoice(self.invoice_id)
                if inv:
                    self._supplier_id = inv.get("supplierid_id") or inv.get("supplierid")
                    self._supplier_name = inv.get("supplier_name", "")
                    self._sup_var.set(self._supplier_name)
        except Exception:
            pass
        if self._supplier_id:
            self._load_all()

    def _filter_supplier_list(self, event=None):
        typed = self._sup_var.get().lower()
        filtered = [s["supplier_name"] for s in self._all_suppliers
                    if typed in s["supplier_name"].lower()]
        self._sup_combo["values"] = filtered
        if filtered:
            self._sup_combo.event_generate("<<ComboboxSelected>>" if not typed else "")

    def _on_supplier_select(self, event=None):
        name = self._sup_var.get().strip()
        for s in self._all_suppliers:
            if s["supplier_name"] == name:
                self._supplier_id = s["supplierid"]
                self._supplier_name = name
                self._load_all()
                return

    def _load_all(self):
        self._load_summary()
        self._load_bulk()
        self._load_history()

    def _load_summary(self):
        try:
            if not self._supplier_id:
                return
            self._pending_invoices = self.db.get_supplier_pending_invoices(self._supplier_id)
            total_pending = sum(float(r["balance"]) for r in self._pending_invoices)
            advance = self.db.get_supplier_advance_balance(self._supplier_id)
            self._lbl_supplier.config(text=self._supplier_name)
            self._lbl_pending_count.config(text=f"{len(self._pending_invoices)} invoice(s)")
            self._lbl_total_pending.config(text=_fmt(total_pending))
            self._lbl_advance.config(text=_fmt(advance))
            self._update_dist_preview()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _update_dist_preview(self):
        try:
            amount = float(self._var_amount.get() or 0)
            if amount <= 0 or not self._pending_invoices:
                self._dist_preview.set("")
                return
            advance = self.db.get_supplier_advance_balance(self._supplier_id)
            remaining = round(amount + advance, 2)
            lines = []
            for inv in self._pending_invoices:
                if remaining <= 0:
                    break
                bal = round(float(inv["balance"]), 2)
                pay = min(remaining, bal)
                lines.append(f"{inv['invoice_no']}: {_fmt(pay)}")
                remaining = round(remaining - pay, 2)
            preview = "Distribution: " + "  |  ".join(lines)
            if remaining > 0.01:
                preview += f"  |  Advance stored: {_fmt(remaining)}"
            self._dist_preview.set(preview)
        except Exception:
            self._dist_preview.set("")

    def _load_bulk(self):
        for w in self._bulk_inner.winfo_children():
            w.destroy()
        self._bulk_vars = []
        try:
            if not self._supplier_id:
                return
            rows = self.db.get_supplier_pending_invoices(self._supplier_id)
            for i, r in enumerate(rows):
                balance = round(float(r["balance"]), 2)
                bg = P["row_a"] if i % 2 else P["row_b"]
                row_frm = tk.Frame(self._bulk_inner, bg=bg)
                row_frm.pack(fill="x", pady=1)
                check_var = tk.BooleanVar(value=(r["invoiceid"] == self.invoice_id))
                amount_var = tk.StringVar(value=f"{balance:.2f}")
                tk.Checkbutton(row_frm, variable=check_var, bg=bg,
                               command=self._update_bulk_total).pack(side="left", padx=4)
                for txt, w in [(r.get("invoice_no", ""), 14),
                               (str(r.get("invoice_date", ""))[:10], 12),
                               (_fmt(float(r.get("invoice_total", 0))), 10),
                               (_fmt(float(r.get("invoice_paid", 0))), 10),
                               (_fmt(balance), 10)]:
                    tk.Label(row_frm, text=txt, font=FONT["sm"], bg=bg,
                             fg=P["lbl"], width=w, anchor="w", padx=4).pack(side="left")
                amt_e = tk.Entry(row_frm, textvariable=amount_var,
                                 font=FONT["sm"], width=12, relief="solid", bd=1,
                                 bg=P["input_bg"], fg=P["input_fg"])
                amt_e.pack(side="left", padx=4)
                amt_e.bind("<FocusOut>", lambda e: self._update_bulk_total())
                self._bulk_vars.append((r["invoiceid"], r.get("invoice_no", ""),
                                        balance, amount_var, check_var))
            self._update_bulk_total()
            self._bulk_inner.update_idletasks()
            self._bulk_canvas.configure(scrollregion=self._bulk_canvas.bbox("all"))
        except Exception as e:
            tk.Label(self._bulk_inner, text=f"Error: {e}",
                     font=FONT["sm"], bg=P["bg"], fg=P["red"]).pack(padx=10, pady=6)

    def _update_bulk_total(self):
        total = 0.0
        for _, _, _, amt_var, chk_var in self._bulk_vars:
            if chk_var.get():
                try:
                    total += float(amt_var.get() or 0)
                except Exception:
                    pass
        self._bulk_total_lbl.set(f"Total to Pay: {_fmt(total)}")

    def _load_history(self):
        for i in self._hist_tree.get_children():
            self._hist_tree.delete(i)
        try:
            if not self._supplier_id:
                return
            rows = self.db.query(
                """SELECT ip.payment_id, i.invoice_no, ip.payment_date,
                          ip.payment_amount, ip.payment_mode, ip.payment_ref_no
                   FROM core_invoicepaid ip
                   JOIN core_invoicemaster i ON i.invoiceid = ip.ip_invoiceid_id
                   WHERE i.supplierid_id=%s AND i.retailer_id=%s
                   ORDER BY ip.payment_date DESC, ip.payment_id DESC LIMIT 200""",
                (self._supplier_id, self.db.config.retailer_id)
            )
            for idx, p in enumerate(rows, 1):
                self._hist_tree.insert("", "end",
                    iid=str(p["payment_id"]),
                    values=(idx,
                            p.get("invoice_no", ""),
                            str(p.get("payment_date", ""))[:10],
                            _fmt(p.get("payment_amount", 0)),
                            p.get("payment_mode", ""),
                            p.get("payment_ref_no", "") or ""))
        except Exception:
            pass

    # ── Actions ───────────────────────────────────────────────────────────────

    def _fill_full(self):
        try:
            total = sum(float(r["balance"]) for r in self._pending_invoices)
            self._var_amount.set(f"{max(0, total):.2f}")
        except Exception:
            pass

    def _save_single(self):
        try:
            amount = float(self._var_amount.get() or 0)
            if amount <= 0:
                raise ValueError("Amount must be > 0.")
            pay_date = self._var_date.get().strip()
            if not pay_date:
                raise ValueError("Payment date required.")
            if not self._supplier_id:
                raise ValueError("Supplier not found.")
            result = self.db.distribute_supplier_payment(
                self._supplier_id, pay_date, amount,
                self._var_mode.get(), self._var_ref.get().strip(),
                self._var_notes.get().strip()
            )
            msg = f"Payment of {_fmt(amount)} recorded.\n{result['invoices_paid']} invoice(s) updated."
            if result['advance_stored'] > 0.01:
                msg += f"\nAdvance stored: {_fmt(result['advance_stored'])}"
            messagebox.showinfo("Saved", msg, parent=self)
            self._load_all()
            if self.on_saved:
                self.on_saved()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _save_bulk(self):
        selected = [(inv_id, inv_no, amt_var)
                    for inv_id, inv_no, _, amt_var, chk_var in self._bulk_vars
                    if chk_var.get()]
        if not selected:
            messagebox.showwarning("Bulk Payment", "Select at least one invoice.", parent=self)
            return
        pay_date = self._bulk_date_var.get().strip()
        mode = self._bulk_mode_var.get()
        ref = self._bulk_ref_var.get().strip()
        if not pay_date:
            messagebox.showwarning("Bulk Payment", "Payment date required.", parent=self)
            return
        saved, errors = 0, []
        for inv_id, inv_no, amt_var in selected:
            try:
                amount = float(amt_var.get() or 0)
                if amount <= 0:
                    continue
                self.db.add_invoice_payment(inv_id, pay_date, amount, mode, ref)
                saved += 1
            except Exception as e:
                errors.append(f"{inv_no}: {e}")
        msg = f"Paid {saved} invoice(s)."
        if errors:
            msg += "\n\nErrors:\n" + "\n".join(errors)
        messagebox.showinfo("Bulk Payment", msg, parent=self)
        self._load_all()
        if self.on_saved:
            self.on_saved()

    def _delete_payment(self):
        sel = self._hist_tree.focus()
        if not sel:
            return
        if messagebox.askyesno("Delete Payment", "Delete this payment? Cannot be undone.", parent=self):
            try:
                self.db.delete_invoice_payment(int(sel))
                self._load_all()
                if self.on_saved:
                    self.on_saved()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self)

    def _build_single(self, parent):
        s = self._card(parent, "Supplier Summary", P["purple"])
        self._lbl_supplier = tk.Label(s, font=FONT["bold"], bg=P["card"], fg=P["lbl"])
        self._lbl_pending_count = tk.Label(s, font=FONT["bold"], bg=P["card"], fg=P["orange"])
        self._lbl_total_pending = tk.Label(s, font=FONT["bold"], bg=P["card"], fg=P["red"])
        self._lbl_advance = tk.Label(s, font=FONT["bold"], bg=P["card"], fg=P["green"])
        self._lrow(s, 1, "Supplier", self._lbl_supplier)
        self._lrow(s, 2, "Pending Invoices", self._lbl_pending_count)
        self._lrow(s, 3, "Total Pending Amount", self._lbl_total_pending)
        self._lrow(s, 4, "Advance Credit", self._lbl_advance)

        f = self._card(parent, "Record Payment  (auto-distributes oldest invoice first)", P["green"])
        self._var_date = tk.StringVar(value=date.today().isoformat())
        self._var_amount = tk.StringVar(value="0")
        self._var_mode = tk.StringVar(value="Cash")
        self._var_ref = tk.StringVar()
        self._var_notes = tk.StringVar()
        self._lrow(f, 1, "Payment Date *", DateEntry(f, textvariable=self._var_date, bg=P["card"]))
        self._lrow(f, 2, "Amount *", self._ent(f, self._var_amount, 16))
        tk.Label(f, text="Mode *", font=FONT["sm"], bg=P["card"],
                 fg=P["lbl"]).grid(row=3, column=0, sticky="w", pady=4, padx=(0, 10))
        ttk.Combobox(f, textvariable=self._var_mode, values=MODES,
                     font=FONT["base"], width=18, state="readonly").grid(
            row=3, column=1, sticky="w", pady=4)
        self._lrow(f, 4, "Reference No", self._ent(f, self._var_ref, 20))
        self._lrow(f, 5, "Notes", self._ent(f, self._var_notes, 28))
        self._dist_preview = tk.StringVar(value="")
        tk.Label(f, textvariable=self._dist_preview, font=FONT["sm"],
                 bg=P["card"], fg=P["muted"], wraplength=600, justify="left").grid(
            row=6, column=0, columnspan=4, sticky="w", pady=(4, 0))
        self._var_amount.trace_add("write", lambda *a: self._update_dist_preview())

        btn = tk.Frame(parent, bg=P["bg"])
        btn.pack(fill="x", padx=10, pady=8)
        tk.Button(btn, text="Ctrl+S   Save Payment", font=FONT["base"],
                  bg=P["green"], fg="white", relief="flat", bd=0,
                  padx=20, pady=8, cursor="hand2",
                  command=self._save_single).pack(side="right", padx=(6, 0))
        tk.Button(btn, text="Pay Full Pending", font=FONT["base"],
                  bg=P["orange"], fg="white", relief="flat", bd=0,
                  padx=14, pady=8, cursor="hand2",
                  command=self._fill_full).pack(side="right", padx=6)
        tk.Button(btn, text="Esc  Cancel", font=FONT["base"],
                  bg=P["muted"], fg="white", relief="flat", bd=0,
                  padx=14, pady=8, cursor="hand2",
                  command=self.destroy).pack(side="right")
