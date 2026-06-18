import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from ...styles import COLORS, FONT, make_button, make_entry


class ProductScreen(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, bg=COLORS["bg_light"], **kwargs)
        self.app = app_instance
        self._search_var = tk.StringVar()
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=COLORS["bg_light"])
        hdr.pack(fill="x", pady=(0, 10))
        tk.Label(hdr, text="Product List", font=FONT["h2"],
                 fg=COLORS["dark_text"], bg=COLORS["bg_light"]).pack(side="left")
        tk.Label(hdr, text="  Ctrl+N=Add  Enter=Edit  Del=Delete  Ctrl+F=Search",
                 font=FONT["sm"], fg=COLORS["muted"], bg=COLORS["bg_light"]).pack(side="left", padx=8)

        bar = tk.Frame(self, bg=COLORS["bg_light"])
        bar.pack(fill="x", pady=(0, 8))
        make_button(bar, "＋ Add Product  (Ctrl+N)", "success",
                    command=self._open_add).pack(side="left", padx=(0, 4))
        make_button(bar, "📄 PDF  Ctrl+P",  "danger",  command=self._export_pdf, padx=10).pack(side="right", padx=(4, 0))
        make_button(bar, "📊 Excel  Ctrl+E", "success", command=self._export_excel, padx=10).pack(side="right", padx=4)

        sh = tk.Frame(self, bg=COLORS["bg_light"])
        sh.pack(fill="x", pady=(0, 8))
        tk.Label(sh, text="Search:", font=FONT["sm"], fg=COLORS["gray_text"],
                 bg=COLORS["bg_light"]).pack(side="left", padx=(0, 4))
        self._search_entry = make_entry(sh, textvariable=self._search_var, width=32)
        self._search_entry.pack(side="left", padx=(0, 6))
        self._search_var.trace_add("write", lambda *_: self.on_show())
        make_button(sh, "Search", "primary",   command=self.on_show, padx=10).pack(side="left", padx=(0, 4))
        make_button(sh, "Reset",  "secondary", command=self._reset,  padx=8).pack(side="left")

        cols = ("#", "Name", "Generic/Salt", "Company", "Category", "Packing", "HSN", "GST%", "Barcode", "Actions")
        widths = (40, 160, 140, 120, 100, 80, 80, 60, 100, 90)
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
            self.tree.column(col, width=w, anchor="w" if col in ("Name", "Generic/Salt", "Company") else "center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frm.grid_rowconfigure(0, weight=1)
        frm.grid_columnconfigure(0, weight=1)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Return>",    lambda e: self._open_edit(self.tree.focus()))
        self.tree.bind("<Delete>",    lambda e: self._delete(self.tree.focus()))
        self._search_entry.bind("<Return>", lambda e: self.on_show())

        hint = tk.Frame(self, bg=COLORS["white"], pady=4)
        hint.pack(fill="x")
        tk.Label(hint, text="↑↓ Navigate  |  Enter = Edit  |  Delete = Remove row  |  Ctrl+N = Add new product",
                 font=FONT["sm"], fg=COLORS["muted"], bg=COLORS["white"]).pack(side="left", padx=10)

    def _reset(self):
        self._search_var.set("")
        self.on_show()

    def on_show(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            rows = self.app.db.fetch_products(self._search_var.get())
            for idx, r in enumerate(rows, 1):
                self.tree.insert("", "end", iid=str(r.get("productid", idx)), values=(
                    idx, r.get("product_name", ""), r.get("product_salt", ""),
                    r.get("product_company", ""), r.get("product_category", ""),
                    r.get("product_packing", ""), r.get("product_hsn", ""),
                    r.get("product_hsn_percent", ""), r.get("product_barcode", ""),
                    "✏ 🗑"
                ))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_double_click(self, event):
        item = self.tree.focus()
        if not item:
            return
        col = self.tree.identify_column(event.x)
        if col == "#10":  # Actions column
            vals = self.tree.item(item, "values")
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="✏ Edit", command=lambda: self._open_edit(item))
            menu.add_command(label="🗑 Delete", command=lambda: self._delete(item))
            menu.post(event.x_root, event.y_root)
        else:
            self._open_edit(item)

    def _open_add(self):
        ProductForm(self, self.app, on_save=self.on_show)

    def _open_edit(self, item_id):
        try:
            rows = self.app.db.query(
                "SELECT * FROM core_productmaster WHERE productid=%s", (item_id,))
            if rows:
                ProductForm(self, self.app, data=rows[0], on_save=self.on_show)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete(self, item_id):
        vals = self.tree.item(item_id, "values")
        name = vals[1] if vals else ""
        if messagebox.askyesno("Confirm Delete", f"Delete product '{name}'?"):
            try:
                self.app.db.execute(
                    "DELETE FROM core_productmaster WHERE productid=%s", (item_id,))
                self.on_show()
                messagebox.showinfo("Success", f"Product '{name}' deleted.")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot delete: {e}")

    def kb_new(self):
        self._open_add()

    def kb_search(self):
        self._search_entry.focus_set()

    def kb_refresh(self):
        self.on_show()

    def kb_export_excel(self): self._export_excel()
    def kb_export_pdf(self):   self._export_pdf()

    def _export_excel(self):
        try:
            from ..invoice_export import export_report_excel
            from tkinter import filedialog
            from pathlib import Path
            import tempfile
            import shutil
            import os
            
            headers = ["#", "Name", "Generic/Salt", "Company", "Category", "Packing", "HSN", "GST%", "Barcode"]
            data = []
            for item in self.tree.get_children():
                vals = list(self.tree.item(item, "values"))
                if vals:
                    data.append(vals[:-1])
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx")],
                initialfile="Product_List.xlsx",
                title="Save Product List Excel",
                parent=self
            )
            if filename:
                temp_dir = Path(tempfile.gettempdir())
                temp_file = temp_dir / "temp_products.xlsx"
                export_report_excel("Product List", headers, data, [""] * len(headers), temp_file)
                shutil.move(str(temp_file), filename)
                if messagebox.askyesno("Export Complete", "Excel file saved successfully!\n\nOpen file now?", parent=self):
                    os.startfile(filename)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export Excel: {e}", parent=self)

    def _export_pdf(self):
        try:
            from ..invoice_export import export_report_pdf
            from tkinter import filedialog
            from pathlib import Path
            import tempfile
            import shutil
            import os
            
            headers = ["#", "Name", "Generic/Salt", "Company", "Category", "Packing", "HSN", "GST%", "Barcode"]
            data = []
            for item in self.tree.get_children():
                vals = list(self.tree.item(item, "values"))
                if vals:
                    data.append(vals[:-1])
                    
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf")],
                initialfile="Product_List.pdf",
                title="Save Product List PDF",
                parent=self
            )
            if filename:
                temp_dir = Path(tempfile.gettempdir())
                temp_file = temp_dir / "temp_products.pdf"
                summary = {"Total Products": str(len(data))}
                export_report_pdf("Product List", headers, data, [""] * len(headers), summary, temp_file)
                shutil.move(str(temp_file), filename)
                if messagebox.askyesno("Export Complete", "PDF file saved successfully!\n\nOpen file now?", parent=self):
                    os.startfile(filename)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF: {e}", parent=self)


class ProductForm(tk.Toplevel):
    FIELDS = [
        ("product_name", "Product Name *"),
        ("product_company", "Company *"),
        ("product_packing", "Packing *"),
        ("product_salt", "Generic/Salt Name"),
        ("product_category", "Category"),
        ("product_hsn", "HSN Code"),
        ("product_hsn_percent", "GST %"),
        ("product_barcode", "Barcode"),
    ]

    def __init__(self, parent, app, data=None, on_save=None):
        super().__init__(parent)
        self.app = app
        self.data = data or {}
        self.on_save = on_save
        self.title("Edit Product" if data else "Add Product")
        self.state("zoomed")
        self.resizable(True, True)
        self.grab_set()
        self._entries = {}
        self._build()

    def _build(self):
        self.configure(bg=COLORS["bg_light"])
        
        canvas = tk.Canvas(self, highlightthickness=0, bg=COLORS["bg_light"])
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        frm = tk.Frame(canvas, padx=24, pady=20, bg=COLORS["bg_light"])
        canvas.create_window((0, 0), window=frm, anchor="nw")
        frm.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        for i, (field, label) in enumerate(self.FIELDS):
            tk.Label(frm, text=label, font=FONT["bold"], fg=COLORS["dark_text"], bg=COLORS["bg_light"]).grid(
                row=i, column=0, sticky="w", pady=6)
            var = tk.StringVar(value=str(self.data.get(field, "")))
            e = make_entry(frm, textvariable=var, width=32)
            e.grid(row=i, column=1, sticky="w", padx=(16, 0), pady=6)
            self._entries[field] = var

        btn_row = tk.Frame(frm, bg=COLORS["bg_light"])
        btn_row.grid(row=len(self.FIELDS), column=0, columnspan=2, pady=20, sticky="w")
        
        make_button(btn_row, "💾 Save", "success", command=self._save).pack(side="left", padx=(0, 8))
        make_button(btn_row, "Cancel", "secondary", command=self.destroy).pack(side="left")

    def _save(self):
        vals = {f: v.get().strip() for f, v in self._entries.items()}
        if not vals["product_name"] or not vals["product_company"] or not vals["product_packing"]:
            messagebox.showwarning("Validation", "Name, Company and Packing are required.", parent=self)
            return
        try:
            if self.data:
                sets = ", ".join(f"{k}=%s" for k in vals)
                self.app.db.execute(
                    f"UPDATE core_productmaster SET {sets} WHERE productid=%s",
                    list(vals.values()) + [self.data["productid"]]
                )
                messagebox.showinfo("Success", "Product updated.", parent=self)
            else:
                cols = ", ".join(vals.keys())
                phs = ", ".join(["%s"] * len(vals))
                self.app.db.execute(
                    f"INSERT INTO core_productmaster ({cols}) VALUES ({phs})",
                    list(vals.values())
                )
                messagebox.showinfo("Success", "Product added.", parent=self)
            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
