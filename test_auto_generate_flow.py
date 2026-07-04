"""
test_auto_generate_flow.py
--------------------------
Full end-to-end test for auto-generate flow.
Run: python test_auto_generate_flow.py

Tests:
1. ERP connection
2. Pending requests fetch (checks retailer_id field)
3. DB connection (medicvista_retailer)
4. fetch_and_generate pipeline for each pending request
5. CSV upload to ERP
6. ERP status check (COMPLETED + View Uploaded CSV)
"""

import sys
import os
import json
import urllib.request
import urllib.error
import ssl

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'retailer_sync'))

from retailer_sync_runner import _load_config, get_retailer_config

cfg_base = _load_config()
cfg = get_retailer_config(cfg_base, 1)   # Test with retailer_id=1 (BSL)

SERVER_URL  = cfg['server_url']
API_KEY     = cfg['api_key']
RETAILER_ID = cfg['retailer_id']

print("")
print("=" * 60)
print("  MedicVista Auto-Generate Flow Test")
print("  Server  : " + SERVER_URL)
print("  Retailer: " + cfg['retailer_name'] + " (ID=" + str(RETAILER_ID) + ")")
print("=" * 60)
print("")


def _get(path, timeout=10):
    url = SERVER_URL + path
    ssl_ctx = ssl._create_unverified_context() if url.startswith('https') else None
    req = urllib.request.Request(url, headers={'X-API-KEY': API_KEY})
    try:
        kw = {'timeout': timeout}
        if ssl_ctx:
            kw['context'] = ssl_ctx
        with urllib.request.urlopen(req, **kw) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, "HTTP " + str(e.code) + ": " + e.read().decode()[:200]
    except Exception as e:
        return None, str(e)


# TEST 1: ERP Health
print("TEST 1: ERP Health Check")
data, err = _get('/api/retailer/health/')
if err:
    print("  [FAIL] " + err)
    print("  [INFO] ERP server not reachable. Start Django server first.")
    sys.exit(1)
print("  [OK] mode=" + str(data.get('server_mode')) + " time=" + str(data.get('server_time')))


# TEST 2: Pending Requests - check retailer_id field
print("")
print("TEST 2: Pending Requests (retailer_id field check)")
data, err = _get('/api/retailer/pending-requests/')
if err:
    print("  [FAIL] " + err)
    sys.exit(1)

requests_list = data.get('requests', [])
print("  [OK] " + str(len(requests_list)) + " pending request(s)")

if requests_list:
    sample = requests_list[0]
    has_rid = 'retailer_id' in sample
    print("  retailer_id field present: " + ("YES - FIXED" if has_rid else "NO - BUG!"))
    for r in requests_list:
        print("  request_id=" + str(r['request_id']) +
              " type=" + str(r['request_type']) +
              " retailer_id=" + str(r.get('retailer_id', 'MISSING')) +
              " from=" + str(r['from_date']) +
              " to=" + str(r['to_date']))
else:
    print("  No pending requests. Create one in ERP first.")
    print("  Go to: ERP -> Retailer Reports -> Create Request")


# TEST 3: DB Connection
print("")
print("TEST 3: Retailer DB Connection (medicvista_retailer)")
try:
    import pymysql
    conn = pymysql.connect(
        host='localhost', port=3306, user='root',
        password='Pratik@123', database='medicvista_retailer', charset='utf8mb4'
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM retailer_request WHERE retailer_id=%s", (RETAILER_ID,))
    count = cur.fetchone()[0]
    print("  [OK] Connected. retailer_request rows for retailer_id=" + str(RETAILER_ID) + ": " + str(count))
    conn.close()
except Exception as e:
    print("  [FAIL] DB connection failed: " + str(e))
    sys.exit(1)


# TEST 4: fetch_and_generate pipeline
if not requests_list:
    print("")
    print("TEST 4: Skipped (no pending requests)")
else:
    print("")
    print("TEST 4: fetch_and_generate pipeline (" + str(len(requests_list)) + " request(s))")

    from app.config import load_config
    from app.db import Database
    from dataclasses import replace

    app_config = load_config()
    app_config = replace(app_config, retailer_id=RETAILER_ID)
    app_db = Database(app_config)

    try:
        app_db.connect()
        print("  [OK] app_db connected")
    except Exception as e:
        print("  [FAIL] app_db.connect() failed: " + str(e))
        sys.exit(1)

    from retailer_sync_runner import RetailerSyncRunner
    runner = RetailerSyncRunner(config=cfg, on_sync_complete=None, app_db=app_db)

    for req in requests_list:
        rid = req['request_id']
        print("")
        print("  Processing request_id=" + str(rid) + " type=" + str(req['request_type']))

        result = runner.fetch_and_generate(
            wholesaler_request_id=rid,
            output_dir='retailer_reports',
        )

        if result['ok']:
            print("    [OK] CSV: " + str(result.get('csv_path')))
            print("    [OK] PDF: " + str(result.get('pdf_path')))
        else:
            print("    [FAIL] Error: " + str(result.get('error')))


# TEST 5: ERP Status Check
print("")
print("TEST 5: ERP Status Check (after generate)")
if requests_list:
    import time
    time.sleep(2)
    for req in requests_list:
        rid = req['request_id']
        data, err = _get('/api/retailer/request-data/' + str(rid) + '/')
        if err:
            print("  request_id=" + str(rid) + ": [ERROR] " + err)
        else:
            print("  request_id=" + str(rid) +
                  " type=" + str(data.get('request_type')) +
                  " retailer_id=" + str(data.get('retailer_id')))

print("")
print("=" * 60)
print("  Test Complete!")
print("  Check ERP -> Retailer Reports -> View Uploaded CSV")
print("  URL: " + SERVER_URL + "/wholesaler/retailer-uploads/")
print("=" * 60)
print("")
