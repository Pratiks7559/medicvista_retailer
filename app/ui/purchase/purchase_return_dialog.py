"""Purchase Return Dialog — Tally-style, light theme, full featured."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import re

from ...styles import COLORS, FONT, make_button

# ── Light theme palette ───────────────────────────────────────────────────────
L = {
    "bg":       "#f8fafc",
    "card":     "#ffffff",
    "border":   "#e2e8f0",
    "input_bg": "#ffffff",
    "input_fg": "#1e293b",
    "lbl":      "#475569",
    "head":     "#1e293b",
    "muted":    "#94a3b8",
    "green":    "#16a34a",
    "blue":     "#2563eb",
    "red":      "#dc2626",
    "orange":   "#d97706",
    "purple":   "#7c3aed",
    "topbar":   "#1e293b",
    "row_odd":  "#f1f5f9",
    "row_even": "#ffffff",
    "sel":      "#dbeafe",
}

def _f(s, default=0.0):
    try:
        return float((s or "").strip())
    except Exception:
        return default

def _fmt_expiry(raw: str) -> str:
    s = raw.strip().replace("-", "").replace("/", "")
    if re.match(r"^\d{6}$", s):
        return f"{s[:2]}-{s[2:]}"
    if re.match(r"^\d{4}$", s):
        return f"{s[:2]}-20{s[2:]}"
    return raw.strip()

# ── Shared widgets ─────────────────────────────────────────────────────────────

class DateEntry(tk.Frame):
    def __init__(self, parent, textvariable=None, width=12, bg=L["card"], **kw):
        super().__init__(parent, bg=bg)
        self._var = textvariable or tk.StringVar(value=date.today().isoformat())
        e = tk.Entry(self, textvariable=self._var, font=FONT["base"], width=width,
                     relief="solid", bd=1, bg=L["input_bg"], fg=L["input_fg"],
                     insertbackground=L["input_fg"])
        e.pack(side="left")
        tk.Button(self, text="...", font=("Segoe UI", 8), bg=L["border"],
                  fg=L["head"], relief="flat", bd=0, padx=3, cursor="hand2",
                  command=self._pick).pack(side="left", padx=(2, 0))
        e.bind("<FocusOut>", self._validate)

    def get(self): return self._var.get()
    def set(self, v): self._var.set(v)

    def _validate(self, e=None):
        v = self._var.get().strip()
        for pat, fmt in [
            (r"^(\d{2})[/\-](\d{2})[/\-](\d{4})$", lambda m: f"{m.group(3)}-{m.group(2)}-{m.group(1)}"),
            (r"^(\d{4})[/\-](\d{2})[/\-](\d{2})$", lambda m: f"{m.group(1)}-{m.group(2)}-{m.group(3)}"),
        ]:
            m = re.match(pat, v)
            if m:
                self._var.set(fmt(m))
                return

    def _pick(self):
        _CalendarPopup(self, self._var)


class _CalendarPopup(tk.Toplevel):
    def __init__(self, parent, var):
        super().__init__(parent)
        self.var = var
        self.overrideredirect(True)
        self.configure(bg=L["border"])
        try:
            y, mo, d = map(int, var.get().split("-"))
        except Exception:
            t = date.today(); y, mo, d = t.year, t.month, t.day
        self._year = y; self._month = mo; self._sel_day = d
        self._build()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty() + parent.winfo_height()
        self.geometry(f"+{px}+{py}")
        self.grab_set()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build(self):
        nav = tk.Frame(self, bg=L["card"], padx=6, pady=4)
        nav.pack(fill="x")
        tk.Button(nav, text="<", command=self._prev, bg=L["card"], fg=L["head"],
                  relief="flat", font=FONT["bold"], cursor="hand2").pack(side="left")
        self._title = tk.Label(nav, bg=L["card"], fg=L["head"], font=FONT["bold"])
        self._title.pack(side="left", expand=True)
        tk.Button(nav, text=">", command=self._next, bg=L["card"], fg=L["head"],
                  relief="flat", font=FONT["bold"], cursor="hand2").pack(side="right")
        self._grid_frm = tk.Frame(self, bg=L["card"], padx=4, pady=4)
        self._grid_frm.pack()
        self._draw()

    def _draw(self):
        import calendar
        for w in self._grid_frm.winfo_children():
            w.destroy()
        DAYS = ["Mo","Tu","We","Th","Fr","Sa","Su"]
        for i, d in enumerate(DAYS):
            tk.Label(self._grid_frm, text=d, font=FONT["sm"], bg=L["card"],
                     fg=L["muted"], width=3).grid(row=0, column=i, padx=1, pady=1)
        self._title.config(text=f"{calendar.month_abbr[self._month]} {self._year}")
        cal = calendar.monthcalendar(self._year, self._month)
        for r, week in enumerate(cal, 1):
            for c, day in enumerate(week):
                if day == 0:
                    tk.Label(self._grid_frm, text="", bg=L["card"], width=3).grid(row=r, column=c)
                    continue
                is_sel = (day == self._sel_day)
                bg = L["blue"] if is_sel else L["card"]
                fg = "white" if is_sel else L["head"]
                tk.Button(self._grid_frm, text=str(day), width=3, relief="flat",
                          bg=bg, fg=fg, font=FONT["sm"], cursor="hand2",
                          command=lambda d=day: self._select(d)).grid(row=r, column=c, padx=1, pady=1)

    def _prev(self):
        if self._month == 1: self._month = 12; self._year -= 1
        else: self._month -= 1
        self._draw()

    def _next(self):
        if self._month == 12: self._month = 1; self._year += 1
        else: self._month += 1
        self._draw()

    def _select(self, day):
        self.var.set(f"{self._year}-{self._month:02d}-{day:02d}")
        self.destroy()


class AutoSuggestEntry(tk.Frame):
    def __init__(self, parent, fetch_fn, display_key, on_select,
                 width=28, bg=L["card"], **kw):
        super().__init__(parent, bg=bg)
        self._fetch_fn    = fetch_fn
        self._display_key = display_key
        self._on_select   = on_select
        self._results     = []
        self._var         = tk.StringVar()
        self._var.trace_add("write", self._on_type)
        self._entry = tk.Entry(self, textvariable=self._var, font=FONT["base"],
                               width=width, relief="solid", bd=1,
                               bg=L["input_bg"], fg=L["input_fg"],
                               insertbackground=L["input_fg"],
                               highlightthickness=1,
                               highlightbackground=L["border"],
                               highlightcolor=L["blue"])
        self._entry.pack(fill="x")
        self._lb_frame = None
        self._lb       = None
        self._entry.bind("<Down>",   self._focus_list)
        self._entry.bind("<Escape>", lambda e: self._hide())
        self._entry.bind("<Return>", lambda e: self._pick_first())
        self._entry.bind("<Tab>",    lambda e: self._pick_first())

    def get(self):  return self._var.get()
    def set(self, v): self._var.set(v)
    def focus(self):  self._entry.focus_set()

    def _on_type(self, *_):
        term = self._var.get().strip()
        if len(term) < 1:
            self._hide(); return
        try:   self._results = self._fetch_fn(term)
        except Exception: self._results = []
        if not self._results: self._hide(); return
        self._show()

    def _show(self):
        if self._lb_frame: self._lb_frame.destroy()
        root = self.winfo_toplevel()
        x = self._entry.winfo_rootx() - root.winfo_rootx()
        y = self._entry.winfo_rooty() - root.winfo_rooty() + self._entry.winfo_height()
        w = max(self._entry.winfo_width(), 340)
        self._lb_frame = tk.Frame(root, bg=L["border"], bd=1, relief="solid")
        self._lb_frame.place(x=x, y=y, width=w)
        self._lb = tk.Listbox(self._lb_frame, font=FONT["base"],
                              bg=L["card"], fg=L["head"],
                              selectbackground=L["blue"],
                              selectforeground="white",
                              height=min(8, len(self._results)),
                              activestyle="none", bd=0, relief="flat")
        self._lb.pack(fill="both")
        for r in self._results:
            self._lb.insert("end", r[self._display_key])
        self._lb.bind("<Return>",   lambda e: self._pick())
        self._lb.bind("<Double-1>", lambda e: self._pick())
        self._lb.bind("<Escape>",   lambda e: self._hide())
        self._lb.bind("<FocusOut>", lambda e: self.after(150, self._hide))

    def _focus_list(self, e=None):
        if self._lb:
            self._lb.focus_set()
            self._lb.selection_set(0)

    def _pick(self):
        if not self._lb: return
        idx = self._lb.curselection()
        if not idx: return
        row = self._results[idx[0]]
        self._var.set(row[self._display_key])
        self._hide()
        self._on_select(row)

    def _pick_first(self):
        if self._results:
            row = self._results[0]
            self._var.set(row[self._display_key])
            self._hide()
            self._on_select(row)

    def _hide(self):
        if self._lb_frame:
            self._lb_frame.destroy()
            self._lb_frame = None
            self._lb = None


# ── Purchase Return Dialog ────────────────────────────────────────────────────

class PurchaseReturnDialog(tk.Toplevel):
    def __init__(self, parent, app, return_data=None, on_saved=None):
        super().__init__(parent)
        self.app        = app
        self.db         = app.db
        self.on_saved   = on_saved
        self._edit_data = return_data
        self._return_id = return_data["returninvoiceid"] if return_data else None

        self.title("Purchase Return Voucher")
        self.state("zoomed")
        self.configure(bg=L["bg"])
        self.grab_set()

        self._supplier_id    = None
        self._product_id     = None
        self._items: list[dict] = []
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
        tk.Label(top, text="  Purchase Return Entry", font=FONT["h3"],
                 bg=L["topbar"], fg="#f8fafc").pack(side="left", padx=10)
        tk.Label(top, text="F2=Save  F4=Add Item  Del=Remove  Esc=Close",
                 font=FONT["sm"], bg=L["topbar"], fg="#94a3b8").pack(side="left", padx=16)
        for txt, cmd, col in [("F2 Save","success",self._save),
                               ("Esc Close","secondary",self.destroy)]:
            bg_color = COLORS["green"] if col == "success" else COLORS["gray_text"]
            tk.Button(top, text=txt, bg=bg_color,
                      fg="white", font=FONT["sm"], bd=0, relief="flat",
                      padx=12, pady=5, cursor="hand2",
                      command=cmd).pack(side="right", padx=4, pady=6)

        body = tk.Frame(self, bg=L["bg"])
        body.pack(fill="both", expand=True, padx=10, pady=8)

        left = tk.Frame(body, bg=L["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        sep = tk.Frame(body, bg=L["border"], width=1)
        sep.pack(side="left", fill="y")

        right = tk.Frame(body, bg=L["bg"], width=550)
        right.pack(side="right", fill="both", padx=(6, 0))
        right.pack_propagate(False)

        self._build_header(left)
        self._build_item_form(left)
        self._build_list(right)
        self._build_footer(right)

    def _card(self, parent, title, title_color=None):
        outer = tk.Frame(parent, bg=L["card"],
                         highlightthickness=1, highlightbackground=L["border"])
        outer.pack(fill="x", pady=(0, 8))
        hdr = tk.Frame(outer, bg=L["card"], padx=12, pady=6)
        hdr.pack(fill="x")
        tk.Label(hdr, text=title, font=FONT["bold"],
                 bg=L["card"], fg=title_color or L["head"]).pack(side="left")
        body = tk.Frame(outer, bg=L["card"], padx=12, pady=8)
        body.pack(fill="x")
        tk.Frame(outer, bg=L["border"], height=1).pack(fill="x", before=body)
        return body

    def _lbl(self, parent, text, r, c, bg=None):
        tk.Label(parent, text=text, font=FONT["sm"],
                 bg=bg or L["card"], fg=L["lbl"]).grid(
            row=r, column=c, sticky="w", padx=(0, 6), pady=3)

    def _ent(self, parent, var, r, c, w=14, state="normal", bg=None):
        e = tk.Entry(parent, textvariable=var, font=FONT["base"], width=w,
                     relief="solid", bd=1, state=state,
                     bg=bg or (L["input_bg"] if state == "normal" else L["border"]),
                     fg=L["input_fg"], insertbackground=L["input_fg"],
                     highlightthickness=1,
                     highlightbackground=L["border"],
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
        de = DateEntry(frm, textvariable=self.var_return_date, width=12, bg=L["card"])
        de.grid(row=0, column=3, sticky="w", padx=(0, 16), pady=3)

        self._lbl(frm, "Supplier *", 1, 0)
        self._supp_widget = AutoSuggestEntry(
            frm,
            fetch_fn=lambda t: self.db.query(
                "SELECT supplierid, supplier_name, supplier_mobile, supplier_gstno "
                "FROM core_suppliermaster WHERE supplier_name LIKE %s "
                "AND retailer_id=%s ORDER BY supplier_name LIMIT 20",
                (f"%{t}%", self.db.config.retailer_id)),
            display_key="supplier_name",
            on_select=self._on_supp_select,
            width=28, bg=L["card"])
        self._supp_widget.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=3)

        self._lbl(frm, "Return Charges (Rs)", 1, 2)
        self.var_return_charges = tk.StringVar(value="0")
        self._ent(frm, self.var_return_charges, 1, 3, w=10)

        self._supp_info = tk.StringVar()
        tk.Label(frm, textvariable=self._supp_info, font=FONT["sm"],
                 bg=L["card"], fg=L["muted"]).grid(
            row=2, column=1, columnspan=3, sticky="w", pady=(0, 2))

    def _on_supp_select(self, row):
        self._supplier_id = int(row["supplierid"])
        self._supp_info.set(
            f"GST: {row.get('supplier_gstno','')}  |  Mobile: {row.get('supplier_mobile','')}")

    def _build_item_form(self, parent):
        frm = self._card(parent, "Add Item  (F4 to add)", L["blue"])

        # product
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
            width=30, bg=L["card"])
        frm.grid_columnconfigure(1, weight=1)
        self._prod_widget.grid(row=0, column=1, columnspan=3, sticky="ew",
                               padx=(0, 16), pady=3)
        self._prod_info = tk.StringVar()
        tk.Label(frm, textvariable=self._prod_info, font=FONT["sm"],
                 bg=L["card"], fg=L["muted"]).grid(
            row=0, column=4, columnspan=2, sticky="w")

        self._lbl(frm, "Batch *", 1, 0)
        self.var_batch = tk.StringVar()
        self._batch_combo = ttk.Combobox(frm, textvariable=self.var_batch,
                                          font=FONT["base"], width=14)
        self._batch_combo.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=3)
        self._batch_combo.bind("<<ComboboxSelected>>", self._on_batch_select_pur)
        self._batch_combo.bind("<Return>", self._on_batch_select_pur)
        self._batch_combo.configure(state="normal")

        self._lbl(frm, "Expiry (MM-YYYY)", 1, 2)
        self.var_expiry = tk.StringVar()
        exp_e = self._ent(frm, self.var_expiry, 1, 3, w=10)
        exp_e.bind("<FocusOut>", self._fmt_expiry_field)

        self._lbl(frm, "MRP", 1, 4)
        self.var_mrp = tk.StringVar(value="0")
        self._ent(frm, self.var_mrp, 1, 5, w=8)

        # row 2
        self._lbl(frm, "Return Rate", 2, 0)
        self.var_rate = tk.StringVar(value="0")
        re_ = self._ent(frm, self.var_rate, 2, 1, w=10)
        re_.bind("<FocusOut>", lambda e: self._calc())

        self._lbl(frm, "Return Qty *", 2, 2)
        self.var_qty = tk.StringVar(value="1")
        qe = self._ent(frm, self.var_qty, 2, 3, w=7)
        qe.bind("<FocusOut>", lambda e: self._calc())
        qe.bind("<Return>",   lambda e: self._calc())

        self._lbl(frm, "Free Qty", 2, 4)
        self.var_free_qty = tk.StringVar(value="0")
        self._ent(frm, self.var_free_qty, 2, 5, w=7)

        # row 3
        self._lbl(frm, "Reason", 3, 0)
        self.var_reason = tk.StringVar()
        self._ent(frm, self.var_reason, 3, 1, w=15)

        self._lbl(frm, "CGST %", 3, 2)
        self.var_cgst = tk.StringVar(value="0")
        self._ent(frm, self.var_cgst, 3, 3, w=6)

        self._lbl(frm, "SGST %", 3, 4)
        self.var_sgst = tk.StringVar(value="0")
        se = self._ent(frm, self.var_sgst, 3, 5, w=6)
        se.bind("<FocusOut>", lambda e: self._calc())

        # line total + add button
        self._line_total_var = tk.StringVar(value="Line Total: Rs 0.00")
        tk.Label(frm, textvariable=self._line_total_var, font=FONT["bold"],
                 bg=L["card"], fg=L["green"]).grid(
            row=4, column=2, columnspan=2, sticky="w")

        tk.Button(frm, text="F4  Add Item", font=FONT["base"],
                  bg=L["blue"], fg="white", relief="flat", bd=0,
                  padx=16, pady=5, cursor="hand2",
                  command=self._add_item).grid(
            row=4, column=4, columnspan=2, sticky="w", pady=4)

    def _fmt_expiry_field(self, e=None):
        self.var_expiry.set(_fmt_expiry(self.var_expiry.get()))

    def _on_prod_select(self, row):
        self._product_id = int(row["productid"])
        self._prod_info.set(
            f"{row.get('product_company','')}  |  {row.get('product_packing','')}")
        gst = _f(str(row.get("product_hsn_percent") or 0))
        h = round(gst / 2, 2)
        self.var_cgst.set(str(h)); self.var_sgst.set(str(h))
        self._load_batch_suggestions()

    def _load_batch_suggestions(self):
        if not self._product_id:
            return
        try:
            rows = self.db.query(
                "SELECT DISTINCT product_batch_no FROM core_purchasemaster "
                "WHERE productid_id=%s ORDER BY product_batch_no DESC LIMIT 20",
                (self._product_id,))
            opts = [r["product_batch_no"] for r in rows]
            self._batch_combo["values"] = opts
            if opts:
                self._batch_combo.set(opts[0])
                self._on_batch_select_pur()
        except Exception:
            pass

    def _on_batch_select_pur(self, e=None):
        batch = self.var_batch.get().strip()
        if not batch or not self._product_id:
            return
        try:
            rows = self.db.query(
                "SELECT product_MRP, product_purchase_rate, product_expiry "
                "FROM core_purchasemaster "
                "WHERE productid_id=%s AND product_batch_no=%s "
                "ORDER BY purchaseid DESC LIMIT 1",
                (self._product_id, batch))
            if rows:
                r = rows[0]
                self.var_mrp.set(str(r.get("product_MRP", 0)))
                self.var_rate.set(str(r.get("product_purchase_rate", 0)))
                self.var_expiry.set(str(r.get("product_expiry", "")))
            
            # Fetch batches with separate quantity and free_quantity
            batches = self.db.get_batches_for_product(self._product_id)
            
            # Find the selected batch
            qty = 0
            free_qty = 0
            for b in batches:
                if b.get('batch_no') == batch:
                    qty = float(b.get('quantity', 0))
                    free_qty = float(b.get('free_quantity', 0))
                    break
            
            # Get product details for display
            p = self.db.get_product_full(self._product_id) or {}
            packing_str = p.get('product_packing', '')
            
            # Display quantity and free quantity separately (already in individual units)
            self._prod_info.set(
                f"{p.get('product_company','')}  |  Qty: {qty:.0f}  |  Free: {free_qty:.0f}  |  {packing_str}")
        except Exception:
            pass

    def _calc(self):
        rate = _f(self.var_rate.get())
        qty  = _f(self.var_qty.get())
        cgst = _f(self.var_cgst.get())
        sgst = _f(self.var_sgst.get())
        total = round((rate * qty) * (1 + (cgst + sgst) / 100), 2)
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
                  padx=8, pady=3, cursor="hand2",
                  command=self._remove_item).pack(side="right")

        cols = ("Product", "Batch", "Expiry", "Rate", "Qty", "Reason", "Total")
        ws   = (130, 80, 70, 65, 45, 90, 80)

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

    # ── item actions ──────────────────────────────────────────────────────────

    def _add_item(self):
        if not self._product_id:
            messagebox.showwarning("Validation", "Select a product first.", parent=self)
            self._prod_widget.focus(); return
        qty = _f(self.var_qty.get())
        if qty <= 0:
            messagebox.showwarning("Validation", "Quantity must be > 0.", parent=self); return
        batch = self.var_batch.get().strip()
        if not batch:
            messagebox.showwarning("Validation", "Batch No is required.", parent=self); return

        self._fmt_expiry_field()

        rate = _f(self.var_rate.get())
        cgst = _f(self.var_cgst.get())
        sgst = _f(self.var_sgst.get())
        total = round((rate * qty) * (1 + (cgst + sgst) / 100), 2)

        p = self.db.get_product_full(self._product_id) or {}
        item = {
            "productid":       self._product_id,
            "product_name":    p.get("product_name", ""),
            "product_company": p.get("product_company", ""),
            "product_packing": p.get("product_packing", ""),
            "batch_no":        batch,
            "expiry":          self.var_expiry.get().strip(),
            "mrp":             _f(self.var_mrp.get()),
            "return_rate":     rate,
            "quantity":        qty,
            "free_qty":        _f(self.var_free_qty.get()),
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
        return (item["product_name"], item["batch_no"], item["expiry"],
                f"{item['return_rate']:.2f}", f"{item['quantity']:.0f}",
                item["reason"], f"Rs {item['total']:.2f}")

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
        self._load_batch_suggestions()
        self.var_batch.set(item["batch_no"])
        self.var_expiry.set(item["expiry"])
        self.var_mrp.set(str(item["mrp"]))
        self.var_rate.set(str(item["return_rate"]))
        self.var_qty.set(str(item["quantity"]))
        self.var_free_qty.set(str(item["free_qty"]))
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
        charges = _f(self.var_return_charges.get())
        self.var_total_lbl.set(f"Total: Rs {total + charges:.2f}")
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
                  self.var_cgst, self.var_sgst):
            v.set("0")
        self.var_reason.set("")
        self.var_qty.set("1")
        self._line_total_var.set("Line Total: Rs 0.00")

    # ── load existing ─────────────────────────────────────────────────────────

    def _load_existing(self):
        inv = self._edit_data
        self.var_return_id.set(inv.get("returninvoiceid", ""))
        self.var_return_date.set(str(inv.get("returninvoice_date", "")))
        self.var_return_charges.set(str(inv.get("return_charges", 0)))
        self._supplier_id = inv.get("returnsupplierid_id") or inv.get("supplierid")
        self._supp_widget.set(inv.get("supplier_name", ""))
        for pm in self.db.get_purchase_return_items(self._return_id):
            item = {
                "productid":       pm["returnproductid_id"],
                "product_name":    pm.get("prod_name", pm.get("product_name", "")),
                "product_company": pm.get("product_company", ""),
                "product_packing": pm.get("product_packing", ""),
                "batch_no":        pm.get("returnproduct_batch_no", ""),
                "expiry":          pm.get("returnproduct_expiry", ""),
                "mrp":             float(pm.get("returnproduct_MRP", 0)),
                "return_rate":     float(pm.get("returnproduct_purchase_rate", 0)),
                "quantity":        float(pm.get("returnproduct_quantity", 0)),
                "free_qty":        float(pm.get("returnproduct_free_qty", 0)),
                "cgst":            float(pm.get("returnproduct_cgst", 0)),
                "sgst":            float(pm.get("returnproduct_sgst", 0)),
                "reason":          pm.get("return_reason", ""),
                "total":           float(pm.get("returntotal_amount", 0)),
            }
            self._items.append(item)
            tag = "odd" if len(self._items) % 2 else "even"
            self.items_tree.insert("", "end", values=self._row(item), tags=(tag,))
        self._refresh_footer()

    # ── save ──────────────────────────────────────────────────────────────────

    def _save(self):
        try:
            if not self._supplier_id:
                raise ValueError("Select a supplier.")
            inv_no   = self.var_return_id.get().strip()
            inv_date = self.var_return_date.get().strip()
            if not inv_date: raise ValueError("Return date required.")
            if not self._items: raise ValueError("Add at least one item.")

            total     = sum(i["total"] for i in self._items)
            charges   = _f(self.var_return_charges.get())
            data = {"return_id": inv_no, "return_date": inv_date,
                    "supplier_id": self._supplier_id,
                    "return_charges": charges,
                    "returninvoice_total": round(total + charges, 2)}

            if self._return_id:
                self.db.delete_purchase_return(self._return_id)
            inv_id = self.db.create_purchase_return(data)

            for item in self._items:
                self.db.add_purchase_return_item(inv_id, self._supplier_id, item)

            messagebox.showinfo("Saved", f"Purchase Return {inv_id} saved.", parent=self)
            if self.on_saved: self.on_saved()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
