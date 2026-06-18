"""Thermal Receipt Print Dialog - 80mm format."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import tempfile

class ReceiptPrintDialog(tk.Toplevel):
    def __init__(self, parent, app, invoice_data):
        super().__init__(parent)
        self.app = app
        self.invoice_data = invoice_data
        self.parent_dialog = parent
        
        self.title("Receipt Preview")
        self.geometry("400x500")  # Smaller window for faster rendering
        self.configure(bg="white")
        self.resizable(False, False)
        
        # Build immediately for speed (no defer needed with simple layout)
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Keyboard shortcuts
        self.bind("<Escape>", lambda e: self._on_close())
        self.bind("<Control-p>", lambda e: self._print_receipt())

        
    def _build(self):
        # Main container - simplified, no scrollbar for speed
        main_frame = tk.Frame(self, bg="white")
        main_frame.pack(fill="both", expand=True)
        
        # Top buttons
        btn_frame = tk.Frame(main_frame, bg="#f1f5f9", pady=8)
        btn_frame.pack(fill="x")
        
        tk.Button(btn_frame, text="🖨️ Print (Ctrl+P)", 
                  bg="#10b981", fg="white", font=("Arial", 10, "bold"),
                  bd=0, padx=20, pady=8, cursor="hand2",
                  command=self._print_receipt).pack(side="left", padx=10)
        
        tk.Button(btn_frame, text="✖ Close (Esc)", 
                  bg="#6b7280", fg="white", font=("Arial", 10, "bold"),
                  bd=0, padx=20, pady=8, cursor="hand2",
                  command=self._on_close).pack(side="left", padx=5)
        
        # Receipt preview area - simple frame, no canvas
        receipt_frame = tk.Frame(main_frame, bg="white", padx=15, pady=15)
        receipt_frame.pack(fill="both", expand=True)
        
        # Build receipt content with simplified fonts
        self._build_receipt_simple(receipt_frame)
        
    def _build_receipt_simple(self, parent):
        """Build simplified receipt (no heavy fonts, minimal widgets)."""
        inv = self.invoice_data
        inv_no = inv.get('sales_invoice_no', 'N/A')
        inv_date = str(inv.get('sales_invoice_date', ''))[:10]
        customer_name = inv.get('customer_name', 'Walk-in Customer')
        items = inv.get('items', [])
        transport = float(inv.get('sales_transport_charges', 0))
        
        # Use simple Arial font instead of Courier New (faster rendering)
        font_h = ("Arial", 11, "bold")
        font_n = ("Arial", 8)
        font_s = ("Arial", 7)
        
        # Store name
        store_name = getattr(self.app, 'config_data', None)
        if store_name:
            store_name = store_name.store_name or "MEDICVISTA PHARMACY"
        else:
            store_name = "MEDICVISTA PHARMACY"
        
        # Header - minimal labels
        tk.Label(parent, text=store_name, font=font_h, bg="white").pack()
        tk.Label(parent, text=f"Invoice: {inv_no}  |  Date: {inv_date}", 
                 font=font_n, bg="white").pack(pady=2)
        tk.Label(parent, text=f"Customer: {customer_name}", font=font_n, bg="white").pack(pady=2)
        
        tk.Frame(parent, bg="#000000", height=1).pack(fill="x", pady=5)
        
        # Items summary (simplified - no detailed table)
        subtotal = 0
        total_gst = 0
        
        tk.Label(parent, text="ITEMS:", font=font_h, bg="white").pack(anchor="w", pady=2)
        
        for idx, item in enumerate(items[:10], 1):  # Show max 10 items for speed
            qty = int(item.get('sale_quantity', 0) or item.get('quantity', 1))
            name = str(item.get('product_name', 'Product'))[:30]
            mrp = float(item.get('product_MRP', 0) or item.get('mrp', 0))
            cgst = float(item.get('sale_cgst', 0) or item.get('cgst', 0))
            sgst = float(item.get('sale_sgst', 0) or item.get('sgst', 0))
            discount = float(item.get('sale_discount', 0) or item.get('discount', 0))
            
            line_sub = (mrp * qty) - discount
            gst = (line_sub * (cgst + sgst)) / 100
            line_total = line_sub + gst
            
            subtotal += line_sub
            total_gst += gst
            
            # Simple item line
            tk.Label(parent, text=f"{idx}. {name} x{qty}  =  ₹{line_total:.2f}",
                     font=font_s, bg="white").pack(anchor="w")
        
        if len(items) > 10:
            tk.Label(parent, text=f"... and {len(items)-10} more items",
                     font=font_s, bg="white", fg="#6b7280").pack(anchor="w")
        
        tk.Frame(parent, bg="#000000", height=1).pack(fill="x", pady=5)
        
        # Totals
        grand = round(subtotal + total_gst + transport)
        
        tk.Label(parent, text=f"Subtotal: ₹{subtotal:.2f}", font=font_n, bg="white").pack(anchor="w")
        if transport > 0:
            tk.Label(parent, text=f"Transport: ₹{transport:.2f}", font=font_n, bg="white").pack(anchor="w")
        tk.Label(parent, text=f"GST: ₹{total_gst:.2f}", font=font_n, bg="white").pack(anchor="w")
        
        tk.Frame(parent, bg="#000000", height=2).pack(fill="x", pady=5)
        
        tk.Label(parent, text=f"TOTAL: ₹{grand:.2f}", 
                 font=("Arial", 14, "bold"), bg="white").pack(pady=5)
        
        tk.Label(parent, text="Press Print button to print receipt",
                 font=font_s, bg="white", fg="#10b981").pack(pady=10)
    
    def _amount_to_words(self, amount):
        """Convert amount to words (simplified version)."""
        try:
            amount = int(amount)
            if amount == 0:
                return "Zero Rupees Only"
            
            ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
            teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 
                     'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
            tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
            
            if amount < 10:
                return f"{ones[amount]} Rupees Only"
            elif amount < 20:
                return f"{teens[amount-10]} Rupees Only"
            elif amount < 100:
                return f"{tens[amount//10]} {ones[amount%10]} Rupees Only".strip()
            elif amount < 1000:
                return f"{ones[amount//100]} Hundred {tens[(amount%100)//10]} {ones[amount%10]} Rupees Only".strip()
            elif amount < 100000:
                thousands = amount // 1000
                remainder = amount % 1000
                result = f"{ones[thousands]} Thousand "
                if remainder > 0:
                    if remainder < 100:
                        result += f"{tens[remainder//10]} {ones[remainder%10]} "
                    else:
                        result += f"{ones[remainder//100]} Hundred {tens[(remainder%100)//10]} {ones[remainder%10]} "
                return (result + "Rupees Only").strip()
            else:
                return f"{amount} Rupees Only"
        except:
            return "Amount in Words"
        
    def _print_receipt(self):
        """Generate HTML and open in browser for printing."""
        try:
            html_content = self._generate_html()
            
            # Save to temp file
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8')
            temp_file.write(html_content)
            temp_file.close()
            
            # Open in browser
            import webbrowser
            webbrowser.open(f'file://{temp_file.name}')
            
            messagebox.showinfo("Print", 
                               "Receipt opened in browser.\nUse Ctrl+P to print from browser.",
                               parent=self)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate receipt: {str(e)}", parent=self)
    
    def _on_close(self):
        """Close receipt dialog only - do NOT close parent or navigate."""
        self.destroy()
    
    @staticmethod
    def generate_receipt_html(app, invoice_data):
        """Static method to generate HTML receipt without opening dialog."""
        inv = invoice_data
        inv_no = inv.get('sales_invoice_no', 'N/A')
        inv_date = inv.get('sales_invoice_date', datetime.now().strftime('%d/%m/%y'))
        
        # Format date
        if len(str(inv_date)) == 10 and '-' in str(inv_date):
            try:
                from datetime import datetime as dt
                date_obj = dt.strptime(str(inv_date), '%Y-%m-%d')
                inv_date = date_obj.strftime('%d/%m/%y')
            except:
                pass
        
        inv_time = datetime.now().strftime('%H:%M')
        customer_name = inv.get('customer_name', 'Walk-in Customer')
        items = inv.get('items', [])
        transport = float(inv.get('sales_transport_charges', 0))
        
        store_name = getattr(app, 'config_data', None)
        if store_name:
            store_name = store_name.store_name or "MEDICVISTA PHARMA PVT. LTD."
        else:
            store_name = "MEDICVISTA PHARMA PVT. LTD."
        
        # Calculate totals
        subtotal = 0
        total_cgst = 0
        total_sgst = 0
        
        items_html = ""
        for item in items:
            qty = int(item.get('sale_quantity', 0) or item.get('quantity', 1))
            name = str(item.get('product_name', 'Product'))
            packing = str(item.get('product_packing', 'N/A'))
            manufacturer = str(item.get('product_company', 'N/A'))
            batch = str(item.get('product_batch_no', '') or item.get('batch_no', 'N/A'))
            expiry = str(item.get('product_expiry', '') or item.get('expiry', 'N/A'))
            mrp = float(item.get('product_MRP', 0) or item.get('mrp', 0))
            
            cgst_pct = float(item.get('sale_cgst', 0) or item.get('cgst', 0))
            sgst_pct = float(item.get('sale_sgst', 0) or item.get('sgst', 0))
            
            discount = float(item.get('sale_discount', 0) or item.get('discount', 0))
            line_subtotal = (mrp * qty) - discount
            cgst_amt = (line_subtotal * cgst_pct) / 100
            sgst_amt = (line_subtotal * sgst_pct) / 100
            line_total = line_subtotal + cgst_amt + sgst_amt
            
            subtotal += line_subtotal
            total_cgst += cgst_amt
            total_sgst += sgst_amt
            
            items_html += f"""
<tr>
  <td>{qty}</td>
  <td>{name}</td>
  <td>{packing}</td>
  <td>{manufacturer}</td>
  <td>{batch}</td>
  <td>{expiry}</td>
  <td class="right">{qty}</td>
  <td class="right">{mrp:.2f}</td>
  <td>3004</td>
  <td class="right">{cgst_pct+sgst_pct:.1f}%</td>
  <td class="right"><b>{line_total:.2f}</b></td>
</tr>
"""
        
        total_gst = total_cgst + total_sgst
        grand_total_before_round = subtotal + total_gst + transport
        grand_total = round(grand_total_before_round)
        round_off = grand_total - grand_total_before_round
        
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Receipt - {inv_no}</title>
<style>
@page {{
  size: landscape;
  margin: 10mm;
}}

body {{
  font-family: Arial, sans-serif;
  margin: 10px;
  font-size: 11px;
}}

.invoice {{
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
}}

.center {{ text-align: center; }}
.line {{ border-bottom: 1px solid #ddd; margin: 8px 0; }}

table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 10px;
}}

td, th {{
  padding: 5px;
  border: 1px solid #ddd;
  text-align: left;
}}

th {{ background-color: #f0f0f0; font-weight: bold; }}
.right {{ text-align: right; }}

@media print {{
  @page {{ size: landscape; margin: 10mm; }}
  body {{ margin: 0; }}
}}
</style>
</head>
<body>

<div class="invoice">
<div class="center" style="font-size: 16px; font-weight: bold;">{store_name}</div>
<div class="center" style="font-size: 10px; margin-bottom: 10px;">
  MIDC Nagar, Bhusawal | Drug License: DL-MH-JLG-20B-1234, DL-MH-JLG-21B-5678<br>
  GST: 27ABCDE1234F1Z5 | Ph: +91-9876543210 | Email: info@medicvista.com
</div>

<div class="center" style="font-size: 14px; font-weight: bold; margin: 10px 0;">GST INVOICE (CASH)</div>

<table style="border: none; margin-bottom: 10px;">
<tr>
  <td style="border: none;"><b>Invoice:</b> {inv_no}</td>
  <td style="border: none;"><b>Date:</b> {inv_date}</td>
  <td style="border: none;"><b>Time:</b> {inv_time}</td>
  <td style="border: none;"><b>Customer:</b> {customer_name}</td>
</tr>
</table>

<table>
<thead>
<tr>
  <th style="width:30px;">#</th>
  <th>Item Name</th>
  <th style="width:80px;">Pack</th>
  <th style="width:120px;">Manufacturer</th>
  <th style="width:70px;">Batch</th>
  <th style="width:70px;">Expiry</th>
  <th style="width:50px;" class="right">Qty</th>
  <th style="width:70px;" class="right">MRP</th>
  <th style="width:50px;">HSN</th>
  <th style="width:60px;" class="right">Tax%</th>
  <th style="width:80px;" class="right">Amount</th>
</tr>
</thead>
<tbody>
{items_html}
</tbody>
</table>

<table style="width: 350px; float: right; margin-top: 10px;">
<tr><td>Subtotal:</td><td class="right"><b>{subtotal:.2f}</b></td></tr>
{f'<tr><td>Transport:</td><td class="right">{transport:.2f}</td></tr>' if transport > 0 else ''}
<tr><td>CGST:</td><td class="right">{total_cgst:.2f}</td></tr>
<tr><td>SGST:</td><td class="right">{total_sgst:.2f}</td></tr>
<tr><td><b>Total GST:</b></td><td class="right"><b>{total_gst:.2f}</b></td></tr>
{f'<tr><td>Round Off:</td><td class="right">{round_off:.2f}</td></tr>' if abs(round_off) > 0.001 else ''}
<tr style="background: #f0f0f0;"><td><b>GRAND TOTAL:</b></td><td class="right"><b style="font-size:14px;">₹ {grand_total:.2f}</b></td></tr>
</table>

<div style="clear: both; margin-top: 20px;"></div>
<div class="center" style="font-size: 10px; margin-top: 20px;">
  <b>Items: {len(items)}</b> | <b>Payment: CASH</b><br><br>
  <b>For {store_name}</b><br>
  <span style="color: #dc2626; font-weight: bold;">⚠ Consult doctor before use</span><br>
  Subject to Bhusawal Jurisdiction<br><br>
  <b>🙏 Thank you for your visit! 🙏</b>
</div>

</div>

<script>
window.onload = function() {{
  setTimeout(function() {{ window.print(); }}, 500);
}};
</script>

</body>
</html>"""
        
        return html
    
    def _generate_html(self):
        """Instance method wrapper for generating HTML."""
        return self.generate_receipt_html(self.app, self.invoice_data)
