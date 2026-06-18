"""Stock Issue Screen with full New/Edit dialog."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from ...styles import COLORS, FONT, make_button, make_entry
from ..purchase.purchase_invoice_dialog import AutoSuggestEntry, DateEntry, L, _f


ISSUE_TYPES = ["damage", "expiry", "theft", "loss", "adjustment", "transfer", "sample", "other"]


class StockIssueScreen(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=COLORS["bg_light"], **kwargs)
        self.app = app_instance
        self._search_var = tk.StringVar()
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=COLORS["bg_light"])
        hdr.pack(fill="x", pady=(0, 8))
        tk.Label(hdr, text="Stock Issues", font=FONT["h2"],
                 fg=COLORS["dark_text"], bg=COLORS["bg_light"]).pack(side="left")
        tk.Label(hdr, text="  F6=New  Enter=Edit  Del=Delete  F5=Refresh",
                 font=FONT["sm"], fg=COLORS["muted"], bg=COLORS["bg_light"]).pack(side="left", padx=8)

        bar = tk.Frame(self, bg=COLORS["bg_light"])
        bar.pack(fill="x", pady=(0, 6))
        make_button(bar, "F6  New Issue", "warning",
                    command=self._open_new).pack(side="left", padx=(0, 4))
        make_button(bar, "F5  Refresh", "primary",
                    command=self.on_show, padx=10).pack(side="left", padx=4)

        sf = tk.Frame(self, bg=COLORS["bg_light"])
        sf.pack(fill="x", pady=(0, 6))
        tk.Label(sf, text="Search:", font=FONT["sm"], fg=COLORS["gray_text"],
                 bg=COLORS["bg_light"]).pack(side="left", padx=(0, 4))
        self._search_entry = make_entry(sf, textvariable=self._search_var, width=28)
        self._search_entry.pack(side="left", padx=(0, 6))
        self._search_var.trace_add("write", lambda *_: self.on_show())
        make_button(sf, "Search", "primary", command=self.on_show, padx=10).pack(side="left", padx=(0, 4))
        make_button(sf, "Reset", "secondary", command=self._reset, padx=8).pack(side="left")

        cols   = ("#", "Issue No", "Date", "Issue Type", "Total Value", "Remarks")
        widths = (40, 130, 100, 120, 110, 260)
        frm = tk.Frame(self, bg=COLORS["bg_light"])
        frm.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(frm, orient="vertical")
        hsb = ttk.Scrollbar(frm, orient="horizontal")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings",
                                  yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="w" if col in ("Remarks",) else "center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frm.grid_rowconfigure(0, weight=1)
        frm.grid_columnconfigure(0, weight=1)
        self.tree.bind("<Return>", lambda e: self._edit_selected())
        self.tree.bind("<Delete>", lambda e: self._delete_selected())

        hint = tk.Frame(self, bg=COLORS["white"], pady=4)
        hint.pack(fill="x")
        tk.Label(hint, text="Enter=Edit  Del=Delete  F6=New",
                 font=FONT["sm"], fg=COLORS["muted"], bg=COLORS["white"]).pack(side="left", padx=10)
        self._status = tk.StringVar(value="Ready")
        tk.Label(hint, textvariable=self._status, font=FONT["sm"],
                 fg=COLORS["purple"], bg=COLORS["white"]).pack(side="right", padx=10)

        # keyboard
        self.bind_all("<F6>", lambda e: self._open_new())

    def _reset(self):
        self._search_var.set("")
        self.on_show()

    def on_show(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            search = self._search_var.get()
            rows = self.app.db.fetch_stock_issues(search)
            for idx, r in enumerate(rows, 1):
                self.tree.insert("", "end", iid=str(r.get("issue_id", idx)), values=(
                    idx, r.get("issue_no", ""), r.get("issue_date", ""),
                    r.get("issue_type", ""), f"Rs {float(r.get('total_value', 0)):.2f}",
                    r.get("remarks", "") or ""
                ))
            self._status.set(f"{len(rows)} record(s)")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _open_new(self):
        StockIssueDialog(self, self.app, on_saved=self.on_show)

    def _edit_selected(self):
        sel = self.tree.focus()
        if not sel:
            return
        issue = self.app.db.get_stock_issue(int(sel))
        if issue:
            StockIssueDialog(self, self.app, issue_data=issue, on_saved=self.on_show)

    def _delete_selected(self):
        sel = self.tree.focus()
        if not sel:
            return
        vals = self.tree.item(sel, "values")
        if messagebox.askyesno("Confirm", f"Delete issue '{vals[1]}'?"):
            try:
                self.app.db.delete_stock_issue(int(sel))
                self.on_show()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def kb_new(self):     self._open_new()
    def kb_refresh(self): self.on_show()


# ── Stock Issue Dialog ─────────────────────────────────────────────────────────

class StockIssueDialog(tk.Toplevel):
    def __init__(self, parent, app, issue_data=None, on_saved=None):
        super().__init__(parent)
        self.app        = app
        self.db         = app.db
        self.on_saved   = on_saved
        self._edit_data = issue_data
        self._issue_id  = issue_data["issue_id"] if issue_data else None

        self.title("Stock Issue Entry")
        self.geometry("1050x650")
        self.state("zoomed")
        self.configure(bg=L["bg"])
        self.grab_set()

        self._product_id    = None
        self._items: list[dict] = []
        self._edit_item_idx = None

        self._build()
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<F2>",     lambda e: self._save())
        self.bind("<F4>",     lambda e: self._add_item())
        self.bind("<Delete>", lambda e: self._remove_item())

        if issue_data:
            self._load_existing()

    def _card(self, parent, title, color=None):
        outer = tk.Frame(parent, bg=L["card"],
                         highlightthickness=1, highlightbackground=L["border"])
        outer.pack(fill="x", pady=(0, 8))
        tk.Frame(outer, bg=L["card"], padx=12, pady=6).pack(fill="x")
        hf = outer.winfo_children()[0]
        tk.Label(hf, text=title, font=FONT["bold"],
                 bg=L["card"], fg=color or L["head"]).pack(side="left")
        tk.Frame(outer, bg=L["border"], height=1).pack(fill="x")
        body = tk.Frame(outer, bg=L["card"], padx=12, pady=8)
        body.pack(fill="x")
        return body

    def _lbl(self, p, t, r, c):
        tk.Label(p, text=t, font=FONT["sm"], bg=L["card"], fg=L["lbl"]).grid(
            row=r, column=c, sticky="w", padx=(0, 6), pady=3)

    def _ent(self, p, var, r, c, w=14, state="normal"):
        e = tk.Entry(p, textvariable=var, font=FONT["base"], width=w,
                     relief="solid", bd=1, state=state,
                     bg=L["input_bg"] if state == "normal" else L["border"],
                     fg=L["input_fg"], insertbackground=L["input_fg"],
                     highlightthickness=1, highlightbackground=L["border"],
                     highlightcolor=L["blue"])
        e.grid(row=r, column=c, sticky="w", padx=(0, 16), pady=3)
        return e

    def _build(self):
        # topbar
        top = tk.Frame(self, bg=L["topbar"], height=46)
        top.pack(fill="x"); top.pack_propagate(False)
        tk.Label(top, text="  Stock Issue Entry", font=FONT["h3"],
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
        right = tk.Frame(body, bg=L["bg"], width=480)
        right.pack(side="right", fill="both", padx=(6, 0))
        right.pack_propagate(False)

        self._build_header(left)
        self._build_item_form(left)
        self._build_list(right)
        self._build_footer(right)

    def _build_header(self, parent):
        frm = self._card(parent, "Issue Header", L["orange"])

        self._lbl(frm, "Issue Date *", 0, 0)
        self.var_date = tk.StringVar(value=date.today().isoformat())
        DateEntry(frm, textvariable=self.var_date, width=12,
                  bg=L["card"]).grid(row=0, column=1, sticky="w", padx=(0, 16), pady=3)

        self._lbl(frm, "Issue Type *", 0, 2)
        self.var_type = tk.StringVar(value=ISSUE_TYPES[0])
        ttk.Combobox(frm, textvariable=self.var_type, values=ISSUE_TYPES,
                     font=FONT["base"], width=14, state="readonly").grid(
            row=0, column=3, sticky="w", padx=(0, 16), pady=3)

        self._lbl(frm, "Remarks", 1, 0)
        self.var_remarks = tk.StringVar()
        self._ent(frm, self.var_remarks, 1, 1, w=40)

    def _build_item_form(self, parent):
        frm = self._card(parent, "Add Item  (F4)", L["blue"])
        frm.grid_columnconfigure(1, weight=1)

        self._lbl(frm, "Product *", 0, 0)
        self._prod_widget = AutoSuggestEntry(
            frm,
            fetch_fn=lambda t: self.db.query(
                "SELECT productid, product_name, product_company, product_packing "
                "FROM core_productmaster WHERE product_name LIKE %s OR product_company LIKE %s "
                "ORDER BY product_name LIMIT 20",
                (f"%{t}%", f"%{t}%")),
            display_key="product_name",
            on_select=self._on_prod_select,
            width=30, bg=L["card"])
        self._prod_widget.grid(row=0, column=1, columnspan=3, sticky="ew",
                               padx=(0, 16), pady=3)
        self._prod_info = tk.StringVar()
        tk.Label(frm, textvariable=self._prod_info, font=FONT["sm"],
                 bg=L["card"], fg=L["muted"]).grid(row=0, column=4, sticky="w")

        # batch from inventory
        self._lbl(frm, "Batch *", 1, 0)
        self.var_batch = tk.StringVar()
        self._batch_combo = ttk.Combobox(frm, textvariable=self.var_batch,
                                          font=FONT["base"], width=14, state="readonly")
        self._batch_combo.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=3)
        self._batch_combo.bind("<<ComboboxSelected>>", self._on_batch_select)

        self._lbl(frm, "Expiry", 1, 2)
        self.var_expiry = tk.StringVar()
        self._ent(frm, self.var_expiry, 1, 3, w=10, state="readonly")

        self._stock_var = tk.StringVar(value="Stock: -")
        tk.Label(frm, textvariable=self._stock_var, font=FONT["bold"],
                 bg=L["card"], fg=L["orange"]).grid(row=1, column=4, sticky="w")

        self._lbl(frm, "Qty Issued *", 2, 0)
        self.var_qty = tk.StringVar(value="1")
        qe = self._ent(frm, self.var_qty, 2, 1, w=8)
        qe.bind("<FocusOut>", lambda e: self._calc())

        self._lbl(frm, "Unit Rate", 2, 2)
        self.var_rate = tk.StringVar(value="0")
        re_ = self._ent(frm, self.var_rate, 2, 3, w=10)
        re_.bind("<FocusOut>", lambda e: self._calc())

        self._line_total_var = tk.StringVar(value="Line Total: Rs 0.00")
        tk.Label(frm, textvariable=self._line_total_var, font=FONT["bold"],
                 bg=L["card"], fg=L["green"]).grid(row=2, column=4, sticky="w")

        self._lbl(frm, "Item Remarks", 3, 0)
        self.var_item_remarks = tk.StringVar()
        self._ent(frm, self.var_item_remarks, 3, 1, w=30)

        tk.Button(frm, text="F4  Add Item", font=FONT["base"],
                  bg=L["blue"], fg="white", relief="flat", bd=0,
                  padx=16, pady=5, cursor="hand2",
                  command=self._add_item).grid(row=3, column=3, sticky="w", pady=4)

    def _on_prod_select(self, row):
        self._product_id = int(row["productid"])
        self._prod_info.set(f"{row.get('product_company','')}  |  {row.get('product_packing','')}")
        self._load_batches()

    def _load_batches(self):
        self._batch_combo["values"] = []
        self.var_batch.set("")
        self.var_expiry.set("")
        self._stock_var.set("Stock: -")
        if not self._product_id:
            return
        try:
            batches = self.db.get_batches_for_product(self._product_id)
            opts = []
            self._batch_data = {}
            for b in batches:
                key = b["batch_no"]
                self._batch_data[key] = b
                opts.append(key)
            self._batch_combo["values"] = opts
            if opts:
                self._batch_combo.current(0)
                self._on_batch_select()
        except Exception:
            pass

    def _on_batch_select(self, e=None):
        key = self.var_batch.get()
        b   = getattr(self, "_batch_data", {}).get(key, {})
        self.var_expiry.set(str(b.get("expiry_date", "")))
        self.var_rate.set(str(b.get("purchase_rate", 0)))
        stock = float(b.get("total_stock", 0))
        self._stock_var.set(f"Stock: {stock:.0f}")

    def _calc(self):
        qty  = _f(self.var_qty.get())
        rate = _f(self.var_rate.get())
        self._line_total_var.set(f"Line Total: Rs {qty * rate:.2f}")

    def _build_list(self, parent):
        hdr = tk.Frame(parent, bg=L["card"],
                       highlightthickness=1, highlightbackground=L["border"])
        hdr.pack(fill="x", pady=(0, 4))
        hf = tk.Frame(hdr, bg=L["card"], padx=10, pady=6)
        hf.pack(fill="x")
        tk.Label(hf, text="Items", font=FONT["bold"],
                 bg=L["card"], fg=L["head"]).pack(side="left")
        tk.Button(hf, text="Del  Remove", font=FONT["sm"],
                  bg=L["red"], fg="white", relief="flat", bd=0,
                  padx=8, pady=3, cursor="hand2",
                  command=self._remove_item).pack(side="right")

        cols = ("Product", "Batch", "Expiry", "Stock", "Qty", "Rate", "Total", "Remarks")
        ws   = (130, 80, 80, 60, 50, 65, 75, 120)
        frm = tk.Frame(parent, bg=L["bg"])
        frm.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(frm, orient="vertical")
        self.items_tree = ttk.Treeview(frm, columns=cols, show="headings",
                                        yscrollcommand=vsb.set, selectmode="browse")
        vsb.config(command=self.items_tree.yview)
        for col, w in zip(cols, ws):
            self.items_tree.heading(col, text=col)
            self.items_tree.column(col, width=w,
                                   anchor="w" if col in ("Product", "Remarks") else "center",
                                   minwidth=40)
        self.items_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.items_tree.bind("<Delete>", lambda e: self._remove_item())

    def _build_footer(self, parent):
        frm = tk.Frame(parent, bg=L["topbar"], padx=14, pady=10)
        frm.pack(fill="x", side="bottom")
        self.var_total_lbl = tk.StringVar(value="Total Value: Rs 0.00")
        tk.Label(frm, textvariable=self.var_total_lbl,
                 font=FONT["xl"], bg=L["topbar"], fg="#fbbf24").pack(side="left")
        self._count_var = tk.StringVar(value="0 items")
        tk.Label(frm, textvariable=self._count_var,
                 font=FONT["sm"], bg=L["topbar"], fg="#94a3b8").pack(side="right")

    def _add_item(self):
        if not self._product_id:
            messagebox.showwarning("Validation", "Select a product first.", parent=self); return
        qty = _f(self.var_qty.get())
        if qty <= 0:
            messagebox.showwarning("Validation", "Quantity must be > 0.", parent=self); return
        batch = self.var_batch.get().strip()
        if not batch:
            messagebox.showwarning("Validation", "Select a batch.", parent=self); return

        b     = getattr(self, "_batch_data", {}).get(batch, {})
        avail = float(b.get("total_stock", 0))
        if qty > avail:
            if not messagebox.askyesno("Warning",
                    f"Only {avail:.0f} available. Proceed?", parent=self):
                return

        rate  = _f(self.var_rate.get())
        total = round(qty * rate, 2)
        p     = self.db.get_product_full(self._product_id) or {}
        item  = {
            "productid":   self._product_id,
            "product_name": p.get("product_name", ""),
            "batch_no":    batch,
            "expiry":      self.var_expiry.get().strip(),
            "stock":       avail,
            "quantity":    qty,
            "rate":        rate,
            "total":       total,
            "remarks":     self.var_item_remarks.get().strip(),
        }

        if self._edit_item_idx is not None:
            self._items[self._edit_item_idx] = item
            iid = self.items_tree.get_children()[self._edit_item_idx]
            self.items_tree.item(iid, values=self._row(item))
            self._edit_item_idx = None
        else:
            self._items.append(item)
            self.items_tree.insert("", "end", values=self._row(item))

        self._refresh_footer()
        self._clear_item()
        self._prod_widget.focus()

    def _row(self, item):
        return (item["product_name"], item["batch_no"], item["expiry"],
                f"{item['stock']:.0f}", f"{item['quantity']:.0f}",
                f"{item['rate']:.2f}", f"Rs {item['total']:.2f}", item["remarks"])

    def _remove_item(self):
        sel = self.items_tree.focus()
        if not sel: return
        idx = self.items_tree.index(sel)
        self.items_tree.delete(sel)
        if idx < len(self._items): self._items.pop(idx)
        self._refresh_footer()

    def _refresh_footer(self):
        total = sum(i["total"] for i in self._items)
        self.var_total_lbl.set(f"Total Value: Rs {total:.2f}")
        self._count_var.set(f"{len(self._items)} item(s)")

    def _clear_item(self):
        self._product_id = None
        self._edit_item_idx = None
        self._prod_widget.set("")
        self._prod_info.set("")
        self._batch_combo["values"] = []
        self.var_batch.set("")
        self.var_expiry.set("")
        self.var_qty.set("1")
        self.var_rate.set("0")
        self.var_item_remarks.set("")
        self._stock_var.set("Stock: -")
        self._line_total_var.set("Line Total: Rs 0.00")

    def _load_existing(self):
        issue = self._edit_data
        self.var_date.set(str(issue.get("issue_date", "")))
        self.var_type.set(issue.get("issue_type", "damage"))
        self.var_remarks.set(issue.get("remarks", "") or "")
        for detail in self.db.get_stock_issue_items(self._issue_id):
            item = {
                "productid":    detail["product_id_id"],
                "product_name": detail.get("product_name", ""),
                "batch_no":     detail.get("batch_no", ""),
                "expiry":       detail.get("expiry_date", ""),
                "stock":        0,
                "quantity":     float(detail.get("quantity_issued", 0)),
                "rate":         float(detail.get("unit_rate", 0)),
                "total":        float(detail.get("total_amount", 0)),
                "remarks":      detail.get("remarks", "") or "",
            }
            self._items.append(item)
            self.items_tree.insert("", "end", values=self._row(item))
        self._refresh_footer()

    def _save(self):
        try:
            issue_date = self.var_date.get().strip()
            issue_type = self.var_type.get().strip()
            if not issue_date: raise ValueError("Issue date required.")
            if not issue_type: raise ValueError("Issue type required.")
            if not self._items: raise ValueError("Add at least one item.")

            data = {"issue_date": issue_date, "issue_type": issue_type,
                    "remarks": self.var_remarks.get().strip()}

            if self._issue_id:
                self.db.execute(
                    "DELETE FROM stock_issue_detail WHERE issue_id_id=%s",
                    (self._issue_id,))
                self.db.execute(
                    "UPDATE stock_issue_master SET issue_date=%s, issue_type=%s, "
                    "remarks=%s WHERE issue_id=%s",
                    (issue_date, issue_type, data["remarks"], self._issue_id))
                issue_id = self._issue_id
            else:
                issue_id = self.db.create_stock_issue(data)

            for item in self._items:
                self.db.add_stock_issue_item(issue_id, item)

            messagebox.showinfo("Saved", "Stock Issue saved.", parent=self)
            if self.on_saved: self.on_saved()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
