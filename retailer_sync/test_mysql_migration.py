"""
Test script to verify MySQL migration works correctly.
Run this to ensure retailer_pending_status_updates table exists.
"""

import mysql.connector
from mysql.connector import Error

def test_mysql_connection():
    """Test MySQL connection and table existence."""
    config = {
        'host': 'localhost',
        'port': 3306,
        'database': 'medicvista_retailer',
        'user': 'root',
        'password': 'Pratik@123'
    }
    
    try:
        print("Connecting to MySQL...")
        conn = mysql.connector.connect(**config)
        
        if conn.is_connected():
            print(f"[OK] Connected to MySQL: {config['database']}")
            
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'medicvista_retailer' 
                AND table_name = 'retailer_pending_status_updates'
            """)
            exists = cursor.fetchone()[0]
            
            if exists:
                print("[OK] Table 'retailer_pending_status_updates' exists")
                
                # Show table structure
                cursor.execute("DESCRIBE retailer_pending_status_updates")
                print("\nTable structure:")
                for row in cursor.fetchall():
                    print(f"  {row[0]} - {row[1]}")
                
                # Count records
                cursor.execute("SELECT COUNT(*) FROM retailer_pending_status_updates")
                count = cursor.fetchone()[0]
                print(f"\n[OK] Current records: {count}")
                
            else:
                print("[ERROR] Table 'retailer_pending_status_updates' NOT FOUND")
                print("\nCreating table...")
                cursor.execute("""
                    CREATE TABLE retailer_pending_status_updates (
                        id BIGINT NOT NULL AUTO_INCREMENT,
                        request_id BIGINT NOT NULL,
                        new_status VARCHAR(30) NOT NULL,
                        queued_at DATETIME NOT NULL,
                        attempt_count INT NOT NULL DEFAULT 0,
                        PRIMARY KEY (id),
                        KEY idx_queued_at (queued_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                """)
                conn.commit()
                print("[OK] Table created successfully")
            
            cursor.close()
            conn.close()
            print("\n[OK] All tests passed - MySQL migration successful!")
            return True
            
    except Error as e:
        print(f"[ERROR] MySQL Error: {e}")
        return False

if __name__ == '__main__':
    test_mysql_connection()
