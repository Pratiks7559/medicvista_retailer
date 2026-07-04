"""Thermal Receipt Print Dialog — matches pharmacy invoice HTML template."""
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import os
import tempfile


class ReceiptPrintDialog(tk.Toplevel):
    def __init__(self, parent, app, invoice_data):
        super().__init__(parent)
        self.app          = app
        self.invoice_data = invoice_data

        self.title("Receipt Preview")
        self.geometry("420x560")
        self.configure(bg="white")
        self.resizable(False, False)
        self.grab_set()

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>",   lambda e: self._on_close())
        self.bind("<Control-p>", lambda e: self._print_receipt())

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build(self):
        # Button bar
        btn_frame = tk.Frame(self, bg="#f1f5f9", pady=8)
        btn_frame.pack(fill="x")

        tk.Button(btn_frame, text="🖨️  Print (Ctrl+P)",
                  bg="#10b981", fg="white", font=("Arial", 10, "bold"),
                  bd=0, padx=20, pady=8, cursor="hand2",
                  command=self._print_receipt).pack(side="left", padx=10)

        tk.Button(btn_frame, text="✖  Close (Esc)",
                  bg="#6b7280", fg="white", font=("Arial", 10, "bold"),
                  bd=0, padx=20, pady=8, cursor="hand2",
                  command=self._on_close).pack(side="left", padx=5)

        # Scrollable preview
        canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        vsb    = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        inner = tk.Frame(canvas, bg="white", padx=12, pady=12)
        win   = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win, width=canvas.winfo_width())
        inner.bind("<Configure>", _resize)

        self._build_preview(inner)

    def _build_preview(self, parent):
        inv           = self.invoice_data
        inv_no        = inv.get("sales_invoice_no", "N/A")
        inv_date      = self._fmt_date(str(inv.get("sales_invoice_date", "")))
        inv_time      = datetime.now().strftime("%H:%M")
        customer_name = inv.get("customer_name", "Walk-in Customer")
        items         = inv.get("items", [])
        transport     = float(inv.get("sales_transport_charges", 0) or 0)

        store_name = "MEDICVISTA PHARMA PVT. LTD."
        cfg = getattr(self.app, "config_data", None)
        if cfg and getattr(cfg, "store_name", None):
            store_name = cfg.store_name

        FH  = ("Courier New", 11, "bold")
        FN  = ("Courier New",  9)
        FS  = ("Courier New",  8)
        FSB = ("Courier New",  8, "bold")

        def sep():
            tk.Frame(parent, bg="#aaa", height=1).pack(fill="x", pady=3)

        def lbl(text, font=FN, anchor="center", fg="black"):
            tk.Label(parent, text=text, font=font, bg="white",
                     fg=fg, anchor=anchor, justify="left").pack(fill="x")

        # ── Store header ──
        lbl(store_name, FH)
        lbl("MIDC Nagar, Bhusawal, District Jalgaon (MH-271)", FS)
        lbl("Drug Lic: DL-MH-JLG-20B-1234, DL-MH-JLG-21B-5678", FS)
        lbl("GST: 27ABCDE1234F1Z5   Ph: +91-9876543210", FS)
        lbl("Email: info@medicvista.com", FS)
        sep()

        # ── Invoice info ──
        lbl("GST INV (CASH)", FSB)
        lbl(f"Invoice No: {inv_no}", FN, "w")
        lbl(f"Date: {inv_date}   Time: {inv_time}", FN, "w")
        sep()

        # ── Patient info ──
        lbl(f"Patient : {customer_name}", FN, "w")
        lbl(f"Doctor  : {'_________________'}", FN, "w")
        lbl(f"Address : {'_________________'}", FN, "w")
        sep()

        # ── Items table header ──
        HDR = f"{'Qty':<4} {'Item':<22} {'Batch':<8} {'Exp':<6} {'Amt':>7} {'Tax':>4}"
        lbl(HDR, FS, "w")
        tk.Frame(parent, bg="#555", height=1).pack(fill="x")

        subtotal   = 0.0
        total_cgst = 0.0
        total_sgst = 0.0

        for item in items:
            qty      = int(float(item.get("sale_quantity", 0) or item.get("quantity", 1)))
            name     = str(item.get("product_name", ""))[:22]
            batch    = str(item.get("product_batch_no", "") or item.get("batch_no", ""))[:8]
            expiry   = str(item.get("product_expiry",  "") or item.get("expiry",   ""))[:6]
            mrp      = float(item.get("product_MRP", 0) or item.get("mrp", 0))
            cgst_pct = float(item.get("sale_cgst", 0)  or item.get("cgst", 0))
            sgst_pct = float(item.get("sale_sgst", 0)  or item.get("sgst", 0))
            disc     = float(item.get("sale_discount", 0) or item.get("discount", 0))

            line_sub  = (mrp * qty) - disc
            cgst_amt  = (line_sub * cgst_pct) / 100
            sgst_amt  = (line_sub * sgst_pct) / 100
            line_tot  = line_sub + cgst_amt + sgst_amt

            subtotal   += line_sub
            total_cgst += cgst_amt
            total_sgst += sgst_amt

            tax_pct = cgst_pct + sgst_pct
            row = f"{qty:<4} {name:<22} {batch:<8} {expiry:<6} {line_tot:>7.2f} {tax_pct:>3.0f}%"
            lbl(row, FS, "w")

        tk.Frame(parent, bg="#555", height=1).pack(fill="x")

        # ── Totals ──
        total_gst              = total_cgst + total_sgst
        grand_before_round     = subtotal + total_gst + transport
        grand_total            = round(grand_before_round)
        round_off              = grand_total - grand_before_round

        def right_row(label, value, bold=False):
            f = FSB if bold else FS
            tk.Label(parent, text=f"{label:<28}{value:>10}",
                     font=f, bg="white", anchor="w").pack(fill="x")

        right_row("CGST:",  f"{total_cgst:.2f}")
        right_row("SGST:",  f"{total_sgst:.2f}")
        right_row("Total GST:", f"{total_gst:.2f}")
        if transport > 0:
            right_row("Transport:", f"{transport:.2f}")
        if abs(round_off) > 0.001:
            right_row("Round Off:", f"{round_off:.2f}")

        sep()
        right_row(f"TOTAL:", f"Rs.{grand_total:.2f}", bold=True)
        sep()

        lbl(f"For {store_name}", FS)
        lbl("Consult doctor before use", FSB, fg="#cc0000")
        lbl("Subject to Bhusawal Jurisdiction", FS)
        lbl("Thank you for your visit!", FS)

    # ── Print ─────────────────────────────────────────────────────────────────
    def _print_receipt(self):
        try:
            html = self.generate_receipt_html(self.app, self.invoice_data)
            tmp  = tempfile.NamedTemporaryFile(mode="w", delete=False,
                                               suffix=".html", encoding="utf-8")
            tmp.write(html)
            tmp.close()
            if hasattr(os, "startfile"):
                os.startfile(tmp.name)
            else:
                import webbrowser
                webbrowser.open(f"file://{tmp.name}")
            messagebox.showinfo("Print",
                                "Receipt opened in browser.\nUse Ctrl+P to print.",
                                parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate receipt: {e}", parent=self)

    def _on_close(self):
        self.destroy()

    # ── HTML generator (static — also called from sales_invoice_dialog) ───────
    @staticmethod
    def generate_receipt_html(app, invoice_data):
        inv           = invoice_data
        inv_no        = inv.get("sales_invoice_no", "N/A")
        inv_date_raw  = str(inv.get("sales_invoice_date", ""))
        inv_time      = datetime.now().strftime("%H:%M")
        customer_name = inv.get("customer_name", "Walk-in Customer")
        items         = inv.get("items", [])
        transport     = float(inv.get("sales_transport_charges", 0) or 0)

        # Format date DD/MM/YY
        inv_date = inv_date_raw
        if len(inv_date_raw) == 10 and "-" in inv_date_raw:
            try:
                d = datetime.strptime(inv_date_raw, "%Y-%m-%d")
                inv_date = d.strftime("%d/%m/%y")
            except Exception:
                pass

        store_name = "MEDICVISTA PHARMA PVT. LTD."
        cfg = getattr(app, "config_data", None)
        if cfg and getattr(cfg, "store_name", None):
            store_name = cfg.store_name

        # Build item rows + totals
        subtotal   = 0.0
        total_cgst = 0.0
        total_sgst = 0.0
        rows_html  = ""

        for item in items:
            qty      = int(float(item.get("sale_quantity", 0) or item.get("quantity", 1)))
            name     = str(item.get("product_name", "Product"))
            packing  = str(item.get("product_packing", ""))
            mfr      = str(item.get("product_company", ""))
            batch    = str(item.get("product_batch_no", "") or item.get("batch_no", ""))
            expiry   = str(item.get("product_expiry",  "") or item.get("expiry",   ""))
            mrp      = float(item.get("product_MRP", 0) or item.get("mrp", 0))
            cgst_pct = float(item.get("sale_cgst", 0)  or item.get("cgst", 0))
            sgst_pct = float(item.get("sale_sgst", 0)  or item.get("sgst", 0))
            disc     = float(item.get("sale_discount", 0) or item.get("discount", 0))
            hsn      = str(item.get("product_hsn", "3004"))

            line_sub  = (mrp * qty) - disc
            cgst_amt  = (line_sub * cgst_pct) / 100
            sgst_amt  = (line_sub * sgst_pct) / 100
            line_tot  = line_sub + cgst_amt + sgst_amt
            tax_pct   = cgst_pct + sgst_pct

            subtotal   += line_sub
            total_cgst += cgst_amt
            total_sgst += sgst_amt

            rows_html += f"""<tr>
  <td>{qty}</td>
  <td>{name}</td>
  <td>{packing}</td>
  <td>{mfr}</td>
  <td>{batch}</td>
  <td>{expiry}</td>
  <td class="right">{mrp:.2f}</td>
  <td>{hsn}</td>
  <td class="right">{tax_pct:.0f}%</td>
  <td class="right"><b>{line_tot:.2f}</b></td>
</tr>
"""

        total_gst          = total_cgst + total_sgst
        grand_before_round = subtotal + total_gst + transport
        grand_total        = round(grand_before_round)
        round_off          = grand_total - grand_before_round

        transport_row = (f'<tr><td>Transport:</td>'
                         f'<td class="right">{transport:.2f}</td></tr>'
                         if transport > 0 else "")
        round_row     = (f'<tr><td>Round Off:</td>'
                         f'<td class="right">{round_off:.2f}</td></tr>'
                         if abs(round_off) > 0.001 else "")

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Receipt - {inv_no}</title>
<style>
body {{
  font-family: Arial, sans-serif;
  margin: 10px;
}}
.form-section {{ display: none; }}
.invoice {{
  font-family: monospace;
  width: 380px;
  font-size: 11px;
  line-height: 1.2;
  border: 1px solid #ddd;
  padding: 10px;
  background: white;
}}
.center {{ text-align: center; }}
.line {{ border-bottom: 1px dashed black; margin: 4px 0; }}
table {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
td, th {{ padding: 1px 2px; text-align: left; }}
.right {{ text-align: right; }}
.bold {{ font-weight: bold; }}
@media print {{
  body {{ margin: 0; }}
  .invoice {{
    display: block !important;
    border: none;
    margin: 0;
    padding: 0;
    width: 100%;
  }}
}}
</style>
</head>
<body>
<div class="invoice">

<div>
  <div class="bold" style="font-size:14px;">{store_name}</div>
  MIDC Nagar, Bhusawal, District Jalgaon (MH-271)<br>
  Drug License No: DL-MH-JLG-20B-1234, DL-MH-JLG-21B-5678<br>
  GST No: 27ABCDE1234F1Z5&nbsp;&nbsp;&nbsp;&nbsp;Phone: +91-9876543210<br>
  Email: info@medicvista.com
</div>

<div class="line"></div>

<div>
  <strong>GST INV (CASH)</strong><br>
  Invoice No: {inv_no}<br>
  Date: {inv_date}&nbsp;&nbsp;Time: {inv_time}
</div>

<div class="line"></div>

<div style="display:flex; justify-content:space-between;">
  <div style="width:70%;">
    Patient Name: {customer_name}<br>
    Doctor Name: _________________<br>
    Address: _________________<br>
    Consultant: Dr. Name
  </div>
  <div style="width:28%; text-align:right;">
    Medi Quest
  </div>
</div>

<div class="line"></div>

<table style="font-size:9px;">
<tr>
  <th>Qty</th>
  <th>Item Name</th>
  <th>Pack</th>
  <th>Mfr</th>
  <th>Batch</th>
  <th>Exp</th>
  <th class="right">MRP</th>
  <th>HSN</th>
  <th class="right">Tax%</th>
  <th class="right">Amt</th>
</tr>
{rows_html}
</table>

<div class="line"></div>

<table>
<tr><td>CGST</td><td class="right">{total_cgst:.2f}</td></tr>
<tr><td>SGST</td><td class="right">{total_sgst:.2f}</td></tr>
<tr><td><strong>Total GST</strong></td><td class="right"><strong>{total_gst:.2f}</strong></td></tr>
{transport_row}
{round_row}
</table>

<div class="line"></div>

<div class="center bold" style="font-size:14px;">
  TOTAL: &#8377;{grand_total:.2f}
</div>

<div class="line"></div>

<div class="center">For {store_name}</div>

<div>
  <strong>Consult doctor before use</strong><br>
  Subject to Bhusawal Jurisdiction<br>
  Thank you for your visit!
</div>

</div>

<script>
window.onload = function() {{
  setTimeout(function() {{ window.print(); }}, 400);
}};
</script>
</body>
</html>"""

        return html

    # ── helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _fmt_date(raw: str) -> str:
        if len(raw) == 10 and "-" in raw:
            try:
                return datetime.strptime(raw, "%Y-%m-%d").strftime("%d/%m/%y")
            except Exception:
                pass
        return raw
