import pymysql

config = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "Pratik@123",
    "database": "medicvista_retailer",
    "charset": "utf8mb4",
}

users = [
    (1, "retailer1", "retailer1", "BSL Pharmacy"),
    (2, "retailer2", "retailer2", "MedPlus Retail"),
    (3, "retailer3", "retailer3", "Apollo Pharmacy"),
    (4, "retailer4", "retailer4", "Wellness Forever"),
]

conn = pymysql.connect(**config)
cur = conn.cursor()

for retailer_id, username, password, full_name in users:
    cur.execute(
        "INSERT INTO retailer_users (retailer_id, username, password, full_name, is_active) "
        "VALUES (%s, %s, %s, %s, 1)",
        (retailer_id, username, password, full_name)
    )
    print(f"  Created: {username} / {password}  ->  {full_name}")

conn.commit()
cur.close()
conn.close()
print("Done. 4 retailer logins created.")
