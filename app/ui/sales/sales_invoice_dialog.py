"""Sales Invoice Dialog — Items at bottom, bulk creation inside dialog."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from ...styles import COLORS, FONT
from ..purchase.purchase_invoice_dialog import (
    AutoSuggestEntry, DateEntry, L, _f, _fmt_expiry
)


class SalesInvoiceDialog(tk.Toplevel):
    def __init__(self, parent, app, invoice_data=None, on_saved=None):
        super().__init__(parent)
        self.app = app; self.db = app.db
        self.on_saved = on_saved
        self._edit_data = invoice_data
        self._invoice_no = invoice_data["sales_invoice_no"] if invoice_data else None
        self._customer_id = None
        self._product_id = None
        self._packing_mult = 1
        self._items: list[dict] = []
        self._batch_data: dict[str, dict] = {}
        self._edit_item_idx = None
        self._auto_inv_no = None

        self.title("Sales Invoice")
        self.state("zoomed")
        self.configure(bg=L["bg"])
        self.grab_set()

        self._build()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<F2>", lambda e: self._save(close_after=False))
        self.bind("<F4>", lambda e: self._add_item())
        self.bind("<F6>", lambda e: self._save_and_new())
        self.bind("<Delete>", lambda e: self._remove_item())
        self.bind("<Control-p>", lambda e: self._print_receipt())
        self.bind("<Control-l>", lambda e: self._save_and_print())

        if invoice_data:
            self._load_existing()
        else:
            self._prefetch_invoice_no()

    def _build(self):
        # ── Top bar ──
        top = tk.Frame(self, bg=L["topbar"], height=50)
        top.pack(fill="x"); top.pack_propagate(False)

        tk.Label(top, text="  💊 Sales Invoice", font=FONT["h3"],
                 bg=L["topbar"], fg="#f8fafc").pack(side="left", padx=10)
        tk.Label(top, text="F2=Save  F6=Save&New  Ctrl+L=Save&Print  F4=Add  Del=Remove  Esc=Close",
                 font=FONT["sm"], bg=L["topbar"], fg="#94a3b8").pack(side="left", padx=10)

        for txt, cmd, col in [
            ("Esc Close",         self.destroy,           "#64748b"),
            ("Ctrl+L Save&Print", self._save_and_print,   "#f59e0b"),
            ("F6 Save & New",     self._save_and_new,     "#7c3aed"),
            ("F2 Save",           lambda: self._save(close_after=False), "#16a34a"),
        ]:
            tk.Button(top, text=txt, bg=col, fg="white", font=FONT["sm"],
                      bd=0, relief="flat", padx=14, pady=6, cursor="hand2",
                      command=cmd).pack(side="right", padx=4, pady=7)

        # ── Main body ──
        body = tk.Frame(self, bg=L["bg"])
        body.pack(fill="both", expand=True, padx=12, pady=8)

        # Item form at top
        self._build_item_form(body)
        
        # Items table in middle
        self._build_items_table(body)
        
        # Header at bottom
        self._build_header(body)

    # ── Sales Header ───────────────────────────────────────────────────────────
    def _build_header(self, parent):
        card = tk.Frame(parent, bg=L["card"], highlightthickness=1,
                        highlightbackground=L["green"])
        card.pack(side="bottom", fill="x", pady=(6, 0))

        tk.Frame(card, bg=L["green"], height=3).pack(fill="x")
        hf = tk.Frame(card, bg=L["card"], padx=10, pady=6); hf.pack(fill="x")
        tk.Label(hf, text="🧾 Sales Header", font=FONT["bold"],
                 bg=L["card"], fg=L["green"]).pack(side="left")

        frm = tk.Frame(card, bg=L["card"], padx=12, pady=10); frm.pack(fill="x")

        def lbl(t, r, c): tk.Label(frm, text=t, font=FONT["sm"], bg=L["card"],
                                    fg=L["lbl"]).grid(row=r, column=c, sticky="w", padx=(0,6), pady=4)
        def ent(var, r, c, w=16, state="normal"):
            e = tk.Entry(frm, textvariable=var, font=FONT["base"], width=w,
                         relief="solid", bd=1, state=state,
                         bg=L["input_bg"] if state == "normal" else "#f1f5f9",
                         fg=L["input_fg"], insertbackground=L["input_fg"],
                         highlightthickness=1, highlightbackground=L["border"],
                         highlightcolor=L["green"])
            e.grid(row=r, column=c, sticky="w", padx=(0, 12), pady=4)
            return e

        lbl("Invoice No", 0, 0)
        self.var_invoice_no = tk.StringVar(value="(auto)")
        inv_e = ent(self.var_invoice_no, 0, 1, w=18)
        inv_e.bind("<FocusIn>", self._on_invno_focus)

        lbl("Date *", 0, 2)
        self.var_invoice_date = tk.StringVar(value=date.today().isoformat())
        DateEntry(frm, textvariable=self.var_invoice_date, width=13,
                  bg=L["card"]).grid(row=0, column=3, sticky="w", padx=(0,12), pady=4)

        lbl("Customer", 1, 0)
        self._cust_widget = AutoSuggestEntry(
            frm,
            fetch_fn=lambda t: self.db.query(
                "SELECT customerid, customer_name, customer_mobile, customer_type, "
                "customer_credit_days FROM core_customermaster "
                "WHERE customer_name LIKE %s AND retailer_id=%s ORDER BY customer_name LIMIT 20",
                (f"%{t}%", self.db.config.retailer_id)),
            display_key="customer_name", on_select=self._on_cust_select, width=30, bg=L["card"])
        self._cust_widget.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(0,12), pady=4)

        lbl("Transport (₹)", 2, 0)
        self.var_transport = tk.StringVar(value="0")
        ent(self.var_transport, 2, 1, w=10)

        self._cust_info = tk.StringVar()
        tk.Label(frm, textvariable=self._cust_info, font=FONT["sm"],
                 bg=L["card"], fg=L["muted"]).grid(row=2, column=2, columnspan=2, sticky="w")

    def _on_cust_select(self, row):
        self._customer_id = int(row["customerid"])
        self._cust_info.set(
            f"Type: {row.get('customer_type','')}  |  "
            f"Mobile: {row.get('customer_mobile','')}  |  "
            f"Credit: {row.get('customer_credit_days', 0)} days")

    def _prefetch_invoice_no(self):
        try:
            self._auto_inv_no = self.db.get_next_sales_invoice_no()
            self.var_invoice_no.set(self._auto_inv_no)
        except: self.var_invoice_no.set("(auto)")

    def _on_invno_focus(self, e=None):
        if self.var_invoice_no.get() == "(auto)":
            self._prefetch_invoice_no()

    # ── Item entry form ────────────────────────────────────────────────────────
    def _build_item_form(self, parent):
        card = tk.Frame(parent, bg=L["card"], highlightthickness=1,
                        highlightbackground=L["blue"])
        card.pack(side="top", fill="x", pady=(0, 6))

        tk.Frame(card, bg=L["blue"], height=3).pack(fill="x")
        hf = tk.Frame(card, bg=L["card"], padx=10, pady=6); hf.pack(fill="x")
        tk.Label(hf, text="➕ Add Item", font=FONT["bold"],
                 bg=L["card"], fg=L["blue"]).pack(side="left")
        tk.Label(hf, text="F4 = Add to list", font=FONT["sm"],
                 bg=L["card"], fg=L["muted"]).pack(side="left", padx=8)

        frm = tk.Frame(card, bg=L["card"], padx=12, pady=8); frm.pack(fill="x")

        def lbl(t, r, c): tk.Label(frm, text=t, font=FONT["sm"], bg=L["card"],
                                    fg=L["lbl"]).grid(row=r, column=c, sticky="w", padx=(0,4), pady=3)
        def ent(var, r, c, w=10, state="normal"):
            e = tk.Entry(frm, textvariable=var, font=FONT["base"], width=w,
                         relief="solid", bd=1, state=state,
                         bg=L["input_bg"] if state == "normal" else "#f1f5f9",
                         fg=L["input_fg"], insertbackground=L["input_fg"],
                         highlightthickness=1, highlightbackground=L["border"],
                         highlightcolor=L["blue"])
            e.grid(row=r, column=c, sticky="w", padx=(0, 10), pady=3)
            return e

        # Row 0: Product
        lbl("Product *", 0, 0)
        self._prod_widget = AutoSuggestEntry(
            frm,
            fetch_fn=lambda t: self.db.query(
                "SELECT productid, product_name, product_company, product_packing, "
                "product_hsn_percent FROM core_productmaster "
                "WHERE (product_name LIKE %s OR product_company LIKE %s) "
                "AND retailer_id=%s ORDER BY product_name LIMIT 20",
                (f"%{t}%", f"%{t}%", self.db.config.retailer_id)),
            display_key="product_name", on_select=self._on_prod_select, width=28, bg=L["card"])
        self._prod_widget.grid(row=0, column=1, columnspan=5, sticky="ew", padx=(0,10), pady=3)
        frm.grid_columnconfigure(1, weight=1)
        self._prod_info = tk.StringVar()
        tk.Label(frm, textvariable=self._prod_info, font=FONT["sm"],
                 bg=L["card"], fg=L["muted"]).grid(row=0, column=6, sticky="w")

        # Row 1: Batch, Expiry, MRP, Stock
        lbl("Batch *", 1, 0)
        self.var_batch = tk.StringVar()
        self._batch_combo = ttk.Combobox(frm, textvariable=self.var_batch,
                                          font=FONT["base"], width=14, state="readonly")
        self._batch_combo.grid(row=1, column=1, sticky="w", padx=(0, 10), pady=3)
        self._batch_combo.bind("<<ComboboxSelected>>", self._on_batch_select)

        lbl("Expiry", 1, 2)
        self.var_expiry = tk.StringVar()
        ent(self.var_expiry, 1, 3, w=10, state="readonly")

        lbl("MRP", 1, 4)
        self.var_mrp = tk.StringVar(value="0")
        ent(self.var_mrp, 1, 5, w=8, state="readonly")

        self._stock_var = tk.StringVar(value="Stock: -")
        tk.Label(frm, textvariable=self._stock_var, font=FONT["bold"],
                 bg=L["card"], fg=L["orange"]).grid(row=1, column=6, sticky="w", padx=4)

        # Row 2: Rate, Qty, Free
        lbl("Sale Rate", 2, 0)
        self.var_rate = tk.StringVar(value="0")
        re_ = ent(self.var_rate, 2, 1, w=10)
        re_.bind("<FocusOut>", lambda e: self._calc())

        lbl("Qty *", 2, 2)
        self.var_qty = tk.StringVar(value="1")
        qe = ent(self.var_qty, 2, 3, w=7)
        qe.bind("<FocusOut>", lambda e: self._calc())
        qe.bind("<Return>", lambda e: self._add_item())

        lbl("Free", 2, 4)
        self.var_free_qty = tk.StringVar(value="0")
        ent(self.var_free_qty, 2, 5, w=7)

        # Row 3: Scheme, Discount, CGST, SGST
        lbl("Scheme%", 3, 0)
        self.var_scheme = tk.StringVar(value="0")
        ent(self.var_scheme, 3, 1, w=7)

        lbl("Disc(₹)", 3, 2)
        self.var_discount = tk.StringVar(value="0")
        de = ent(self.var_discount, 3, 3, w=9)
        de.bind("<FocusOut>", lambda e: self._calc())

        lbl("CGST%", 3, 4)
        self.var_cgst = tk.StringVar(value="0")
        ent(self.var_cgst, 3, 5, w=6)

        lbl("SGST%", 3, 6)
        self.var_sgst = tk.StringVar(value="0")
        se = ent(self.var_sgst, 3, 7, w=6)
        se.bind("<FocusOut>", lambda e: self._calc())

        # Row 4: Line total + Add button
        self._line_total_var = tk.StringVar(value="Line Total: ₹ 0.00")
        tk.Label(frm, textvariable=self._line_total_var, font=FONT["bold"],
                 bg=L["card"], fg=L["green"]).grid(row=4, column=0, columnspan=4, sticky="w", pady=4)

        tk.Button(frm, text="F4  Add to List ↓", font=FONT["base"],
                  bg=L["blue"], fg="white", relief="flat", bd=0,
                  padx=16, pady=6, cursor="hand2",
                  command=self._add_item).grid(row=4, column=4, columnspan=4, sticky="e", pady=4)

    def _on_prod_select(self, row):
        self._product_id = int(row["productid"])
        packing = row.get('product_packing', '')
        self._prod_info.set(f"{row.get('product_company','')}  |  Packing: {packing}")
        gst = _f(str(row.get("product_hsn_percent") or 0))
        h = round(gst / 2, 2)
        self.var_cgst.set(str(h)); self.var_sgst.set(str(h))
        import re as _re
        m = _re.search(r'(\d+)[xX*](\d+)', str(packing))
        if m:
            self._packing_mult = int(m.group(1)) * int(m.group(2))
        else:
            m2 = _re.search(r'(\d+)', str(packing))
            self._packing_mult = int(m2.group(1)) if m2 else 1
        self._load_batches()

    def _load_batches(self):
        self._batch_data = {}
        self._batch_combo["values"] = []
        self.var_batch.set(""); self.var_expiry.set(""); self.var_mrp.set("0")
        self._stock_var.set("Stock: -")
        if not self._product_id: return
        try:
            batches = self.db.get_batches_for_product(self._product_id)
            opts = []
            for b in batches:
                key = b["batch_no"]
                self._batch_data[key] = b
                opts.append(key)
            self._batch_combo["values"] = opts
            if opts:
                self._batch_combo.current(0)
                self.var_batch.set(opts[0])
                self._on_batch_select()
        except: pass

    def _on_batch_select(self, e=None):
        key = self.var_batch.get()
        b = self._batch_data.get(key, {})
        self.var_expiry.set(str(b.get("expiry_date", "")))
        self.var_mrp.set(str(b.get("mrp", 0)))
        self.var_rate.set(str(b.get("rate_a", 0) or b.get("mrp", 0)))
        
        # Get quantity and free_quantity separately
        qty = float(b.get("quantity", 0))
        free_qty = float(b.get("free_quantity", 0))
        total_stock = qty + free_qty
        
        mult = self._packing_mult
        # stock is stored in individual units; show as boxes (units / packing) if packing > 1
        if mult > 1:
            boxes = total_stock / mult
            stock_label = f"Stock: Qty {qty:.0f} + Free {free_qty:.0f} = {total_stock:.0f} units ({boxes:.1f} boxes of {mult})"
        else:
            stock_label = f"Stock: Qty {qty:.0f} + Free {free_qty:.0f} = {total_stock:.0f} units"
        color = L["red"] if total_stock <= 0 else (L["orange"] if total_stock < mult * 2 else L["green"])
        self._stock_var.set(stock_label)
        # Also update the stock label color dynamically
        try:
            for w in self.winfo_children():
                self._update_stock_label_color(w, color)
        except Exception:
            pass

    def _update_stock_label_color(self, widget, color):
        """Recursively find the stock label and update its color."""
        try:
            if isinstance(widget, tk.Label) and hasattr(self, '_stock_var'):
                if widget.cget('textvariable') == str(self._stock_var):
                    widget.config(fg=color)
                    return
        except Exception:
            pass
        for child in widget.winfo_children():
            self._update_stock_label_color(child, color)

    def _calc(self):
        mrp  = _f(self.var_mrp.get()); qty = _f(self.var_qty.get())
        disc = _f(self.var_discount.get())
        cgst = _f(self.var_cgst.get()); sgst = _f(self.var_sgst.get())
        total = round((mrp * qty - disc) * (1 + (cgst + sgst) / 100), 2)
        # Show user input qty as-is (NO packing multiplication for display)
        self._line_total_var.set(f"Qty: {int(qty)} units   Line Total: ₹ {total:.2f}")

    # ── Items table ────────────────────────────────────────────────────────────
    def _build_items_table(self, parent):
        card = tk.Frame(parent, bg=L["card"], highlightthickness=1,
                        highlightbackground=L["border"])
        card.pack(fill="both", expand=True)

        tk.Frame(card, bg=L["green"], height=3).pack(fill="x")
        hf = tk.Frame(card, bg=L["card"], padx=10, pady=6); hf.pack(fill="x")
        tk.Label(hf, text="🧾 Invoice Items", font=FONT["bold"],
                 bg=L["card"], fg=L["green"]).pack(side="left")

        self.var_total_lbl = tk.StringVar(value="Grand Total: ₹ 0.00")
        tk.Label(hf, textvariable=self.var_total_lbl, font=FONT["bold"],
                 bg=L["card"], fg=L["green"]).pack(side="right", padx=10)
        self._count_var = tk.StringVar(value="0 items")
        tk.Label(hf, textvariable=self._count_var, font=FONT["sm"],
                 bg=L["card"], fg=L["muted"]).pack(side="right", padx=4)

        btn_bar = tk.Frame(card, bg=L["card"], padx=10, pady=4); btn_bar.pack(fill="x")
        tk.Button(btn_bar, text="✏ Edit (Dbl-click)", font=FONT["sm"],
                  bg="#f1f5f9", fg=L["head"], relief="flat", bd=0,
                  padx=8, pady=3, cursor="hand2",
                  command=self._edit_row).pack(side="left", padx=(0, 6))
        tk.Button(btn_bar, text="🗑 Remove (Del)", font=FONT["sm"],
                  bg=L["red"], fg="white", relief="flat", bd=0,
                  padx=8, pady=3, cursor="hand2",
                  command=self._remove_item).pack(side="left")

        tk.Button(btn_bar, text="📊 Export Excel", font=FONT["sm"],
                  bg="#d97706", fg="white", relief="flat", bd=0,
                  padx=8, pady=3, cursor="hand2",
                  command=self._export_excel).pack(side="right", padx=(6, 0))
        tk.Button(btn_bar, text="📄 Export PDF", font=FONT["sm"],
                  bg="#dc2626", fg="white", relief="flat", bd=0,
                  padx=8, pady=3, cursor="hand2",
                  command=self._export_pdf).pack(side="right")

        tk.Frame(card, bg=L["border"], height=1).pack(fill="x")

        cols = ("#", "Product", "Batch", "Expiry", "MRP", "Rate", "Qty", "Free", "Scheme%", "Disc", "CGST%", "SGST%", "Total")
        ws   = (30, 160, 80, 75, 60, 70, 50, 50, 60, 60, 55, 55, 85)

        frm = tk.Frame(card, bg=L["bg"]); frm.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(frm, orient="vertical")
        hsb = ttk.Scrollbar(frm, orient="horizontal")
        self.items_tree = ttk.Treeview(frm, columns=cols, show="headings",
                                        yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                        selectmode="browse", height=8)
        vsb.config(command=self.items_tree.yview)
        hsb.config(command=self.items_tree.xview)
        for col, w in zip(cols, ws):
            self.items_tree.heading(col, text=col)
            self.items_tree.column(col, width=w, anchor="w" if col == "Product" else "center", minwidth=30)
        self.items_tree.tag_configure("odd", background=L["row_odd"])
        self.items_tree.tag_configure("even", background=L["row_even"])
        self.items_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frm.grid_rowconfigure(0, weight=1)
        frm.grid_columnconfigure(0, weight=1)
        self.items_tree.bind("<Double-1>", self._edit_row)
        self.items_tree.bind("<Delete>", lambda e: self._remove_item())

    # ── Add / Edit / Remove ───────────────────────────────────────────────────
    def _add_item(self):
        if not self._product_id:
            messagebox.showwarning("Validation", "Select a product first.", parent=self); return
        qty = _f(self.var_qty.get())
        if qty <= 0:
            messagebox.showwarning("Validation", "Quantity must be > 0.", parent=self); return
        batch = self.var_batch.get().strip()
        if not batch:
            messagebox.showwarning("Validation", "Select a batch.", parent=self); return

        # Skip slow stock check if in edit mode
        if self._edit_item_idx is None:
            b = self._batch_data.get(batch, {})
            qty_avail = float(b.get("quantity", 0))
            free_avail = float(b.get("free_quantity", 0))
            avail = qty_avail + free_avail
            if qty > avail:
                if not messagebox.askyesno("Low Stock", f"Only {avail:.0f} available (Qty: {qty_avail:.0f}, Free: {free_avail:.0f}). Proceed?", parent=self):
                    return

        mrp  = _f(self.var_mrp.get()); disc = _f(self.var_discount.get())
        cgst = _f(self.var_cgst.get()); sgst = _f(self.var_sgst.get())
        total = round((mrp * qty - disc) * (1 + (cgst + sgst) / 100), 2)

        p = self.db.get_product_full(self._product_id) or {}
        item = {
            "productid": self._product_id,
            "product_name": p.get("product_name", ""),
            "product_company": p.get("product_company", ""),
            "product_packing": p.get("product_packing", ""),
            "batch_no": batch, "expiry": self.var_expiry.get().strip(),
            "mrp": _f(self.var_mrp.get()), "sale_rate": _f(self.var_rate.get()),
            "quantity": qty, "free_qty": _f(self.var_free_qty.get()),
            "scheme": _f(self.var_scheme.get()), "discount": disc,
            "cgst": cgst, "sgst": sgst, "rate_applied": "A", "total": total,
        }

        if self._edit_item_idx is not None and self._edit_item_idx < len(self._items):
            self._items[self._edit_item_idx] = item
            children = self.items_tree.get_children()
            if self._edit_item_idx < len(children):
                iid = children[self._edit_item_idx]
                self.items_tree.item(iid, values=self._row(item))
            self._edit_item_idx = None
        else:
            self._items.append(item)
            tag = "odd" if len(self._items) % 2 else "even"
            self.items_tree.insert("", "end", values=self._row(item), tags=(tag,))

        self._refresh_footer()
        self._clear_form()
        self._prod_widget.focus()

    def _row(self, item):
        return (len(self._items) if self._edit_item_idx is None else "",
                item["product_name"], item["batch_no"], item["expiry"],
                f"{item['mrp']:.2f}", f"{item['sale_rate']:.2f}",
                f"{item['quantity']:.0f}", f"{item['free_qty']:.0f}",
                f"{item['scheme']:.1f}", f"{item['discount']:.2f}",
                f"{item['cgst']:.1f}", f"{item['sgst']:.1f}",
                f"₹{item['total']:.2f}")

    def _edit_row(self, e=None):
        sel = self.items_tree.focus()
        if not sel: return
        idx = self.items_tree.index(sel)
        if idx >= len(self._items): return
        self._edit_item_idx = idx
        item = self._items[idx]
        self._product_id = item["productid"]
        p = self.db.get_product_full(self._product_id) or {}
        self._prod_widget.set(p.get("product_name", ""))
        self._prod_info.set(f"{p.get('product_company','')}  |  {p.get('product_packing','')}")
        self._load_batches()
        self.var_batch.set(item["batch_no"])
        self._on_batch_select()
        self.var_rate.set(str(item["sale_rate"]))
        self.var_qty.set(str(item["quantity"]))
        self.var_free_qty.set(str(item["free_qty"]))
        self.var_scheme.set(str(item["scheme"]))
        self.var_discount.set(str(item["discount"]))
        self.var_cgst.set(str(item["cgst"]))
        self.var_sgst.set(str(item["sgst"]))
        self._calc()

    def _remove_item(self):
        sel = self.items_tree.focus()
        if not sel: return
        idx = self.items_tree.index(sel)
        self.items_tree.delete(sel)
        if idx < len(self._items): self._items.pop(idx)
        self._refresh_footer()

    def _refresh_footer(self):
        total = sum(i["total"] for i in self._items)
        transport = _f(self.var_transport.get())
        self.var_total_lbl.set(f"Grand Total: ₹ {total + transport:.2f}")
        self._count_var.set(f"{len(self._items)} item(s)")
        for i, iid in enumerate(self.items_tree.get_children(), 1):
            vals = list(self.items_tree.item(iid, "values"))
            vals[0] = i
            self.items_tree.item(iid, values=vals)

    def _clear_form(self):
        self._product_id = None; self._edit_item_idx = None; self._packing_mult = 1
        self._prod_widget.set(""); self._prod_info.set("")
        self._batch_combo["values"] = []; self._batch_data = {}
        self.var_batch.set(""); self.var_expiry.set(""); self.var_mrp.set("0")
        self.var_rate.set("0"); self.var_qty.set("1")
        self._stock_var.set("Stock: -")
        for v in (self.var_free_qty, self.var_scheme, self.var_discount,
                  self.var_cgst, self.var_sgst):
            v.set("0")
        self._line_total_var.set("Line Total: ₹ 0.00")

    def _load_existing(self):
        """Load existing invoice data - ULTRA OPTIMIZED for instant loading."""
        inv = self._edit_data
        
        # Quick header load
        self.var_invoice_no.set(inv.get("sales_invoice_no", ""))
        self.var_invoice_date.set(str(inv.get("sales_invoice_date", "")))
        self.var_transport.set(str(inv.get("sales_transport_charges", 0)))
        self._customer_id = inv.get("customerid_id") or inv.get("customerid")
        self._cust_widget.set(inv.get("customer_name", ""))
        
        # Fast batch load (pre-calculate everything in memory)
        items_data = self.db.get_sales_items(self._invoice_no)
        
        # Process all items in memory first (NO UI updates yet)
        for sm in items_data:
            mrp  = float(sm.get("product_MRP", 0))
            qty  = float(sm.get("sale_quantity", 0))
            disc = float(sm.get("sale_discount", 0))
            cgst = float(sm.get("sale_cgst", 0))
            sgst = float(sm.get("sale_sgst", 0))
            
            self._items.append({
                "productid": sm["productid_id"],
                "product_name": sm.get("product_name", ""),
                "product_company": sm.get("product_company", ""),
                "product_packing": sm.get("product_packing", ""),
                "batch_no": sm.get("product_batch_no", ""),
                "expiry": sm.get("product_expiry", ""),
                "mrp": mrp,
                "sale_rate": float(sm.get("sale_rate", 0)),
                "quantity": qty,
                "free_qty": float(sm.get("sale_free_qty", 0)),
                "scheme": float(sm.get("sale_scheme", 0)),
                "discount": disc,
                "cgst": cgst,
                "sgst": sgst,
                "rate_applied": sm.get("rate_applied", "A"),
                "total": round((mrp * qty - disc) * (1 + (cgst + sgst) / 100), 2),
            })
        
        # Single UI update - insert all rows at once
        for idx, item in enumerate(self._items):
            tag = "odd" if (idx + 1) % 2 else "even"
            self.items_tree.insert("", "end", values=self._row(item), tags=(tag,))
        
        # Single footer refresh
        self._refresh_footer()

    # ── Save ───────────────────────────────────────────────────────────────────
    def _save(self, close_after=False):
        try:
            inv_date = self.var_invoice_date.get().strip()
            if not inv_date: raise ValueError("Invoice date required.")
            if not self._items: raise ValueError("Add at least one item.")

            transport = _f(self.var_transport.get())
            manual_no = self.var_invoice_no.get().strip()
            use_manual = manual_no and manual_no not in ("(auto)", self._auto_inv_no or "")
            
            customer_id = self._customer_id if self._customer_id else None
            
            # If no customer selected, create/get a default "Walk-in Customer"
            if not customer_id:
                with self.db.cursor() as cur:
                    cur.execute(
                        "SELECT customerid FROM core_customermaster WHERE customer_name='Walk-in Customer' LIMIT 1"
                    )
                    row = cur.fetchone()
                    if row:
                        customer_id = row['customerid']
                    else:
                        cur.execute(
                            "INSERT INTO core_customermaster "
                            "(customer_name, customer_type, customer_mobile, customer_address) "
                            "VALUES ('Walk-in Customer', 'CASH', 'N/A', 'N/A')"
                        )
                        customer_id = cur.lastrowid

            # Use context manager for transaction
            with self.db.cursor() as cur:
                if self._invoice_no:
                    # Edit mode
                    inv_no = self._invoice_no
                    # Delete old items and inventory transactions in one go
                    cur.execute("DELETE FROM core_salesmaster WHERE sales_invoice_no_id=%s", (inv_no,))
                    if self.db.table_exists("inventory_transaction"):
                        cur.execute(
                            "DELETE FROM inventory_transaction WHERE retailer_id=%s AND reference_type='INVOICE' AND reference_number=%s",
                            (self.db.config.retailer_id, inv_no))
                    # Update header
                    cur.execute(
                        "UPDATE core_salesinvoicemaster SET sales_invoice_date=%s, customerid_id=%s, "
                        "sales_transport_charges=%s WHERE sales_invoice_no=%s",
                        (inv_date, customer_id, transport, inv_no))
                elif use_manual:
                    # Check if manual number exists
                    cur.execute("SELECT 1 FROM core_salesinvoicemaster WHERE sales_invoice_no=%s", (manual_no,))
                    if cur.fetchone():
                        raise ValueError(f"Invoice No '{manual_no}' already exists.")
                    inv_no = manual_no
                    cur.execute(
                        "INSERT INTO core_salesinvoicemaster "
                        "(sales_invoice_no, retailer_id, sales_invoice_date, customerid_id, sales_transport_charges, sales_invoice_paid) "
                        "VALUES (%s,%s,%s,%s,%s,0)",
                        (inv_no, self.db.config.retailer_id, inv_date, customer_id, transport))
                else:
                    # Auto-generate invoice number with lock to prevent race condition
                    cur.execute(
                        "SELECT sales_invoice_no FROM core_salesinvoicemaster "
                        "WHERE sales_invoice_no REGEXP '^INV[0-9]+$' "
                        "ORDER BY CAST(SUBSTRING(sales_invoice_no,4) AS UNSIGNED) DESC LIMIT 1 FOR UPDATE")
                    row = cur.fetchone()
                    n = int(row["sales_invoice_no"][3:]) + 1 if row else 1
                    inv_no = f"INV{n:07d}"
                    cur.execute(
                        "INSERT INTO core_salesinvoicemaster "
                        "(sales_invoice_no, retailer_id, sales_invoice_date, customerid_id, sales_transport_charges, sales_invoice_paid) "
                        "VALUES (%s,%s,%s,%s,%s,0)",
                        (inv_no, self.db.config.retailer_id, inv_date, customer_id, transport))

                # Batch insert sales items WITHOUT packing multiplication
                for item in self._items:
                    qty = float(item.get("quantity", 0))  # User entered qty directly
                    free = float(item.get("free_qty", 0))
                    # DON'T multiply by packing - use qty as-is (already in units)
                    stock_deduct = qty
                    mrp = float(item.get("mrp", 0))
                    rate = float(item.get("sale_rate", 0))
                    discount = float(item.get("discount", 0))
                    cgst = float(item.get("cgst", 0))
                    sgst = float(item.get("sgst", 0))
                    total = round((mrp * qty - discount) * (1 + (cgst + sgst) / 100), 2)
                    
                    cur.execute(
                        "INSERT INTO core_salesmaster "
                        "(retailer_id, sales_invoice_no_id, customerid_id, productid_id, product_name, product_company, "
                        "product_packing, product_batch_no, product_expiry, product_MRP, sale_rate, sale_quantity, "
                        "sale_free_qty, sale_scheme, sale_discount, sale_cgst, sale_sgst, sale_total_amount, "
                        "sale_entry_date, rate_applied, sale_calculation_mode) "
                        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s,'flat')",
                        (self.db.config.retailer_id, inv_no, customer_id, item["productid"],
                         item["product_name"], item.get("product_company", ""), item.get("product_packing", ""),
                         item.get("batch_no", ""), item.get("expiry", ""), mrp, rate, qty, free,
                         float(item.get("scheme", 0)), discount, cgst, sgst, total, item.get("rate_applied", "A")))
                    
                    # Log inventory transaction with direct qty (no packing multiplication)
                    if self.db.table_exists("inventory_transaction"):
                        cur.execute(
                            "INSERT INTO inventory_transaction "
                            "(retailer_id, product_id, batch_no, expiry_date, transaction_type, quantity, free_quantity, "
                            "transaction_date, reference_type, reference_number, rate, mrp, total_value, created_at, remarks) "
                            "VALUES (%s,%s,%s,%s,'SALE',%s,%s,NOW(),'INVOICE',%s,%s,%s,%s,NOW(),%s)",
                            (self.db.config.retailer_id, item["productid"], item.get("batch_no", ""),
                             item.get("expiry", ""), stock_deduct, free, inv_no, rate, mrp, total,
                             f"Sales Invoice {inv_no}"))

            # Store the saved invoice number
            self._invoice_no = inv_no
            self.var_invoice_no.set(inv_no)
            
            messagebox.showinfo("Saved", f"Sales Invoice {inv_no} saved successfully.", parent=self)
            
            if close_after:
                if self.on_saved: 
                    self.on_saved()
                self.destroy()
                
        except Exception as e:
            import logging
            logging.error(f"Sales invoice save error: {e}")
            messagebox.showerror("Error", str(e), parent=self)

    def _create_with_no(self, data, inv_no):
        # Not needed anymore - integrated into _save method
        pass

    def _save_and_new(self):
        """Save & clear form for next invoice (used in bulk entry)."""
        self._save(close_after=False)

    def _reset_form(self):
        """Reset entire form for new invoice."""
        # Reset header
        self._invoice_no = None
        self._customer_id = None
        self._prefetch_invoice_no()
        self.var_invoice_date.set(date.today().isoformat())
        self._cust_widget.set("")
        self._cust_info.set("")
        self.var_transport.set("0")
        
        # Clear items list and tree
        self._items = []
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        self._refresh_footer()
        
        # Clear item form
        self._clear_form()
        
        # Focus on product entry
        self._prod_widget.focus()
    
    def _save_and_print(self):
        """Save invoice and directly generate print-ready receipt (no preview)."""
        try:
            # Save the invoice first
            self._save(close_after=False)
            
            inv_no = self.var_invoice_no.get().strip()
            if not inv_no or inv_no == "(auto)":
                return
            
            # Generate HTML and open in browser directly for printing (no preview dialog)
            self._generate_and_print_receipt(inv_no)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}", parent=self)
    
    def _generate_and_print_receipt(self, inv_no):
        """Generate receipt HTML and open in browser for printing - OPTIMIZED."""
        try:
            # Use in-memory data (fast - no DB query needed)
            receipt_data = {
                'sales_invoice_no': inv_no,
                'sales_invoice_date': self.var_invoice_date.get(),
                'customer_name': self._cust_widget.get() or 'Walk-in Customer',
                'sales_transport_charges': float(self.var_transport.get() or 0),
                'items': [
                    {
                        'sale_quantity': item['quantity'],
                        'quantity': item['quantity'],
                        'product_name': item['product_name'],
                        'product_packing': item['product_packing'],
                        'product_company': item['product_company'],
                        'product_batch_no': item['batch_no'],
                        'batch_no': item['batch_no'],
                        'product_expiry': item['expiry'],
                        'expiry': item['expiry'],
                        'product_MRP': item['mrp'],
                        'mrp': item['mrp'],
                        'sale_cgst': item['cgst'],
                        'cgst': item['cgst'],
                        'sale_sgst': item['sgst'],
                        'sgst': item['sgst'],
                        'sale_discount': item['discount'],
                        'discount': item['discount'],
                    } for item in self._items
                ]
            }
            
            # Generate HTML directly (no dialog preview = faster)
            from .receipt_print_dialog import ReceiptPrintDialog
            html_content = ReceiptPrintDialog.generate_receipt_html(self.app, receipt_data)
            
            # Save to temp file
            import tempfile, os
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8')
            temp_file.write(html_content)
            temp_file.close()
            
            # Open in browser (Windows startfile = faster)
            if hasattr(os, 'startfile'):
                os.startfile(temp_file.name)
            else:
                import webbrowser
                webbrowser.open(f'file://{temp_file.name}')
            
            # Quick message (non-blocking)
            self.after(50, lambda: messagebox.showinfo(
                "Print Ready", 
                "Receipt opened in browser. Use Ctrl+P to print.",
                parent=self
            ))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate receipt: {str(e)}", parent=self)

    
    def _close_and_goto_sales(self):
        """Close invoice dialog and navigate to Sales Invoices."""
        if self.on_saved:
            self.on_saved()
        self.destroy()
        # Navigate to Sales Invoices
        try:
            self.app.show_screen("Sales Invoices")
        except:
            pass

    def _print_receipt(self):
        """Open receipt print preview dialog."""
        # Check if invoice is saved
        inv_no = self.var_invoice_no.get().strip()
        if not inv_no or inv_no == "(auto)":
            if messagebox.askyesno("Save First", 
                                   "Invoice must be saved before printing.\n\nSave now?",
                                   parent=self):
                self._save(close_after=False)
                # After save, inv_no should be set
                inv_no = self.var_invoice_no.get().strip()
                if not inv_no or inv_no == "(auto)":
                    return
            else:
                return
        
        # Fetch saved invoice data
        try:
            inv = self.db.get_sales_invoice(inv_no)
            if not inv:
                messagebox.showerror("Error", f"Invoice {inv_no} not found in database.", parent=self)
                return
            
            # Get items
            items = self.db.get_sales_items(inv_no)
            
            # Prepare invoice data for receipt
            receipt_data = {
                'sales_invoice_no': inv_no,
                'sales_invoice_date': inv.get('sales_invoice_date', ''),
                'customer_name': inv.get('customer_name', 'Walk-in Customer'),
                'sales_transport_charges': inv.get('sales_transport_charges', 0),
                'items': items
            }
            
            # Open receipt dialog
            from .receipt_print_dialog import ReceiptPrintDialog
            ReceiptPrintDialog(self, self.app, receipt_data)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load invoice data: {str(e)}", parent=self)

    # ── Export ─────────────────────────────────────────────────────────────────
    def _export_excel(self):
        inv_no = self.var_invoice_no.get().strip()
        if not inv_no or inv_no == "(auto)":
            messagebox.showwarning("Save First", "Save the invoice first to export.", parent=self); return
        try:
            from ..invoice_export import export_sales_invoice_excel
            from pathlib import Path
            import os
            docs = Path.home() / "Documents" / "MedicVista_Exports"
            docs.mkdir(parents=True, exist_ok=True)
            path = export_sales_invoice_excel(self.db, inv_no, docs)
            if messagebox.askyesno("Exported", f"Saved to:\n{path}\n\nOpen now?", parent=self):
                os.startfile(path)
        except Exception as e:
            messagebox.showerror("Export Error", str(e), parent=self)

    def _export_pdf(self):
        inv_no = self.var_invoice_no.get().strip()
        if not inv_no or inv_no == "(auto)":
            messagebox.showwarning("Save First", "Save the invoice first to export.", parent=self); return
        try:
            from ..invoice_export import export_sales_invoice_pdf
            from pathlib import Path
            import os
            docs = Path.home() / "Documents" / "MedicVista_Exports"
            docs.mkdir(parents=True, exist_ok=True)
            path = export_sales_invoice_pdf(self.db, inv_no, docs)
            if messagebox.askyesno("Exported", f"Saved to:\n{path}\n\nOpen now?", parent=self):
                os.startfile(path)
        except Exception as e:
            messagebox.showerror("Export Error", str(e), parent=self)
