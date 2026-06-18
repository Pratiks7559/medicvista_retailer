"""Purchase Invoice Dialog — Items at bottom, bulk creation inside dialog."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import re

from ...styles import COLORS, FONT

L = {
    "bg": "#f8fafc", "card": "#ffffff", "border": "#e2e8f0",
    "input_bg": "#ffffff", "input_fg": "#1e293b", "lbl": "#475569",
    "head": "#1e293b", "muted": "#94a3b8", "green": "#16a34a",
    "blue": "#2563eb", "red": "#dc2626", "orange": "#d97706",
    "purple": "#7c3aed", "topbar": "#1e293b",
    "row_odd": "#f1f5f9", "row_even": "#ffffff",
}

def _f(s, default=0.0):
    try: return float((s or "").strip())
    except: return default

def _fmt_expiry(raw):
    s = raw.strip().replace("-", "").replace("/", "")
    if re.match(r"^\d{6}$", s): return f"{s[:2]}-{s[2:]}"
    if re.match(r"^\d{4}$", s): return f"{s[:2]}-20{s[2:]}"
    if re.match(r"^\d{2}-\d{4}$", raw.strip()): return raw.strip()
    return raw.strip()


class DateEntry(tk.Frame):
    def __init__(self, parent, textvariable=None, width=12, bg=None, **kw):
        super().__init__(parent, bg=bg or L["card"])
        self._var = textvariable or tk.StringVar(value=date.today().isoformat())
        e = tk.Entry(self, textvariable=self._var, font=FONT["base"], width=width,
                     relief="solid", bd=1, bg=L["input_bg"], fg=L["input_fg"],
                     insertbackground=L["input_fg"])
        e.pack(side="left")
        tk.Button(self, text="📅", font=("Segoe UI", 8), bg=L["border"],
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
            if m: self._var.set(fmt(m)); return

    def _pick(self): _CalendarPopup(self, self._var)


class _CalendarPopup(tk.Toplevel):
    def __init__(self, parent, var):
        super().__init__(parent)
        self.var = var
        self.overrideredirect(True)
        self.configure(bg=L["border"])
        try: y, mo, d = map(int, var.get().split("-"))
        except: t = date.today(); y, mo, d = t.year, t.month, t.day
        self._year = y; self._month = mo; self._sel_day = d
        self._build()
        px, py = parent.winfo_rootx(), parent.winfo_rooty() + parent.winfo_height()
        self.geometry(f"+{px}+{py}")
        self.grab_set()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build(self):
        nav = tk.Frame(self, bg=L["card"], padx=6, pady=4); nav.pack(fill="x")
        tk.Button(nav, text="<", command=self._prev, bg=L["card"], fg=L["head"],
                  relief="flat", font=FONT["bold"], cursor="hand2").pack(side="left")
        self._title = tk.Label(nav, bg=L["card"], fg=L["head"], font=FONT["bold"])
        self._title.pack(side="left", expand=True)
        tk.Button(nav, text=">", command=self._next, bg=L["card"], fg=L["head"],
                  relief="flat", font=FONT["bold"], cursor="hand2").pack(side="right")
        self._gf = tk.Frame(self, bg=L["card"], padx=4, pady=4); self._gf.pack()
        self._draw()

    def _draw(self):
        import calendar
        for w in self._gf.winfo_children(): w.destroy()
        for i, d in enumerate(["Mo","Tu","We","Th","Fr","Sa","Su"]):
            tk.Label(self._gf, text=d, font=FONT["sm"], bg=L["card"],
                     fg=L["muted"], width=3).grid(row=0, column=i, padx=1, pady=1)
        self._title.config(text=f"{calendar.month_abbr[self._month]} {self._year}")
        for r, week in enumerate(calendar.monthcalendar(self._year, self._month), 1):
            for c, day in enumerate(week):
                if day == 0:
                    tk.Label(self._gf, text="", bg=L["card"], width=3).grid(row=r, column=c); continue
                bg = L["blue"] if day == self._sel_day else L["card"]
                fg = "white" if day == self._sel_day else L["head"]
                tk.Button(self._gf, text=str(day), width=3, relief="flat", bg=bg, fg=fg,
                          font=FONT["sm"], cursor="hand2",
                          command=lambda d=day: self._select(d)).grid(row=r, column=c, padx=1, pady=1)

    def _prev(self):
        self._month -= 1
        if self._month == 0: self._month = 12; self._year -= 1
        self._draw()

    def _next(self):
        self._month += 1
        if self._month == 13: self._month = 1; self._year += 1
        self._draw()

    def _select(self, day):
        self.var.set(f"{self._year}-{self._month:02d}-{day:02d}")
        self.destroy()


class AutoSuggestEntry(tk.Frame):
    def __init__(self, parent, fetch_fn, display_key, on_select, width=28, bg=None, **kw):
        super().__init__(parent, bg=bg or L["card"])
        self._fetch_fn = fetch_fn; self._display_key = display_key
        self._on_select = on_select; self._results = []
        self._var = tk.StringVar()
        self._var.trace_add("write", self._on_type)
        self._entry = tk.Entry(self, textvariable=self._var, font=FONT["base"], width=width,
                               relief="solid", bd=1, bg=L["input_bg"], fg=L["input_fg"],
                               insertbackground=L["input_fg"], highlightthickness=1,
                               highlightbackground=L["border"], highlightcolor=L["blue"])
        self._entry.pack(fill="x")
        self._lb_frame = self._lb = None
        self._entry.bind("<Down>", self._focus_list)
        self._entry.bind("<Escape>", lambda e: self._hide())
        self._entry.bind("<Return>", lambda e: self._pick_first())
        self._entry.bind("<Tab>", lambda e: self._pick_first())

    def get(self): return self._var.get()
    def set(self, v): self._var.set(v)
    def focus(self): self._entry.focus_set()

    def _on_type(self, *_):
        term = self._var.get().strip()
        if len(term) < 1: self._hide(); return
        try: self._results = self._fetch_fn(term)
        except: self._results = []
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
        self._lb = tk.Listbox(self._lb_frame, font=FONT["base"], bg=L["card"], fg=L["head"],
                              selectbackground=L["blue"], selectforeground="white",
                              height=min(8, len(self._results)), activestyle="none", bd=0, relief="flat")
        self._lb.pack(fill="both")
        for r in self._results: self._lb.insert("end", r[self._display_key])
        self._lb.bind("<Return>", lambda e: self._pick())
        self._lb.bind("<Double-1>", lambda e: self._pick())
        self._lb.bind("<Escape>", lambda e: self._hide())
        self._lb.bind("<FocusOut>", lambda e: self.after(150, self._hide))

    def _focus_list(self, e=None):
        if self._lb: self._lb.focus_set(); self._lb.selection_set(0)

    def _pick(self):
        if not self._lb: return
        idx = self._lb.curselection()
        if not idx: return
        row = self._results[idx[0]]
        self._var.set(row[self._display_key]); self._hide(); self._on_select(row)

    def _pick_first(self):
        if self._results:
            row = self._results[0]
            self._var.set(row[self._display_key]); self._hide(); self._on_select(row)

    def _hide(self):
        if self._lb_frame: self._lb_frame.destroy(); self._lb_frame = self._lb = None


class PurchaseInvoiceDialog(tk.Toplevel):
    def __init__(self, parent, app, invoice_data=None, on_saved=None):
        super().__init__(parent)
        self.app = app; self.db = app.db
        self.on_saved = on_saved
        self._edit_data = invoice_data
        self._invoice_id = invoice_data["invoiceid"] if invoice_data else None
        self._supplier_id = None
        self._product_id = None
        self._packing_mult = 1
        self._items: list[dict] = []
        self._edit_item_idx = None

        self.title("Purchase Invoice")
        self.state("zoomed")
        self.configure(bg=L["bg"])
        self.grab_set()

        self._build()
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<F2>", lambda e: self._save())
        self.bind("<F4>", lambda e: self._add_item())
        self.bind("<F6>", lambda e: self._save_and_new())
        self.bind("<Delete>", lambda e: self._remove_item())

        if invoice_data:
            self._load_existing()

    def _build(self):
        # ── Top bar ──
        top = tk.Frame(self, bg=L["topbar"], height=50)
        top.pack(fill="x"); top.pack_propagate(False)

        tk.Label(top, text="  🛒 Purchase Invoice", font=FONT["h3"],
                 bg=L["topbar"], fg="#f8fafc").pack(side="left", padx=10)
        tk.Label(top, text="F2=Save  F6=Save&New(Bulk)  F4=Add Item  Del=Remove  Esc=Close",
                 font=FONT["sm"], bg=L["topbar"], fg="#94a3b8").pack(side="left", padx=10)

        for txt, cmd, col in [
            ("Esc Close",      self.destroy,        "#64748b"),
            ("F6 Save & New",  self._save_and_new,  "#7c3aed"),
            ("F2 Save",        self._save,           "#16a34a"),
        ]:
            tk.Button(top, text=txt, bg=col, fg="white", font=FONT["sm"],
                      bd=0, relief="flat", padx=14, pady=6, cursor="hand2",
                      command=cmd).pack(side="right", padx=4, pady=7)

        # ── Main body ──
        body = tk.Frame(self, bg=L["bg"])
        body.pack(fill="both", expand=True, padx=12, pady=8)

        # Top section: header + item form side by side
        top_sec = tk.Frame(body, bg=L["bg"])
        top_sec.pack(fill="x", pady=(0, 6))

        self._build_header(top_sec)
        self._build_item_form(top_sec)

        # Bottom section: items table (full width)
        self._build_items_table(body)

    # ── Header (Invoice info) ──────────────────────────────────────────────────
    def _build_header(self, parent):
        card = tk.Frame(parent, bg=L["card"], highlightthickness=1,
                        highlightbackground=L["purple"])
        card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        tk.Frame(card, bg=L["purple"], height=3).pack(fill="x")
        hf = tk.Frame(card, bg=L["card"], padx=10, pady=6); hf.pack(fill="x")
        tk.Label(hf, text="📋 Invoice Header", font=FONT["bold"],
                 bg=L["card"], fg=L["purple"]).pack(side="left")

        frm = tk.Frame(card, bg=L["card"], padx=12, pady=10); frm.pack(fill="x")

        def lbl(t, r, c): tk.Label(frm, text=t, font=FONT["sm"], bg=L["card"],
                                    fg=L["lbl"]).grid(row=r, column=c, sticky="w", padx=(0,6), pady=4)
        def ent(var, r, c, w=16, state="normal"):
            e = tk.Entry(frm, textvariable=var, font=FONT["base"], width=w,
                         relief="solid", bd=1, state=state,
                         bg=L["input_bg"] if state == "normal" else "#f1f5f9",
                         fg=L["input_fg"], insertbackground=L["input_fg"],
                         highlightthickness=1, highlightbackground=L["border"],
                         highlightcolor=L["purple"])
            e.grid(row=r, column=c, sticky="w", padx=(0, 12), pady=4)
            return e

        lbl("Invoice No *", 0, 0)
        self.var_invoice_no = tk.StringVar()
        ent(self.var_invoice_no, 0, 1, w=18).focus_set()

        lbl("Date *", 0, 2)
        self.var_invoice_date = tk.StringVar(value=date.today().isoformat())
        DateEntry(frm, textvariable=self.var_invoice_date, width=13,
                  bg=L["card"]).grid(row=0, column=3, sticky="w", padx=(0,12), pady=4)

        lbl("Supplier *", 1, 0)
        self._supp_widget = AutoSuggestEntry(
            frm,
            fetch_fn=lambda t: self.db.query(
                "SELECT supplierid, supplier_name, supplier_mobile, supplier_gstno "
                "FROM core_suppliermaster WHERE supplier_name LIKE %s "
                "ORDER BY supplier_name LIMIT 20", (f"%{t}%",)),
            display_key="supplier_name", on_select=self._on_supp_select, width=30, bg=L["card"])
        self._supp_widget.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(0,12), pady=4)

        lbl("Transport (₹)", 2, 0)
        self.var_transport = tk.StringVar(value="0")
        ent(self.var_transport, 2, 1, w=10)

        self._supp_info = tk.StringVar()
        tk.Label(frm, textvariable=self._supp_info, font=FONT["sm"],
                 bg=L["card"], fg=L["muted"]).grid(row=2, column=2, columnspan=2, sticky="w")

    def _on_supp_select(self, row):
        self._supplier_id = int(row["supplierid"])
        self._supp_info.set(f"GST: {row.get('supplier_gstno','')}  |  Mobile: {row.get('supplier_mobile','')}")

    # ── Item entry form ────────────────────────────────────────────────────────
    def _build_item_form(self, parent):
        card = tk.Frame(parent, bg=L["card"], highlightthickness=1,
                        highlightbackground=L["blue"])
        card.pack(side="left", fill="both", expand=True)

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
                "WHERE product_name LIKE %s OR product_company LIKE %s "
                "ORDER BY product_name LIMIT 20", (f"%{t}%", f"%{t}%")),
            display_key="product_name", on_select=self._on_prod_select, width=28, bg=L["card"])
        self._prod_widget.grid(row=0, column=1, columnspan=5, sticky="ew", padx=(0,10), pady=3)
        frm.grid_columnconfigure(1, weight=1)
        self._prod_info = tk.StringVar()
        tk.Label(frm, textvariable=self._prod_info, font=FONT["sm"],
                 bg=L["card"], fg=L["muted"]).grid(row=0, column=6, sticky="w")

        # Row 1: Batch, Expiry, MRP
        lbl("Batch *", 1, 0)
        self.var_batch = tk.StringVar()
        self._batch_combo = ttk.Combobox(frm, textvariable=self.var_batch,
                                          font=FONT["base"], width=14, state="normal")
        self._batch_combo.grid(row=1, column=1, sticky="w", padx=(0, 10), pady=3)
        self._batch_combo.bind("<<ComboboxSelected>>", self._on_batch_select)
        self._batch_combo.bind("<Return>", self._on_batch_select)

        lbl("Expiry", 1, 2)
        self.var_expiry = tk.StringVar()
        exp = ent(self.var_expiry, 1, 3, w=10)
        exp.bind("<FocusOut>", lambda e: self.var_expiry.set(_fmt_expiry(self.var_expiry.get())))

        lbl("MRP", 1, 4)
        self.var_mrp = tk.StringVar(value="0")
        ent(self.var_mrp, 1, 5, w=8)

        # Row 2: Rate, Qty, Free Qty
        lbl("Pur. Rate", 2, 0)
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

        # Row 4: Rate A/B/C + line total + add button
        lbl("Rate A", 4, 0)
        self.var_rate_a = tk.StringVar(value="0")
        ent(self.var_rate_a, 4, 1, w=8)

        lbl("Rate B", 4, 2)
        self.var_rate_b = tk.StringVar(value="0")
        ent(self.var_rate_b, 4, 3, w=8)

        lbl("Rate C", 4, 4)
        self.var_rate_c = tk.StringVar(value="0")
        ent(self.var_rate_c, 4, 5, w=8)

        self._line_total_var = tk.StringVar(value="Line Total: ₹ 0.00")
        tk.Label(frm, textvariable=self._line_total_var, font=FONT["bold"],
                 bg=L["card"], fg=L["green"]).grid(row=4, column=6, sticky="w", padx=4)

        tk.Button(frm, text="F4  Add to List ↓", font=FONT["base"],
                  bg=L["blue"], fg="white", relief="flat", bd=0,
                  padx=16, pady=6, cursor="hand2",
                  command=self._add_item).grid(row=4, column=7, sticky="w", pady=4)

    # ── Items table (full width at bottom) ────────────────────────────────────
    def _build_items_table(self, parent):
        card = tk.Frame(parent, bg=L["card"], highlightthickness=1,
                        highlightbackground=L["border"])
        card.pack(fill="both", expand=True)

        tk.Frame(card, bg=L["green"], height=3).pack(fill="x")
        hf = tk.Frame(card, bg=L["card"], padx=10, pady=6); hf.pack(fill="x")
        tk.Label(hf, text="📦 Invoice Items", font=FONT["bold"],
                 bg=L["card"], fg=L["green"]).pack(side="left")

        # Totals on right of header
        self.var_total_lbl = tk.StringVar(value="Grand Total: ₹ 0.00")
        tk.Label(hf, textvariable=self.var_total_lbl, font=FONT["bold"],
                 bg=L["card"], fg=L["green"]).pack(side="right", padx=10)
        self._count_var = tk.StringVar(value="0 items")
        tk.Label(hf, textvariable=self._count_var, font=FONT["sm"],
                 bg=L["card"], fg=L["muted"]).pack(side="right", padx=4)

        # Action buttons
        btn_bar = tk.Frame(card, bg=L["card"], padx=10, pady=4); btn_bar.pack(fill="x")
        tk.Button(btn_bar, text="✏ Edit (Dbl-click)", font=FONT["sm"],
                  bg="#f1f5f9", fg=L["head"], relief="flat", bd=0,
                  padx=8, pady=3, cursor="hand2",
                  command=self._edit_row).pack(side="left", padx=(0, 6))
        tk.Button(btn_bar, text="🗑 Remove (Del)", font=FONT["sm"],
                  bg=L["red"], fg="white", relief="flat", bd=0,
                  padx=8, pady=3, cursor="hand2",
                  command=self._remove_item).pack(side="left")

        # Export buttons
        tk.Button(btn_bar, text="📊 Export Excel", font=FONT["sm"],
                  bg="#d97706", fg="white", relief="flat", bd=0,
                  padx=8, pady=3, cursor="hand2",
                  command=self._export_excel).pack(side="right", padx=(6, 0))
        tk.Button(btn_bar, text="📄 Export PDF", font=FONT["sm"],
                  bg="#dc2626", fg="white", relief="flat", bd=0,
                  padx=8, pady=3, cursor="hand2",
                  command=self._export_pdf).pack(side="right")

        tk.Frame(card, bg=L["border"], height=1).pack(fill="x")

        # Treeview
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

    # ── Product / Batch ────────────────────────────────────────────────────────
    def _on_prod_select(self, row):
        self._product_id = int(row["productid"])
        packing = row.get('product_packing', '')
        self._prod_info.set(f"{row.get('product_company','')}  |  Packing: {packing}")
        gst = _f(str(row.get("product_hsn_percent") or 0))
        h = round(gst / 2, 2)
        self.var_cgst.set(str(h)); self.var_sgst.set(str(h))
        # Show packing multiplier hint on qty label
        import re as _re
        m = _re.search(r'(\d+)[xX*](\d+)', str(packing))
        if m:
            mult = int(m.group(1)) * int(m.group(2))
        else:
            m2 = _re.search(r'(\d+)', str(packing))
            mult = int(m2.group(1)) if m2 else 1
        self._packing_mult = mult
        self._line_total_var.set(f"Packing x{mult} — Line Total: ₹ 0.00")
        self._load_batch_suggestions()

    def _load_batch_suggestions(self):
        if not self._product_id: return
        try:
            rows = self.db.query(
                "SELECT product_batch_no FROM core_purchasemaster "
                "WHERE productid_id=%s GROUP BY product_batch_no "
                "ORDER BY MAX(purchaseid) DESC LIMIT 20",
                (self._product_id,))
            opts = [r["product_batch_no"] for r in rows]
            self._batch_combo["values"] = opts
            if opts:
                self._batch_combo.set(opts[0])
                self._on_batch_select()
        except: pass

    def _on_batch_select(self, e=None):
        batch = self.var_batch.get().strip()
        if not batch or not self._product_id: return
        try:
            rows = self.db.query(
                "SELECT product_MRP, product_purchase_rate, product_expiry, "
                "rate_a, rate_b, rate_c FROM core_purchasemaster "
                "WHERE productid_id=%s AND product_batch_no=%s "
                "ORDER BY purchaseid DESC LIMIT 1",
                (self._product_id, batch))
            if rows:
                r = rows[0]
                self.var_mrp.set(str(r.get("product_MRP", 0)))
                self.var_rate.set(str(r.get("product_purchase_rate", 0)))
                self.var_expiry.set(str(r.get("product_expiry", "")))
                self.var_rate_a.set(str(r.get("rate_a", 0)))
                self.var_rate_b.set(str(r.get("rate_b", 0)))
                self.var_rate_c.set(str(r.get("rate_c", 0)))
        except: pass

    def _calc(self):
        rate = _f(self.var_rate.get()); qty = _f(self.var_qty.get())
        disc = _f(self.var_discount.get())
        cgst = _f(self.var_cgst.get()); sgst = _f(self.var_sgst.get())
        total = round((rate * qty - disc) * (1 + (cgst + sgst) / 100), 2)
        mult = getattr(self, '_packing_mult', 1)
        stock_units = int(qty * mult)
        self._line_total_var.set(f"Packing x{mult}  →  Stock +{stock_units} units   Line Total: ₹ {total:.2f}")

    # ── Add / Edit / Remove ───────────────────────────────────────────────────
    def _add_item(self):
        if not self._product_id:
            messagebox.showwarning("Validation", "Select a product first.", parent=self)
            return
        qty = _f(self.var_qty.get())
        if qty <= 0:
            messagebox.showwarning("Validation", "Quantity must be > 0.", parent=self); return
        batch = self.var_batch.get().strip()
        if not batch:
            messagebox.showwarning("Validation", "Batch No is required.", parent=self); return

        self.var_expiry.set(_fmt_expiry(self.var_expiry.get()))
        rate = _f(self.var_rate.get()); disc = _f(self.var_discount.get())
        cgst = _f(self.var_cgst.get()); sgst = _f(self.var_sgst.get())
        total = round((rate * qty - disc) * (1 + (cgst + sgst) / 100), 2)

        p = self.db.get_product_full(self._product_id) or {}
        item = {
            "productid": self._product_id,
            "product_name": p.get("product_name", ""),
            "product_company": p.get("product_company", ""),
            "product_packing": p.get("product_packing", ""),
            "batch_no": batch, "expiry": self.var_expiry.get().strip(),
            "mrp": _f(self.var_mrp.get()), "purchase_rate": rate,
            "quantity": qty, "free_qty": _f(self.var_free_qty.get()),
            "scheme": _f(self.var_scheme.get()), "discount": disc,
            "cgst": cgst, "sgst": sgst,
            "rate_a": _f(self.var_rate_a.get()), "rate_b": _f(self.var_rate_b.get()),
            "rate_c": _f(self.var_rate_c.get()), "total": total,
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
        return (len(self._items) if self._edit_item_idx is None else "",
                item["product_name"], item["batch_no"], item["expiry"],
                f"{item['mrp']:.2f}", f"{item['purchase_rate']:.2f}",
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
        self._load_batch_suggestions()
        self.var_batch.set(item["batch_no"])
        self.var_expiry.set(item["expiry"])
        self.var_mrp.set(str(item["mrp"]))
        self.var_rate.set(str(item["purchase_rate"]))
        self.var_qty.set(str(item["quantity"]))
        self.var_free_qty.set(str(item["free_qty"]))
        self.var_scheme.set(str(item["scheme"]))
        self.var_discount.set(str(item["discount"]))
        self.var_cgst.set(str(item["cgst"]))
        self.var_sgst.set(str(item["sgst"]))
        self.var_rate_a.set(str(item["rate_a"]))
        self.var_rate_b.set(str(item["rate_b"]))
        self.var_rate_c.set(str(item["rate_c"]))
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
        # Renumber
        for i, iid in enumerate(self.items_tree.get_children(), 1):
            vals = list(self.items_tree.item(iid, "values"))
            vals[0] = i
            self.items_tree.item(iid, values=vals)

    def _clear_form(self):
        self._product_id = None; self._edit_item_idx = None; self._packing_mult = 1
        self._prod_widget.set(""); self._prod_info.set("")
        self._batch_combo["values"] = []; self.var_batch.set(""); self.var_expiry.set("")
        for v in (self.var_mrp, self.var_rate, self.var_free_qty, self.var_scheme,
                  self.var_discount, self.var_cgst, self.var_sgst,
                  self.var_rate_a, self.var_rate_b, self.var_rate_c):
            v.set("0")
        self.var_qty.set("1")
        self._line_total_var.set("Line Total: ₹ 0.00")

    # ── Load existing ──────────────────────────────────────────────────────────
    def _load_existing(self):
        inv = self._edit_data
        self.var_invoice_no.set(inv.get("invoice_no", ""))
        self.var_invoice_date.set(str(inv.get("invoice_date", "")))
        self.var_transport.set(str(inv.get("transport_charges", 0)))
        self._supplier_id = inv.get("supplierid_id") or inv.get("supplierid")
        self._supp_widget.set(inv.get("supplier_name", ""))
        for pm in self.db.get_invoice_items(self._invoice_id):
            item = {
                "productid": pm["productid_id"],
                "product_name": pm.get("prod_name", pm.get("product_name", "")),
                "product_company": pm.get("product_company", ""),
                "product_packing": pm.get("product_packing", ""),
                "batch_no": pm.get("product_batch_no", ""),
                "expiry": pm.get("product_expiry", ""),
                "mrp": float(pm.get("product_MRP", 0)),
                "purchase_rate": float(pm.get("product_purchase_rate", 0)),
                "quantity": float(pm.get("product_quantity", 0)),
                "free_qty": float(pm.get("product_free_qty", 0)),
                "scheme": float(pm.get("product_scheme", 0)),
                "discount": float(pm.get("product_discount_got", 0)),
                "cgst": float(pm.get("CGST", 0)), "sgst": float(pm.get("SGST", 0)),
                "rate_a": float(pm.get("rate_a", 0)), "rate_b": float(pm.get("rate_b", 0)),
                "rate_c": float(pm.get("rate_c", 0)),
                "total": float(pm.get("total_amount", 0)),
            }
            self._items.append(item)
            tag = "odd" if len(self._items) % 2 else "even"
            self.items_tree.insert("", "end", values=self._row(item), tags=(tag,))
        self._refresh_footer()

    # ── Save ───────────────────────────────────────────────────────────────────
    def _save(self):
        try:
            if not self._supplier_id: raise ValueError("Select a supplier.")
            inv_no   = self.var_invoice_no.get().strip()
            inv_date = self.var_invoice_date.get().strip()
            if not inv_no:   raise ValueError("Invoice number required.")
            if not inv_date: raise ValueError("Invoice date required.")
            if not self._items: raise ValueError("Add at least one item.")

            transport = _f(self.var_transport.get())
            items_total = sum(i["total"] for i in self._items)
            data = {"invoice_no": inv_no, "invoice_date": inv_date,
                    "supplierid": self._supplier_id,
                    "transport_charges": transport,
                    "invoice_total": round(items_total + transport, 2)}

            if self._invoice_id:
                # Reverse old stock then delete old items
                self.db.reverse_purchase_items_stock(self._invoice_id)
                self.db.update_invoice(self._invoice_id, data)
                self.db.execute("DELETE FROM core_purchasemaster WHERE product_invoiceid_id=%s",
                                (self._invoice_id,))
                inv_id = self._invoice_id
            else:
                # Check duplicate invoice number
                exists = self.db.query(
                    "SELECT 1 FROM core_invoicemaster WHERE invoice_no=%s AND retailer_id=%s",
                    (inv_no, self.db.config.retailer_id))
                if exists:
                    raise ValueError(f"Invoice No '{inv_no}' already exists.")
                inv_id = self.db.create_invoice(data)

            for item in self._items:
                self.db.add_purchase_item(inv_id, inv_no, self._supplier_id, item)
            self.db.recalc_invoice_total(inv_id)

            messagebox.showinfo("Saved", f"Purchase Invoice {inv_no} saved successfully.", parent=self)
            self.destroy()
            if self.on_saved: self.on_saved()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _save_and_new(self):
        """Save & open next (bulk entry driven by caller's on_saved)."""
        self._save()

    # ── Export ─────────────────────────────────────────────────────────────────
    def _export_excel(self):
        if not self._invoice_id and not self.var_invoice_no.get().strip():
            messagebox.showwarning("Save First", "Save the invoice first to export.", parent=self); return
        try:
            from ..invoice_export import export_purchase_invoice_excel
            from pathlib import Path
            import os
            docs = Path.home() / "Documents" / "MedicVista_Exports"
            docs.mkdir(parents=True, exist_ok=True)
            inv_no = self.var_invoice_no.get().strip()
            path = export_purchase_invoice_excel(self.db, inv_no, docs)
            if messagebox.askyesno("Exported", f"Saved to:\n{path}\n\nOpen now?", parent=self):
                os.startfile(path)
        except Exception as e:
            messagebox.showerror("Export Error", str(e), parent=self)

    def _export_pdf(self):
        if not self.var_invoice_no.get().strip():
            messagebox.showwarning("Save First", "Save the invoice first to export.", parent=self); return
        try:
            from ..invoice_export import export_purchase_invoice_pdf
            from pathlib import Path
            import os
            docs = Path.home() / "Documents" / "MedicVista_Exports"
            docs.mkdir(parents=True, exist_ok=True)
            inv_no = self.var_invoice_no.get().strip()
            path = export_purchase_invoice_pdf(self.db, inv_no, docs)
            if messagebox.askyesno("Exported", f"Saved to:\n{path}\n\nOpen now?", parent=self):
                os.startfile(path)
        except Exception as e:
            messagebox.showerror("Export Error", str(e), parent=self)
