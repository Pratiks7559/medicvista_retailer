import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from ...styles import COLORS, FONT


# ── colour tokens matching the screenshot (light card on dark bg) ─────────────
BG       = COLORS["bg_light"]    # page bg  (#0f172a)
CARD     = "#ffffff"             # white card
CARD_BDR = "#e2e8f0"
TXT      = "#1e293b"
MUTED    = "#64748b"
GREEN    = "#10b981"
GREEN_H  = "#059669"
BLUE     = "#3b82f6"
BLUE_H   = "#2563eb"
GRAY     = "#6b7280"
GRAY_H   = "#4b5563"
HDR_BG   = "#1e293b"             # dark navbar


def _btn(parent, text, bg, hover, cmd=None, padx=14, pady=7):
    b = tk.Button(parent, text=text, bg=bg, fg="white",
                  font=("Segoe UI", 10, "bold"), bd=0, relief="flat",
                  padx=padx, pady=pady, cursor="hand2",
                  activebackground=hover, activeforeground="white",
                  command=cmd)
    b.bind("<Enter>", lambda e: b.config(bg=hover))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def _entry(parent, var, width=22, ph=""):
    e = tk.Entry(parent, textvariable=var, font=("Segoe UI", 10),
                 width=width, relief="solid", bd=1,
                 bg="white", fg=TXT, insertbackground=TXT,
                 highlightthickness=2,
                 highlightbackground=CARD_BDR,
                 highlightcolor=BLUE)
    return e


class ReturnsScreen(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.app   = app_instance
        self._mode = "purchase"
        self._var_search = tk.StringVar()
        self._var_from   = tk.StringVar()
        self._var_to     = tk.StringVar()
        self._rows: list = []
        self._build()
        self._bind_keys()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.config(bg=BG)

        # ── Top header card ────────────────────────────────────────────────
        hdr_card = tk.Frame(self, bg=CARD, bd=0, relief="flat")
        hdr_card.pack(fill="x", padx=0, pady=(0, 0))
        tk.Frame(hdr_card, bg=CARD_BDR, height=1).pack(fill="x", side="bottom")

        hdr_inner = tk.Frame(hdr_card, bg=CARD, padx=20, pady=16)
        hdr_inner.pack(fill="x")

        # title
        title_row = tk.Frame(hdr_inner, bg=CARD)
        title_row.pack(fill="x")
        self._title_lbl = tk.Label(title_row,
                                    text="↺  Purchase Returns",
                                    font=("Segoe UI", 16, "bold"),
                                    fg=TXT, bg=CARD)
        self._title_lbl.pack(side="left")

        # New Return button (top-right)
        self._new_btn = _btn(hdr_inner, "⊕  New Return  (Ctrl+I)",
                              GREEN, GREEN_H, cmd=self._new_return)
        self._new_btn.pack(side="right")

        # ── Mode tabs ──────────────────────────────────────────────────────
        tab_card = tk.Frame(self, bg=CARD, padx=20, pady=10)
        tab_card.pack(fill="x")
        tk.Frame(tab_card, bg=CARD_BDR, height=1).pack(fill="x", side="bottom")

        tab_row = tk.Frame(tab_card, bg=CARD)
        tab_row.pack(anchor="w")
        self._tab_pur = self._make_tab(tab_row, "Purchase Returns", "purchase")
        self._tab_sal = self._make_tab(tab_row, "Sales Returns",    "sales")
        self._update_tabs()

        # ── Filter card ────────────────────────────────────────────────────
        flt_card = tk.Frame(self, bg="#f1f5f9", padx=20, pady=14)
        flt_card.pack(fill="x")
        tk.Frame(flt_card, bg=CARD_BDR, height=1).pack(fill="x", side="bottom")

        flt_inner = tk.Frame(flt_card, bg="#f1f5f9")
        flt_inner.pack(fill="x")

        # search
        srch_wrap = tk.Frame(flt_inner, bg="white", relief="solid", bd=1)
        srch_wrap.pack(side="left", padx=(0, 16))
        tk.Label(srch_wrap, text="🔍", bg="white", fg=BLUE,
                 font=("Segoe UI", 11)).pack(side="left", padx=(8, 2))
        self._e_search = tk.Entry(srch_wrap, textvariable=self._var_search,
                                   font=("Segoe UI", 10), width=26,
                                   relief="flat", bd=0, bg="white",
                                   fg=TXT, insertbackground=TXT)
        self._e_search.pack(side="left", padx=(0, 8), ipady=6)
        self._e_search.insert(0, "Search returns...")
        self._e_search.bind("<FocusIn>",  self._clear_ph)
        self._e_search.bind("<FocusOut>", self._restore_ph)
        self._e_search.bind("<Return>",   lambda e: self._apply_filter())

        # date from
        tk.Label(flt_inner, text="📅 From:", font=("Segoe UI", 10),
                 fg=MUTED, bg="#f1f5f9").pack(side="left", padx=(0, 4))
        self._e_from = _entry(flt_inner, self._var_from, width=13, ph="dd-mm-yyyy")
        self._e_from.pack(side="left", padx=(0, 10))
        self._e_from.bind("<Return>", lambda e: self._e_to.focus_set())

        tk.Label(flt_inner, text="To:", font=("Segoe UI", 10),
                 fg=MUTED, bg="#f1f5f9").pack(side="left", padx=(0, 4))
        self._e_to = _entry(flt_inner, self._var_to, width=13, ph="dd-mm-yyyy")
        self._e_to.pack(side="left", padx=(0, 14))
        self._e_to.bind("<Return>", lambda e: self._apply_filter())

        _btn(flt_inner, "⬤  Filter", BLUE, BLUE_H,
             cmd=self._apply_filter, padx=18).pack(side="left")

        # ── Content card ───────────────────────────────────────────────────
        self._content = tk.Frame(self, bg=CARD, padx=0, pady=0)
        self._content.pack(fill="both", expand=True, padx=0, pady=0)
        tk.Frame(self._content, bg=CARD_BDR, height=1).pack(fill="x")

        # treeview (hidden until data)
        self._tree_frame = tk.Frame(self._content, bg=CARD)
        cols = ("#", "Return No", "Date", "Party", "Total", "Paid", "Status", "Actions")
        widths = (40, 130, 100, 180, 100, 90, 90, 90)
        vsb = ttk.Scrollbar(self._tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(self._tree_frame, orient="horizontal")
        self.tree = ttk.Treeview(self._tree_frame, columns=cols,
                                  show="headings",
                                  yscrollcommand=vsb.set,
                                  xscrollcommand=hsb.set,
                                  selectmode="browse")
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w,
                             anchor="w" if col == "Party" else "center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self._tree_frame.grid_rowconfigure(0, weight=1)
        self._tree_frame.grid_columnconfigure(0, weight=1)

        # empty-state widget
        self._empty = tk.Frame(self._content, bg=CARD)
        tk.Label(self._empty, text="↺", font=("Segoe UI", 42),
                 fg="#cbd5e1", bg=CARD).pack(pady=(40, 6))
        self._empty_title = tk.Label(self._empty,
                                      text="No purchase returns found",
                                      font=("Segoe UI", 13, "bold"),
                                      fg=TXT, bg=CARD)
        self._empty_title.pack()
        self._empty_sub = tk.Label(self._empty,
                                    text="Get started by creating your first purchase return.",
                                    font=("Segoe UI", 10),
                                    fg=MUTED, bg=CARD)
        self._empty_sub.pack(pady=(2, 18))
        self._create_btn = _btn(self._empty,
                                 "⊕  Create Purchase Return",
                                 GREEN, GREEN_H,
                                 cmd=self._new_return,
                                 padx=20, pady=10)
        self._create_btn.pack()

        # ── Status bar ─────────────────────────────────────────────────────
        sb = tk.Frame(self, bg=HDR_BG, pady=6)
        sb.pack(fill="x", side="bottom")
        self._sb_var = tk.StringVar(value="Ctrl+I  Add new Purchase return")
        tk.Label(sb, textvariable=self._sb_var,
                 font=("Segoe UI", 9), fg="#94a3b8", bg=HDR_BG).pack(side="left", padx=12)
        tk.Label(sb, text="Enter=Open  Del=Delete  ↑↓=Navigate",
                 font=("Segoe UI", 9), fg="#475569", bg=HDR_BG).pack(side="right", padx=12)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _make_tab(self, parent, label, mode):
        b = tk.Label(parent, text=label, font=("Segoe UI", 10, "bold"),
                     padx=14, pady=8, cursor="hand2", bg=CARD)
        b.bind("<Button-1>", lambda e, m=mode: self._switch(m))
        b.bind("<Return>",   lambda e, m=mode: self._switch(m))
        b.pack(side="left", padx=(0, 2))
        return b

    def _update_tabs(self):
        self._tab_pur.config(
            fg=BLUE if self._mode == "purchase" else MUTED,
            relief="flat" if self._mode != "purchase" else "flat",
            bg="#eff6ff" if self._mode == "purchase" else CARD)
        self._tab_sal.config(
            fg=BLUE if self._mode == "sales" else MUTED,
            bg="#eff6ff" if self._mode == "sales" else CARD)

    def _switch(self, mode):
        self._mode = mode
        self._update_tabs()
        title = "Purchase Returns" if mode == "purchase" else "Sales Returns"
        self._title_lbl.config(text=f"↺  {title}")
        self._empty_title.config(text=f"No {title.lower()} found")
        self._empty_sub.config(
            text=f"Get started by creating your first {title[:-1].lower()}.")
        self._create_btn.config(text=f"⊕  Create {title[:-1]}")
        self._sb_var.set(f"Ctrl+I  Add new {title[:-1]}")
        self.on_show()

    def _clear_ph(self, e):
        if self._e_search.get() == "Search returns...":
            self._e_search.delete(0, "end")
            self._e_search.config(fg=TXT)

    def _restore_ph(self, e):
        if not self._e_search.get():
            self._e_search.insert(0, "Search returns...")
            self._e_search.config(fg=MUTED)

    def _search_term(self):
        v = self._var_search.get()
        return "" if v == "Search returns..." else v

    def _apply_filter(self):
        self.on_show()

    # ── Keyboard ──────────────────────────────────────────────────────────────

    def _bind_keys(self):
        self.tree.bind("<Return>",  lambda e: self._open_selected())
        self.tree.bind("<Delete>",  lambda e: self._delete_selected())
        self.tree.bind("<<TreeviewOpen>>",   lambda e: self._open_selected())
        self.tree.bind("<<TreeviewDelete>>", lambda e: self._delete_selected())

    def kb_new(self):    self._new_return()
    def kb_refresh(self): self.on_show()
    def kb_search(self): self._e_search.focus_set()
    def kb_ctrl_i(self): self._new_return()

    # ── Data ──────────────────────────────────────────────────────────────────

    def on_show(self):
        self._rows = []
        for i in self.tree.get_children():
            self.tree.delete(i)

        try:
            rid = self.app.config_data.retailer_id
            term = self._search_term().lower()
            frm  = self._var_from.get().strip()
            to   = self._var_to.get().strip()
            
            # Get FY dates from navbar
            fy_start = getattr(self.app, 'current_fy_start', None)
            fy_end = getattr(self.app, 'current_fy_end', None)

            if self._mode == "purchase":
                rows = self.app.db.fetch_purchase_returns(term)
            else:
                rows = self.app.db.fetch_sales_returns(term)

            for r in rows:
                d = str(r.get("returninvoice_date") or
                        r.get("return_sales_invoice_date") or "")
                        
                # Apply FY filter from navbar if available
                if fy_start and d < fy_start:
                    continue
                if fy_end and d > fy_end:
                    continue
                    
                if frm and d < frm:
                    continue
                if to and d > to:
                    continue
                self._rows.append(r)

        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

        self._render()

    def _render(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        if not self._rows:
            self._empty.pack(fill="both", expand=True)
            self._tree_frame.pack_forget()
            return

        self._empty.pack_forget()
        self._tree_frame.pack(fill="both", expand=True)

        for idx, r in enumerate(self._rows, 1):
            if self._mode == "purchase":
                ret_no = r.get("returninvoiceid", "")
                dt     = r.get("returninvoice_date", "")
                party  = r.get("supplier_name", "")
                total  = float(r.get("returninvoice_total", 0) or 0)
                paid   = float(r.get("returninvoice_paid",  0) or 0)
            else:
                ret_no = r.get("return_sales_invoice_no", "")
                dt     = r.get("return_sales_invoice_date", "")
                party  = r.get("customer_name", "")
                total  = float(r.get("return_sales_invoice_total", 0) or 0)
                paid   = float(r.get("return_sales_invoice_paid",  0) or 0)

            balance = total - paid
            status  = "Paid" if balance <= 0.01 else ("Partial" if paid > 0 else "Pending")
            self.tree.insert("", "end", iid=str(ret_no), values=(
                idx, ret_no, dt, party,
                f"₹{total:.2f}", f"₹{paid:.2f}", status, "Enter=Open"
            ))

        self._sb_var.set(f"{len(self._rows)} record(s)")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _new_return(self):
        if self._mode == "purchase":
            from ..purchase.purchase_return_dialog import PurchaseReturnDialog
            PurchaseReturnDialog(self, self.app, on_saved=self.on_show)
        else:
            from ..sales.sales_return_dialog import SalesReturnDialog
            SalesReturnDialog(self, self.app, on_saved=self.on_show)

    def _open_selected(self):
        sel = self.tree.focus()
        if sel:
            messagebox.showinfo("Return", f"Return: {sel}", parent=self)

    def _delete_selected(self):
        sel = self.tree.focus()
        if not sel:
            return
        if messagebox.askyesno("Delete", f"Delete return '{sel}'?", parent=self):
            try:
                if self._mode == "purchase":
                    self.app.db.delete_purchase_return(sel)
                else:
                    self.app.db.delete_sales_return(sel)
                self.on_show()
            except Exception as ex:
                messagebox.showerror("Error", str(ex), parent=self)
