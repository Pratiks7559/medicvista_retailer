"""Sales Return Dialog — Tally-style, light theme, full featured."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from ...styles import COLORS, FONT
from ..purchase.purchase_invoice_dialog import (
    AutoSuggestEntry, DateEntry, L, _f, _fmt_expiry
)


class SalesReturnDialog(tk.Toplevel):
    def __init__(self, parent, app, return_data=None, on_saved=None):
        super().__init__(parent)
        self.app         = app
        self.db          = app.db
        self.on_saved    = on_saved
        self._edit_data  = return_data
        self._return_id  = return_data["return_sales_invoice_no"] if return_data else None

        self.title("Sales Return Voucher")
        self.state("zoomed")
        self.configure(bg=L["bg"])
        self.grab_set()

        self._customer_id    = None
        self._product_id     = None
        self._items: list[dict] = []
        self._batch_data: dict[str, dict] = {}
        self._edit_item_idx  = None

        self._build()
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<F2>",     lambda e: self._save())
        self.bind("<F4>",     lambda e: self._add_item())
        self.bind("<Delete>", lambda e: self._remove_item())

        if return_data:
            self._load_existing()

    def _build(self):
        top = tk.Frame(self, bg=L["topbar"], height=46)
        top.pack(fill="x"); top.pack_propagate(False)
        tk.Label(top, text="  Sales Return Entry", font=FONT["h3"],
                 bg=L["topbar"], fg="#f8fafc").pack(side="left", padx=10)
        tk.Label(top, text="F2=Save  F4=Add Item  Del=Remove  Esc=Close",
                 font=FONT["sm"], bg=L["topbar"], fg="#94a3b8").pack(side="left", padx=16)
        for txt, cmd, bg in [("F2 Save", self._save, "#16a34a"),
                               ("Esc Close", self.destroy, "#64748b")]:
            tk.Button(top, text=txt, bg=bg, fg="white", font=FONT["sm"],
                      bd=0, relief="flat", padx=12, pady=5, cursor="hand2",
                      command=cmd).pack(side="right", padx=4, pady=6)

        body = tk.Frame(self, bg=L["bg"])
        body.pack(fill="both", expand=True, padx=10, pady=8)

        left  = tk.Frame(body, bg=L["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        tk.Frame(body, bg=L["border"], width=1).pack(side="left", fill="y")
        right = tk.Frame(body, bg=L["bg"], width=550)
        right.pack(side="right", fill="both", padx=(6, 0))
        right.pack_propagate(False)

        self._build_header(left)
        self._build_item_form(left)
        self._build_list(right)
        self._build_footer(right)

    def _card(self, parent, title, color=None):
        outer = tk.Frame(parent, bg=L["card"],
                         highlightthickness=1, highlightbackground=L["border"])
        outer.pack(fill="x", pady=(0, 8))
        hdr = tk.Frame(outer, bg=L["card"], padx=12, pady=6)
        hdr.pack(fill="x")
        tk.Label(hdr, text=title, font=FONT["bold"],
                 bg=L["card"], fg=color or L["head"]).pack(side="left")
        b = tk.Frame(outer, bg=L["card"], padx=12, pady=8)
        b.pack(fill="x")
        tk.Frame(outer, bg=L["border"], height=1).pack(fill="x", before=b)
        return b

    def _lbl(self, parent, text, r, c):
        tk.Label(parent, text=text, font=FONT["sm"],
                 bg=L["card"], fg=L["lbl"]).grid(
            row=r, column=c, sticky="w", padx=(0, 6), pady=3)

    def _ent(self, parent, var, r, c, w=14, state="normal"):
        bg = L["input_bg"] if state == "normal" else L["border"]
        e = tk.Entry(parent, textvariable=var, font=FONT["base"], width=w,
                     relief="solid", bd=1, state=state, bg=bg,
                     fg=L["input_fg"], insertbackground=L["input_fg"],
                     highlightthickness=1, highlightbackground=L["border"],
                     highlightcolor=L["blue"])
        e.grid(row=r, column=c, sticky="w", padx=(0, 16), pady=3)
        return e

    def _build_header(self, parent):
        frm = self._card(parent, "Return Header", L["purple"])

        self._lbl(frm, "Return ID", 0, 0)
        self.var_return_id = tk.StringVar()
        e = self._ent(frm, self.var_return_id, 0, 1, w=16)
        e.focus_set()

        self._lbl(frm, "Date *", 0, 2)
        self.var_return_date = tk.StringVar(value=date.today().isoformat())
        DateEntry(frm, textvariable=self.var_return_date, width=12).grid(
            row=0, column=3, sticky="w", padx=(0, 16), pady=3)

        self._lbl(frm, "Customer *", 1, 0)
        self._cust_widget = AutoSuggestEntry(
            frm,
            fetch_fn=lambda t: self.db.query(
                "SELECT customerid, customer_name, customer_mobile, customer_gstno "
                "FROM core_customermaster WHERE customer_name LIKE %s "
                "AND retailer_id=%s ORDER BY customer_name LIMIT 20",
                (f"%{t}%", self.db.config.retailer_id)),
            display_key="customer_name",
            on_select=self._on_cust_select,
            width=28)
        self._cust_widget.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=3)

        self._lbl(frm, "Return Charges", 1, 2)
        self.var_return_charges = tk.StringVar(value="0")
        self._ent(frm, self.var_return_charges, 1, 3, w=10)
        
        self._lbl(frm, "Transport", 1, 4)
        self.var_transport = tk.StringVar(value="0")
        self._ent(frm, self.var_transport, 1, 5, w=10)

        self._cust_info = tk.StringVar()
        tk.Label(frm, textvariable=self._cust_info, font=FONT["sm"],
                 bg=L["card"], fg=L["muted"]).grid(
            row=2, column=1, columnspan=5, sticky="w", pady=(0, 2))

    def _on_cust_select(self, row):
        self._customer_id = int(row["customerid"])
        self._cust_info.set(f"GST: {row.get('customer_gstno','')}  |  Mobile: {row.get('customer_mobile','')}")

    def _build_item_form(self, parent):
        frm = self._card(parent, "Return Item  (F4 to add)", L["blue"])

        self._lbl(frm, "Product *", 0, 0)
        self._prod_widget = AutoSuggestEntry(
            frm,
            fetch_fn=lambda t: self.db.query(
                "SELECT productid, product_name, product_company, product_packing, "
                "product_hsn_percent FROM core_productmaster "
                "WHERE (product_name LIKE %s OR product_company LIKE %s) "
                "AND retailer_id=%s ORDER BY product_name LIMIT 20",
                (f"%{t}%", f"%{t}%", self.db.config.retailer_id)),
            display_key="product_name",
            on_select=self._on_prod_select,
            width=30)
        frm.grid_columnconfigure(1, weight=1)
        self._prod_widget.grid(row=0, column=1, columnspan=3, sticky="ew", padx=(0, 16), pady=3)

        self._prod_info = tk.StringVar()
        tk.Label(frm, textvariable=self._prod_info, font=FONT["sm"],
                 bg=L["card"], fg=L["muted"]).grid(row=0, column=4, columnspan=2, sticky="w")

        self._lbl(frm, "Batch *", 1, 0)
        self.var_batch = tk.StringVar()
        self._batch_combo = ttk.Combobox(frm, textvariable=self.var_batch,
                                          font=FONT["base"], width=14, state="normal")
        self._batch_combo.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=3)
        self._batch_combo.bind("<<ComboboxSelected>>", self._on_batch_select)
        self._batch_combo.bind("<Return>", self._on_batch_select)

        self._lbl(frm, "Expiry (MM-YYYY)", 1, 2)
        self.var_expiry = tk.StringVar()
        ee = self._ent(frm, self.var_expiry, 1, 3, w=10)
        ee.bind("<FocusOut>", lambda e: self.var_expiry.set(_fmt_expiry(self.var_expiry.get())))

        self._lbl(frm, "MRP", 1, 4)
        self.var_mrp = tk.StringVar(value="0")
        self._ent(frm, self.var_mrp, 1, 5, w=8, state="readonly")

        self._lbl(frm, "Return Rate", 2, 0)
        self.var_rate = tk.StringVar(value="0")
        self._e_rate = self._ent(frm, self.var_rate, 2, 1, w=10)
        self._e_rate.bind("<FocusOut>", lambda e: self._calc())

        self._lbl(frm, "Return Qty *", 2, 2)
        self.var_qty = tk.StringVar(value="1")
        qe = self._ent(frm, self.var_qty, 2, 3, w=7)
        qe.bind("<FocusOut>", lambda e: self._calc())
        qe.bind("<Return>",   lambda e: self._calc())

        self._lbl(frm, "Free Qty", 2, 4)
        self.var_free_qty = tk.StringVar(value="0")
        self._ent(frm, self.var_free_qty, 2, 5, w=7)

        self._lbl(frm, "Reason", 3, 0)
        self.var_reason = tk.StringVar()
        self._ent(frm, self.var_reason, 3, 1, w=15)

        self._lbl(frm, "Discount (Rs)", 3, 2)
        self.var_discount = tk.StringVar(value="0")
        de = self._ent(frm, self.var_discount, 3, 3, w=8)
        de.bind("<FocusOut>", lambda e: self._calc())

        self._lbl(frm, "CGST %", 3, 4)
        self.var_cgst = tk.StringVar(value="0")
        self._ent(frm, self.var_cgst, 3, 5, w=6)

        self._lbl(frm, "SGST %", 4, 0)
        self.var_sgst = tk.StringVar(value="0")
        se = self._ent(frm, self.var_sgst, 4, 1, w=6)
        se.bind("<FocusOut>", lambda e: self._calc())

        self._line_total_var = tk.StringVar(value="Line Total: Rs 0.00")
        tk.Label(frm, textvariable=self._line_total_var, font=FONT["bold"],
                 bg=L["card"], fg=L["green"]).grid(row=4, column=2, columnspan=2, sticky="w")

        tk.Button(frm, text="F4  Add Item", font=FONT["base"],
                  bg=L["blue"], fg="white", relief="flat", bd=0,
                  padx=16, pady=5, cursor="hand2", command=self._add_item).grid(
            row=4, column=4, columnspan=2, sticky="w", pady=4)

    def _on_prod_select(self, row):
        self._product_id = int(row["productid"])
        packing = row.get('product_packing', '')
        self._prod_info.set(f"{row.get('product_company','')}  |  {packing}")
        gst = _f(str(row.get("product_hsn_percent") or 0))
        h = round(gst / 2, 2)
        self.var_cgst.set(str(h)); self.var_sgst.set(str(h))
        self._load_batches()

    def _load_batches(self):
        if not self._product_id: return
        self._batch_data.clear()
        opts = []
        for r in self.db.get_batches_for_product(self._product_id):
            b = r.get("batch_no", "")
            if b:
                self._batch_data[b] = r
                opts.append(b)
        self._batch_combo["values"] = opts
        if opts:
            self._batch_combo.set(opts[0])
            self._on_batch_select()

    def _on_batch_select(self, e=None):
        b = self.var_batch.get().strip()
        if b in self._batch_data:
            d = self._batch_data[b]
            self.var_expiry.set(d.get("expiry_date", ""))
            self.var_mrp.set(str(d.get("mrp", 0)))
            self.var_rate.set(str(d.get("rate_a", 0)))
            
            # Get stock directly from batch data (already in units, no need to multiply)
            qty = float(d.get("quantity", 0))
            free_qty = float(d.get("free_quantity", 0))
            total_stock = qty + free_qty
            
            p = self.db.get_product_full(self._product_id) or {}
            packing_str = p.get('product_packing', '')
            
            # Display stock as-is (already in units)
            self._prod_info.set(
                f"{p.get('product_company','')}  |  Stock: Qty {qty:.0f} + Free {free_qty:.0f} = {total_stock:.0f} units  |  {packing_str}")
        self._calc()

    def _calc(self):
        rate = _f(self.var_rate.get())
        qty  = _f(self.var_qty.get())
        disc = _f(self.var_discount.get())
        cgst = _f(self.var_cgst.get())
        sgst = _f(self.var_sgst.get())
        base = rate * qty
        discounted = base - disc
        total = round(discounted * (1 + (cgst + sgst) / 100), 2)
        self._line_total_var.set(f"Line Total: Rs {total:.2f}")

    def _build_list(self, parent):
        hdr = tk.Frame(parent, bg=L["card"],
                       highlightthickness=1, highlightbackground=L["border"])
        hdr.pack(fill="x", pady=(0, 4))
        hf = tk.Frame(hdr, bg=L["card"], padx=10, pady=6)
        hf.pack(fill="x")
        tk.Label(hf, text="Return Items", font=FONT["bold"],
                 bg=L["card"], fg=L["head"]).pack(side="left")
        tk.Button(hf, text="Del  Remove", font=FONT["sm"],
                  bg=L["red"], fg="white", relief="flat", bd=0,
                  padx=8, pady=3, cursor="hand2", command=self._remove_item).pack(side="right")

        cols = ("Product", "Batch", "Rate", "Qty", "Disc", "Reason", "Total")
        ws   = (140, 80, 60, 40, 50, 90, 80)

        frm = tk.Frame(parent, bg=L["bg"])
        frm.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(frm, orient="vertical")
        self.items_tree = ttk.Treeview(frm, columns=cols, show="headings",
                                        yscrollcommand=vsb.set, selectmode="browse")
        vsb.config(command=self.items_tree.yview)
        for col, w in zip(cols, ws):
            self.items_tree.heading(col, text=col)
            self.items_tree.column(col, width=w,
                                   anchor="w" if col in ("Product", "Reason") else "center",
                                   minwidth=40)
        self.items_tree.tag_configure("odd",  background=L["row_odd"])
        self.items_tree.tag_configure("even", background=L["row_even"])
        self.items_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.items_tree.bind("<Double-1>", self._edit_row)
        self.items_tree.bind("<Delete>",   lambda e: self._remove_item())

    def _build_footer(self, parent):
        frm = tk.Frame(parent, bg=L["topbar"], padx=14, pady=10)
        frm.pack(fill="x", side="bottom")
        self.var_total_lbl = tk.StringVar(value="Total: Rs 0.00")
        tk.Label(frm, textvariable=self.var_total_lbl,
                 font=FONT["xl"], bg=L["topbar"], fg="#4ade80").pack(side="left")
        self._count_var = tk.StringVar(value="0 items")
        tk.Label(frm, textvariable=self._count_var,
                 font=FONT["sm"], bg=L["topbar"], fg="#94a3b8").pack(side="right")

    def _add_item(self):
        if not self._product_id:
            messagebox.showwarning("Validation", "Select a product.", parent=self)
            self._prod_widget.focus(); return
        qty = _f(self.var_qty.get())
        if qty <= 0:
            messagebox.showwarning("Validation", "Quantity > 0 required.", parent=self); return

        rate = _f(self.var_rate.get())
        disc = _f(self.var_discount.get())
        cgst = _f(self.var_cgst.get())
        sgst = _f(self.var_sgst.get())
        base = rate * qty
        discounted = base - disc
        total = round(discounted * (1 + (cgst + sgst) / 100), 2)

        p = self.db.get_product_full(self._product_id) or {}
        item = {
            "productid":       self._product_id,
            "product_name":    p.get("product_name", ""),
            "product_company": p.get("product_company", ""),
            "product_packing": p.get("product_packing", ""),
            "batch_no":        self.var_batch.get().strip(),
            "expiry":          self.var_expiry.get().strip(),
            "mrp":             _f(self.var_mrp.get()),
            "return_rate":     rate,
            "quantity":        qty,
            "free_qty":        _f(self.var_free_qty.get()),
            "discount":        disc,
            "cgst":            cgst,
            "sgst":            sgst,
            "reason":          self.var_reason.get().strip(),
            "total":           total,
        }

        if self._edit_item_idx is not None:
            self._items[self._edit_item_idx] = item
            iid = self.items_tree.get_children()[self._edit_item_idx]
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
        return (item["product_name"], item["batch_no"], f"{item['return_rate']:.2f}",
                f"{item['quantity']:.0f}", f"{item['discount']:.2f}", item["reason"],
                f"Rs {item['total']:.2f}")

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
        # Trigger batch select to update stock display with packing
        self._on_batch_select()
        self.var_expiry.set(item["expiry"])
        self.var_mrp.set(str(item["mrp"]))
        self.var_rate.set(str(item["return_rate"]))
        self.var_qty.set(str(item["quantity"]))
        self.var_free_qty.set(str(item["free_qty"]))
        self.var_discount.set(str(item["discount"]))
        self.var_cgst.set(str(item["cgst"]))
        self.var_sgst.set(str(item["sgst"]))
        self.var_reason.set(item.get("reason", ""))
        self._calc()

    def _remove_item(self):
        sel = self.items_tree.focus()
        if not sel: return
        idx = self.items_tree.index(sel)
        self.items_tree.delete(sel)
        if idx < len(self._items): self._items.pop(idx)
        self._refresh_footer()

    def _refresh_footer(self):
        total     = sum(i["total"] for i in self._items)
        charges   = _f(self.var_return_charges.get())
        transport = _f(self.var_transport.get())
        self.var_total_lbl.set(f"Total: Rs {total + charges + transport:.2f}")
        self._count_var.set(f"{len(self._items)} item(s)")

    def _clear_form(self):
        self._product_id    = None
        self._edit_item_idx = None
        self._prod_widget.set("")
        self._prod_info.set("")
        self._batch_combo["values"] = []
        self.var_batch.set("")
        self.var_expiry.set("")
        for v in (self.var_mrp, self.var_rate, self.var_free_qty,
                  self.var_discount, self.var_cgst, self.var_sgst):
            v.set("0")
        self.var_reason.set("")
        self.var_qty.set("1")
        self._line_total_var.set("Line Total: Rs 0.00")

    def _load_existing(self):
        inv = self._edit_data
        self.var_return_id.set(inv.get("return_sales_invoice_no", ""))
        self.var_return_date.set(str(inv.get("return_sales_invoice_date", "")))
        self.var_return_charges.set(str(inv.get("return_sales_charges", 0)))
        self.var_transport.set(str(inv.get("transport_charges", 0)))
        self._customer_id = inv.get("return_sales_customerid_id") or inv.get("customerid")
        self._cust_widget.set(inv.get("customer_name", ""))
        for pm in self.db.get_sales_return_items(self._return_id):
            item = {
                "productid":       pm["return_productid_id"],
                "product_name":    pm.get("return_product_name", ""),
                "product_company": pm.get("return_product_company", ""),
                "product_packing": pm.get("return_product_packing", ""),
                "batch_no":        pm.get("return_product_batch_no", ""),
                "expiry":          pm.get("return_product_expiry", ""),
                "mrp":             float(pm.get("return_product_MRP", 0)),
                "return_rate":     float(pm.get("return_sale_rate", 0)),
                "quantity":        float(pm.get("return_sale_quantity", 0)),
                "free_qty":        float(pm.get("return_sale_free_qty", 0)),
                "discount":        float(pm.get("return_sale_discount", 0)),
                "cgst":            float(pm.get("return_sale_cgst", 0)),
                "sgst":            float(pm.get("return_sale_sgst", 0)),
                "reason":          pm.get("return_reason", ""),
                "total":           float(pm.get("return_sale_total_amount", 0)),
            }
            self._items.append(item)
            tag = "odd" if len(self._items) % 2 else "even"
            self.items_tree.insert("", "end", values=self._row(item), tags=(tag,))
        self._refresh_footer()

    def _save(self):
        try:
            if not self._customer_id:
                raise ValueError("Select a customer.")
            inv_no   = self.var_return_id.get().strip()
            inv_date = self.var_return_date.get().strip()
            if not inv_date: raise ValueError("Return date required.")
            if not self._items: raise ValueError("Add at least one item.")

            total     = sum(i["total"] for i in self._items)
            charges   = _f(self.var_return_charges.get())
            transport = _f(self.var_transport.get())
            data = {"return_id": inv_no, "return_date": inv_date,
                    "customer_id": self._customer_id,
                    "return_charges": charges,
                    "transport_charges": transport,
                    "return_sales_invoice_total": round(total + charges + transport, 2)}

            if self._return_id:
                self.db.delete_sales_return(self._return_id)
            inv_id = self.db.create_sales_return(data)

            for item in self._items:
                self.db.add_sales_return_item(inv_id, self._customer_id, item)

            messagebox.showinfo("Saved", f"Sales Return {inv_id} saved.", parent=self)
            if self.on_saved: self.on_saved()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
