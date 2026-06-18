import tkinter as tk
from tkinter import ttk, messagebox
from ...styles import COLORS, FONT

BG    = COLORS["bg_light"]
CARD  = "#ffffff"
BDR   = "#e2e8f0"
TXT   = "#1e293b"
MUTED = "#64748b"
BLUE  = "#3b82f6"
BLUE_H = "#2563eb"
GREEN = "#10b981"
GREEN_H = "#059669"
LIGHT = "#f8fafc"
ITEM_H = "#eff6ff"


def _btn(parent, text, bg, hover, cmd=None, padx=12, pady=6):
    b = tk.Button(parent, text=text, bg=bg, fg="white",
                  font=("Segoe UI", 10, "bold"),
                  bd=0, relief="flat", padx=padx, pady=pady,
                  cursor="hand2",
                  activebackground=hover, activeforeground="white",
                  command=cmd)
    b.bind("<Enter>", lambda e: b.config(bg=hover))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


class LedgerScreen(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.app = app_instance
        self._var_cust = tk.StringVar()
        self._var_supp = tk.StringVar()
        self._cust_rows: list = []
        self._supp_rows: list = []
        self._build()
        self._var_cust.trace_add("write", lambda *_: self._filter_cust())
        self._var_supp.trace_add("write", lambda *_: self._filter_supp())

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Page title ────────────────────────────────────────────────────
        title_frm = tk.Frame(self, bg=BG, pady=20)
        title_frm.pack(fill="x")
        tk.Label(title_frm, text="📋 Ledger Management",
                 font=("Segoe UI", 18, "bold"), fg=CARD, bg=BG).pack()
        tk.Label(title_frm,
                 text="Select a customer or supplier to view their ledger",
                 font=("Segoe UI", 10), fg=MUTED, bg=BG).pack(pady=(2, 0))

        # ── Two-panel row ─────────────────────────────────────────────────
        panels = tk.Frame(self, bg=BG)
        panels.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        panels.grid_columnconfigure(0, weight=1)
        panels.grid_columnconfigure(1, weight=1)
        panels.grid_rowconfigure(0, weight=1)

        self._cust_panel = self._make_panel(
            panels, "👤  Customers", "blue",
            self._var_cust, "Search customers...",
            col=0)
        self._supp_panel = self._make_panel(
            panels, "🚚  Suppliers", "green",
            self._var_supp, "Search suppliers...",
            col=1)

    def _make_panel(self, parent, title, color, var, ph, col):
        accent = BLUE if color == "blue" else GREEN
        card = tk.Frame(parent, bg=CARD,
                        relief="flat", bd=1,
                        highlightbackground=BDR,
                        highlightthickness=1)
        card.grid(row=0, column=col, sticky="nsew",
                  padx=(0 if col == 1 else 0, 10 if col == 0 else 0))

        # header
        hdr = tk.Frame(card, bg=CARD, padx=20, pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text=title, font=("Segoe UI", 14, "bold"),
                 fg=TXT, bg=CARD).pack(anchor="w")
        tk.Frame(hdr, bg=accent, height=3).pack(fill="x", pady=(8, 0))

        # search
        srch = tk.Frame(card, bg=CARD, padx=16, pady=8)
        srch.pack(fill="x")
        wrap = tk.Frame(srch, bg="white", relief="solid", bd=1,
                        highlightthickness=2,
                        highlightbackground=BLUE if color == "blue" else GREEN)
        wrap.pack(fill="x")
        tk.Label(wrap, text="🔍", bg="white", fg=accent,
                 font=("Segoe UI", 10)).pack(side="left", padx=(8, 2))
        e = tk.Entry(wrap, textvariable=var,
                     font=("Segoe UI", 10), width=30,
                     relief="flat", bd=0, bg="white",
                     fg=TXT, insertbackground=TXT)
        e.pack(side="left", padx=(0, 8), ipady=7, fill="x", expand=True)
        e.insert(0, ph)
        e.bind("<FocusIn>",  lambda ev, p=ph, en=e: self._clr(ev, en, p))
        e.bind("<FocusOut>", lambda ev, p=ph, en=e: self._rst(ev, en, p))

        # list area (scrollable)
        list_outer = tk.Frame(card, bg=CARD)
        list_outer.pack(fill="both", expand=True, padx=16, pady=(4, 16))

        canvas = tk.Canvas(list_outer, bg=CARD, highlightthickness=0)
        vsb = ttk.Scrollbar(list_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=CARD)
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda ev, c=canvas: c.configure(
            scrollregion=c.bbox("all")))
        canvas.bind("<Configure>", lambda ev, c=canvas, w=win: c.itemconfig(w, width=ev.width))

        # empty label
        empty = tk.Label(inner, text="No entries found",
                         font=("Segoe UI", 10, "italic"),
                         fg=MUTED, bg=CARD)

        panel_info = {"inner": inner, "empty": empty, "color": color,
                      "accent": accent, "var": var, "ph": ph}
        if color == "blue":
            self._cust_inner  = inner
            self._cust_empty  = empty
        else:
            self._supp_inner  = inner
            self._supp_empty  = empty
        return card

    # ── Placeholder ───────────────────────────────────────────────────────────

    def _clr(self, e, entry, ph):
        if entry.get() == ph:
            entry.delete(0, "end")
            entry.config(fg=TXT)

    def _rst(self, e, entry, ph):
        if not entry.get():
            entry.insert(0, ph)
            entry.config(fg=MUTED)

    # ── Data ──────────────────────────────────────────────────────────────────

    def on_show(self):
        try:
            self._cust_rows = self.app.db.fetch_customers("")
        except Exception:
            self._cust_rows = []
        try:
            self._supp_rows = self.app.db.fetch_suppliers("")
        except Exception:
            self._supp_rows = []
        self._filter_cust()
        self._filter_supp()

    def _filter_cust(self):
        term = self._var_cust.get().lower()
        if term in ("search customers...", ""):
            term = ""
        rows = [r for r in self._cust_rows
                if term in str(r.get("customer_name","")).lower()
                or term in str(r.get("customer_mobile","")).lower()]
        self._render_list(self._cust_inner, self._cust_empty, rows, "customer")

    def _filter_supp(self):
        term = self._var_supp.get().lower()
        if term in ("search suppliers...", ""):
            term = ""
        rows = [r for r in self._supp_rows
                if term in str(r.get("supplier_name","")).lower()
                or term in str(r.get("supplier_mobile","")).lower()]
        self._render_list(self._supp_inner, self._supp_empty, rows, "supplier")

    def _render_list(self, inner, empty, rows, kind):
        for w in inner.winfo_children():
            w.destroy()
        if not rows:
            empty_lbl = tk.Label(inner,
                                  text=f"No {'customers' if kind=='customer' else 'suppliers'} found",
                                  font=("Segoe UI", 10, "italic"),
                                  fg=MUTED, bg=CARD)
            empty_lbl.pack(pady=20)
            return
        for r in rows:
            if kind == "customer":
                name    = r.get("customer_name","")
                mobile  = r.get("customer_mobile","")
                gst     = r.get("customer_gstno","")
                row_id  = r.get("customerid")
            else:
                name    = r.get("supplier_name","")
                mobile  = r.get("supplier_mobile","")
                gst     = r.get("supplier_gstno","")
                row_id  = r.get("supplierid")

            item = tk.Frame(inner, bg=CARD, relief="solid", bd=1,
                            highlightbackground=BDR, highlightthickness=1,
                            cursor="hand2", padx=12, pady=10)
            item.pack(fill="x", pady=(0, 6))
            item.bind("<Enter>", lambda e, i=item: i.config(bg=ITEM_H))
            item.bind("<Leave>", lambda e, i=item: i.config(bg=CARD))
            item.bind("<Button-1>", lambda e, n=name, k=kind, rid=row_id:
                      self._open_ledger(n, k, rid))

            tk.Label(item, text=name, font=("Segoe UI", 10, "bold"),
                     fg=TXT, bg=CARD, anchor="w").pack(anchor="w")
            detail = f"📞 {mobile}" if mobile else ""
            if gst:
                detail += f"  |  🏷 {gst}"
            if detail:
                tk.Label(item, text=detail, font=("Segoe UI", 9),
                         fg=MUTED, bg=CARD, anchor="w").pack(anchor="w")
            for w in item.winfo_children():
                w.bind("<Button-1>", lambda e, n=name, k=kind, rid=row_id:
                       self._open_ledger(n, k, rid))
                w.bind("<Enter>", lambda e, i=item: i.config(bg=ITEM_H))
                w.bind("<Leave>", lambda e, i=item: i.config(bg=CARD))

    def _open_ledger(self, name, kind, row_id):
        LedgerDetailWindow(self, self.app, name=name, kind=kind, row_id=row_id)

    def kb_refresh(self): self.on_show()
    def kb_search(self):  self._cust_inner.master.master.focus_set()


# ── Ledger detail popup ───────────────────────────────────────────────────────

class LedgerDetailWindow(tk.Toplevel):
    def __init__(self, parent, app, name, kind, row_id):
        super().__init__(parent)
        self.app  = app
        self.name = name
        self.kind = kind
        self.row_id = row_id
        self.title(f"Ledger — {name}")
        self.state("zoomed")
        self.configure(bg=CARD)
        self.grab_set()
        self.bind("<Escape>", lambda e: self.destroy())
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=TXT, padx=20, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"📋 Ledger: {self.name}",
                 font=("Segoe UI", 14, "bold"), fg=CARD, bg=TXT).pack(side="left")
        tk.Button(hdr, text="✕ Close", bg=MUTED, fg="white",
                  font=("Segoe UI", 9), bd=0, relief="flat",
                  padx=10, pady=4, command=self.destroy).pack(side="right")

        cols = ("#", "Date", "Particulars", "Type", "Debit", "Credit", "Balance")
        widths = (40, 100, 280, 80, 100, 100, 100)
        frm = tk.Frame(self, bg=CARD)
        frm.pack(fill="both", expand=True, padx=16, pady=12)
        vsb = ttk.Scrollbar(frm, orient="vertical")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings",
                                  yscrollcommand=vsb.set, selectmode="browse")
        vsb.config(command=self.tree.yview)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w,
                             anchor="w" if col == "Particulars" else "center")
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # footer balance
        self._bal_var = tk.StringVar(value="Balance: ₹0.00")
        tk.Label(self, textvariable=self._bal_var,
                 font=("Segoe UI", 11, "bold"), fg=TXT, bg=CARD,
                 anchor="e").pack(fill="x", padx=20, pady=(0, 10))

        self._load()

    def _load(self):
        try:
            rid = self.app.config_data.retailer_id
            if self.kind == "customer":
                invoices = self.app.db.query(
                    """SELECT si.sales_invoice_date AS dt,
                              si.sales_invoice_no   AS ref,
                              COALESCE(SUM(sm.sale_total_amount),0) AS total,
                              si.sales_invoice_paid AS paid
                       FROM core_salesinvoicemaster si
                       LEFT JOIN core_salesmaster sm
                              ON sm.sales_invoice_no_id = si.sales_invoice_no
                       WHERE si.customerid_id=%s AND si.retailer_id=%s
                       GROUP BY si.sales_invoice_no, si.sales_invoice_date,
                                si.sales_invoice_paid
                       ORDER BY si.sales_invoice_date""",
                    (self.row_id, rid))
                entries = [{"date": r["dt"], "particulars": f"Sales Invoice {r['ref']}",
                            "type": "Sale",
                            "debit": 0.0, "credit": float(r["total"])} for r in invoices]
                payments = self.app.db.get_sales_payments_by_customer(self.row_id) \
                    if hasattr(self.app.db, "get_sales_payments_by_customer") else []
                for p in payments:
                    entries.append({"date": p.get("sales_payment_date",""),
                                    "particulars": "Payment Received",
                                    "type": "Payment",
                                    "debit": float(p.get("sales_payment_amount",0)),
                                    "credit": 0.0})
            else:
                invoices = self.app.db.query(
                    """SELECT i.invoice_date AS dt,
                              i.invoice_no   AS ref,
                              i.invoice_total AS total,
                              i.invoice_paid  AS paid
                       FROM core_invoicemaster i
                       WHERE i.supplierid_id=%s AND i.retailer_id=%s
                       ORDER BY i.invoice_date""",
                    (self.row_id, rid))
                entries = [{"date": r["dt"], "particulars": f"Purchase Invoice {r['ref']}",
                            "type": "Purchase",
                            "debit": float(r["total"]), "credit": 0.0} for r in invoices]

            entries.sort(key=lambda x: str(x["date"]))
            balance = 0.0
            for idx, e in enumerate(entries, 1):
                balance += e["credit"] - e["debit"]
                self.tree.insert("", "end", values=(
                    idx, e["date"], e["particulars"], e["type"],
                    f"₹{e['debit']:,.2f}" if e["debit"] else "—",
                    f"₹{e['credit']:,.2f}" if e["credit"] else "—",
                    f"₹{balance:,.2f}"
                ))
            self._bal_var.set(f"Closing Balance:  ₹{balance:,.2f}")
        except Exception as ex:
            messagebox.showerror("Error", str(ex), parent=self)
