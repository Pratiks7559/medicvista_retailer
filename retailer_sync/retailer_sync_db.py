"""
retailer_sync_db.py
-------------------
REDIRECT TO MYSQL VERSION

This module now uses MySQL instead of SQLite.
All imports are redirected to retailer_sync_db_mysql.py

Old SQLite version backed up at: retailer_sync_db_sqlite_backup.py
"""

# Import MySQL-based version
from retailer_sync_db_mysql import RetailerCacheDB

__all__ = ['RetailerCacheDB']
