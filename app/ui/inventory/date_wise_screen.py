"""Date-wise Inventory Report — Premium UI."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from ...styles import COLORS, FONT
from ...date_utils import parse_date, today_iso, month_start_iso

BG     = "#f1f5f9"; CARD   = "#ffffff"; BDR    = "#e2e8f0"
TXT    = "#1e293b"; MUTED  = "#64748b"; HDR_BG = "#0f172a"
BLUE   = "#3b82f6"; BLUE_H = "#2563eb"; BLUE_L = "#eff6ff"
GREEN  = "#10b981"; GREEN_H= "#059669"; GREEN_L= "#f0fdf4"
RED    = "#ef4444"; RED_H  = "#dc2626"
TEAL   = "#14b8a6"; TEAL_H = "#0f9488"; TEAL_L = "#f0fdfa"
INDIGO = "#6366f1"; GRAY   = "#6b7280"
ORANGE = "#f59e0b"; ORANGE_L="#fffbeb"


def _btn(p, text, bg, hover, cmd=None, padx=14, pady=8):
    b = tk.Button(p, text=text, bg=bg, fg="white",
                  font=("Segoe UI", 10, "bold"), bd=0, relief="flat",
                  padx=padx, pady=pady, cursor="hand2",
                  activebackground=hover, activeforeground="white", command=cmd)
    b.bind("<Enter>", lambda e: b.config(bg=hover))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def _field(parent, label, var, width=14, placeholder=""):
    col = tk.Frame(parent, bg=CARD)
    col.pack(side="left", padx=(0, 16))
    tk.Label(col, text=label, font=("Segoe UI", 8, "bold"),
             fg=MUTED, bg=CARD).pack(anchor="w", pady=(0, 3))
    wrap = tk.Frame(col, bg=BDR, bd=0)
    wrap.pack()
    inner = tk.Frame(wrap, bg="white", bd=0)
    inner.pack(fill="x", padx=1, pady=1)
    e = tk.Entry(inner, textvariable=var, font=("Segoe UI", 10),
                 width=width, relief="flat", bd=0,
                 bg="white", fg=TXT, insertbackground=BLUE)
    e.pack(ipady=7, padx=8)
    if placeholder:
        e.insert(0, placeholder)
        e.config(fg=MUTED)
        def _fc(ev): 
            if e.get() == placeholder: e.delete(0,"end"); e.config(fg=TXT)
            wrap.config(bg=BLUE)
        def _fo(ev):
            if not e.get(): e.insert(0, placeholder); e.config(fg=MUTED)
            wrap.config(bg=BDR)
        e.bind("<FocusIn>", _fc); e.bind("<FocusOut>", _fo)
    else:
        e.bind("<FocusIn>",  lambda ev: wrap.config(bg=BLUE))
        e.bind("<FocusOut>", lambda ev: wrap.config(bg=BDR))
    return e


class DateWiseScreen(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.app = app_instance
        self._search_var = tk.StringVar()
        self._var_from   = tk.StringVar()
        self._var_to     = tk.StringVar()
        self._rows: list = []
        self._fy_label = tk.StringVar(value="FY 2024-25")
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        hdr_inner = tk.Frame(hdr, bg=HDR_BG, padx=20, pady=14)
        hdr_inner.pack(fill="x")

        left = tk.Frame(hdr_inner, bg=HDR_BG)
        left.pack(side="left")
        tk.Label(left, text="📅  Date-wise Inventory Report",
                 font=("Segoe UI", 16, "bold"), fg="white", bg=HDR_BG).pack(anchor="w")
        tk.Label(left, text="Filter inventory by transaction date range",
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
        
        _btn(right, "📦 Batch-wise", TEAL,  TEAL_H,  cmd=lambda: self.app.show_screen("Batch-wise Report")).pack(side="left", padx=(0,6))
        _btn(right, "📊 Excel",      GREEN, GREEN_H, cmd=self._export_excel).pack(side="left", padx=(0,6))
        _btn(right, "📄 PDF",        RED,   RED_H,   cmd=self._export_pdf).pack(side="left")

        tk.Frame(self, bg=BDR, height=1).pack(fill="x")

        # ── Stat strip ────────────────────────────────────────────────────
        self._total_items = tk.StringVar(value="0")
        self._total_val   = tk.StringVar(value="₹0.00")

        stat_row = tk.Frame(self, bg=BG, padx=20, pady=12)
        stat_row.pack(fill="x")
        stat_items = [
            ("Total Records",   self._total_items, "📋", BLUE,  BLUE_L),
            ("Total Value",     self._total_val,   "₹",  GREEN, GREEN_L),
        ]
        for idx, (label, var, icon, color, bg_c) in enumerate(stat_items):
            c = tk.Frame(stat_row, bg=bg_c, highlightbackground=BDR, highlightthickness=1)
            c.pack(side="left", padx=5, ipadx=16, ipady=10)
            tk.Label(c, text=icon, font=("Segoe UI", 20), fg=color, bg=bg_c).pack(side="left", padx=(12,8))
            sub = tk.Frame(c, bg=bg_c); sub.pack(side="left")
            tk.Label(sub, text=label, font=("Segoe UI", 8, "bold"), fg=MUTED, bg=bg_c).pack(anchor="w")
            tk.Label(sub, textvariable=var, font=("Segoe UI", 16, "bold"), fg=TXT, bg=bg_c).pack(anchor="w")

        # ── Filter bar ────────────────────────────────────────────────────
        flt_card = tk.Frame(self, bg=CARD, padx=20, pady=14,
                             highlightbackground=BDR, highlightthickness=1)
        flt_card.pack(fill="x")
        tk.Frame(flt_card, bg=BDR, height=1).pack(fill="x", side="bottom")
        flt_inner = tk.Frame(flt_card, bg=CARD)
        flt_inner.pack(fill="x")

        # Search
        srch_col = tk.Frame(flt_inner, bg=CARD)
        srch_col.pack(side="left", padx=(0,20))
        tk.Label(srch_col, text="Search", font=("Segoe UI", 8, "bold"),
                 fg=MUTED, bg=CARD).pack(anchor="w", pady=(0,3))
        wrap = tk.Frame(srch_col, bg=BDR, bd=0)
        wrap.pack()
        i_wrap = tk.Frame(wrap, bg="white", bd=0)
        i_wrap.pack(fill="x", padx=1, pady=1)
        tk.Label(i_wrap, text="🔍", font=("Segoe UI", 9), fg=MUTED, bg="white").pack(side="left", padx=(8,0))
        self._e_search = tk.Entry(i_wrap, textvariable=self._search_var,
                                   font=("Segoe UI", 10), relief="flat", bd=0, width=24,
                                   bg="white", fg=TXT, insertbackground=BLUE)
        self._e_search.pack(side="left", padx=4, ipady=7)
        self._e_search.insert(0, "Product name, company…")
        self._e_search.config(fg=MUTED)
        self._e_search.bind("<FocusIn>",  self._clr)
        self._e_search.bind("<FocusOut>", self._rst)
        self._e_search.bind("<Return>",   lambda e: self.on_show())
        self._e_search.bind("<FocusIn>",  lambda e: [self._clr(e), wrap.config(bg=BLUE)])
        self._e_search.bind("<FocusOut>", lambda e: [self._rst(e), wrap.config(bg=BDR)])

        # Quick date buttons
        quick_col = tk.Frame(flt_inner, bg=CARD)
        quick_col.pack(side="left", padx=(0,20))
        tk.Label(quick_col, text="Quick Range", font=("Segoe UI", 8, "bold"),
                 fg=MUTED, bg=CARD).pack(anchor="w", pady=(0,3))
        qbtn_row = tk.Frame(quick_col, bg=CARD)
        qbtn_row.pack()
        for label, cmd in [
            ("This Month", self._set_this_month),
            ("This Year",  self._set_this_year),
            ("All Time",   self._set_all_time),
        ]:
            b = tk.Button(qbtn_row, text=label, bg="#f1f5f9", fg=TXT,
                          font=("Segoe UI", 9), bd=0, relief="flat",
                          padx=8, pady=6, cursor="hand2", command=cmd,
                          highlightbackground=BDR, highlightthickness=1)
            b.pack(side="left", padx=(0,4))
            b.bind("<Enter>", lambda e, btn=b: btn.config(bg=BLUE_L))
            b.bind("<Leave>", lambda e, btn=b: btn.config(bg="#f1f5f9"))

        self._e_from = _field(flt_inner, "From Date", self._var_from, width=13, placeholder="YYYY-MM-DD")
        self._e_from.bind("<FocusOut>", lambda e: self._var_from.set(parse_date(self._var_from.get())))
        self._e_from.bind("<Return>",   lambda e: self._e_to.focus_set())

        self._e_to = _field(flt_inner, "To Date", self._var_to, width=13, placeholder="YYYY-MM-DD")
        self._e_to.bind("<FocusOut>", lambda e: self._var_to.set(parse_date(self._var_to.get())))
        self._e_to.bind("<Return>",   lambda e: self.on_show())

        btn_col = tk.Frame(flt_inner, bg=CARD)
        btn_col.pack(side="left", pady=(18,0))
        _btn(btn_col, "▼ Apply Filter", BLUE, BLUE_H, cmd=self.on_show, pady=7).pack(side="left", padx=(0,6))
        _btn(btn_col, "⟳ Reset", GRAY, "#4b5563", cmd=self._reset, pady=7).pack(side="left")

        # ── Table ─────────────────────────────────────────────────────────
        tbl_card = tk.Frame(self, bg=CARD, highlightbackground=BDR, highlightthickness=1)
        tbl_card.pack(fill="both", expand=True)

        tbar = tk.Frame(tbl_card, bg=CARD, padx=16, pady=10)
        tbar.pack(fill="x")
        tk.Frame(tbar, bg=BDR, height=1).pack(fill="x", side="bottom")
        
        tbar_left = tk.Frame(tbar, bg=CARD)
        tbar_left.pack(side="left")
        tk.Label(tbar_left, text="Inventory by Date", font=("Segoe UI", 11, "bold"), fg=TXT, bg=CARD).pack(side="left")
        self._fy_badge = tk.Label(tbar_left, textvariable=self._fy_label,
                                  font=("Segoe UI", 8, "bold"), fg="white",
                                  bg=BLUE, padx=6, pady=2)
        self._fy_badge.pack(side="left", padx=8)
        
        self._count_var = tk.StringVar(value="")
        tk.Label(tbar, textvariable=self._count_var, font=("Segoe UI", 9), fg=MUTED, bg=CARD).pack(side="left", padx=10)

        style = ttk.Style()
        style.configure("DW.Treeview", font=("Segoe UI", 10), rowheight=34,
                         background=CARD, fieldbackground=CARD, foreground=TXT, borderwidth=0)
        style.configure("DW.Treeview.Heading", font=("Segoe UI", 9, "bold"),
                         background="#f8fafc", foreground=MUTED, relief="flat")
        style.map("DW.Treeview",
                  background=[("selected", BLUE_L)],
                  foreground=[("selected", BLUE)])

        cols   = ("PRODUCT NAME","COMPANY","PACKING","BATCH NO","EXPIRY","STOCK QTY","PURCHASE RATE","MRP","STOCK VALUE")
        widths = (210, 130, 80, 110, 90, 90, 120, 90, 120)

        frm = tk.Frame(tbl_card, bg=CARD)
        frm.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(frm, orient="vertical")
        hsb = ttk.Scrollbar(frm, orient="horizontal")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings",
                                  yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                  selectmode="browse", style="DW.Treeview")
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col, anchor="w")
            self.tree.column(col, width=w, anchor="w" if col in ("PRODUCT NAME","COMPANY") else "center")
        self.tree.tag_configure("odd",  background="#f9fafb")
        self.tree.tag_configure("even", background=CARD)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frm.grid_rowconfigure(0, weight=1)
        frm.grid_columnconfigure(0, weight=1)

        foot = tk.Frame(tbl_card, bg="#f8fafc", padx=16, pady=10)
        foot.pack(fill="x")
        tk.Frame(foot, bg=BDR, height=1).pack(fill="x", side="top")
        self._footer_var = tk.StringVar(value="Total Inventory Value:  ₹0.00")
        tk.Label(foot, textvariable=self._footer_var,
                 font=("Segoe UI", 11, "bold"), fg=TXT, bg="#f8fafc").pack(side="right", pady=(6,0))

        self.bind_all("<Control-e>", lambda e: self._export_excel())
        self.bind_all("<Control-q>", lambda e: self._export_pdf())

    # ── Quick date helpers ────────────────────────────────────────────────────
    def _set_this_month(self):
        self._var_from.set(month_start_iso()); self._var_to.set(today_iso()); self.on_show()

    def _set_this_year(self):
        import datetime; y = datetime.date.today().year
        self._var_from.set(f"{y}-01-01"); self._var_to.set(today_iso()); self.on_show()

    def _set_all_time(self):
        self._var_from.set(""); self._var_to.set(""); self.on_show()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _clr(self, e):
        if self._e_search.get() == "Product name, company…":
            self._e_search.delete(0,"end"); self._e_search.config(fg=TXT)

    def _rst(self, e):
        if not self._e_search.get():
            self._e_search.insert(0,"Product name, company…"); self._e_search.config(fg=MUTED)

    def _reset(self):
        self._search_var.set(""); self._var_from.set(""); self._var_to.set("")
        self._e_search.delete(0,"end")
        self._e_search.insert(0,"Product name, company…"); self._e_search.config(fg=MUTED)
        self.on_show()

    # ── Data ──────────────────────────────────────────────────────────────────
    def on_show(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        term = self._search_var.get()
        if term == "Product name, company…": term = ""
        frm = parse_date(self._var_from.get())
        to  = parse_date(self._var_to.get())
        
        # Get FY dates and mode
        fy_start = getattr(self.app, 'current_fy_start', None)
        fy_end = getattr(self.app, 'current_fy_end', None)
        mode = getattr(self, '_mode_var', None)
        current_mode = mode.get() if mode else "current"
        
        # Update FY badge
        if hasattr(self.app, 'fy_var') and self.app.fy_var:
            fy_text = self.app.fy_var.get()
            self._fy_label.set(f"FY {fy_text}")
        
        # If FY mode and no custom dates, use FY dates
        if current_mode == "fy" and not frm and not to and fy_start and fy_end:
            frm = fy_start
            to = fy_end
        
        try:
            self._rows = self.app.db.fetch_inventory_datewise(term, frm, to)
        except Exception as ex:
            messagebox.showerror("Error", str(ex), parent=self); return

        total_val = 0.0
        for idx, r in enumerate(self._rows):
            val = float(str(r.get("value","0")).replace("₹","").replace(",","") or 0)
            total_val += val
            tag = "odd" if idx%2 else "even"
            self.tree.insert("","end", tags=(tag,), values=(
                r.get("name",""), r.get("company",""), r.get("packing",""),
                r.get("batch_no",""), r.get("expiry",""),
                r.get("stock", r.get("current_stock","0")),
                f"₹{float(r.get('purchase_rate',0)):.2f}",
                f"₹{float(str(r.get('mrp',0)).replace('₹','') or 0):.2f}",
                f"₹{val:,.2f}",
            ))

        n = len(self._rows)
        self._total_items.set(str(n))
        self._total_val.set(f"₹{total_val:,.2f}")
        self._count_var.set(f"{n} record{'s' if n!=1 else ''}")
        self._footer_var.set(f"Total Inventory Value:  ₹{total_val:,.2f}")

    def _export_excel(self):
        if not self._rows: messagebox.showinfo("No Data", "Load data first.", parent=self); return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx",
            filetypes=[("Excel","*.xlsx")], initialfile="DateWise_Inventory.xlsx", parent=self)
        if not path: return
        try:
            from ..invoice_export import export_inventory_excel
            export_inventory_excel(self._rows, Path(path))
            messagebox.showinfo("Exported", f"Saved:\n{path}", parent=self)
        except Exception as e: messagebox.showerror("Error", str(e), parent=self)

    def _export_pdf(self):
        if not self._rows: messagebox.showinfo("No Data", "Load data first.", parent=self); return
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
            filetypes=[("PDF","*.pdf")], initialfile="DateWise_Inventory.pdf", parent=self)
        if not path: return
        try:
            from ..invoice_export import export_inventory_pdf
            adapted = [{"name": r.get("name",""), "batch_no": r.get("batch_no",""),
                        "expiry": r.get("expiry",""), "stock": r.get("stock",""),
                        "current_free_qty": "", "mrp": r.get("mrp",0),
                        "value": r.get("value",0)} for r in self._rows]
            export_inventory_pdf(adapted, Path(path), "Date-wise Inventory Report")
            messagebox.showinfo("Exported", f"Saved:\n{path}", parent=self)
        except Exception as e: messagebox.showerror("Error", str(e), parent=self)

    def kb_refresh(self): self.on_show()
    def kb_search(self): self._clr(None); self._e_search.focus_set()
