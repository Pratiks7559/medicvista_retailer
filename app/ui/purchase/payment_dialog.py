"""Purchase Payment Dialog — Modern light UI, calendar + typing, normal + bulk payment."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import re

from ...styles import FONT

# ── Color palette ─────────────────────────────────────────────────────────────
P = {
    "bg":        "#f0f9ff",   # sky-50
    "card":      "#ffffff",
    "border":    "#bae6fd",   # sky-200
    "head_bg":   "#0ea5e9",   # sky-500
    "head_fg":   "#ffffff",
    "lbl":       "#0c4a6e",   # sky-900
    "input_bg":  "#ffffff",
    "input_fg":  "#0f172a",
    "input_brd": "#7dd3fc",   # sky-300
    "focus":     "#0ea5e9",
    "green":     "#16a34a",
    "green_lt":  "#dcfce7",
    "red":       "#dc2626",
    "red_lt":    "#fee2e2",
    "orange":    "#d97706",
    "orange_lt": "#fef3c7",
    "purple":    "#7c3aed",
    "purple_lt": "#ede9fe",
    "muted":     "#64748b",
    "row_a":     "#f0f9ff",
    "row_b":     "#ffffff",
    "paid_bg":   "#dcfce7",
    "paid_fg":   "#15803d",
    "pend_bg":   "#fef3c7",
    "pend_fg":   "#b45309",
}

MODES = ["Cash", "Cheque", "Bank Transfer", "UPI", "Card", "NEFT", "RTGS"]


def _fmt_inr(v):
    try:
        return f"Rs {float(v):,.2f}"
    except Exception:
        return "Rs 0.00"


# ── Shared DateEntry with calendar popup AND free typing ──────────────────────
class DateEntry(tk.Frame):
    """Date entry that allows both typing (YYYY-MM-DD) and calendar picking."""
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
        cal_btn = tk.Button(self, text="📅", font=("Segoe UI", 9),
                            bg=P["head_bg"], fg="white",
                            relief="flat", bd=0, padx=5, pady=2,
                            cursor="hand2", command=self._pick)
        cal_btn.pack(side="left", padx=(2, 0))
        self._entry.bind("<FocusOut>", self._normalize)
        self._entry.bind("<Return>",   self._normalize)

    def get(self):   return self._var.get()
    def set(self, v): self._var.set(v)
    def focus(self): self._entry.focus_set()

    def _normalize(self, e=None):
        """Accept dd-mm-yyyy, dd/mm/yyyy, ddmmyyyy, yyyymmdd → YYYY-MM-DD."""
        v = self._var.get().strip()
        for pat, fn in [
            (r"^(\d{2})[/\-\.](\d{2})[/\-\.](\d{4})$",
             lambda m: f"{m.group(3)}-{m.group(2)}-{m.group(1)}"),
            (r"^(\d{4})[/\-\.](\d{2})[/\-\.](\d{2})$",
             lambda m: f"{m.group(1)}-{m.group(2)}-{m.group(3)}"),
            (r"^(\d{2})(\d{2})(\d{4})$",
             lambda m: f"{m.group(3)}-{m.group(2)}-{m.group(1)}"),
            (r"^(\d{4})(\d{2})(\d{2})$",
             lambda m: f"{m.group(1)}-{m.group(2)}-{m.group(3)}"),
        ]:
            m = re.match(pat, v)
            if m:
                self._var.set(fn(m))
                return

    def _pick(self):
        _CalPop(self, self._var)


class _CalPop(tk.Toplevel):
    """Compact calendar popup."""
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
        self._lbl = tk.Label(nav, bg=P["head_bg"], fg="white", font=FONT["bold"], width=16)
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
        for i, d in enumerate(["Mo","Tu","We","Th","Fr","Sa","Su"]):
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


# ── Purchase Payment Dialog ────────────────────────────────────────────────────

class PurchasePaymentDialog(tk.Toplevel):
    def __init__(self, parent, app, invoice_id: int, invoice_no: str, on_saved=None):
        super().__init__(parent)
        self.app        = app
        self.db         = app.db
        self.invoice_id = invoice_id
        self.invoice_no = invoice_no
        self.on_saved   = on_saved

        self.title(f"Purchase Payment — {invoice_no}")
        self.state("zoomed")
        self.resizable(True, True)
        self.configure(bg=P["bg"])
        self.grab_set()
        self.bind("<Escape>",     lambda e: self.destroy())
        self.bind("<Control-s>",  lambda e: self._save_single())

        self._inv_data    = {}
        self._history     = []
        self._bulk_vars   = []   # list of (inv_id, inv_no, balance, amount_var, check_var)

        self._build()
        self._load()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        # header bar
        hdr = tk.Frame(self, bg=P["head_bg"], height=50)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="  Purchase Payment", font=FONT["h3"],
                 bg=P["head_bg"], fg="white").pack(side="left", padx=12)
        tk.Label(hdr, text="Ctrl+S = Save  |  Esc = Close",
                 font=FONT["sm"], bg=P["head_bg"], fg="#bae6fd").pack(side="left", padx=10)
        tk.Button(hdr, text="Esc  Close", bg="#0369a1", fg="white",
                  font=FONT["sm"], relief="flat", bd=0, padx=12, pady=4,
                  cursor="hand2", command=self.destroy).pack(side="right", padx=8, pady=8)

        # tabs
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
        bar = tk.Frame(f, bg=accent or P["head_bg"], height=4)
        bar.pack(fill="x")
        inner = tk.Frame(f, bg=P["card"], padx=16, pady=12)
        inner.pack(fill="x")
        if title:
            tk.Label(inner, text=title, font=FONT["bold"],
                     bg=P["card"], fg=accent or P["head_bg"]).grid(
                row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
        return inner

    def _row(self, frm, r, label, widget_or_text, readonly=False, color=None):
        tk.Label(frm, text=label, font=FONT["sm"], bg=P["card"],
                 fg=P["lbl"]).grid(row=r, column=0, sticky="w", pady=4, padx=(0, 10))
        if isinstance(widget_or_text, tk.Widget):
            widget_or_text.grid(row=r, column=1, sticky="w", pady=4, padx=(0, 20))
        else:
            tk.Label(frm, text=str(widget_or_text), font=FONT["bold"],
                     bg=P["card"], fg=color or P["lbl"]).grid(
                row=r, column=1, sticky="w", pady=4)

    def _ent(self, parent, var, w=20):
        return tk.Entry(parent, textvariable=var, font=FONT["base"], width=w,
                        relief="solid", bd=1, bg=P["input_bg"], fg=P["input_fg"],
                        insertbackground=P["input_fg"],
                        highlightthickness=2,
                        highlightbackground=P["input_brd"],
                        highlightcolor=P["focus"])

    def _build_single(self, parent):
        # summary card
        s = self._card(parent, "Invoice Summary", P["purple"])
        self._lbl_inv   = tk.Label(s, font=FONT["bold"], bg=P["card"], fg=P["lbl"])
        self._lbl_total = tk.Label(s, font=FONT["bold"], bg=P["card"], fg=P["lbl"])
        self._lbl_paid  = tk.Label(s, font=FONT["bold"], bg=P["card"], fg=P["green"])
        self._lbl_bal   = tk.Label(s, font=FONT["bold"], bg=P["card"], fg=P["red"])
        self._lbl_status = tk.Label(s, font=FONT["bold"], bg=P["card"])
        self._row(s, 1, "Invoice #",   self._lbl_inv)
        self._row(s, 2, "Total",       self._lbl_total)
        self._row(s, 3, "Paid",        self._lbl_paid)
        self._row(s, 4, "Balance Due", self._lbl_bal)
        self._row(s, 5, "Status",      self._lbl_status)

        # payment form card
        f = self._card(parent, "Record Payment", P["green"])
        self._var_date   = tk.StringVar(value=date.today().isoformat())
        self._var_amount = tk.StringVar(value="0")
        self._var_mode   = tk.StringVar(value="Cash")
        self._var_ref    = tk.StringVar()
        self._var_notes  = tk.StringVar()

        self._row(f, 1, "Payment Date *", DateEntry(f, textvariable=self._var_date, bg=P["card"]))
        self._row(f, 2, "Amount *",       self._ent(f, self._var_amount, 16))
        tk.Label(f, text="Mode *", font=FONT["sm"], bg=P["card"], fg=P["lbl"]).grid(
            row=3, column=0, sticky="w", pady=4, padx=(0, 10))
        ttk.Combobox(f, textvariable=self._var_mode, values=MODES,
                     font=FONT["base"], width=18, state="readonly").grid(
            row=3, column=1, sticky="w", pady=4)
        self._row(f, 4, "Reference No", self._ent(f, self._var_ref, 20))
        self._row(f, 5, "Notes",        self._ent(f, self._var_notes, 28))

        btn = tk.Frame(parent, bg=P["bg"])
        btn.pack(fill="x", padx=10, pady=8)
        tk.Button(btn, text="Ctrl+S   Save Payment", font=FONT["base"],
                  bg=P["green"], fg="white", relief="flat", bd=0,
                  padx=20, pady=8, cursor="hand2",
                  command=self._save_single).pack(side="right", padx=(6, 0))
        tk.Button(btn, text="Pay Full Balance", font=FONT["base"],
                  bg=P["orange"], fg="white", relief="flat", bd=0,
                  padx=14, pady=8, cursor="hand2",
                  command=self._fill_full).pack(side="right", padx=6)
        tk.Button(btn, text="Esc  Cancel", font=FONT["base"],
                  bg=P["muted"], fg="white", relief="flat", bd=0,
                  padx=14, pady=8, cursor="hand2",
                  command=self.destroy).pack(side="right")

    def _build_bulk(self, parent):
        """Bulk payment — pay multiple pending invoices of same supplier at once."""
        info = tk.Frame(parent, bg=P["bg"], padx=10, pady=6)
        info.pack(fill="x")
        tk.Label(info, text="Pay multiple pending invoices for this supplier at once.",
                 font=FONT["sm"], bg=P["bg"], fg=P["muted"]).pack(side="left")
        tk.Button(info, text="Refresh List", font=FONT["sm"],
                  bg=P["head_bg"], fg="white", relief="flat", bd=0,
                  padx=10, pady=3, cursor="hand2",
                  command=self._load_bulk).pack(side="right")

        # header
        cols_frm = tk.Frame(parent, bg=P["head_bg"])
        cols_frm.pack(fill="x", padx=10)
        for txt, w in [("", 3), ("Invoice No", 14), ("Date", 12),
                       ("Total", 10), ("Paid", 10), ("Balance", 10), ("Pay Amount", 12)]:
            tk.Label(cols_frm, text=txt if txt else "Sel", font=FONT["bold"],
                     bg=P["head_bg"], fg="white", width=w, anchor="w",
                     padx=4, pady=6).pack(side="left")

        # scrollable rows
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

        # bulk footer
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
        tk.Label(hdr, text="All payments for this invoice",
                 font=FONT["sm"], bg=P["bg"], fg=P["muted"]).pack(side="left")
        tk.Button(hdr, text="Refresh", font=FONT["sm"],
                  bg=P["head_bg"], fg="white", relief="flat", bd=0,
                  padx=10, pady=3, cursor="hand2",
                  command=self._load_history).pack(side="right")

        cols   = ("#", "Date", "Amount", "Mode", "Reference", "Action")
        widths = (40,  110,    100,      110,    150,          80)
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
        tk.Label(df, text="Del = delete selected payment",
                 font=FONT["sm"], bg=P["bg"], fg=P["muted"]).pack(side="left")

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load(self):
        self._load_invoice()
        self._load_bulk()
        self._load_history()

    def _load_invoice(self):
        try:
            inv = self.db.get_invoice(self.invoice_id)
            if inv:
                self._inv_data = inv
                total   = float(inv.get("invoice_total", 0) or 0)
                paid    = float(inv.get("invoice_paid",  0) or 0)
                balance = total - paid
                status  = (inv.get("payment_status") or "pending").capitalize()
                self._lbl_inv.config(text=self.invoice_no)
                self._lbl_total.config(text=_fmt_inr(total))
                self._lbl_paid.config(text=_fmt_inr(paid))
                self._lbl_bal.config(text=_fmt_inr(balance),
                                     fg=P["green"] if balance <= 0 else P["red"])
                s_bg = P["paid_bg"] if balance <= 0.01 else P["pend_bg"]
                s_fg = P["paid_fg"] if balance <= 0.01 else P["pend_fg"]
                self._lbl_status.config(text=f"  {status}  ", bg=s_bg, fg=s_fg)
                self._var_amount.set(f"{max(0, balance):.2f}")
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _load_bulk(self):
        """Load all pending/partial invoices of same supplier."""
        for w in self._bulk_inner.winfo_children():
            w.destroy()
        self._bulk_vars = []
        try:
            inv = self._inv_data or self.db.get_invoice(self.invoice_id)
            sup_id = inv.get("supplierid_id") or inv.get("supplierid") if inv else None
            if not sup_id:
                return
            rows = self.db.query(
                "SELECT invoiceid, invoice_no, invoice_date, invoice_total, invoice_paid, "
                "payment_status FROM core_invoicemaster "
                "WHERE supplierid_id=%s AND payment_status IN ('pending','partial') "
                "ORDER BY invoice_date ASC LIMIT 100",
                (sup_id,))
            for i, r in enumerate(rows):
                total   = float(r.get("invoice_total", 0) or 0)
                paid    = float(r.get("invoice_paid",  0) or 0)
                balance = round(total - paid, 2)
                if balance <= 0:
                    continue
                bg = P["row_a"] if i % 2 else P["row_b"]
                row_frm = tk.Frame(self._bulk_inner, bg=bg)
                row_frm.pack(fill="x", pady=1)

                check_var  = tk.BooleanVar(value=(r["invoiceid"] == self.invoice_id))
                amount_var = tk.StringVar(value=f"{balance:.2f}")

                tk.Checkbutton(row_frm, variable=check_var, bg=bg,
                               command=lambda: self._update_bulk_total()).pack(side="left", padx=4)
                for txt, w in [(r.get("invoice_no",""), 14),
                               (str(r.get("invoice_date",""))[:10], 12),
                               (_fmt_inr(total), 10),
                               (_fmt_inr(paid),  10),
                               (_fmt_inr(balance), 10)]:
                    tk.Label(row_frm, text=txt, font=FONT["sm"], bg=bg,
                             fg=P["lbl"], width=w, anchor="w", padx=4).pack(side="left")
                amt_e = tk.Entry(row_frm, textvariable=amount_var,
                                 font=FONT["sm"], width=12, relief="solid", bd=1,
                                 bg=P["input_bg"], fg=P["input_fg"])
                amt_e.pack(side="left", padx=4)
                amt_e.bind("<FocusOut>", lambda e: self._update_bulk_total())

                self._bulk_vars.append((r["invoiceid"], r.get("invoice_no",""),
                                        balance, amount_var, check_var))
            self._update_bulk_total()
            # Force canvas to update scrollregion after loading
            self._bulk_inner.update_idletasks()
            self._bulk_canvas.configure(scrollregion=self._bulk_canvas.bbox("all"))
        except Exception as e:
            tk.Label(self._bulk_inner, text=f"Error: {e}",
                     font=FONT["sm"], bg=P["bg"], fg=P["red"]).pack(padx=10, pady=6)
            self._bulk_inner.update_idletasks()
            self._bulk_canvas.configure(scrollregion=self._bulk_canvas.bbox("all"))

    def _update_bulk_total(self):
        total = 0.0
        for _, _, _, amt_var, chk_var in self._bulk_vars:
            if chk_var.get():
                try:
                    total += float(amt_var.get() or 0)
                except Exception:
                    pass
        self._bulk_total_lbl.set(f"Total to Pay: {_fmt_inr(total)}")

    def _load_history(self):
        for i in self._hist_tree.get_children():
            self._hist_tree.delete(i)
        try:
            payments = self.db.get_invoice_payments(self.invoice_id)
            for idx, p in enumerate(payments, 1):
                self._hist_tree.insert("", "end",
                    iid=str(p.get("payment_id", idx)),
                    values=(idx,
                            str(p.get("payment_date", ""))[:10],
                            _fmt_inr(p.get("payment_amount", 0)),
                            p.get("payment_mode", ""),
                            p.get("payment_ref_no", "") or "",
                            "Del to remove"))
        except Exception:
            pass

    # ── Actions ───────────────────────────────────────────────────────────────

    def _fill_full(self):
        try:
            inv = self._inv_data or self.db.get_invoice(self.invoice_id)
            if inv:
                bal = float(inv.get("invoice_total", 0)) - float(inv.get("invoice_paid", 0))
                self._var_amount.set(f"{max(0, bal):.2f}")
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
            self.db.add_invoice_payment(
                self.invoice_id, pay_date, amount,
                self._var_mode.get(), self._var_ref.get().strip())
            messagebox.showinfo("Saved", f"Payment of {_fmt_inr(amount)} recorded.", parent=self)
            self._load()
            if self.on_saved: self.on_saved()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _save_bulk(self):
        selected = [(inv_id, inv_no, amt_var, chk_var)
                    for inv_id, inv_no, _, amt_var, chk_var in self._bulk_vars
                    if chk_var.get()]
        if not selected:
            messagebox.showwarning("Bulk Payment", "Select at least one invoice.", parent=self)
            return
        pay_date = self._bulk_date_var.get().strip()
        mode     = self._bulk_mode_var.get()
        ref      = self._bulk_ref_var.get().strip()
        if not pay_date:
            messagebox.showwarning("Bulk Payment", "Payment date required.", parent=self)
            return
        saved = 0
        errors = []
        for inv_id, inv_no, amt_var, _ in selected:
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
        self._load()
        if self.on_saved: self.on_saved()

    def _delete_payment(self):
        sel = self._hist_tree.focus()
        if not sel:
            return
        if messagebox.askyesno("Delete Payment", "Delete this payment? Cannot be undone.", parent=self):
            try:
                self.db.delete_invoice_payment(int(sel))
                self._load()
                if self.on_saved: self.on_saved()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self)
