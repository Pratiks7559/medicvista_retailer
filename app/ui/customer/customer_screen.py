import tkinter as tk
from tkinter import ttk, messagebox
from ...styles import COLORS, FONT, make_button, make_entry

BG      = "#f1f5f9"
CARD    = "#ffffff"
BDR     = "#e2e8f0"
TXT     = "#1e293b"
MUTED   = "#64748b"
BLUE    = "#3b82f6"
BLUE_H  = "#2563eb"
GREEN   = "#10b981"
GREEN_H = "#059669"
RED     = "#ef4444"
RED_H   = "#dc2626"
GRAY    = "#6b7280"
TEAL    = "#0891b2"
TEAL_H  = "#0e7490"
PURPLE  = "#8b5cf6"
PURPLE_H= "#7c3aed"
HDR_BG  = "#0f172a"

TYPE_COLORS = {
    "TYPE-A": ("#dcfce7", "#15803d"),
    "TYPE-B": ("#dbeafe", "#1d4ed8"),
    "TYPE-C": ("#fef9c3", "#a16207"),
    "TYPE-D": ("#ffe4e6", "#be123c"),
}


def _btn(p, text, bg, hover, cmd=None, padx=14, pady=7):
    b = tk.Button(p, text=text, bg=bg, fg="white",
                  font=("Segoe UI", 10, "bold"), bd=0, relief="flat",
                  padx=padx, pady=pady, cursor="hand2",
                  activebackground=hover, activeforeground="white", command=cmd)
    b.bind("<Enter>", lambda e: b.config(bg=hover))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


class CustomerScreen(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.app = app_instance
        self._search_var = tk.StringVar()
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        inner = tk.Frame(hdr, bg=HDR_BG, padx=20, pady=14)
        inner.pack(fill="x")

        left = tk.Frame(inner, bg=HDR_BG)
        left.pack(side="left")
        tk.Label(left, text="👥  Customer Management",
                 font=("Segoe UI", 16, "bold"), fg="white", bg=HDR_BG).pack(anchor="w")
        tk.Label(left, text="Manage all your customer accounts and credit information",
                 font=("Segoe UI", 9), fg="#94a3b8", bg=HDR_BG).pack(anchor="w")

        right = tk.Frame(inner, bg=HDR_BG)
        right.pack(side="right")
        _btn(right, "+ Add Customer  (Ctrl+N)", TEAL,  TEAL_H,  cmd=self._open_add, padx=16, pady=8).pack(side="left", padx=(0, 6))
        _btn(right, "📊 Excel", GREEN, GREEN_H, cmd=self._export_excel, pady=8).pack(side="left", padx=(0, 6))
        _btn(right, "📄 PDF",   RED,   RED_H,   cmd=self._export_pdf,   pady=8).pack(side="left")

        tk.Frame(self, bg=BDR, height=1).pack(fill="x")

        # ── Stat cards ────────────────────────────────────────────────────
        self._total_var = tk.StringVar(value="0")
        self._type_vars = {t: tk.StringVar(value="0") for t in ("TYPE-A", "TYPE-B", "TYPE-C", "TYPE-D")}

        stat_row = tk.Frame(self, bg=BG, padx=20, pady=12)
        stat_row.pack(fill="x")

        # total card
        tc = tk.Frame(stat_row, bg=CARD, highlightbackground=BDR, highlightthickness=1)
        tc.pack(side="left", padx=(0, 12), ipadx=16, ipady=10)
        tk.Label(tc, text="👥", font=("Segoe UI", 20), fg=TEAL, bg=CARD).pack(side="left", padx=(12, 8))
        sub = tk.Frame(tc, bg=CARD)
        sub.pack(side="left")
        tk.Label(sub, text="Total Customers", font=("Segoe UI", 8), fg=MUTED, bg=CARD).pack(anchor="w")
        tk.Label(sub, textvariable=self._total_var, font=("Segoe UI", 16, "bold"), fg=TXT, bg=CARD).pack(anchor="w")

        # type badge cards
        type_items = list(self._type_vars.items())
        for idx, (t, var) in enumerate(type_items):
            bg_c, fg_c = TYPE_COLORS[t]
            fc = tk.Frame(stat_row, bg=bg_c, highlightbackground=BDR, highlightthickness=1)
            fc.pack(side="left", padx=5, ipadx=12, ipady=8)
            tk.Label(fc, text=t, font=("Segoe UI", 8, "bold"), fg=fg_c, bg=bg_c).pack()
            tk.Label(fc, textvariable=var, font=("Segoe UI", 14, "bold"), fg=fg_c, bg=bg_c).pack()

        # ── Search bar ────────────────────────────────────────────────────
        srch_card = tk.Frame(self, bg=CARD, padx=20, pady=10,
                              highlightbackground=BDR, highlightthickness=1)
        srch_card.pack(fill="x")
        tk.Frame(srch_card, bg=BDR, height=1).pack(fill="x", side="bottom")
        srch_inner = tk.Frame(srch_card, bg=CARD)
        srch_inner.pack(fill="x")

        wrap = tk.Frame(srch_inner, bg="white", relief="solid", bd=1,
                        highlightthickness=2, highlightbackground=TEAL)
        wrap.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(wrap, text="🔍", font=("Segoe UI", 10), fg=MUTED, bg="white").pack(side="left", padx=(8, 0))
        self._search_entry = tk.Entry(wrap, textvariable=self._search_var,
                                       font=("Segoe UI", 10), relief="flat", bd=0,
                                       bg="white", fg=TXT, insertbackground=TEAL)
        self._search_entry.pack(side="left", fill="x", expand=True, padx=6, ipady=7)
        self._search_entry.insert(0, "Search by name, mobile, email…")
        self._search_entry.bind("<FocusIn>",  self._clr)
        self._search_entry.bind("<FocusOut>", self._rst)
        self._search_entry.bind("<Return>",   lambda e: self.on_show())
        self._search_var.trace_add("write", lambda *_: self.on_show())

        _btn(srch_inner, "Search", TEAL,  TEAL_H,   cmd=self.on_show,  pady=7).pack(side="left", padx=(0, 6))
        _btn(srch_inner, "Reset",  GRAY, "#4b5563",  cmd=self._reset,   pady=7).pack(side="left")

        # ── Table ─────────────────────────────────────────────────────────
        tbl_card = tk.Frame(self, bg=CARD, highlightbackground=BDR, highlightthickness=1)
        tbl_card.pack(fill="both", expand=True)

        tbar = tk.Frame(tbl_card, bg=CARD, padx=16, pady=10)
        tbar.pack(fill="x")
        tk.Frame(tbar, bg=BDR, height=1).pack(fill="x", side="bottom")
        tk.Label(tbar, text="All Customers", font=("Segoe UI", 11, "bold"),
                 fg=TXT, bg=CARD).pack(side="left")
        self._count_var = tk.StringVar(value="")
        tk.Label(tbar, textvariable=self._count_var, font=("Segoe UI", 9),
                 fg=MUTED, bg=CARD).pack(side="left", padx=10)
        tk.Label(tbar, text="Double-click to Edit  |  Del = Delete  |  Ctrl+N = Add",
                 font=("Segoe UI", 8), fg=MUTED, bg=CARD).pack(side="right")

        style = ttk.Style()
        style.configure("Customer.Treeview",
                         font=("Segoe UI", 10), rowheight=34,
                         background=CARD, fieldbackground=CARD,
                         foreground=TXT, borderwidth=0)
        style.configure("Customer.Treeview.Heading",
                         font=("Segoe UI", 9, "bold"),
                         background="#f8fafc", foreground=MUTED,
                         relief="flat", borderwidth=0)
        style.map("Customer.Treeview", background=[("selected", "#f0fdfa")],
                  foreground=[("selected", TEAL)])

        cols   = ("#", "Name", "Type", "Mobile", "Email", "DL No", "GST No", "Credit Days", "Actions")
        widths = (40, 200, 80, 120, 180, 120, 120, 90, 80)
        frm = tk.Frame(tbl_card, bg=CARD)
        frm.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(frm, orient="vertical")
        hsb = ttk.Scrollbar(frm, orient="horizontal")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings",
                                  yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                  style="Customer.Treeview", selectmode="browse")
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col.upper(), anchor="w")
            self.tree.column(col, width=w, anchor="w" if col in ("Name", "Email") else "center")
        self.tree.tag_configure("odd",  background="#f8fafc")
        self.tree.tag_configure("even", background=CARD)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frm.grid_rowconfigure(0, weight=1)
        frm.grid_columnconfigure(0, weight=1)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Return>",   lambda e: self._open_edit(self.tree.focus()))
        self.tree.bind("<Delete>",   lambda e: self._delete(self.tree.focus()))

        foot = tk.Frame(tbl_card, bg=CARD, padx=16, pady=8)
        foot.pack(fill="x")
        tk.Frame(foot, bg=BDR, height=1).pack(fill="x", side="top")
        self._foot_var = tk.StringVar(value="")
        tk.Label(foot, textvariable=self._foot_var,
                 font=("Segoe UI", 9), fg=MUTED, bg=CARD).pack(side="right", pady=(6, 0))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _clr(self, e):
        if self._search_entry.get() == "Search by name, mobile, email…":
            self._search_entry.delete(0, "end")
            self._search_entry.config(fg=TXT)

    def _rst(self, e):
        if not self._search_entry.get():
            self._search_entry.insert(0, "Search by name, mobile, email…")
            self._search_entry.config(fg=MUTED)

    def _reset(self):
        self._search_var.set("")
        self._search_entry.delete(0, "end")
        self._search_entry.insert(0, "Search by name, mobile, email…")
        self._search_entry.config(fg=MUTED)
        self.on_show()

    # ── Data ──────────────────────────────────────────────────────────────────
    def on_show(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        term = self._search_var.get()
        if term == "Search by name, mobile, email…":
            term = ""
        try:
            rows = self.app.db.fetch_customers(term)
            type_counts = {"TYPE-A": 0, "TYPE-B": 0, "TYPE-C": 0, "TYPE-D": 0}
            for idx, r in enumerate(rows, 1):
                t = r.get("customer_type", "TYPE-A") or "TYPE-A"
                if t in type_counts:
                    type_counts[t] += 1
                tag = "odd" if idx % 2 else "even"
                self.tree.insert("", "end", iid=str(r.get("customerid", idx)),
                                  tags=(tag,), values=(
                    idx, r.get("customer_name", ""), t,
                    r.get("customer_mobile", ""), r.get("customer_emailid", ""),
                    r.get("customer_dlno", ""), r.get("customer_gstno", ""),
                    r.get("customer_credit_days", 0), "✏  🗑"
                ))
            n = len(rows)
            self._total_var.set(str(n))
            for t, v in self._type_vars.items():
                v.set(str(type_counts.get(t, 0)))
            self._count_var.set(f"{n} customer{'s' if n != 1 else ''} found")
            self._foot_var.set(f"Showing {n} customers")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_double_click(self, event):
        item = self.tree.focus()
        if not item:
            return
        col = self.tree.identify_column(event.x)
        if col == "#9":
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="✏  Edit",   command=lambda: self._open_edit(item))
            menu.add_command(label="🗑  Delete", command=lambda: self._delete(item))
            menu.post(event.x_root, event.y_root)
        else:
            self._open_edit(item)

    def _open_add(self):
        CustomerForm(self, self.app, on_save=self.on_show)

    def _open_edit(self, item_id):
        try:
            rows = self.app.db.query(
                "SELECT * FROM core_customermaster WHERE customerid=%s", (item_id,))
            if rows:
                CustomerForm(self, self.app, data=rows[0], on_save=self.on_show)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete(self, item_id):
        vals = self.tree.item(item_id, "values")
        name = vals[1] if vals else ""
        if messagebox.askyesno("Confirm Delete",
                                f"Delete customer '{name}'?\nThis will fail if they have invoices."):
            try:
                self.app.db.execute(
                    "DELETE FROM core_customermaster WHERE customerid=%s", (item_id,))
                self.on_show()
                messagebox.showinfo("Deleted", f"Customer '{name}' deleted.")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot delete: {e}")

    def kb_new(self):          self._open_add()
    def kb_search(self):       self._clr(None); self._search_entry.focus_set()
    def kb_refresh(self):      self.on_show()
    def kb_export_excel(self): self._export_excel()
    def kb_export_pdf(self):   self._export_pdf()

    def _export_excel(self):
        try:
            from ..invoice_export import export_report_excel
            from tkinter import filedialog
            from pathlib import Path
            import tempfile, shutil, os
            headers = ["#", "Name", "Type", "Mobile", "Email", "DL No", "GST No", "Credit Days"]
            data = [list(self.tree.item(i, "values"))[:-1] for i in self.tree.get_children()]
            fn = filedialog.asksaveasfilename(defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx")], initialfile="Customer_List.xlsx", parent=self)
            if fn:
                tmp = Path(tempfile.gettempdir()) / "tmp_cust.xlsx"
                export_report_excel("Customer List", headers, data, [""] * len(headers), tmp)
                shutil.move(str(tmp), fn)
                if messagebox.askyesno("Exported", "Excel saved!\n\nOpen now?", parent=self):
                    os.startfile(fn)
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}", parent=self)

    def _export_pdf(self):
        try:
            from ..invoice_export import export_report_pdf
            from tkinter import filedialog
            from pathlib import Path
            import tempfile, shutil, os
            headers = ["#", "Name", "Type", "Mobile", "Email", "DL No", "GST No", "Credit Days"]
            data = [list(self.tree.item(i, "values"))[:-1] for i in self.tree.get_children()]
            fn = filedialog.asksaveasfilename(defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")], initialfile="Customer_List.pdf", parent=self)
            if fn:
                tmp = Path(tempfile.gettempdir()) / "tmp_cust.pdf"
                export_report_pdf("Customer List", headers, data, [""] * len(headers),
                                  {"Total Customers": str(len(data))}, tmp)
                shutil.move(str(tmp), fn)
                if messagebox.askyesno("Exported", "PDF saved!\n\nOpen now?", parent=self):
                    os.startfile(fn)
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}", parent=self)


# ── Customer Form ─────────────────────────────────────────────────────────────

class CustomerForm(tk.Toplevel):
    FIELDS = [
        ("customer_name",            "Customer Name *",  "basic"),
        ("customer_type",            "Type",             "basic"),
        ("customer_mobile",          "Mobile",           "basic"),
        ("customer_whatsapp",        "WhatsApp",         "basic"),
        ("customer_emailid",         "Email",            "basic"),
        ("customer_spoc",            "Contact Person",   "basic"),
        ("customer_address",         "Address",          "basic"),
        ("customer_credit_days",     "Credit Days",      "basic"),
        ("customer_dlno",            "Drug Licence No",  "legal"),
        ("customer_gstno",           "GST No",           "legal"),
        ("customer_food_license_no", "Food License No",  "legal"),
    ]

    SECTION_META = {
        "basic": ("👤  Basic Information",  TEAL),
        "legal": ("📋  Legal & Compliance", PURPLE),
    }

    COMBO_FIELDS = {
        "customer_type": ["TYPE-A", "TYPE-B", "TYPE-C", "TYPE-D"],
    }

    def __init__(self, parent, app, data=None, on_save=None):
        super().__init__(parent)
        self.app     = app
        self.data    = data or {}
        self.on_save = on_save
        self.title("Edit Customer" if data else "Add New Customer")
        self.state("zoomed")
        self.resizable(True, True)
        self.grab_set()
        self.configure(bg=BG)
        self._entries = {}
        self._build()
        self.after(150, self._focus_first)

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=HDR_BG, padx=24, pady=16)
        hdr.pack(fill="x")
        icon = "✏  Edit Customer" if self.data else "👥  Add New Customer"
        tk.Label(hdr, text=icon, font=("Segoe UI", 14, "bold"),
                 fg="white", bg=HDR_BG).pack(side="left")
        tk.Label(hdr, text="Fill in customer details below",
                 font=("Segoe UI", 9), fg="#94a3b8", bg=HDR_BG).pack(side="left", padx=12)

        # ── Scrollable body ───────────────────────────────────────────────
        body_wrap = tk.Frame(self, bg=BG)
        body_wrap.pack(fill="both", expand=True)
        canvas = tk.Canvas(body_wrap, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(body_wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        body = tk.Frame(canvas, bg=BG, padx=24, pady=16)
        win_id = canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        from collections import defaultdict
        sections = defaultdict(list)
        for field, label, section in self.FIELDS:
            sections[section].append((field, label))

        for sec_key in ("basic", "legal"):
            fields = sections[sec_key]
            title, color = self.SECTION_META[sec_key]

            card = tk.Frame(body, bg=CARD, highlightbackground=BDR, highlightthickness=1)
            card.pack(fill="x", pady=(0, 14))

            sec_hdr = tk.Frame(card, bg=color, padx=16, pady=10)
            sec_hdr.pack(fill="x")
            tk.Label(sec_hdr, text=title, font=("Segoe UI", 10, "bold"),
                     fg="white", bg=color).pack(side="left")

            grid = tk.Frame(card, bg=CARD, padx=16, pady=14)
            grid.pack(fill="x")
            grid.columnconfigure(0, weight=1)
            grid.columnconfigure(1, weight=1)

            for idx, (field, label) in enumerate(fields):
                row, col = divmod(idx, 2)
                cell = tk.Frame(grid, bg=CARD)
                cell.grid(row=row, column=col, sticky="ew",
                          padx=(0, 16 if col == 0 else 0), pady=6)

                tk.Label(cell, text=label, font=("Segoe UI", 9, "bold"),
                         fg=MUTED, bg=CARD).pack(anchor="w", pady=(0, 3))

                var = tk.StringVar(value=str(self.data.get(field, "") or ""))

                if field in self.COMBO_FIELDS:
                    opts = self.COMBO_FIELDS[field]
                    wrap = tk.Frame(cell, bg=BDR, bd=0)
                    wrap.pack(fill="x")
                    cb = ttk.Combobox(wrap, textvariable=var, values=opts,
                                      font=("Segoe UI", 10), state="readonly")
                    cb.pack(fill="x", padx=1, pady=1, ipady=5)
                    if not self.data.get(field):
                        var.set(opts[0])
                else:
                    wrap = tk.Frame(cell, bg=BDR, bd=0)
                    wrap.pack(fill="x")
                    inner = tk.Frame(wrap, bg=CARD, bd=0)
                    inner.pack(fill="x", padx=1, pady=1)
                    e = tk.Entry(inner, textvariable=var,
                                 font=("Segoe UI", 10), bg=CARD, fg=TXT,
                                 insertbackground=TEAL, relief="flat", bd=0)
                    e.pack(fill="x", ipady=8, padx=10)
                    e.bind("<FocusIn>",  lambda ev, w=wrap: w.config(bg=TEAL))
                    e.bind("<FocusOut>", lambda ev, w=wrap: w.config(bg=BDR))

                self._entries[field] = var

        # ── Footer ────────────────────────────────────────────────────────
        foot = tk.Frame(self, bg=CARD, padx=24, pady=14,
                        highlightbackground=BDR, highlightthickness=1)
        foot.pack(fill="x", side="bottom")
        _btn(foot, "💾  Save Customer", GREEN, GREEN_H, cmd=self._save, padx=20, pady=9).pack(side="left", padx=(0, 8))
        _btn(foot, "✕  Cancel",         GRAY,  "#4b5563", cmd=self.destroy, padx=14, pady=9).pack(side="left")
        tk.Label(foot, text="* Required fields", font=("Segoe UI", 8),
                 fg=MUTED, bg=CARD).pack(side="right")

    def _focus_first(self):
        for field, _, _ in self.FIELDS:
            if field in self._entries:
                entry = self._find_entry(self)
                if entry:
                    entry.focus_set()
                    entry.icursor("end")
                    return

    def _find_entry(self, widget):
        if isinstance(widget, tk.Entry):
            return widget
        for child in widget.winfo_children():
            result = self._find_entry(child)
            if result:
                return result
        return None

    def _save(self):
        vals = {f: self._entries[f].get().strip() for f, _, _ in self.FIELDS}
        if not vals.get("customer_name"):
            messagebox.showwarning("Validation", "Customer Name is required.", parent=self)
            return
        try:
            vals["customer_credit_days"] = int(vals.get("customer_credit_days") or 0)
        except ValueError:
            vals["customer_credit_days"] = 0
        try:
            if self.data:
                sets = ", ".join(f"{k}=%s" for k in vals)
                self.app.db.execute(
                    f"UPDATE core_customermaster SET {sets} WHERE customerid=%s",
                    list(vals.values()) + [self.data["customerid"]]
                )
                messagebox.showinfo("Updated", "Customer updated successfully.", parent=self)
            else:
                cols = ", ".join(vals.keys())
                phs  = ", ".join(["%s"] * len(vals))
                self.app.db.execute(
                    f"INSERT INTO core_customermaster ({cols}) VALUES ({phs})",
                    list(vals.values())
                )
                messagebox.showinfo("Saved", "Customer added successfully.", parent=self)
            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
