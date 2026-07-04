import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from ...styles import COLORS, FONT

BG      = COLORS["bg_light"]
CARD    = "#ffffff"
DARK    = "#1e293b"
DARKER  = "#0f172a"
BDR     = "#334155"
TXT_LT  = "#f1f5f9"
TXT_DK  = "#1e293b"
MUTED   = "#94a3b8"
BLUE    = "#3b82f6"
BLUE_H  = "#2563eb"
GREEN   = "#10b981"
GREEN_H = "#059669"
RED     = "#ef4444"
RED_H   = "#dc2626"
PURPLE  = "#7c3aed"

# gradient card colours (left bg, right accent)
CARD_PURPLE = ("#7c3aed", "#6d28d9")
CARD_PINK   = ("#ec4899", "#db2777")
CARD_ORANGE = ("#f59e0b", "#fcd34d")


def _btn(parent, text, bg, hover, cmd=None, padx=14, pady=7):
    b = tk.Button(parent, text=text, bg=bg, fg="white",
                  font=("Segoe UI", 10, "bold"),
                  bd=0, relief="flat", padx=padx, pady=pady,
                  cursor="hand2",
                  activebackground=hover, activeforeground="white",
                  command=cmd)
    b.bind("<Enter>", lambda e: b.config(bg=hover))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def _entry_dark(parent, var, width=30):
    e = tk.Entry(parent, textvariable=var, font=("Segoe UI", 10),
                 width=width, relief="solid", bd=1,
                 bg=CARD, fg=TXT_DK, insertbackground=TXT_DK)
    return e


class ReportsScreen(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.app  = app_instance
        self._tab = "Purchases Report"
        self._var_from = tk.StringVar()
        self._var_to   = tk.StringVar()
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Dark header bar ───────────────────────────────────────────────
        hdr = tk.Frame(self, bg=DARK, padx=20, pady=14)
        hdr.pack(fill="x")

        self._title_lbl = tk.Label(hdr,
                                    text="🛒 Purchase Report",
                                    font=("Segoe UI", 15, "bold"),
                                    fg=TXT_LT, bg=DARK)
        self._title_lbl.pack(side="left")

        _btn(hdr, "📊 Export Excel", GREEN, GREEN_H,
             cmd=self._export_excel).pack(side="right", padx=(6, 0))
        _btn(hdr, "📄 Export PDF",   RED,   RED_H,
             cmd=self._export_pdf).pack(side="right", padx=(6, 0))

        # ── Tab bar ───────────────────────────────────────────────────────
        tab_bar = tk.Frame(self, bg=DARK, padx=20, pady=0)
        tab_bar.pack(fill="x")
        tk.Frame(tab_bar, bg=BDR, height=1).pack(fill="x", side="bottom")

        self._tab_btns: dict[str, tk.Label] = {}
        for name in ["Purchases Report", "Sales Report", "Customer Wise Sales"]:
            lbl = tk.Label(tab_bar, text=name,
                           font=("Segoe UI", 10, "bold"),
                           fg=MUTED, bg=DARK,
                           padx=16, pady=10, cursor="hand2")
            lbl.pack(side="left")
            lbl.bind("<Button-1>", lambda e, n=name: self._switch(n))
            lbl.bind("<Return>",   lambda e, n=name: self._switch(n))
            self._tab_btns[name] = lbl
        self._update_tabs()

        # ── Date filter row ───────────────────────────────────────────────
        flt = tk.Frame(self, bg=DARK, padx=20, pady=14)
        flt.pack(fill="x")

        from ..purchase.purchase_invoice_dialog import DateEntry as _DE
        from datetime import date as _date
        self._var_from.set(_date.today().replace(day=1).isoformat())
        self._var_to.set(_date.today().isoformat())

        tk.Label(flt, text="From Date", font=("Segoe UI", 9),
                 fg=MUTED, bg=DARK).grid(row=0, column=0, sticky="w")
        tk.Label(flt, text="To Date", font=("Segoe UI", 9),
                 fg=MUTED, bg=DARK).grid(row=0, column=2, sticky="w", padx=(20, 0))

        self._e_from = _DE(flt, textvariable=self._var_from, width=14, bg=DARK)
        self._e_from.grid(row=1, column=0, padx=(0, 20))

        self._e_to = _DE(flt, textvariable=self._var_to, width=14, bg=DARK)
        self._e_to.grid(row=1, column=2, padx=(0, 16))

        _btn(flt, "🔍 Show Report", BLUE, BLUE_H,
             cmd=self.on_show, padx=18).grid(row=1, column=3)

        # ── Summary cards ─────────────────────────────────────────────────
        self._cards_frame = tk.Frame(self, bg=BG, padx=16, pady=14)
        self._cards_frame.pack(fill="x")

        self._var_total   = tk.StringVar(value="₹0.00")
        self._var_paid    = tk.StringVar(value="₹0.00")
        self._var_pending = tk.StringVar(value="₹0.00")

        card_defs = [
            ("Total Purchases", self._var_total,   CARD_PURPLE),
            ("Total Paid",      self._var_paid,     CARD_PINK),
            ("Total Pending",   self._var_pending,  CARD_ORANGE),
        ]
        for idx, (label, var, (bg1, bg2)) in enumerate(card_defs):
            c = tk.Frame(self._cards_frame, bg=bg1, padx=24, pady=18)
            c.pack(side="left", expand=True, fill="x", padx=5)
            tk.Label(c, text=label, font=("Segoe UI", 10),
                     fg="white", bg=bg1).pack(anchor="w")
            tk.Label(c, textvariable=var, font=("Segoe UI", 20, "bold"),
                     fg="white", bg=bg1).pack(anchor="w")

        # ── Data table ────────────────────────────────────────────────────
        self._tbl_frame = tk.Frame(self, bg=DARK, padx=16, pady=0)
        self._tbl_frame.pack(fill="both", expand=True)

        self.tree = None
        self._build_table()

    def _build_table(self):
        for w in self._tbl_frame.winfo_children():
            w.destroy()

        if self._tab == "Customer Wise Sales":
            cols = ("CUSTOMER", "INVOICES", "TOTAL", "PAID", "BALANCE")
            widths = (260, 80, 130, 120, 130)
        elif self._tab == "Sales Report":
            cols = ("INVOICE NO", "DATE", "CUSTOMER", "TOTAL", "PAID", "BALANCE")
            widths = (140, 110, 200, 120, 110, 120)
        else:
            cols = ("INVOICE NO", "DATE", "SUPPLIER", "TOTAL", "PAID", "BALANCE")
            widths = (140, 110, 200, 120, 110, 120)

        style = ttk.Style()
        style.configure("Dark.Treeview",
                         rowheight=36,
                         font=("Segoe UI", 10),
                         background=DARK,
                         fieldbackground=DARK,
                         foreground=TXT_LT,
                         bordercolor=BDR)
        style.configure("Dark.Treeview.Heading",
                         font=("Segoe UI", 9, "bold"),
                         background=DARKER,
                         foreground=MUTED,
                         relief="flat")
        style.map("Dark.Treeview",
                  background=[("selected", BLUE)],
                  foreground=[("selected", "white")])

        vsb = ttk.Scrollbar(self._tbl_frame, orient="vertical")
        hsb = ttk.Scrollbar(self._tbl_frame, orient="horizontal")
        self.tree = ttk.Treeview(self._tbl_frame, columns=cols,
                                  show="headings", style="Dark.Treeview",
                                  yscrollcommand=vsb.set,
                                  xscrollcommand=hsb.set,
                                  selectmode="browse")
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col, anchor="w")
            nm = col.lower()
            self.tree.column(col, width=w,
                             anchor="w" if nm in ("customer","supplier","invoice no") else "center")
        self.tree.tag_configure("total_row",
                                 font=("Segoe UI", 10, "bold"),
                                 background=DARKER, foreground=TXT_LT)
        self.tree.tag_configure("balance_red", foreground=RED)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self._tbl_frame.grid_rowconfigure(0, weight=1)
        self._tbl_frame.grid_columnconfigure(0, weight=1)

    def _switch(self, name):
        self._tab = name
        self._update_tabs()
        icons = {"Purchases Report": "🛒",
                 "Sales Report": "🧾",
                 "Customer Wise Sales": "👥"}
        self._title_lbl.config(text=f"{icons.get(name,'')} {name}")
        self._build_table()
        self.on_show()

    def _update_tabs(self):
        for n, lbl in self._tab_btns.items():
            if n == self._tab:
                lbl.config(fg=TXT_LT,
                           relief="flat",
                           borderwidth=0)
                # underline via frame below — simplest approach
            else:
                lbl.config(fg=MUTED)

    # ── Data ──────────────────────────────────────────────────────────────────

    def on_show(self):
        if self.tree is None:
            return
        for i in self.tree.get_children():
            self.tree.delete(i)

        frm = self._var_from.get().strip()
        to  = self._var_to.get().strip()

        try:
            if self._tab == "Purchases Report":
                self._load_purchase_data(frm, to)
            elif self._tab == "Sales Report":
                self._load_sales_data(frm, to)
            else:  # Customer Wise Sales
                self._load_customer_wise_data(frm, to)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}", parent=self)

    def _load_purchase_data(self, frm, to):
        rid = self.app.db.config.retailer_id
        query = """SELECT i.invoice_no, i.invoice_date, s.supplier_name,
                          i.invoice_total, i.invoice_paid,
                          (i.invoice_total - i.invoice_paid) as balance
                   FROM core_invoicemaster i
                   JOIN core_suppliermaster s ON s.supplierid = i.supplierid_id
                   WHERE i.retailer_id=%s"""
        params = [rid]
        if frm:
            query += " AND i.invoice_date >= %s"
            params.append(frm)
        if to:
            query += " AND i.invoice_date <= %s"
            params.append(to)
        query += " ORDER BY i.invoice_date ASC"

        rows = self.app.db.query(query, params)
        total_purchases = sum(float(r.get("invoice_total") or 0) for r in rows)
        total_paid = sum(float(r.get("invoice_paid") or 0) for r in rows)
        total_pending = total_purchases - total_paid

        self._var_total.set(f"₹{total_purchases:,.2f}")
        self._var_paid.set(f"₹{total_paid:,.2f}")
        self._var_pending.set(f"₹{total_pending:,.2f}")

        for i in self.tree.get_children():
            self.tree.delete(i)

        for r in rows:
            bal = float(r.get("balance") or 0)
            tag = "balance_red" if bal > 0.01 else ""
            self.tree.insert("", "end", values=(
                r.get("invoice_no", ""),
                str(r.get("invoice_date", ""))[:10],
                r.get("supplier_name", ""),
                f"₹{float(r.get('invoice_total') or 0):,.2f}",
                f"₹{float(r.get('invoice_paid') or 0):,.2f}",
                f"₹{bal:,.2f}",
            ), tags=(tag,))

        # Add totals row
        self.tree.insert("", "end", values=(
            "TOTAL", "", "",
            f"₹{total_purchases:,.2f}",
            f"₹{total_paid:,.2f}",
            f"₹{total_pending:,.2f}"
        ), tags=("total_row",))

    def _load_sales_data(self, frm, to):
        rid = self.app.db.config.retailer_id
        query = """SELECT si.sales_invoice_no, si.sales_invoice_date, c.customer_name,
                          COALESCE(SUM(sm.sale_total_amount), 0) as total,
                          si.sales_invoice_paid as paid
                   FROM core_salesinvoicemaster si
                   JOIN core_customermaster c ON c.customerid = si.customerid_id
                   LEFT JOIN core_salesmaster sm ON sm.sales_invoice_no_id = si.sales_invoice_no
                   WHERE si.retailer_id=%s"""
        params = [rid]
        if frm:
            query += " AND si.sales_invoice_date >= %s"
            params.append(frm)
        if to:
            query += " AND si.sales_invoice_date <= %s"
            params.append(to)
        query += " GROUP BY si.sales_invoice_no, si.sales_invoice_date, c.customer_name, si.sales_invoice_paid"
        query += " ORDER BY si.sales_invoice_date ASC"

        rows = self.app.db.query(query, params)
        total_sales = sum(float(r.get("total") or 0) for r in rows)
        total_paid = sum(float(r.get("paid") or 0) for r in rows)
        total_pending = total_sales - total_paid

        self._var_total.set(f"₹{total_sales:,.2f}")
        self._var_paid.set(f"₹{total_paid:,.2f}")
        self._var_pending.set(f"₹{total_pending:,.2f}")

        for i in self.tree.get_children():
            self.tree.delete(i)

        for r in rows:
            total = float(r.get("total") or 0)
            paid = float(r.get("paid") or 0)
            bal = total - paid
            tag = "balance_red" if bal > 0.01 else ""
            self.tree.insert("", "end", values=(
                r.get("sales_invoice_no", ""),
                str(r.get("sales_invoice_date", ""))[:10],
                r.get("customer_name", ""),
                f"₹{total:,.2f}",
                f"₹{paid:,.2f}",
                f"₹{bal:,.2f}",
            ), tags=(tag,))

        self.tree.insert("", "end", values=(
            "TOTAL", "", "",
            f"₹{total_sales:,.2f}",
            f"₹{total_paid:,.2f}",
            f"₹{total_pending:,.2f}"
        ), tags=("total_row",))

    def _load_customer_wise_data(self, frm, to):
        rid = self.app.db.config.retailer_id
        query = """SELECT c.customer_name,
                          COUNT(DISTINCT si.sales_invoice_no) as invoices,
                          COALESCE(SUM(sm.sale_total_amount), 0) as total,
                          COALESCE(SUM(si.sales_invoice_paid), 0) as paid
                   FROM core_customermaster c
                   LEFT JOIN core_salesinvoicemaster si ON si.customerid_id = c.customerid
                   LEFT JOIN core_salesmaster sm ON sm.sales_invoice_no_id = si.sales_invoice_no
                   WHERE c.retailer_id=%s"""
        params = [rid]
        if frm:
            query += " AND si.sales_invoice_date >= %s"
            params.append(frm)
        if to:
            query += " AND si.sales_invoice_date <= %s"
            params.append(to)
        query += " GROUP BY c.customer_name HAVING COUNT(DISTINCT si.sales_invoice_no) > 0"
        query += " ORDER BY total DESC"

        rows = self.app.db.query(query, params)
        total_sales = sum(float(r.get("total") or 0) for r in rows)
        total_paid = sum(float(r.get("paid") or 0) for r in rows)
        total_pending = total_sales - total_paid

        self._var_total.set(f"₹{total_sales:,.2f}")
        self._var_paid.set(f"₹{total_paid:,.2f}")
        self._var_pending.set(f"₹{total_pending:,.2f}")

        for i in self.tree.get_children():
            self.tree.delete(i)

        for r in rows:
            total = float(r.get("total") or 0)
            paid = float(r.get("paid") or 0)
            bal = total - paid
            tag = "balance_red" if bal > 0.01 else ""
            self.tree.insert("", "end", values=(
                r.get("customer_name", ""),
                int(r.get("invoices") or 0),
                f"₹{total:,.2f}",
                f"₹{paid:,.2f}",
                f"₹{bal:,.2f}",
            ), tags=(tag,))

        self.tree.insert("", "end", values=(
            "TOTAL", len(rows),
            f"₹{total_sales:,.2f}",
            f"₹{total_paid:,.2f}",
            f"₹{total_pending:,.2f}"
        ), tags=("total_row",))

    # ── Export functions ──────────────────────────────────────────────────────

    def _export_excel(self):
        try:
            from ..invoice_export import export_report_excel
            import os
            from pathlib import Path
            from tkinter import filedialog
            
            # Get data from tree
            data = []
            headers = []
            totals = None
            
            if not self.tree:
                messagebox.showwarning("No Data", "No data to export", parent=self)
                return
                
            # Get headers
            if self._tab == "Customer Wise Sales":
                headers = ["Customer", "Invoices", "Total", "Paid", "Balance"]
            else:
                headers = ["Invoice No", "Date", 
                          "Supplier" if "Purchase" in self._tab else "Customer",
                          "Total", "Paid", "Balance"]
                          
            # Get data rows (excluding totals)
            for item in self.tree.get_children():
                values = self.tree.item(item, "values")
                tags = self.tree.item(item, "tags")
                if "total_row" in tags:
                    totals = list(values)
                else:
                    data.append(list(values))
            
            if not totals:
                totals = [""] * len(headers)
                
            # Ask for save location
            filename = f"{self._tab.replace(' ', '_')}_{date.today().isoformat()}.xlsx"
            filepath = filedialog.asksaveasfilename(
                title="Save Excel Report",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=filename,
                parent=self
            )
            
            if filepath:
                export_report_excel(
                    title=self._tab,
                    headers=headers,
                    rows=data,
                    totals_row=totals,
                    path=Path(filepath)
                )
                
                # Open the file
                if messagebox.askyesno("Export Complete", 
                                     f"Excel report saved successfully!\n\nOpen file now?", 
                                     parent=self):
                    os.startfile(filepath)
                    
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export Excel: {e}", parent=self)

    def _export_pdf(self):
        try:
            from ..invoice_export import export_report_pdf
            import os
            from pathlib import Path
            from tkinter import filedialog

            if not self.tree:
                messagebox.showwarning("No Data", "No data to export", parent=self)
                return

            if self._tab == "Customer Wise Sales":
                headers = ["Customer", "Invoices", "Total", "Paid", "Balance"]
            else:
                headers = ["Invoice No", "Date",
                          "Supplier" if "Purchase" in self._tab else "Customer",
                          "Total", "Paid", "Balance"]

            data = []
            totals = None
            for item in self.tree.get_children():
                values = self.tree.item(item, "values")
                tags = self.tree.item(item, "tags")
                if "total_row" in tags:
                    totals = list(values)
                else:
                    data.append(list(values))

            if not totals:
                totals = [""] * len(headers)

            summary = {
                "Total": self._var_total.get(),
                "Paid": self._var_paid.get(),
                "Pending": self._var_pending.get()
            }

            filename = f"{self._tab.replace(' ', '_')}_{date.today().isoformat()}.pdf"
            filepath = filedialog.asksaveasfilename(
                title="Save PDF Report",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=filename,
                parent=self
            )

            if filepath:
                export_report_pdf(
                    title=self._tab,
                    headers=headers,
                    rows=data,
                    totals_row=totals,
                    summary=summary,
                    path=Path(filepath)
                )
                messagebox.showinfo("Export Complete",
                                    f"PDF report saved to:\n{filepath}",
                                    parent=self)

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {e}", parent=self)

    def set_screen_name(self, name):
        if name in ("Purchases Report", "Sales Report", "Customer Wise Sales"):
            self._tab = name
            self._update_tabs()
            icons = {"Purchases Report": "🛒",
                     "Sales Report": "🧾",
                     "Customer Wise Sales": "👥"}
            self._title_lbl.config(text=f"{icons.get(name,'')} {name}")
            self._build_table()

    def kb_search(self):  self._e_from.focus_set()
    def kb_refresh(self): self.on_show()
    def kb_new(self):     self.on_show()
