"""
retailer_sync_runner.py
-----------------------
Background sync loop. Talks to wholesaler API only.
All MySQL writes go through SyncBridge → app_db (your existing DB class).
SQLite is used ONLY for the offline status-update queue.
"""

import sys
import time
import logging
import json
import os
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def _load_config(config_path: str = None) -> dict:
    """
    Load sync config. Detects environment and loads appropriate JSON config.
    Returns config for ALL 4 retailers to run simultaneously.
    """
    import configparser
    
    # Detect environment from parent config files
    parent_dir = Path(__file__).parents[1]
    main_config_path = parent_dir / 'config.ini'
    environment = 'LOCAL'
    
    # ALWAYS re-read config.ini (no caching)
    if main_config_path.exists():
        parser = configparser.ConfigParser()
        parser.read(main_config_path)
        if parser.has_option('mode', 'environment'):
            environment = parser.get('mode', 'environment', fallback='LOCAL').upper()
    
    # Auto-select correct JSON config based on environment
    if config_path is None:
        base_dir = Path(__file__).parent
        if environment == 'CLOUD':
            config_path = base_dir / 'retailer_sync_config_cloud.json'
        else:
            config_path = base_dir / 'retailer_sync_config_local.json'
    
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            f"Environment: {environment}"
        )
    
    # Force reload JSON (no caching)
    with open(config_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    
    config = {k: v for k, v in raw.items() if not k.startswith('_comment')}
    
    # Log which config was loaded
    logging.getLogger('retailer_sync').info(
        f"Loaded config: {config_path.name} | Environment: {environment} | Server: {config.get('server_url')}"
    )
    
    # Return config with all retailers data intact
    # Individual retailer data will be extracted when creating SyncBridge instances
    return config


def get_retailer_config(base_config: dict, retailer_id: int) -> dict:
    """
    Extract config for a specific retailer from base config.
    Used to create individual SyncBridge instances for each retailer.
    """
    retailers = base_config.get('retailers', {})
    retailer_key = f'retailer{retailer_id}'
    
    if retailer_key not in retailers:
        raise ValueError(f"Retailer {retailer_id} not found in config")
    
    retailer_data = retailers[retailer_key]
    
    # Create retailer-specific config
    config = dict(base_config)
    config['retailer_id'] = retailer_data['retailer_id']
    config['retailer_name'] = retailer_data['retailer_name']
    config['retailer_code'] = retailer_data['retailer_code']
    config['api_key'] = retailer_data['api_key']
    
    # Remove the retailers dict to avoid confusion
    config.pop('retailers', None)
    
    return config


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def _setup_logging(log_file: str, level=logging.INFO):
    fmt = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding='utf-8'),
    ]
    logging.basicConfig(level=level, format=fmt, handlers=handlers)
    return logging.getLogger('retailer_sync')


# ---------------------------------------------------------------------------
# Sync runner
# ---------------------------------------------------------------------------

class RetailerSyncRunner:
    def __init__(self, config: dict, on_sync_complete=None, app_db=None):
        self.config             = config
        self.retailer_id        = int(config['retailer_id'])  # always int, never str
        self.sync_interval      = config.get('sync_interval_seconds', 60)
        self.on_sync_complete   = on_sync_complete
        self.app_db             = app_db  # MySQL DB instance for retailer

        from retailer_sync_service import RequestSyncService
        from retailer_sync_db_mysql import RetailerCacheDB

        self.service = RequestSyncService(
            server_url=config['server_url'],
            api_key=config['api_key'],
            timeout=config.get('request_timeout_seconds', 10),
        )
        # MySQL-based offline queue using medicvista_retailer database
        self.db = RetailerCacheDB(self._load_mysql_config())
        self.logger = logging.getLogger('retailer_sync')

        self._connected      = False
        self._last_sync_time = None
        self._stop_flag      = False
        self._wake_event     = __import__('threading').Event()

    def _load_mysql_config(self) -> dict:
        """
        Load MySQL database config from config.ini.
        Returns config dict for RetailerCacheDB.
        """
        import configparser
        parent_dir = Path(__file__).parents[1]
        config_path = parent_dir / 'config.ini'
        
        if not config_path.exists():
            # Fallback to default config
            self.logger.warning("config.ini not found, using default MySQL config")
            return {
                'host': 'localhost',
                'port': 3306,
                'name': 'medicvista_retailer',
                'user': 'root',
                'password': 'Pratik@123'
            }
        
        parser = configparser.ConfigParser()
        parser.read(config_path)
        
        return {
            'host': parser.get('database', 'host', fallback='localhost'),
            'port': parser.getint('database', 'port', fallback=3306),
            'name': parser.get('database', 'name', fallback='medicvista_retailer'),
            'user': parser.get('database', 'user', fallback='root'),
            'password': parser.get('database', 'password', fallback='Pratik@123')
        }

    # ------------------------------------------------------------------
    # Called by SyncBridge when user clicks Generate Report
    # ------------------------------------------------------------------

    def fetch_and_generate(self, wholesaler_request_id: int,
                           output_dir: str = 'retailer_reports') -> dict:
        """
        Full pipeline:
          1. Fetch request METADATA from wholesaler (no business data).
          2. GUARD: verify retailer_id matches this instance.
          3. Query THIS retailer's local MySQL for report data.
          4. Mark PROCESSING on wholesaler.
          5. Generate PDF + Excel + CSV locally.
          6. Upload CSV to wholesaler (up to 3 retries).
          7. Mark COMPLETED or FAILED on wholesaler.
             On failure also call /api/retailer/report-failed/ with error message.

        Returns: {ok, pdf_path, excel_path, csv_path, error}
        """
        from retailer_report_generator import ReportGenerator

        retailer_code = self.config.get('retailer_code', f'RTL{self.retailer_id:03d}')

        # Step 1 — fetch request metadata from wholesaler
        self.logger.info(
            "[Step 1] Fetching metadata: request_id=%s retailer_id=%s retailer_code=%s",
            wholesaler_request_id, self.retailer_id, retailer_code,
        )
        fetch = self.service.get_request_data(wholesaler_request_id)
        if not fetch['ok']:
            self.logger.error(
                "[Step 1] Metadata fetch FAILED id=%s: %s",
                wholesaler_request_id, fetch['error'],
            )
            return {'ok': False, 'pdf_path': None, 'excel_path': None,
                    'csv_path': None, 'error': fetch['error']}

        # Step 2 — CRITICAL GUARD: verify this request belongs to THIS retailer
        request_retailer_id = fetch.get('retailer_id')
        self.logger.info(
            "[Step 2] Security check: logged_in=%s request=%s request_id=%s type=%s from=%s to=%s",
            self.retailer_id, request_retailer_id,
            wholesaler_request_id, fetch.get('request_type'),
            fetch.get('from_date'), fetch.get('to_date'),
        )
        if request_retailer_id is not None and int(request_retailer_id) != int(self.retailer_id):
            err = (f'retailer_id mismatch: request={request_retailer_id} '
                   f'local={self.retailer_id}')
            self.logger.error("[Step 2] SECURITY BLOCK: %s", err)
            return {'ok': False, 'pdf_path': None, 'excel_path': None,
                    'csv_path': None, 'error': err}

        # Step 3 — query THIS retailer's local MySQL for actual report data
        self.logger.info(
            "[Step 3] Querying local DB: retailer_id=%s type=%s product_ids=%s",
            self.retailer_id, fetch.get('request_type'), fetch.get('product_ids', ''),
        )
        fetch = self._fetch_local_report_data(fetch)
        if not fetch['ok']:
            err = fetch['error']
            self.logger.error("[Step 3] Local DB query FAILED: %s", err)
            self.service.report_failed(wholesaler_request_id, err)
            return {'ok': False, 'pdf_path': None, 'excel_path': None,
                    'csv_path': None, 'error': err}

        self.logger.info(
            "[Step 3] Local DB query OK: %d rows fetched",
            len(fetch.get('data', [])),
        )

        # Step 4 — tell wholesaler we are processing
        self.logger.info("[Step 4] Marking PROCESSING: request_id=%s", wholesaler_request_id)
        self._send_status(wholesaler_request_id, 'PROCESSING')

        # Step 5 — generate PDF + Excel + CSV from local data
        self.logger.info(
            "[Step 5] Generating report files: type=%s retailer_code=%s",
            fetch.get('request_type'), retailer_code,
        )
        gen    = ReportGenerator(output_dir=output_dir, retailer_code=retailer_code)
        result = gen.generate(fetch)

        if not result['ok']:
            err = result['error']
            self.logger.error("[Step 5] Report generation FAILED id=%s: %s",
                              wholesaler_request_id, err)
            self._send_status(wholesaler_request_id, 'FAILED')
            self.service.report_failed(wholesaler_request_id, err)
            return result

        self.logger.info(
            "[Step 5] Files generated: pdf=%s excel=%s csv=%s",
            result['pdf_path'], result['excel_path'], result['csv_path'],
        )

        # Step 6 — upload CSV to wholesaler (with retry)
        csv_path = result.get('csv_path')
        if csv_path and os.path.exists(csv_path):
            self.logger.info(
                "[Step 6] Uploading CSV: request_id=%s file=%s",
                wholesaler_request_id, csv_path,
            )
            upload_result = self.service.upload_csv(
                request_id=wholesaler_request_id,
                request_type=fetch.get('request_type', 'STOCK'),
                csv_file_path=csv_path,
                retailer_code=retailer_code,
                max_retries=3,
            )
            if upload_result['ok']:
                self.logger.info(
                    "[Step 6] CSV upload SUCCESS: id=%s url=%s",
                    wholesaler_request_id, upload_result.get('file_url'),
                )
            else:
                err = upload_result.get('error', 'Upload failed')
                self.logger.error(
                    "[Step 6] CSV upload FAILED after retries: id=%s error=%s",
                    wholesaler_request_id, err,
                )
                # Upload failed — mark FAILED on ERP with error detail
                self._send_status(wholesaler_request_id, 'FAILED')
                self.service.report_failed(
                    wholesaler_request_id,
                    f'CSV upload failed after 3 retries: {err}',
                )
                # Keep local CSV — do NOT delete, caller may retry manually
                result['ok']    = False
                result['error'] = err
                return result
        else:
            self.logger.warning(
                "[Step 6] CSV file missing: id=%s path=%s",
                wholesaler_request_id, csv_path,
            )

        # Step 7 — CSV upload already marks COMPLETED on ERP via api_upload_csv.
        # Sending COMPLETED again would cause HTTP 400 "Cannot transition from COMPLETED to COMPLETED".
        # So we only log here — no duplicate status call.
        self.logger.info(
            "[Step 7] Pipeline COMPLETE: request_id=%s retailer=%s type=%s rows=%d",
            wholesaler_request_id, retailer_code,
            fetch.get('request_type'), len(fetch.get('data', [])),
        )
        return result

    def _fetch_local_report_data(self, metadata: dict) -> dict:
        """
        Query THIS retailer's local MySQL database for report data.
        Uses the request metadata (type, from_date, to_date, product_ids) received from ERP.
        The retailer_id used is always self.retailer_id — never from the request.
        product_ids: comma-separated string of product IDs to filter, empty = all products.
        """
        rtype      = metadata.get('request_type', '')
        from_date  = metadata.get('from_date', '')
        to_date    = metadata.get('to_date', '')
        request_id = metadata.get('request_id')

        # Parse product_ids filter: '1,2,3' → [1, 2, 3], '' → [] (means all)
        raw_pids = metadata.get('product_ids', '') or ''
        product_ids = [int(p.strip()) for p in raw_pids.split(',') if p.strip().isdigit()]

        self.logger.info(
            "_fetch_local_report_data: retailer_id=%s request_id=%s type=%s from=%s to=%s product_ids=%s",
            self.retailer_id, request_id, rtype, from_date, to_date,
            product_ids if product_ids else 'ALL',
        )

        if not self.app_db:
            return {'ok': False, 'error': 'No local database connection available'}

        try:
            # Ensure DB is connected before querying
            try:
                self.app_db.connect()
            except Exception as conn_err:
                self.logger.warning("app_db.connect() failed: %s — retrying query anyway", conn_err)

            if rtype == 'SALES':
                rows = self.app_db.fetch_sales_for_report(
                    from_date, to_date, self.retailer_id, product_ids
                )
            elif rtype == 'PURCHASE':
                rows = self.app_db.fetch_purchases_for_report(
                    from_date, to_date, self.retailer_id, product_ids
                )
            elif rtype == 'STOCK':
                rows = self.app_db.fetch_stock_for_report(
                    self.retailer_id, product_ids, from_date, to_date
                )
            elif rtype == 'RETURN':
                rows = self.app_db.fetch_returns_for_report(
                    from_date, to_date, self.retailer_id, product_ids
                )
            else:
                return {'ok': False, 'error': f'Unknown report type: {rtype}'}

            self.logger.info(
                "_fetch_local_report_data: retailer_id=%s type=%s rows=%d",
                self.retailer_id, rtype, len(rows),
            )

            result = dict(metadata)
            result['data']  = rows
            result['ok']    = True
            result['error'] = None
            return result

        except Exception as e:
            self.logger.exception(
                "_fetch_local_report_data failed: retailer_id=%s type=%s error=%s",
                self.retailer_id, rtype, e,
            )
            return {'ok': False, 'error': str(e)}

    def _send_status(self, request_id: int, status: str):
        """
        Send status to wholesaler. If offline, queue for later.
        Does NOT touch retailer MySQL — SyncBridge handles that.
        """
        result = self.service.update_status(request_id, status)
        if result['ok']:
            self.logger.info("Status sent: id=%s → %s", request_id, status)
        else:
            self.logger.warning(
                "Wholesaler offline, queuing status: id=%s → %s", request_id, status
            )
            self.db.queue_status_update(request_id, status)
    
    def push_status_update(self, request_id: int, status: str):
        """Public wrapper for _send_status - used by RetailerRequestsScreen."""
        self._send_status(request_id, status)

    # ------------------------------------------------------------------
    # Core sync cycle
    # ------------------------------------------------------------------

    def run_once(self):
        self.logger.info("--- Sync cycle start ---")
        new_requests = []
        error        = None

        conn_result      = self.service.test_connection()
        self._connected  = conn_result['connected']

        if not self._connected:
            error = conn_result['error']
            self.logger.warning(
                "Wholesaler unreachable [%s]: %s. Retry in %ds.",
                self.config['server_url'], error, self.sync_interval,
            )
            self._fire_callback(new_requests=[], error=error)
            return

        self.logger.info(
            "Connected [mode=%s server_time=%s]",
            conn_result.get('server_mode', '?'),
            conn_result.get('server_time', '?'),
        )

        # Flush offline queue first
        pending_queue = self.db.get_pending_updates()
        if pending_queue:
            self.logger.info("Flushing %d queued status updates...", len(pending_queue))
            self.service.sync_pending_updates(
                pending_queue,
                on_success=self._on_queue_success,
                on_fail=self._on_queue_fail,
            )

        # Fetch pending requests from wholesaler
        fetch_result = self.service.get_requests()
        if fetch_result['ok']:
            new_requests         = fetch_result['requests']
            self._last_sync_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.logger.info(
                "Fetched %d pending request(s). Last sync: %s",
                len(new_requests), self._last_sync_time,
            )
        else:
            error = fetch_result['error']
            self.logger.error("Failed to fetch requests: %s", error)

        # Check for deleted requests and cleanup from retailer MySQL
        self._cleanup_deleted_requests()

        self._fire_callback(new_requests=new_requests, error=error)
        self.logger.info("--- Sync cycle end ---")

    def _fire_callback(self, new_requests: list, error):
        if self.on_sync_complete:
            try:
                self.on_sync_complete({
                    'connected':      self._connected,
                    'last_sync_time': self._last_sync_time,
                    'new_requests':   new_requests,
                    'error':          error,
                })
            except Exception:
                self.logger.exception("Error in on_sync_complete callback")

    def force_wake(self):
        """Called by SyncBridge.force_sync_now() — interrupts current sleep immediately."""
        self._wake_event.set()

    def run_forever(self):
        self.logger.info(
            "Sync runner started. Server: %s | Interval: %ds",
            self.config['server_url'], self.sync_interval,
        )
        self._stop_flag = False
        self._wake_event.clear()
        while not self._stop_flag:
            try:
                self.run_once()
            except Exception:
                self.logger.exception("Unexpected error in sync cycle — continuing.")
            self._wake_event.wait(timeout=self.sync_interval)
            self._wake_event.clear()
        self.logger.info("Sync runner stopped.")

    def stop(self):
        self._stop_flag = True
        self._wake_event.set()   # unblock wait() immediately

    def _on_queue_success(self, queue_id: int, request_id: int, new_status: str):
        self.db.remove_pending_update(queue_id)
        self.logger.info("Flushed queued update: id=%s → %s", request_id, new_status)

    def _on_queue_fail(self, queue_id: int):
        self.db.increment_attempt(queue_id)

    def _cleanup_deleted_requests(self):
        """
        Check wholesaler for deleted requests and remove them from retailer MySQL.
        Called during each sync cycle.
        OPTIONAL: If endpoint returns 404, cleanup is skipped (backward compatibility).
        """
        if not self.app_db or not hasattr(self.app_db, 'get_all_reference_ids'):
            return  # No MySQL access, skip cleanup
        
        try:
            # Get all reference_ids from retailer MySQL
            known_ids = self.app_db.get_all_reference_ids(self.retailer_id)
            if not known_ids:
                return  # No requests in retailer DB
            
            # Ask wholesaler which of these IDs have been deleted
            ids_str = ','.join(str(i) for i in known_ids)
            # NOTE: API contract uses URL pattern /api/retailer/deleted-request-ids/
            # Some deployments may have an older/wrong routing that returns 404.
            url = self.service.server_url + '/api/retailer/deleted-request-ids/?ids=' + ids_str
            
            result = self.service._get(url, authenticated=True)
            if not result['ok']:
                # If 404, endpoint not implemented / wrong routing on this host — skip cleanup silently
                if '404' in str(result.get('error', '')):
                    self.logger.debug(
                        "Deleted request cleanup endpoint returned 404 (url=%s) - skipping",
                        url,
                    )
                    return

                # Defensive fallback: try with trailing slash after endpoint
                # (server_url + '/api/retailer/deleted-request-ids/' already correct for Django path)
                if 'deleted-request-ids' in url:
                    alt_url = self.service.server_url + '/api/retailer/deleted-request-ids/?ids=' + ids_str
                    # If alt_url equals url, no point retrying
                    if alt_url != url:
                        alt_result = self.service._get(alt_url, authenticated=True)
                        if alt_result.get('ok'):
                            deleted_ids = alt_result.get('data', {}).get('deleted_ids', [])
                        else:
                            self.logger.warning("Failed to fetch deleted IDs (fallback): %s", alt_result.get('error'))
                            return
                    else:
                        self.logger.warning("Failed to fetch deleted IDs: %s", result.get('error'))
                        return
                else:
                    self.logger.warning("Failed to fetch deleted IDs: %s", result['error'])
                    return
            
            deleted_ids = result['data'].get('deleted_ids', [])

            if deleted_ids:
                self.logger.info("Found %d deleted request(s) on wholesaler: %s", 
                               len(deleted_ids), deleted_ids)
                
                # Delete from retailer MySQL
                for ref_id in deleted_ids:
                    try:
                        self.app_db.delete_wholesaler_request(ref_id, self.retailer_id)
                        self.logger.info("Deleted request from retailer DB: reference_id=%s", ref_id)
                    except Exception as e:
                        self.logger.error("Failed to delete reference_id=%s: %s", ref_id, e)
                        
        except Exception as e:
            self.logger.exception("Cleanup deleted requests failed: %s", e)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Retailer sync runner')
    parser.add_argument('--config',    default=None)
    parser.add_argument('--once',      action='store_true')
    parser.add_argument('--test-conn', action='store_true')
    parser.add_argument('--status',    nargs=2, metavar=('REQUEST_ID', 'NEW_STATUS'))
    args = parser.parse_args()

    config = _load_config(args.config)
    _setup_logging(
        config.get('log_file', 'retailer_sync.log'),
        level=logging.DEBUG if os.getenv('SYNC_DEBUG') else logging.INFO,
    )

    runner = RetailerSyncRunner(config)

    if args.test_conn:
        result = runner.service.test_connection()
        if result['connected']:
            print(f"[OK] Connected  |  Mode: {result['server_mode']}  |  Server time: {result['server_time']}")
        else:
            print(f"[FAIL] Disconnected  |  Error: {result['error']}")
        sys.exit(0 if result['connected'] else 1)

    if args.status:
        request_id, new_status = int(args.status[0]), args.status[1].upper()
        runner._send_status(request_id, new_status)
        sys.exit(0)

    if args.once:
        runner.run_once()
        sys.exit(0)

    runner.run_forever()


if __name__ == '__main__':
    main()
