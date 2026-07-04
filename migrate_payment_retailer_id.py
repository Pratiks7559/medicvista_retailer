"""
migrate_payment_retailer_id.py
-------------------------------
Adds retailer_id column to core_invoicepaid and core_salesinvoicepaid tables.
Also fills existing rows with correct retailer_id from parent invoice tables.

Run:
    python migrate_payment_retailer_id.py
"""

import pymysql
import configparser

# ── Load config ──────────────────────────────────────────────────────────────
p = configparser.ConfigParser()
p.read('config.ini')

conn = pymysql.connect(
    host     = p.get('database', 'host',     fallback='localhost'),
    port     = p.getint('database', 'port',  fallback=3306),
    user     = p.get('database', 'user',     fallback='root'),
    password = p.get('database', 'password', fallback=''),
    database = p.get('database', 'name',     fallback='medicvista_retailer'),
    charset  = 'utf8mb4',
)
cur = conn.cursor()

def column_exists(table, column):
    cur.execute(f"SHOW COLUMNS FROM `{table}` LIKE %s", (column,))
    return bool(cur.fetchone())

print("=" * 55)
print("  MedicVista Payment Tables - retailer_id Migration")
print("=" * 55)

# ── 1. core_invoicepaid ───────────────────────────────────────────────────────
print("\n[1] core_invoicepaid ...")
if not column_exists('core_invoicepaid', 'retailer_id'):
    cur.execute("ALTER TABLE core_invoicepaid ADD COLUMN retailer_id BIGINT NULL")
    conn.commit()
    print("    Column added.")
else:
    print("    Column already exists.")

# Fill retailer_id from core_invoicemaster via ip_invoiceid_id
cur.execute("""
    UPDATE core_invoicepaid ip
    JOIN core_invoicemaster i ON i.invoiceid = ip.ip_invoiceid_id
    SET ip.retailer_id = i.retailer_id
    WHERE ip.retailer_id IS NULL
""")
conn.commit()
print(f"    Filled {cur.rowcount} rows with retailer_id.")

# ── 2. core_salesinvoicepaid ──────────────────────────────────────────────────
print("\n[2] core_salesinvoicepaid ...")
if not column_exists('core_salesinvoicepaid', 'retailer_id'):
    cur.execute("ALTER TABLE core_salesinvoicepaid ADD COLUMN retailer_id BIGINT NULL")
    conn.commit()
    print("    Column added.")
else:
    print("    Column already exists.")

# Fill retailer_id from core_salesinvoicemaster via sales_ip_invoice_no_id
cur.execute("""
    UPDATE core_salesinvoicepaid sip
    JOIN core_salesinvoicemaster si ON si.sales_invoice_no = sip.sales_ip_invoice_no_id
    SET sip.retailer_id = si.retailer_id
    WHERE sip.retailer_id IS NULL
""")
conn.commit()
print(f"    Filled {cur.rowcount} rows with retailer_id.")

# ── 3. Verify ─────────────────────────────────────────────────────────────────
print("\n[3] Verification ...")
cur.execute("SELECT retailer_id, COUNT(*) as cnt FROM core_invoicepaid GROUP BY retailer_id")
rows = cur.fetchall()
print("    core_invoicepaid by retailer_id:")
for r in rows:
    print(f"      retailer_id={r[0]}  rows={r[1]}")

cur.execute("SELECT retailer_id, COUNT(*) as cnt FROM core_salesinvoicepaid GROUP BY retailer_id")
rows = cur.fetchall()
print("    core_salesinvoicepaid by retailer_id:")
for r in rows:
    print(f"      retailer_id={r[0]}  rows={r[1]}")

cur.close()
conn.close()

print("\n Migration complete!")
print("=" * 55)
