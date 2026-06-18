"""
Integration Test - Dashboard with Financial Year Dropdown
Tests the actual dashboard screen implementation
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import tkinter as tk
from tkinter import ttk
from app.ui.dashboard_screen import DashboardScreen

class MockApp:
    """Mock application instance for testing"""
    def __init__(self):
        self.db = MockDB()
        self._active_screen = None
    
class MockDB:
    """Mock database for testing"""
    def fetch_dashboard(self, start, end):
        return {
            "products": 150,
            "value": 250000,
            "low_stock": 12,
            "out_stock": 5
        }
    
    def fetch_inventory(self, query=""):
        return []

def create_test_dashboard():
    root = tk.Tk()
    root.title("Dashboard Integration Test - MedicVista Retailer")
    root.geometry("1200x800")
    root.state("zoomed")
    
    # Info bar at top
    info_bar = tk.Frame(root, bg="#10b981", height=40)
    info_bar.pack(fill="x", side="top")
    info_bar.pack_propagate(False)
    
    info_label = tk.Label(
        info_bar,
        text="✓ INTEGRATION TEST - Dashboard with Financial Year Dropdown",
        font=("Segoe UI", 12, "bold"),
        fg="#ffffff",
        bg="#10b981",
        padx=20
    )
    info_label.pack(side="left", pady=8)
    
    instructions_btn = tk.Label(
        info_bar,
        text="📌 Instructions",
        font=("Segoe UI", 10, "bold"),
        fg="#ffffff",
        bg="#059669",
        padx=15,
        pady=5,
        cursor="hand2"
    )
    instructions_btn.pack(side="right", padx=10)
    
    # Main container
    main_container = tk.Frame(root)
    main_container.pack(fill="both", expand=True)
    
    # Mock app instance
    mock_app = MockApp()
    
    # Create actual DashboardScreen
    try:
        dashboard = DashboardScreen(main_container, mock_app)
        dashboard.pack(fill="both", expand=True)
        mock_app._active_screen = dashboard
        
        print("="*70)
        print("DASHBOARD INTEGRATION TEST")
        print("="*70)
        print("✓ Dashboard screen created successfully")
        print(f"✓ FY Combo exists: {dashboard.fy_combo is not None}")
        if dashboard.fy_combo:
            print(f"✓ FY Combo winfo_exists: {dashboard.fy_combo.winfo_exists()}")
            print(f"✓ FY Combo current value: {dashboard.fy_var.get()}")
            print(f"✓ FY Combo values count: {len(dashboard.fy_combo['values'])}")
        print("="*70)
        print("\nTEST CHECKLIST:")
        print("1. Can you see the header with light gray background?")
        print("2. Can you see 'Dashboard' title on the left?")
        print("3. Can you see Financial Year dropdown on the right?")
        print("4. Is the FY dropdown white with purple border?")
        print("5. Does it show current financial year (e.g., 2025-2026)?")
        print("6. Press Ctrl+B - does the dropdown open?")
        print("7. Can you select different years?")
        print("="*70)
        
    except Exception as e:
        error_label = tk.Label(
            main_container,
            text=f"ERROR: {str(e)}",
            font=("Segoe UI", 14, "bold"),
            fg="#ef4444",
            bg="#ffffff",
            wraplength=800
        )
        error_label.pack(expand=True)
        print(f"ERROR creating dashboard: {e}")
        import traceback
        traceback.print_exc()
    
    # Global Ctrl+B handler (simulating shortcuts.py)
    def on_ctrl_b(event):
        print("\n[GLOBAL] Ctrl+B pressed!")
        if mock_app._active_screen and hasattr(mock_app._active_screen, 'fy_combo'):
            try:
                combo = mock_app._active_screen.fy_combo
                print(f"[GLOBAL] FY combo found: {combo}")
                combo.focus_set()
                combo.focus_force()
                combo.event_generate('<Button-1>')
                root.after(50, lambda: combo.event_generate('<Down>'))
                print("[GLOBAL] FY dropdown opened!")
            except Exception as e:
                print(f"[GLOBAL] Error: {e}")
        return "break"
    
    root.bind("<Control-b>", on_ctrl_b)
    root.bind("<Control-B>", on_ctrl_b)
    
    # Show instructions
    def show_instructions():
        inst_win = tk.Toplevel(root)
        inst_win.title("Test Instructions")
        inst_win.geometry("600x500")
        inst_win.configure(bg="#ffffff")
        
        tk.Label(
            inst_win,
            text="Dashboard Integration Test",
            font=("Segoe UI", 18, "bold"),
            fg="#111827",
            bg="#ffffff"
        ).pack(pady=20)
        
        text = tk.Text(
            inst_win,
            font=("Segoe UI", 11),
            bg="#f9fafb",
            fg="#111827",
            relief="flat",
            wrap="word",
            padx=20,
            pady=20
        )
        text.pack(fill="both", expand=True, padx=20, pady=10)
        
        text.insert("1.0", """
What to Check:
═══════════════════════════════════

✓ VISUAL ELEMENTS:
1. Header should have LIGHT GRAY background (#f9fafb)
2. "Dashboard" title should be visible on the LEFT
3. Financial Year dropdown should be on the RIGHT
4. FY dropdown should have:
   - WHITE background
   - PURPLE border (thick)
   - Calendar emoji 📅
   - Current year displayed (e.g., 2025-2026)
   - "Ctrl+B" hint label next to it

✓ FUNCTIONALITY:
1. Click on FY dropdown - should show years from 2012-13 to current
2. Press Ctrl+B - dropdown should open automatically
3. Select a year - should update and show in dropdown
4. Console should show debug messages

✓ IF NOT VISIBLE:
1. Check if header is rendering (look for light gray strip at top)
2. Check console for any errors
3. Try clicking on the right side of the header
4. Try pressing Ctrl+B and check console output

✓ DEBUG INFO:
Check the terminal/console output:
- "Dashboard screen created successfully"
- "FY Combo exists: True"
- Current FY value
- Number of FY options available

═══════════════════════════════════

Press Ctrl+B anywhere to test!
Press Escape to close this window.
""")
        text.config(state="disabled")
        
        tk.Button(
            inst_win,
            text="Close",
            font=("Segoe UI", 11, "bold"),
            bg="#6366f1",
            fg="#ffffff",
            padx=30,
            pady=10,
            cursor="hand2",
            command=inst_win.destroy
        ).pack(pady=10)
        
        inst_win.bind("<Escape>", lambda e: inst_win.destroy())
    
    instructions_btn.bind("<Button-1>", lambda e: show_instructions())
    
    # Show instructions immediately
    root.after(500, show_instructions)
    
    root.mainloop()

if __name__ == "__main__":
    print("\nStarting Dashboard Integration Test...")
    print("This will load the ACTUAL DashboardScreen class")
    print("="*70)
    create_test_dashboard()
