import pymysql

config = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "Pratik@123",
    "database": "medicvista_retailer",
    "charset": "utf8mb4",
}

conn = pymysql.connect(**config)
cur = conn.cursor()

cur.execute("SHOW TABLES;")
tables = [row[0] for row in cur.fetchall()]
print(f"Found {len(tables)} tables: {tables}")

cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
for table in tables:
    cur.execute(f"DELETE FROM `{table}`;")
    print(f"  Cleared: {table}")
cur.execute("SET FOREIGN_KEY_CHECKS = 1;")

conn.commit()
cur.close()
conn.close()
print("Done. All table data deleted.")
