"""
Test Financial Year Dropdown - Simple Standalone Test
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime

def create_test_window():
    root = tk.Tk()
    root.title("Financial Year Dropdown Test")
    root.geometry("800x600")
    root.configure(bg="#f9fafb")
    
    # Main container
    main_frame = tk.Frame(root, bg="#f9fafb")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Title
    title = tk.Label(
        main_frame,
        text="Financial Year Dropdown Test",
        font=("Segoe UI", 20, "bold"),
        fg="#111827",
        bg="#f9fafb"
    )
    title.pack(pady=20)
    
    # Info label
    info = tk.Label(
        main_frame,
        text="Press Ctrl+B to open Financial Year dropdown",
        font=("Segoe UI", 12),
        fg="#6b7280",
        bg="#f9fafb"
    )
    info.pack(pady=10)
    
    # Financial Year Section
    fy_container = tk.Frame(main_frame, bg="#f9fafb")
    fy_container.pack(pady=30)
    
    # Purple border frame
    fy_outer = tk.Frame(fy_container, bg="#6366f1", bd=0)
    fy_outer.pack()
    
    # White inner frame
    fy_frame = tk.Frame(fy_outer, bg="#ffffff", bd=0)
    fy_frame.pack(padx=3, pady=3)
    
    # Label
    fy_label = tk.Label(
        fy_frame,
        text="📅 Financial Year:",
        font=("Segoe UI", 14, "bold"),
        fg="#1f2937",
        bg="#ffffff",
        padx=15,
        pady=12
    )
    fy_label.pack(side="left")
    
    # Generate FY list
    def generate_fy_list():
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        if current_month < 4:
            end_year = current_year
        else:
            end_year = current_year + 1
        
        fy_list = []
        for year in range(2012, end_year):
            fy_list.append(f"{year}-{year+1}")
        
        return list(reversed(fy_list))
    
    def get_current_fy():
        now = datetime.now()
        if now.month >= 4:
            return f"{now.year}-{now.year+1}"
        else:
            return f"{now.year-1}-{now.year}"
    
    # Combobox
    fy_var = tk.StringVar(value=get_current_fy())
    fy_combo = ttk.Combobox(
        fy_frame,
        textvariable=fy_var,
        values=generate_fy_list(),
        state="readonly",
        width=15,
        font=("Segoe UI", 14, "bold")
    )
    fy_combo.pack(side="left", padx=(0, 15), pady=12)
    
    # Status label
    status_label = tk.Label(
        main_frame,
        text="Status: Waiting...",
        font=("Segoe UI", 12),
        fg="#10b981",
        bg="#f9fafb"
    )
    status_label.pack(pady=20)
    
    # Selected value display
    selected_label = tk.Label(
        main_frame,
        text=f"Selected: {get_current_fy()}",
        font=("Segoe UI", 16, "bold"),
        fg="#6366f1",
        bg="#f9fafb"
    )
    selected_label.pack(pady=10)
    
    # Bind selection change
    def on_fy_change(event=None):
        selected = fy_var.get()
        selected_label.config(text=f"Selected: {selected}")
        status_label.config(text=f"Status: Changed to {selected}", fg="#10b981")
        print(f"Financial Year changed to: {selected}")
    
    fy_combo.bind("<<ComboboxSelected>>", on_fy_change)
    
    # Ctrl+B shortcut
    def on_ctrl_b(event):
        print("Ctrl+B pressed!")
        status_label.config(text="Status: Ctrl+B pressed - Opening dropdown", fg="#f59e0b")
        try:
            fy_combo.focus_set()
            fy_combo.focus_force()
            fy_combo.event_generate('<Button-1>')
            root.after(50, lambda: fy_combo.event_generate('<Down>'))
            status_label.config(text="Status: Dropdown opened!", fg="#10b981")
        except Exception as e:
            status_label.config(text=f"Status: Error - {e}", fg="#ef4444")
            print(f"Error: {e}")
        return "break"
    
    root.bind("<Control-b>", on_ctrl_b)
    root.bind("<Control-B>", on_ctrl_b)
    
    # Instructions
    instructions = tk.Text(
        main_frame,
        height=10,
        width=60,
        font=("Segoe UI", 10),
        bg="#ffffff",
        fg="#111827",
        relief="solid",
        bd=1,
        wrap="word"
    )
    instructions.pack(pady=20)
    
    instructions.insert("1.0", """
Test Instructions:
==================

1. You should see a white box with purple border containing Financial Year dropdown
2. The dropdown should show current financial year (e.g., 2025-2026)
3. Click on the dropdown to see all years from 2012-13 to current
4. Press Ctrl+B to open the dropdown using keyboard shortcut
5. Select any year and it should update below

If you can see the dropdown clearly with white background and purple border,
then the issue is in the dashboard_screen.py file loading or layout.

If you CANNOT see the dropdown here either, then there might be a
tkinter/ttk configuration issue on your system.

Current Status: Everything should be visible!
""")
    instructions.config(state="disabled")
    
    # Quit button
    quit_btn = tk.Button(
        main_frame,
        text="Close Test",
        font=("Segoe UI", 12, "bold"),
        bg="#ef4444",
        fg="#ffffff",
        padx=20,
        pady=10,
        cursor="hand2",
        command=root.destroy
    )
    quit_btn.pack(pady=20)
    
    print("="*60)
    print("Financial Year Dropdown Test Started")
    print("="*60)
    print(f"Current FY: {get_current_fy()}")
    print(f"Available FYs: {len(generate_fy_list())} options")
    print("Press Ctrl+B to test keyboard shortcut")
    print("="*60)
    
    root.mainloop()

if __name__ == "__main__":
    create_test_window()
