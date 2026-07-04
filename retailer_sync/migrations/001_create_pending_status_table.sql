-- ============================================================
-- Migration: Ensure retailer_pending_status_updates exists
-- Database: medicvista_retailer
-- ============================================================

-- Create table if not exists
CREATE TABLE IF NOT EXISTS retailer_pending_status_updates (
    id BIGINT NOT NULL AUTO_INCREMENT,
    request_id BIGINT NOT NULL,
    new_status VARCHAR(30) NOT NULL,
    queued_at DATETIME NOT NULL,
    attempt_count INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    KEY idx_queued_at (queued_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Verify table exists
SELECT 'Table retailer_pending_status_updates created/verified' AS status;

-- Show current records (if any)
SELECT COUNT(*) AS pending_updates_count FROM retailer_pending_status_updates;
