from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterable

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError:  # pragma: no cover - handled at runtime for client installs
    pymysql = None
    DictCursor = None


class DatabaseError(RuntimeError):
    pass


class RetailerSchemaError(DatabaseError):
    pass


class Database:
    def __init__(self, config):
        self.config = config
        self._conn = None
        self._lock = __import__('threading').Lock()   # serialise multi-thread access
        self._columns_cache: dict[tuple[str, str], bool] = {}
        self._tables_cache: dict[str, bool] = {}

    def connect(self):
        if pymysql is None:
            raise DatabaseError("PyMySQL is not installed. Run: pip install -r requirements.txt")
        if not self.config.is_ready:
            raise DatabaseError("config.ini is missing database settings or retailer_id.")

        if self._conn:
            try:
                self._conn.ping(reconnect=True)
                # Verify the connection is truly alive with a lightweight check
                if self._conn.open:
                    return self._conn
            except Exception:
                pass
            # Connection is broken — discard it and reconnect fresh
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

        try:
            # First try connecting without a database to see if it exists
            temp_conn = pymysql.connect(
                host=self.config.db_host,
                port=self.config.db_port,
                user=self.config.db_user,
                password=self.config.db_password,
                charset="utf8mb4",
                connect_timeout=8,
            )
            with temp_conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.config.db_name}`")
            temp_conn.close()

            self._conn = pymysql.connect(
                host=self.config.db_host,
                port=self.config.db_port,
                user=self.config.db_user,
                password=self.config.db_password,
                database=self.config.db_name,
                charset="utf8mb4",
                cursorclass=DictCursor,
                autocommit=False,
                connect_timeout=8,
                read_timeout=30,
                write_timeout=30,
            )
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            raise DatabaseError(f"Could not connect to MySQL: {e}")

        return self._conn

    @contextmanager
    def cursor(self):
        """Context manager for database cursor with optimized connection handling."""
        with self._lock:
            conn = self.connect()
            cur = conn.cursor()
            try:
                yield cur
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()

    def query(self, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        """Execute SELECT query with automatic error handling."""
        try:
            with self.cursor() as cur:
                cur.execute(sql, tuple(params))
                return list(cur.fetchall())
        except Exception as e:
            logging.error(f"Query error: {sql[:100]}... | {e}")
            return []

    def execute(self, sql: str, params: Iterable[Any] = ()) -> int:
        """Execute INSERT/UPDATE/DELETE with automatic error handling."""
        try:
            with self.cursor() as cur:
                return cur.execute(sql, tuple(params))
        except Exception as e:
            logging.error(f"Execute error: {sql[:100]}... | {e}")
            return 0

    def test_connection(self) -> str:
        row = self.query("SELECT NOW() AS server_time")[0]
        return str(row["server_time"])

    def table_exists(self, table: str) -> bool:
        if table not in self._tables_cache:
            rows = self.query("SHOW TABLES LIKE %s", (table,))
            self._tables_cache[table] = bool(rows)
        return self._tables_cache[table]

    def column_exists(self, table: str, column: str) -> bool:
        key = (table, column)
        if key not in self._columns_cache:
            if not self.table_exists(table):
                return False
            safe_table = table.replace("`", "")
            rows = self.query(f"SHOW COLUMNS FROM `{safe_table}` LIKE %s", (column,))
            self._columns_cache[key] = bool(rows)
        return self._columns_cache[key]

    def retailer_where(self, table: str, alias: str | None = None, required: bool = True) -> tuple[str, list[Any]]:
        try:
            if self.column_exists(table, "retailer_id"):
                prefix = f"{alias}." if alias else ""
                return f" AND {prefix}retailer_id = %s", [self.config.retailer_id]
        except:
            pass

        if required:
            return " AND 0=1", [] # Return empty result if required but table/column missing
        return "", []

    def fetch_dashboard(self, fy_start: str = "", fy_end: str = "") -> dict[str, Any]:
        rid = self.config.retailer_id
        products = self._safe_count("core_productmaster", required=False)
        low_stock, out_stock, total_value = 0, 0, 0.0
        try:
            if self.table_exists("inventory_transaction"):
                date_filter = ""
                params = [rid]
                if fy_start and fy_end:
                    date_filter = " AND DATE(t.transaction_date) BETWEEN %s AND %s"
                    params.extend([fy_start, fy_end])
                rows = self.query(
                    f"""SELECT
                        COUNT(DISTINCT t.product_id) AS total,
                        COALESCE(SUM(CASE
                            WHEN t.transaction_type IN ('PURCHASE') THEN t.quantity * t.rate
                            WHEN t.transaction_type IN ('PURCHASE_RETURN','REVERT_PURCHASE_RETURN','REVERT_PURCHASE') THEN -(t.quantity * t.rate)
                            WHEN t.transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') THEN -(t.quantity * t.rate)
                            WHEN t.transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') THEN t.quantity * t.rate
                            ELSE 0 END), 0) AS val
                       FROM inventory_transaction t WHERE t.retailer_id=%s{date_filter}""",
                    params)
                if rows:
                    total_value = float(rows[0].get("val", 0))
        except Exception:
            pass
        return {
            "products":  products,
            "value":     total_value,
            "low_stock": low_stock,
            "out_stock": out_stock,
        }

    def _safe_count(self, table: str, required: bool) -> int:
        try:
            if not self.table_exists(table): return 0
            where, params = self.retailer_where(table, required=required)
            row = self.query(f"SELECT COUNT(*) AS total FROM `{table}` WHERE 1=1{where}", params)
            return int(row[0]["total"]) if row else 0
        except Exception:
            return 0

    def _safe_sum_stock(self) -> float:
        """Legacy method - batch_inventory_cache table removed. Returns 0."""
        return 0.0

    def _safe_pending_requests(self) -> int:
        try:
            if not self.table_exists("retailer_request"):
                return 0
            row = self.query(
                """
                SELECT COUNT(*) AS total
                FROM retailer_request
                WHERE retailer_id = %s AND UPPER(status) = 'PENDING'
                """,
                (self.config.retailer_id,),
            )
            return int(row[0]["total"]) if row else 0
        except Exception:
            return 0

    def fetch_products(self, search: str = "") -> list[dict[str, Any]]:
        if not self.table_exists("core_productmaster"): return []
        params: list[Any] = []
        where = ""
        if search:
            where = "WHERE product_name LIKE %s OR product_company LIKE %s OR product_barcode LIKE %s"
            term = f"%{search}%"
            params = [term, term, term]
        return self.query(
            f"""
            SELECT productid, product_name, product_company, product_packing,
                   product_category, product_hsn, product_hsn_percent, product_barcode, product_salt
            FROM core_productmaster
            {where}
            ORDER BY product_name
            LIMIT 500
            """,
            params,
        )

    def fetch_stock(self, search: str = "") -> list[dict[str, Any]]:
        """Batch-wise stock report from inventory_transaction table."""
        if not self.table_exists("inventory_transaction"):
            self._ensure_inventory_transaction_table()
        rid = self.config.retailer_id
        search_clause = ""
        params: list[Any] = [rid]
        if search:
            search_clause = " AND (p.product_name LIKE %s OR p.product_company LIKE %s OR t.batch_no LIKE %s)"
            term = f"%{search}%"
            params += [term, term, term]
        rows = self.query(
            f"""
            SELECT p.productid, p.product_name, p.product_company, t.batch_no,
                   t.expiry_date,
                   COALESCE(SUM(CASE
                       WHEN t.transaction_type IN ('PURCHASE') THEN t.quantity
                       WHEN t.transaction_type IN ('PURCHASE_RETURN','REVERT_PURCHASE_RETURN','REVERT_PURCHASE') THEN -t.quantity
                       WHEN t.transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') THEN -t.quantity
                       WHEN t.transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') THEN t.quantity
                       ELSE 0 END), 0) AS current_stock,
                   COALESCE(SUM(CASE
                       WHEN t.transaction_type IN ('PURCHASE') THEN t.free_quantity
                       WHEN t.transaction_type IN ('PURCHASE_RETURN','REVERT_PURCHASE_RETURN','REVERT_PURCHASE') THEN -t.free_quantity
                       WHEN t.transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') THEN -t.free_quantity
                       WHEN t.transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') THEN t.free_quantity
                       ELSE 0 END), 0) AS current_free_qty,
                   COALESCE(MAX(t.mrp), 0) AS mrp,
                   COALESCE(MAX(t.rate), 0) AS purchase_rate,
                   CASE 
                       WHEN STR_TO_DATE(CONCAT('01-', t.expiry_date), '%d-%m-%Y') < CURDATE() THEN 'expired'
                       WHEN STR_TO_DATE(CONCAT('01-', t.expiry_date), '%d-%m-%Y') < DATE_ADD(CURDATE(), INTERVAL 3 MONTH) THEN 'expiring_soon'
                       ELSE 'valid'
                   END AS expiry_status
            FROM inventory_transaction t
            JOIN core_productmaster p ON p.productid = t.product_id
            WHERE t.retailer_id = %s{search_clause}
            GROUP BY p.productid, p.product_name, p.product_company, t.batch_no, t.expiry_date
            HAVING current_stock > 0 OR current_free_qty > 0
            ORDER BY p.product_name, t.expiry_date
            LIMIT 500
            """,
            params,
        )
        # Add total_stock as sum of current_stock + current_free_qty
        for row in rows:
            row["total_stock"] = float(row.get("current_stock", 0)) + float(row.get("current_free_qty", 0))
        return rows

    def fetch_purchases(self, search: str = "", fy_start: str = "", fy_end: str = "") -> list[dict[str, Any]]:
        if not self.table_exists("core_invoicemaster"): return []
        where, params = self.retailer_where("core_invoicemaster", "i", required=False)
        if fy_start and fy_end:
            # Use >= and <= for broader date matching
            where += " AND i.invoice_date >= %s AND i.invoice_date <= %s"
            params.extend([fy_start, fy_end])
        if search:
            where += " AND (i.invoice_no LIKE %s OR s.supplier_name LIKE %s)"
            term = f"%{search}%"
            params += [term, term]
        return self.query(
            f"""
            SELECT i.invoiceid, i.invoice_no, i.invoice_date, s.supplier_name,
                   i.invoice_total, i.invoice_paid, i.payment_status,
                   COUNT(pm.purchaseid) AS item_count
            FROM core_invoicemaster i
            JOIN core_suppliermaster s ON s.supplierid = i.supplierid_id
            LEFT JOIN core_purchasemaster pm ON pm.product_invoiceid_id = i.invoiceid
            WHERE 1=1{where}
            GROUP BY i.invoiceid, i.invoice_no, i.invoice_date, s.supplier_name,
                     i.invoice_total, i.invoice_paid, i.payment_status
            ORDER BY i.invoice_date DESC, i.invoiceid DESC
            LIMIT 500
            """,
            params,
        )

    def fetch_sales(self, search: str = "", fy_start: str = "", fy_end: str = "") -> list[dict[str, Any]]:
        if not self.table_exists("core_salesinvoicemaster"): return []
        where, params = self.retailer_where("core_salesinvoicemaster", "si", required=False)
        if fy_start and fy_end:
            # Use >= and <= for broader date matching
            where += " AND si.sales_invoice_date >= %s AND si.sales_invoice_date <= %s"
            params.extend([fy_start, fy_end])
        if search:
            where += " AND (si.sales_invoice_no LIKE %s OR c.customer_name LIKE %s)"
            term = f"%{search}%"
            params += [term, term]
        return self.query(
            f"""
            SELECT si.sales_invoice_no, si.sales_invoice_date, c.customer_name,
                   si.sales_invoice_paid,
                   COALESCE(SUM(sm.sale_total_amount), 0) AS invoice_total,
                   COUNT(sm.id) AS item_count
            FROM core_salesinvoicemaster si
            JOIN core_customermaster c ON c.customerid = si.customerid_id
            LEFT JOIN core_salesmaster sm ON sm.sales_invoice_no_id = si.sales_invoice_no
            WHERE 1=1{where}
            GROUP BY si.sales_invoice_no, si.sales_invoice_date, c.customer_name, si.sales_invoice_paid
            ORDER BY si.sales_invoice_date DESC, si.sales_invoice_no DESC
            LIMIT 500
            """,
            params,
        )

    def fetch_inventory(self, search: str = "") -> list[dict[str, Any]]:
        """Inventory data from inventory_transaction: purchase increases, sales decreases."""
        if not self.table_exists("inventory_transaction"):
            self._ensure_inventory_transaction_table()
        rid = self.config.retailer_id
        search_clause = ""
        params: list[Any] = [rid]
        if search:
            search_clause = " AND (p.product_name LIKE %s OR p.product_company LIKE %s OR p.product_hsn LIKE %s)"
            term = f"%{search}%"
            params += [term, term, term]
        rows = self.query(
            f"""SELECT
                    p.product_name AS name,
                    p.product_company AS company,
                    p.product_packing AS packing,
                    p.product_category AS category,
                    t.batch_no,
                    t.expiry_date AS expiry,
                    COALESCE(MAX(t.mrp), 0) AS mrp,
                    COALESCE(MAX(t.rate), 0) AS purchase_rate,
                    COALESCE(SUM(CASE
                        WHEN t.transaction_type IN ('PURCHASE') THEN t.quantity
                        WHEN t.transaction_type IN ('PURCHASE_RETURN','REVERT_PURCHASE_RETURN','REVERT_PURCHASE') THEN -t.quantity
                        WHEN t.transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') THEN -t.quantity
                        WHEN t.transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') THEN t.quantity
                        ELSE 0 END), 0) AS stock,
                    COALESCE(SUM(CASE
                        WHEN t.transaction_type IN ('PURCHASE') THEN t.free_quantity
                        WHEN t.transaction_type IN ('PURCHASE_RETURN','REVERT_PURCHASE_RETURN','REVERT_PURCHASE') THEN -t.free_quantity
                        WHEN t.transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') THEN -t.free_quantity
                        WHEN t.transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') THEN t.free_quantity
                        ELSE 0 END), 0) AS current_free_qty,
                    0 AS rate_a, 0 AS rate_b, 0 AS rate_c
                FROM inventory_transaction t
                JOIN core_productmaster p ON p.productid = t.product_id
                WHERE t.retailer_id = %s{search_clause}
                GROUP BY p.productid, p.product_name, p.product_company,
                         p.product_packing, p.product_category,
                         t.batch_no, t.expiry_date
                HAVING stock > 0 OR current_free_qty > 0
                ORDER BY p.product_name, t.expiry_date
                LIMIT 500""",
            params,
        )
        for r in rows:
            stock = float(r.get("stock") or 0)
            rate  = float(r.get("purchase_rate") or 0)
            val   = round(stock * rate, 2)
            r["value"]  = f"₹{val:.2f}"
            r["rates"]  = f"A:₹{r.get('rate_a',0)} B:₹{r.get('rate_b',0)} C:₹{r.get('rate_c',0)}"
            r["status"] = "in_stock" if stock > 0 else "out_of_stock"
        return rows

    def fetch_inventory_datewise(self, search: str = "", date_from: str = "", date_to: str = "") -> list[dict[str, Any]]:
        """Date-wise inventory from inventory_transaction, optionally filtered by transaction_date."""
        if not self.table_exists("inventory_transaction"):
            self._ensure_inventory_transaction_table()
        rid = self.config.retailer_id
        extra = ""
        params: list[Any] = [rid]
        if search:
            extra += " AND (p.product_name LIKE %s OR p.product_company LIKE %s OR p.product_hsn LIKE %s)"
            term = f"%{search}%"
            params += [term, term, term]
        if date_from:
            extra += " AND DATE(t.transaction_date) >= %s"
            params.append(date_from)
        if date_to:
            extra += " AND DATE(t.transaction_date) <= %s"
            params.append(date_to)
        rows = self.query(
            f"""SELECT
                    p.product_name AS name,
                    p.product_company AS company,
                    p.product_packing AS packing,
                    p.product_category AS category,
                    t.batch_no,
                    t.expiry_date AS expiry,
                    COALESCE(MAX(t.mrp), 0) AS mrp,
                    COALESCE(MAX(t.rate), 0) AS purchase_rate,
                    COALESCE(SUM(CASE
                        WHEN t.transaction_type IN ('PURCHASE') THEN t.quantity
                        WHEN t.transaction_type IN ('PURCHASE_RETURN','REVERT_PURCHASE_RETURN','REVERT_PURCHASE') THEN -t.quantity
                        WHEN t.transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') THEN -t.quantity
                        WHEN t.transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') THEN t.quantity
                        ELSE 0 END), 0) AS stock,
                    COALESCE(SUM(CASE
                        WHEN t.transaction_type IN ('PURCHASE') THEN t.free_quantity
                        WHEN t.transaction_type IN ('PURCHASE_RETURN','REVERT_PURCHASE_RETURN','REVERT_PURCHASE') THEN -t.free_quantity
                        WHEN t.transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') THEN -t.free_quantity
                        WHEN t.transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') THEN t.free_quantity
                        ELSE 0 END), 0) AS current_free_qty
                FROM inventory_transaction t
                JOIN core_productmaster p ON p.productid = t.product_id
                WHERE t.retailer_id = %s{extra}
                GROUP BY p.productid, p.product_name, p.product_company,
                         p.product_packing, p.product_category,
                         t.batch_no, t.expiry_date
                ORDER BY t.expiry_date, p.product_name
                LIMIT 500""",
            params,
        )
        for r in rows:
            stock = float(r.get("stock") or 0)
            rate  = float(r.get("purchase_rate") or 0)
            r["value"]  = f"₹{round(stock * rate, 2):.2f}"
            r["status"] = "in_stock" if stock > 0 else "out_of_stock"
        return rows

    def fetch_inventory_stock_statement(self, search: str = "") -> list[dict[str, Any]]:
        """Stock statement from inventory_transaction: net stock per product."""
        if not self.table_exists("inventory_transaction"):
            self._ensure_inventory_transaction_table()
        rid = self.config.retailer_id
        extra = ""
        params: list[Any] = [rid]
        if search:
            extra += " AND (p.product_name LIKE %s OR p.product_company LIKE %s OR p.product_hsn LIKE %s)"
            term = f"%{search}%"
            params += [term, term, term]
        rows = self.query(
            f"""SELECT
                    p.product_name AS name,
                    p.product_company AS company,
                    p.product_category AS category,
                    p.product_packing AS packing,
                    COALESCE(SUM(CASE
                        WHEN t.transaction_type IN ('PURCHASE') THEN t.quantity
                        WHEN t.transaction_type IN ('PURCHASE_RETURN','REVERT_PURCHASE_RETURN','REVERT_PURCHASE') THEN -t.quantity
                        WHEN t.transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') THEN -t.quantity
                        WHEN t.transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') THEN t.quantity
                        ELSE 0 END), 0) AS total_stock,
                    COALESCE(SUM(CASE
                        WHEN t.transaction_type IN ('PURCHASE') THEN t.quantity * t.rate
                        WHEN t.transaction_type IN ('PURCHASE_RETURN','REVERT_PURCHASE_RETURN','REVERT_PURCHASE') THEN -(t.quantity * t.rate)
                        WHEN t.transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') THEN -(t.quantity * t.rate)
                        WHEN t.transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') THEN t.quantity * t.rate
                        ELSE 0 END), 0) AS total_value
                FROM inventory_transaction t
                JOIN core_productmaster p ON p.productid = t.product_id
                WHERE t.retailer_id = %s{extra}
                GROUP BY p.productid, p.product_name, p.product_company,
                         p.product_category, p.product_packing
                HAVING total_stock > 0
                ORDER BY p.product_name
                LIMIT 500""",
            params,
        )
        for r in rows:
            r["total_value"] = f"₹{float(r.get('total_value') or 0):.2f}"
        return rows

    def fetch_suppliers(self, search: str = "") -> list[dict[str, Any]]:
        if not self.table_exists("core_suppliermaster"): return []
        params: list[Any] = []
        where = "WHERE 1=1"
        if search:
            where += " AND (supplier_name LIKE %s OR supplier_mobile LIKE %s)"
            term = f"%{search}%"
            params = [term, term]
        rows = self.query(
            f"""
            SELECT s.supplierid, s.supplier_name, s.supplier_mobile, s.supplier_emailid,
                   s.supplier_address, s.supplier_gstno, s.supplier_dlno,
                   COALESCE((SELECT SUM(i.invoice_total - i.invoice_paid)
                              FROM core_invoicemaster i WHERE i.supplierid_id = s.supplierid), 0) AS balance
            FROM core_suppliermaster s
            {where}
            ORDER BY s.supplier_name LIMIT 500
            """,
            params,
        )
        return rows

    def fetch_customers(self, search: str = "") -> list[dict[str, Any]]:
        if not self.table_exists("core_customermaster"): return []
        params: list[Any] = []
        where = "WHERE 1=1"
        if search:
            where += " AND (customer_name LIKE %s OR customer_mobile LIKE %s OR customer_emailid LIKE %s)"
            term = f"%{search}%"
            params = [term, term, term]
        rows = self.query(
            f"""
            SELECT c.customerid, c.customer_name, c.customer_type, c.customer_mobile,
                   c.customer_emailid, c.customer_address, c.customer_dlno, c.customer_gstno,
                   c.customer_credit_days,
                   COALESCE((SELECT SUM(si.sales_invoice_paid)
                              FROM core_salesinvoicemaster si WHERE si.customerid_id = c.customerid
                              AND si.retailer_id = %s), 0) AS paid_total
            FROM core_customermaster c
            {where}
            ORDER BY c.customer_name LIMIT 500
            """,
            [self.config.retailer_id] + params,
        )
        return rows

    def fetch_reports(self) -> list[dict[str, Any]]:
        dashboard = self.fetch_dashboard()
        return [
            {"report": "Product Count", "value": dashboard["products"], "remarks": "Shared product master"},
            {"report": "Total Inventory Value", "value": f"₹{dashboard['value']:.2f}", "remarks": "Batch inventory"},
            {"report": "Low Stock Items", "value": dashboard["low_stock"], "remarks": "Filtered by retailer_id"},
            {"report": "Out of Stock", "value": dashboard["out_stock"], "remarks": "Filtered by retailer_id"},
        ]

    def fetch_requests(
        self,
        status: str = "",
        request_type: str = "",
        date_text: str = "",
        only_pending: bool = False,
    ) -> list[dict[str, Any]]:
        if not self.table_exists("retailer_request"):
            return []
        # Ensure from_date / to_date columns exist (added in later version)
        for col in ('from_date', 'to_date'):
            if not self.column_exists('retailer_request', col):
                self.execute(
                    f"ALTER TABLE retailer_request ADD COLUMN {col} VARCHAR(20) DEFAULT ''"
                )
        params: list[Any] = [self.config.retailer_id]
        where = "WHERE retailer_id = %s"
        if only_pending:
            where += " AND UPPER(status) = 'PENDING'"
        elif status:
            where += " AND UPPER(status) = UPPER(%s)"
            params.append(status)
        if request_type:
            where += " AND UPPER(request_type) = UPPER(%s)"
            params.append(request_type)
        if date_text:
            where += " AND DATE(created_at) = %s"
            params.append(date_text)
        return self.query(
            f"""
            SELECT id, request_type, reference_id, status, created_at, processed_at, remarks,
                   COALESCE(from_date, '') AS from_date, COALESCE(to_date, '') AS to_date
            FROM retailer_request
            {where}
            ORDER BY created_at DESC, id DESC
            LIMIT 500
            """,
            params,
        )

    def mark_request_processed(self, request_id: int) -> None:
        self.execute(
            """
            UPDATE retailer_request
            SET status = 'Processed', processed_at = NOW()
            WHERE id = %s AND retailer_id = %s
            """,
            (request_id, self.config.retailer_id),
        )

    def delete_wholesaler_request(self, reference_id: int, retailer_id: int) -> None:
        """Remove a request from retailer_request that was deleted on wholesaler."""
        self.execute(
            "DELETE FROM retailer_request WHERE reference_id=%s AND retailer_id=%s",
            (reference_id, retailer_id),
        )

    def get_all_reference_ids(self, retailer_id: int) -> list:
        """Return all known reference_ids for this retailer."""
        rows = self.query(
            "SELECT reference_id FROM retailer_request WHERE retailer_id=%s AND reference_id IS NOT NULL",
            (retailer_id,),
        )
        return [r['reference_id'] for r in rows]

    def upsert_wholesaler_requests(self, requests: list, retailer_id: int) -> int:
        if not requests:
            return 0
        from datetime import datetime
        # Ensure from_date/to_date columns exist (added later)
        for col, dtype in [('from_date', 'VARCHAR(20)'), ('to_date', 'VARCHAR(20)')]:
            if not self.column_exists('retailer_request', col):
                self.execute(f"ALTER TABLE retailer_request ADD COLUMN {col} {dtype} DEFAULT ''")
                self._columns_cache.pop(('retailer_request', col), None)
        inserted = 0
        for r in requests:
            existing = self.query(
                "SELECT id FROM retailer_request "
                "WHERE reference_id = %s AND retailer_id = %s LIMIT 1",
                (r['request_id'], retailer_id),
            )
            if existing:
                continue
            self.execute(
                """
                INSERT INTO retailer_request
                    (request_type, reference_id, status, remarks,
                     created_at, retailer_id, from_date, to_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    r['request_type'],
                    r['request_id'],
                    'Pending',
                    r.get('remarks', ''),
                    r.get('created_at') or datetime.now(),
                    retailer_id,
                    r.get('from_date', ''),
                    r.get('to_date', ''),
                ),
            )
            inserted += 1
        return inserted

    def update_request_status_by_reference(
        self, reference_id: int, new_status: str, retailer_id: int
    ) -> None:
        _status_map = {
            'PENDING': 'Pending', 'PROCESSING': 'Processing',
            'COMPLETED': 'Processed', 'FAILED': 'Failed',
        }
        mapped = _status_map.get(new_status.upper(), new_status.capitalize())
        if mapped in ('Processed', 'Failed'):
            self.execute(
                """
                UPDATE retailer_request
                SET status = %s, processed_at = NOW()
                WHERE reference_id = %s AND retailer_id = %s
                """,
                (mapped, reference_id, retailer_id),
            )
        else:
            self.execute(
                """
                UPDATE retailer_request
                SET status = %s
                WHERE reference_id = %s AND retailer_id = %s
                """,
                (mapped, reference_id, retailer_id),
            )

    def mark_request_failed(self, request_id: int, remarks: str) -> None:
        self.execute(
            """
            UPDATE retailer_request
            SET status = 'Failed', processed_at = NOW(), remarks = %s
            WHERE id = %s AND retailer_id = %s
            """,
            (remarks[:500], request_id, self.config.retailer_id),
        )

    # ── PURCHASE INVOICE CRUD ─────────────────────────────────────────────────

    def get_suppliers_list(self) -> list[dict[str, Any]]:
        return self.query(
            "SELECT supplierid, supplier_name FROM core_suppliermaster ORDER BY supplier_name LIMIT 500"
        )

    def get_customers_list(self) -> list[dict[str, Any]]:
        return self.query(
            "SELECT customerid, customer_name, customer_type FROM core_customermaster ORDER BY customer_name LIMIT 500"
        )

    def get_products_list(self) -> list[dict[str, Any]]:
        return self.query(
            "SELECT productid, product_name, product_company, product_packing, product_hsn_percent FROM core_productmaster ORDER BY product_name LIMIT 2000"
        )

    def get_invoice(self, invoice_id: int) -> dict[str, Any] | None:
        rows = self.query(
            """SELECT i.*, s.supplier_name FROM core_invoicemaster i
               JOIN core_suppliermaster s ON s.supplierid = i.supplierid_id
               WHERE i.invoiceid=%s""", (invoice_id,))
        return rows[0] if rows else None

    def get_invoice_items(self, invoice_id: int) -> list[dict[str, Any]]:
        return self.query(
            """SELECT pm.*, p.product_name AS prod_name FROM core_purchasemaster pm
               JOIN core_productmaster p ON p.productid = pm.productid_id
               WHERE pm.product_invoiceid_id=%s ORDER BY pm.purchaseid""",
            (invoice_id,)
        )

    def create_invoice(self, data: dict) -> int:
        """Insert InvoiceMaster, return new invoiceid."""
        with self.cursor() as cur:
            cur.execute(
                """INSERT INTO core_invoicemaster
                   (retailer_id, invoice_no, invoice_date, supplierid_id,
                    transport_charges, invoice_total, invoice_paid, payment_status)
                   VALUES (%s,%s,%s,%s,%s,%s,0,'pending')""",
                (
                    self.config.retailer_id,
                    data["invoice_no"], data["invoice_date"],
                    data["supplierid"], data.get("transport_charges", 0),
                    data.get("invoice_total", 0),
                )
            )
            return cur.lastrowid

    def update_invoice(self, invoice_id: int, data: dict) -> None:
        self.execute(
            """UPDATE core_invoicemaster
               SET invoice_no=%s, invoice_date=%s, supplierid_id=%s,
                   transport_charges=%s, invoice_total=%s
               WHERE invoiceid=%s""",
            (data["invoice_no"], data["invoice_date"], data["supplierid"],
             data.get("transport_charges", 0), data.get("invoice_total", 0),
             invoice_id)
        )

    def delete_invoice(self, invoice_id: int) -> None:
        # Fetch items before deleting
        items = self.get_invoice_items(invoice_id)
        inv = self.get_invoice(invoice_id)
        invoice_no = inv['invoice_no'] if inv else str(invoice_id)

        for item in items:
            pid        = item['productid_id']
            batch      = item.get('product_batch_no', '') or ''
            expiry     = item.get('product_expiry', '') or ''
            qty        = float(item.get('product_quantity', 0))
            free       = float(item.get('product_free_qty', 0))
            mrp        = float(item.get('product_MRP', 0))
            rate       = float(item.get('product_purchase_rate', 0))
            ra         = float(item.get('rate_a', 0))
            rb         = float(item.get('rate_b', 0))
            rc         = float(item.get('rate_c', 0))
            total      = float(item.get('total_amount', 0))

            # Reverse batch_inventory_cache
            self.update_inventory_cache_purchase(
                {'productid': pid, 'batch_no': batch, 'expiry': expiry,
                 'quantity': qty, 'free_qty': free, 'mrp': mrp,
                 'purchase_rate': rate, 'rate_a': ra, 'rate_b': rb, 'rate_c': rc},
                multiplier=-1.0
            )

        # Delete child rows then parent
        self.execute("DELETE FROM core_purchasemaster WHERE product_invoiceid_id=%s", (invoice_id,))
        self.execute("DELETE FROM core_invoicepaid WHERE ip_invoiceid_id=%s", (invoice_id,))
        if self.table_exists("inventory_transaction"):
            self.execute(
                "DELETE FROM inventory_transaction WHERE retailer_id=%s AND reference_type='INVOICE' AND reference_id=%s",
                (self.config.retailer_id, invoice_id)
            )
        self.execute("DELETE FROM core_invoicemaster WHERE invoiceid=%s", (invoice_id,))

    def update_inventory_cache_purchase(self, item: dict, multiplier: float = 1.0) -> None:
        """Legacy method - batch_inventory_cache table removed. No-op now."""
        pass

    def update_inventory_cache_sale(self, item: dict, multiplier: float = 1.0) -> None:
        """Legacy method - batch_inventory_cache table removed. No-op now."""
        pass

    def _ensure_inventory_transaction_table(self) -> None:
        self.execute(
            """CREATE TABLE IF NOT EXISTS inventory_transaction (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                retailer_id BIGINT,
                product_id BIGINT NOT NULL,
                batch_no VARCHAR(100) DEFAULT '',
                expiry_date VARCHAR(20) DEFAULT '',
                transaction_type VARCHAR(50) NOT NULL,
                quantity DECIMAL(12,3) DEFAULT 0,
                free_quantity DECIMAL(12,3) DEFAULT 0,
                transaction_date DATETIME,
                reference_type VARCHAR(50) DEFAULT '',
                reference_id BIGINT DEFAULT 0,
                reference_number VARCHAR(100) DEFAULT '',
                rate DECIMAL(12,4) DEFAULT 0,
                mrp DECIMAL(12,4) DEFAULT 0,
                total_value DECIMAL(14,2) DEFAULT 0,
                created_at DATETIME,
                created_by_id BIGINT DEFAULT NULL,
                remarks VARCHAR(1000) DEFAULT '',
                INDEX idx_retailer_product (retailer_id, product_id),
                INDEX idx_transaction_type (transaction_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"""
        )
        self._tables_cache["inventory_transaction"] = True

    def log_inventory_transaction(
        self,
        product_id: int,
        batch_no: str,
        expiry_date: str,
        transaction_type: str,
        quantity: float,
        free_quantity: float,
        reference_type: str,
        reference_id: int,
        reference_number: str,
        rate: float,
        mrp: float,
        total_value: float,
        remarks: str = "",
    ) -> None:
        try:
            if not self.table_exists("inventory_transaction"):
                self._ensure_inventory_transaction_table()
            self.execute(
                "INSERT INTO inventory_transaction "
                "(retailer_id, product_id, batch_no, expiry_date, transaction_type, "
                "quantity, free_quantity, transaction_date, reference_type, reference_id, "
                "reference_number, rate, mrp, total_value, created_at, created_by_id, remarks) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,NOW(),%s,%s,%s,%s,%s,%s,NOW(),%s,%s)",
                (
                    self.config.retailer_id,
                    product_id,
                    batch_no or "",
                    expiry_date or "",
                    transaction_type,
                    quantity,
                    free_quantity,
                    reference_type,
                    reference_id,
                    reference_number,
                    rate,
                    mrp,
                    total_value,
                    None,
                    remarks[:1000],
                ),
            )
        except Exception as e:
            import logging
            logging.error(f"inventory transaction log failed: {e}")

    def reverse_purchase_items_stock(self, invoice_id: int) -> None:
        """Remove stock for all items of a purchase invoice before re-saving (edit)."""
        rows = self.query(
            "SELECT productid_id AS productid, product_batch_no AS batch_no, "
            "product_expiry AS expiry, product_quantity AS quantity, "
            "product_free_qty AS free_qty, product_MRP AS mrp, "
            "product_purchase_rate AS purchase_rate, rate_a, rate_b, rate_c "
            "FROM core_purchasemaster WHERE product_invoiceid_id=%s", (invoice_id,))
        for row in rows:
            self.update_inventory_cache_purchase({
                'productid':    row['productid'],
                'batch_no':     row.get('batch_no', '') or '',
                'expiry':       row.get('expiry', '') or '',
                'quantity':     float(row.get('quantity') or 0),
                'free_qty':     float(row.get('free_qty') or 0),
                'mrp':          float(row.get('mrp') or 0),
                'purchase_rate':float(row.get('purchase_rate') or 0),
                'rate_a':       float(row.get('rate_a') or 0),
                'rate_b':       float(row.get('rate_b') or 0),
                'rate_c':       float(row.get('rate_c') or 0),
            }, multiplier=-1.0)

    def reverse_sales_items_stock(self, invoice_no: str) -> None:
        """Add back stock for all items of a sales invoice before re-saving (edit)."""
        rows = self.query(
            "SELECT productid_id AS productid, product_batch_no AS batch_no, "
            "product_expiry AS expiry, sale_quantity AS quantity, sale_free_qty AS free_qty "
            "FROM core_salesmaster WHERE sales_invoice_no_id=%s", (invoice_no,))
        for row in rows:
            self.update_inventory_cache_sale({
                'productid': row['productid'],
                'batch_no':  row.get('batch_no', '') or '',
                'quantity':  float(row.get('quantity') or 0),
                'free_qty':  float(row.get('free_qty') or 0),
            }, multiplier=-1.0)

    def _get_packing_qty(self, product_id: int, packing: str = "") -> int:
        """Parse packing string e.g. '10x10', '1x100', '30' → integer multiplier."""
        try:
            if not packing:
                rows = self.query("SELECT product_packing FROM core_productmaster WHERE productid=%s", (product_id,))
                packing = (rows[0]["product_packing"] or "") if rows else ""
            packing = str(packing).strip().upper()
            # formats: 10X10, 10x10, 10*10, 1x100, just 10
            import re
            m = re.search(r'(\d+)[xX*](\d+)', packing)
            if m:
                return int(m.group(1)) * int(m.group(2))
            m2 = re.search(r'(\d+)', packing)
            if m2:
                return int(m2.group(1))
        except Exception:
            pass
        return 1

    def add_purchase_item(self, invoice_id: int, invoice_no: str, supplier_id: int, item: dict) -> int:
        """Insert one PurchaseMaster row, update stock cache, return purchaseid.
        Stock stored = qty * packing_multiplier (boxes → individual units)."""
        qty = float(item.get("quantity", 0))
        free = float(item.get("free_qty", 0))
        packing_qty = self._get_packing_qty(item["productid"], item.get("product_packing", ""))
        stock_qty  = qty  * packing_qty
        stock_free = free  # free qty is already in individual units, no packing multiply
        rate = float(item.get("purchase_rate", 0))
        mrp = float(item.get("mrp", 0))
        discount = float(item.get("discount", 0))
        cgst = float(item.get("cgst", 0))
        sgst = float(item.get("sgst", 0))
        mode = item.get("calc_mode", "flat")
        base = rate * qty
        discounted = base - discount if mode == "flat" else base * (1 - discount / 100)
        actual_rate = discounted / qty if qty else 0
        total = round(discounted * (1 + (cgst + sgst) / 100), 2)
        rid = self.config.retailer_id
        pid = item["productid"]
        batch = item.get("batch_no", "")
        expiry = item.get("expiry", "")
        ra = float(item.get("rate_a", 0))
        rb = float(item.get("rate_b", 0))
        rc = float(item.get("rate_c", 0))

        with self.cursor() as cur:
            cur.execute(
                """INSERT INTO core_purchasemaster
                   (retailer_id, product_supplierid_id, product_invoiceid_id, product_invoice_no,
                    productid_id, product_name, product_company, product_packing,
                    product_batch_no, product_expiry, product_MRP, product_purchase_rate,
                    product_quantity, product_free_qty, product_scheme, product_discount_got,
                    product_transportation_charges, actual_rate_per_qty, product_actual_rate,
                    total_amount, purchase_entry_date, CGST, SGST, purchase_calculation_mode,
                    rate_a, rate_b, rate_c)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,%s,%s,%s,NOW(),%s,%s,%s,%s,%s,%s)""",
                (
                    rid, supplier_id, invoice_id, invoice_no,
                    pid, item["product_name"], item.get("product_company", ""),
                    item.get("product_packing", ""), batch, expiry, mrp, rate,
                    qty, free, float(item.get("scheme", 0)),
                    discount, actual_rate, actual_rate, total, cgst, sgst, mode,
                    ra, rb, rc,
                )
            )
            new_id = cur.lastrowid
        
        self.log_inventory_transaction(
            pid, batch, expiry, "PURCHASE", stock_qty, stock_free,
            "INVOICE", invoice_id, invoice_no, rate, mrp, total,
            f"Purchase Invoice {invoice_no} (packing x{packing_qty})",
        )
        return new_id

    def delete_purchase_item(self, purchase_id: int) -> None:
        """Delete single purchase item and reverse its stock in cache."""
        rows = self.query(
            "SELECT productid_id AS productid, product_batch_no AS batch_no, "
            "product_expiry AS expiry, product_quantity AS quantity, product_free_qty AS free_qty, "
            "product_MRP AS mrp, product_purchase_rate AS purchase_rate, "
            "rate_a, rate_b, rate_c FROM core_purchasemaster WHERE purchaseid=%s", (purchase_id,))
        if rows:
            self.update_inventory_cache_purchase({
                'productid':    rows[0]['productid'],
                'batch_no':     rows[0].get('batch_no', '') or '',
                'expiry':       rows[0].get('expiry', '') or '',
                'quantity':     float(rows[0].get('quantity') or 0),
                'free_qty':     float(rows[0].get('free_qty') or 0),
                'mrp':          float(rows[0].get('mrp') or 0),
                'purchase_rate':float(rows[0].get('purchase_rate') or 0),
                'rate_a':       float(rows[0].get('rate_a') or 0),
                'rate_b':       float(rows[0].get('rate_b') or 0),
                'rate_c':       float(rows[0].get('rate_c') or 0),
            }, multiplier=-1.0)
        self.execute("DELETE FROM core_purchasemaster WHERE purchaseid=%s", (purchase_id,))

    def recalc_invoice_total(self, invoice_id: int) -> float:
        """Sum all items + transport and update invoice_total. Returns new total."""
        rows = self.query(
            "SELECT COALESCE(SUM(total_amount),0) AS t, transport_charges FROM core_invoicemaster i "
            "LEFT JOIN core_purchasemaster pm ON pm.product_invoiceid_id=i.invoiceid "
            "WHERE i.invoiceid=%s GROUP BY i.transport_charges", (invoice_id,))
        if rows:
            total = float(rows[0]["t"]) + float(rows[0].get("transport_charges") or 0)
        else:
            total = 0.0
        self.execute("UPDATE core_invoicemaster SET invoice_total=%s WHERE invoiceid=%s",
                     (total, invoice_id))
        return total

    def add_invoice_payment(self, invoice_id: int, date: str, amount: float, mode: str, ref: str) -> None:
        self.execute(
            "INSERT INTO core_invoicepaid (ip_invoiceid_id, payment_date, payment_amount, payment_mode, payment_ref_no) VALUES (%s,%s,%s,%s,%s)",
            (invoice_id, date, amount, mode, ref)
        )
        self.execute(
            "UPDATE core_invoicemaster SET invoice_paid=invoice_paid+%s WHERE invoiceid=%s",
            (amount, invoice_id)
        )
        self._update_invoice_payment_status(invoice_id)

    def _update_invoice_payment_status(self, invoice_id: int) -> None:
        rows = self.query(
            "SELECT invoice_total, invoice_paid FROM core_invoicemaster WHERE invoiceid=%s",
            (invoice_id,))
        if rows:
            total = float(rows[0]["invoice_total"])
            paid = float(rows[0]["invoice_paid"])
            balance = total - paid
            status = "paid" if balance <= 0.01 else ("partial" if paid > 0 else "pending")
            self.execute("UPDATE core_invoicemaster SET payment_status=%s WHERE invoiceid=%s",
                         (status, invoice_id))

    def get_invoice_payments(self, invoice_id: int) -> list[dict[str, Any]]:
        return self.query(
            "SELECT * FROM core_invoicepaid WHERE ip_invoiceid_id=%s ORDER BY payment_date DESC",
            (invoice_id,)
        )

    def delete_invoice_payment(self, payment_id: int) -> None:
        rows = self.query(
            "SELECT ip_invoiceid_id, payment_amount FROM core_invoicepaid WHERE payment_id=%s",
            (payment_id,))
        if rows:
            self.execute("DELETE FROM core_invoicepaid WHERE payment_id=%s", (payment_id,))
            inv_id = rows[0]["ip_invoiceid_id"]
            amt = float(rows[0]["payment_amount"])
            self.execute(
                "UPDATE core_invoicemaster SET invoice_paid=GREATEST(0, invoice_paid-%s) WHERE invoiceid=%s",
                (amt, inv_id))
            self._update_invoice_payment_status(inv_id)

    # ── SALES INVOICE CRUD ────────────────────────────────────────────────────

    def get_sales_invoice(self, invoice_no: str) -> dict[str, Any] | None:
        """Get sales invoice header with items in single optimized query."""
        rows = self.query(
            """SELECT si.*, c.customer_name, c.customer_type
               FROM core_salesinvoicemaster si
               JOIN core_customermaster c ON c.customerid = si.customerid_id
               WHERE si.sales_invoice_no=%s""", (invoice_no,))
        return rows[0] if rows else None

    def get_sales_invoice_with_items(self, invoice_no: str) -> dict[str, Any] | None:
        """OPTIMIZED: Get sales invoice with items in single call - prevents UI lag."""
        # Get header
        inv = self.get_sales_invoice(invoice_no)
        if not inv:
            return None
        
        # Get items in same transaction
        inv['items'] = self.get_sales_items(invoice_no)
        return inv

    def get_sales_items(self, invoice_no: str) -> list[dict[str, Any]]:
        return self.query(
            "SELECT * FROM core_salesmaster WHERE sales_invoice_no_id=%s ORDER BY id",
            (invoice_no,)
        )

    def get_next_sales_invoice_no(self, series_id: int | None = None) -> str:
        """Generate next invoice number — race-condition-safe via MAX()+1."""
        if series_id:
            rows = self.query(
                "SELECT series_name, series_prefix, current_number FROM core_invoiceseries WHERE series_id=%s",
                (series_id,))
            if rows:
                r = rows[0]
                prefix = r.get("series_prefix") or r["series_name"]
                num = int(r["current_number"])
                inv_no = f"{prefix}{num:07d}"
                self.execute(
                    "UPDATE core_invoiceseries SET current_number=current_number+1 WHERE series_id=%s",
                    (series_id,))
                return inv_no
        # Use MAX numeric suffix to avoid race condition with COUNT(*)
        rows = self.query(
            "SELECT sales_invoice_no FROM core_salesinvoicemaster "
            "WHERE sales_invoice_no REGEXP '^INV[0-9]+$' "
            "ORDER BY CAST(SUBSTRING(sales_invoice_no,4) AS UNSIGNED) DESC LIMIT 1")
        if rows:
            try:
                n = int(rows[0]["sales_invoice_no"][3:]) + 1
            except Exception:
                n = 1
        else:
            n = 1
        candidate = f"INV{n:07d}"
        # Ensure uniqueness in case of collision
        while self.query("SELECT 1 FROM core_salesinvoicemaster WHERE sales_invoice_no=%s", (candidate,)):
            n += 1
            candidate = f"INV{n:07d}"
        return candidate

    def create_sales_invoice(self, data: dict) -> str:
        """Insert SalesInvoiceMaster, return sales_invoice_no."""
        with self.cursor() as cur:
            inv_no = self.get_next_sales_invoice_no(data.get("series_id"))
            cur.execute(
                """INSERT INTO core_salesinvoicemaster
                   (sales_invoice_no, retailer_id, sales_invoice_date, customerid_id,
                    invoice_series_id, sales_transport_charges, sales_invoice_paid)
                   VALUES (%s,%s,%s,%s,%s,%s,0)""",
                (
                    inv_no, self.config.retailer_id,
                    data["invoice_date"], data["customerid"],
                    data.get("series_id"), data.get("transport_charges", 0),
                )
            )
        return inv_no

    def delete_sales_invoice(self, invoice_no: str) -> None:
        # Fetch items before deleting
        items = self.get_sales_items(invoice_no)

        for item in items:
            pid    = item['productid_id']
            batch  = item.get('product_batch_no', '') or ''
            expiry = item.get('product_expiry', '') or ''
            qty    = float(item.get('sale_quantity', 0))
            free   = float(item.get('sale_free_qty', 0))
            mrp    = float(item.get('product_MRP', 0))
            rate   = float(item.get('sale_rate', 0))
            total  = float(item.get('sale_total_amount', 0))

            # Add stock back to batch_inventory_cache
            self.update_inventory_cache_sale(
                {'productid': pid, 'batch_no': batch, 'expiry': expiry,
                 'quantity': qty, 'free_qty': free},
                multiplier=-1.0
            )

        # Delete children first, then parent
        self.execute("DELETE FROM core_salesmaster WHERE sales_invoice_no_id=%s", (invoice_no,))
        self.execute("DELETE FROM core_salesinvoicepaid WHERE sales_ip_invoice_no_id=%s", (invoice_no,))
        if self.table_exists("inventory_transaction"):
            self.execute(
                "DELETE FROM inventory_transaction WHERE retailer_id=%s AND reference_type='INVOICE' AND reference_number=%s",
                (self.config.retailer_id, invoice_no)
            )
        self.execute("DELETE FROM core_salesinvoicemaster WHERE sales_invoice_no=%s", (invoice_no,))

    def add_sales_item(self, invoice_no: str, customer_id: int, item: dict) -> int:
        """Insert one SalesMaster row, log inventory transaction, return id."""
        qty      = float(item.get("quantity", 0))
        free     = float(item.get("free_qty", 0))
        packing_qty  = self._get_packing_qty(item["productid"], item.get("product_packing", ""))
        stock_deduct = qty  * packing_qty
        free_deduct  = free  # free qty is already in individual units, no packing multiply
        mrp      = float(item.get("mrp", 0))
        rate     = float(item.get("sale_rate", 0))
        discount = float(item.get("discount", 0))
        cgst     = float(item.get("cgst", 0))
        sgst     = float(item.get("sgst", 0))
        mode     = item.get("calc_mode", "flat")
        base       = mrp * qty
        discounted = base - discount if mode == "flat" else base * (1 - discount / 100)
        total      = round(discounted * (1 + (cgst + sgst) / 100), 2)
        rid  = self.config.retailer_id
        pid  = item["productid"]
        batch  = item.get("batch_no", "")
        expiry = item.get("expiry", "")

        with self.cursor() as cur:
            cur.execute(
                """INSERT INTO core_salesmaster
                   (retailer_id, sales_invoice_no_id, customerid_id, productid_id,
                    product_name, product_company, product_packing,
                    product_batch_no, product_expiry, product_MRP,
                    sale_rate, sale_quantity, sale_free_qty, sale_scheme,
                    sale_discount, sale_cgst, sale_sgst, sale_total_amount,
                    sale_entry_date, rate_applied, sale_calculation_mode)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s,%s)""",
                (
                    rid, invoice_no, customer_id,
                    pid, item["product_name"], item.get("product_company", ""),
                    item.get("product_packing", ""), batch, expiry, mrp,
                    rate, qty, free, float(item.get("scheme", 0)),
                    discount, cgst, sgst, total,
                    item.get("rate_applied", "A"), mode,
                )
            )
            new_id = cur.lastrowid
        
        # Log inventory transaction (no cache update needed)
        self.log_inventory_transaction(
            pid, batch, expiry, "SALE", stock_deduct, free_deduct,
            "INVOICE", 0, invoice_no, rate, mrp, total,
            f"Sales Invoice {invoice_no} (packing x{packing_qty})",
        )
        return new_id

    def delete_sales_item(self, sale_id: int) -> None:
        """Delete single sales item and add stock back in cache."""
        rows = self.query(
            "SELECT productid_id AS productid, product_batch_no AS batch_no, "
            "sale_quantity AS quantity, sale_free_qty AS free_qty "
            "FROM core_salesmaster WHERE id=%s", (sale_id,))
        if rows:
            self.update_inventory_cache_sale({
                'productid': rows[0]['productid'],
                'batch_no':  rows[0].get('batch_no', '') or '',
                'quantity':  float(rows[0].get('quantity') or 0),
                'free_qty':  float(rows[0].get('free_qty') or 0),
            }, multiplier=-1.0)
        self.execute("DELETE FROM core_salesmaster WHERE id=%s", (sale_id,))

    def add_sales_payment(self, invoice_no: str, date: str, amount: float, mode: str, ref: str) -> None:
        self.execute(
            "INSERT INTO core_salesinvoicepaid (sales_ip_invoice_no_id, sales_payment_date, sales_payment_amount, sales_payment_mode, sales_payment_ref_no) VALUES (%s,%s,%s,%s,%s)",
            (invoice_no, date, amount, mode, ref)
        )
        self.execute(
            "UPDATE core_salesinvoicemaster SET sales_invoice_paid=sales_invoice_paid+%s WHERE sales_invoice_no=%s",
            (amount, invoice_no)
        )

    def get_sales_payments(self, invoice_no: str) -> list[dict[str, Any]]:
        return self.query(
            "SELECT * FROM core_salesinvoicepaid WHERE sales_ip_invoice_no_id=%s ORDER BY sales_payment_date DESC",
            (invoice_no,)
        )

    def delete_sales_payment(self, payment_id: int) -> None:
        rows = self.query(
            "SELECT sales_ip_invoice_no_id, sales_payment_amount FROM core_salesinvoicepaid WHERE sales_payment_id=%s",
            (payment_id,))
        if rows:
            self.execute("DELETE FROM core_salesinvoicepaid WHERE sales_payment_id=%s", (payment_id,))
            inv_no = rows[0]["sales_ip_invoice_no_id"]
            amt = float(rows[0]["sales_payment_amount"])
            self.execute(
                "UPDATE core_salesinvoicemaster SET sales_invoice_paid=GREATEST(0, sales_invoice_paid-%s) WHERE sales_invoice_no=%s",
                (amt, inv_no))

    def get_batch_stock(self, product_id: int, batch_no: str) -> float:
        """Return current total_stock for a batch from inventory_transaction."""
        if not self.table_exists("inventory_transaction"):
            self._ensure_inventory_transaction_table()
        rows = self.query(
            """SELECT COALESCE(SUM(CASE
                   WHEN transaction_type IN ('PURCHASE') THEN quantity + free_quantity
                   WHEN transaction_type IN ('PURCHASE_RETURN','REVERT_PURCHASE_RETURN','REVERT_PURCHASE') THEN -(quantity + free_quantity)
                   WHEN transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') THEN -(quantity + free_quantity)
                   WHEN transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') THEN (quantity + free_quantity)
                   ELSE 0 END), 0) AS total_stock
               FROM inventory_transaction
               WHERE product_id=%s AND batch_no=%s AND retailer_id=%s""",
            (product_id, batch_no, self.config.retailer_id)
        )
        return float(rows[0]["total_stock"]) if rows else 0.0

    def get_batches_for_product(self, product_id: int) -> list[dict[str, Any]]:
        """Batches with stock > 0 for a product, from inventory_transaction.
        Returns quantity and free_quantity separately (NOT multiplied by packing)."""
        if not self.table_exists("inventory_transaction"):
            self._ensure_inventory_transaction_table()
        return self.query(
            """SELECT t.batch_no, t.expiry_date,
                      COALESCE(SUM(CASE
                          WHEN t.transaction_type IN ('PURCHASE') THEN t.quantity
                          WHEN t.transaction_type IN ('PURCHASE_RETURN','REVERT_PURCHASE_RETURN','REVERT_PURCHASE') THEN -t.quantity
                          WHEN t.transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') THEN -t.quantity
                          WHEN t.transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') THEN t.quantity
                          ELSE 0 END), 0) AS quantity,
                      COALESCE(SUM(CASE
                          WHEN t.transaction_type IN ('PURCHASE') THEN t.free_quantity
                          WHEN t.transaction_type IN ('PURCHASE_RETURN','REVERT_PURCHASE_RETURN','REVERT_PURCHASE') THEN -t.free_quantity
                          WHEN t.transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') THEN -t.free_quantity
                          WHEN t.transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') THEN t.free_quantity
                          ELSE 0 END), 0) AS free_quantity,
                      COALESCE(MAX(t.mrp), 0) AS mrp,
                      COALESCE(MAX(t.rate), 0) AS rate_a,
                      COALESCE(MAX(t.rate), 0) AS rate_b,
                      COALESCE(MAX(t.rate), 0) AS rate_c,
                      COALESCE(MAX(t.rate), 0) AS purchase_rate
               FROM inventory_transaction t
               WHERE t.product_id=%s AND t.retailer_id=%s
               GROUP BY t.batch_no, t.expiry_date
               HAVING quantity > 0 OR free_quantity > 0
               ORDER BY t.expiry_date""",
            (product_id, self.config.retailer_id)
        )

    def get_invoice_series(self) -> list[dict[str, Any]]:
        return self.query(
            "SELECT series_id, series_name, series_prefix, current_number FROM core_invoiceseries WHERE is_active=1 ORDER BY series_name"
        )

    # ── PURCHASE RETURN CRUD ──────────────────────────────────────────────────

    def fetch_purchase_returns(self, search: str = "") -> list[dict[str, Any]]:
        where, params = self.retailer_where("core_returninvoicemaster", "ri", required=False)
        if search:
            where += " AND (ri.returninvoiceid LIKE %s OR s.supplier_name LIKE %s)"
            t = f"%{search}%"
            params += [t, t]
        return self.query(
            f"""SELECT ri.returninvoiceid, ri.returninvoice_date, s.supplier_name,
                       ri.returninvoice_total, ri.returninvoice_paid, ri.return_charges
                FROM core_returninvoicemaster ri
                JOIN core_suppliermaster s ON s.supplierid = ri.returnsupplierid_id
                WHERE 1=1{where}
                ORDER BY ri.returninvoice_date DESC LIMIT 500""", params)

    def get_purchase_return(self, return_id: str) -> dict[str, Any] | None:
        rows = self.query(
            """SELECT ri.*, s.supplier_name FROM core_returninvoicemaster ri
               JOIN core_suppliermaster s ON s.supplierid = ri.returnsupplierid_id
               WHERE ri.returninvoiceid=%s""", (return_id,))
        return rows[0] if rows else None

    def get_purchase_return_items(self, return_id: str) -> list[dict[str, Any]]:
        return self.query(
            """SELECT rpm.*, p.product_name AS prod_name
               FROM core_returnpurchasemaster rpm
               JOIN core_productmaster p ON p.productid = rpm.returnproductid_id
               WHERE rpm.returninvoiceid_id=%s ORDER BY rpm.returnpurchaseid""",
            (return_id,))

    def _gen_purchase_return_id(self) -> str:
        from datetime import date
        d = date.today().strftime("%Y%m%d")
        for i in range(1, 9999):
            rid = f"PR-{d}-{i:04d}"
            if not self.query("SELECT 1 FROM core_returninvoicemaster WHERE returninvoiceid=%s", (rid,)):
                return rid
        return f"PR-{d}-9999"

    def create_purchase_return(self, data: dict) -> str:
        rid = data.get("return_id") or self._gen_purchase_return_id()
        self.execute(
            """INSERT INTO core_returninvoicemaster
               (returninvoiceid, retailer_id, returninvoice_date, returnsupplierid_id,
                return_charges, returninvoice_total, returninvoice_paid)
               VALUES (%s,%s,%s,%s,%s,0,0)""",
            (rid, self.config.retailer_id, data["return_date"],
             data["supplier_id"], data.get("return_charges", 0))
        )
        return rid

    def add_purchase_return_item(self, return_id: str, supplier_id: int, item: dict) -> None:
        qty = float(item.get("quantity", 0))
        rate = float(item.get("return_rate", 0))
        cgst = float(item.get("cgst", 2.5))
        sgst = float(item.get("sgst", 2.5))
        total = round(rate * qty * (1 + (cgst + sgst) / 100), 2)
        self.execute(
            """INSERT INTO core_returnpurchasemaster
               (retailer_id, returninvoiceid_id, returnproduct_supplierid_id,
                returnproductid_id, returnproduct_batch_no, returnproduct_expiry,
                returnproduct_MRP, returnproduct_purchase_rate, returnproduct_quantity,
                returnproduct_free_qty, returnproduct_cgst, returnproduct_sgst,
                returntotal_amount, return_reason, returnpurchase_entry_date)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())""",
            (self.config.retailer_id, return_id, supplier_id,
             item["productid"], item.get("batch_no", ""), item.get("expiry", ""),
             float(item.get("mrp", 0)), rate, qty, float(item.get("free_qty", 0)),
             cgst, sgst, total, item.get("reason", ""))
        )
        self._recalc_purchase_return_total(return_id)
        
        # Deduct from stock cache
        item_copy = item.copy()
        if "purchase_rate" not in item_copy and "return_rate" in item_copy:
            item_copy["purchase_rate"] = item_copy["return_rate"]
        self.update_inventory_cache_purchase(item_copy, multiplier=-1.0)
        self.log_inventory_transaction(
            item["productid"],
            item.get("batch_no", ""),
            item.get("expiry", ""),
            "PURCHASE_RETURN",
            qty,
            float(item.get("free_qty", 0)),
            "PURCHASE_RETURN",
            0,
            return_id,
            rate,
            float(item.get("mrp", 0)),
            total,
            f"Purchase Return {return_id}"
        )

    def delete_purchase_return_item(self, item_id: int, return_id: str) -> None:
        # Get item details before deleting
        rows = self.query(
            "SELECT returnproductid_id, returnproduct_batch_no, returnproduct_quantity, returnproduct_free_qty "
            "FROM core_returnpurchasemaster WHERE returnpurchaseid=%s", (item_id,))
        
        if rows and self.table_exists("inventory_transaction"):
            item = rows[0]
            # Delete specific inventory transaction entry for this item
            self.execute(
                "DELETE FROM inventory_transaction WHERE retailer_id=%s AND reference_type='PURCHASE_RETURN' "
                "AND reference_number=%s AND product_id=%s AND batch_no=%s AND quantity=%s LIMIT 1",
                (self.config.retailer_id, return_id, item["returnproductid_id"], 
                 item["returnproduct_batch_no"], float(item["returnproduct_quantity"]))
            )
        
        self.execute("DELETE FROM core_returnpurchasemaster WHERE returnpurchaseid=%s", (item_id,))
        self._recalc_purchase_return_total(return_id)

    def _recalc_purchase_return_total(self, return_id: str) -> None:
        rows = self.query(
            "SELECT COALESCE(SUM(returntotal_amount),0) AS t, return_charges "
            "FROM core_returninvoicemaster ri "
            "LEFT JOIN core_returnpurchasemaster rpm ON rpm.returninvoiceid_id=ri.returninvoiceid "
            "WHERE ri.returninvoiceid=%s GROUP BY ri.return_charges", (return_id,))
        total = (float(rows[0]["t"]) + float(rows[0].get("return_charges") or 0)) if rows else 0.0
        self.execute("UPDATE core_returninvoicemaster SET returninvoice_total=%s WHERE returninvoiceid=%s",
                     (total, return_id))

    def delete_purchase_return(self, return_id: str) -> None:
        items = self.get_purchase_return_items(return_id)
        
        # Delete inventory transaction entries directly (no revert entries)
        if self.table_exists("inventory_transaction"):
            self.execute(
                "DELETE FROM inventory_transaction WHERE retailer_id=%s AND reference_type='PURCHASE_RETURN' AND reference_number=%s",
                (self.config.retailer_id, return_id)
            )
        
        # Add stock back to cache for each item
        for item in items:
            mapped_item = {
                "productid": item["returnproductid_id"],
                "batch_no": item["returnproduct_batch_no"],
                "expiry": item["returnproduct_expiry"],
                "quantity": float(item["returnproduct_quantity"]),
                "free_qty": float(item["returnproduct_free_qty"]),
                "mrp": float(item["returnproduct_MRP"]),
                "purchase_rate": float(item["returnproduct_purchase_rate"]),
            }
            # Revert purchase return in cache: add stock back. So multiplier is 1.0.
            self.update_inventory_cache_purchase(mapped_item, multiplier=1.0)
        
        # Delete detail and master records
        self.execute("DELETE FROM core_returnpurchasemaster WHERE returninvoiceid_id=%s", (return_id,))
        self.execute("DELETE FROM core_returninvoicemaster WHERE returninvoiceid=%s", (return_id,))

    # ── SALES RETURN CRUD ─────────────────────────────────────────────────────

    def fetch_sales_returns(self, search: str = "") -> list[dict[str, Any]]:
        where, params = self.retailer_where("core_returnsalesinvoicemaster", "rsi", required=False)
        if search:
            where += " AND (rsi.return_sales_invoice_no LIKE %s OR c.customer_name LIKE %s)"
            t = f"%{search}%"
            params += [t, t]
        return self.query(
            f"""SELECT rsi.return_sales_invoice_no, rsi.return_sales_invoice_date,
                       c.customer_name, rsi.return_sales_invoice_total,
                       rsi.return_sales_invoice_paid
                FROM core_returnsalesinvoicemaster rsi
                JOIN core_customermaster c ON c.customerid = rsi.return_sales_customerid_id
                WHERE 1=1{where}
                ORDER BY rsi.return_sales_invoice_date DESC LIMIT 500""", params)

    def get_sales_return(self, return_id: str) -> dict[str, Any] | None:
        rows = self.query(
            """SELECT rsi.*, c.customer_name FROM core_returnsalesinvoicemaster rsi
               JOIN core_customermaster c ON c.customerid = rsi.return_sales_customerid_id
               WHERE rsi.return_sales_invoice_no=%s""", (return_id,))
        return rows[0] if rows else None

    def get_sales_return_items(self, return_id: str) -> list[dict[str, Any]]:
        return self.query(
            "SELECT * FROM core_returnsalesmaster WHERE return_sales_invoice_no_id=%s ORDER BY return_sales_id",
            (return_id,))

    def _gen_sales_return_id(self) -> str:
        from datetime import date
        d = date.today().strftime("%Y%m%d")
        for i in range(1, 9999):
            rid = f"SR-{d}-{i:04d}"
            if not self.query("SELECT 1 FROM core_returnsalesinvoicemaster WHERE return_sales_invoice_no=%s", (rid,)):
                return rid
        return f"SR-{d}-9999"

    def create_sales_return(self, data: dict) -> str:
        rid = data.get("return_id") or self._gen_sales_return_id()
        self.execute(
            """INSERT INTO core_returnsalesinvoicemaster
               (return_sales_invoice_no, retailer_id, return_sales_invoice_date,
                return_sales_customerid_id, return_sales_charges, transport_charges,
                return_sales_invoice_total, return_sales_invoice_paid, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,0,0,NOW())""",
            (rid, self.config.retailer_id, data["return_date"],
             data["customer_id"], data.get("return_charges", 0), data.get("transport_charges", 0))
        )
        return rid

    def add_sales_return_item(self, return_id: str, customer_id: int, item: dict) -> None:
        qty = float(item.get("quantity", 0))
        rate = float(item.get("return_rate", 0))
        discount = float(item.get("discount", 0))
        cgst = float(item.get("cgst", 0))
        sgst = float(item.get("sgst", 0))
        base = rate * qty
        discounted = base - discount
        total = round(discounted * (1 + (cgst + sgst) / 100), 2)
        self.execute(
            """INSERT INTO core_returnsalesmaster
               (retailer_id, return_sales_invoice_no_id, return_customerid_id,
                return_productid_id, return_product_name, return_product_company,
                return_product_packing, return_product_batch_no, return_product_expiry,
                return_product_MRP, return_sale_rate, return_sale_quantity,
                return_sale_free_qty, return_sale_discount, return_sale_cgst,
                return_sale_sgst, return_sale_total_amount, return_reason,
                return_sale_entry_date, return_sale_calculation_mode)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),'flat')""",
            (self.config.retailer_id, return_id, customer_id,
             item["productid"], item.get("product_name", ""), item.get("product_company", ""),
             item.get("product_packing", ""), item.get("batch_no", ""), item.get("expiry", ""),
             float(item.get("mrp", 0)), rate, qty, float(item.get("free_qty", 0)),
             discount, cgst, sgst, total, item.get("reason", ""))
        )
        self._recalc_sales_return_total(return_id)
        
        # Update stock! Since it's a sales return, it should ADD to stock.
        # So multiplier is -1.0 for update_inventory_cache_sale (which subtracts multiplier * qty, i.e. subtracts -quantity = adds quantity).
        self.update_inventory_cache_sale(item, multiplier=-1.0)
        self.log_inventory_transaction(
            item["productid"],
            item.get("batch_no", ""),
            item.get("expiry", ""),
            "SALES_RETURN",
            qty,
            float(item.get("free_qty", 0)),
            "SALES_RETURN",
            0,
            return_id,
            rate,
            float(item.get("mrp", 0)),
            total,
            f"Sales Return {return_id}"
        )

    def delete_sales_return_item(self, item_id: int, return_id: str) -> None:
        # Get item details before deleting
        rows = self.query(
            "SELECT return_productid_id, return_product_batch_no, return_sale_quantity, return_sale_free_qty "
            "FROM core_returnsalesmaster WHERE return_sales_id=%s", (item_id,))
        
        if rows and self.table_exists("inventory_transaction"):
            item = rows[0]
            # Delete specific inventory transaction entry for this item
            self.execute(
                "DELETE FROM inventory_transaction WHERE retailer_id=%s AND reference_type='SALES_RETURN' "
                "AND reference_number=%s AND product_id=%s AND batch_no=%s AND quantity=%s LIMIT 1",
                (self.config.retailer_id, return_id, item["return_productid_id"], 
                 item["return_product_batch_no"], float(item["return_sale_quantity"]))
            )
        
        self.execute("DELETE FROM core_returnsalesmaster WHERE return_sales_id=%s", (item_id,))
        self._recalc_sales_return_total(return_id)

    def _recalc_sales_return_total(self, return_id: str) -> None:
        rows = self.query(
            "SELECT COALESCE(SUM(return_sale_total_amount),0) AS t, "
            "return_sales_charges, transport_charges "
            "FROM core_returnsalesinvoicemaster rsi "
            "LEFT JOIN core_returnsalesmaster rsm ON rsm.return_sales_invoice_no_id=rsi.return_sales_invoice_no "
            "WHERE rsi.return_sales_invoice_no=%s "
            "GROUP BY rsi.return_sales_charges, rsi.transport_charges", (return_id,))
        if rows:
            total = (float(rows[0]["t"]) + float(rows[0].get("return_sales_charges") or 0)
                     + float(rows[0].get("transport_charges") or 0))
        else:
            total = 0.0
        self.execute(
            "UPDATE core_returnsalesinvoicemaster SET return_sales_invoice_total=%s WHERE return_sales_invoice_no=%s",
            (total, return_id))

    def delete_sales_return(self, return_id: str) -> None:
        items = self.get_sales_return_items(return_id)
        
        # Delete inventory transaction entries directly (no revert entries)
        if self.table_exists("inventory_transaction"):
            self.execute(
                "DELETE FROM inventory_transaction WHERE retailer_id=%s AND reference_type='SALES_RETURN' AND reference_number=%s",
                (self.config.retailer_id, return_id)
            )
        
        # Deduct stock from cache for each item
        for item in items:
            mapped_item = {
                "productid": item["return_productid_id"],
                "batch_no": item["return_product_batch_no"],
                "expiry": item["return_product_expiry"],
                "quantity": float(item["return_sale_quantity"]),
                "free_qty": float(item["return_sale_free_qty"]),
                "mrp": float(item["return_product_MRP"]),
                "return_rate": float(item["return_sale_rate"]),
            }
            # Revert sales return in cache: deduct from stock. So multiplier is 1.0.
            self.update_inventory_cache_sale(mapped_item, multiplier=1.0)
        
        # Delete detail and master records
        self.execute("DELETE FROM core_returnsalesmaster WHERE return_sales_invoice_no_id=%s", (return_id,))
        self.execute("DELETE FROM core_returnsalesinvoicemaster WHERE return_sales_invoice_no=%s", (return_id,))

    def add_sales_return_payment(self, return_id: str, date: str, amount: float, mode: str, ref: str) -> None:
        self.execute(
            """INSERT INTO core_returnsalesinvoicepaid
               (return_sales_ip_invoice_no_id, return_sales_payment_date,
                return_sales_payment_amount, return_sales_payment_mode,
                return_sales_payment_ref_no)
               VALUES (%s,%s,%s,%s,%s)""",
            (return_id, date, amount, mode, ref))
        self.execute(
            "UPDATE core_returnsalesinvoicemaster SET return_sales_invoice_paid=return_sales_invoice_paid+%s WHERE return_sales_invoice_no=%s",
            (amount, return_id))

    # ── CHALLAN CRUD ──────────────────────────────────────────────────────────

    def fetch_supplier_challans(self, search: str = "") -> list[dict[str, Any]]:
        rid = self.config.retailer_id
        params: list[Any] = [rid]
        where = "WHERE c.retailer_id=%s"
        if search:
            where += " AND (c.challan_no LIKE %s OR s.supplier_name LIKE %s)"
            t = f"%{search}%"
            params += [t, t]
        return self.query(
            f"""SELECT c.challan_id, c.challan_no, c.challan_date, s.supplier_name,
                       c.challan_total, c.challan_paid,
                       IF(c.is_invoiced,'Invoiced','Pending') AS status
                FROM challan1 c
                JOIN core_suppliermaster s ON s.supplierid = c.supplier_id_id
                {where} ORDER BY c.challan_date DESC LIMIT 500""", params)

    def fetch_customer_challans(self, search: str = "") -> list[dict[str, Any]]:
        rid = self.config.retailer_id
        params: list[Any] = [rid]
        where = "WHERE c.retailer_id=%s"
        if search:
            where += " AND (c.customer_challan_no LIKE %s OR cm.customer_name LIKE %s)"
            t = f"%{search}%"
            params += [t, t]
        return self.query(
            f"""SELECT c.customer_challan_id, c.customer_challan_no, c.customer_challan_date,
                       cm.customer_name, c.challan_total, c.challan_invoice_paid,
                       IF(c.is_invoiced,'Invoiced','Pending') AS status
                FROM customer_challan c
                JOIN core_customermaster cm ON cm.customerid = c.customer_name_id_id
                {where} ORDER BY c.customer_challan_date DESC LIMIT 500""", params)

    def create_supplier_challan(self, data: dict) -> int:
        with self.cursor() as cur:
            cur.execute(
                """INSERT INTO challan1
                   (retailer_id, challan_no, challan_date, supplier_id_id,
                    challan_total, transport_charges, challan_paid,
                    challan_remark, is_invoiced, created_at, updated_at)
                   VALUES (%s,%s,%s,%s,0,%s,0,%s,0,NOW(),NOW())""",
                (self.config.retailer_id, data["challan_no"], data["challan_date"],
                 data["supplier_id"], data.get("transport_charges", 0),
                 data.get("remark", "None"))
            )
            return cur.lastrowid

    def create_customer_challan(self, data: dict) -> int:
        with self.cursor() as cur:
            cur.execute(
                """INSERT INTO customer_challan
                   (retailer_id, customer_challan_no, customer_challan_date,
                    customer_name_id_id, customer_transport_charges, challan_total,
                    challan_invoice_paid, is_invoiced, created_at, updated_at)
                   VALUES (%s,%s,%s,%s,%s,0,0,0,NOW(),NOW())""",
                (self.config.retailer_id, data["challan_no"], data["challan_date"],
                 data["customer_id"], data.get("transport_charges", 0))
            )
            return cur.lastrowid

    def delete_supplier_challan(self, challan_id: int) -> None:
        self.execute("DELETE FROM challan1 WHERE challan_id=%s", (challan_id,))

    def delete_customer_challan(self, challan_id: int) -> None:
        self.execute("DELETE FROM customer_challan WHERE customer_challan_id=%s", (challan_id,))

    # ── STOCK ISSUE CRUD ──────────────────────────────────────────────────────

    def fetch_stock_issues(self, search: str = "") -> list[dict[str, Any]]:
        rid = self.config.retailer_id
        params: list[Any] = [rid]
        where = "WHERE retailer_id=%s"
        if search:
            where += " AND (issue_no LIKE %s OR issue_type LIKE %s)"
            t = f"%{search}%"
            params += [t, t]
        return self.query(
            f"SELECT issue_id, issue_no, issue_date, issue_type, total_value, remarks "
            f"FROM stock_issue_master {where} ORDER BY issue_date DESC LIMIT 500", params)

    def get_stock_issue(self, issue_id: int) -> dict[str, Any] | None:
        rows = self.query("SELECT * FROM stock_issue_master WHERE issue_id=%s", (issue_id,))
        return rows[0] if rows else None

    def get_stock_issue_items(self, issue_id: int) -> list[dict[str, Any]]:
        return self.query(
            """SELECT sid.*, p.product_name FROM stock_issue_detail sid
               JOIN core_productmaster p ON p.productid = sid.product_id_id
               WHERE sid.issue_id_id=%s ORDER BY sid.detail_id""", (issue_id,))

    def _gen_issue_no(self) -> str:
        rows = self.query("SELECT issue_no FROM stock_issue_master ORDER BY issue_id DESC LIMIT 1")
        if rows:
            try:
                last = int(rows[0]["issue_no"].replace("SI", ""))
                return f"SI{last+1:06d}"
            except Exception:
                pass
        return "SI000001"

    def create_stock_issue(self, data: dict) -> int:
        issue_no = self._gen_issue_no()
        with self.cursor() as cur:
            cur.execute(
                """INSERT INTO stock_issue_master
                   (retailer_id, issue_no, issue_date, issue_type,
                    total_value, remarks, created_at, updated_at)
                   VALUES (%s,%s,%s,%s,0,%s,NOW(),NOW())""",
                (self.config.retailer_id, issue_no, data["issue_date"],
                 data["issue_type"], data.get("remarks", ""))
            )
            return cur.lastrowid

    def add_stock_issue_item(self, issue_id: int, item: dict) -> None:
        qty = float(item.get("quantity", 0))
        rate = float(item.get("rate", 0))
        total = round(qty * rate, 2)
        self.execute(
            """INSERT INTO stock_issue_detail
               (retailer_id, issue_id_id, product_id_id, batch_no, expiry_date,
                quantity_issued, unit_rate, total_amount, remarks)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (self.config.retailer_id, issue_id, item["productid"],
             item.get("batch_no", ""), item.get("expiry", ""),
             qty, rate, total, item.get("remarks", ""))
        )
        self._recalc_issue_total(issue_id)
        # Deduct issued stock from inventory cache
        self.update_inventory_cache_sale(
            {"productid": item["productid"], "batch_no": item.get("batch_no", ""),
             "expiry": item.get("expiry", ""), "quantity": qty, "free_qty": 0.0},
            multiplier=1.0
        )

    def _recalc_issue_total(self, issue_id: int) -> None:
        rows = self.query(
            "SELECT COALESCE(SUM(total_amount),0) AS t FROM stock_issue_detail WHERE issue_id_id=%s",
            (issue_id,))
        total = float(rows[0]["t"]) if rows else 0.0
        self.execute("UPDATE stock_issue_master SET total_value=%s WHERE issue_id=%s",
                     (total, issue_id))

    def delete_stock_issue_item(self, detail_id: int, issue_id: int) -> None:
        self.execute("DELETE FROM stock_issue_detail WHERE detail_id=%s", (detail_id,))
        self._recalc_issue_total(issue_id)

    def delete_stock_issue(self, issue_id: int) -> None:
        self.execute("DELETE FROM stock_issue_master WHERE issue_id=%s", (issue_id,))

    # ── CONTRA ENTRY CRUD ─────────────────────────────────────────────────────

    def fetch_contra_entries(self) -> list[dict[str, Any]]:
        return self.query(
            "SELECT contra_id, contra_no, contra_date, contra_type, "
            "from_account, to_account, amount, reference_no, narration "
            "FROM contra_entry ORDER BY contra_date DESC LIMIT 500"
        )

    def _gen_contra_no(self) -> str:
        rows = self.query("SELECT contra_no FROM contra_entry ORDER BY contra_id DESC LIMIT 1")
        if rows:
            try:
                last = int(rows[0]["contra_no"].replace("CE", ""))
                return f"CE{last+1:06d}"
            except Exception:
                pass
        return "CE000001"

    def create_contra(self, data: dict) -> int:
        no = self._gen_contra_no()
        with self.cursor() as cur:
            cur.execute(
                """INSERT INTO contra_entry
                   (contra_no, contra_date, contra_type, amount,
                    from_account, to_account, reference_no, narration, created_at, updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())""",
                (no, data["contra_date"], data["contra_type"], float(data["amount"]),
                 data["from_account"], data["to_account"],
                 data.get("reference_no", ""), data.get("narration", ""))
            )
            return cur.lastrowid

    def delete_contra(self, contra_id: int) -> None:
        self.execute("DELETE FROM contra_entry WHERE contra_id=%s", (contra_id,))

    # ── SUPPLIER / CUSTOMER FULL DETAIL ──────────────────────────────────────

    def get_supplier_full(self, supplier_id: int) -> dict[str, Any] | None:
        rows = self.query("SELECT * FROM core_suppliermaster WHERE supplierid=%s", (supplier_id,))
        return rows[0] if rows else None

    def create_supplier(self, data: dict) -> int:
        cols = ", ".join(data.keys())
        phs = ", ".join(["%s"] * len(data))
        with self.cursor() as cur:
            cur.execute(f"INSERT INTO core_suppliermaster ({cols}) VALUES ({phs})",
                        list(data.values()))
            return cur.lastrowid

    def update_supplier(self, supplier_id: int, data: dict) -> None:
        sets = ", ".join(f"{k}=%s" for k in data)
        self.execute(f"UPDATE core_suppliermaster SET {sets} WHERE supplierid=%s",
                     list(data.values()) + [supplier_id])

    def delete_supplier(self, supplier_id: int) -> None:
        self.execute("DELETE FROM core_suppliermaster WHERE supplierid=%s", (supplier_id,))

    def get_customer_full(self, customer_id: int) -> dict[str, Any] | None:
        rows = self.query("SELECT * FROM core_customermaster WHERE customerid=%s", (customer_id,))
        return rows[0] if rows else None

    def create_customer(self, data: dict) -> int:
        cols = ", ".join(data.keys())
        phs = ", ".join(["%s"] * len(data))
        with self.cursor() as cur:
            cur.execute(f"INSERT INTO core_customermaster ({cols}) VALUES ({phs})",
                        list(data.values()))
            return cur.lastrowid

    def update_customer(self, customer_id: int, data: dict) -> None:
        sets = ", ".join(f"{k}=%s" for k in data)
        self.execute(f"UPDATE core_customermaster SET {sets} WHERE customerid=%s",
                     list(data.values()) + [customer_id])

    def delete_customer(self, customer_id: int) -> None:
        self.execute("DELETE FROM core_customermaster WHERE customerid=%s", (customer_id,))

    def get_product_full(self, product_id: int) -> dict[str, Any] | None:
        rows = self.query("SELECT * FROM core_productmaster WHERE productid=%s", (product_id,))
        return rows[0] if rows else None

    def create_product(self, data: dict) -> int:
        cols = ", ".join(data.keys())
        phs = ", ".join(["%s"] * len(data))
        with self.cursor() as cur:
            cur.execute(f"INSERT INTO core_productmaster ({cols}) VALUES ({phs})",
                        list(data.values()))
            return cur.lastrowid

    def update_product(self, product_id: int, data: dict) -> None:
        sets = ", ".join(f"{k}=%s" for k in data)
        self.execute(f"UPDATE core_productmaster SET {sets} WHERE productid=%s",
                     list(data.values()) + [product_id])

    def delete_product(self, product_id: int) -> None:
        # Delete related inventory transactions
        if self.table_exists("inventory_transaction"):
            self.execute(
                "DELETE FROM inventory_transaction WHERE product_id=%s AND retailer_id=%s",
                (product_id, self.config.retailer_id)
            )
        
        # Delete product
        self.execute("DELETE FROM core_productmaster WHERE productid=%s", (product_id,))

    def fetch_backups(self) -> list[dict[str, Any]]:
        self.execute(
            """CREATE TABLE IF NOT EXISTS core_backup (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                retailer_id BIGINT,
                backup_filename VARCHAR(255) NOT NULL,
                backup_path VARCHAR(500) NOT NULL,
                backup_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'Success',
                file_size VARCHAR(50) DEFAULT '0 KB',
                INDEX idx_retailer (retailer_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"""
        )
        return self.query("SELECT * FROM core_backup WHERE retailer_id=%s ORDER BY backup_date DESC LIMIT 100", (self.config.retailer_id,))

    def log_backup(self, filename: str, filepath: str, status: str, file_size: str) -> None:
        self.execute(
            """CREATE TABLE IF NOT EXISTS core_backup (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                retailer_id BIGINT,
                backup_filename VARCHAR(255) NOT NULL,
                backup_path VARCHAR(500) NOT NULL,
                backup_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'Success',
                file_size VARCHAR(50) DEFAULT '0 KB',
                INDEX idx_retailer (retailer_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"""
        )
        self.execute(
            "INSERT INTO core_backup (retailer_id, backup_filename, backup_path, backup_date, status, file_size) "
            "VALUES (%s, %s, %s, NOW(), %s, %s)",
            (self.config.retailer_id, filename, filepath, status, file_size)
        )
