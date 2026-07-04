"""
Diagnostic script - Check why auto-generate is not working
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / 'app'))
sys.path.insert(0, str(Path(__file__).parent / 'retailer_sync'))

print("=" * 70)
print("RETAILER SYNC DIAGNOSTIC")
print("=" * 70)

# Test 1: Check db.py Database class
print("\n1. Checking db.py Database class...")
try:
    from app.db import Database as DB_Database
    print("   [OK] Imported from app.db")
    print(f"   Has upsert_wholesaler_requests: {hasattr(DB_Database, 'upsert_wholesaler_requests')}")
    print(f"   Has get_requests: {hasattr(DB_Database, 'get_requests')}")
    print(f"   Has update_request_status_by_reference: {hasattr(DB_Database, 'update_request_status_by_reference')}")
except Exception as e:
    print(f"   [ERROR] {e}")

# Test 2: Check database.py Database class
print("\n2. Checking database.py Database class...")
try:
    from app.database import Database as Simple_Database
    print("   [OK] Imported from app.database")
    print(f"   Has upsert_wholesaler_requests: {hasattr(Simple_Database, 'upsert_wholesaler_requests')}")
    print(f"   Has get_requests: {hasattr(Simple_Database, 'get_requests')}")
except Exception as e:
    print(f"   [ERROR] {e}")

# Test 3: Check MySQL connection
print("\n3. Testing MySQL connection...")
try:
    import mysql.connector
    conn = mysql.connector.connect(
        host='localhost',
        port=3306,
        database='medicvista_retailer',
        user='root',
        password='Pratik@123'
    )
    if conn.is_connected():
        print("   [OK] MySQL connected")
        cursor = conn.cursor()
        
        # Check retailer_request table
        cursor.execute("SELECT COUNT(*) FROM retailer_request")
        count = cursor.fetchone()[0]
        print(f"   retailer_request table: {count} rows")
        
        # Check latest request
        cursor.execute("""
            SELECT id, reference_id, retailer_id, status, created_at 
            FROM retailer_request 
            ORDER BY id DESC LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            print(f"   Latest request: ID={row[0]}, Ref={row[1]}, Retailer={row[2]}, Status={row[3]}, Created={row[4]}")
        
        cursor.close()
        conn.close()
except Exception as e:
    print(f"   [ERROR] {e}")

# Test 4: Check wholesaler API
print("\n4. Testing wholesaler API...")
try:
    import requests
    response = requests.get('http://127.0.0.1:8000/api/retailer/health/', timeout=5)
    if response.status_code == 200:
        print(f"   [OK] Wholesaler API responding: {response.json()}")
    else:
        print(f"   [WARNING] API returned {response.status_code}")
except Exception as e:
    print(f"   [ERROR] {e}")

# Test 5: Check sync log for errors
print("\n5. Checking sync log...")
try:
    log_path = Path(__file__).parent / 'retailer_sync' / 'retailer_sync.log'
    if log_path.exists():
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            last_50 = lines[-50:] if len(lines) > 50 else lines
            
            # Count key messages
            cached_count = sum(1 for line in last_50 if 'Cached' in line and 'in memory' in line)
            mysql_count = sum(1 for line in last_50 if 'Wrote' in line and 'into retailer MySQL' in line)
            auto_gen_count = sum(1 for line in last_50 if 'Auto-generating' in line)
            
            print(f"   Last 50 log lines analysis:")
            print(f"     - Cached in memory: {cached_count} times")
            print(f"     - Written to MySQL: {mysql_count} times")
            print(f"     - Auto-generate attempts: {auto_gen_count} times")
            
            if cached_count > 0 and mysql_count == 0:
                print("   [WARNING] Running in STANDALONE MODE - app_db not connected!")
            elif mysql_count > 0:
                print("   [OK] MySQL mode detected")
    else:
        print("   [WARNING] Log file not found")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n" + "=" * 70)
print("DIAGNOSIS SUMMARY")
print("=" * 70)

print("""
If you see "Cached in memory" but NO "Wrote into retailer MySQL":
  → app_db is None or missing upsert_wholesaler_requests method
  → Auto-generate will NOT run (standalone mode)
  
Fix:
  1. Make sure retailer app uses db.py Database class (not database.py)
  2. Check application.py imports: from .db import Database
  3. Restart the retailer application
  
Expected in logs when working correctly:
  - "Wrote X new request(s) into retailer MySQL"
  - "Auto-generating report for request_id=X"
  - "Auto-generated report SUCCESS"
""")
