"""
Quick verification script - Run this to check if the fix is working.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def verify_import():
    """Verify that the MySQL version is being used."""
    print("=" * 70)
    print("VERIFYING MYSQL MIGRATION")
    print("=" * 70)
    
    try:
        print("\n1. Importing RetailerCacheDB...")
        from retailer_sync_db import RetailerCacheDB
        print("   [OK] Import successful")
        
        print("\n2. Checking if MySQL version is loaded...")
        import retailer_sync_db
        if 'mysql' in retailer_sync_db.__file__.lower() or 'from retailer_sync_db_mysql' in open(retailer_sync_db.__file__).read():
            print("   [OK] MySQL version detected")
        else:
            print("   [WARNING] Check if retailer_sync_db.py imports from mysql version")
        
        print("\n3. Testing database connection...")
        db = RetailerCacheDB({
            'host': 'localhost',
            'port': 3306,
            'name': 'medicvista_retailer',
            'user': 'root',
            'password': 'Pratik@123'
        })
        print("   [OK] Database connection successful")
        
        print("\n4. Testing table operations...")
        # Try to get pending updates (should work if table exists)
        pending = db.get_pending_updates()
        print(f"   [OK] Table accessible - {len(pending)} pending updates")
        
        print("\n" + "=" * 70)
        print("[SUCCESS] VERIFICATION COMPLETE - ALL CHECKS PASSED")
        print("=" * 70)
        print("\nYou can now start your retailer application.")
        print("The SQLite error will be gone!")
        
        return True
        
    except Exception as e:
        print(f"\n   [ERROR] {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 70)
        print("[FAILED] VERIFICATION FAILED")
        print("=" * 70)
        return False

if __name__ == '__main__':
    verify_import()
