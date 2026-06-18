import tkinter as tk
from tkinter import ttk
from ...styles import COLORS


class ReceiptsScreen(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=COLORS["bg_light"], **kwargs)
        self.app = app_instance
        self._mode = "sales"
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=COLORS["bg_light"])
        top.pack(fill="x", pady=(0, 8))
        tk.Label(top, text="Receipts & Payments", font=("Inter", 16, "bold"),
                 fg=COLORS["dark_text"], bg=COLORS["bg_light"]).pack(side="left")

        tabs = tk.Frame(top, bg=COLORS["bg_light"])
        tabs.pack(side="right")
        self._rb = tk.Button(tabs, text="Sales Receipts",
                             bg=COLORS["purple_dark"], fg="white", font=("Inter", 10),
                             bd=0, relief="flat", padx=10, pady=4, cursor="hand2",
                             command=lambda: self._switch("sales"))
        self._rb.pack(side="left", padx=2)
        self._pb = tk.Button(tabs, text="Purchase Payments",
                             bg=COLORS["purple"], fg="white", font=("Inter", 10),
                             bd=0, relief="flat", padx=10, pady=4, cursor="hand2",
                             command=lambda: self._switch("purchase"))
        self._pb.pack(side="left", padx=2)

        cols = ("#", "Payment ID", "Invoice No", "Date", "Amount", "Mode", "Ref No")
        widths = (40, 90, 130, 100, 100, 100, 130)
        frm = tk.Frame(self, bg=COLORS["bg_light"])
        frm.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(frm, orient="vertical")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", yscrollcommand=vsb.set)
        vsb.config(command=self.tree.yview)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        frm.grid_rowconfigure(0, weight=1)
        frm.grid_columnconfigure(0, weight=1)

    def _switch(self, mode: str):
        self._mode = mode
        self._rb.config(bg=COLORS["purple_dark"] if mode == "sales" else COLORS["purple"])
        self._pb.config(bg=COLORS["purple_dark"] if mode == "purchase" else COLORS["purple"])
        self.on_show()

    def on_show(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        rid = self.app.config_data.retailer_id
        try:
            if self._mode == "sales":
                rows = self.app.db.query(
                    """SELECT sip.sales_payment_id, sip.sales_ip_invoice_no_id,
                              sip.sales_payment_date, sip.sales_payment_amount,
                              sip.sales_payment_mode, sip.sales_payment_ref_no
                       FROM core_salesinvoicepaid sip
                       JOIN core_salesinvoicemaster si
                         ON si.sales_invoice_no = sip.sales_ip_invoice_no_id
                       WHERE si.retailer_id = %s
                       ORDER BY sip.sales_payment_date DESC LIMIT 500""",
                    (rid,)
                )
                for idx, r in enumerate(rows, 1):
                    self.tree.insert("", "end", values=(
                        idx, r.get("sales_payment_id", ""),
                        r.get("sales_ip_invoice_no_id", ""),
                        r.get("sales_payment_date", ""),
                        f"\u20b9{float(r.get('sales_payment_amount', 0)):.2f}",
                        r.get("sales_payment_mode", ""),
                        r.get("sales_payment_ref_no", "")
                    ))
            else:
                rows = self.app.db.query(
                    """SELECT ip.payment_id, ip.ip_invoiceid_id, ip.payment_date,
                              ip.payment_amount, ip.payment_mode, ip.payment_ref_no
                       FROM core_invoicepaid ip
                       JOIN core_invoicemaster i ON i.invoiceid = ip.ip_invoiceid_id
                       WHERE i.retailer_id = %s
                       ORDER BY ip.payment_date DESC LIMIT 500""",
                    (rid,)
                )
                for idx, r in enumerate(rows, 1):
                    self.tree.insert("", "end", values=(
                        idx, r.get("payment_id", ""),
                        r.get("ip_invoiceid_id", ""),
                        r.get("payment_date", ""),
                        f"\u20b9{float(r.get('payment_amount', 0)):.2f}",
                        r.get("payment_mode", ""),
                        r.get("payment_ref_no", "")
                    ))
        except Exception:
            pass
