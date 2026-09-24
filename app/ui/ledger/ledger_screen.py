# import tkinter as tk
# from tkinter import ttk, messagebox
# from ...styles import COLORS, FONT

# BG    = COLORS["bg_light"]
# CARD  = "#ffffff"
# BDR   = "#e2e8f0"
# TXT   = "#1e293b"
# MUTED = "#64748b"
# BLUE  = "#3b82f6"
# BLUE_H = "#2563eb"
# GREEN = "#10b981"
# GREEN_H = "#059669"
# LIGHT = "#f8fafc"
# ITEM_H = "#eff6ff"


# def _btn(parent, text, bg, hover, cmd=None, padx=12, pady=6):
#     b = tk.Button(parent, text=text, bg=bg, fg="white",
#                   font=("Segoe UI", 10, "bold"),
#                   bd=0, relief="flat", padx=padx, pady=pady,
#                   cursor="hand2",
#                   activebackground=hover, activeforeground="white",
#                   command=cmd)
#     b.bind("<Enter>", lambda e: b.config(bg=hover))
#     b.bind("<Leave>", lambda e: b.config(bg=bg))
#     return b


# class LedgerScreen(tk.Frame):
#     def __init__(self, parent, app_instance, **kwargs):
#         super().__init__(parent, bg=BG, **kwargs)
#         self.app = app_instance
#         self._var_cust = tk.StringVar()
#         self._var_supp = tk.StringVar()
#         self._cust_rows: list = []
#         self._supp_rows: list = []
#         self._build()
#         self._var_cust.trace_add("write", lambda *_: self._filter_cust())
#         self._var_supp.trace_add("write", lambda *_: self._filter_supp())

#     # ── Build ─────────────────────────────────────────────────────────────────

#     def _build(self):
#         # ── Page title ────────────────────────────────────────────────────
#         title_frm = tk.Frame(self, bg=BG, pady=20)
#         title_frm.pack(fill="x")
#         tk.Label(title_frm, text="📋 Ledger Management",
#                  font=("Segoe UI", 18, "bold"), fg=CARD, bg=BG).pack()
#         tk.Label(title_frm,
#                  text="Select a customer or supplier to view their ledger",
#                  font=("Segoe UI", 10), fg=MUTED, bg=BG).pack(pady=(2, 0))

#         # ── Two-panel row ─────────────────────────────────────────────────
#         panels = tk.Frame(self, bg=BG)
#         panels.pack(fill="both", expand=True, padx=20, pady=(0, 20))
#         panels.grid_columnconfigure(0, weight=1)
#         panels.grid_columnconfigure(1, weight=1)
#         panels.grid_rowconfigure(0, weight=1)

#         self._cust_panel = self._make_panel(
#             panels, "👤  Customers", "blue",
#             self._var_cust, "Search customers...",
#             col=0)
#         self._supp_panel = self._make_panel(
#             panels, "🚚  Suppliers", "green",
#             self._var_supp, "Search suppliers...",
#             col=1)

#     def _make_panel(self, parent, title, color, var, ph, col):
#         accent = BLUE if color == "blue" else GREEN
#         card = tk.Frame(parent, bg=CARD,
#                         relief="flat", bd=1,
#                         highlightbackground=BDR,
#                         highlightthickness=1)
#         card.grid(row=0, column=col, sticky="nsew",
#                   padx=(0 if col == 1 else 0, 10 if col == 0 else 0))

#         # header
#         hdr = tk.Frame(card, bg=CARD, padx=20, pady=16)
#         hdr.pack(fill="x")
#         tk.Label(hdr, text=title, font=("Segoe UI", 14, "bold"),
#                  fg=TXT, bg=CARD).pack(anchor="w")
#         tk.Frame(hdr, bg=accent, height=3).pack(fill="x", pady=(8, 0))

#         # search
#         srch = tk.Frame(card, bg=CARD, padx=16, pady=8)
#         srch.pack(fill="x")
#         wrap = tk.Frame(srch, bg="white", relief="solid", bd=1,
#                         highlightthickness=2,
#                         highlightbackground=BLUE if color == "blue" else GREEN)
#         wrap.pack(fill="x")
#         tk.Label(wrap, text="🔍", bg="white", fg=accent,
#                  font=("Segoe UI", 10)).pack(side="left", padx=(8, 2))
#         e = tk.Entry(wrap, textvariable=var,
#                      font=("Segoe UI", 10), width=30,
#                      relief="flat", bd=0, bg="white",
#                      fg=TXT, insertbackground=TXT)
#         e.pack(side="left", padx=(0, 8), ipady=7, fill="x", expand=True)
#         e.insert(0, ph)
#         e.bind("<FocusIn>",  lambda ev, p=ph, en=e: self._clr(ev, en, p))
#         e.bind("<FocusOut>", lambda ev, p=ph, en=e: self._rst(ev, en, p))

#         # list area (scrollable)
#         list_outer = tk.Frame(card, bg=CARD)
#         list_outer.pack(fill="both", expand=True, padx=16, pady=(4, 16))

#         canvas = tk.Canvas(list_outer, bg=CARD, highlightthickness=0)
#         vsb = ttk.Scrollbar(list_outer, orient="vertical", command=canvas.yview)
#         canvas.configure(yscrollcommand=vsb.set)
#         vsb.pack(side="right", fill="y")
#         canvas.pack(side="left", fill="both", expand=True)

#         inner = tk.Frame(canvas, bg=CARD)
#         win = canvas.create_window((0, 0), window=inner, anchor="nw")
#         inner.bind("<Configure>", lambda ev, c=canvas: c.configure(
#             scrollregion=c.bbox("all")))
#         canvas.bind("<Configure>", lambda ev, c=canvas, w=win: c.itemconfig(w, width=ev.width))

#         # empty label
#         empty = tk.Label(inner, text="No entries found",
#                          font=("Segoe UI", 10, "italic"),
#                          fg=MUTED, bg=CARD)

#         panel_info = {"inner": inner, "empty": empty, "color": color,
#                       "accent": accent, "var": var, "ph": ph}
#         if color == "blue":
#             self._cust_inner  = inner
#             self._cust_empty  = empty
#         else:
#             self._supp_inner  = inner
#             self._supp_empty  = empty
#         return card

#     # ── Placeholder ───────────────────────────────────────────────────────────

#     def _clr(self, e, entry, ph):
#         if entry.get() == ph:
#             entry.delete(0, "end")
#             entry.config(fg=TXT)

#     def _rst(self, e, entry, ph):
#         if not entry.get():
#             entry.insert(0, ph)
#             entry.config(fg=MUTED)

#     # ── Data ──────────────────────────────────────────────────────────────────

#     def on_show(self):
#         try:
#             self._cust_rows = self.app.db.fetch_customers("")
#         except Exception:
#             self._cust_rows = []
#         try:
#             self._supp_rows = self.app.db.fetch_suppliers("")
#         except Exception:
#             self._supp_rows = []
#         self._filter_cust()
#         self._filter_supp()

#     def _filter_cust(self):
#         term = self._var_cust.get().lower()
#         if term in ("search customers...", ""):
#             term = ""
#         rows = [r for r in self._cust_rows
#                 if term in str(r.get("customer_name","")).lower()
#                 or term in str(r.get("customer_mobile","")).lower()]
#         self._render_list(self._cust_inner, self._cust_empty, rows, "customer")

#     def _filter_supp(self):
#         term = self._var_supp.get().lower()
#         if term in ("search suppliers...", ""):
#             term = ""
#         rows = [r for r in self._supp_rows
#                 if term in str(r.get("supplier_name","")).lower()
#                 or term in str(r.get("supplier_mobile","")).lower()]
#         self._render_list(self._supp_inner, self._supp_empty, rows, "supplier")

#     def _render_list(self, inner, empty, rows, kind):
#         for w in inner.winfo_children():
#             w.destroy()
#         if not rows:
#             empty_lbl = tk.Label(inner,
#                                   text=f"No {'customers' if kind=='customer' else 'suppliers'} found",
#                                   font=("Segoe UI", 10, "italic"),
#                                   fg=MUTED, bg=CARD)
#             empty_lbl.pack(pady=20)
#             return
#         for r in rows:
#             if kind == "customer":
#                 name    = r.get("customer_name","")
#                 mobile  = r.get("customer_mobile","")
#                 gst     = r.get("customer_gstno","")
#                 row_id  = r.get("customerid")
#             else:
#                 name    = r.get("supplier_name","")
#                 mobile  = r.get("supplier_mobile","")
#                 gst     = r.get("supplier_gstno","")
#                 row_id  = r.get("supplierid")

#             item = tk.Frame(inner, bg=CARD, relief="solid", bd=1,
#                             highlightbackground=BDR, highlightthickness=1,
#                             cursor="hand2", padx=12, pady=10)
#             item.pack(fill="x", pady=(0, 6))
#             item.bind("<Enter>", lambda e, i=item: i.config(bg=ITEM_H))
#             item.bind("<Leave>", lambda e, i=item: i.config(bg=CARD))
#             item.bind("<Button-1>", lambda e, n=name, k=kind, rid=row_id:
#                       self._open_ledger(n, k, rid))

#             tk.Label(item, text=name, font=("Segoe UI", 10, "bold"),
#                      fg=TXT, bg=CARD, anchor="w").pack(anchor="w")
#             detail = f"📞 {mobile}" if mobile else ""
#             if gst:
#                 detail += f"  |  🏷 {gst}"
#             if detail:
#                 tk.Label(item, text=detail, font=("Segoe UI", 9),
#                          fg=MUTED, bg=CARD, anchor="w").pack(anchor="w")
#             for w in item.winfo_children():
#                 w.bind("<Button-1>", lambda e, n=name, k=kind, rid=row_id:
#                        self._open_ledger(n, k, rid))
#                 w.bind("<Enter>", lambda e, i=item: i.config(bg=ITEM_H))
#                 w.bind("<Leave>", lambda e, i=item: i.config(bg=CARD))

#     def _open_ledger(self, name, kind, row_id):
#         LedgerDetailWindow(self, self.app, name=name, kind=kind, row_id=row_id)

#     def kb_refresh(self): self.on_show()
#     def kb_search(self):  self._cust_inner.master.master.focus_set()


# # ── Ledger detail popup ───────────────────────────────────────────────────────

# class LedgerDetailWindow(tk.Toplevel):
#     def __init__(self, parent, app, name, kind, row_id):
#         super().__init__(parent)
#         self.app  = app
#         self.name = name
#         self.kind = kind
#         self.row_id = row_id
#         self.title(f"Ledger — {name}")
#         self.state("zoomed")
#         self.configure(bg=CARD)
#         self.grab_set()
#         self.bind("<Escape>", lambda e: self.destroy())
#         self._build()

#     def _build(self):
#         hdr = tk.Frame(self, bg=TXT, padx=20, pady=14)
#         hdr.pack(fill="x")
#         tk.Label(hdr, text=f"📋 Ledger: {self.name}",
#                  font=("Segoe UI", 14, "bold"), fg=CARD, bg=TXT).pack(side="left")
#         tk.Button(hdr, text="✕ Close", bg=MUTED, fg="white",
#                   font=("Segoe UI", 9), bd=0, relief="flat",
#                   padx=10, pady=4, command=self.destroy).pack(side="right")

#         # Action buttons
#         act = tk.Frame(self, bg=LIGHT, padx=16, pady=8)
#         act.pack(fill="x")
#         if self.kind == "supplier":
#             _btn(act, "💳 Add Payment", BLUE, BLUE_H,
#                  cmd=self._open_payment).pack(side="left", padx=(0, 8))
#         else:
#             _btn(act, "💳 Add Receipt", GREEN, GREEN_H,
#                  cmd=self._open_payment).pack(side="left", padx=(0, 8))
#         _btn(act, "🔄 Refresh", MUTED, "#475569",
#              cmd=self._load).pack(side="left")

#         # Summary bar
#         self._summary_frm = tk.Frame(self, bg=LIGHT, padx=16, pady=6)
#         self._summary_frm.pack(fill="x")
#         self._lbl_total_inv = tk.Label(self._summary_frm, text="",
#                                         font=("Segoe UI", 9), fg=MUTED, bg=LIGHT)
#         self._lbl_total_inv.pack(side="left", padx=(0, 20))
#         self._lbl_total_paid = tk.Label(self._summary_frm, text="",
#                                          font=("Segoe UI", 9), fg=GREEN, bg=LIGHT)
#         self._lbl_total_paid.pack(side="left", padx=(0, 20))
#         self._lbl_advance = tk.Label(self._summary_frm, text="",
#                                       font=("Segoe UI", 9), fg=BLUE, bg=LIGHT)
#         self._lbl_advance.pack(side="left")

#         cols = ("#", "Date", "Particulars", "Type", "Debit", "Credit", "Balance")
#         widths = (40, 100, 300, 100, 110, 110, 110)
#         frm = tk.Frame(self, bg=CARD)
#         frm.pack(fill="both", expand=True, padx=16, pady=8)
#         vsb = ttk.Scrollbar(frm, orient="vertical")
#         self.tree = ttk.Treeview(frm, columns=cols, show="headings",
#                                   yscrollcommand=vsb.set, selectmode="browse")
#         vsb.config(command=self.tree.yview)
#         for col, w in zip(cols, widths):
#             self.tree.heading(col, text=col)
#             self.tree.column(col, width=w,
#                              anchor="w" if col == "Particulars" else "center")
#         self.tree.tag_configure("invoice", foreground="#1e293b")
#         self.tree.tag_configure("payment", foreground=GREEN)
#         self.tree.tag_configure("advance", foreground=BLUE)
#         self.tree.pack(side="left", fill="both", expand=True)
#         vsb.pack(side="right", fill="y")

#         self._bal_var = tk.StringVar(value="Balance: ₹0.00")
#         bal_frm = tk.Frame(self, bg=CARD, pady=8)
#         bal_frm.pack(fill="x")
#         tk.Label(bal_frm, textvariable=self._bal_var,
#                  font=("Segoe UI", 12, "bold"), fg=TXT, bg=CARD,
#                  anchor="e").pack(fill="x", padx=20)

#         self._load()

#     def _open_payment(self):
#         if self.kind == "supplier":
#             from ..purchase.payment_dialog import PurchasePaymentDialog
#             PurchasePaymentDialog(self, self.app, invoice_id=None,
#                                   invoice_no="", on_saved=self._load,
#                                   preselect_supplier_id=self.row_id,
#                                   preselect_supplier_name=self.name)
#         else:
#             from ..sales.payment_dialog import SalesPaymentDialog
#             SalesPaymentDialog(self, self.app, invoice_no="",
#                                on_saved=self._load,
#                                preselect_customer_id=self.row_id,
#                                preselect_customer_name=self.name)

#     def _load(self):
#         for i in self.tree.get_children():
#             self.tree.delete(i)
#         try:
#             rid = self.app.config_data.retailer_id
#             entries = []

#             if self.kind == "supplier":
#                 # Purchase invoices — debit (we owe supplier)
#                 invoices = self.app.db.query(
#                     """SELECT i.invoice_date AS dt, i.invoice_no AS ref,
#                               i.invoice_total AS total
#                        FROM core_invoicemaster i
#                        WHERE i.supplierid_id=%s AND i.retailer_id=%s
#                        ORDER BY i.invoice_date, i.invoiceid""",
#                     (self.row_id, rid))
#                 for r in invoices:
#                     entries.append({"date": str(r["dt"]), "ref": r["ref"],
#                                     "particulars": f"Purchase Invoice {r['ref']}",
#                                     "type": "Purchase", "tag": "invoice",
#                                     "debit": float(r["total"]), "credit": 0.0})

#                 # Payments made — credit (reduces what we owe)
#                 payments = self.app.db.query(
#                     """SELECT ip.payment_date AS dt, ip.payment_amount AS amt,
#                               ip.payment_mode AS mode, ip.payment_ref_no AS ref,
#                               i.invoice_no
#                        FROM core_invoicepaid ip
#                        JOIN core_invoicemaster i ON i.invoiceid = ip.ip_invoiceid_id
#                        WHERE i.supplierid_id=%s AND i.retailer_id=%s
#                        ORDER BY ip.payment_date, ip.payment_id""",
#                     (self.row_id, rid))
#                 for p in payments:
#                     entries.append({"date": str(p["dt"]),
#                                     "ref": p.get("invoice_no", ""),
#                                     "particulars": f"Payment  [{p.get('mode','')}]  {p.get('ref','') or ''}",
#                                     "type": "Payment", "tag": "payment",
#                                     "debit": 0.0, "credit": float(p["amt"])})

#                 # Advance payments
#                 self.app.db._ensure_supplier_advance_table()
#                 advances = self.app.db.query(
#                     """SELECT payment_date AS dt, advance_amount AS amt,
#                               payment_mode AS mode, notes
#                        FROM supplier_advance_payment
#                        WHERE supplier_id=%s AND retailer_id=%s
#                        ORDER BY payment_date, id""",
#                     (self.row_id, rid))
#                 for a in advances:
#                     amt = float(a["amt"])
#                     if amt > 0:
#                         entries.append({"date": str(a["dt"]),
#                                         "ref": "",
#                                         "particulars": f"Advance Payment  [{a.get('mode','')}]  {a.get('notes','') or ''}",
#                                         "type": "Advance", "tag": "advance",
#                                         "debit": 0.0, "credit": amt})
#                     elif amt < 0:
#                         entries.append({"date": str(a["dt"]),
#                                         "ref": "",
#                                         "particulars": f"Advance Used  {a.get('notes','') or ''}",
#                                         "type": "Adv.Used", "tag": "payment",
#                                         "debit": 0.0, "credit": amt})  # negative credit = debit

#             else:  # customer
#                 # Sales invoices — credit (customer owes us)
#                 invoices = self.app.db.query(
#                     """SELECT si.sales_invoice_date AS dt,
#                               si.sales_invoice_no AS ref,
#                               COALESCE(SUM(sm.sale_total_amount),0) AS total
#                        FROM core_salesinvoicemaster si
#                        LEFT JOIN core_salesmaster sm
#                               ON sm.sales_invoice_no_id = si.sales_invoice_no
#                        WHERE si.customerid_id=%s AND si.retailer_id=%s
#                        GROUP BY si.sales_invoice_no, si.sales_invoice_date
#                        ORDER BY si.sales_invoice_date""",
#                     (self.row_id, rid))
#                 for r in invoices:
#                     entries.append({"date": str(r["dt"]), "ref": r["ref"],
#                                     "particulars": f"Sales Invoice {r['ref']}",
#                                     "type": "Sale", "tag": "invoice",
#                                     "debit": 0.0, "credit": float(r["total"])})

#                 # Receipts — debit (reduces what customer owes)
#                 receipts = self.app.db.query(
#                     """SELECT sp.sales_payment_date AS dt,
#                               sp.sales_payment_amount AS amt,
#                               sp.sales_payment_mode AS mode,
#                               sp.sales_payment_ref_no AS ref,
#                               si.sales_invoice_no
#                        FROM core_salesinvoicepaid sp
#                        JOIN core_salesinvoicemaster si
#                               ON si.sales_invoice_no = sp.sales_ip_invoice_no_id
#                        WHERE si.customerid_id=%s AND si.retailer_id=%s
#                        ORDER BY sp.sales_payment_date, sp.sales_payment_id""",
#                     (self.row_id, rid))
#                 for p in receipts:
#                     entries.append({"date": str(p["dt"]),
#                                     "ref": p.get("sales_invoice_no", ""),
#                                     "particulars": f"Receipt  [{p.get('mode','')}]  {p.get('ref','') or ''}",
#                                     "type": "Receipt", "tag": "payment",
#                                     "debit": float(p["amt"]), "credit": 0.0})

#                 # Advance receipts
#                 self.app.db._ensure_customer_advance_table()
#                 advances = self.app.db.query(
#                     """SELECT payment_date AS dt, advance_amount AS amt,
#                               payment_mode AS mode, notes
#                        FROM customer_advance_payment
#                        WHERE customer_id=%s AND retailer_id=%s
#                        ORDER BY payment_date, id""",
#                     (self.row_id, rid))
#                 for a in advances:
#                     amt = float(a["amt"])
#                     if amt > 0:
#                         entries.append({"date": str(a["dt"]),
#                                         "ref": "",
#                                         "particulars": f"Advance Receipt  [{a.get('mode','')}]  {a.get('notes','') or ''}",
#                                         "type": "Advance", "tag": "advance",
#                                         "debit": amt, "credit": 0.0})
#                     elif amt < 0:
#                         entries.append({"date": str(a["dt"]),
#                                         "ref": "",
#                                         "particulars": f"Advance Used  {a.get('notes','') or ''}",
#                                         "type": "Adv.Used", "tag": "payment",
#                                         "debit": amt, "credit": 0.0})  # negative debit

#             entries.sort(key=lambda x: x["date"])

#             balance = 0.0
#             total_inv = 0.0
#             total_paid = 0.0
#             advance_bal = 0.0

#             for idx, e in enumerate(entries, 1):
#                 dr = e["debit"]
#                 cr = e["credit"]
#                 if self.kind == "supplier":
#                     # supplier: debit = invoice (we owe), credit = payment (reduces debt)
#                     balance += dr - cr
#                     if e["type"] == "Purchase":
#                         total_inv += dr
#                     elif e["type"] in ("Payment", "Adv.Used"):
#                         total_paid += cr
#                     elif e["type"] == "Advance":
#                         advance_bal += cr
#                 else:
#                     # customer: credit = invoice (they owe), debit = receipt (reduces debt)
#                     balance += cr - dr
#                     if e["type"] == "Sale":
#                         total_inv += cr
#                     elif e["type"] in ("Receipt", "Adv.Used"):
#                         total_paid += dr
#                     elif e["type"] == "Advance":
#                         advance_bal += dr

#                 dr_str = f"₹{abs(dr):,.2f}" if dr else "—"
#                 cr_str = f"₹{abs(cr):,.2f}" if cr else "—"
#                 self.tree.insert("", "end", tags=(e["tag"],), values=(
#                     idx, e["date"], e["particulars"], e["type"],
#                     dr_str, cr_str, f"₹{abs(balance):,.2f}"
#                 ))

#             bal_label = "Balance Payable" if self.kind == "supplier" else "Balance Receivable"
#             self._bal_var.set(f"{bal_label}:  ₹{abs(balance):,.2f}")

#             inv_label = "Total Purchases" if self.kind == "supplier" else "Total Sales"
#             paid_label = "Total Paid" if self.kind == "supplier" else "Total Received"
#             self._lbl_total_inv.config(text=f"{inv_label}: ₹{total_inv:,.2f}")
#             self._lbl_total_paid.config(text=f"{paid_label}: ₹{total_paid:,.2f}")
#             adv_label = "Advance Credit" if self.kind == "supplier" else "Advance Received"
#             self._lbl_advance.config(text=f"{adv_label}: ₹{advance_bal:,.2f}")

#         except Exception as ex:
#             messagebox.showerror("Error", str(ex), parent=self)


import csv
import html
import tempfile
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from ...styles import COLORS


BG = COLORS["bg_light"]
CARD = "#ffffff"
BDR = "#dbe5ea"
TXT = "#1e293b"
MUTED = "#64748b"
BLUE = "#2563eb"
BLUE_H = "#1d4ed8"
GREEN = "#059669"
GREEN_H = "#047857"
TEAL = "#0f766e"
TEAL_H = "#115e59"
RED = "#dc3545"
RED_H = "#b42334"
AMBER = "#b45309"
LIGHT = "#f8fafc"
ITEM_H = "#eff6ff"


def _btn(parent, text, bg, hover, cmd=None, padx=12, pady=6):
    """Create a compact action button with a consistent hover state."""
    button = tk.Button(
        parent,
        text=text,
        bg=bg,
        fg="white",
        font=("Segoe UI", 10, "bold"),
        bd=0,
        relief="flat",
        padx=padx,
        pady=pady,
        cursor="hand2",
        activebackground=hover,
        activeforeground="white",
        command=cmd,
    )
    button.bind("<Enter>", lambda _event: button.config(bg=hover))
    button.bind("<Leave>", lambda _event: button.config(bg=bg))
    return button


class LedgerScreen(tk.Frame):
    """Searchable customer and supplier ledgers landing screen."""

    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.app = app_instance
        self._var_cust = tk.StringVar()
        self._var_supp = tk.StringVar()
        self._cust_rows: list[dict] = []
        self._supp_rows: list[dict] = []
        self._build()
        self._var_cust.trace_add("write", lambda *_args: self._filter_cust())
        self._var_supp.trace_add("write", lambda *_args: self._filter_supp())

    def _build(self):
        title_frm = tk.Frame(self, bg=BG, pady=20)
        title_frm.pack(fill="x")
        tk.Label(
            title_frm,
            text="📋 Ledger Management",
            font=("Segoe UI", 18, "bold"),
            fg=TXT,
            bg=BG,
        ).pack()
        tk.Label(
            title_frm,
            text="Select a customer or supplier to view their ledger statement",
            font=("Segoe UI", 10),
            fg=MUTED,
            bg=BG,
        ).pack(pady=(2, 0))

        panels = tk.Frame(self, bg=BG)
        panels.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        panels.grid_columnconfigure(0, weight=1)
        panels.grid_columnconfigure(1, weight=1)
        panels.grid_rowconfigure(0, weight=1)

        self._cust_panel = self._make_panel(
            panels, "👤  Customers", "blue", self._var_cust, "Search customers...", col=0
        )
        self._supp_panel = self._make_panel(
            panels, "🚚  Suppliers", "green", self._var_supp, "Search suppliers...", col=1
        )

    def _make_panel(self, parent, title, color, var, placeholder, col):
        accent = BLUE if color == "blue" else GREEN
        card = tk.Frame(
            parent,
            bg=CARD,
            relief="flat",
            bd=1,
            highlightbackground=BDR,
            highlightthickness=1,
        )
        card.grid(row=0, column=col, sticky="nsew", padx=(0, 10 if col == 0 else 0))

        header = tk.Frame(card, bg=CARD, padx=20, pady=16)
        header.pack(fill="x")
        tk.Label(header, text=title, font=("Segoe UI", 14, "bold"), fg=TXT, bg=CARD).pack(anchor="w")
        tk.Frame(header, bg=accent, height=3).pack(fill="x", pady=(8, 0))

        search = tk.Frame(card, bg=CARD, padx=16, pady=8)
        search.pack(fill="x")
        wrap = tk.Frame(
            search,
            bg="white",
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=accent,
        )
        wrap.pack(fill="x")
        tk.Label(wrap, text="🔍", bg="white", fg=accent, font=("Segoe UI", 10)).pack(side="left", padx=(8, 2))
        entry = tk.Entry(
            wrap,
            textvariable=var,
            font=("Segoe UI", 10),
            width=30,
            relief="flat",
            bd=0,
            bg="white",
            fg=MUTED,
            insertbackground=TXT,
        )
        entry.pack(side="left", padx=(0, 8), ipady=7, fill="x", expand=True)
        entry.insert(0, placeholder)
        entry.bind("<FocusIn>", lambda event, ph=placeholder, ent=entry: self._clear_placeholder(event, ent, ph))
        entry.bind("<FocusOut>", lambda event, ph=placeholder, ent=entry: self._restore_placeholder(event, ent, ph))

        list_outer = tk.Frame(card, bg=CARD)
        list_outer.pack(fill="both", expand=True, padx=16, pady=(4, 16))
        canvas = tk.Canvas(list_outer, bg=CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=CARD)
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda _event, current_canvas=canvas: current_canvas.configure(scrollregion=current_canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event, current_canvas=canvas, win=window_id: current_canvas.itemconfig(win, width=event.width))

        empty = tk.Label(inner, text="No entries found", font=("Segoe UI", 10, "italic"), fg=MUTED, bg=CARD)
        if color == "blue":
            self._cust_inner = inner
            self._cust_empty = empty
        else:
            self._supp_inner = inner
            self._supp_empty = empty
        return card

    @staticmethod
    def _clear_placeholder(_event, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, "end")
            entry.config(fg=TXT)

    @staticmethod
    def _restore_placeholder(_event, entry, placeholder):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg=MUTED)

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
        rows = [
            row for row in self._cust_rows
            if term in str(row.get("customer_name", "")).lower()
            or term in str(row.get("customer_mobile", "")).lower()
        ]
        self._render_list(self._cust_inner, rows, "customer")

    def _filter_supp(self):
        term = self._var_supp.get().lower()
        if term in ("search suppliers...", ""):
            term = ""
        rows = [
            row for row in self._supp_rows
            if term in str(row.get("supplier_name", "")).lower()
            or term in str(row.get("supplier_mobile", "")).lower()
        ]
        self._render_list(self._supp_inner, rows, "supplier")

    def _render_list(self, inner, rows, kind):
        for widget in inner.winfo_children():
            widget.destroy()
        if not rows:
            tk.Label(
                inner,
                text=f"No {'customers' if kind == 'customer' else 'suppliers'} found",
                font=("Segoe UI", 10, "italic"),
                fg=MUTED,
                bg=CARD,
            ).pack(pady=20)
            return

        for row in rows:
            if kind == "customer":
                name = row.get("customer_name", "")
                mobile = row.get("customer_mobile", "")
                gst = row.get("customer_gstno", "")
                row_id = row.get("customerid")
                accent = BLUE
            else:
                name = row.get("supplier_name", "")
                mobile = row.get("supplier_mobile", "")
                gst = row.get("supplier_gstno", "")
                row_id = row.get("supplierid")
                accent = GREEN

            item = tk.Frame(
                inner,
                bg=CARD,
                relief="solid",
                bd=1,
                highlightbackground=BDR,
                highlightthickness=1,
                cursor="hand2",
                padx=12,
                pady=10,
            )
            item.pack(fill="x", pady=(0, 6))
            item.bind("<Enter>", lambda _event, current=item: current.config(bg=ITEM_H))
            item.bind("<Leave>", lambda _event, current=item: current.config(bg=CARD))
            item.bind("<Button-1>", lambda _event, n=name, k=kind, rid=row_id, data=row: self._open_ledger(n, k, rid, data))

            name_label = tk.Label(item, text=name, font=("Segoe UI", 10, "bold"), fg=TXT, bg=CARD, anchor="w")
            name_label.pack(anchor="w")
            details = f"📞 {mobile}" if mobile else ""
            if gst:
                details += f"  |  🏷 {gst}"
            if details:
                detail_label = tk.Label(item, text=details, font=("Segoe UI", 9), fg=MUTED, bg=CARD, anchor="w")
                detail_label.pack(anchor="w")
            for child in item.winfo_children():
                child.bind("<Button-1>", lambda _event, n=name, k=kind, rid=row_id, data=row: self._open_ledger(n, k, rid, data))
                child.bind("<Enter>", lambda _event, current=item: current.config(bg=ITEM_H))
                child.bind("<Leave>", lambda _event, current=item: current.config(bg=CARD))

    def _open_ledger(self, name, kind, row_id, entity=None):
        LedgerDetailWindow(self, self.app, name=name, kind=kind, row_id=row_id, entity=entity or {})

    def kb_refresh(self):
        self.on_show()

    def kb_search(self):
        self._cust_inner.master.master.focus_set()


class LedgerDetailWindow(tk.Toplevel):
    """Supplier/customer statement with the same hierarchy as the reference ledger."""

    def __init__(self, parent, app, name, kind, row_id, entity=None):
        super().__init__(parent)
        self.app = app
        self.name = name
        self.kind = kind
        self.row_id = row_id
        self.entity = entity or {}
        self._all_entries: list[dict] = []
        self._visible_entries: list[dict] = []
        self.title(f"{'Supplier' if kind == 'supplier' else 'Customer'} Ledger — {name}")
        self.configure(bg=BG)
        self.minsize(980, 650)
        try:
            self.state("zoomed")
        except tk.TclError:
            self.geometry("1240x780")
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.bind("<Escape>", lambda _event: self.destroy())
        self.bind("<Control-q>", self._on_print_shortcut)
        self.bind("<Control-e>", self._on_excel_shortcut)
        self._configure_tree_style()
        self._build()

    def _configure_tree_style(self):
        style = ttk.Style(self)
        style.configure(
            "Ledger.Treeview",
            background=CARD,
            foreground=TXT,
            fieldbackground=CARD,
            rowheight=32,
            font=("Segoe UI", 9),
            borderwidth=0,
        )
        style.map("Ledger.Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", TXT)])
        style.configure(
            "Ledger.Treeview.Heading",
            background="#eaf5f3",
            foreground="#155e59",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padding=(8, 8),
        )

    def _build(self):
        page = tk.Frame(self, bg=BG)
        page.pack(fill="both", expand=True)

        self._build_header(page)
        self._build_filter_bar(page)
        self._build_summary_cards(page)
        self._build_advance_section(page)
        self._build_transaction_section(page)
        self._build_footer(page)
        self._load()

    def _build_header(self, parent):
        card = tk.Frame(parent, bg=CARD, highlightbackground=BDR, highlightthickness=1, padx=20, pady=16)
        card.pack(fill="x", padx=18, pady=(18, 8))
        info = tk.Frame(card, bg=CARD)
        info.pack(side="left", fill="x", expand=True)

        document_title = "Supplier Ledger" if self.kind == "supplier" else "Customer Ledger"
        accent = GREEN if self.kind == "supplier" else BLUE
        tk.Label(info, text=document_title, font=("Segoe UI", 16, "bold"), fg=TXT, bg=CARD).pack(anchor="w")
        tk.Frame(info, bg=accent, height=3, width=116).pack(anchor="w", pady=(5, 8))
        tk.Label(info, text=self.name, font=("Segoe UI", 12, "bold"), fg=TXT, bg=CARD).pack(anchor="w")

        mobile = self.entity.get(f"{self.kind}_mobile", "") or "N/A"
        email = self.entity.get(f"{self.kind}_emailid", "") or "N/A"
        gst = self.entity.get(f"{self.kind}_gstno", "") or ""
        details = f"📞 {mobile}     ✉ {email}"
        if gst:
            details += f"     GST: {gst}"
        tk.Label(info, text=details, font=("Segoe UI", 9), fg=MUTED, bg=CARD).pack(anchor="w", pady=(3, 0))

        actions = tk.Frame(card, bg=CARD)
        actions.pack(side="right", anchor="ne", padx=(20, 0))
        _btn(actions, "🧾 PDF / Print", BLUE, BLUE_H, self._open_printable_statement, padx=10).pack(side="left", padx=(0, 7))
        _btn(actions, "📗 Excel", GREEN, GREEN_H, self._export_excel, padx=10).pack(side="left", padx=(0, 7))
        _btn(actions, "🖨 Print", TEAL, TEAL_H, self._open_printable_statement, padx=10).pack(side="left", padx=(0, 7))
        _btn(actions, "← Back", MUTED, "#475569", self.destroy, padx=10).pack(side="left")

    def _build_filter_bar(self, parent):
        bar = tk.Frame(parent, bg=CARD, highlightbackground=BDR, highlightthickness=1, padx=16, pady=10)
        bar.pack(fill="x", padx=18, pady=(0, 8))
        self._start_var = tk.StringVar()
        self._end_var = tk.StringVar()
        tk.Label(bar, text="Start Date", font=("Segoe UI", 9, "bold"), fg=MUTED, bg=CARD).pack(side="left")
        ttk.Entry(bar, textvariable=self._start_var, width=13, font=("Segoe UI", 10)).pack(side="left", padx=(7, 14), ipady=4)
        tk.Label(bar, text="End Date", font=("Segoe UI", 9, "bold"), fg=MUTED, bg=CARD).pack(side="left")
        ttk.Entry(bar, textvariable=self._end_var, width=13, font=("Segoe UI", 10)).pack(side="left", padx=(7, 14), ipady=4)
        _btn(bar, "🔎 Filter", TEAL, TEAL_H, self._apply_date_filter, padx=12, pady=5).pack(side="left", padx=(0, 7))
        tk.Button(
            bar,
            text="✕ Clear",
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 9, "bold"),
            bd=1,
            relief="solid",
            highlightbackground=BDR,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._clear_date_filter,
        ).pack(side="left")
        self._period_var = tk.StringVar(value="All transactions")
        tk.Label(bar, textvariable=self._period_var, font=("Segoe UI", 9), fg=TEAL, bg=CARD).pack(side="right")

    def _build_summary_cards(self, parent):
        wrap = tk.Frame(parent, bg=BG)
        wrap.pack(fill="x", padx=18, pady=(0, 8))
        wrap.grid_columnconfigure((0, 1, 2), weight=1, uniform="summary")

        invoice_label = "Total Purchases" if self.kind == "supplier" else "Total Sales"
        paid_label = "Total Paid" if self.kind == "supplier" else "Total Received"
        due_label = "Balance Due" if self.kind == "supplier" else "Balance Receivable"
        self._summary_invoice_var = tk.StringVar(value="₹0.00")
        self._summary_paid_var = tk.StringVar(value="₹0.00")
        self._summary_balance_var = tk.StringVar(value="₹0.00")
        self._make_summary_card(wrap, 0, invoice_label, self._summary_invoice_var, BLUE)
        self._make_summary_card(wrap, 1, paid_label, self._summary_paid_var, GREEN)
        self._make_summary_card(wrap, 2, due_label, self._summary_balance_var, RED)

    @staticmethod
    def _make_summary_card(parent, column, label, value_var, accent):
        card = tk.Frame(parent, bg=CARD, highlightbackground=BDR, highlightthickness=1, padx=14, pady=12)
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 5, 0 if column == 2 else 5))
        tk.Frame(card, bg=accent, height=3).pack(fill="x", pady=(0, 9))
        tk.Label(card, text=label, font=("Segoe UI", 9, "bold"), fg=MUTED, bg=CARD).pack(anchor="w")
        tk.Label(card, textvariable=value_var, font=("Segoe UI", 15, "bold"), fg=accent, bg=CARD).pack(anchor="w", pady=(3, 0))

    def _build_advance_section(self, parent):
        self.advance_card = tk.Frame(parent, bg=CARD, highlightbackground=BDR, highlightthickness=1)
        advance_header = tk.Frame(self.advance_card, bg=CARD, padx=16, pady=10)
        advance_header.pack(fill="x")
        tk.Frame(advance_header, bg=GREEN, width=4).pack(side="left", fill="y", padx=(0, 8))
        self._advance_title_var = tk.StringVar(value="💰 Advance Balance")
        tk.Label(advance_header, textvariable=self._advance_title_var, font=("Segoe UI", 11, "bold"), fg="#166534", bg=CARD).pack(side="left")
        self._advance_balance_var = tk.StringVar(value="₹0.00")
        tk.Label(advance_header, textvariable=self._advance_balance_var, font=("Segoe UI", 11, "bold"), fg="#166534", bg="#dcfce7", padx=10, pady=4).pack(side="right")

        advance_columns = ("Date", "Type", "Amount (₹)", "Invoice Ref", "Narration")
        advance_frame = tk.Frame(self.advance_card, bg=CARD)
        advance_frame.pack(fill="x")
        self.advance_tree = ttk.Treeview(
            advance_frame,
            columns=advance_columns,
            show="headings",
            height=3,
            style="Ledger.Treeview",
            selectmode="browse",
        )
        for column, width in zip(advance_columns, (110, 150, 125, 145, 460)):
            column_anchor = "e" if column == "Amount (₹)" else "w"
            self.advance_tree.heading(column, text=column, anchor=column_anchor)
            self.advance_tree.column(column, width=width, minwidth=width, stretch=True, anchor=column_anchor)
        self.advance_tree.pack(fill="x")
        self.advance_card.pack_forget()

    def _build_transaction_section(self, parent):
        card = tk.Frame(parent, bg=CARD, highlightbackground=BDR, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=18, pady=(0, 8))
        heading = tk.Frame(card, bg=CARD, padx=16, pady=10)
        heading.pack(fill="x")
        tk.Frame(heading, bg=TEAL, width=4).pack(side="left", fill="y", padx=(0, 8))
        statement_title = "Supplier transaction ledger" if self.kind == "supplier" else "Customer transaction ledger"
        tk.Label(heading, text=statement_title, font=("Segoe UI", 11, "bold"), fg=TXT, bg=CARD).pack(side="left")
        self._entry_count_var = tk.StringVar(value="0 transactions")
        tk.Label(heading, textvariable=self._entry_count_var, font=("Segoe UI", 9), fg=MUTED, bg=CARD).pack(side="right")

        debit_heading = "Debit (Paid)" if self.kind == "supplier" else "Debit (Received)"
        credit_heading = "Credit (Purchase)" if self.kind == "supplier" else "Credit (Sales)"
        self._ledger_headers = ("Date", "Type", "Invoice No.", debit_heading, credit_heading, "Balance")
        tree_frame = tk.Frame(card, bg=CARD)
        tree_frame.pack(fill="both", expand=True)
        vertical_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=self._ledger_headers,
            show="headings",
            yscrollcommand=vertical_scroll.set,
            selectmode="browse",
            style="Ledger.Treeview",
        )
        vertical_scroll.config(command=self.tree.yview)
        for column, width in zip(self._ledger_headers, (110, 155, 195, 140, 145, 145)):
            # Header and body use the exact same anchor.  Earlier the default
            # Treeview heading anchor was centred while values were left/right
            # aligned, making each value appear under a different column.
            column_anchor = "e" if column in self._ledger_headers[-3:] else "w"
            self.tree.heading(column, text=column, anchor=column_anchor)
            self.tree.column(column, width=width, minwidth=width, stretch=True, anchor=column_anchor)
        self.tree.tag_configure("invoice", foreground=BLUE)
        self.tree.tag_configure("payment", foreground=GREEN)
        self.tree.tag_configure("advance", foreground=TEAL)
        self.tree.tag_configure("adjusted", foreground=AMBER)
        self.tree.pack(side="left", fill="both", expand=True)
        vertical_scroll.pack(side="right", fill="y")

        totals = tk.Frame(card, bg="#eefaf7", padx=16, pady=10)
        totals.pack(fill="x")
        tk.Frame(totals, bg=TEAL, height=2).pack(fill="x", side="top", pady=(0, 8))
        tk.Label(totals, text="TOTAL", font=("Segoe UI", 10, "bold"), fg=TEAL_H, bg="#eefaf7").pack(side="left")
        self._total_balance_var = tk.StringVar(value="Balance: ₹0.00")
        self._total_credit_var = tk.StringVar(value="Credit: ₹0.00")
        self._total_debit_var = tk.StringVar(value="Debit: ₹0.00")
        tk.Label(totals, textvariable=self._total_balance_var, font=("Segoe UI", 10, "bold"), fg=RED, bg="#eefaf7").pack(side="right")
        tk.Label(totals, textvariable=self._total_credit_var, font=("Segoe UI", 10, "bold"), fg=BLUE, bg="#eefaf7").pack(side="right", padx=24)
        tk.Label(totals, textvariable=self._total_debit_var, font=("Segoe UI", 10, "bold"), fg=GREEN, bg="#eefaf7").pack(side="right", padx=24)

    def _build_footer(self, parent):
        footer = tk.Frame(parent, bg=BG, padx=20, pady=5)
        footer.pack(fill="x")
        tk.Label(
            footer,
            text="This is a computer-generated ledger statement.",
            font=("Segoe UI", 8),
            fg=MUTED,
            bg=BG,
        ).pack(side="left")
        tk.Label(footer, text="Ctrl+Q: PDF / Print     Ctrl+E: Excel", font=("Segoe UI", 8), fg=MUTED, bg=BG).pack(side="right")

    def _open_payment(self):
        if self.kind == "supplier":
            from ..purchase.payment_dialog import PurchasePaymentDialog

            PurchasePaymentDialog(
                self,
                self.app,
                invoice_id=None,
                invoice_no="",
                on_saved=self._load,
                preselect_supplier_id=self.row_id,
                preselect_supplier_name=self.name,
            )
        else:
            from ..sales.payment_dialog import SalesPaymentDialog

            SalesPaymentDialog(
                self,
                self.app,
                invoice_no="",
                on_saved=self._load,
                preselect_customer_id=self.row_id,
                preselect_customer_name=self.name,
            )

    def _load(self):
        """Load current ledger data while keeping the existing database queries intact."""
        try:
            retailer_id = self.app.config_data.retailer_id
            entries: list[dict] = []

            if self.kind == "supplier":
                invoices = self.app.db.query(
                    """SELECT i.invoice_date AS dt, i.invoice_no AS ref, i.invoice_total AS total
                       FROM core_invoicemaster i
                       WHERE i.supplierid_id=%s AND i.retailer_id=%s
                       ORDER BY i.invoice_date, i.invoiceid""",
                    (self.row_id, retailer_id),
                )
                for row in invoices:
                    entries.append(
                        {
                            "date": str(row["dt"]),
                            "ref": row["ref"],
                            "particulars": f"Purchase Invoice {row['ref']}",
                            "type": "Purchase",
                            "tag": "invoice",
                            "debit": float(row["total"]),
                            "credit": 0.0,
                        }
                    )

                payments = self.app.db.query(
                    """SELECT ip.payment_date AS dt, ip.payment_amount AS amt,
                              ip.payment_mode AS mode, ip.payment_ref_no AS ref, i.invoice_no
                       FROM core_invoicepaid ip
                       JOIN core_invoicemaster i ON i.invoiceid = ip.ip_invoiceid_id
                       WHERE i.supplierid_id=%s AND i.retailer_id=%s
                       ORDER BY ip.payment_date, ip.payment_id""",
                    (self.row_id, retailer_id),
                )
                for payment in payments:
                    entries.append(
                        {
                            "date": str(payment["dt"]),
                            "ref": payment.get("invoice_no", ""),
                            "particulars": f"Payment [{payment.get('mode', '')}] {payment.get('ref', '') or ''}".strip(),
                            "type": "Payment",
                            "tag": "payment",
                            "debit": 0.0,
                            "credit": float(payment["amt"]),
                        }
                    )

                self.app.db._ensure_supplier_advance_table()
                advances = self.app.db.query(
                    """SELECT payment_date AS dt, advance_amount AS amt, payment_mode AS mode, notes
                       FROM supplier_advance_payment
                       WHERE supplier_id=%s AND retailer_id=%s
                       ORDER BY payment_date, id""",
                    (self.row_id, retailer_id),
                )
                for advance in advances:
                    amount = float(advance["amt"])
                    if amount > 0:
                        entries.append(
                            {
                                "date": str(advance["dt"]),
                                "ref": "",
                                "particulars": f"Advance Payment [{advance.get('mode', '')}] {advance.get('notes', '') or ''}".strip(),
                                "type": "Advance",
                                "tag": "advance",
                                "debit": 0.0,
                                "credit": amount,
                            }
                        )
                    elif amount < 0:
                        entries.append(
                            {
                                "date": str(advance["dt"]),
                                "ref": "",
                                "particulars": f"Advance Used {advance.get('notes', '') or ''}".strip(),
                                "type": "Adv.Used",
                                "tag": "adjusted",
                                "debit": 0.0,
                                "credit": amount,
                            }
                        )

            else:
                invoices = self.app.db.query(
                    """SELECT si.sales_invoice_date AS dt, si.sales_invoice_no AS ref,
                              COALESCE(SUM(sm.sale_total_amount),0) AS total
                       FROM core_salesinvoicemaster si
                       LEFT JOIN core_salesmaster sm ON sm.sales_invoice_no_id = si.sales_invoice_no
                       WHERE si.customerid_id=%s AND si.retailer_id=%s
                       GROUP BY si.sales_invoice_no, si.sales_invoice_date
                       ORDER BY si.sales_invoice_date""",
                    (self.row_id, retailer_id),
                )
                for row in invoices:
                    entries.append(
                        {
                            "date": str(row["dt"]),
                            "ref": row["ref"],
                            "particulars": f"Sales Invoice {row['ref']}",
                            "type": "Sale",
                            "tag": "invoice",
                            "debit": 0.0,
                            "credit": float(row["total"]),
                        }
                    )

                receipts = self.app.db.query(
                    """SELECT sp.sales_payment_date AS dt, sp.sales_payment_amount AS amt,
                              sp.sales_payment_mode AS mode, sp.sales_payment_ref_no AS ref,
                              si.sales_invoice_no
                       FROM core_salesinvoicepaid sp
                       JOIN core_salesinvoicemaster si ON si.sales_invoice_no = sp.sales_ip_invoice_no_id
                       WHERE si.customerid_id=%s AND si.retailer_id=%s
                       ORDER BY sp.sales_payment_date, sp.sales_payment_id""",
                    (self.row_id, retailer_id),
                )
                for receipt in receipts:
                    entries.append(
                        {
                            "date": str(receipt["dt"]),
                            "ref": receipt.get("sales_invoice_no", ""),
                            "particulars": f"Receipt [{receipt.get('mode', '')}] {receipt.get('ref', '') or ''}".strip(),
                            "type": "Receipt",
                            "tag": "payment",
                            "debit": float(receipt["amt"]),
                            "credit": 0.0,
                        }
                    )

                self.app.db._ensure_customer_advance_table()
                advances = self.app.db.query(
                    """SELECT payment_date AS dt, advance_amount AS amt, payment_mode AS mode, notes
                       FROM customer_advance_payment
                       WHERE customer_id=%s AND retailer_id=%s
                       ORDER BY payment_date, id""",
                    (self.row_id, retailer_id),
                )
                for advance in advances:
                    amount = float(advance["amt"])
                    if amount > 0:
                        entries.append(
                            {
                                "date": str(advance["dt"]),
                                "ref": "",
                                "particulars": f"Advance Receipt [{advance.get('mode', '')}] {advance.get('notes', '') or ''}".strip(),
                                "type": "Advance",
                                "tag": "advance",
                                "debit": amount,
                                "credit": 0.0,
                            }
                        )
                    elif amount < 0:
                        entries.append(
                            {
                                "date": str(advance["dt"]),
                                "ref": "",
                                "particulars": f"Advance Used {advance.get('notes', '') or ''}".strip(),
                                "type": "Adv.Used",
                                "tag": "adjusted",
                                "debit": amount,
                                "credit": 0.0,
                            }
                        )

            self._all_entries = sorted(entries, key=lambda entry: entry["date"])
            self._apply_date_filter(show_errors=False)
        except Exception as exception:
            messagebox.showerror("Ledger Error", str(exception), parent=self)

    def _apply_date_filter(self, show_errors=True):
        start_date = self._start_var.get().strip()
        end_date = self._end_var.get().strip()
        if start_date and not self._is_valid_date(start_date):
            if show_errors:
                messagebox.showwarning("Invalid Start Date", "Use the YYYY-MM-DD format for Start Date.", parent=self)
            return
        if end_date and not self._is_valid_date(end_date):
            if show_errors:
                messagebox.showwarning("Invalid End Date", "Use the YYYY-MM-DD format for End Date.", parent=self)
            return
        if start_date and end_date and start_date > end_date:
            if show_errors:
                messagebox.showwarning("Invalid Date Range", "Start Date cannot be later than End Date.", parent=self)
            return

        visible = [
            entry for entry in self._all_entries
            if (not start_date or entry["date"][:10] >= start_date)
            and (not end_date or entry["date"][:10] <= end_date)
        ]
        if start_date or end_date:
            self._period_var.set(f"Period: {start_date or 'Beginning'} to {end_date or 'Today'}")
        else:
            self._period_var.set("All transactions")
        self._render_entries(visible)

    def _clear_date_filter(self):
        self._start_var.set("")
        self._end_var.set("")
        self._apply_date_filter(show_errors=False)

    @staticmethod
    def _is_valid_date(value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def _render_entries(self, entries):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for item in self.advance_tree.get_children():
            self.advance_tree.delete(item)
        self._visible_entries = entries

        balance = 0.0
        total_debit = 0.0
        total_credit = 0.0
        advance_balance = 0.0
        advance_rows = []

        for entry in entries:
            debit = float(entry["debit"])
            credit = float(entry["credit"])
            if self.kind == "supplier":
                balance += debit - credit
                if entry["type"] == "Purchase":
                    total_credit += abs(debit)
                elif entry["type"] == "Payment":
                    total_debit += abs(credit)
                display_debit = abs(credit) if entry["type"] in ("Payment", "Advance") else 0.0
                display_credit = abs(debit) if entry["type"] == "Purchase" else 0.0
                if entry["type"] in ("Advance", "Adv.Used"):
                    advance_balance += credit
            else:
                balance += credit - debit
                if entry["type"] == "Sale":
                    total_credit += abs(credit)
                elif entry["type"] == "Receipt":
                    total_debit += abs(debit)
                display_debit = abs(debit) if entry["type"] in ("Receipt", "Advance") else 0.0
                display_credit = abs(credit) if entry["type"] == "Sale" else 0.0
                if entry["type"] in ("Advance", "Adv.Used"):
                    advance_balance += debit

            type_label = self._transaction_label(entry["type"])
            reference = entry["ref"] or "—"
            balance_text = f"₹{abs(balance):,.2f}"
            if balance < 0:
                balance_text += " Cr"
            self.tree.insert(
                "",
                "end",
                tags=(entry["tag"],),
                values=(
                    self._display_date(entry["date"]),
                    type_label,
                    reference,
                    f"₹{display_debit:,.2f}" if display_debit else "—",
                    f"₹{display_credit:,.2f}" if display_credit else "—",
                    balance_text,
                ),
            )

            if entry["type"] in ("Advance", "Adv.Used"):
                advance_type = "Advance In" if entry["type"] == "Advance" else "Adjusted"
                amount = abs(credit) if self.kind == "supplier" else abs(debit)
                advance_rows.append(
                    (
                        self._display_date(entry["date"]),
                        advance_type,
                        f"₹{amount:,.2f}",
                        reference,
                        entry["particulars"],
                    )
                )

        if advance_rows:
            for row in advance_rows:
                self.advance_tree.insert("", "end", values=row)
            self._advance_title_var.set("💰 Advance Balance")
            self._advance_balance_var.set(f"₹{abs(advance_balance):,.2f}")
            self.advance_card.pack(fill="x", padx=18, pady=(0, 8), before=self.tree.master.master)
        else:
            self.advance_card.pack_forget()

        balance_label = "Balance Due" if self.kind == "supplier" else "Balance Receivable"
        self._summary_invoice_var.set(f"₹{total_credit:,.2f}")
        self._summary_paid_var.set(f"₹{total_debit:,.2f}")
        self._summary_balance_var.set(f"₹{abs(balance):,.2f}")
        self._total_debit_var.set(f"Debit: ₹{total_debit:,.2f}")
        self._total_credit_var.set(f"Credit: ₹{total_credit:,.2f}")
        self._total_balance_var.set(f"{balance_label}: ₹{abs(balance):,.2f}")
        self._entry_count_var.set(f"{len(entries)} transaction{'s' if len(entries) != 1 else ''}")

    def _transaction_label(self, entry_type):
        if self.kind == "supplier":
            return {
                "Purchase": "Purchase Invoice",
                "Payment": "Payment",
                "Advance": "Advance In",
                "Adv.Used": "Advance Adjusted",
            }.get(entry_type, entry_type)
        return {
            "Sale": "Sales Invoice",
            "Receipt": "Payment Received",
            "Advance": "Advance In",
            "Adv.Used": "Advance Adjusted",
        }.get(entry_type, entry_type)

    @staticmethod
    def _display_date(value):
        raw = str(value)[:10]
        try:
            return datetime.strptime(raw, "%Y-%m-%d").strftime("%d-%m-%Y")
        except ValueError:
            return raw

    def _export_excel(self):
        if not self._visible_entries:
            messagebox.showinfo("Export Ledger", "There are no ledger entries in the selected date range.", parent=self)
            return
        safe_name = "".join(char if char.isalnum() else "_" for char in self.name).strip("_") or "ledger"
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Ledger to Excel-compatible CSV",
            defaultextension=".csv",
            initialfile=f"{safe_name}_ledger.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as output:
                writer = csv.writer(output)
                writer.writerow(["MedicVista Retailer Ledger"])
                writer.writerow([self.name, self._period_var.get()])
                writer.writerow([])
                writer.writerow(self._ledger_headers)
                for item in self.tree.get_children():
                    writer.writerow(self.tree.item(item, "values"))
                writer.writerow([])
                writer.writerow(["TOTAL", "", "", self._total_debit_var.get(), self._total_credit_var.get(), self._total_balance_var.get()])
            messagebox.showinfo("Export Ledger", f"Ledger exported successfully.\n{path}", parent=self)
        except OSError as exception:
            messagebox.showerror("Export Error", str(exception), parent=self)

    def _open_printable_statement(self):
        if not self._visible_entries:
            messagebox.showinfo("Print Ledger", "There are no ledger entries in the selected date range.", parent=self)
            return
        table_rows = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            table_rows.append("<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in values) + "</tr>")
        table_headers = "".join(f"<th>{html.escape(header)}</th>" for header in self._ledger_headers)
        mobile = html.escape(str(self.entity.get(f"{self.kind}_mobile", "N/A") or "N/A"))
        email = html.escape(str(self.entity.get(f"{self.kind}_emailid", "N/A") or "N/A"))
        title = "Supplier Ledger" if self.kind == "supplier" else "Customer Ledger"
        statement = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>{html.escape(title)} — {html.escape(self.name)}</title>
<style>
@page {{ size: A4 landscape; margin: 10mm; }}
body {{ font-family: Arial, sans-serif; color: #1e293b; margin: 0; font-size: 11px; }}
h1, h2, p {{ margin: 0; }} .header {{ border-bottom: 2px solid #0f766e; padding-bottom: 10px; margin-bottom: 14px; }}
.name {{ margin: 8px 0 3px; font-size: 15px; }} .meta {{ color: #64748b; }} .period {{ float: right; color: #0f766e; font-weight: bold; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }} th {{ background: #0f766e; color: white; text-align: left; }} th, td {{ border: 1px solid #cbd5e1; padding: 6px; }} td:nth-last-child(-n+3), th:nth-last-child(-n+3) {{ text-align: right; }}
.total {{ margin-top: 12px; padding: 8px; background: #eefaf7; border-top: 2px solid #0f766e; font-weight: bold; }} .footer {{ margin-top: 14px; font-size: 9px; color: #64748b; text-align: center; }}
</style></head><body>
<div class='header'><span class='period'>{html.escape(self._period_var.get())}</span><h1>MedicVista Retailer Ledger</h1><h2>{html.escape(title)}</h2><p class='name'>{html.escape(self.name)}</p><p class='meta'>Mobile: {mobile} &nbsp;|&nbsp; Email: {email}</p></div>
<table><thead><tr>{table_headers}</tr></thead><tbody>{''.join(table_rows)}</tbody></table>
<div class='total'>{html.escape(self._total_debit_var.get())} &nbsp;&nbsp;&nbsp; {html.escape(self._total_credit_var.get())} &nbsp;&nbsp;&nbsp; {html.escape(self._total_balance_var.get())}</div>
<p class='footer'>This is a computer-generated ledger statement. Use your browser's Print command and select “Save as PDF” to create a PDF.</p>
</body></html>"""
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix="_ledger.html", delete=False) as output:
                output.write(statement)
                output_path = output.name
            webbrowser.open_new_tab(f"file://{output_path}")
            messagebox.showinfo("Print / PDF", "The printable ledger opened in your browser. Use Print and choose 'Save as PDF' if required.", parent=self)
        except OSError as exception:
            messagebox.showerror("Print Error", str(exception), parent=self)

    def _on_print_shortcut(self, _event):
        self._open_printable_statement()
        return "break"

    def _on_excel_shortcut(self, _event):
        self._export_excel()
        return "break"
