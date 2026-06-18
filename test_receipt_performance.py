"""Test script to identify lag in receipt generation (Ctrl+L)"""
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import load_config
from app.db import Database

def test_receipt_generation_performance():
    """Test each step of receipt generation to identify bottleneck."""
    print("=" * 80)
    print("RECEIPT GENERATION PERFORMANCE TEST")
    print("=" * 80)
    
    # Initialize
    config = load_config()
    db = Database(config)
    
    # Get a sample invoice
    print("\n[1] Fetching sample invoice...")
    start = time.time()
    invoices = db.query("""
        SELECT sales_invoice_no, sales_invoice_date, customerid_id
        FROM core_salesinvoicemaster 
        ORDER BY sales_invoice_date DESC 
        LIMIT 1
    """)
    
    if not invoices:
        print("[ERROR] No invoices found in database!")
        return
    
    inv = invoices[0]
    inv_no = inv['sales_invoice_no']
    elapsed = (time.time() - start) * 1000
    print(f"[OK] Found invoice: {inv_no} - Time: {elapsed:.2f}ms")
    
    # Test 1: Get invoice details
    print("\n[2] Testing: db.get_sales_invoice()...")
    start = time.time()
    inv_data = db.get_sales_invoice(inv_no)
    elapsed = (time.time() - start) * 1000
    print(f"[RESULT] Invoice fetch time: {elapsed:.2f}ms")
    if elapsed > 100:
        print("[WARNING] This is slow! Should be < 100ms")
    
    # Test 2: Get items
    print("\n[3] Testing: db.get_sales_items()...")
    start = time.time()
    items = db.get_sales_items(inv_no)
    elapsed = (time.time() - start) * 1000
    print(f"[RESULT] Items fetch time: {elapsed:.2f}ms ({len(items)} items)")
    if elapsed > 200:
        print("[WARNING] This is slow! Should be < 200ms")
    
    # Test 3: HTML generation
    print("\n[4] Testing: HTML generation...")
    start = time.time()
    
    # Prepare receipt data
    receipt_data = {
        'sales_invoice_no': inv_no,
        'sales_invoice_date': inv_data.get('sales_invoice_date', ''),
        'customer_name': inv_data.get('customer_name', 'Walk-in Customer'),
        'sales_transport_charges': float(inv_data.get('sales_transport_charges', 0)),
        'items': items
    }
    
    # Simulate HTML generation (without opening browser)
    class MockApp:
        class ConfigData:
            store_name = "Test Store"
        config_data = ConfigData()
    
    try:
        from app.ui.sales.receipt_print_dialog import ReceiptPrintDialog
        html_content = ReceiptPrintDialog.generate_receipt_html(MockApp(), receipt_data)
        elapsed = (time.time() - start) * 1000
        print(f"[RESULT] HTML generation time: {elapsed:.2f}ms")
        print(f"[INFO] HTML size: {len(html_content)} characters")
        if elapsed > 100:
            print("[WARNING] HTML generation is slow!")
    except Exception as e:
        print(f"[ERROR] HTML generation failed: {e}")
    
    # Test 4: File write speed
    print("\n[5] Testing: Temp file write...")
    start = time.time()
    import tempfile
    try:
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8')
        temp_file.write(html_content)
        temp_file.close()
        elapsed = (time.time() - start) * 1000
        print(f"[RESULT] File write time: {elapsed:.2f}ms")
        print(f"[INFO] Temp file: {temp_file.name}")
        
        # Clean up
        import os
        os.unlink(temp_file.name)
    except Exception as e:
        print(f"[ERROR] File write failed: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("PERFORMANCE SUMMARY")
    print("=" * 80)
    print("\nExpected total time for Ctrl+L: ~300-500ms")
    print("If total > 1000ms, there's a performance issue!")
    print("\nCommon bottlenecks:")
    print("1. Database queries (should be < 300ms total)")
    print("2. HTML generation (should be < 100ms)")
    print("3. Browser launch (not measured here, ~200-500ms)")
    print("\n" + "=" * 80)


def test_in_memory_vs_database():
    """Compare in-memory data vs database fetch."""
    print("\n" + "=" * 80)
    print("IN-MEMORY vs DATABASE COMPARISON")
    print("=" * 80)
    
    config = load_config()
    db = Database(config)
    
    # Get sample invoice
    invoices = db.query("SELECT sales_invoice_no FROM core_salesinvoicemaster LIMIT 1")
    if not invoices:
        print("[ERROR] No invoices found!")
        return
    
    inv_no = invoices[0]['sales_invoice_no']
    
    # Method 1: Database fetch (current slow method)
    print("\n[METHOD 1] Database Fetch")
    start = time.time()
    inv_data = db.get_sales_invoice(inv_no)
    items = db.get_sales_items(inv_no)
    db_time = (time.time() - start) * 1000
    print(f"Time: {db_time:.2f}ms")
    
    # Method 2: Simulate in-memory (form data)
    print("\n[METHOD 2] In-Memory Data (from form)")
    start = time.time()
    # This simulates getting data from form variables (instant)
    mock_data = {
        'sales_invoice_no': inv_no,
        'sales_invoice_date': '2024-01-01',
        'customer_name': 'Test Customer',
        'sales_transport_charges': 0,
        'items': []  # Already in self._items
    }
    mem_time = (time.time() - start) * 1000
    print(f"Time: {mem_time:.2f}ms")
    
    # Comparison
    print("\n[COMPARISON]")
    print(f"Database method: {db_time:.2f}ms")
    print(f"In-memory method: {mem_time:.2f}ms")
    print(f"Speed improvement: {(db_time - mem_time):.2f}ms faster ({(db_time/mem_time):.1f}x)")
    
    if db_time > 500:
        print("\n[CRITICAL] Database fetch is TOO SLOW!")
        print("Recommendation: Use in-memory data from form variables")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        # Run performance tests
        test_receipt_generation_performance()
        
        # Run comparison test
        test_in_memory_vs_database()
        
        print("\n[DONE] Performance test complete!")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
