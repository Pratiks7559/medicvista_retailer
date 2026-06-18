"""Batch-wise Inventory Report — Premium UI."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from ...styles import COLORS, FONT

BG     = "#f1f5f9"; CARD   = "#ffffff"; BDR    = "#e2e8f0"
TXT    = "#1e293b"; MUTED  = "#64748b"; HDR_BG = "#0f172a"
BLUE   = "#3b82f6"; BLUE_H = "#2563eb"; BLUE_L = "#eff6ff"
GREEN  = "#10b981"; GREEN_H= "#059669"; GREEN_L= "#f0fdf4"
RED    = "#ef4444"; RED_H  = "#dc2626"
TEAL   = "#14b8a6"; TEAL_H = "#0f9488"; TEAL_L = "#f0fdfa"
INDIGO = "#6366f1"; GRAY   = "#6b7280"
ORANGE = "#f59e0b"; ORANGE_L="#fffbeb"
PROD_BG= "#eff6ff"; PROD_FG= "#1d4ed8"


def _btn(p, text, bg, hover, cmd=None, padx=14, pady=8):
    b = tk.Button(p, text=text, bg=bg, fg="white",
                  font=("Segoe UI", 10, "bold"), bd=0, relief="flat",
                  padx=padx, pady=pady, cursor="hand2",
                  activebackground=hover, activeforeground="white", command=cmd)
    b.bind("<Enter>", lambda e: b.config(bg=hover))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


class BatchWiseScreen(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.app = app_instance
        self._search_var = tk.StringVar()
        self._rows: list = []
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        hdr_inner = tk.Frame(hdr, bg=HDR_BG, padx=20, pady=14)
        hdr_inner.pack(fill="x")

        left = tk.Frame(hdr_inner, bg=HDR_BG)
        left.pack(side="left")
        tk.Label(left, text="📦  Batch-wise Inventory Report",
                 font=("Segoe UI", 16, "bold"), fg="white", bg=HDR_BG).pack(anchor="w")
        tk.Label(left, text="Detailed batch-level stock including zero-stock batches",
                 font=("Segoe UI", 9), fg="#94a3b8", bg=HDR_BG).pack(anchor="w")

        right = tk.Frame(hdr_inner, bg=HDR_BG)
        right.pack(side="right")
        
        # View Mode Toggle
        mode_frame = tk.Frame(right, bg="#1e3a5f", relief="flat")
        mode_frame.pack(side="left", padx=(0, 10))
        
        tk.Label(mode_frame, text="View:", font=("Segoe UI", 9, "bold"),
                 fg="#93c5fd", bg="#1e3a5f", padx=8, pady=6).pack(side="left")
        
        self._mode_var = tk.StringVar(value="current")
        
        tk.Radiobutton(
            mode_frame, text="Current Stock", variable=self._mode_var, value="current",
            font=("Segoe UI", 9), bg="#1e3a5f", fg="white", selectcolor="#1e3a5f",
            activebackground="#2563eb", activeforeground="white",
            command=self.on_show, cursor="hand2"
        ).pack(side="left", padx=4)
        
        tk.Radiobutton(
            mode_frame, text="FY Movement", variable=self._mode_var, value="fy",
            font=("Segoe UI", 9), bg="#1e3a5f", fg="white", selectcolor="#1e3a5f",
            activebackground="#2563eb", activeforeground="white",
            command=self.on_show, cursor="hand2"
        ).pack(side="left", padx=4)
        
        _btn(right, "📅 Date-wise", TEAL,  TEAL_H,   cmd=lambda: self.app.show_screen("Date-wise Report")).pack(side="left", padx=(0,6))
        _btn(right, "📊 Excel",     GREEN, GREEN_H,  cmd=self._export_excel).pack(side="left", padx=(0,6))
        _btn(right, "📄 PDF",       RED,   RED_H,    cmd=self._export_pdf).pack(side="left")

        tk.Frame(self, bg=BDR, height=1).pack(fill="x")

        # ── Stat strip ────────────────────────────────────────────────────
        self._total_products = tk.StringVar(value="0")
        self._total_batches  = tk.StringVar(value="0")
        self._total_value    = tk.StringVar(value="₹0.00")
        self._fy_label = tk.StringVar(value="FY 2024-25")

        stat_row = tk.Frame(self, bg=BG, padx=20, pady=12)
        stat_row.pack(fill="x")

        stat_items = [
            ("Total Products",  self._total_products, "💊", BLUE,   BLUE_L),
            ("Total Batches",   self._total_batches,  "📦", TEAL,   TEAL_L),
            ("Total Value",     self._total_value,    "₹",  GREEN,  GREEN_L),
        ]
        for idx, (label, var, icon, color, bg_c) in enumerate(stat_items):
            c = tk.Frame(stat_row, bg=bg_c, highlightbackground=BDR, highlightthickness=1)
            c.pack(side="left", padx=5, ipadx=16, ipady=10)
            tk.Label(c, text=icon, font=("Segoe UI", 20), fg=color, bg=bg_c).pack(side="left", padx=(12,8))
            sub = tk.Frame(c, bg=bg_c); sub.pack(side="left")
            tk.Label(sub, text=label, font=("Segoe UI", 8, "bold"), fg=MUTED, bg=bg_c).pack(anchor="w")
            tk.Label(sub, textvariable=var, font=("Segoe UI", 16, "bold"), fg=TXT, bg=bg_c).pack(anchor="w")

        # ── Search bar ────────────────────────────────────────────────────
        srch_card = tk.Frame(self, bg=CARD, padx=20, pady=12,
                              highlightbackground=BDR, highlightthickness=1)
        srch_card.pack(fill="x")
        tk.Frame(srch_card, bg=BDR, height=1).pack(fill="x", side="bottom")
        srch_inner = tk.Frame(srch_card, bg=CARD)
        srch_inner.pack(fill="x")

        wrap = tk.Frame(srch_inner, bg=BDR, bd=0)
        wrap.pack(side="left", fill="x", expand=True, padx=(0,12))
        i_wrap = tk.Frame(wrap, bg="white", bd=0)
        i_wrap.pack(fill="x", padx=1, pady=1)
        tk.Label(i_wrap, text="🔍", font=("Segoe UI", 10), fg=MUTED, bg="white").pack(side="left", padx=(10,0))
        self._e_search = tk.Entry(i_wrap, textvariable=self._search_var,
                                   font=("Segoe UI", 10), relief="flat", bd=0,
                                   bg="white", fg=TXT, insertbackground=BLUE)
        self._e_search.pack(side="left", fill="x", expand=True, padx=6, ipady=8)
        self._e_search.insert(0, "Search products, companies…")
        self._e_search.bind("<FocusIn>",  self._clr)
        self._e_search.bind("<FocusOut>", self._rst)
        self._e_search.bind("<Return>",   lambda e: self.on_show())

        _btn(srch_inner, "🔍 Search", BLUE,  BLUE_H,    cmd=self.on_show, pady=7).pack(side="left", padx=(0,6))
        _btn(srch_inner, "⟳ Reset",   GRAY,  "#4b5563", cmd=self._reset,  pady=7).pack(side="left")

        # ── Table ─────────────────────────────────────────────────────────
        tbl_card = tk.Frame(self, bg=CARD, highlightbackground=BDR, highlightthickness=1)
        tbl_card.pack(fill="both", expand=True)

        tbar = tk.Frame(tbl_card, bg=CARD, padx=16, pady=10)
        tbar.pack(fill="x")
        tk.Frame(tbar, bg=BDR, height=1).pack(fill="x", side="bottom")
        
        tbar_left = tk.Frame(tbar, bg=CARD)
        tbar_left.pack(side="left")
        tk.Label(tbar_left, text="Batch-wise Stock Details",
                 font=("Segoe UI", 11, "bold"), fg=TXT, bg=CARD).pack(side="left")
        self._fy_badge = tk.Label(tbar_left, textvariable=self._fy_label,
                                  font=("Segoe UI", 8, "bold"), fg="white",
                                  bg=BLUE, padx=6, pady=2)
        self._fy_badge.pack(side="left", padx=8)
        
        self._count_var = tk.StringVar(value="")
        tk.Label(tbar, textvariable=self._count_var,
                 font=("Segoe UI", 9), fg=MUTED, bg=CARD).pack(side="left", padx=10)
        tk.Label(tbar, text="Click ▶ to expand product batches",
                 font=("Segoe UI", 8), fg=MUTED, bg=CARD).pack(side="right")

        style = ttk.Style()
        style.configure("BW.Treeview", font=("Segoe UI", 10), rowheight=34,
                         background=CARD, fieldbackground=CARD, foreground=TXT, borderwidth=0)
        style.configure("BW.Treeview.Heading", font=("Segoe UI", 9, "bold"),
                         background="#f8fafc", foreground=MUTED, relief="flat")
        style.map("BW.Treeview",
                  background=[("selected", BLUE_L)],
                  foreground=[("selected", BLUE)])

        cols   = ("PRODUCT NAME","COMPANY","PACKING","BATCH NO","EXPIRY","STOCK QTY","FREE QTY","MRP","STOCK VALUE")
        widths = (210, 130, 80, 120, 90, 90, 80, 90, 110)

        frm = tk.Frame(tbl_card, bg=CARD)
        frm.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(frm, orient="vertical")
        hsb = ttk.Scrollbar(frm, orient="horizontal")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings",
                                  yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                  selectmode="browse", style="BW.Treeview")
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col, anchor="w")
            self.tree.column(col, width=w, anchor="w" if col == "PRODUCT NAME" else "center")
        self.tree.tag_configure("prod",  background=PROD_BG, foreground=PROD_FG,
                                 font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure("batch_odd",  background="#f9fafb", foreground=TXT)
        self.tree.tag_configure("batch_even", background=CARD,       foreground=TXT)
        self.tree.tag_configure("zero",  foreground="#9ca3af")
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frm.grid_rowconfigure(0, weight=1)
        frm.grid_columnconfigure(0, weight=1)

        # Footer
        foot = tk.Frame(tbl_card, bg="#f8fafc", padx=16, pady=10)
        foot.pack(fill="x")
        tk.Frame(foot, bg=BDR, height=1).pack(fill="x", side="top")
        self._footer_var = tk.StringVar(value="Page Total Value:  ₹0.00")
        tk.Label(foot, textvariable=self._footer_var,
                 font=("Segoe UI", 11, "bold"), fg=TXT, bg="#f8fafc").pack(side="right", pady=(6,0))

        self.bind_all("<Control-e>", lambda e: self._export_excel())
        self.bind_all("<Control-q>", lambda e: self._export_pdf())

    def _clr(self, e):
        if self._e_search.get() == "Search products, companies…":
            self._e_search.delete(0, "end"); self._e_search.config(fg=TXT)

    def _rst(self, e):
        if not self._e_search.get():
            self._e_search.insert(0, "Search products, companies…"); self._e_search.config(fg=MUTED)

    def _reset(self):
        self._search_var.set("")
        self._e_search.delete(0, "end")
        self._e_search.insert(0, "Search products, companies…"); self._e_search.config(fg=MUTED)
        self.on_show()

    def on_show(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        term = self._search_var.get()
        if term == "Search products, companies…": term = ""
        
        # Get FY dates and mode
        fy_start = getattr(self.app, 'current_fy_start', None)
        fy_end = getattr(self.app, 'current_fy_end', None)
        mode = getattr(self, '_mode_var', None)
        current_mode = mode.get() if mode else "current"
        
        # Update FY badge
        if hasattr(self.app, 'fy_var') and self.app.fy_var:
            fy_text = self.app.fy_var.get()
            self._fy_label.set(f"FY {fy_text}")
        
        try:
            if current_mode == "fy" and fy_start and fy_end:
                self._rows = self._fetch_fy_inventory(term, fy_start, fy_end)
            else:
                self._rows = self.app.db.fetch_inventory(term)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self); return

        from collections import defaultdict
        groups: dict = defaultdict(list)
        for r in self._rows:
            groups[(r.get("name",""), r.get("company",""), r.get("packing",""))].append(r)

        total_val = 0.0; batch_count = 0
        for (name, company, packing), batches in groups.items():
            def _fv(v):
                try: return float(str(v or 0).replace("₹","").replace(",","").strip())
                except: return 0.0
            prod_val = sum(_fv(b.get("value", 0)) for b in batches)
            total_val += prod_val
            n_batches = len(batches)
            batch_count += n_batches

            prod_iid = f"p_{name}_{company}"
            self.tree.insert("", "end", iid=prod_iid, tags=("prod",), values=(
                f"▶  {name}", company, packing,
                f"{n_batches} batch{'es' if n_batches!=1 else ''}",
                "", "", "", "", f"₹{prod_val:,.2f}"
            ))
            for i, b in enumerate(batches):
                val = _fv(b.get("value", 0))
                stock = b.get("stock", b.get("current_stock", 0))
                tag = "zero" if float(stock or 0) == 0 else ("batch_odd" if i%2 else "batch_even")
                self.tree.insert(prod_iid, "end", tags=(tag,), values=(
                    f"    └  {name}", company, packing,
                    b.get("batch_no", ""),
                    b.get("expiry", ""),
                    stock,
                    b.get("current_free_qty", ""),
                    f"₹{float(str(b.get('mrp',0)).replace('₹','').replace(',','').strip() or 0):.2f}",
                    f"₹{val:,.2f}",
                ))
            self.tree.item(prod_iid, open=True)

        n = len(groups)
        self._total_products.set(str(n))
        self._total_batches.set(str(batch_count))
        self._total_value.set(f"₹{total_val:,.2f}")
        self._count_var.set(f"{n} product{'s' if n!=1 else ''},  {batch_count} batches")
        self._footer_var.set(f"Page Total Value:  ₹{total_val:,.2f}")

    def _export_excel(self):
        if not self._rows: messagebox.showinfo("No Data", "Load data first.", parent=self); return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx",
            filetypes=[("Excel","*.xlsx")], initialfile="BatchWise_Inventory.xlsx", parent=self)
        if not path: return
        try:
            from ..invoice_export import export_inventory_excel
            export_inventory_excel(self._rows, Path(path))
            messagebox.showinfo("Exported", f"Saved:\n{path}", parent=self)
        except Exception as e: messagebox.showerror("Error", str(e), parent=self)

    def _export_pdf(self):
        if not self._rows: messagebox.showinfo("No Data", "Load data first.", parent=self); return
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
            filetypes=[("PDF","*.pdf")], initialfile="BatchWise_Inventory.pdf", parent=self)
        if not path: return
        try:
            from ..invoice_export import export_inventory_pdf
            export_inventory_pdf(self._rows, Path(path))
            messagebox.showinfo("Exported", f"Saved:\n{path}", parent=self)
        except Exception as e: messagebox.showerror("Error", str(e), parent=self)

    def kb_refresh(self): self.on_show()
    def kb_search(self): self._clr(None); self._e_search.focus_set()
    
    def _fetch_fy_inventory(self, search, fy_start, fy_end):
        rid = self.app.config_data.retailer_id
        if search:
            search_clause = " AND (p.product_name LIKE %s OR p.product_company LIKE %s)"
            search_params = (f"%{search}%", f"%{search}%")
        else:
            search_clause = ""
            search_params = ()
        
        query = f"""
            SELECT p.product_name AS name, p.product_company AS company,
                   p.product_packing AS packing, p.product_category AS category,
                   t.batch_no, t.expiry_date AS expiry,
                   COALESCE(MAX(t.mrp), 0) AS mrp, COALESCE(MAX(t.rate), 0) AS purchase_rate,
                   COALESCE(SUM(CASE WHEN DATE(t.transaction_date) < %s THEN
                       CASE WHEN t.transaction_type = 'PURCHASE' THEN t.quantity
                            WHEN t.transaction_type = 'PURCHASE_RETURN' THEN -t.quantity
                            WHEN t.transaction_type IN ('SALE','STOCK_ISSUE') THEN -t.quantity
                            WHEN t.transaction_type = 'SALES_RETURN' THEN t.quantity
                            ELSE 0 END ELSE 0 END), 0) AS opening_stock,
                   COALESCE(SUM(CASE WHEN DATE(t.transaction_date) BETWEEN %s AND %s 
                       AND t.transaction_type = 'PURCHASE' THEN t.quantity ELSE 0 END), 0) AS fy_purchases,
                   COALESCE(SUM(CASE WHEN DATE(t.transaction_date) BETWEEN %s AND %s 
                       AND t.transaction_type = 'SALE' THEN t.quantity ELSE 0 END), 0) AS fy_sales,
                   COALESCE(SUM(CASE WHEN t.transaction_type = 'PURCHASE' THEN t.quantity
                       WHEN t.transaction_type = 'PURCHASE_RETURN' THEN -t.quantity
                       WHEN t.transaction_type IN ('SALE','STOCK_ISSUE') THEN -t.quantity
                       WHEN t.transaction_type = 'SALES_RETURN' THEN t.quantity
                       ELSE 0 END), 0) AS stock,
                   0 AS current_free_qty, 0 AS rate_a, 0 AS rate_b, 0 AS rate_c
            FROM inventory_transaction t
            JOIN core_productmaster p ON p.productid = t.product_id
            WHERE t.retailer_id = %s{search_clause}
            GROUP BY p.productid, p.product_name, p.product_company, p.product_packing,
                     p.product_category, t.batch_no, t.expiry_date
            HAVING stock > 0 OR opening_stock != 0 OR fy_purchases > 0 OR fy_sales > 0
            ORDER BY p.product_name, t.expiry_date LIMIT 500
        """
        params = (fy_start, fy_start, fy_end, fy_start, fy_end, rid) + search_params
        try:
            rows = self.app.db.query(query, params)
        except Exception as e:
            import logging
            logging.error(f"FY query error: {e}")
            return []
        for r in rows:
            stock = float(r.get("stock") or 0)
            rate = float(r.get("purchase_rate") or 0)
            r["value"] = f"₹{round(stock * rate, 2):.2f}"
        return rows
