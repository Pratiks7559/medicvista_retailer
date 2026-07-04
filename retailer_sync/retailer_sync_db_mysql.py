"""
retailer_sync_db_mysql.py
--------------------------
MySQL-based offline status-update queue.
Replaces SQLite with MySQL using medicvista_retailer database.

Table: retailer_pending_status_updates (already exists in medicvista_retailer)
"""

import logging
from datetime import datetime
from contextlib import contextmanager
import mysql.connector
from mysql.connector import Error

logger = logging.getLogger('retailer_sync')


class RetailerCacheDB:
    """
    MySQL-based offline queue for pending status updates.
    Uses medicvista_retailer database.
    """
    
    def __init__(self, db_config: dict = None):
        """
        Parameters
        ----------
        db_config : dict with keys: host, port, name (database), user, password
        """
        if db_config is None:
            # Default to local config
            db_config = {
                'host': 'localhost',
                'port': 3306,
                'name': 'medicvista_retailer',
                'user': 'root',
                'password': 'Pratik@123'
            }
        
        self.db_config = db_config
        self._ensure_table_exists()
        logger.info(
            "RetailerCacheDB initialized with MySQL: %s@%s/%s",
            db_config.get('user'),
            db_config.get('host'),
            db_config.get('name')
        )

    @contextmanager
    def _conn(self):
        """Context manager for MySQL connections."""
        conn = None
        try:
            conn = mysql.connector.connect(
                host=self.db_config['host'],
                port=self.db_config.get('port', 3306),
                database=self.db_config['name'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                autocommit=False
            )
            yield conn
            conn.commit()
        except Error as e:
            if conn:
                conn.rollback()
            logger.error("MySQL connection error: %s", e)
            raise
        finally:
            if conn and conn.is_connected():
                conn.close()

    def _ensure_table_exists(self):
        """
        Ensure retailer_pending_status_updates table exists.
        Table should already exist from medicvista_retailer schema.
        """
        try:
            with self._conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS retailer_pending_status_updates (
                        id BIGINT NOT NULL AUTO_INCREMENT,
                        request_id BIGINT NOT NULL,
                        new_status VARCHAR(30) NOT NULL,
                        queued_at DATETIME NOT NULL,
                        attempt_count INT NOT NULL DEFAULT 0,
                        PRIMARY KEY (id),
                        KEY idx_queued_at (queued_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                """)
                cursor.close()
            logger.debug("MySQL table retailer_pending_status_updates verified")
        except Error as e:
            logger.error("Failed to create/verify table: %s", e)
            raise

    # ------------------------------------------------------------------
    # pending_status_updates — offline queue
    # ------------------------------------------------------------------

    def queue_status_update(self, request_id: int, new_status: str):
        """Queue a status update that could not reach the wholesaler."""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with self._conn() as conn:
                cursor = conn.cursor()
                # Remove existing pending update for same request_id
                cursor.execute(
                    "DELETE FROM retailer_pending_status_updates WHERE request_id=%s",
                    (request_id,)
                )
                # Insert new pending update
                cursor.execute(
                    """
                    INSERT INTO retailer_pending_status_updates 
                    (request_id, new_status, queued_at, attempt_count) 
                    VALUES (%s, %s, %s, 0)
                    """,
                    (request_id, new_status, now)
                )
                cursor.close()
            logger.info(
                "Queued offline status update: request_id=%s status=%s",
                request_id, new_status
            )
        except Error as e:
            logger.error(
                "Failed to queue status update: request_id=%s error=%s",
                request_id, e
            )

    def get_pending_updates(self) -> list:
        """Retrieve all pending status updates, ordered by queued_at."""
        try:
            with self._conn() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT * FROM retailer_pending_status_updates ORDER BY queued_at ASC"
                )
                rows = cursor.fetchall()
                cursor.close()
                return rows
        except Error as e:
            logger.error("Failed to get pending updates: %s", e)
            return []

    def increment_attempt(self, queue_id: int):
        """Increment attempt count for a pending update."""
        try:
            with self._conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE retailer_pending_status_updates 
                    SET attempt_count = attempt_count + 1 
                    WHERE id=%s
                    """,
                    (queue_id,)
                )
                cursor.close()
        except Error as e:
            logger.error("Failed to increment attempt: queue_id=%s error=%s", queue_id, e)

    def remove_pending_update(self, queue_id: int):
        """Remove a pending update after successful delivery."""
        try:
            with self._conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM retailer_pending_status_updates WHERE id=%s",
                    (queue_id,)
                )
                cursor.close()
                logger.debug("Removed pending update: queue_id=%s", queue_id)
        except Error as e:
            logger.error("Failed to remove pending update: queue_id=%s error=%s", queue_id, e)
