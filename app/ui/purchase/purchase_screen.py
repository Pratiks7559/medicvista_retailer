import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date

from ...styles import COLORS, FONT
from ...modern_ui_components import ModernButton, ModernEntry, ModernFrame, ModernLabel
from ...ui.invoice_export import export_purchase_invoice_excel, export_purchase_invoice_pdf
from .purchase_invoice_dialog import PurchaseInvoiceDialog


class PurchaseScreen(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=COLORS["bg_light"], **kwargs)
        self.app = app_instance
        self._var_from  = tk.StringVar()
        self._var_to    = tk.StringVar()
        self._var_search = tk.StringVar()
        self._rows: list[dict] = []
        self._build()
        self._bind_keys()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        header = tk.Frame(self, bg=COLORS["bg_light"])
        header.pack(fill="x", pady=(0, 12))
        ModernLabel(header, "Purchase Invoices", variant="h1", bg=COLORS["bg_light"]).pack(side="left")
        ModernLabel(header,
                    "Manage purchase bills, supplier payments, and invoice history.",
                    variant="subtitle", bg=COLORS["bg_light"]).pack(side="left", padx=(12, 0), pady=(8, 0))

        action_card = ModernFrame(self, title="Actions")
        action_card.pack(fill="x", pady=(0, 12))
        action_bar = tk.Frame(action_card.content, bg=COLORS["white"])
        action_bar.pack(fill="x")
        ModernButton(action_bar, "＋ New  (Ctrl+N)", variant="success",
                     command=self._open_new_invoice).pack(side="left", padx=(0, 6))
        ModernButton(action_bar, "⚡ Bulk Entry", variant="purple",
                     command=self._open_bulk_entry).pack(side="left", padx=6)
        ModernButton(action_bar, "💳 Payment  (Ctrl+W)", variant="info",
                     command=self._add_payment).pack(side="left", padx=6)
        ModernButton(action_bar, "📊 Excel  (Ctrl+E)", variant="warning",
                     command=self._export_excel).pack(side="right", padx=(6, 0))
        ModernButton(action_bar, "📄 PDF  (Ctrl+P)", variant="danger",
                     command=self._export_pdf).pack(side="right", padx=6)

        filter_card = ModernFrame(self, title="Filters")
        filter_card.pack(fill="x", pady=(0, 12))
        fr = tk.Frame(filter_card.content, bg=COLORS["white"])
        fr.pack(fill="x")

        self._var_from.set(date.today().replace(day=1).isoformat())
        self._var_to.set(date.today().isoformat())

        from ...ui.purchase.purchase_invoice_dialog import DateEntry as _DE
        ModernLabel(fr, "From:", variant="subtitle", bg=COLORS["white"]).pack(side="left", padx=(0, 4))
        self._e_from = _DE(fr, textvariable=self._var_from, width=13, bg=COLORS["white"])
        self._e_from.pack(side="left", padx=(0, 10))

        ModernLabel(fr, "To:", variant="subtitle", bg=COLORS["white"]).pack(side="left", padx=(0, 4))
        self._e_to = _DE(fr, textvariable=self._var_to, width=13, bg=COLORS["white"])
        self._e_to.pack(side="left", padx=(0, 10))

        ModernLabel(fr, "Search:", variant="subtitle", bg=COLORS["white"]).pack(side="left", padx=(0, 6))
        self._e_search = ModernEntry(fr, textvariable=self._var_search, width=24)
        self._e_search.pack(side="left", padx=(0, 10))
        self._var_search.trace_add("write", lambda *_: self._fill_tree())

        ModernButton(fr, "🔍 Filter  (F5)", variant="primary",
                     command=self.on_show, padx=12).pack(side="left", padx=(0, 6))
        ModernButton(fr, "Reset", variant="secondary",
                     command=self._reset_filter, padx=10).pack(side="left")

        tree_card = ModernFrame(self, title="Purchase Records")
        tree_card.pack(fill="both", expand=True)
        frm = tk.Frame(tree_card.content, bg=COLORS["white"])
        frm.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(frm, orient="vertical")
        hsb = ttk.Scrollbar(frm, orient="horizontal")
        self.tree = ttk.Treeview(frm, columns=("#", "Invoice No", "Date", "Supplier", "Items",
                                               "Total", "Paid", "Balance", "Status", "Actions"),
                                  show="headings", yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                  selectmode="browse")
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        for col, w in zip(("#", "Invoice No", "Date", "Supplier", "Items",
                           "Total", "Paid", "Balance", "Status", "Actions"),
                          (40, 120, 100, 180, 55, 90, 80, 90, 80, 80)):
            self.tree.heading(col, text=col)
            anchor = "w" if col in ("Invoice No", "Supplier") else "center"
            self.tree.column(col, width=w, anchor=anchor, minwidth=40)
        self.tree.tag_configure("paid",    foreground=COLORS["green"])
        self.tree.tag_configure("partial", foreground=COLORS["orange"])
        self.tree.tag_configure("pending", foreground=COLORS["gray_text"])
        self.tree.tag_configure("overdue", foreground=COLORS["red"])
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frm.grid_rowconfigure(0, weight=1)
        frm.grid_columnconfigure(0, weight=1)

        hint = tk.Frame(self, bg=COLORS["white2"], pady=8)
        hint.pack(fill="x", pady=(12, 0))
        ModernLabel(hint,
                    "↑↓ Navigate  |  Enter = Edit  |  Delete = Remove  |  Ctrl+W = Add Payment  |  Ctrl+N = New Invoice",
                    variant="caption", bg=COLORS["white2"]).pack(side="left", padx=12)
        self._status_var = tk.StringVar(value="Ready")
        ModernLabel(hint, textvariable=self._status_var, variant="caption",
                    bg=COLORS["white2"], fg=COLORS["purple"]).pack(side="right", padx=12)

    # ── Keyboard bindings ─────────────────────────────────────────────────────

    def _bind_keys(self):
        self.tree.bind("<Return>",          lambda e: self._edit_selected())
        self.tree.bind("<Delete>",          lambda e: self._delete_selected())
        self.tree.bind("<<TreeviewOpen>>",  lambda e: self._edit_selected())
        self.tree.bind("<<TreeviewDelete>>",lambda e: self._delete_selected())
        self.tree.bind("<space>",           lambda e: self._action_menu())
        self._e_search.bind("<Return>",     lambda e: self.on_show())
        self._e_from.bind("<Return>",       lambda e: self._e_to.focus_set())
        self._e_to.bind("<Return>",         lambda e: self.on_show())

    # keyboard action hooks (called by shortcuts dispatcher)
    def kb_new(self):     self._open_new_invoice()
    def kb_save(self):    pass
    def kb_delete(self):  self._delete_selected()
    def kb_search(self):  self._e_search.focus_set()
    def kb_refresh(self): self.on_show()
    def kb_export_excel(self): self._export_excel()
    def kb_export_pdf(self):   self._export_pdf()
    def kb_add_payment(self):  self._add_payment()

    # ── Data ──────────────────────────────────────────────────────────────────

    def on_show(self):
        """Load purchase invoices - OPTIMIZED."""
        # Clear tree
        self._rows = []
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        # Show loading
        self._status_var.set("Loading...")
        self.update_idletasks()
        
        try:
            # Get FY dates
            fy_start = getattr(self.app, 'current_fy_start', None)
            fy_end = getattr(self.app, 'current_fy_end', None)
            
            # Update filter bar
            if fy_start and fy_end:
                self._var_from.set(fy_start)
                self._var_to.set(fy_end)
            
            # Single DB query
            rows = self.app.db.fetch_purchases(
                self._var_search.get(), 
                fy_start or self._var_from.get(), 
                fy_end or self._var_to.get()
            )
            
            # Filter in memory (faster than multiple DB queries)
            frm_date = self._var_from.get().strip()
            to_date = self._var_to.get().strip()
            
            self._rows = [
                r for r in rows
                if (not frm_date or str(r.get("invoice_date", "")) >= frm_date)
                and (not to_date or str(r.get("invoice_date", "")) <= to_date)
            ]
            
            self._fill_tree()
            
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
            self._status_var.set("Error")

    def _fill_tree(self):
        term = self._var_search.get().lower()
        for i in self.tree.get_children():
            self.tree.delete(i)
        shown = 0
        first_item = None
        for idx, r in enumerate(self._rows, 1):
            if term and term not in str(r.get("invoice_no", "")).lower() \
                    and term not in str(r.get("supplier_name", "")).lower():
                continue
            total   = float(r.get("invoice_total", 0) or 0)
            paid    = float(r.get("invoice_paid",  0) or 0)
            balance = total - paid
            status  = (r.get("payment_status") or "pending").lower()
            item_id = str(r.get("invoiceid", idx))
            self.tree.insert("", "end", iid=item_id,
                             tags=(status,), values=(
                idx, r.get("invoice_no", ""), r.get("invoice_date", ""),
                r.get("supplier_name", ""), r.get("item_count", ""),
                f"₹{total:.2f}", f"₹{paid:.2f}", f"₹{balance:.2f}",
                status.capitalize(), "Enter=Edit  Del=Delete"
            ))
            if first_item is None:
                first_item = item_id
            shown += 1
        self._status_var.set(f"{shown} record(s)")
        
        # Focus on first item and scroll to top
        if first_item:
            self.tree.selection_set(first_item)
            self.tree.focus(first_item)
            self.tree.see(first_item)
            self.tree.yview_moveto(0)

    def _reset_filter(self):
        self._var_from.set(date.today().replace(day=1).isoformat())
        self._var_to.set(date.today().isoformat())
        self._var_search.set("")
        self.on_show()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _open_new_invoice(self):
        PurchaseInvoiceDialog(self, self.app, on_saved=self.on_show)

    def _open_bulk_entry(self):
        """Open bulk purchase entry — shows count dialog then opens N invoices."""
        from tkinter import simpledialog
        count = simpledialog.askinteger(
            "Bulk Purchase Entry",
            "How many purchase invoices do you want to create?",
            minvalue=1, maxvalue=50, initialvalue=5, parent=self
        )
        if not count:
            return
        self._bulk_remaining = count
        self._bulk_created   = 0
        self._open_next_bulk()

    def _open_next_bulk(self):
        if self._bulk_remaining <= 0:
            if self._bulk_created > 0:
                messagebox.showinfo(
                    "Bulk Entry Complete",
                    f"{self._bulk_created} purchase invoice(s) created.",
                    parent=self
                )
            self.on_show()
            return

        self._bulk_remaining -= 1

        def on_saved_bulk():
            self._bulk_created += 1
            self._open_next_bulk()

        def on_cancelled():
            # user closed without saving — stop bulk
            self._bulk_remaining = 0
            if self._bulk_created > 0:
                messagebox.showinfo(
                    "Bulk Entry Stopped",
                    f"{self._bulk_created} invoice(s) saved before stopping.",
                    parent=self
                )
            self.on_show()

        dlg = PurchaseInvoiceDialog(
            self, self.app,
            on_saved=on_saved_bulk
        )
        # detect close without saving
        dlg.protocol("WM_DELETE_WINDOW", lambda: (dlg.destroy(), on_cancelled()))

    def _get_selected(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showinfo("Select", "Use ↑↓ to select a row first.")
            return None, None
        vals = self.tree.item(sel, "values")
        return sel, vals

    def _edit_selected(self):
        """Edit selected invoice - OPTIMIZED."""
        sel, vals = self._get_selected()
        if not vals:
            return
        
        self._status_var.set("Loading invoice...")
        self.update_idletasks()
        
        try:
            invoice_id = int(sel)
            inv = self.app.db.get_invoice(invoice_id)
            if inv:
                PurchaseInvoiceDialog(self, self.app, invoice_data=inv, on_saved=self.on_show)
            else:
                messagebox.showerror("Error", "Invoice not found.", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load invoice: {str(e)}", parent=self)
        finally:
            self._status_var.set("Ready")

    def _delete_selected(self):
        sel, vals = self._get_selected()
        if not vals:
            return
        inv_no = vals[1]
        if messagebox.askyesno("Confirm Delete",
                               f"Delete invoice '{inv_no}'?\nThis cannot be undone."):
            try:
                self.app.db.delete_invoice(int(sel))
                self.on_show()
                messagebox.showinfo("Deleted", f"Invoice {inv_no} deleted.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _add_payment(self):
        sel, vals = self._get_selected()
        if not vals:
            return
        from ...ui.purchase.payment_dialog import PurchasePaymentDialog
        PurchasePaymentDialog(self, self.app, invoice_id=int(sel),
                              invoice_no=vals[1], on_saved=self.on_show)

    def _action_menu(self):
        sel = self.tree.focus()
        if not sel:
            return
        menu = tk.Menu(self, tearoff=0, bg=COLORS["white"],
                       fg=COLORS["dark_text"], font=FONT["base"],
                       activebackground=COLORS["purple"], activeforeground="white")
        menu.add_command(label="✏  Edit Invoice    (Enter)", command=self._edit_selected)
        menu.add_command(label="💳  Add Payment    (Ctrl+W)", command=self._add_payment)
        menu.add_command(label="📊  Export Excel   (Ctrl+E)", command=self._export_excel)
        menu.add_command(label="📄  Export PDF     (Ctrl+P)", command=self._export_pdf)
        menu.add_separator()
        menu.add_command(label="🗑  Delete Invoice  (Del)", command=self._delete_selected)
        # position near tree
        try:
            x = self.tree.winfo_rootx() + 80
            y = self.tree.winfo_rooty() + 80
            menu.post(x, y)
            menu.focus_set()
        finally:
            menu.grab_release()

    def _get_selected_invoice_no(self):
        sel, vals = self._get_selected()
        return vals[1] if vals else None

    def _export_excel(self):
        try:
            from ..invoice_export import export_report_excel
            from pathlib import Path
            import os

            headers = ["#", "Invoice No", "Date", "Supplier", "Items",
                       "Total", "Paid", "Balance", "Status"]
            data = []
            for item in self.tree.get_children():
                vals = list(self.tree.item(item, "values"))
                if vals:
                    data.append(vals[:len(headers)])

            if not data:
                messagebox.showwarning("No Data", "No invoices to export.", parent=self)
                return

            docs_dir = Path.home() / "Documents" / "MedicVista_Exports"
            docs_dir.mkdir(parents=True, exist_ok=True)
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx")],
                initialfile=f"Purchase_Invoices_{date.today().isoformat()}.xlsx",
                initialdir=str(docs_dir),
                title="Save Purchase Invoices Excel",
                parent=self
            )
            if filename:
                totals = ["", "", "", "", "",
                          sum(float(str(r[5]).replace("₹","").replace(",","").strip() or 0) for r in data),
                          sum(float(str(r[6]).replace("₹","").replace(",","").strip() or 0) for r in data),
                          sum(float(str(r[7]).replace("₹","").replace(",","").strip() or 0) for r in data),
                          ""]
                export_report_excel("Purchase Invoices", headers, data, totals, Path(filename))
                if messagebox.askyesno("Export Complete",
                                       f"Saved to:\n{filename}\n\nOpen file now?", parent=self):
                    os.startfile(filename)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export Excel: {e}", parent=self)

    def _export_pdf(self):
        try:
            from ..invoice_export import export_report_pdf
            from pathlib import Path
            import os

            headers = ["#", "Invoice No", "Date", "Supplier", "Items",
                       "Total", "Paid", "Balance", "Status"]
            data = []
            for item in self.tree.get_children():
                vals = list(self.tree.item(item, "values"))
                if vals:
                    data.append(vals[:len(headers)])

            if not data:
                messagebox.showwarning("No Data", "No invoices to export.", parent=self)
                return

            docs_dir = Path.home() / "Documents" / "MedicVista_Exports"
            docs_dir.mkdir(parents=True, exist_ok=True)
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf")],
                initialfile=f"Purchase_Invoices_{date.today().isoformat()}.pdf",
                initialdir=str(docs_dir),
                title="Save Purchase Invoices PDF",
                parent=self
            )
            if filename:
                totals = ["", "", "", "", "",
                          sum(float(str(r[5]).replace("₹","").replace(",","").strip() or 0) for r in data),
                          sum(float(str(r[6]).replace("₹","").replace(",","").strip() or 0) for r in data),
                          sum(float(str(r[7]).replace("₹","").replace(",","").strip() or 0) for r in data),
                          ""]
                summary = {"Total Invoices": str(len(data)),
                           "Period": f"{self._var_from.get()} to {self._var_to.get()}"}
                export_report_pdf("Purchase Invoices", headers, data, totals, summary, Path(filename))
                if messagebox.askyesno("Export Complete",
                                       f"Saved to:\n{filename}\n\nOpen file now?", parent=self):
                    os.startfile(filename)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF: {e}", parent=self)
