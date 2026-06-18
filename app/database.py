# D:/MEDICVISTA_RETAILER/Medicvist_retailer/app/database.py

import mysql.connector
from mysql.connector import Error

class Database:
    _instance = None

    def __new__(cls, db_config=None):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._connection = None
            cls._instance._cursor = None
            cls._instance._db_config = db_config
            if db_config:
                cls._instance.connect()
        return cls._instance

    def connect(self):
        if self._connection is None or not self._connection.is_connected():
            try:
                # Use provided config or defaults
                config = self._db_config if self._db_config else {}
                self._connection = mysql.connector.connect(
                    host=config.get('host', 'localhost'),
                    database=config.get('database', 'medicvista_retailer'),
                    user=config.get('user', 'root'),
                    password=config.get('password', 'abcdef'),
                    port=config.get('port', 3306)
                )
                if self._connection.is_connected():
                    self._cursor = self._connection.cursor(dictionary=True) # Return rows as dictionaries
                    print("Successfully connected to MySQL database")
                else:
                    print("Failed to connect to MySQL database")
            except Error as e:
                print(f"Error connecting to MySQL database: {e}")
                self._connection = None
                self._cursor = None
        return self._connection

    def disconnect(self):
        if self._connection and self._connection.is_connected():
            if self._cursor:
                self._cursor.close()
            self._connection.close()
            self._connection = None
            self._cursor = None
            print("MySQL connection closed")

    def get_connection(self):
        if self._connection is None or not self._connection.is_connected():
            self.connect()
        return self._connection

    def get_cursor(self):
        if self._cursor is None or not self._connection.is_connected():
            self.connect() # Reconnect if necessary
        return self._cursor

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False, commit=False):
        try:
            cursor = self.get_cursor()
            if cursor:
                cursor.execute(query, params or ())
                if commit:
                    self._connection.commit()
                if fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
                return cursor.rowcount # For INSERT/UPDATE/DELETE
        except Error as e:
            print(f"Database query error: {e}")
            if self._connection:
                self._connection.rollback() # Rollback on error
            return None

# Example usage (you'd configure this in your main app)
# DB_CONFIG = {
#     'host': 'localhost',
#     'database': 'medicvista_retailer',
#     'user': 'root',
#     'password': 'abcdef',
#     'port': 3306
# }
# db = Database(DB_CONFIG)