# MedicVista Retailer Desktop

Tkinter desktop application for retailer stores that connects to the same cloud MySQL database used by the existing MedicVista ERP.

## What This Folder Contains

- `main.py` starts the desktop app.
- `config.example.ini` shows the required cloud DB and retailer settings.
- `app/db.py` centralizes all database access and retailer filtering.
- `app/sync.py` polls `retailer_request` every 1 minute.
- `app/ui/screens.py` contains dashboard, table screens, request inbox, and settings.
- `logs/app.log` stores runtime and sync errors.

## Setup

1. Copy this folder to the retailer machine.
2. Install Python 3.10+.
3. Open terminal inside `Medicvist_retailer`.
4. Install requirements:

```powershell
pip install -r requirements.txt
```

5. Copy `config.example.ini` to `config.ini`.
6. Edit `config.ini`:

```ini
[database]
host = your-cloud-mysql-host
port = 3306
name = pharma_db
user = retailer_user
password = change-me

[retailer]
retailer_id = 1
store_name = Retailer Store 1

[sync]
poll_seconds = 60
```

7. Run:

```powershell
python main.py
```

## Required ERP Database Changes

This app expects the cloud ERP database to have retailer isolation.

Required table:

```sql
CREATE TABLE retailer_request (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    retailer_id BIGINT NOT NULL,
    request_type VARCHAR(20) NOT NULL,
    reference_id BIGINT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME NULL,
    remarks TEXT NULL
);
```

Required request types:

- `STOCK`
- `PURCHASE`
- `SALE`

Required status values:

- `Pending`
- `Processed`
- `Failed`

Retailer-owned ERP tables should have `retailer_id`, especially:

- `core_invoicemaster`
- `core_purchasemaster`
- `core_salesinvoicemaster`
- `core_salesmaster`
- `batch_inventory_cache` if stock is retailer-specific
- `inventory_transaction` if stock movement is retailer-specific

If a required table does not have `retailer_id`, the desktop app shows an error instead of leaking another retailer's data.

## Keyboard Shortcuts

- `F1` Dashboard
- `F2` Product Master
- `F3` Purchase
- `F4` Sales
- `Ctrl+I` Invoice
- `F5` Stock Management and Sync Now
- `F6` Reports
- `F7` Retailer Requests
- `F8` Settings
- `ESC` Back to Dashboard, then close
- `Enter` Next field or open selected row in grid
- `Shift+Enter` Previous field
- `Ctrl+F` Search
- `Ctrl+R` Refresh current screen
- `Ctrl+S` Save or mark selected request processed where supported
- `Ctrl+N` New record placeholder
- `Ctrl+E` Edit record placeholder
- `Ctrl+D` Delete record placeholder
- `Ctrl+P` Print/export placeholder
- Arrow keys navigate grids
- `Delete` triggers delete action placeholder

## Sync Behavior

- The app polls `retailer_request` every `poll_seconds`.
- Only rows matching `config.ini` `retailer_id` are loaded.
- Pending requests are processed:
  - `STOCK` refreshes Stock Management.
  - `PURCHASE` refreshes Purchase and Reports.
  - `SALE` refreshes Sales and Reports.
- Successful requests are marked `Processed`.
- Failed requests are marked `Failed` with error text in `remarks`.

## How To Show AI The Existing ERP UI And DB

Give the AI these paths from the existing ERP:

- UI layout: `pharmamgmt/templates/base.html`
- Sidebar/menu: `pharmamgmt/templates/sidebar.html`
- Main CSS: `pharmamgmt/static/css/global.css`
- Dashboard CSS: `pharmamgmt/static/css/dashboard.css`
- Product UI: `pharmamgmt/templates/products/`
- Purchase UI: `pharmamgmt/templates/purchases/`
- Sales UI: `pharmamgmt/templates/sales/`
- Inventory UI: `pharmamgmt/templates/inventory/`
- Reports UI: `pharmamgmt/templates/reports/`
- DB models: `pharmamgmt/core/models.py`
- Routes: `pharmamgmt/core/urls.py`

For database structure, give AI:

```powershell
python pharmamgmt/manage.py showmigrations
python pharmamgmt/manage.py sqlmigrate core <migration_number>
```

Or export schema from MySQL:

```powershell
mysqldump -h HOST -u USER -p --no-data DB_NAME > medicvista_schema.sql
```

Do not share real DB passwords with AI.
