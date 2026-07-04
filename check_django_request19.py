"""
Check Django database (pharma_db) for request #19 status and CSV upload
"""

import mysql.connector

print("=" * 70)
print("DJANGO DATABASE CHECK - Request #19")
print("=" * 70)

try:
    conn = mysql.connector.connect(
        host='localhost',
        port=3306,
        database='pharma_db',
        user='root',
        password='Pratik@123'
    )
    
    if conn.is_connected():
        print("\n[OK] Connected to Django database (pharma_db)")
        cursor = conn.cursor(dictionary=True)
        
        # Check retailer_report_request table
        print("\n1. Checking core_retailerreportrequest table...")
        cursor.execute("""
            SELECT request_id, retailer_id, request_type, from_date, to_date,
                   status, created_at, completed_at
            FROM core_retailerreportrequest
            WHERE request_id = 19
        """)
        req = cursor.fetchone()
        
        if req:
            print(f"   Request #19 found:")
            print(f"     Retailer ID: {req['retailer_id']}")
            print(f"     Type: {req['request_type']}")
            print(f"     Status: {req['status']}")
            print(f"     From: {req['from_date']} To: {req['to_date']}")
            print(f"     Created: {req['created_at']}")
            print(f"     Completed: {req['completed_at']}")
        else:
            print("   [WARNING] Request #19 NOT FOUND in Django database!")
        
        # Check CSV upload table
        print("\n2. Checking core_retailercsvupload table...")
        cursor.execute("""
            SELECT id, request_id, retailer_id, file_name, file_size_kb,
                   request_type, uploaded_at, row_count
            FROM core_retailercsvupload
            WHERE request_id = 19
        """)
        upload = cursor.fetchone()
        
        if upload:
            print(f"   CSV Upload found:")
            print(f"     Upload ID: {upload['id']}")
            print(f"     File: {upload['file_name']}")
            print(f"     Size: {upload['file_size_kb']} KB")
            print(f"     Rows: {upload['row_count']}")
            print(f"     Uploaded: {upload['uploaded_at']}")
        else:
            print("   [WARNING] CSV upload NOT FOUND for request #19!")
        
        # Check all recent requests
        print("\n3. Recent requests (last 5)...")
        cursor.execute("""
            SELECT r.request_id, r.retailer_id, rm.retailer_name, r.request_type,
                   r.status, r.created_at,
                   COUNT(c.id) as csv_count
            FROM core_retailerreportrequest r
            LEFT JOIN core_retailermaster rm ON rm.retailer_id = r.retailer_id
            LEFT JOIN core_retailercsvupload c ON c.request_id = r.request_id
            GROUP BY r.request_id
            ORDER BY r.created_at DESC
            LIMIT 5
        """)
        recent = cursor.fetchall()
        
        for row in recent:
            has_csv = "✓" if row['csv_count'] > 0 else "✗"
            print(f"   #{row['request_id']} | {row['retailer_name']} | {row['request_type']} | {row['status']} | CSV: {has_csv}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 70)
        print("DIAGNOSIS:")
        print("=" * 70)
        
        if req and upload:
            print("[OK] Request exists + CSV uploaded")
            print("→ CSV should be visible in Django UI")
        elif req and not upload:
            print("[PROBLEM] Request exists but NO CSV uploaded")
            print("→ Auto-generate may not have uploaded CSV")
            print("→ Check retailer_sync.log for upload errors")
        elif not req:
            print("[PROBLEM] Request #19 NOT in Django database")
            print("→ Request may have been deleted or not synced")
        
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
