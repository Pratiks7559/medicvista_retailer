from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox


class LookupDialog(tk.Toplevel):
    def __init__(self, parent, app, title: str, mode: str, on_select):
        super().__init__(parent)
        self.app = app
        self.db = app.db
        self.configure(bg="#0b1220")

        self.mode = mode  # 'supplier' or 'customer'
        self.on_select = on_select

        self.title(title)
        self.state("zoomed")
        self.resizable(True, True)
        self.grab_set()

        self._search_var = tk.StringVar(value="")
        self._build()

        # defaults
        self._fill()

        # keyboard
        self.bind("<Escape>", lambda e: self.destroy())

    def _build(self):
        top = tk.Frame(self)
        top.pack(fill="x", padx=12, pady=10)

        tk.Label(top, text="Search:").pack(side="left")
        tk.Entry(top, textvariable=self._search_var, width=40).pack(side="left", padx=8)
        tk.Button(top, text="Search", command=self._fill).pack(side="left")

        cols = ()
        widths = ()
        if self.mode == "supplier":
            cols = ("id", "name", "mobile", "email", "address", "gst", "dl", "balance")
            widths = (60, 220, 120, 180, 220, 120, 120, 100)
        else:
            cols = ("id", "name", "type", "mobile", "email", "dl", "gst", "credit")
            widths = (60, 220, 120, 120, 180, 110, 110, 90)

        frm = tk.Frame(self)
        frm.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        vsb = ttk.Scrollbar(frm, orient="vertical")
        hsb = ttk.Scrollbar(frm, orient="horizontal")

        self.tree = ttk.Treeview(frm, columns=cols, show="headings", yscrollcommand=vsb.set,
                                   xscrollcommand=hsb.set, selectmode="browse")
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w")

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        self.tree.bind("<Double-1>", self._pick)
        self.tree.bind("<Return>", self._pick)

        # buttons
        btn_row = tk.Frame(self)
        btn_row.pack(fill="x", padx=12, pady=(0, 12))
        tk.Button(btn_row, text="Select", command=self._pick).pack(side="right")

    def _fill(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        term = self._search_var.get() or ""
        try:
            if self.mode == "supplier":
                rows = self.db.fetch_suppliers(term)
                for r in rows:
                    self.tree.insert("", "end", values=(
                        r.get("supplierid", ""), r.get("supplier_name", ""),
                        r.get("supplier_mobile", ""), r.get("supplier_emailid", ""),
                        r.get("supplier_address", ""), r.get("supplier_gstno", ""),
                        r.get("supplier_dlno", ""), r.get("balance", 0),
                    ))
            else:
                rows = self.db.fetch_customers(term)
                for r in rows:
                    self.tree.insert("", "end", values=(
                        r.get("customerid", ""), r.get("customer_name", ""),
                        r.get("customer_type", ""), r.get("customer_mobile", ""),
                        r.get("customer_emailid", ""), r.get("customer_dlno", ""),
                        r.get("customer_gstno", ""), r.get("paid_total", 0),
                    ))
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _pick(self, event=None):
        sel = self.tree.focus()
        if not sel:
            return
        vals = self.tree.item(sel, "values")
        if self.mode == "supplier":
            res = {
                "supplierid": int(vals[0]),
                "supplier_name": vals[1],
                "supplier_mobile": vals[2],
                "supplier_emailid": vals[3],
                "supplier_address": vals[4],
                "supplier_gstno": vals[5],
                "supplier_dlno": vals[6],
            }
        else:
            res = {
                "customerid": int(vals[0]),
                "customer_name": vals[1],
                "customer_type": vals[2],
                "customer_mobile": vals[3],
                "customer_emailid": vals[4],
                "customer_dlno": vals[5],
                "customer_gstno": vals[6],
            }

        if self.on_select:
            self.on_select(res)
        self.destroy()

