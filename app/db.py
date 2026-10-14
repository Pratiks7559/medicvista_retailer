from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import date
from typing import Any, Iterable

from .date_utils import parse_date
from .inventory_date_sql import transaction_document_date_sql

logger = logging.getLogger('retailer_sync')

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
        self._invoice_financial_year_schema_ready = False
        self._inventory_transaction_schema_ready = False

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
                self._ensure_inventory_transaction_table()
                date_filter = ""
                params = [rid]
                if fy_start and fy_end:
                    invoice_date = transaction_document_date_sql("t")
                    date_filter = f" AND DATE({invoice_date}) BETWEEN %s AND %s"
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
        where, params = self.retailer_where("core_productmaster", required=False)
        if search:
            where += " AND (product_name LIKE %s OR product_company LIKE %s OR product_barcode LIKE %s)"
            term = f"%{search}%"
            params += [term, term, term]
        return self.query(
            f"""
            SELECT productid, product_name, product_company, product_packing,
                   product_category, product_hsn, product_hsn_percent, product_barcode, product_salt
            FROM core_productmaster
            WHERE 1=1{where}
            ORDER BY product_name
            LIMIT 500
            """,
            params,
        )

    def fetch_stock(self, search: str = "") -> list[dict[str, Any]]:
        """Batch-wise stock report from inventory_transaction table."""
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
                       WHEN STR_TO_DATE(CONCAT('01-', t.expiry_date), '%%d-%%m-%%Y') < CURDATE() THEN 'expired'
                       WHEN STR_TO_DATE(CONCAT('01-', t.expiry_date), '%%d-%%m-%%Y') < DATE_ADD(CURDATE(), INTERVAL 3 MONTH) THEN 'expiring_soon'
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
                   COALESCE(SUM(sm.sale_total_amount), 0)
                   + COALESCE(si.sales_transport_charges, 0)
                   - COALESCE(si.whole_discount_amount, 0) AS invoice_total,
                   COUNT(sm.id) AS item_count
            FROM core_salesinvoicemaster si
            JOIN core_customermaster c ON c.customerid = si.customerid_id
            LEFT JOIN core_salesmaster sm ON sm.sales_invoice_no_id = si.sales_invoice_no
            WHERE 1=1{where}
            GROUP BY si.sales_invoice_no, si.sales_invoice_date, c.customer_name,
                     si.sales_invoice_paid, si.sales_transport_charges, si.whole_discount_amount
            ORDER BY si.sales_invoice_date DESC, si.sales_invoice_no DESC
            LIMIT 500
            """,
            params,
        )

    def fetch_inventory(self, search: str = "") -> list[dict[str, Any]]:
        """Inventory data from inventory_transaction: purchase increases, sales decreases."""
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
                    p.productid AS productid,
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

    def fetch_inventory_datewise(
        self,
        search: str = "",
        date_from: str = "",
        date_to: str = "",
        use_invoice_date: bool = False,
    ) -> list[dict[str, Any]]:
        """Fetch date-wise inventory, optionally filtering by transaction or invoice date."""
        self._ensure_inventory_transaction_table()
        rid = self.config.retailer_id
        extra = ""
        date_expression = (
            f"DATE({transaction_document_date_sql('t')})"
            if use_invoice_date
            else "DATE(t.transaction_date)"
        )
        params: list[Any] = [rid]
        if search:
            extra += " AND (p.product_name LIKE %s OR p.product_company LIKE %s OR p.product_hsn LIKE %s)"
            term = f"%{search}%"
            params += [term, term, term]
        if date_from:
            extra += f" AND {date_expression} >= %s"
            params.append(date_from)
        if date_to:
            extra += f" AND {date_expression} <= %s"
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
        rid = self.config.retailer_id
        has_rid = self.column_exists("core_suppliermaster", "retailer_id")
        params: list[Any] = []
        if has_rid:
            params = [rid]
            where = "WHERE s.retailer_id = %s"
        else:
            where = "WHERE 1=1"
        if search:
            where += " AND (supplier_name LIKE %s OR supplier_mobile LIKE %s)"
            term = f"%{search}%"
            params += [term, term]
        bal_filter = "AND i.retailer_id = %s" if self.column_exists("core_invoicemaster", "retailer_id") else ""
        bal_params = [rid] if bal_filter else []
        rows = self.query(
            f"""
            SELECT s.supplierid, s.supplier_name, s.supplier_mobile, s.supplier_emailid,
                   s.supplier_address, s.supplier_gstno, s.supplier_dlno,
                   COALESCE((SELECT SUM(i.invoice_total - i.invoice_paid)
                              FROM core_invoicemaster i WHERE i.supplierid_id = s.supplierid
                              {bal_filter}), 0) AS balance
            FROM core_suppliermaster s
            {where}
            ORDER BY s.supplier_name LIMIT 500
            """,
            bal_params + params,
        )
        return rows

    def fetch_customers(self, search: str = "") -> list[dict[str, Any]]:
        if not self.table_exists("core_customermaster"): return []
        rid = self.config.retailer_id
        has_rid = self.column_exists("core_customermaster", "retailer_id")
        params: list[Any] = []
        if has_rid:
            params = [rid]
            where = "WHERE c.retailer_id = %s"
        else:
            where = "WHERE 1=1"
        if search:
            where += " AND (customer_name LIKE %s OR customer_mobile LIKE %s OR customer_emailid LIKE %s)"
            term = f"%{search}%"
            params += [term, term, term]
        bal_filter = "AND si.retailer_id = %s" if self.column_exists("core_salesinvoicemaster", "retailer_id") else ""
        bal_params = [rid] if bal_filter else []
        rows = self.query(
            f"""
            SELECT c.customerid, c.customer_name, c.customer_type, c.customer_mobile,
                   c.customer_emailid, c.customer_address, c.customer_dlno, c.customer_gstno,
                   c.customer_credit_days,
                   COALESCE((SELECT SUM(si.sales_invoice_paid)
                              FROM core_salesinvoicemaster si WHERE si.customerid_id = c.customerid
                              {bal_filter}), 0) AS paid_total
            FROM core_customermaster c
            {where}
            ORDER BY c.customer_name LIMIT 500
            """,
            bal_params + params,
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

    def fetch_sales_for_report(self, from_date: str, to_date: str, retailer_id: int,
                               product_ids: list = None) -> list:
        """Sales data for ERP report request. Filters by retailer_id and optionally by product_ids."""
        retailer_id = int(retailer_id)
        logger.info(
            "fetch_sales_for_report: retailer_id=%s from=%s to=%s product_ids=%s",
            retailer_id, from_date, to_date,
            product_ids if product_ids else 'ALL',
        )
        if not self.table_exists("core_salesmaster"):
            return []
        product_filter = ''
        params = [retailer_id, from_date, to_date]
        if product_ids:
            placeholders = ','.join(['%s'] * len(product_ids))
            product_filter = f' AND sm.productid_id IN ({placeholders})'
            params = [retailer_id, from_date, to_date] + list(product_ids)
        return self.query(
            f"""
            SELECT sm.sales_invoice_no_id AS invoice_no,
                   si.sales_invoice_date  AS invoice_date,
                   c.customer_name, c.customer_type,
                   sm.product_name, sm.product_company, sm.product_packing,
                   sm.product_batch_no AS batch_no, sm.product_expiry AS expiry,
                   sm.product_MRP AS mrp, sm.sale_rate, sm.sale_quantity AS quantity,
                   sm.sale_free_qty AS free_qty, sm.sale_discount AS discount,
                   sm.sale_cgst AS cgst, sm.sale_sgst AS sgst,
                   sm.sale_total_amount AS total_amount
            FROM core_salesmaster sm
            JOIN core_salesinvoicemaster si ON si.sales_invoice_no = sm.sales_invoice_no_id
            JOIN core_customermaster c ON c.customerid = sm.customerid_id
            WHERE sm.retailer_id = %s
              AND si.sales_invoice_date >= %s
              AND si.sales_invoice_date <= %s{product_filter}
            ORDER BY si.sales_invoice_date, sm.sales_invoice_no_id
            LIMIT 5000
            """,
            params,
        )

    def fetch_purchases_for_report(self, from_date: str, to_date: str, retailer_id: int,
                                   product_ids: list = None) -> list:
        """Purchase data for ERP report request. Filters by retailer_id and optionally by product_ids."""
        retailer_id = int(retailer_id)
        logger.info(
            "fetch_purchases_for_report: retailer_id=%s from=%s to=%s product_ids=%s",
            retailer_id, from_date, to_date,
            product_ids if product_ids else 'ALL',
        )
        if not self.table_exists("core_purchasemaster"):
            return []
        product_filter = ''
        params = [retailer_id, from_date, to_date]
        if product_ids:
            placeholders = ','.join(['%s'] * len(product_ids))
            product_filter = f' AND pm.productid_id IN ({placeholders})'
            params = [retailer_id, from_date, to_date] + list(product_ids)
        return self.query(
            f"""
            SELECT pm.product_invoice_no AS invoice_no,
                   i.invoice_date,
                   s.supplier_name,
                   pm.product_name, pm.product_company, pm.product_packing,
                   pm.product_batch_no AS batch_no, pm.product_expiry AS expiry,
                   pm.product_MRP AS mrp, pm.product_purchase_rate AS purchase_rate,
                   pm.product_quantity AS quantity, pm.product_free_qty AS free_qty,
                   pm.product_discount_got AS discount,
                   pm.CGST AS cgst, pm.SGST AS sgst,
                   pm.total_amount
            FROM core_purchasemaster pm
            JOIN core_invoicemaster i ON i.invoiceid = pm.product_invoiceid_id
            JOIN core_suppliermaster s ON s.supplierid = pm.product_supplierid_id
            WHERE pm.retailer_id = %s
              AND i.invoice_date >= %s
              AND i.invoice_date <= %s{product_filter}
            ORDER BY i.invoice_date, pm.product_invoice_no
            LIMIT 5000
            """,
            params,
        )

    def fetch_stock_for_report(self, retailer_id: int, product_ids: list = None,
                               from_date: str = '', to_date: str = '') -> list:
        """Batch-wise stock report. Filters by retailer_id, optionally by product_ids and date range."""
        retailer_id = int(retailer_id)
        logger.info("fetch_stock_for_report: retailer_id=%s product_ids=%s from=%s to=%s",
                    retailer_id, product_ids if product_ids else 'ALL', from_date, to_date)
        if not self.table_exists("inventory_transaction"):
            return []

        product_filter = ''
        date_filter = ''
        params = [retailer_id]
        if product_ids:
            placeholders = ','.join(['%s'] * len(product_ids))
            product_filter = f' AND t.product_id IN ({placeholders})'
            params = [retailer_id] + list(product_ids)
        if from_date:
            date_filter += ' AND DATE(t.transaction_date) >= %s'
            params.append(from_date)
        if to_date:
            date_filter += ' AND DATE(t.transaction_date) <= %s'
            params.append(to_date)

        rows = self.query(
            f"""
            SELECT
                p.productid,
                p.product_name,
                p.product_company,
                p.product_packing,
                p.product_hsn AS hsn,
                t.batch_no,
                t.expiry_date AS expiry,
                COALESCE(MAX(t.mrp), 0) AS mrp,
                COALESCE(MAX(t.rate), 0) AS purchase_rate,
                COALESCE(SUM(CASE WHEN t.transaction_type = 'PURCHASE' THEN t.quantity ELSE 0 END), 0) AS bought_qty,
                COALESCE(SUM(CASE WHEN t.transaction_type = 'PURCHASE' THEN t.free_quantity ELSE 0 END), 0) AS free_qty,
                COALESCE(SUM(CASE
                    WHEN t.transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') THEN t.quantity
                    WHEN t.transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') THEN -t.quantity
                    ELSE 0 END), 0) AS sold_qty,
                COALESCE(SUM(CASE
                    WHEN t.transaction_type = 'PURCHASE' THEN t.quantity
                    WHEN t.transaction_type IN ('PURCHASE_RETURN','REVERT_PURCHASE_RETURN','REVERT_PURCHASE') THEN -t.quantity
                    WHEN t.transaction_type IN ('SALE','STOCK_ISSUE','REVERT_SALE') THEN -t.quantity
                    WHEN t.transaction_type IN ('SALES_RETURN','REVERT_SALES_RETURN') THEN t.quantity
                    ELSE 0 END), 0) AS available_qty,
                MIN(CASE WHEN t.transaction_type = 'PURCHASE' THEN i.invoice_date ELSE NULL END) AS receive_date,
                MAX(CASE WHEN t.transaction_type = 'PURCHASE' THEN i.invoice_date ELSE NULL END) AS ac_date
            FROM inventory_transaction t
            JOIN core_productmaster p ON p.productid = t.product_id
            LEFT JOIN core_purchasemaster pm ON pm.productid_id = t.product_id
                AND pm.product_batch_no = t.batch_no
                AND pm.retailer_id = t.retailer_id
            LEFT JOIN core_invoicemaster i ON i.invoiceid = pm.product_invoiceid_id
            WHERE t.retailer_id = %s{product_filter}{date_filter}
            GROUP BY p.productid, p.product_name, p.product_company,
                     p.product_packing, p.product_hsn, t.batch_no, t.expiry_date
            HAVING available_qty > 0
            ORDER BY p.product_name, t.expiry_date
            LIMIT 5000
            """,
            params,
        )

        # Get supplier name per batch from core_purchasemaster (filtered by date if provided)
        supplier_map = {}
        if self.table_exists("core_purchasemaster") and self.table_exists("core_suppliermaster"):
            sup_params = [retailer_id]
            sup_date_filter = ''
            if from_date:
                sup_date_filter += ' AND i.invoice_date >= %s'
                sup_params.append(from_date)
            if to_date:
                sup_date_filter += ' AND i.invoice_date <= %s'
                sup_params.append(to_date)
            sup_rows = self.query(
                f"""
                SELECT pm.product_batch_no AS batch_no, pm.productid_id AS productid,
                       s.supplier_name
                FROM core_purchasemaster pm
                JOIN core_suppliermaster s ON s.supplierid = pm.product_supplierid_id
                JOIN core_invoicemaster i ON i.invoiceid = pm.product_invoiceid_id
                WHERE pm.retailer_id = %s{sup_date_filter}
                GROUP BY pm.productid_id, pm.product_batch_no, s.supplier_name
                """,
                sup_params
            )
            for sr in sup_rows:
                supplier_map[(sr['productid'], sr['batch_no'])] = sr['supplier_name']

        def _to_date_str(val) -> str:
            """Convert datetime.date / datetime.datetime / str to DD-MM-YYYY, or '' if None."""
            if val is None or val == '':
                return ''
            import datetime as _dt
            if isinstance(val, (_dt.datetime, _dt.date)):
                return val.strftime('%d-%m-%Y')
            s = str(val).strip()
            # YYYY-MM-DD → DD-MM-YYYY
            if len(s) >= 10 and s[4:5] == '-' and s[7:8] == '-':
                return s[8:10] + '-' + s[5:7] + '-' + s[:4]
            # already DD-MM-YYYY
            if len(s) == 10 and s[2:3] == '-' and s[5:6] == '-':
                return s
            # datetime string 'YYYY-MM-DD HH:MM:SS' — take date part only
            if len(s) > 10 and s[4:5] == '-':
                return _to_date_str(s[:10])
            return s

        for r in rows:
            pid = r['productid']
            # inventory_transaction already stores qty * packing — show as-is
            r['bought']          = float(r.get('bought_qty', 0))
            r['free_qty_raw']    = float(r.get('free_qty', 0))
            r['sold']            = float(r.get('sold_qty', 0))
            r['available_stock'] = float(r.get('available_qty', 0))
            r['supplier_name']   = supplier_map.get((pid, r.get('batch_no', '')), '')
            r['receive_date']    = _to_date_str(r.get('receive_date'))
            r['ac_date']         = _to_date_str(r.get('ac_date'))
        return rows

    def fetch_returns_for_report(self, from_date: str, to_date: str, retailer_id: int,
                                  product_ids: list = None) -> list:
        """Sales return data for ERP report request. Filters by retailer_id and optionally by product_ids."""
        retailer_id = int(retailer_id)
        logger.info(
            "fetch_returns_for_report: retailer_id=%s from=%s to=%s product_ids=%s",
            retailer_id, from_date, to_date,
            product_ids if product_ids else 'ALL',
        )
        if not self.table_exists("core_returnsalesmaster"):
            return []
        product_filter = ''
        params = [retailer_id, from_date, to_date]
        if product_ids:
            placeholders = ','.join(['%s'] * len(product_ids))
            product_filter = f' AND rsm.return_productid_id IN ({placeholders})'
            params = [retailer_id, from_date, to_date] + list(product_ids)
        return self.query(
            f"""
            SELECT rsi.return_sales_invoice_no AS invoice_no,
                   rsi.return_sales_invoice_date AS invoice_date,
                   c.customer_name,
                   rsm.return_product_name AS product_name,
                   rsm.return_product_company AS product_company,
                   rsm.return_product_packing AS product_packing,
                   rsm.return_product_batch_no AS batch_no,
                   rsm.return_product_expiry AS expiry,
                   rsm.return_product_MRP AS mrp,
                   rsm.return_sale_rate AS sale_rate,
                   rsm.return_sale_quantity AS quantity,
                   rsm.return_sale_free_qty AS free_qty,
                   rsm.return_sale_discount AS discount,
                   rsm.return_sale_cgst AS cgst,
                   rsm.return_sale_sgst AS sgst,
                   rsm.return_sale_total_amount AS total_amount
            FROM core_returnsalesmaster rsm
            JOIN core_returnsalesinvoicemaster rsi
                ON rsi.return_sales_invoice_no = rsm.return_sales_invoice_no_id
            JOIN core_customermaster c ON c.customerid = rsm.return_customerid_id
            WHERE rsm.retailer_id = %s
              AND rsi.return_sales_invoice_date >= %s
              AND rsi.return_sales_invoice_date <= %s{product_filter}
            ORDER BY rsi.return_sales_invoice_date, rsi.return_sales_invoice_no
            LIMIT 5000
            """,
            params,
        )

    def fetch_requests(
        self,
        status: str = "",
        request_type: str = "",
        date_text: str = "",
        only_pending: bool = False,
    ) -> list[dict[str, Any]]:
        if not self.table_exists("retailer_request"):
            return []
        # Ensure from_date / to_date / product_ids columns exist
        for col in ('from_date', 'to_date'):
            if not self.column_exists('retailer_request', col):
                self.execute(
                    f"ALTER TABLE retailer_request ADD COLUMN {col} VARCHAR(20) DEFAULT ''"
                )
        if not self.column_exists('retailer_request', 'product_ids'):
            self.execute(
                "ALTER TABLE retailer_request ADD COLUMN product_ids TEXT NULL"
            )
            self._columns_cache.pop(('retailer_request', 'product_ids'), None)
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
                   COALESCE(from_date, '') AS from_date, COALESCE(to_date, '') AS to_date,
                   COALESCE(product_ids, '') AS product_ids
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

    def get_requests(self, retailer_id: int) -> list[dict[str, Any]]:
        """
        Get all requests for a retailer, used by SyncBridge.get_cached_requests().
        Returns all requests ordered by created_at DESC.
        """
        if not self.table_exists("retailer_request"):
            return []
        return self.query(
            """
            SELECT id, request_type, reference_id, status, created_at, processed_at, remarks,
                   COALESCE(from_date, '') AS from_date, COALESCE(to_date, '') AS to_date,
                   COALESCE(product_ids, '') AS product_ids
            FROM retailer_request
            WHERE retailer_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT 500
            """,
            (retailer_id,),
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
        # Ensure from_date/to_date/product_ids columns exist
        for col, dtype in [('from_date', 'VARCHAR(20) DEFAULT ""'), ('to_date', 'VARCHAR(20) DEFAULT ""'), ('product_ids', 'TEXT NULL')]:
            if not self.column_exists('retailer_request', col.split()[0]):
                self.execute(f"ALTER TABLE retailer_request ADD COLUMN {col.split()[0]} {dtype}")
                self._columns_cache.pop(('retailer_request', col.split()[0]), None)
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
                     created_at, retailer_id, from_date, to_date, product_ids)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    r.get('product_ids', '') or '',
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
        if self.column_exists("core_suppliermaster", "retailer_id"):
            return self.query(
                "SELECT supplierid, supplier_name FROM core_suppliermaster WHERE retailer_id=%s ORDER BY supplier_name LIMIT 500",
                (self.config.retailer_id,)
            )
        return self.query(
            "SELECT supplierid, supplier_name FROM core_suppliermaster ORDER BY supplier_name LIMIT 500"
        )

    def get_customers_list(self) -> list[dict[str, Any]]:
        if self.column_exists("core_customermaster", "retailer_id"):
            return self.query(
                "SELECT customerid, customer_name, customer_type FROM core_customermaster WHERE retailer_id=%s ORDER BY customer_name LIMIT 500",
                (self.config.retailer_id,)
            )
        return self.query(
            "SELECT customerid, customer_name, customer_type FROM core_customermaster ORDER BY customer_name LIMIT 500"
        )

    def get_products_list(self) -> list[dict[str, Any]]:
        where, params = self.retailer_where("core_productmaster", required=False)
        return self.query(
            f"SELECT productid, product_name, product_company, product_packing, product_hsn_percent FROM core_productmaster WHERE 1=1{where} ORDER BY product_name LIMIT 2000",
            params
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

    def _ensure_whole_discount_column(self) -> None:
        """Add whole_discount_amount column to core_invoicemaster if missing."""
        if not self.column_exists("core_invoicemaster", "whole_discount_amount"):
            try:
                self.execute(
                    "ALTER TABLE core_invoicemaster "
                    "ADD COLUMN whole_discount_amount DECIMAL(10,2) NOT NULL DEFAULT 0"
                )
                self._columns_cache[("core_invoicemaster", "whole_discount_amount")] = True
            except Exception:
                pass

    def _ensure_sales_whole_discount_column(self) -> None:
        """Add whole_discount_amount column to core_salesinvoicemaster if missing."""
        if not self.column_exists("core_salesinvoicemaster", "whole_discount_amount"):
            try:
                self.execute(
                    "ALTER TABLE core_salesinvoicemaster "
                    "ADD COLUMN whole_discount_amount DECIMAL(10,2) NOT NULL DEFAULT 0"
                )
                self._columns_cache[("core_salesinvoicemaster", "whole_discount_amount")] = True
            except Exception:
                pass

    def _ensure_sales_calculation_mode_column(self) -> None:
        """Allow the percentage mode value used by the retailer sales form."""
        if not self.column_exists("core_salesmaster", "sale_calculation_mode"):
            return
        try:
            self.execute(
                "ALTER TABLE core_salesmaster "
                "MODIFY COLUMN sale_calculation_mode VARCHAR(10) "
                "NOT NULL DEFAULT 'flat'"
            )
        except Exception:
            pass

    def _ensure_purchase_calculation_mode_column(self) -> None:
        """Allow the percentage mode value used by the retailer invoice form."""
        if not self.column_exists("core_purchasemaster", "purchase_calculation_mode"):
            return
        try:
            self.execute(
                "ALTER TABLE core_purchasemaster "
                "MODIFY COLUMN purchase_calculation_mode VARCHAR(10) "
                "NOT NULL DEFAULT 'flat'"
            )
        except Exception:
            pass

    @staticmethod
    def _invoice_financial_year(invoice_date: str) -> str:
        normalized_date = parse_date(str(invoice_date))
        if not normalized_date:
            raise ValueError("Enter a valid invoice date.")
        parsed_date = date.fromisoformat(normalized_date)
        start_year = parsed_date.year if parsed_date.month >= 4 else parsed_date.year - 1
        return f"{start_year}-{(start_year + 1) % 100:02d}"

    def _ensure_invoice_financial_year_schema(self) -> None:
        if self._invoice_financial_year_schema_ready:
            return

        with self.cursor() as cur:
            cur.execute(
                "SHOW COLUMNS FROM core_invoicemaster LIKE %s",
                ("invoice_financial_year",),
            )
            financial_year_column = cur.fetchone()
            needs_date_backfill = financial_year_column is None
            if financial_year_column is None:
                cur.execute(
                    "ALTER TABLE core_invoicemaster "
                    "ADD COLUMN invoice_financial_year VARCHAR(7) NULL"
                )
            elif financial_year_column["Type"].lower() != "varchar(7)":
                needs_date_backfill = True
                cur.execute(
                    "ALTER TABLE core_invoicemaster "
                    "MODIFY COLUMN invoice_financial_year VARCHAR(7) NULL"
                )

            backfill_condition = "" if needs_date_backfill else (
                " WHERE invoice_financial_year IS NULL "
                "OR invoice_financial_year REGEXP '^[0-9]{4}$'"
            )
            cur.execute(
                """UPDATE core_invoicemaster
                   SET invoice_financial_year = CONCAT(
                       YEAR(invoice_date) - (MONTH(invoice_date) < 4),
                       '-',
                       LPAD(MOD(YEAR(invoice_date) - (MONTH(invoice_date) < 4) + 1, 100), 2, '0')
                   )"""
                + backfill_condition
            )
            if needs_date_backfill or financial_year_column["Null"] == "YES":
                cur.execute(
                    "ALTER TABLE core_invoicemaster "
                    "MODIFY COLUMN invoice_financial_year VARCHAR(7) NOT NULL"
                )
            cur.execute("SHOW INDEX FROM core_invoicemaster")
            index_names = {row["Key_name"] for row in cur.fetchall()}

            if "unique_supplier_invoice_fy" not in index_names:
                cur.execute(
                    "ALTER TABLE core_invoicemaster "
                    "ADD CONSTRAINT unique_supplier_invoice_fy "
                    "UNIQUE (invoice_no, supplierid_id, invoice_financial_year)"
                )
            if "unique_invoiceno_supplierid" in index_names:
                cur.execute(
                    "ALTER TABLE core_invoicemaster "
                    "DROP INDEX unique_invoiceno_supplierid"
                )

        self._columns_cache[("core_invoicemaster", "invoice_financial_year")] = True
        self._invoice_financial_year_schema_ready = True

    def invoice_number_exists_for_supplier_fy(
        self,
        invoice_no: str,
        supplier_id: int,
        invoice_date: str,
        exclude_invoice_id: int | None = None,
    ) -> bool:
        self._ensure_invoice_financial_year_schema()
        financial_year = self._invoice_financial_year(invoice_date)
        exclude_filter = " AND invoiceid<>%s" if exclude_invoice_id is not None else ""
        params = [invoice_no, supplier_id, self.config.retailer_id, financial_year]
        if exclude_invoice_id is not None:
            params.append(exclude_invoice_id)

        invoices = self.query(
            """SELECT invoice_financial_year
               FROM core_invoicemaster
               WHERE invoice_no=%s AND supplierid_id=%s AND retailer_id=%s
                 AND invoice_financial_year=%s"""
            + exclude_filter,
            params,
        )
        return bool(invoices)

    def create_invoice(self, data: dict) -> int:
        """Insert InvoiceMaster, return new invoiceid."""
        self._ensure_whole_discount_column()
        self._ensure_invoice_financial_year_schema()
        financial_year = self._invoice_financial_year(data["invoice_date"])
        with self.cursor() as cur:
            cur.execute(
                """INSERT INTO core_invoicemaster
                   (retailer_id, invoice_no, invoice_date, invoice_financial_year, supplierid_id,
                    transport_charges, invoice_total, whole_discount_amount, invoice_paid, payment_status)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,0,'pending')""",
                (
                    self.config.retailer_id,
                    data["invoice_no"], data["invoice_date"], financial_year,
                    data["supplierid"], data.get("transport_charges", 0),
                    data.get("invoice_total", 0),
                    data.get("whole_discount_amount", 0),
                )
            )
            return cur.lastrowid

    def update_invoice(self, invoice_id: int, data: dict) -> None:
        self._ensure_invoice_financial_year_schema()
        financial_year = self._invoice_financial_year(data["invoice_date"])
        self.execute(
            """UPDATE core_invoicemaster
               SET invoice_no=%s, invoice_date=%s, invoice_financial_year=%s, supplierid_id=%s,
                   transport_charges=%s, invoice_total=%s, whole_discount_amount=%s
               WHERE invoiceid=%s""",
            (data["invoice_no"], data["invoice_date"], financial_year, data["supplierid"],
             data.get("transport_charges", 0), data.get("invoice_total", 0),
             data.get("whole_discount_amount", 0),
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
        if self._inventory_transaction_schema_ready:
            return
        with self.cursor() as cur:
            cur.execute(
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
                    invoice_date DATE NULL,
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
            )
            cur.execute("SHOW COLUMNS FROM inventory_transaction LIKE %s", ("invoice_date",))
            if not cur.fetchone():
                cur.execute(
                    "ALTER TABLE inventory_transaction ADD COLUMN invoice_date DATE NULL"
                )

            cur.execute(
                """UPDATE inventory_transaction t
                   JOIN core_purchasemaster pm
                     ON pm.purchaseid = t.reference_id
                    AND pm.retailer_id = t.retailer_id
                   JOIN core_invoicemaster i
                     ON i.invoiceid = pm.product_invoiceid_id
                    AND i.retailer_id = t.retailer_id
                    AND i.invoice_no = t.reference_number
                   SET t.invoice_date = i.invoice_date
                   WHERE t.invoice_date IS NULL
                     AND t.transaction_type IN ('PURCHASE', 'REVERT_PURCHASE')"""
            )
            cur.execute(
                """UPDATE inventory_transaction t
                   JOIN core_invoicemaster i
                     ON i.invoiceid = t.reference_id
                    AND i.retailer_id = t.retailer_id
                    AND i.invoice_no = t.reference_number
                   SET t.invoice_date = i.invoice_date
                   WHERE t.invoice_date IS NULL
                     AND t.transaction_type IN ('PURCHASE', 'REVERT_PURCHASE')"""
            )
            cur.execute(
                """UPDATE inventory_transaction t
                   JOIN core_salesinvoicemaster si
                     ON si.sales_invoice_no = t.reference_number
                    AND si.retailer_id = t.retailer_id
                   SET t.invoice_date = si.sales_invoice_date
                   WHERE t.invoice_date IS NULL
                     AND t.transaction_type IN ('SALE', 'REVERT_SALE')"""
            )
            cur.execute(
                """UPDATE inventory_transaction t
                   JOIN core_returninvoicemaster ri
                     ON ri.returninvoiceid = t.reference_number
                    AND ri.retailer_id = t.retailer_id
                   SET t.invoice_date = ri.returninvoice_date
                   WHERE t.invoice_date IS NULL
                     AND t.transaction_type IN ('PURCHASE_RETURN', 'REVERT_PURCHASE_RETURN')"""
            )
            cur.execute(
                """UPDATE inventory_transaction t
                   JOIN core_returnsalesinvoicemaster rsi
                     ON rsi.return_sales_invoice_no = t.reference_number
                    AND rsi.retailer_id = t.retailer_id
                   SET t.invoice_date = rsi.return_sales_invoice_date
                   WHERE t.invoice_date IS NULL
                     AND t.transaction_type IN ('SALES_RETURN', 'REVERT_SALES_RETURN')"""
            )
        self._tables_cache["inventory_transaction"] = True
        self._columns_cache[("inventory_transaction", "invoice_date")] = True
        self._inventory_transaction_schema_ready = True

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
        invoice_date: str | None = None,
    ) -> None:
        try:
            self._ensure_inventory_transaction_table()
            if invoice_date is None:
                invoice_query = {
                    "PURCHASE": (
                        "SELECT invoice_date FROM core_invoicemaster "
                        "WHERE invoiceid=%s AND retailer_id=%s",
                        (reference_id, self.config.retailer_id),
                    ),
                    "SALE": (
                        "SELECT sales_invoice_date AS invoice_date "
                        "FROM core_salesinvoicemaster "
                        "WHERE sales_invoice_no=%s AND retailer_id=%s",
                        (reference_number, self.config.retailer_id),
                    ),
                    "PURCHASE_RETURN": (
                        "SELECT returninvoice_date AS invoice_date "
                        "FROM core_returninvoicemaster "
                        "WHERE returninvoiceid=%s AND retailer_id=%s",
                        (reference_number, self.config.retailer_id),
                    ),
                    "SALES_RETURN": (
                        "SELECT return_sales_invoice_date AS invoice_date "
                        "FROM core_returnsalesinvoicemaster "
                        "WHERE return_sales_invoice_no=%s AND retailer_id=%s",
                        (reference_number, self.config.retailer_id),
                    ),
                }.get(transaction_type)
                if invoice_query:
                    invoice_rows = self.query(*invoice_query)
                    if invoice_rows:
                        invoice_date = invoice_rows[0].get("invoice_date")
            self.execute(
                "INSERT INTO inventory_transaction "
                "(retailer_id, product_id, batch_no, expiry_date, transaction_type, "
                "quantity, free_quantity, transaction_date, invoice_date, reference_type, reference_id, "
                "reference_number, rate, mrp, total_value, created_at, created_by_id, remarks) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,NOW(),%s,%s,%s,%s,%s,%s,%s,NOW(),%s,%s)",
                (
                    self.config.retailer_id,
                    product_id,
                    batch_no or "",
                    expiry_date or "",
                    transaction_type,
                    quantity,
                    free_quantity,
                    invoice_date,
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
        self._ensure_purchase_calculation_mode_column()
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
        """Sum all items + transport - whole_discount and update invoice_total. Returns new total."""
        rows = self.query(
            "SELECT COALESCE(SUM(pm.total_amount),0) AS t, "
            "i.transport_charges, COALESCE(i.whole_discount_amount,0) AS whole_disc "
            "FROM core_invoicemaster i "
            "LEFT JOIN core_purchasemaster pm ON pm.product_invoiceid_id=i.invoiceid "
            "WHERE i.invoiceid=%s GROUP BY i.transport_charges, i.whole_discount_amount",
            (invoice_id,))
        if rows:
            total = (float(rows[0]["t"])
                     + float(rows[0].get("transport_charges") or 0)
                     - float(rows[0].get("whole_disc") or 0))
        else:
            total = 0.0
        self.execute("UPDATE core_invoicemaster SET invoice_total=%s WHERE invoiceid=%s",
                     (total, invoice_id))
        return total

    def get_customer_pending_invoices(self, customer_id: int) -> list[dict[str, Any]]:
        """Get all pending/partial sales invoices for a customer filtered by retailer_id, oldest first."""
        rid = self.config.retailer_id
        return self.query(
            """SELECT si.sales_invoice_no, si.sales_invoice_date,
                      si.sales_invoice_paid,
                      COALESCE((SELECT SUM(sale_total_amount) FROM core_salesmaster
                                WHERE sales_invoice_no_id=si.sales_invoice_no), 0) AS invoice_total,
                      ROUND(
                        COALESCE((SELECT SUM(sale_total_amount) FROM core_salesmaster
                                  WHERE sales_invoice_no_id=si.sales_invoice_no), 0)
                        - si.sales_invoice_paid, 2) AS balance
               FROM core_salesinvoicemaster si
               WHERE si.customerid_id=%s AND si.retailer_id=%s
                 AND ROUND(
                       COALESCE((SELECT SUM(sale_total_amount) FROM core_salesmaster
                                 WHERE sales_invoice_no_id=si.sales_invoice_no), 0)
                       - si.sales_invoice_paid, 2) > 0
               ORDER BY si.sales_invoice_date ASC, si.sales_invoice_no ASC""",
            (customer_id, rid)
        )

    def get_customer_advance_balance(self, customer_id: int) -> float:
        """Get total advance/overpayment credit for a customer."""
        rid = self.config.retailer_id
        self._ensure_customer_advance_table()
        rows = self.query(
            "SELECT COALESCE(SUM(advance_amount), 0) AS total FROM customer_advance_payment "
            "WHERE customer_id=%s AND retailer_id=%s",
            (customer_id, rid)
        )
        return float(rows[0]['total']) if rows else 0.0

    def _ensure_customer_advance_table(self) -> None:
        if not self.table_exists('customer_advance_payment'):
            self.execute(
                """CREATE TABLE IF NOT EXISTS customer_advance_payment (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    retailer_id BIGINT NOT NULL,
                    customer_id BIGINT NOT NULL,
                    advance_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
                    payment_date DATE NOT NULL,
                    payment_mode VARCHAR(30) DEFAULT 'Cash',
                    payment_ref_no VARCHAR(100) DEFAULT '',
                    notes VARCHAR(500) DEFAULT '',
                    created_at DATETIME DEFAULT NOW(),
                    INDEX idx_cust_ret (customer_id, retailer_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
            )
            self._tables_cache['customer_advance_payment'] = True

    def distribute_customer_payment(self, customer_id: int, pay_date: str, total_amount: float,
                                     mode: str, ref: str, notes: str = '') -> dict:
        """Distribute customer receipt across oldest pending sales invoices first.
        Overpayment stored as advance credit for future invoices."""
        rid = self.config.retailer_id
        self._ensure_customer_advance_table()
        invoices_paid = 0

        advance_bal = self.get_customer_advance_balance(customer_id)
        total_distributable = round(total_amount + advance_bal, 2)
        remaining = total_distributable

        pending = self.get_customer_pending_invoices(customer_id)
        for inv in pending:
            if remaining <= 0.009:
                break
            balance = round(float(inv['balance']), 2)
            pay = round(min(remaining, balance), 2)
            self.add_sales_payment(inv['sales_invoice_no'], pay_date, pay, mode, ref)
            remaining = round(remaining - pay, 2)
            invoices_paid += 1

        # Deduct used advance
        advance_used = round(advance_bal - max(0.0, remaining - total_amount), 2)
        if advance_used > 0.009:
            self.execute(
                "INSERT INTO customer_advance_payment "
                "(retailer_id, customer_id, advance_amount, payment_date, payment_mode, payment_ref_no, notes) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (rid, customer_id, -advance_used, pay_date, mode, ref, 'Advance used for invoices')
            )

        # Store overpayment as new advance
        advance_stored = round(min(remaining, total_amount), 2)
        if advance_stored > 0.009:
            self.execute(
                "INSERT INTO customer_advance_payment "
                "(retailer_id, customer_id, advance_amount, payment_date, payment_mode, payment_ref_no, notes) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (rid, customer_id, advance_stored, pay_date, mode, ref, notes or 'Overpayment advance')
            )

        return {'invoices_paid': invoices_paid, 'advance_stored': advance_stored, 'remaining': remaining}

    def get_supplier_pending_invoices(self, supplier_id: int) -> list[dict[str, Any]]:
        """Get all pending/partial invoices for a supplier filtered by retailer_id, oldest first."""
        rid = self.config.retailer_id
        return self.query(
            """SELECT invoiceid, invoice_no, invoice_date, invoice_total, invoice_paid,
                      ROUND(invoice_total - invoice_paid, 2) AS balance, payment_status
               FROM core_invoicemaster
               WHERE supplierid_id=%s AND retailer_id=%s
                 AND payment_status IN ('pending','partial')
                 AND invoice_total > invoice_paid
               ORDER BY invoice_date ASC, invoiceid ASC""",
            (supplier_id, rid)
        )

    def get_supplier_advance_balance(self, supplier_id: int) -> float:
        """Get total advance/overpayment credit for a supplier."""
        rid = self.config.retailer_id
        self._ensure_supplier_advance_table()
        rows = self.query(
            "SELECT COALESCE(SUM(advance_amount), 0) AS total FROM supplier_advance_payment "
            "WHERE supplier_id=%s AND retailer_id=%s",
            (supplier_id, rid)
        )
        return float(rows[0]['total']) if rows else 0.0

    def _ensure_supplier_advance_table(self) -> None:
        if not self.table_exists('supplier_advance_payment'):
            self.execute(
                """CREATE TABLE IF NOT EXISTS supplier_advance_payment (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    retailer_id BIGINT NOT NULL,
                    supplier_id BIGINT NOT NULL,
                    advance_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
                    payment_date DATE NOT NULL,
                    payment_mode VARCHAR(30) DEFAULT 'Cash',
                    payment_ref_no VARCHAR(100) DEFAULT '',
                    notes VARCHAR(500) DEFAULT '',
                    created_at DATETIME DEFAULT NOW(),
                    INDEX idx_sup_ret (supplier_id, retailer_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
            )
            self._tables_cache['supplier_advance_payment'] = True

    def distribute_supplier_payment(self, supplier_id: int, pay_date: str, total_amount: float,
                                     mode: str, ref: str, notes: str = '') -> dict:
        """Distribute payment + existing advance across oldest pending invoices first.
        Any leftover is stored as advance credit for future invoices."""
        rid = self.config.retailer_id
        self._ensure_supplier_advance_table()
        invoices_paid = 0

        advance_bal = self.get_supplier_advance_balance(supplier_id)
        total_distributable = round(total_amount + advance_bal, 2)
        remaining = total_distributable

        pending = self.get_supplier_pending_invoices(supplier_id)
        for inv in pending:
            if remaining <= 0.009:
                break
            balance = round(float(inv['balance']), 2)
            pay = round(min(remaining, balance), 2)
            self.add_invoice_payment(inv['invoiceid'], pay_date, pay, mode, ref)
            remaining = round(remaining - pay, 2)
            invoices_paid += 1

        # Deduct used advance
        advance_used = round(advance_bal - max(0.0, remaining - total_amount), 2)
        if advance_used > 0.009:
            self.execute(
                "INSERT INTO supplier_advance_payment "
                "(retailer_id, supplier_id, advance_amount, payment_date, payment_mode, payment_ref_no, notes) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (rid, supplier_id, -advance_used, pay_date, mode, ref, 'Advance used for invoices')
            )

        # Store overpayment as new advance
        advance_stored = round(min(remaining, total_amount), 2)
        if advance_stored > 0.009:
            self.execute(
                "INSERT INTO supplier_advance_payment "
                "(retailer_id, supplier_id, advance_amount, payment_date, payment_mode, payment_ref_no, notes) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (rid, supplier_id, advance_stored, pay_date, mode, ref, notes or 'Overpayment advance')
            )

        return {'invoices_paid': invoices_paid, 'advance_stored': advance_stored, 'remaining': remaining}

    def add_invoice_payment(self, invoice_id: int, date: str, amount: float, mode: str, ref: str) -> None:
        rid = self.config.retailer_id
        has_rid = self.column_exists('core_invoicepaid', 'retailer_id')
        if has_rid:
            self.execute(
                "INSERT INTO core_invoicepaid (retailer_id, ip_invoiceid_id, payment_date, payment_amount, payment_mode, payment_ref_no) VALUES (%s,%s,%s,%s,%s,%s)",
                (rid, invoice_id, date, amount, mode, ref)
            )
        else:
            self.execute(
                "INSERT INTO core_invoicepaid (ip_invoiceid_id, payment_date, payment_amount, payment_mode, payment_ref_no) VALUES (%s,%s,%s,%s,%s)",
                (invoice_id, date, amount, mode, ref)
            )
        self.execute(
            "UPDATE core_invoicemaster SET invoice_paid=invoice_paid+%s WHERE invoiceid=%s AND retailer_id=%s",
            (amount, invoice_id, rid)
        )
        self._update_invoice_payment_status(invoice_id)

    def _update_invoice_payment_status(self, invoice_id: int) -> None:
        rows = self.query(
            "SELECT invoice_total, invoice_paid FROM core_invoicemaster WHERE invoiceid=%s AND retailer_id=%s",
            (invoice_id, self.config.retailer_id))
        if rows:
            total = float(rows[0]["invoice_total"])
            paid = float(rows[0]["invoice_paid"])
            balance = total - paid
            status = "paid" if balance <= 0.01 else ("partial" if paid > 0 else "pending")
            self.execute("UPDATE core_invoicemaster SET payment_status=%s WHERE invoiceid=%s AND retailer_id=%s",
                         (status, invoice_id, self.config.retailer_id))

    def get_invoice_payments(self, invoice_id: int) -> list[dict[str, Any]]:
        rid = self.config.retailer_id
        has_rid = self.column_exists('core_invoicepaid', 'retailer_id')
        if has_rid:
            return self.query(
                "SELECT * FROM core_invoicepaid WHERE ip_invoiceid_id=%s AND retailer_id=%s ORDER BY payment_date DESC",
                (invoice_id, rid)
            )
        return self.query(
            "SELECT * FROM core_invoicepaid WHERE ip_invoiceid_id=%s ORDER BY payment_date DESC",
            (invoice_id,)
        )

    def delete_invoice_payment(self, payment_id: int) -> None:
        rid = self.config.retailer_id
        has_rid = self.column_exists('core_invoicepaid', 'retailer_id')
        if has_rid:
            rows = self.query(
                "SELECT ip_invoiceid_id, payment_amount FROM core_invoicepaid WHERE payment_id=%s AND retailer_id=%s",
                (payment_id, rid))
        else:
            rows = self.query(
                "SELECT ip_invoiceid_id, payment_amount FROM core_invoicepaid WHERE payment_id=%s",
                (payment_id,))
        if rows:
            self.execute("DELETE FROM core_invoicepaid WHERE payment_id=%s", (payment_id,))
            inv_id = rows[0]["ip_invoiceid_id"]
            amt = float(rows[0]["payment_amount"])
            self.execute(
                "UPDATE core_invoicemaster SET invoice_paid=GREATEST(0, invoice_paid-%s) WHERE invoiceid=%s AND retailer_id=%s",
                (amt, inv_id, rid))
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
        rid = self.config.retailer_id
        has_rid = self.column_exists('core_salesinvoicepaid', 'retailer_id')
        if has_rid:
            self.execute(
                "INSERT INTO core_salesinvoicepaid (retailer_id, sales_ip_invoice_no_id, sales_payment_date, sales_payment_amount, sales_payment_mode, sales_payment_ref_no) VALUES (%s,%s,%s,%s,%s,%s)",
                (rid, invoice_no, date, amount, mode, ref)
            )
        else:
            self.execute(
                "INSERT INTO core_salesinvoicepaid (sales_ip_invoice_no_id, sales_payment_date, sales_payment_amount, sales_payment_mode, sales_payment_ref_no) VALUES (%s,%s,%s,%s,%s)",
                (invoice_no, date, amount, mode, ref)
            )
        self.execute(
            "UPDATE core_salesinvoicemaster SET sales_invoice_paid=sales_invoice_paid+%s WHERE sales_invoice_no=%s AND retailer_id=%s",
            (amount, invoice_no, rid)
        )

    def get_sales_payments(self, invoice_no: str) -> list[dict[str, Any]]:
        rid = self.config.retailer_id
        has_rid = self.column_exists('core_salesinvoicepaid', 'retailer_id')
        if has_rid:
            return self.query(
                "SELECT * FROM core_salesinvoicepaid WHERE sales_ip_invoice_no_id=%s AND retailer_id=%s ORDER BY sales_payment_date DESC",
                (invoice_no, rid)
            )
        return self.query(
            "SELECT * FROM core_salesinvoicepaid WHERE sales_ip_invoice_no_id=%s ORDER BY sales_payment_date DESC",
            (invoice_no,)
        )

    def delete_sales_payment(self, payment_id: int) -> None:
        rid = self.config.retailer_id
        has_rid = self.column_exists('core_salesinvoicepaid', 'retailer_id')
        if has_rid:
            rows = self.query(
                "SELECT sales_ip_invoice_no_id, sales_payment_amount FROM core_salesinvoicepaid WHERE sales_payment_id=%s AND retailer_id=%s",
                (payment_id, rid))
        else:
            rows = self.query(
                "SELECT sales_ip_invoice_no_id, sales_payment_amount FROM core_salesinvoicepaid WHERE sales_payment_id=%s",
                (payment_id,))
        if rows:
            self.execute("DELETE FROM core_salesinvoicepaid WHERE sales_payment_id=%s", (payment_id,))
            inv_no = rows[0]["sales_ip_invoice_no_id"]
            amt = float(rows[0]["sales_payment_amount"])
            self.execute(
                "UPDATE core_salesinvoicemaster SET sales_invoice_paid=GREATEST(0, sales_invoice_paid-%s) WHERE sales_invoice_no=%s AND retailer_id=%s",
                (amt, inv_no, rid))

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

    def get_batches_for_product(self, product_id: int,
                                purchased_on_or_before: str = '') -> list[dict[str, Any]]:
        """Batches with stock > 0 for a product, from inventory_transaction.
        Only includes batches whose first PURCHASE transaction_date <= purchased_on_or_before.
        Returns quantity and free_quantity separately (NOT multiplied by packing)."""
        if not self.table_exists("inventory_transaction"):
            self._ensure_inventory_transaction_table()

        date_having = ""
        date_params: list[Any] = []
        if purchased_on_or_before:
            # HAVING clause: the earliest purchase date for this batch must be <= sale date
            date_having = " AND MIN(CASE WHEN t.transaction_type = 'PURCHASE' THEN DATE(t.transaction_date) ELSE NULL END) <= %s"
            date_params = [purchased_on_or_before]

        return self.query(
            f"""SELECT t.batch_no, t.expiry_date,
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
               HAVING (quantity > 0 OR free_quantity > 0){date_having}
               ORDER BY t.expiry_date""",
            [product_id, self.config.retailer_id] + date_params
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
        if self.column_exists("core_suppliermaster", "retailer_id"):
            rows = self.query("SELECT * FROM core_suppliermaster WHERE supplierid=%s AND retailer_id=%s",
                              (supplier_id, self.config.retailer_id))
        else:
            rows = self.query("SELECT * FROM core_suppliermaster WHERE supplierid=%s", (supplier_id,))
        return rows[0] if rows else None

    def create_supplier(self, data: dict) -> int:
        if self.column_exists("core_suppliermaster", "retailer_id"):
            data['retailer_id'] = self.config.retailer_id
        cols = ", ".join(data.keys())
        phs = ", ".join(["%s"] * len(data))
        with self.cursor() as cur:
            cur.execute(f"INSERT INTO core_suppliermaster ({cols}) VALUES ({phs})",
                        list(data.values()))
            return cur.lastrowid

    def update_supplier(self, supplier_id: int, data: dict) -> None:
        sets = ", ".join(f"{k}=%s" for k in data)
        if self.column_exists("core_suppliermaster", "retailer_id"):
            self.execute(f"UPDATE core_suppliermaster SET {sets} WHERE supplierid=%s AND retailer_id=%s",
                         list(data.values()) + [supplier_id, self.config.retailer_id])
        else:
            self.execute(f"UPDATE core_suppliermaster SET {sets} WHERE supplierid=%s",
                         list(data.values()) + [supplier_id])

    def delete_supplier(self, supplier_id: int) -> None:
        if self.column_exists("core_suppliermaster", "retailer_id"):
            self.execute("DELETE FROM core_suppliermaster WHERE supplierid=%s AND retailer_id=%s",
                         (supplier_id, self.config.retailer_id))
        else:
            self.execute("DELETE FROM core_suppliermaster WHERE supplierid=%s", (supplier_id,))

    def get_customer_full(self, customer_id: int) -> dict[str, Any] | None:
        if self.column_exists("core_customermaster", "retailer_id"):
            rows = self.query("SELECT * FROM core_customermaster WHERE customerid=%s AND retailer_id=%s",
                              (customer_id, self.config.retailer_id))
        else:
            rows = self.query("SELECT * FROM core_customermaster WHERE customerid=%s", (customer_id,))
        return rows[0] if rows else None

    def create_customer(self, data: dict) -> int:
        if self.column_exists("core_customermaster", "retailer_id"):
            data['retailer_id'] = self.config.retailer_id
        cols = ", ".join(data.keys())
        phs = ", ".join(["%s"] * len(data))
        with self.cursor() as cur:
            cur.execute(f"INSERT INTO core_customermaster ({cols}) VALUES ({phs})",
                        list(data.values()))
            return cur.lastrowid

    def update_customer(self, customer_id: int, data: dict) -> None:
        sets = ", ".join(f"{k}=%s" for k in data)
        if self.column_exists("core_customermaster", "retailer_id"):
            self.execute(f"UPDATE core_customermaster SET {sets} WHERE customerid=%s AND retailer_id=%s",
                         list(data.values()) + [customer_id, self.config.retailer_id])
        else:
            self.execute(f"UPDATE core_customermaster SET {sets} WHERE customerid=%s",
                         list(data.values()) + [customer_id])

    def delete_customer(self, customer_id: int) -> None:
        if self.column_exists("core_customermaster", "retailer_id"):
            self.execute("DELETE FROM core_customermaster WHERE customerid=%s AND retailer_id=%s",
                         (customer_id, self.config.retailer_id))
        else:
            self.execute("DELETE FROM core_customermaster WHERE customerid=%s", (customer_id,))

    def get_product_full(self, product_id: int) -> dict[str, Any] | None:
        where, params = self.retailer_where("core_productmaster", required=False)
        params.insert(0, product_id)
        rows = self.query(f"SELECT * FROM core_productmaster WHERE productid=%s{where}", params)
        return rows[0] if rows else None

    def create_product(self, data: dict) -> int:
        # Add retailer_id to product data
        data['retailer_id'] = self.config.retailer_id
        # Convert empty barcode to None — MySQL unique constraint allows multiple NULLs but not multiple ''
        if 'product_barcode' in data and not data['product_barcode']:
            data['product_barcode'] = None
        cols = ", ".join(data.keys())
        phs = ", ".join(["%s"] * len(data))
        with self.cursor() as cur:
            cur.execute(f"INSERT INTO core_productmaster ({cols}) VALUES ({phs})",
                        list(data.values()))
            return cur.lastrowid

    def update_product(self, product_id: int, data: dict) -> None:
        sets = ", ".join(f"{k}=%s" for k in data)
        where, where_params = self.retailer_where("core_productmaster", required=False)
        params = list(data.values()) + [product_id] + where_params
        self.execute(f"UPDATE core_productmaster SET {sets} WHERE productid=%s{where}", params)

    def delete_product(self, product_id: int) -> None:
        # Delete related inventory transactions
        if self.table_exists("inventory_transaction"):
            self.execute(
                "DELETE FROM inventory_transaction WHERE product_id=%s AND retailer_id=%s",
                (product_id, self.config.retailer_id)
            )
        
        # Delete product (with retailer_id check)
        where, params = self.retailer_where("core_productmaster", required=False)
        params.insert(0, product_id)
        self.execute(f"DELETE FROM core_productmaster WHERE productid=%s{where}", params)

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
