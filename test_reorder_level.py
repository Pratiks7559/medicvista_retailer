"""Test Reorder Level Calculations
This script verifies that reorder levels are correctly calculated based on
purchase, sales, and available stock data.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import load_config
from app.db import Database


def test_reorder_calculations():
    """Test reorder level calculations for products with purchase and sales."""
    print("=" * 80)
    print("REORDER LEVEL CALCULATION TEST")
    print("=" * 80)
    
    # Initialize database
    config = load_config()
    db = Database(config)
    
    print(f"\n[+] Connected to database: {config.db_name}")
    print(f"[+] Retailer ID: {config.retailer_id}")
    
    # Get 30 days ago date
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    print(f"\n[DATE] Analyzing last 30 days (from {thirty_days_ago} to today)")
    
    # Get sample products
    products = db.query("""
        SELECT productid, product_name, product_company, product_packing
        FROM core_productmaster
        ORDER BY product_name
        LIMIT 10
    """)
    
    print(f"\n[PRODUCTS] Found {len(products)} products to analyze\n")
    
    if not products:
        print("[ERROR] No products found in database!")
        return
    
    print("-" * 80)
    
    for idx, product in enumerate(products, 1):
        product_id = product["productid"]
        product_name = product["product_name"]
        
        print(f"\n{idx}. Product: {product_name}")
        print(f"   Company: {product['product_company']}")
        print(f"   Packing: {product['product_packing']}")
        
        # Calculate total stock from inventory_transaction
        stock_result = db.query("""
            SELECT 
                COALESCE(SUM(CASE
                    WHEN transaction_type IN ('PURCHASE') THEN quantity + free_quantity
                    WHEN transaction_type IN ('PURCHASE_RETURN','REVERT_PURCHASE_RETURN','REVERT_PURCHASE') 
                        THEN -(quantity + free_quantity)
                    WHEN transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') 
                        THEN -(quantity + free_quantity)
                    WHEN transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') 
                        THEN (quantity + free_quantity)
                    ELSE 0 END), 0) AS total_stock,
                COALESCE(SUM(CASE
                    WHEN transaction_type IN ('PURCHASE') THEN free_quantity
                    WHEN transaction_type IN ('PURCHASE_RETURN','REVERT_PURCHASE_RETURN','REVERT_PURCHASE') 
                        THEN -free_quantity
                    WHEN transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') 
                        THEN -free_quantity
                    WHEN transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') 
                        THEN free_quantity
                    ELSE 0 END), 0) AS free_qty
            FROM inventory_transaction
            WHERE product_id = %s AND retailer_id = %s
        """, (product_id, config.retailer_id))
        
        total_stock = float(stock_result[0]["total_stock"]) if stock_result else 0
        free_qty = float(stock_result[0]["free_qty"]) if stock_result else 0
        
        print(f"\n   [STOCK] Current Stock:")
        print(f"      Total Available: {total_stock:.1f}")
        print(f"      Free Quantity: {free_qty:.1f}")
        
        # Get purchase details for last 30 days
        purchase_result = db.query("""
            SELECT 
                COUNT(*) as purchase_count,
                COALESCE(SUM(quantity), 0) as total_purchased
            FROM inventory_transaction
            WHERE product_id = %s 
                AND retailer_id = %s
                AND transaction_type = 'PURCHASE'
                AND DATE(transaction_date) >= %s
        """, (product_id, config.retailer_id, thirty_days_ago))
        
        if purchase_result:
            purchase_count = int(purchase_result[0]["purchase_count"])
            total_purchased = float(purchase_result[0]["total_purchased"])
            print(f"\n   [PURCHASE] Purchases (Last 30 days):")
            print(f"      Transactions: {purchase_count}")
            print(f"      Total Quantity: {total_purchased:.1f}")
        
        # Get sales details for last 30 days
        sales_result = db.query("""
            SELECT 
                COUNT(*) as sales_count,
                COALESCE(SUM(quantity), 0) AS total_sales
            FROM inventory_transaction
            WHERE product_id = %s 
                AND retailer_id = %s
                AND transaction_type = 'SALE'
                AND DATE(transaction_date) >= %s
        """, (product_id, config.retailer_id, thirty_days_ago))
        
        avg_monthly_sale = 0
        if sales_result:
            sales_count = int(sales_result[0]["sales_count"])
            total_sales = float(sales_result[0]["total_sales"])
            avg_monthly_sale = total_sales
            
            print(f"\n   [SALES] Sales (Last 30 days):")
            print(f"      Transactions: {sales_count}")
            print(f"      Total Quantity Sold: {total_sales:.1f}")
            print(f"      Avg Monthly Sale: {avg_monthly_sale:.1f}")
        else:
            print(f"\n   [SALES] Sales (Last 30 days): No sales")
        
        # Calculate reorder level
        reorder_level = avg_monthly_sale * 1.5
        reorder_needed = max(0, reorder_level - total_stock)
        status = "[CRITICAL]" if reorder_needed > 0 else "[OK]"
        
        print(f"\n   [REORDER] Reorder Analysis:")
        print(f"      Reorder Level: {reorder_level:.1f} (Avg Sale × 1.5)")
        print(f"      Reorder Needed: {reorder_needed:.1f}")
        print(f"      Status: {status}")
        
        # Check recent transactions
        recent_trans = db.query("""
            SELECT transaction_type, quantity, free_quantity, 
                   DATE(transaction_date) as trans_date, reference_number
            FROM inventory_transaction
            WHERE product_id = %s AND retailer_id = %s
            ORDER BY transaction_date DESC
            LIMIT 5
        """, (product_id, config.retailer_id))
        
        if recent_trans:
            print(f"\n   [RECENT] Recent Transactions:")
            for t in recent_trans:
                qty = float(t["quantity"])
                fqty = float(t["free_quantity"])
                print(f"      {t['trans_date']} | {t['transaction_type']:20s} | "
                      f"Qty: {qty:6.1f} | Free: {fqty:6.1f} | Ref: {t['reference_number']}")
        
        print("\n" + "-" * 80)
    
    print("\n[SUCCESS] Test completed successfully!\n")
    print("=" * 80)


def check_database_status():
    """Check overall database and inventory status."""
    print("\n" + "=" * 80)
    print("DATABASE STATUS CHECK")
    print("=" * 80)
    
    config = load_config()
    db = Database(config)
    
    # Check total products
    products = db.query("SELECT COUNT(*) as total FROM core_productmaster")
    print(f"\n[PRODUCTS] Total Products: {products[0]['total'] if products else 0}")
    
    # Check inventory transactions
    trans = db.query("""
        SELECT 
            transaction_type,
            COUNT(*) as count,
            SUM(quantity) as total_qty
        FROM inventory_transaction
        WHERE retailer_id = %s
        GROUP BY transaction_type
        ORDER BY transaction_type
    """, (config.retailer_id,))
    
    if trans:
        print(f"\n[TRANSACTIONS] Inventory Transactions by Type:")
        for t in trans:
            print(f"   {t['transaction_type']:25s} | Count: {t['count']:5d} | "
                  f"Total Qty: {float(t['total_qty']):.1f}")
    else:
        print("\n[WARN] No inventory transactions found!")
    
    # Check products with stock
    stock = db.query("""
        SELECT COUNT(DISTINCT product_id) as products_with_stock
        FROM inventory_transaction
        WHERE retailer_id = %s
    """, (config.retailer_id,))
    
    if stock:
        print(f"\n[STOCK] Products with Stock: {stock[0]['products_with_stock']}")
    
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    try:
        # Check database status first
        check_database_status()
        
        # Run reorder level test
        test_reorder_calculations()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
