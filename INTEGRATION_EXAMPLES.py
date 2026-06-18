"""
Integration Example: How to Use Modern UI Components in Your Application

This file demonstrates how to integrate the modern UI system into your existing app.
Copy and adapt the patterns shown here to your screens.
"""

import tkinter as tk
from tkinter import ttk

# Import modern components
from app.modern_ui_components import (
    ModernButton, ModernEntry, ModernLabel, ModernFrame,
    ModernCheckbutton, StatusBadge, PopupNotification,
    LoadingSpinner, AnimatedProgressBar
)
from app.ui.components.modern_sidebar import ModernColorfulSidebar
from app.ui.modern_dashboard import ModernDashboardScreen
from app.ui.login.modern_login_screen import ModernLoginScreen
from app.styles import COLORS, FONT

# ──────────────────────────────────────────────────────────────────────────────
# EXAMPLE 1: Integrate Modern Login
# ──────────────────────────────────────────────────────────────────────────────

def example_login_integration(root):
    """Show how to use modern login screen."""
    
    def on_login(username, password):
        """Handle login callback."""
        print(f"Login: {username}")
        # TODO: Validate credentials
        # On success:
        PopupNotification(root, "Success", "Logged in!", notification_type="success")
        # Switch to main screen
    
    login_screen = ModernLoginScreen(root, on_login=on_login)
    login_screen.pack(fill="both", expand=True)


# ──────────────────────────────────────────────────────────────────────────────
# EXAMPLE 2: Integrate Modern Sidebar
# ──────────────────────────────────────────────────────────────────────────────

class MainApplicationWithSidebar:
    """Example app structure with modern sidebar and screens."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("MedicVista Retailer")
        self.root.geometry("1400x800")
        
        # Main container
        main_frame = tk.Frame(root, bg=COLORS["bg_light"])
        main_frame.pack(fill="both", expand=True)
        
        # Sidebar
        self.sidebar = ModernColorfulSidebar(main_frame, app=self)
        self.sidebar.pack(side="left", fill="y")
        
        # Content area
        self.content_frame = tk.Frame(main_frame, bg=COLORS["bg_light"])
        self.content_frame.pack(side="left", fill="both", expand=True)
        
        # Show initial screen
        self.show_screen("Dashboard")
    
    def show_screen(self, screen_name):
        """Switch to a different screen."""
        # Clear previous content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Load new screen
        if screen_name == "Dashboard":
            ModernDashboardScreen(self.content_frame, self).pack(fill="both", expand=True)
        elif screen_name == "Product List":
            self._show_product_list()
        elif screen_name == "New Sale":
            self._show_sales_form()
        else:
            # Generic placeholder
            lbl = ModernLabel(self.content_frame, f"Screen: {screen_name}", variant="h1")
            lbl.pack(padx=20, pady=20)


# ──────────────────────────────────────────────────────────────────────────────
# EXAMPLE 3: Modern Form Screen
# ──────────────────────────────────────────────────────────────────────────────

def _show_sales_form(self):
    """Example: Modern sales form."""
    
    # Create scrollable container
    canvas = tk.Canvas(self.content_frame, bg=COLORS["bg_light"], highlightthickness=0)
    scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=COLORS["bg_light"])
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Form content
    form = tk.Frame(scrollable_frame, bg=COLORS["bg_light"])
    form.pack(padx=20, pady=20, fill="both")
    
    # Title
    ModernLabel(form, "Create New Sale", variant="h1").pack(anchor="w", pady=(0, 12))
    
    # Form section 1: Customer
    section1 = tk.Frame(form, bg=COLORS["white"], relief="solid", bd=1)
    section1.pack(fill="x", pady=(0, 16))
    
    header1 = tk.Frame(section1, bg=COLORS["purple"], height=40)
    header1.pack(fill="x")
    header1.pack_propagate(False)
    
    ModernLabel(header1, "Customer Information", variant="h3", bg=COLORS["purple"]).pack(
        anchor="w", padx=12, pady=8, side="left"
    )
    
    content1 = tk.Frame(section1, bg=COLORS["white"], padx=16, pady=16)
    content1.pack(fill="both", expand=True)
    
    ModernLabel(content1, "Customer Name", variant="subtitle").pack(anchor="w", pady=(0, 4))
    ModernEntry(content1, placeholder="Select or enter customer").pack(fill="x", pady=(0, 12))
    
    ModernLabel(content1, "Phone", variant="subtitle").pack(anchor="w", pady=(0, 4))
    ModernEntry(content1, placeholder="Enter phone number").pack(fill="x", pady=(0, 12))
    
    ModernLabel(content1, "Address", variant="subtitle").pack(anchor="w", pady=(0, 4))
    ModernEntry(content1, placeholder="Enter address").pack(fill="x", pady=(0, 0))
    
    # Form section 2: Items
    section2 = tk.Frame(form, bg=COLORS["white"], relief="solid", bd=1)
    section2.pack(fill="x", pady=(0, 16))
    
    header2 = tk.Frame(section2, bg=COLORS["green"], height=40)
    header2.pack(fill="x")
    header2.pack_propagate(False)
    
    ModernLabel(header2, "Products", variant="h3", bg=COLORS["green"]).pack(
        anchor="w", padx=12, pady=8, side="left"
    )
    
    # Sample item table
    content2 = tk.Frame(section2, bg=COLORS["white"], padx=16, pady=16)
    content2.pack(fill="both", expand=True)
    
    # Item rows (simplified)
    items = [
        ("Paracetamol 500mg", "1 Box", "₹150", "₹150"),
        ("Ibuprofen 400mg", "2 Strips", "₹80", "₹160"),
    ]
    
    for product, qty, price, total in items:
        item_row = tk.Frame(content2, bg=COLORS["row_odd"])
        item_row.pack(fill="x", pady=2)
        
        ModernLabel(item_row, product, variant="body", bg=COLORS["row_odd"]).pack(
            side="left", expand=True, padx=8, pady=4
        )
        ModernLabel(item_row, qty, variant="body", bg=COLORS["row_odd"]).pack(
            side="left", padx=8, pady=4
        )
        ModernLabel(item_row, price, variant="body", bg=COLORS["row_odd"]).pack(
            side="left", padx=8, pady=4
        )
        ModernLabel(item_row, total, variant="body", bg=COLORS["row_odd"]).pack(
            side="right", padx=8, pady=4
        )
    
    # Add button
    ModernButton(content2, "+ Add Product", variant="info").pack(fill="x", pady=(12, 0))
    
    # Form section 3: Summary
    section3 = tk.Frame(form, bg=COLORS["white"], relief="solid", bd=1)
    section3.pack(fill="x", pady=(0, 16))
    
    content3 = tk.Frame(section3, bg=COLORS["white"], padx=16, pady=16)
    content3.pack(fill="both", expand=True)
    
    # Summary items
    summary_items = [
        ("Subtotal", "₹310"),
        ("Tax (18%)", "₹55.80"),
        ("Discount", "-₹10"),
        ("Total", "₹355.80"),
    ]
    
    for label, value in summary_items:
        row = tk.Frame(content3, bg=COLORS["white"])
        row.pack(fill="x", pady=4)
        
        if label == "Total":
            ModernLabel(row, label, variant="h3", bg=COLORS["white"]).pack(side="left")
            ModernLabel(row, value, variant="h3", bg=COLORS["white"], fg=COLORS["green"]).pack(side="right")
        else:
            ModernLabel(row, label, variant="body", bg=COLORS["white"]).pack(side="left")
            ModernLabel(row, value, variant="body", bg=COLORS["white"]).pack(side="right")
    
    # Action buttons
    button_frame = tk.Frame(form, bg=COLORS["bg_light"])
    button_frame.pack(fill="x", pady=(20, 0))
    
    ModernButton(button_frame, "Cancel", variant="secondary").pack(side="left", padx=(0, 8))
    ModernButton(button_frame, "Save Draft", variant="info").pack(side="left", padx=(0, 8))
    ModernButton(button_frame, "Complete Sale", variant="success").pack(side="left")


# ──────────────────────────────────────────────────────────────────────────────
# EXAMPLE 4: Modern Data List
# ──────────────────────────────────────────────────────────────────────────────

def _show_product_list(self):
    """Example: Modern product list with status."""
    
    # Header
    header = tk.Frame(self.content_frame, bg=COLORS["bg_light"])
    header.pack(fill="x", padx=20, pady=(20, 16))
    
    ModernLabel(header, "Product List", variant="h1").pack(anchor="w", side="left")
    ModernButton(header, "+ New Product", variant="primary").pack(side="right")
    
    # Search
    search_frame = tk.Frame(self.content_frame, bg=COLORS["bg_light"])
    search_frame.pack(fill="x", padx=20, pady=(0, 12))
    
    ModernLabel(search_frame, "Search:", variant="body").pack(side="left", padx=(0, 8))
    ModernEntry(search_frame, placeholder="Search products...", width=30).pack(side="left")
    
    # Table header
    table_header = tk.Frame(self.content_frame, bg=COLORS["heading_bg"])
    table_header.pack(fill="x", padx=20, pady=(0, 2))
    table_header.grid_columnconfigure(0, weight=3)
    table_header.grid_columnconfigure(1, weight=1)
    table_header.grid_columnconfigure(2, weight=1)
    table_header.grid_columnconfigure(3, weight=1)
    
    ModernLabel(table_header, "Product Name", variant="body", bg=COLORS["heading_bg"]).grid(
        row=0, column=0, sticky="w", padx=12, pady=8
    )
    ModernLabel(table_header, "Qty", variant="body", bg=COLORS["heading_bg"]).grid(
        row=0, column=1, sticky="w", padx=12, pady=8
    )
    ModernLabel(table_header, "Price", variant="body", bg=COLORS["heading_bg"]).grid(
        row=0, column=2, sticky="w", padx=12, pady=8
    )
    ModernLabel(table_header, "Status", variant="body", bg=COLORS["heading_bg"]).grid(
        row=0, column=3, sticky="w", padx=12, pady=8
    )
    
    # Sample products
    products = [
        ("Paracetamol 500mg", "150", "₹45.00", "in_stock"),
        ("Ibuprofen 400mg", "45", "₹65.00", "low_stock"),
        ("Cough Syrup", "0", "₹85.00", "out_of_stock"),
        ("Vitamin D3", "200", "₹120.00", "in_stock"),
    ]
    
    # Table body
    table_body = tk.Frame(self.content_frame, bg=COLORS["bg_light"])
    table_body.pack(fill="both", expand=True, padx=20)
    
    for idx, (name, qty, price, status) in enumerate(products):
        row = tk.Frame(table_body, bg=COLORS["row_odd"] if idx % 2 == 0 else COLORS["row_even"])
        row.pack(fill="x", pady=1)
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=1)
        row.grid_columnconfigure(2, weight=1)
        row.grid_columnconfigure(3, weight=1)
        
        ModernLabel(row, name, variant="body", bg=row.cget("bg")).grid(
            row=0, column=0, sticky="w", padx=12, pady=8
        )
        ModernLabel(row, qty, variant="body", bg=row.cget("bg")).grid(
            row=0, column=1, sticky="w", padx=12, pady=8
        )
        ModernLabel(row, price, variant="body", bg=row.cget("bg")).grid(
            row=0, column=2, sticky="w", padx=12, pady=8
        )
        StatusBadge(row, text=status.upper(), status=status).grid(
            row=0, column=3, sticky="w", padx=12, pady=8
        )


# ──────────────────────────────────────────────────────────────────────────────
# EXAMPLE 5: Modal Dialog with Modern Styling
# ──────────────────────────────────────────────────────────────────────────────

def show_modern_dialog(parent, title, fields):
    """Create a modern modal dialog."""
    
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.geometry("500x400")
    dialog.resizable(False, False)
    
    # Header
    header = tk.Frame(dialog, bg=COLORS["purple"], height=50)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    tk.Label(
        header,
        text=title,
        font=("Segoe UI", 14, "bold"),
        bg=COLORS["purple"],
        fg="white"
    ).pack(anchor="w", padx=16, pady=12)
    
    # Content
    content = tk.Frame(dialog, bg=COLORS["bg_light"], padx=16, pady=16)
    content.pack(fill="both", expand=True)
    
    # Fields
    entries = {}
    for field_name in fields:
        ModernLabel(content, field_name, variant="subtitle").pack(anchor="w", pady=(0, 4))
        entry = ModernEntry(content, placeholder=f"Enter {field_name.lower()}")
        entry.pack(fill="x", pady=(0, 12))
        entries[field_name] = entry
    
    # Footer
    footer = tk.Frame(dialog, bg=COLORS["bg_light"], padx=16, pady=12)
    footer.pack(fill="x", side="bottom")
    
    def on_submit():
        data = {k: v.get() for k, v in entries.items()}
        print("Dialog data:", data)
        dialog.destroy()
    
    ModernButton(footer, "Cancel", variant="secondary").pack(side="left", padx=(0, 8))
    ModernButton(footer, "Submit", variant="primary", command=on_submit).pack(side="left")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1400x800")
    
    # Apply styles
    from app.styles import apply_style
    apply_style(root)
    
    # Create app with sidebar
    app = MainApplicationWithSidebar(root)
    
    # Bind show_screen methods
    app._show_product_list = _show_product_list.__get__(app)
    app._show_sales_form = _show_sales_form.__get__(app)
    
    root.mainloop()
