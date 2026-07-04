import datetime
import threading
from pathlib import Path
from tkinter import messagebox


# Tables that have a direct retailer_id column — exported with WHERE retailer_id = %s
_RETAILER_ID_TABLES = [
    "core_productmaster",
    "core_suppliermaster",
    "core_customermaster",
    "core_invoicemaster",
    "core_purchasemaster",
    "core_salesinvoicemaster",
    "core_salesmaster",
    "core_returninvoicemaster",
    "core_returnpurchasemaster",
    "core_returnsalesinvoicemaster",
    "core_returnsalesmaster",
    "inventory_transaction",
    "retailer_request",
    "challan1",
    "customer_challan",
    "stock_issue_master",
    "stock_issue_detail",
    "core_backup",
]

# Tables linked to core_invoicemaster via invoice FK — exported by joining to retailer invoices
_INVOICE_PAYMENT_TABLES = [
    ("core_invoicepaid",        "ip_invoiceid_id",       "core_invoicemaster", "invoiceid"),
    ("core_salesinvoicepaid",   "sales_ip_invoice_no_id","core_salesinvoicemaster", "sales_invoice_no"),
    ("core_returnsalesinvoicepaid", "return_sales_ip_invoice_no_id", "core_returnsalesinvoicemaster", "return_sales_invoice_no"),
]

# Tables with no retailer_id that are shared/structural — exported in full
_SHARED_TABLES = [
    "core_invoiceseries",
    "retailer_users",
]


def _escape(val) -> str:
    """Escape a Python value to a safe SQL literal."""
    if val is None:
        return "NULL"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, datetime.datetime):
        return f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'"
    if isinstance(val, datetime.date):
        return f"'{val.strftime('%Y-%m-%d')}'"
    # String — escape backslash, single-quote, and NUL
    s = str(val).replace("\\", "\\\\").replace("'", "\\'").replace("\x00", "")
    return f"'{s}'"


def _write_table(f, conn, table: str, where_clause: str, params: tuple):
    """
    Fetch rows from `table` using `where_clause` and write INSERT statements to `f`.
    Skips silently if the table does not exist.
    """
    try:
        with conn.cursor() as cur:
            # Check table exists
            cur.execute("SHOW TABLES LIKE %s", (table,))
            if not cur.fetchone():
                return

            # Fetch column names
            cur.execute(f"SHOW COLUMNS FROM `{table}`")
            columns = [row[0] for row in cur.fetchall()]
            if not columns:
                return

            col_list = ", ".join(f"`{c}`" for c in columns)
            sql = f"SELECT {col_list} FROM `{table}`"
            if where_clause:
                sql += f" WHERE {where_clause}"

            cur.execute(sql, params)
            rows = cur.fetchall()

        if not rows:
            return

        f.write(f"\n-- Table: {table}\n")
        f.write(f"LOCK TABLES `{table}` WRITE;\n")

        for row in rows:
            values = ", ".join(_escape(v) for v in row)
            f.write(f"INSERT INTO `{table}` ({col_list}) VALUES ({values});\n")

        f.write(f"UNLOCK TABLES;\n")

    except Exception as e:
        f.write(f"-- WARNING: could not export {table}: {e}\n")


def create_database_backup(app, parent_widget=None, on_complete=None):
    """
    Creates a retailer-filtered SQL backup using PyMySQL.
    Only rows belonging to the logged-in retailer_id are exported.
    Saved to: Documents\MedicVista Backups\
    """
    import os
    documents = Path.home() / "Documents" / "MedicVista Backups"
    documents.mkdir(parents=True, exist_ok=True)
    backup_dir = documents

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    retailer_id = app.config_data.retailer_id
    db_name = app.config_data.db_name
    filename = f"backup_{db_name}_retailer{retailer_id}_{timestamp}.sql"
    filepath = backup_dir / filename

    def run_backup():
        try:
            import pymysql
            conn = pymysql.connect(
                host=app.config_data.db_host,
                port=app.config_data.db_port,
                user=app.config_data.db_user,
                password=app.config_data.db_password,
                database=db_name,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.Cursor,
                connect_timeout=10,
            )

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"-- MedicVista Retailer Backup\n")
                f.write(f"-- Database  : {db_name}\n")
                f.write(f"-- Retailer  : {retailer_id}\n")
                f.write(f"-- Generated : {datetime.datetime.now()}\n")
                f.write(f"-- NOTE: Contains ONLY data for retailer_id = {retailer_id}\n\n")
                f.write("SET FOREIGN_KEY_CHECKS=0;\n")
                f.write("SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO';\n")
                f.write("SET NAMES utf8mb4;\n\n")

                # 1. Tables with direct retailer_id column
                for table in _RETAILER_ID_TABLES:
                    _write_table(f, conn, table, "retailer_id = %s", (retailer_id,))

                # 2. Payment/child tables linked via FK to a parent that has retailer_id
                for child_table, fk_col, parent_table, parent_pk in _INVOICE_PAYMENT_TABLES:
                    where = (
                        f"`{fk_col}` IN "
                        f"(SELECT `{parent_pk}` FROM `{parent_table}` WHERE retailer_id = %s)"
                    )
                    _write_table(f, conn, child_table, where, (retailer_id,))

                # 3. Shared/structural tables — full export
                for table in _SHARED_TABLES:
                    _write_table(f, conn, table, "", ())

                f.write("\nSET FOREIGN_KEY_CHECKS=1;\n")

            conn.close()

            try:
                size_bytes = filepath.stat().st_size
                size_str = (
                    f"{size_bytes / 1024:.1f} KB"
                    if size_bytes < 1024 * 1024
                    else f"{size_bytes / (1024 * 1024):.2f} MB"
                )
            except Exception:
                size_str = "Unknown"

            try:
                app.db.log_backup(filename, str(filepath.absolute()), "Success", size_str)
            except Exception as ex:
                print(f"Failed to log backup to DB: {ex}")

            app.after(0, lambda: messagebox.showinfo(
                "Backup Successful",
                f"Retailer backup created successfully!\n\n"
                f"Retailer ID : {retailer_id}\n"
                f"File        : {filepath.absolute()}\n"
                f"Size        : {size_str}",
                parent=parent_widget,
            ))
            if on_complete:
                app.after(0, on_complete)

        except Exception as e:
            try:
                app.db.log_backup(filename, str(filepath.absolute()), "Failed", "0 KB")
            except Exception:
                pass
            if filepath.exists():
                filepath.unlink()
            app.after(0, lambda: messagebox.showerror(
                "Backup Failed",
                f"An error occurred during backup:\n{e}",
                parent=parent_widget,
            ))
            if on_complete:
                app.after(0, on_complete)

    thread = threading.Thread(target=run_backup)
    thread.daemon = True
    thread.start()
