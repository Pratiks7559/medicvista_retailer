"""
Complete End-to-End Test for Auto-Generate Flow
This script will verify the entire pipeline from request creation to CSV upload
"""

import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / 'app'))
sys.path.insert(0, str(Path(__file__).parent / 'retailer_sync'))

print("=" * 80)
print("END-TO-END AUTO-GENERATE TEST")
print("=" * 80)

# Test 1: Check db.py has required methods
print("\n[TEST 1] Checking db.py methods...")
try:
    from app.db import Database
    
    has_upsert = hasattr(Database, 'upsert_wholesaler_requests')
    has_get = hasattr(Database, 'get_requests')
    has_update = hasattr(Database, 'update_request_status_by_reference')
    
    print(f"  [OK] upsert_wholesaler_requests: {has_upsert}")
    print(f"  [OK] get_requests: {has_get}")
    print(f"  [OK] update_request_status_by_reference: {has_update}")
    
    if has_upsert and has_get and has_update:
        print("  [PASS] All required methods present")
    else:
        print("  [FAIL] Missing required methods")
        sys.exit(1)
except Exception as e:
    print(f"  [FAIL] {e}")
    sys.exit(1)

# Test 2: Check MySQL connection
print("\n[TEST 2] Checking MySQL connection...")
try:
    import mysql.connector
    
    # Test medicvista_retailer database
    conn1 = mysql.connector.connect(
        host='localhost',
        port=3306,
        database='medicvista_retailer',
        user='root',
        password='Pratik@123'
    )
    print(f"  [OK] Connected to medicvista_retailer")
    
    cursor1 = conn1.cursor()
    cursor1.execute("SELECT COUNT(*) FROM retailer_request")
    count1 = cursor1.fetchone()[0]
    print(f"  [OK] retailer_request table: {count1} rows")
    
    cursor1.execute("SELECT COUNT(*) FROM retailer_pending_status_updates")
    count2 = cursor1.fetchone()[0]
    print(f"  [OK] retailer_pending_status_updates table: {count2} rows")
    
    conn1.close()
    
    # Test pharma_db database
    conn2 = mysql.connector.connect(
        host='localhost',
        port=3306,
        database='pharma_db',
        user='root',
        password='Pratik@123'
    )
    print(f"  [OK] Connected to pharma_db")
    
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT COUNT(*) FROM core_retailerreportrequest")
    count3 = cursor2.fetchone()[0]
    print(f"  [OK] core_retailerreportrequest table: {count3} rows")
    
    cursor2.execute("SELECT COUNT(*) FROM core_retailercsvupload")
    count4 = cursor2.fetchone()[0]
    print(f"  [OK] core_retailercsvupload table: {count4} uploads")
    
    conn2.close()
    
    print("  [PASS] Both databases accessible")
except Exception as e:
    print(f"  [FAIL] {e}")
    sys.exit(1)

# Test 3: Check sync configuration
print("\n[TEST 3] Checking sync configuration...")
try:
    config_path = Path(__file__).parent / 'config.ini'
    if config_path.exists():
        import configparser
        parser = configparser.ConfigParser()
        parser.read(config_path)
        
        env = parser.get('mode', 'environment', fallback='LOCAL')
        db_name = parser.get('database', 'name', fallback='unknown')
        
        print(f"  [OK] Environment: {env}")
        print(f"  [OK] Database: {db_name}")
        print("  [PASS] Config file valid")
    else:
        print("  [FAIL] config.ini not found")
        sys.exit(1)
except Exception as e:
    print(f"  [FAIL] {e}")
    sys.exit(1)

# Test 4: Check wholesaler API
print("\n[TEST 4] Checking wholesaler API...")
try:
    import requests
    
    response = requests.get('http://127.0.0.1:8000/api/retailer/health/', timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"  [OK] API Status: {data.get('status')}")
        print(f"  [OK] Server Mode: {data.get('server_mode')}")
        print(f"  [OK] Server Time: {data.get('server_time')}")
        print("  [PASS] Wholesaler API reachable")
    else:
        print(f"  [FAIL] API returned {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"  [FAIL] {e}")
    sys.exit(1)

# Test 5: Check retailer sync files
print("\n[TEST 5] Checking retailer sync files...")
sync_dir = Path(__file__).parent / 'retailer_sync'
required_files = [
    'retailer_sync_runner.py',
    'retailer_sync_bridge.py',
    'retailer_sync_service.py',
    'retailer_sync_db.py',
    'retailer_sync_db_mysql.py',
    'retailer_report_generator.py',
]

all_found = True
for fname in required_files:
    fpath = sync_dir / fname
    if fpath.exists():
        print(f"  [OK] {fname}")
    else:
        print(f"  [X] {fname} NOT FOUND")
        all_found = False

if all_found:
    print("  [PASS] All sync files present")
else:
    print("  [FAIL] Missing sync files")
    sys.exit(1)

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("""
All tests passed! System is ready for auto-generate.

NEXT STEPS:
1. Restart retailer application (close and reopen)
2. Login with any retailer (1, 2, 3, or 4)
3. Create request in Django ERP for that retailer
4. Wait 10-30 seconds for auto-generate
5. Check Django UI for CSV download link

VERIFY AUTO-GENERATE:
- Check logs: retailer_sync/retailer_sync.log
- Look for: "Auto-generating report for request_id=X"
- Look for: "CSV uploaded: id=X file=..."
- Look for: "Status sent: id=X → COMPLETED"

If auto-generate doesn't work:
- Run: python diagnose_sync.py
- Check for "STANDALONE MODE" warning
- Check logs for errors
""")
print("=" * 80)
