import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

BG      = "#f1f5f9"; CARD    = "#ffffff"; BDR     = "#e2e8f0"
TXT     = "#1e293b"; MUTED   = "#64748b"; DARK    = "#0f172a"
BLUE    = "#3b82f6"; BLUE_H  = "#2563eb"; BLUE_L  = "#eff6ff"
GREEN   = "#10b981"; GREEN_H = "#059669"; GREEN_L = "#f0fdf4"
RED     = "#ef4444"; RED_H   = "#dc2626"; RED_L   = "#fef2f2"
ORANGE  = "#f59e0b"; ORANGE_H= "#d97706"; ORANGE_L= "#fffbeb"
TEAL    = "#14b8a6"; TEAL_H  = "#0f9488"
GRAY    = "#6b7280"; INDIGO  = "#6366f1"
HDR_BG  = "#0f172a"; HDR2    = "#1e293b"


# ── Shared Helpers ────────────────────────────────────────────────────────────

def _btn(parent, text, bg, hover, cmd=None, padx=14, pady=8):
    """Create a flat, hover-aware button."""
    b = tk.Button(
        parent, text=text, bg=bg, fg="white",
        font=("Segoe UI", 10, "bold"), bd=0, relief="flat",
        padx=padx, pady=pady, cursor="hand2",
        activebackground=hover, activeforeground="white", command=cmd
    )
    b.bind("<Enter>", lambda e: b.config(bg=hover))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def _stat_card(parent, label, var, icon, color, bg_c, last=False):
    """Stat summary card using uniform padding."""
    c = tk.Frame(parent, bg=bg_c, highlightbackground=BDR, highlightthickness=1)
    c.pack(side="left", expand=True, fill="x", padx=5)

    top = tk.Frame(c, bg=bg_c, padx=14, pady=12)
    top.pack(fill="x")

    left = tk.Frame(top, bg=bg_c)
    left.pack(side="left", fill="x", expand=True)
    tk.Label(left, text=label,
             font=("Segoe UI", 8, "bold"), fg=MUTED, bg=bg_c).pack(anchor="w")
    tk.Label(left, textvariable=var,
             font=("Segoe UI", 18, "bold"), fg=TXT, bg=bg_c).pack(anchor="w")

    tk.Label(top, text=icon, font=("Segoe UI", 22), fg=color, bg=bg_c).pack(side="right")
    tk.Frame(c, bg=color, height=3).pack(fill="x", side="bottom")


def _safe_float(val, default=0.0):
    """Safely convert a value to float, stripping ₹ and commas."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(str(val).replace("₹", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return default


def _fmt_date(dt):
    """Return dd/mm/yyyy string from a datetime object or string; 'N/A' on failure."""
    if dt is None:
        return "N/A"
    if isinstance(dt, datetime):
        return dt.strftime("%d/%m/%Y")
    return str(dt)


# ── Inventory Screen ──────────────────────────────────────────────────────────

class InventoryScreen(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.app = app_instance
        self._search_var = tk.StringVar()
        self._rows: list = []
        self._debounce_id = None
        self._build()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        self._build_header()
        tk.Frame(self, bg=BDR, height=1).pack(fill="x")
        self._build_stat_cards()
        self._build_search_bar()
        self._build_table()

    def _build_header(self):
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        inner = tk.Frame(hdr, bg=HDR_BG, padx=20, pady=14)
        inner.pack(fill="x")

        left = tk.Frame(inner, bg=HDR_BG)
        left.pack(side="left")
        tk.Label(left, text="💊  All Products Inventory",
                 font=("Segoe UI", 16, "bold"), fg="white", bg=HDR_BG).pack(anchor="w")
        tk.Label(left, text="Real-time stock levels across all products and batches",
                 font=("Segoe UI", 9), fg="#94a3b8", bg=HDR_BG).pack(anchor="w")

        right = tk.Frame(inner, bg=HDR_BG)
        right.pack(side="right")
        
        # View Mode Toggle
        mode_frame = tk.Frame(right, bg="#1e3a5f", relief="flat")
        mode_frame.pack(side="left", padx=(0, 10))
        
        tk.Label(mode_frame, text="View:", font=("Segoe UI", 9, "bold"),
                 fg="#93c5fd", bg="#1e3a5f", padx=8, pady=6).pack(side="left")
        
        self._mode_var = tk.StringVar(value="current")
        
        mode_current = tk.Radiobutton(
            mode_frame, text="Current Stock", variable=self._mode_var, value="current",
            font=("Segoe UI", 9), bg="#1e3a5f", fg="white", selectcolor="#1e3a5f",
            activebackground="#2563eb", activeforeground="white",
            command=self.on_show, cursor="hand2"
        )
        mode_current.pack(side="left", padx=4)
        
        mode_fy = tk.Radiobutton(
            mode_frame, text="FY Movement", variable=self._mode_var, value="fy",
            font=("Segoe UI", 9), bg="#1e3a5f", fg="white", selectcolor="#1e3a5f",
            activebackground="#2563eb", activeforeground="white",
            command=self.on_show, cursor="hand2"
        )
        mode_fy.pack(side="left", padx=4)
        
        _btn(right, "≡ Batch-wise",  TEAL,      TEAL_H,    cmd=self._open_batch_wise).pack(side="left", padx=(0, 6))
        _btn(right, "📅 Date-wise",  INDIGO,    "#4f46e5", cmd=self._open_date_wise).pack(side="left", padx=(0, 6))
        _btn(right, "↻ Refresh",     GREEN,     GREEN_H,   cmd=self.on_show).pack(side="left", padx=(0, 6))
        _btn(right, "📊 Excel",      "#059669", "#047857", cmd=self._export_excel).pack(side="left", padx=(0, 6))
        _btn(right, "📄 PDF",        RED,       RED_H,     cmd=self._export_pdf).pack(side="left")

    def _build_stat_cards(self):
        self._stat_vars = {
            "products": tk.StringVar(value="0"),
            "value":    tk.StringVar(value="₹0.00"),
            "low":      tk.StringVar(value="0"),
            "out":      tk.StringVar(value="0"),
        }
        row = tk.Frame(self, bg=BG, padx=20, pady=14)
        row.pack(fill="x")
        # FIX: pass last=True to the final card so it gets no right padding
        _stat_card(row, "Total Products",        self._stat_vars["products"], "💊", BLUE,   BLUE_L)
        _stat_card(row, "Total Inventory Value", self._stat_vars["value"],    "₹",  GREEN,  GREEN_L)
        _stat_card(row, "Low Stock Items",       self._stat_vars["low"],      "⚠",  ORANGE, ORANGE_L)
        _stat_card(row, "Out of Stock",          self._stat_vars["out"],      "✖",  RED,    RED_L,  last=True)

    def _build_search_bar(self):
        card = tk.Frame(self, bg=CARD, padx=20, pady=12,
                        highlightbackground=BDR, highlightthickness=1)
        card.pack(fill="x")
        tk.Frame(card, bg=BDR, height=1).pack(fill="x", side="bottom")

        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="x")

        # search box with border wrapper
        wrap = tk.Frame(inner, bg=BDR)
        wrap.pack(side="left", fill="x", expand=True, padx=(0, 12))
        i_wrap = tk.Frame(wrap, bg="white")
        i_wrap.pack(fill="x", padx=1, pady=1)
        tk.Label(i_wrap, text="🔍", font=("Segoe UI", 10),
                 fg=MUTED, bg="white").pack(side="left", padx=(10, 0))
        self._search_entry = tk.Entry(
            i_wrap, textvariable=self._search_var,
            font=("Segoe UI", 10), relief="flat", bd=0,
            bg="white", fg=TXT, insertbackground=BLUE
        )
        self._search_entry.pack(side="left", fill="x", expand=True, padx=6, ipady=8)
        self._search_entry.insert(0, "Search products by name, company, HSN…")
        self._search_entry.bind("<FocusIn>",   self._clr)
        self._search_entry.bind("<FocusOut>",  self._rst)
        self._search_entry.bind("<Return>",    lambda e: self.on_show())
        self._search_entry.bind("<KeyRelease>",lambda e: self._debounce_search())

        _btn(inner, "🔍 Search", BLUE, BLUE_H, cmd=self.on_show, pady=7).pack(side="left", padx=(0, 6))
        _btn(inner, "⟳ Reset",   GRAY, "#4b5563", cmd=self._reset, pady=7).pack(side="left")

    def _build_table(self):
        card = tk.Frame(self, bg=CARD, highlightbackground=BDR, highlightthickness=1)
        card.pack(fill="both", expand=True)

        # Table toolbar
        tbar = tk.Frame(card, bg=CARD, padx=16, pady=10)
        tbar.pack(fill="x")
        tk.Frame(tbar, bg=BDR, height=1).pack(fill="x", side="bottom")

        tbar_left = tk.Frame(tbar, bg=CARD)
        tbar_left.pack(side="left")
        tk.Label(tbar_left, text="All Products Inventory",
                 font=("Segoe UI", 11, "bold"), fg=TXT, bg=CARD).pack(side="left")
        self._fy_badge = tk.Label(tbar_left, text=" FY 2026-27 ",
                                  font=("Segoe UI", 8, "bold"), fg="white",
                                  bg=BLUE, padx=6, pady=2)
        self._fy_badge.pack(side="left", padx=8)
        self._count_var = tk.StringVar(value="")
        tk.Label(tbar, textvariable=self._count_var,
                 font=("Segoe UI", 9), fg=MUTED, bg=CARD).pack(side="right")
        tk.Label(tbar, text="💡 Click ▶ to expand batches | Double-click for history",
                 font=("Segoe UI", 8), fg=MUTED, bg=CARD).pack(side="right", padx=10)

        # Treeview styling
        style = ttk.Style()
        style.configure("Inv.Treeview",
                         font=("Segoe UI", 10), rowheight=36,
                         background=CARD, fieldbackground=CARD,
                         foreground=TXT, borderwidth=0)
        style.configure("Inv.Treeview.Heading",
                         font=("Segoe UI", 9, "bold"),
                         background="#f8fafc", foreground=MUTED, relief="flat")
        style.map("Inv.Treeview",
                  background=[("selected", BLUE_L)],
                  foreground=[("selected", BLUE)])

        cols   = ("Product Info", "Batches", "Total Stock", "Stock Value", "Status", "Actions")
        widths = (280, 80, 120, 120, 100, 80)

        frm = tk.Frame(card, bg=CARD)
        frm.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(frm, orient="vertical")
        hsb = ttk.Scrollbar(frm, orient="horizontal")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings",
                                  yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                  selectmode="browse", style="Inv.Treeview")
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        for col, w in zip(cols, widths):
            anchor = "w" if col in ("Product Info", "Batches") else "center"
            self.tree.heading(col, text=col.upper(), anchor="w")
            self.tree.column(col, width=w, anchor=anchor)

        self.tree.tag_configure("odd",      background="#f8fafc")
        self.tree.tag_configure("even",     background=CARD)
        self.tree.tag_configure("batch",    background="#fefce8", font=("Segoe UI", 9))
        self.tree.tag_configure("low",      foreground=ORANGE, font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure("out",      foreground=RED, font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure("expired",  foreground="#7c3aed", font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure("ok",       foreground=GREEN)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frm.grid_rowconfigure(0, weight=1)
        frm.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Return>",    lambda e: self._view_selected())
        self.tree.bind("<Double-1>",  lambda e: self._show_transaction_history())

        # Footer
        foot = tk.Frame(card, bg="#f8fafc", padx=16, pady=10)
        foot.pack(fill="x")
        tk.Frame(foot, bg=BDR, height=1).pack(fill="x", side="top")
        self._footer_var = tk.StringVar(value="Total Inventory Value:  ₹0.00")
        tk.Label(foot, textvariable=self._footer_var,
                 font=("Segoe UI", 11, "bold"), fg=TXT, bg="#f8fafc").pack(side="right", pady=(6, 0))

    # ── Search helpers ────────────────────────────────────────────────────────

    def _clr(self, e):
        if self._search_entry.get() == "Search products by name, company, HSN…":
            self._search_entry.delete(0, "end")
            self._search_entry.config(fg=TXT)

    def _rst(self, e):
        if not self._search_entry.get():
            self._search_entry.insert(0, "Search products by name, company, HSN…")
            self._search_entry.config(fg=MUTED)

    def _reset(self):
        self._search_var.set("")
        self._search_entry.delete(0, "end")
        self._search_entry.insert(0, "Search products by name, company, HSN…")
        self._search_entry.config(fg=MUTED)
        self.on_show()

    def _debounce_search(self):
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(400, self.on_show)

    # ── Data ──────────────────────────────────────────────────────────────────

    def on_show(self):
        """Load inventory data - OPTIMIZED for speed."""
        # Clear tree
        for i in self.tree.get_children():
            self.tree.delete(i)

        term = self._search_var.get()
        if term == "Search products by name, company, HSN…":
            term = ""

        # Get FY and mode
        fy_start = getattr(self.app, 'current_fy_start', None)
        fy_end = getattr(self.app, 'current_fy_end', None)
        
        if hasattr(self.app, 'fy_var') and self.app.fy_var:
            self._fy_badge.config(text=f" FY {self.app.fy_var.get()} ")
        
        mode = getattr(self, '_mode_var', None)
        current_mode = mode.get() if mode else "current"

        try:
            # Single DB query based on mode
            if current_mode == "fy" and fy_start and fy_end:
                rows = self._fetch_fy_movement(term, fy_start, fy_end)
            else:
                rows = self.app.db.fetch_inventory(term)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
            return

        # Group in memory (faster than multiple queries)
        from collections import defaultdict
        groups = defaultdict(list)
        for r in rows:
            key = (r.get("name", ""), r.get("company", ""), r.get("packing", ""), r.get("category", ""))
            groups[key].append(r)

        total_val = low = out = 0.0

        # Process and insert in bulk
        for idx, ((name, company, packing, category), batches) in enumerate(groups.items()):
            total_stock = stock_val = 0.0
            worst = "ok"

            for b in batches:
                qty = _safe_float(b.get("stock", b.get("current_stock", 0)))
                total_stock += qty
                stock_val += _safe_float(b.get("value", 0))

                st = str(b.get("status", "")).lower()
                if "out" in st:
                    worst = "out"; out += 1
                elif "low" in st and worst != "out":
                    worst = "low"; low += 1
                elif "exp" in st and worst not in ("out", "low"):
                    worst = "expired"

            total_val += stock_val
            tag = "low" if worst == "low" else "out" if worst == "out" else "expired" if worst == "expired" else ("odd" if idx % 2 else "even")
            status_lbl = {"out": "⚠ Out of Stock", "ok": "✓ In Stock", "low": "⚡ Low Stock", "expired": "⏰ Expired"}.get(worst, "✓ In Stock")

            prod_id = f"prod_{name}_{company}_{idx}"
            self.tree.insert("", "end", iid=prod_id, tags=(tag,),
                values=(f"▶  {name}\n    {company} | {packing}",
                    f"{len(batches)} batch{'es' if len(batches) > 1 else ''}",
                    f"{total_stock:.0f}", f"₹{stock_val:.2f}", status_lbl, "📜"))
            
            # Batch children
            for b in batches:
                bn = b.get("batch_no", "N/A")
                qty = _safe_float(b.get("stock", b.get("current_stock", 0)))
                exp = b.get("expiry", "N/A")
                val = _safe_float(b.get("value", 0))
                st = str(b.get("status", "")).lower()
                batch_status = "⚠ Out" if "out" in st else "⚡ Low" if "low" in st else "⏰ Expired" if "exp" in st else "✓ OK"
                
                self.tree.insert(prod_id, "end", tags=("batch",),
                    values=(f"    └─ Batch: {bn}", f"Exp: {exp}", f"{qty:.0f}",
                        f"₹{val:.2f}", batch_status, f"MRP: ₹{_safe_float(b.get('mrp', 0)):.2f}"))

        # Update stats
        self._stat_vars["products"].set(str(len(groups)))
        self._stat_vars["value"].set(f"₹{total_val:,.2f}")
        self._stat_vars["low"].set(str(int(low)))
        self._stat_vars["out"].set(str(int(out)))
        self._footer_var.set(f"Total Inventory Value:  ₹{total_val:,.2f}")
        n = len(groups)
        self._count_var.set(f"{n} product{'s' if n != 1 else ''} loaded")

    # ── Row actions ───────────────────────────────────────────────────────────

    def _view_selected(self):
        sel = self.tree.focus()
        if not sel:
            return
        v = self.tree.item(sel, "values")
        messagebox.showinfo(
            "Product Details",
            f"Product: {v[0]}\nCompany: {v[1]}\nBatches: {v[2]}",
            parent=self,
        )

    def _show_transaction_history(self):
        sel = self.tree.focus()
        if not sel:
            return
        v = self.tree.item(sel, "values")
        product_name, company = v[0], v[1]
        try:
            prod = self.app.db.query(
                "SELECT productid FROM core_productmaster "
                "WHERE product_name=%s AND product_company=%s LIMIT 1",
                (product_name, company),
            )
            if not prod:
                messagebox.showwarning("Not Found", "Product not found in database.", parent=self)
                return
            TransactionHistoryDialog(self, self.app, prod[0]["productid"], product_name, company)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load transactions: {e}", parent=self)

    # ── Keyboard shortcuts ────────────────────────────────────────────────────

    def kb_search(self):       self._clr(None); self._search_entry.focus_set()
    def kb_refresh(self):      self.on_show()
    def kb_export_excel(self): self._export_excel()
    def kb_export_pdf(self):   self._export_pdf()

    # ── Navigation ────────────────────────────────────────────────────────────

    def _open_batch_wise(self):
        from .batch_wise_screen import BatchWiseScreen
        d = tk.Toplevel(self)
        d.title("Batch-wise Inventory")
        d.state("zoomed")
        BatchWiseScreen(d, self.app).pack(fill="both", expand=True)

    def _open_date_wise(self):
        from .date_wise_screen import DateWiseScreen
        d = tk.Toplevel(self)
        d.title("Date-wise Inventory")
        d.state("zoomed")
        DateWiseScreen(d, self.app).pack(fill="both", expand=True)

    # ── Export helpers ────────────────────────────────────────────────────────

    def _get_inventory_rows(self):
        rows = []
        for item in self.tree.get_children():
            v = self.tree.item(item, "values")
            rows.append({
                "name":              v[0],
                "company":           v[1],
                "packing":           v[2],
                "batch_no":          "Multiple",
                "expiry":            "Various",
                "current_stock":     "See Batches",
                "current_free_qty":  0,
                "mrp":               0,
                "value":             _safe_float(v[3]),
            })
        return rows

    def _export_excel(self):
        try:
            from ..invoice_export import export_inventory_excel
            from tkinter import filedialog
            from pathlib import Path
            import os
            rows = self._get_inventory_rows()
            fn = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx")],
                initialfile="Inventory_Report.xlsx",
            )
            if fn:
                export_inventory_excel(rows, Path(fn))
                if messagebox.askyesno("Exported", "Excel saved!\n\nOpen now?"):
                    os.startfile(fn)
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

    def _export_pdf(self):
        try:
            from ..invoice_export import export_inventory_pdf
            from tkinter import filedialog
            from pathlib import Path
            rows = self._get_inventory_rows()
            fn = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")],
                initialfile="Inventory_Report.pdf",
            )
            if fn:
                export_inventory_pdf(rows, Path(fn), "Inventory Report")
                messagebox.showinfo("Exported", f"PDF saved:\n{fn}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")
    
    def _fetch_fy_movement(self, search: str, fy_start: str, fy_end: str):
        rid = self.app.config_data.retailer_id
        
        if search:
            search_clause = " AND (p.product_name LIKE %s OR p.product_company LIKE %s)"
            search_params = (f"%{search}%", f"%{search}%")
        else:
            search_clause = ""
            search_params = ()
        
        query = f"""
            SELECT p.product_name AS name,
                   p.product_company AS company,
                   p.product_packing AS packing,
                   p.product_category AS category,
                   t.batch_no,
                   t.expiry_date AS expiry,
                   COALESCE(MAX(t.mrp), 0) AS mrp,
                   COALESCE(MAX(t.rate), 0) AS purchase_rate,
                   COALESCE(SUM(CASE
                       WHEN DATE(t.transaction_date) < %s THEN
                           CASE
                               WHEN t.transaction_type = 'PURCHASE' THEN t.quantity
                               WHEN t.transaction_type = 'PURCHASE_RETURN' THEN -t.quantity
                               WHEN t.transaction_type IN ('SALE','STOCK_ISSUE') THEN -t.quantity
                               WHEN t.transaction_type = 'SALES_RETURN' THEN t.quantity
                               ELSE 0 END
                       ELSE 0 END), 0) AS opening_stock,
                   COALESCE(SUM(CASE
                       WHEN DATE(t.transaction_date) BETWEEN %s AND %s AND t.transaction_type = 'PURCHASE'
                       THEN t.quantity ELSE 0 END), 0) AS fy_purchases,
                   COALESCE(SUM(CASE
                       WHEN DATE(t.transaction_date) BETWEEN %s AND %s AND t.transaction_type = 'SALE'
                       THEN t.quantity ELSE 0 END), 0) AS fy_sales,
                   COALESCE(SUM(CASE
                       WHEN t.transaction_type = 'PURCHASE' THEN t.quantity
                       WHEN t.transaction_type = 'PURCHASE_RETURN' THEN -t.quantity
                       WHEN t.transaction_type IN ('SALE','STOCK_ISSUE') THEN -t.quantity
                       WHEN t.transaction_type = 'SALES_RETURN' THEN t.quantity
                       ELSE 0 END), 0) AS stock,
                   0 AS current_free_qty, 0 AS rate_a, 0 AS rate_b, 0 AS rate_c
            FROM inventory_transaction t
            JOIN core_productmaster p ON p.productid = t.product_id
            WHERE t.retailer_id = %s{search_clause}
            GROUP BY p.productid, p.product_name, p.product_company,
                     p.product_packing, p.product_category, t.batch_no, t.expiry_date
            HAVING stock > 0 OR opening_stock != 0 OR fy_purchases > 0 OR fy_sales > 0
            ORDER BY p.product_name, t.expiry_date LIMIT 500
        """
        
        params = (fy_start, fy_start, fy_end, fy_start, fy_end, rid) + search_params
        
        try:
            rows = self.app.db.query(query, params)
        except Exception as e:
            import logging
            logging.error(f"FY movement query error: {e}")
            return []
        
        for r in rows:
            stock = float(r.get("stock") or 0)
            rate = float(r.get("purchase_rate") or 0)
            r["value"] = f"₹{round(stock * rate, 2):.2f}"
            r["rates"] = f"A:₹{r.get('rate_a',0)} B:₹{r.get('rate_b',0)} C:₹{r.get('rate_c',0)}"
            r["status"] = "in_stock" if stock > 0 else "out_of_stock"
            r["fy_info"] = f"Open:{r.get('opening_stock',0):.0f} | +{r.get('fy_purchases',0):.0f} | -{r.get('fy_sales',0):.0f}"
        
        return rows


# ── Transaction History Dialog ────────────────────────────────────────────────

class TransactionHistoryDialog(tk.Toplevel):
    def __init__(self, parent, app, product_id, product_name, company):
        super().__init__(parent)
        self.app          = app
        self.product_id   = product_id
        self.product_name = product_name
        self.company      = company

        self.title(f"Transaction History – {product_name}")
        self.state("zoomed")
        self.configure(bg=BG)
        self.grab_set()

        self._build()
        self._load_transactions()   # FIX: safe loading with proper error handling

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=HDR_BG, padx=20, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📊 Transaction History",
                 font=("Segoe UI", 16, "bold"), fg="white", bg=HDR_BG).pack(anchor="w")
        tk.Label(hdr,
                 text=f"Product: {self.product_name}  |  Company: {self.company}",
                 font=("Segoe UI", 10), fg="#94a3b8", bg=HDR_BG).pack(anchor="w")
        tk.Frame(self, bg=BDR, height=1).pack(fill="x")

        # Summary cards
        sf = tk.Frame(self, bg=BG, padx=20, pady=14)
        sf.pack(fill="x")
        self._summary_vars = {
            "purchases":     tk.StringVar(value="0"),
            "sales":         tk.StringVar(value="0"),
            "current_stock": tk.StringVar(value="0"),
            "stock_value":   tk.StringVar(value="₹0.00"),
        }
        cards = [
            ("📦 Total Purchases", "purchases",     GREEN),
            ("📤 Total Sales",     "sales",         RED),
            ("📊 Current Stock",   "current_stock", BLUE),
            ("💰 Stock Value",     "stock_value",   ORANGE),
        ]
        for i, (label, key, color) in enumerate(cards):
            self._create_summary_card(sf, label, self._summary_vars[key], color,
                                      last=(i == len(cards) - 1))

        # Table card
        tbl_card = tk.Frame(self, bg=CARD, highlightbackground=BDR, highlightthickness=1)
        tbl_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        tbar = tk.Frame(tbl_card, bg=CARD, padx=16, pady=10)
        tbar.pack(fill="x")
        tk.Label(tbar, text="All Transactions",
                 font=("Segoe UI", 11, "bold"), fg=TXT, bg=CARD).pack(side="left")
        tk.Frame(tbl_card, bg=BDR, height=1).pack(fill="x")

        # Treeview
        style = ttk.Style()
        style.configure("TH.Treeview",
                         font=("Segoe UI", 9), rowheight=32,
                         background=CARD, fieldbackground=CARD,
                         foreground=TXT, borderwidth=0)
        style.configure("TH.Treeview.Heading",
                         font=("Segoe UI", 9, "bold"),
                         background="#f8fafc", foreground=MUTED, relief="flat")

        cols   = ("Date", "Type", "Invoice/Ref No", "Batch", "Expiry",
                  "Qty", "Free Qty", "Rate", "MRP", "Total Amount")
        widths = (100, 120, 140, 100, 80, 70, 70, 80, 80, 100)

        frm = tk.Frame(tbl_card, bg=CARD)
        frm.pack(fill="both", expand=True, padx=10, pady=10)

        vsb = ttk.Scrollbar(frm, orient="vertical")
        hsb = ttk.Scrollbar(frm, orient="horizontal")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings",
                                  yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                  selectmode="browse", style="TH.Treeview")
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=w, anchor="center")

        self.tree.tag_configure("purchase",       background="#f0fdf4")
        self.tree.tag_configure("sale",           background="#fef2f2")
        self.tree.tag_configure("return_purchase",background="#fffbeb")
        self.tree.tag_configure("return_sale",    background="#eff6ff")

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frm.grid_rowconfigure(0, weight=1)
        frm.grid_columnconfigure(0, weight=1)

        # Close button
        btn_frame = tk.Frame(self, bg=BG, padx=20, pady=(0, 14))
        btn_frame.pack(fill="x")
        _btn(btn_frame, "✖ Close", GRAY, "#4b5563", cmd=self.destroy, pady=8).pack(side="right")

    def _create_summary_card(self, parent, label, var, color, last=False):
        """Summary card using grid layout to avoid padx distance errors."""
        card = tk.Frame(parent, bg="#fafafa", highlightbackground=BDR, highlightthickness=1)
        card.pack(side="left", fill="both", expand=True, padx=5)

        inner = tk.Frame(card, bg="#fafafa", padx=14, pady=10)
        inner.pack(fill="x")
        tk.Label(inner, text=label,
                 font=("Segoe UI", 8, "bold"), fg=MUTED, bg="#fafafa").pack(anchor="w")
        tk.Label(inner, textvariable=var,
                 font=("Segoe UI", 16, "bold"), fg=TXT, bg="#fafafa").pack(anchor="w")
        tk.Frame(card, bg=color, height=3).pack(fill="x", side="bottom")

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_transactions(self):
        """
        FIX: Guard every dict access with .get() + safe type coercion.
        Sort key uses datetime.min as fallback so None dates don't crash.
        Stock value uses last available MRP instead of assuming index 0.
        """
        for i in self.tree.get_children():
            self.tree.delete(i)

        try:
            purchases = self.app.db.query(
                """
                SELECT pm.purchase_entry_date  AS date,
                       pm.product_invoice_no   AS ref_no,
                       pm.product_batch_no     AS batch,
                       pm.product_expiry       AS expiry,
                       pm.product_quantity     AS qty,
                       pm.product_free_qty     AS free_qty,
                       pm.product_purchase_rate AS rate,
                       pm.product_MRP          AS mrp,
                       pm.total_amount
                FROM   core_purchasemaster pm
                WHERE  pm.productid_id = %s
                ORDER  BY pm.purchase_entry_date DESC
                """,
                (self.product_id,),
            )

            sales = self.app.db.query(
                """
                SELECT sm.sale_entry_date      AS date,
                       sm.sales_invoice_no_id  AS ref_no,
                       sm.product_batch_no     AS batch,
                       sm.product_expiry       AS expiry,
                       sm.sale_quantity        AS qty,
                       sm.sale_free_qty        AS free_qty,
                       sm.sale_rate            AS rate,
                       sm.product_MRP          AS mrp,
                       sm.sale_total_amount    AS total_amount
                FROM   core_salesmaster sm
                WHERE  sm.productid_id = %s
                ORDER  BY sm.sale_entry_date DESC
                """,
                (self.product_id,),
            )

        except Exception as e:
            import traceback
            messagebox.showerror(
                "Database Error",
                f"Failed to fetch transactions:\n{e}\n\n{traceback.format_exc()}",
                parent=self,
            )
            return

        # Build unified list ──────────────────────────────────────────────────
        all_transactions: list[dict] = []

        for p in (purchases or []):
            raw_dt = p.get("date")
            all_transactions.append({
                "date":         raw_dt,
                "date_str":     _fmt_date(raw_dt),
                "type":         "PURCHASE",
                "ref_no":       str(p.get("ref_no") or ""),
                "batch":        str(p.get("batch") or ""),
                "expiry":       str(p.get("expiry") or ""),
                "qty":          _safe_float(p.get("qty")),
                "free_qty":     _safe_float(p.get("free_qty")),
                "rate":         _safe_float(p.get("rate")),
                "mrp":          _safe_float(p.get("mrp")),
                "total_amount": _safe_float(p.get("total_amount")),
            })

        for s in (sales or []):
            raw_dt = s.get("date")
            all_transactions.append({
                "date":         raw_dt,
                "date_str":     _fmt_date(raw_dt),
                "type":         "SALE",
                "ref_no":       str(s.get("ref_no") or ""),
                "batch":        str(s.get("batch") or ""),
                "expiry":       str(s.get("expiry") or ""),
                "qty":          _safe_float(s.get("qty")),
                "free_qty":     _safe_float(s.get("free_qty")),
                "rate":         _safe_float(s.get("rate")),
                "mrp":          _safe_float(s.get("mrp")),
                "total_amount": _safe_float(s.get("total_amount")),
            })

        # Sort newest first; None dates go to the bottom ──────────────────────
        all_transactions.sort(
            key=lambda x: x["date"] if x["date"] is not None else datetime.min,
            reverse=True,
        )

        # Summary calculations ─────────────────────────────────────────────────
        total_purchases = sum(t["qty"] for t in all_transactions if t["type"] == "PURCHASE")
        total_sales     = sum(t["qty"] for t in all_transactions if t["type"] == "SALE")
        current_stock   = total_purchases - total_sales

        # FIX: use the MRP from the most-recent transaction that has one,
        # rather than blindly accessing index 0 (which could be a sale with MRP=0)
        latest_mrp = next(
            (t["mrp"] for t in all_transactions if t["mrp"] > 0),
            0.0,
        )
        stock_value = current_stock * latest_mrp

        self._summary_vars["purchases"].set(f"{total_purchases:.0f}")
        self._summary_vars["sales"].set(f"{total_sales:.0f}")
        self._summary_vars["current_stock"].set(f"{current_stock:.0f}")
        self._summary_vars["stock_value"].set(f"₹{stock_value:,.2f}")

        # Populate treeview ───────────────────────────────────────────────────
        for t in all_transactions:
            tag = "purchase" if t["type"] == "PURCHASE" else "sale"
            self.tree.insert("", "end", tags=(tag,), values=(
                t["date_str"],
                t["type"],
                t["ref_no"],
                t["batch"],
                t["expiry"],
                f"{t['qty']:.0f}",
                f"{t['free_qty']:.0f}",
                f"₹{t['rate']:.2f}",
                f"₹{t['mrp']:.2f}",
                f"₹{t['total_amount']:.2f}",
            ))

        if not all_transactions:
            messagebox.showinfo(
                "No Transactions",
                f"No transactions found for:\n{self.product_name}",
                parent=self,
            )