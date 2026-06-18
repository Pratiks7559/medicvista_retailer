import tkinter as tk
from tkinter import ttk
from ...styles import COLORS


def _make_tree(parent, cols, widths):
    frm = tk.Frame(parent, bg=COLORS["bg_light"])
    frm.pack(fill="both", expand=True)
    vsb = ttk.Scrollbar(frm, orient="vertical")
    hsb = ttk.Scrollbar(frm, orient="horizontal")
    tree = ttk.Treeview(frm, columns=cols, show="headings",
                        yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)
    for col, w in zip(cols, widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="w" if col in ("Supplier", "Customer", "Challan No") else "center")
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    frm.grid_rowconfigure(0, weight=1)
    frm.grid_columnconfigure(0, weight=1)
    return tree


class ChallanScreen(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=COLORS["bg_light"], **kwargs)
        self.app = app_instance
        self._mode = "purchase"  # or "sales"
        self._build()

    def _build(self):
        # Title + tab toggle
        top = tk.Frame(self, bg=COLORS["bg_light"])
        top.pack(fill="x", pady=(0, 8))
        tk.Label(top, text="Challans", font=("Inter", 16, "bold"),
                 fg=COLORS["dark_text"], bg=COLORS["bg_light"]).pack(side="left")

        tabs = tk.Frame(top, bg=COLORS["bg_light"])
        tabs.pack(side="right")
        self._pur_btn = tk.Button(tabs, text="Purchase Challans",
                                  bg=COLORS["purple_dark"], fg="white", font=("Inter", 10),
                                  bd=0, relief="flat", padx=10, pady=4, cursor="hand2",
                                  command=lambda: self._switch("purchase"))
        self._pur_btn.pack(side="left", padx=2)
        self._sal_btn = tk.Button(tabs, text="Sales Challans",
                                  bg=COLORS["purple"], fg="white", font=("Inter", 10),
                                  bd=0, relief="flat", padx=10, pady=4, cursor="hand2",
                                  command=lambda: self._switch("sales"))
        self._sal_btn.pack(side="left", padx=2)

        # Search
        sf = tk.Frame(self, bg=COLORS["bg_light"])
        sf.pack(fill="x", pady=(0, 6))
        self._search = tk.StringVar()
        tk.Entry(sf, textvariable=self._search, font=("Inter", 10),
                 width=30, relief="solid", bd=1).pack(side="left", padx=4)
        tk.Button(sf, text="Search", bg=COLORS["purple"], fg="white",
                  font=("Inter", 10), bd=0, relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self.on_show).pack(side="left", padx=3)
        tk.Button(sf, text="Reset", bg=COLORS["gray_text"], fg="white",
                  font=("Inter", 10), bd=0, relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self._reset).pack(side="left", padx=3)

        # Table
        cols = ("#", "Challan No", "Date", "Supplier/Customer", "Total", "Paid", "Status", "Actions")
        widths = (40, 130, 100, 180, 90, 80, 90, 80)
        self.tree = _make_tree(self, cols, widths)

    def _switch(self, mode: str):
        self._mode = mode
        self._pur_btn.config(bg=COLORS["purple_dark"] if mode == "purchase" else COLORS["purple"])
        self._sal_btn.config(bg=COLORS["purple_dark"] if mode == "sales" else COLORS["purple"])
        self.on_show()

    def _reset(self):
        self._search.set("")
        self.on_show()

    def on_show(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        search = self._search.get()
        try:
            if self._mode == "purchase":
                rows = self.app.db.query(
                    """SELECT c.challan_id, c.challan_no, c.challan_date,
                              s.supplier_name, c.challan_total, c.challan_paid,
                              IF(c.is_invoiced,'Invoiced','Pending') AS status
                       FROM challan1 c
                       JOIN core_suppliermaster s ON s.supplierid = c.supplier_id_id
                       WHERE c.retailer_id = %s
                       ORDER BY c.challan_date DESC LIMIT 500""",
                    (self.app.config_data.retailer_id,)
                )
            else:
                rows = self.app.db.query(
                    """SELECT c.customer_challan_id, c.customer_challan_no,
                              c.customer_challan_date, cm.customer_name,
                              c.challan_total, c.challan_invoice_paid,
                              IF(c.is_invoiced,'Invoiced','Pending') AS status
                       FROM customer_challan c
                       JOIN core_customermaster cm ON cm.customerid = c.customer_name_id_id
                       WHERE c.retailer_id = %s
                       ORDER BY c.customer_challan_date DESC LIMIT 500""",
                    (self.app.config_data.retailer_id,)
                )
            for idx, r in enumerate(rows, 1):
                vals = list(r.values())
                self.tree.insert("", "end", values=(idx, *vals[1:], "👁 ✏"))
        except Exception:
            pass
