"""Sales Payment Dialog — Modern light UI, calendar + typing, normal + bulk payment."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from ...styles import FONT
from ..purchase.payment_dialog import DateEntry, P, MODES, _fmt_inr


class SalesPaymentDialog(tk.Toplevel):
    def __init__(self, parent, app, invoice_no: str, on_saved=None):
        super().__init__(parent)
        self.app        = app
        self.db         = app.db
        self.invoice_no = invoice_no
        self.on_saved   = on_saved

        self.title(f"Sales Payment — {invoice_no}")
        self.state("zoomed")
        self.resizable(True, True)
        self.configure(bg=P["bg"])
        self.grab_set()
        self.bind("<Escape>",    lambda e: self.destroy())
        self.bind("<Control-s>", lambda e: self._save_single())

        self._inv_data  = {}
        self._bulk_vars = []

        self._build()
        self._load()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        hdr = tk.Frame(self, bg="#059669", height=50)   # emerald-600
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="  Sales Payment", font=FONT["h3"],
                 bg="#059669", fg="white").pack(side="left", padx=12)
        tk.Label(hdr, text="Ctrl+S = Save  |  Esc = Close",
                 font=FONT["sm"], bg="#059669", fg="#a7f3d0").pack(side="left", padx=10)
        tk.Button(hdr, text="Esc  Close", bg="#047857", fg="white",
                  font=FONT["sm"], relief="flat", bd=0, padx=12, pady=4,
                  cursor="hand2", command=self.destroy).pack(side="right", padx=8, pady=8)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=12, pady=8)

        tab1 = tk.Frame(nb, bg=P["bg"])
        tab2 = tk.Frame(nb, bg=P["bg"])
        tab3 = tk.Frame(nb, bg=P["bg"])
        nb.add(tab1, text="  Single Payment  ")
        nb.add(tab2, text="  Bulk Payment  ")
        nb.add(tab3, text="  Payment History  ")

        self._build_single(tab1)
        self._build_bulk(tab2)
        self._build_history(tab3)

    def _card(self, parent, title, accent="#059669"):
        f = tk.Frame(parent, bg=P["card"], relief="flat",
                     highlightthickness=1, highlightbackground=P["border"])
        f.pack(fill="x", padx=10, pady=(8, 4))
        tk.Frame(f, bg=accent, height=4).pack(fill="x")
        inner = tk.Frame(f, bg=P["card"], padx=16, pady=12)
        inner.pack(fill="x")
        if title:
            tk.Label(inner, text=title, font=FONT["bold"],
                     bg=P["card"], fg=accent).grid(
                row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
        return inner

    def _ent(self, p, var, w=20):
        return tk.Entry(p, textvariable=var, font=FONT["base"], width=w,
                        relief="solid", bd=1, bg=P["input_bg"], fg=P["input_fg"],
                        insertbackground=P["input_fg"],
                        highlightthickness=2,
                        highlightbackground=P["input_brd"],
                        highlightcolor="#059669")

    def _row(self, frm, r, label, widget):
        tk.Label(frm, text=label, font=FONT["sm"], bg=P["card"],
                 fg=P["lbl"]).grid(row=r, column=0, sticky="w", pady=4, padx=(0, 10))
        if isinstance(widget, tk.Widget):
            widget.grid(row=r, column=1, sticky="w", pady=4, padx=(0, 20))
        else:
            tk.Label(frm, text=str(widget), font=FONT["bold"],
                     bg=P["card"], fg=P["lbl"]).grid(row=r, column=1, sticky="w", pady=4)

    def _build_single(self, parent):
        # summary
        s = self._card(parent, "Invoice Summary", "#7c3aed")
        self._lbl_inv    = tk.Label(s, font=FONT["bold"], bg=P["card"], fg=P["lbl"])
        self._lbl_total  = tk.Label(s, font=FONT["bold"], bg=P["card"], fg=P["lbl"])
        self._lbl_paid   = tk.Label(s, font=FONT["bold"], bg=P["card"], fg=P["green"])
        self._lbl_bal    = tk.Label(s, font=FONT["bold"], bg=P["card"], fg=P["red"])
        self._lbl_status = tk.Label(s, font=FONT["bold"], bg=P["card"])
        self._row(s, 1, "Invoice #",   self._lbl_inv)
        self._row(s, 2, "Total",       self._lbl_total)
        self._row(s, 3, "Paid",        self._lbl_paid)
        self._row(s, 4, "Balance Due", self._lbl_bal)
        self._row(s, 5, "Status",      self._lbl_status)

        # payment form
        f = self._card(parent, "Record Payment", "#059669")
        self._var_date   = tk.StringVar(value=date.today().isoformat())
        self._var_amount = tk.StringVar(value="0")
        self._var_mode   = tk.StringVar(value="Cash")
        self._var_ref    = tk.StringVar()
        self._var_notes  = tk.StringVar()

        self._row(f, 1, "Payment Date *", DateEntry(f, textvariable=self._var_date, bg=P["card"]))
        self._row(f, 2, "Amount *",       self._ent(f, self._var_amount, 16))
        tk.Label(f, text="Mode *", font=FONT["sm"], bg=P["card"], fg=P["lbl"]).grid(
            row=3, column=0, sticky="w", pady=4, padx=(0, 10))
        ttk.Combobox(f, textvariable=self._var_mode, values=MODES,
                     font=FONT["base"], width=18, state="readonly").grid(
            row=3, column=1, sticky="w", pady=4)
        self._row(f, 4, "Reference No", self._ent(f, self._var_ref, 20))
        self._row(f, 5, "Notes",        self._ent(f, self._var_notes, 28))

        btn = tk.Frame(parent, bg=P["bg"])
        btn.pack(fill="x", padx=10, pady=8)
        tk.Button(btn, text="Ctrl+S   Save Payment", font=FONT["base"],
                  bg=P["green"], fg="white", relief="flat", bd=0,
                  padx=20, pady=8, cursor="hand2",
                  command=self._save_single).pack(side="right", padx=(6, 0))
        tk.Button(btn, text="Pay Full Balance", font=FONT["base"],
                  bg=P["orange"], fg="white", relief="flat", bd=0,
                  padx=14, pady=8, cursor="hand2",
                  command=self._fill_full).pack(side="right", padx=6)
        tk.Button(btn, text="Esc  Cancel", font=FONT["base"],
                  bg=P["muted"], fg="white", relief="flat", bd=0,
                  padx=14, pady=8, cursor="hand2",
                  command=self.destroy).pack(side="right")

    def _build_bulk(self, parent):
        info = tk.Frame(parent, bg=P["bg"], padx=10, pady=6)
        info.pack(fill="x")
        tk.Label(info, text="Pay multiple pending sales invoices for this customer at once.",
                 font=FONT["sm"], bg=P["bg"], fg=P["muted"]).pack(side="left")
        tk.Button(info, text="Refresh List", font=FONT["sm"],
                  bg="#059669", fg="white", relief="flat", bd=0,
                  padx=10, pady=3, cursor="hand2",
                  command=self._load_bulk).pack(side="right")

        cols_frm = tk.Frame(parent, bg="#059669")
        cols_frm.pack(fill="x", padx=10)
        for txt, w in [("", 3), ("Invoice No", 14), ("Date", 12),
                       ("Total", 10), ("Paid", 10), ("Balance", 10), ("Pay Amount", 12)]:
            tk.Label(cols_frm, text=txt if txt else "Sel", font=FONT["bold"],
                     bg="#059669", fg="white", width=w, anchor="w",
                     padx=4, pady=6).pack(side="left")

        wrap = tk.Frame(parent, bg=P["bg"])
        wrap.pack(fill="both", expand=True, padx=10, pady=4)
        canvas = tk.Canvas(wrap, bg=P["bg"], highlightthickness=0)
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self._bulk_inner = tk.Frame(canvas, bg=P["bg"])
        self._bulk_canvas = canvas
        win = canvas.create_window((0, 0), window=self._bulk_inner, anchor="nw")
        self._bulk_inner.bind("<Configure>",
                              lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        canvas.bind("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        bf = tk.Frame(parent, bg=P["card"],
                      highlightthickness=1, highlightbackground=P["border"])
        bf.pack(fill="x", padx=10, pady=4)
        bfi = tk.Frame(bf, bg=P["card"], padx=12, pady=8)
        bfi.pack(fill="x")

        tk.Label(bfi, text="Payment Date *", font=FONT["sm"],
                 bg=P["card"], fg=P["lbl"]).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self._bulk_date_var = tk.StringVar(value=date.today().isoformat())
        DateEntry(bfi, textvariable=self._bulk_date_var,
                  bg=P["card"]).grid(row=0, column=1, sticky="w", padx=(0, 16), pady=4)

        tk.Label(bfi, text="Mode *", font=FONT["sm"],
                 bg=P["card"], fg=P["lbl"]).grid(row=0, column=2, sticky="w", padx=(0, 8))
        self._bulk_mode_var = tk.StringVar(value="Cash")
        ttk.Combobox(bfi, textvariable=self._bulk_mode_var, values=MODES,
                     font=FONT["base"], width=14, state="readonly").grid(
            row=0, column=3, sticky="w", padx=(0, 16), pady=4)

        tk.Label(bfi, text="Reference", font=FONT["sm"],
                 bg=P["card"], fg=P["lbl"]).grid(row=0, column=4, sticky="w", padx=(0, 8))
        self._bulk_ref_var = tk.StringVar()
        tk.Entry(bfi, textvariable=self._bulk_ref_var, font=FONT["base"],
                 width=14, relief="solid", bd=1,
                 bg=P["input_bg"], fg=P["input_fg"]).grid(row=0, column=5, sticky="w")

        self._bulk_total_lbl = tk.StringVar(value="Total to Receive: Rs 0.00")
        tk.Label(bfi, textvariable=self._bulk_total_lbl, font=FONT["bold"],
                 bg=P["card"], fg=P["green"]).grid(
            row=1, column=0, columnspan=4, sticky="w", pady=(4, 0))
        tk.Button(bfi, text="Collect Selected Payments", font=FONT["base"],
                  bg=P["green"], fg="white", relief="flat", bd=0,
                  padx=16, pady=6, cursor="hand2",
                  command=self._save_bulk).grid(row=1, column=4, columnspan=2, sticky="e", pady=4)

    def _build_history(self, parent):
        hdr = tk.Frame(parent, bg=P["bg"], padx=10, pady=6)
        hdr.pack(fill="x")
        tk.Label(hdr, text="All receipts for this invoice",
                 font=FONT["sm"], bg=P["bg"], fg=P["muted"]).pack(side="left")
        tk.Button(hdr, text="Refresh", font=FONT["sm"],
                  bg="#059669", fg="white", relief="flat", bd=0,
                  padx=10, pady=3, cursor="hand2",
                  command=self._load_history).pack(side="right")

        cols   = ("#", "Date", "Amount", "Mode", "Reference", "Action")
        widths = (40,  110,    100,      110,    150,          80)
        frm = tk.Frame(parent, bg=P["bg"])
        frm.pack(fill="both", expand=True, padx=10, pady=4)
        vsb = ttk.Scrollbar(frm, orient="vertical")
        self._hist_tree = ttk.Treeview(frm, columns=cols, show="headings",
                                        yscrollcommand=vsb.set, selectmode="browse")
        vsb.config(command=self._hist_tree.yview)
        for col, w in zip(cols, widths):
            self._hist_tree.heading(col, text=col)
            self._hist_tree.column(col, width=w, anchor="center", minwidth=40)
        self._hist_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._hist_tree.bind("<Delete>", lambda e: self._delete_payment())

        df = tk.Frame(parent, bg=P["bg"], padx=10, pady=4)
        df.pack(fill="x")
        tk.Button(df, text="Delete Selected Receipt", font=FONT["sm"],
                  bg=P["red"], fg="white", relief="flat", bd=0,
                  padx=12, pady=5, cursor="hand2",
                  command=self._delete_payment).pack(side="right")
        tk.Label(df, text="Del = delete selected receipt",
                 font=FONT["sm"], bg=P["bg"], fg=P["muted"]).pack(side="left")

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load(self):
        self._load_invoice()
        self._load_bulk()
        self._load_history()

    def _load_invoice(self):
        try:
            inv = self.db.get_sales_invoice(self.invoice_no)
            if inv:
                self._inv_data = inv
                items   = self.db.get_sales_items(self.invoice_no)
                total   = sum(float(i.get("sale_total_amount", 0) or 0) for i in items)
                paid    = float(inv.get("sales_invoice_paid", 0) or 0)
                balance = round(total - paid, 2)
                status  = "Paid" if balance <= 0.01 else ("Partial" if paid > 0 else "Pending")
                self._lbl_inv.config(text=self.invoice_no)
                self._lbl_total.config(text=_fmt_inr(total))
                self._lbl_paid.config(text=_fmt_inr(paid))
                self._lbl_bal.config(text=_fmt_inr(balance),
                                     fg=P["green"] if balance <= 0 else P["red"])
                s_bg = P["paid_bg"] if balance <= 0.01 else P["pend_bg"]
                s_fg = P["paid_fg"] if balance <= 0.01 else P["pend_fg"]
                self._lbl_status.config(text=f"  {status}  ", bg=s_bg, fg=s_fg)
                self._var_amount.set(f"{max(0, balance):.2f}")
                self._cust_id = inv.get("customerid_id") or inv.get("customerid")
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _load_bulk(self):
        for w in self._bulk_inner.winfo_children():
            w.destroy()
        self._bulk_vars = []
        try:
            cust_id = getattr(self, "_cust_id", None)
            if not cust_id:
                inv = self.db.get_sales_invoice(self.invoice_no)
                cust_id = inv.get("customerid_id") if inv else None
            if not cust_id:
                return
            rows = self.db.query(
                "SELECT si.sales_invoice_no, si.sales_invoice_date, "
                "si.sales_invoice_paid, "
                "COALESCE((SELECT SUM(sale_total_amount) FROM core_salesmaster "
                "WHERE sales_invoice_no_id=si.sales_invoice_no),0) AS total "
                "FROM core_salesinvoicemaster si "
                "WHERE si.customerid_id=%s "
                "ORDER BY si.sales_invoice_date ASC LIMIT 100",
                (cust_id,))
            for i, r in enumerate(rows):
                total   = float(r.get("total", 0) or 0)
                paid    = float(r.get("sales_invoice_paid", 0) or 0)
                balance = round(total - paid, 2)
                if balance <= 0:
                    continue
                bg = P["row_a"] if i % 2 else P["row_b"]
                row_frm = tk.Frame(self._bulk_inner, bg=bg)
                row_frm.pack(fill="x", pady=1)

                inv_no     = r.get("sales_invoice_no", "")
                check_var  = tk.BooleanVar(value=(inv_no == self.invoice_no))
                amount_var = tk.StringVar(value=f"{balance:.2f}")

                tk.Checkbutton(row_frm, variable=check_var, bg=bg,
                               command=lambda: self._update_bulk_total()).pack(side="left", padx=4)
                for txt, w in [(inv_no, 14),
                               (str(r.get("sales_invoice_date",""))[:10], 12),
                               (_fmt_inr(total), 10),
                               (_fmt_inr(paid), 10),
                               (_fmt_inr(balance), 10)]:
                    tk.Label(row_frm, text=txt, font=FONT["sm"], bg=bg,
                             fg=P["lbl"], width=w, anchor="w", padx=4).pack(side="left")
                amt_e = tk.Entry(row_frm, textvariable=amount_var,
                                 font=FONT["sm"], width=12, relief="solid", bd=1,
                                 bg=P["input_bg"], fg=P["input_fg"])
                amt_e.pack(side="left", padx=4)
                amt_e.bind("<FocusOut>", lambda e: self._update_bulk_total())
                self._bulk_vars.append((inv_no, balance, amount_var, check_var))
            self._update_bulk_total()
            # Force canvas to update scrollregion after loading
            self._bulk_inner.update_idletasks()
            self._bulk_canvas.configure(scrollregion=self._bulk_canvas.bbox("all"))
        except Exception as e:
            tk.Label(self._bulk_inner, text=f"Error: {e}",
                     font=FONT["sm"], bg=P["bg"], fg=P["red"]).pack(padx=10, pady=6)
            self._bulk_inner.update_idletasks()
            self._bulk_canvas.configure(scrollregion=self._bulk_canvas.bbox("all"))

    def _update_bulk_total(self):
        total = 0.0
        for _, _, amt_var, chk_var in self._bulk_vars:
            if chk_var.get():
                try: total += float(amt_var.get() or 0)
                except Exception: pass
        self._bulk_total_lbl.set(f"Total to Receive: {_fmt_inr(total)}")

    def _load_history(self):
        for i in self._hist_tree.get_children():
            self._hist_tree.delete(i)
        try:
            payments = self.db.get_sales_payments(self.invoice_no)
            for idx, p in enumerate(payments, 1):
                self._hist_tree.insert("", "end",
                    iid=str(p.get("sales_payment_id", idx)),
                    values=(idx,
                            str(p.get("sales_payment_date", ""))[:10],
                            _fmt_inr(p.get("sales_payment_amount", 0)),
                            p.get("sales_payment_mode", ""),
                            p.get("sales_payment_ref_no", "") or "",
                            "Del to remove"))
        except Exception:
            pass

    # ── Actions ───────────────────────────────────────────────────────────────

    def _fill_full(self):
        try:
            inv   = self._inv_data or self.db.get_sales_invoice(self.invoice_no)
            items = self.db.get_sales_items(self.invoice_no)
            total = sum(float(i.get("sale_total_amount", 0) or 0) for i in items)
            paid  = float(inv.get("sales_invoice_paid", 0) or 0) if inv else 0
            self._var_amount.set(f"{max(0, total - paid):.2f}")
        except Exception:
            pass

    def _save_single(self):
        try:
            amount = float(self._var_amount.get() or 0)
            if amount <= 0:
                raise ValueError("Amount must be > 0.")
            pay_date = self._var_date.get().strip()
            if not pay_date:
                raise ValueError("Payment date required.")
            self.db.add_sales_payment(
                self.invoice_no, pay_date, amount,
                self._var_mode.get(), self._var_ref.get().strip())
            messagebox.showinfo("Saved", f"Payment of {_fmt_inr(amount)} recorded.", parent=self)
            self._load()
            if self.on_saved: self.on_saved()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _save_bulk(self):
        selected = [(inv_no, amt_var, chk_var)
                    for inv_no, _, amt_var, chk_var in self._bulk_vars
                    if chk_var.get()]
        if not selected:
            messagebox.showwarning("Bulk Payment", "Select at least one invoice.", parent=self)
            return
        pay_date = self._bulk_date_var.get().strip()
        mode     = self._bulk_mode_var.get()
        ref      = self._bulk_ref_var.get().strip()
        if not pay_date:
            messagebox.showwarning("Bulk Payment", "Payment date required.", parent=self)
            return
        saved = 0
        errors = []
        for inv_no, amt_var, _ in selected:
            try:
                amount = float(amt_var.get() or 0)
                if amount <= 0:
                    continue
                self.db.add_sales_payment(inv_no, pay_date, amount, mode, ref)
                saved += 1
            except Exception as e:
                errors.append(f"{inv_no}: {e}")
        msg = f"Collected from {saved} invoice(s)."
        if errors:
            msg += "\n\nErrors:\n" + "\n".join(errors)
        messagebox.showinfo("Bulk Payment", msg, parent=self)
        self._load()
        if self.on_saved: self.on_saved()

    def _delete_payment(self):
        sel = self._hist_tree.focus()
        if not sel:
            return
        if messagebox.askyesno("Delete", "Delete this receipt?", parent=self):
            try:
                self.db.delete_sales_payment(int(sel))
                self._load()
                if self.on_saved: self.on_saved()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self)
