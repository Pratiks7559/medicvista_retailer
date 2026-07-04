"""
Migration: Add retailer_id to core_productmaster, core_suppliermaster, core_customermaster
-------------------------------------------------------------------------------------------
Run this ONCE on your database.
"""

import pymysql
import sys

# ── Read DB config from config.ini automatically ──────────────────────────────
import configparser
from pathlib import Path

_cfg = configparser.ConfigParser()
_cfg_path = Path(__file__).parent / "config.ini"
if _cfg_path.exists():
    _cfg.read(_cfg_path)

DB_CONFIG = {
    'host':     _cfg.get("database", "host",     fallback="localhost"),
    'port': int(_cfg.get("database", "port",     fallback="3306")),
    'user':     _cfg.get("database", "user",     fallback="root"),
    'password': _cfg.get("database", "password", fallback=""),
    'database': _cfg.get("database", "name",     fallback="medicvista_retailer"),
    'charset':  'utf8mb4',
}


def _column_exists(cursor, table: str, column: str, db: str) -> bool:
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
    """, (db, table, column))
    return cursor.fetchone()[0] > 0


def _migrate_table(cursor, conn, table: str, db: str, step_prefix: str):
    print(f"\n{'='*60}")
    print(f"  Table: {table}")
    print(f"{'='*60}")

    if _column_exists(cursor, table, "retailer_id", db):
        print(f"  ✓ retailer_id already exists — skipping")
        return

    print(f"  [{step_prefix}.1] Adding retailer_id column...")
    cursor.execute(f"""
        ALTER TABLE `{table}`
        ADD COLUMN retailer_id BIGINT DEFAULT 1
    """)
    print(f"  ✓ Column added")

    print(f"  [{step_prefix}.2] Creating index...")
    cursor.execute(f"""
        CREATE INDEX idx_retailer_id_{table} ON `{table}`(retailer_id)
    """)
    print(f"  ✓ Index created")

    print(f"  [{step_prefix}.3] Setting existing rows to retailer_id = 1...")
    cursor.execute(f"""
        UPDATE `{table}` SET retailer_id = 1
        WHERE retailer_id IS NULL OR retailer_id = 0
    """)
    updated = cursor.rowcount
    print(f"  ✓ {updated} rows updated to retailer_id = 1")

    conn.commit()
    print(f"  ✓ Committed")


def migrate():
    print("=" * 60)
    print("  MedicVista — retailer_id Migration")
    print("=" * 60)
    print(f"  Host    : {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"  Database: {DB_CONFIG['database']}")
    print()

    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        db = DB_CONFIG['database']

        _migrate_table(cursor, conn, "core_productmaster",  db, "1")
        _migrate_table(cursor, conn, "core_suppliermaster", db, "2")
        _migrate_table(cursor, conn, "core_customermaster", db, "3")

        cursor.close()
        conn.close()

        print()
        print("=" * 60)
        print("  Migration complete!")
        print("=" * 60)
        print("  ✓ core_productmaster  — retailer_id ready")
        print("  ✓ core_suppliermaster — retailer_id ready")
        print("  ✓ core_customermaster — retailer_id ready")
        print()
        print("  All existing rows assigned to retailer_id = 1")
        print("  Restart the app now.")
        print()

    except pymysql.Error as e:
        print(f"\n  ❌ DB Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n  ❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    print()
    print("This will add retailer_id column to:")
    print("  - core_productmaster")
    print("  - core_suppliermaster")
    print("  - core_customermaster")
    print()
    confirm = input("Proceed? (yes/no): ").strip().lower()
    if confirm in ('yes', 'y'):
        migrate()
    else:
        print("Migration cancelled.")
