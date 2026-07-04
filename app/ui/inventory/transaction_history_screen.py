"""Transaction History Screen - Product-wise transaction history."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

BG = "#f1f5f9"; CARD = "#ffffff"; BDR = "#e2e8f0"
TXT = "#1e293b"; MUTED = "#64748b"; HDR_BG = "#0f172a"
BLUE = "#3b82f6"; BLUE_H = "#2563eb"; BLUE_L = "#eff6ff"
GREEN = "#10b981"; RED = "#ef4444"; ORANGE = "#f59e0b"

class TransactionHistoryScreen(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.app = app_instance
        self._search_var = tk.StringVar()
        self._products = []
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        hdr_inner = tk.Frame(hdr, bg=HDR_BG, padx=20, pady=14)
        hdr_inner.pack(fill="x")
        
        left = tk.Frame(hdr_inner, bg=HDR_BG)
        left.pack(side="left")
        tk.Label(left, text="📜  Transaction History",
                 font=("Segoe UI", 16, "bold"), fg="white", bg=HDR_BG).pack(anchor="w")
        tk.Label(left, text="View product-wise transaction history",
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
            mode_frame, text="All Time", variable=self._mode_var, value="current",
            font=("Segoe UI", 9), bg="#1e3a5f", fg="white", selectcolor="#1e3a5f",
            activebackground="#2563eb", activeforeground="white",
            command=self.on_show, cursor="hand2"
        ).pack(side="left", padx=4)
        
        tk.Radiobutton(
            mode_frame, text="FY Only", variable=self._mode_var, value="fy",
            font=("Segoe UI", 9), bg="#1e3a5f", fg="white", selectcolor="#1e3a5f",
            activebackground="#2563eb", activeforeground="white",
            command=self.on_show, cursor="hand2"
        ).pack(side="left", padx=4)

        tk.Frame(self, bg=BDR, height=1).pack(fill="x")

        # Search bar
        search_frame = tk.Frame(self, bg=CARD, padx=20, pady=12,
                                highlightbackground=BDR, highlightthickness=1)
        search_frame.pack(fill="x", pady=(20,0), padx=20)
        
        tk.Label(search_frame, text="Search Product:", font=("Segoe UI", 9, "bold"),
                 fg=MUTED, bg=CARD).pack(side="left", padx=(0,10))
        
        wrap = tk.Frame(search_frame, bg=BDR)
        wrap.pack(side="left", fill="x", expand=True)
        inner = tk.Frame(wrap, bg="white")
        inner.pack(fill="x", padx=1, pady=1)
        
        tk.Label(inner, text="🔍", font=("Segoe UI", 10), fg=MUTED, bg="white").pack(side="left", padx=(8,4))
        search_entry = tk.Entry(inner, textvariable=self._search_var,
                               font=("Segoe UI", 10), relief="flat", bd=0,
                               bg="white", fg=TXT, width=40)
        search_entry.pack(side="left", ipady=6, fill="x", expand=True, padx=(0,8))
        search_entry.bind("<KeyRelease>", lambda e: self._load_products())

        # Products list
        self._fy_label = tk.StringVar(value="FY 2024-25")
        list_card = tk.Frame(self, bg=CARD, highlightbackground=BDR, highlightthickness=1)
        list_card.pack(fill="both", expand=True, padx=20, pady=(10,20))
        
        tbar = tk.Frame(list_card, bg=CARD, padx=16, pady=10)
        tbar.pack(fill="x")
        
        tbar_left = tk.Frame(tbar, bg=CARD)
        tbar_left.pack(side="left")
        tk.Label(tbar_left, text="Products", font=("Segoe UI", 11, "bold"),
                 fg=TXT, bg=CARD).pack(side="left")
        self._fy_badge = tk.Label(tbar_left, textvariable=self._fy_label,
                                  font=("Segoe UI", 8, "bold"), fg="white",
                                  bg=BLUE, padx=6, pady=2)
        self._fy_badge.pack(side="left", padx=8)
        
        tk.Frame(list_card, bg=BDR, height=1).pack(fill="x")

        # Treeview for products
        tree_frame = tk.Frame(list_card, bg=CARD)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        style = ttk.Style()
        style.configure("TH.Treeview", font=("Segoe UI", 10), rowheight=36,
                       background=CARD, fieldbackground=CARD, foreground=TXT)
        style.configure("TH.Treeview.Heading", font=("Segoe UI", 9, "bold"),
                       background="#f8fafc", foreground=MUTED)
        style.map("TH.Treeview",
                 background=[("selected", BLUE_L)],
                 foreground=[("selected", BLUE)])

        cols = ("PRODUCT NAME", "COMPANY", "TOTAL TRANSACTIONS", "CURRENT STOCK")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        self.product_tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                         yscrollcommand=vsb.set, style="TH.Treeview")
        vsb.config(command=self.product_tree.yview)
        
        for col in cols:
            self.product_tree.heading(col, text=col)
            self.product_tree.column(col, width=200, anchor="w" if col == "PRODUCT NAME" else "center")
        
        self.product_tree.tag_configure("odd", background="#f9fafb")
        self.product_tree.tag_configure("even", background=CARD)
        self.product_tree.bind("<Double-Button-1>", lambda e: self._show_history())
        self.product_tree.bind("<Return>", lambda e: self._show_history())
        
        self.product_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Instruction label
        tk.Label(list_card, text="💡 Double-click on any product to view its transaction history",
                 font=("Segoe UI", 9), fg=MUTED, bg=CARD).pack(pady=(0,10))

    def on_show(self):
        self._load_products()

    def _load_products(self):
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        search = self._search_var.get().strip().lower()
        
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
            query = """
                SELECT p.productid, p.product_name, p.product_company,
                       (SELECT COUNT(*) FROM inventory_transaction t 
                        WHERE t.product_id = p.productid AND t.retailer_id = %s"""
            
            # Add FY filter if in FY mode
            if current_mode == "fy" and fy_start and fy_end:
                query += " AND DATE(t.transaction_date) BETWEEN %s AND %s"
            
            query += """) as txn_count,
                       (SELECT COALESCE(SUM(CASE
                           WHEN t2.transaction_type IN ('PURCHASE') THEN t2.quantity + t2.free_quantity
                           WHEN t2.transaction_type IN ('PURCHASE_RETURN','REVERT_PURCHASE_RETURN','REVERT_PURCHASE') THEN -(t2.quantity + t2.free_quantity)
                           WHEN t2.transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') THEN -(t2.quantity + t2.free_quantity)
                           WHEN t2.transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') THEN (t2.quantity + t2.free_quantity)
                           ELSE 0 END), 0)
                        FROM inventory_transaction t2
                        WHERE t2.product_id = p.productid AND t2.retailer_id = %s"""
            
            # Add FY filter for stock calculation
            if current_mode == "fy" and fy_start and fy_end:
                query += " AND DATE(t2.transaction_date) BETWEEN %s AND %s"
            
            query += """) as total_stock
                FROM core_productmaster p
                WHERE p.retailer_id = %s
            """
            
            rid = self.app.config_data.retailer_id
            
            # Build params based on mode
            if current_mode == "fy" and fy_start and fy_end:
                base_params = (rid, fy_start, fy_end, rid, fy_start, fy_end, rid)
            else:
                base_params = (rid, rid, rid)
            
            if search:
                query += " AND (LOWER(p.product_name) LIKE %s OR LOWER(p.product_company) LIKE %s)"
                self._products = self.app.db.query(
                    query + " ORDER BY txn_count DESC, p.product_name LIMIT 500",
                    base_params + (f"%{search}%", f"%{search}%")
                )
            else:
                self._products = self.app.db.query(
                    query + " ORDER BY txn_count DESC, p.product_name LIMIT 500",
                    base_params
                )
            
            for idx, prod in enumerate(self._products):
                tag = "odd" if idx % 2 else "even"
                self.product_tree.insert("", "end", tags=(tag,), values=(
                    prod['product_name'],
                    prod['product_company'],
                    prod['txn_count'] or 0,
                    int(prod['total_stock'] or 0)
                ))
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to load products: {str(ex)}", parent=self)

    def _show_history(self):
        sel = self.product_tree.selection()
        if not sel:
            return
        
        item = self.product_tree.item(sel[0])
        values = item['values']
        if not values:
            return
            
        product_name = values[0]
        company = values[1]
        
        # Find product_id
        product_id = None
        for p in self._products:
            if p['product_name'] == product_name and p['product_company'] == company:
                product_id = p['productid']
                break
        
        if product_id:
            # Pass mode to dialog
            mode = getattr(self, '_mode_var', None)
            current_mode = mode.get() if mode else "current"
            self.app._transaction_history_mode = current_mode
            ProductHistoryDialog(self, self.app, product_id, product_name, company)


class ProductHistoryDialog(tk.Toplevel):
    def __init__(self, parent, app, product_id, product_name, company):
        super().__init__(parent)
        self.app = app
        self.product_id = product_id
        
        self.title(f"Transaction History - {product_name}")
        self.geometry("1100x650")
        self.configure(bg=BG)
        self.transient(parent)
        
        # Header
        hdr = tk.Frame(self, bg=HDR_BG, padx=20, pady=16)
        hdr.pack(fill="x")
        
        tk.Label(hdr, text=f"📊 {product_name}", font=("Segoe UI", 14, "bold"),
                 fg="white", bg=HDR_BG).pack(anchor="w")
        tk.Label(hdr, text=f"Company: {company}", font=("Segoe UI", 9),
                 fg="#94a3b8", bg=HDR_BG).pack(anchor="w")

        # Stats
        stat_frame = tk.Frame(self, bg=BG, padx=20, pady=10)
        stat_frame.pack(fill="x")
        
        self._total_in = tk.StringVar(value="0")
        self._total_out = tk.StringVar(value="0")
        self._current_stock = tk.StringVar(value="0")
        
        self._stat_card(stat_frame, "📥 Total In", self._total_in, GREEN, "#f0fdf4").pack(side="left", padx=5)
        self._stat_card(stat_frame, "📤 Total Out", self._total_out, RED, "#fef2f2").pack(side="left", padx=5)
        self._stat_card(stat_frame, "📦 Current Stock", self._current_stock, BLUE, BLUE_L).pack(side="left", padx=5)

        # History table
        table_card = tk.Frame(self, bg=CARD, highlightbackground=BDR, highlightthickness=1)
        table_card.pack(fill="both", expand=True, padx=20, pady=(0,20))
        
        tk.Label(table_card, text="Transaction History", font=("Segoe UI", 11, "bold"),
                 fg=TXT, bg=CARD).pack(anchor="w", padx=16, pady=10)
        tk.Frame(table_card, bg=BDR, height=1).pack(fill="x")

        tree_frame = tk.Frame(table_card, bg=CARD)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        cols = ("DATE", "TYPE", "INVOICE NO", "BATCH", "QUANTITY", "RATE", "AMOUNT", "PARTY")
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        self.history_tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                         yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                         style="TH.Treeview", height=15)
        vsb.config(command=self.history_tree.yview)
        hsb.config(command=self.history_tree.xview)
        
        widths = [100, 100, 110, 100, 80, 90, 100, 150]
        for col, w in zip(cols, widths):
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=w, anchor="center")
        
        self.history_tree.tag_configure("purchase", foreground=GREEN)
        self.history_tree.tag_configure("sale", foreground=RED)
        self.history_tree.tag_configure("odd", background="#f9fafb")
        self.history_tree.tag_configure("even", background=CARD)
        
        self.history_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self._load_history()

    def _stat_card(self, parent, label, var, color, bg_color):
        card = tk.Frame(parent, bg=bg_color, highlightbackground=BDR, highlightthickness=1)
        inner = tk.Frame(card, bg=bg_color, padx=16, pady=10)
        inner.pack()
        tk.Label(inner, text=label, font=("Segoe UI", 8, "bold"),
                 fg=MUTED, bg=bg_color).pack(anchor="w")
        tk.Label(inner, textvariable=var, font=("Segoe UI", 14, "bold"),
                 fg=color, bg=bg_color).pack(anchor="w")
        return card

    def _load_history(self):
        try:
            rid = self.app.config_data.retailer_id
            
            # Get FY dates and mode
            fy_start = getattr(self.app, 'current_fy_start', None)
            fy_end = getattr(self.app, 'current_fy_end', None)
            mode = getattr(self.app, '_mode_var', None)
            current_mode = mode.get() if mode else "current"
            
            # Base query
            base_query = """
                SELECT t.transaction_date as date, t.transaction_type as type,
                       t.reference_number as invoice_no, t.batch_no,
                       t.quantity, t.rate, t.total_value as amount,
                       CASE 
                           WHEN t.transaction_type = 'PURCHASE' THEN
                               COALESCE((SELECT s.supplier_name FROM core_suppliermaster s 
                                         JOIN core_invoicemaster i ON s.supplierid = i.supplierid_id 
                                         WHERE i.invoiceid = t.reference_id LIMIT 1), 'N/A')
                           WHEN t.transaction_type = 'SALE' THEN
                               COALESCE((SELECT c.customer_name FROM core_customermaster c 
                                         JOIN core_salesinvoicemaster si ON c.customerid = si.customerid_id 
                                         WHERE si.sales_invoice_no = t.reference_number LIMIT 1), 'N/A')
                           WHEN t.transaction_type = 'PURCHASE_RETURN' THEN
                               COALESCE((SELECT s.supplier_name FROM core_suppliermaster s 
                                         JOIN core_returninvoicemaster ri ON s.supplierid = ri.returnsupplierid_id 
                                         WHERE ri.returninvoiceid = t.reference_number LIMIT 1), 'N/A')
                           WHEN t.transaction_type = 'SALES_RETURN' THEN
                               COALESCE((SELECT c.customer_name FROM core_customermaster c 
                                         JOIN core_returnsalesinvoicemaster rsi ON c.customerid = rsi.return_sales_customerid_id 
                                         WHERE rsi.return_sales_invoice_no = t.reference_number LIMIT 1), 'N/A')
                           WHEN t.transaction_type = 'STOCK_ISSUE' THEN 'Internal Issue'
                           ELSE 'System'
                       END as party
                FROM inventory_transaction t
                WHERE t.product_id = %s AND t.retailer_id = %s"""
            
            params = [self.product_id, rid]
            
            # Add FY filter if in FY mode
            parent_mode = getattr(self.app, '_transaction_history_mode', None)
            if parent_mode and parent_mode == "fy" and fy_start and fy_end:
                base_query += " AND DATE(t.transaction_date) BETWEEN %s AND %s"
                params.extend([fy_start, fy_end])
            
            base_query += " ORDER BY t.transaction_date DESC"
            
            # Get transactions
            transactions = self.app.db.query(base_query, tuple(params))
            
            # Calculate totals
            total_in = 0
            total_out = 0
            
            for txn in transactions:
                qty = float(txn['quantity'] or 0)
                if txn['type'] in ('PURCHASE', 'SALES_RETURN'):
                    total_in += qty
                elif txn['type'] in ('SALE', 'PURCHASE_RETURN', 'STOCK_ISSUE'):
                    total_out += qty
            
            # Get current stock with FY filter if needed
            stock_query = """
                SELECT COALESCE(SUM(CASE
                    WHEN transaction_type IN ('PURCHASE') THEN quantity + free_quantity
                    WHEN transaction_type IN ('PURCHASE_RETURN','REVERT_PURCHASE_RETURN','REVERT_PURCHASE') THEN -(quantity + free_quantity)
                    WHEN transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') THEN -(quantity + free_quantity)
                    WHEN transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') THEN (quantity + free_quantity)
                    ELSE 0 END), 0) AS stock
                FROM inventory_transaction
                WHERE product_id = %s AND retailer_id = %s
            """
            stock_params = [self.product_id, rid]
            
            if parent_mode and parent_mode == "fy" and fy_start and fy_end:
                stock_query += " AND DATE(transaction_date) BETWEEN %s AND %s"
                stock_params.extend([fy_start, fy_end])
            
            stock_result = self.app.db.query(stock_query, tuple(stock_params))
            current_stock = int(stock_result[0]['stock']) if stock_result else 0
            
            self._total_in.set(f"{int(total_in)}")
            self._total_out.set(f"{int(total_out)}")
            self._current_stock.set(str(current_stock))
            
            # Display in tree
            for idx, txn in enumerate(transactions):
                # Determine transaction display type
                txn_type = txn['type']
                if txn_type == 'PURCHASE':
                    display_type = 'PURCHASE'
                    tag = 'purchase'
                elif txn_type == 'SALE':
                    display_type = 'SALE'
                    tag = 'sale'
                elif txn_type == 'PURCHASE_RETURN':
                    display_type = 'PURCHASE RTN'
                    tag = 'sale'
                elif txn_type == 'SALES_RETURN':
                    display_type = 'SALES RTN'
                    tag = 'purchase'
                elif txn_type == 'STOCK_ISSUE':
                    display_type = 'STOCK ISSUE'
                    tag = 'sale'
                else:
                    display_type = txn_type
                    tag = 'purchase'
                
                bg_tag = "odd" if idx % 2 else "even"
                
                self.history_tree.insert("", "end", tags=(tag, bg_tag), values=(
                    str(txn['date'])[:10] if txn['date'] else 'N/A',
                    display_type,
                    txn['invoice_no'] or 'N/A',
                    txn['batch_no'] or 'N/A',
                    int(txn['quantity'] or 0),
                    f"₹{float(txn['rate'] or 0):.2f}",
                    f"₹{float(txn['amount'] or 0):.2f}",
                    txn['party'] or 'N/A'
                ))
            
        except Exception as ex:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to load history: {str(ex)}", parent=self)
