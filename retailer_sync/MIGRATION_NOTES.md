# Migration from SQLite to MySQL

## Issue Fixed
**Error:** `sqlite3.OperationalError: no such table: pending_status_updates`

## Changes Made

### 1. Removed SQLite Dependency
- **Old:** `retailer_sync_db.py` used SQLite for offline queue
- **New:** `retailer_sync_db_mysql.py` uses MySQL for offline queue

### 2. Database Location
- **Table:** `retailer_pending_status_updates`
- **Database:** `medicvista_retailer` (NOT `pharma_db`)
- **Config:** Loaded from `config.ini` [database] section

### 3. Files Changed

#### New Files:
- `retailer_sync_db_mysql.py` - MySQL-based implementation
- `retailer_sync_db_sqlite_backup.py` - Backup of old SQLite version
- `migrations/001_create_pending_status_table.sql` - Table creation script

#### Modified Files:
- `retailer_sync_db.py` - Now redirects to MySQL version
- `retailer_sync_runner.py` - Uses MySQL config from config.ini

### 4. Table Structure
```sql
CREATE TABLE retailer_pending_status_updates (
    id BIGINT NOT NULL AUTO_INCREMENT,
    request_id BIGINT NOT NULL,
    new_status VARCHAR(30) NOT NULL,
    queued_at DATETIME NOT NULL,
    attempt_count INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    KEY idx_queued_at (queued_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 5. Configuration
The system reads MySQL config from `config.ini`:

```ini
[database]
host = localhost
port = 3306
name = medicvista_retailer
user = root
password = Pratik@123
```

## Why medicvista_retailer (not pharma_db)?

- `medicvista_retailer` - Retailer's own app database (stores local data)
- `pharma_db` - Django ERP database (only for retailer_request table sync)

The `pending_status_updates` table is part of the retailer sync system's offline queue, so it belongs in `medicvista_retailer`.

## Testing

1. Ensure MySQL is running
2. Verify `medicvista_retailer` database exists
3. Run the migration script (optional - table auto-creates):
   ```bash
   mysql -u root -p medicvista_retailer < migrations/001_create_pending_status_table.sql
   ```
4. Start the retailer app - sync system will now use MySQL

## Rollback (if needed)
If you need to revert to SQLite (not recommended):
1. Restore `retailer_sync_db_sqlite_backup.py` to `retailer_sync_db.py`
2. Revert changes in `retailer_sync_runner.py`
3. Delete/move `retailer_sync_db_mysql.py`
