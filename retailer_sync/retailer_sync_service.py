"""
retailer_sync_service.py
------------------------
RequestSyncService — the ONLY place that talks to the wholesaler REST API.

Design principles
-----------------
* URL is always read from config — never hardcoded.
* Works identically on LOCAL (http) and CLOUD (https) — only the
  server_url value in config changes.
* Every method catches all network exceptions and returns a structured
  result dict so callers never crash on connectivity issues.
* Extensible request_type: adding a new type (e.g. GST, EXPIRY) requires
  zero changes here — types are passed through as plain strings.

Supported report types (current):   STOCK, PURCHASE, SALES
Supported report types (future):    GST, PROFIT_LOSS, EXPIRY,
                                    CUSTOMER_LEDGER, SUPPLIER_LEDGER,
                                    CUSTOM_REPORT — no code changes needed.
"""

import json
import logging
import time
import urllib.request
import urllib.error
import ssl
from datetime import datetime

logger = logging.getLogger('retailer_sync')


class RequestSyncService:
    """
    All wholesaler API communication lives here.

    Parameters
    ----------
    server_url : str
        Base URL with no trailing slash.
        LOCAL  example: 'http://192.168.1.100:8000'
        CLOUD  example: 'https://erp.company.com'
    api_key : str
        X-API-KEY value assigned to this retailer in wholesaler admin.
    timeout : int
        Per-request HTTP timeout in seconds.
    """

    # Endpoint paths — relative, so server_url swap is all that changes.
    _PATH_HEALTH   = '/api/retailer/health/'
    _PATH_PENDING  = '/api/retailer/pending-requests/'
    _PATH_DATA     = '/api/retailer/request-data/'
    _PATH_UPDATE   = '/api/retailer/update-status/'

    def __init__(self, server_url: str, api_key: str, timeout: int = 10):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def test_connection(self) -> dict:
        """
        Call the health endpoint WITH API key so retailer gets marked online.

        Returns
        -------
        {
            'connected': bool,
            'server_mode': str | None,   # 'LOCAL' or 'CLOUD'
            'server_time': str | None,
            'error': str | None,
            'checked_at': str,
        }
        """
        url = self.server_url + self._PATH_HEALTH
        result = self._get(url, authenticated=True)  # ← Changed to True!
        if result['ok']:
            return {
                'connected': True,
                'server_mode': result['data'].get('server_mode'),
                'server_time': result['data'].get('server_time'),
                'error': None,
                'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
        return {
            'connected': False,
            'server_mode': None,
            'server_time': None,
            'error': result['error'],
            'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    def get_requests(self) -> dict:
        """
        Fetch PENDING requests for this retailer.

        Returns
        -------
        {
            'ok': bool,
            'requests': list,   # list of request dicts on success, [] on failure
            'error': str | None,
        }
        """
        url = self.server_url + self._PATH_PENDING
        result = self._get(url, authenticated=True)
        if result['ok']:
            return {
                'ok': True,
                'requests': result['data'].get('requests', []),
                'error': None,
            }
        return {'ok': False, 'requests': [], 'error': result['error']}

    def get_request_data(self, request_id: int) -> dict:
        """
        Fetch raw report data for a specific request from the wholesaler.
        The wholesaler queries its own MySQL and returns structured JSON.
        The retailer never touches wholesaler MySQL directly.

        Returns
        -------
        {
            'ok': bool,
            'request_id': int,
            'request_type': str,
            'from_date': str,
            'to_date': str,
            'generated_at': str,
            'data': list,     # list of row dicts
            'error': str | None,
        }
        """
        url = self.server_url + self._PATH_DATA + str(request_id) + '/'
        result = self._get(url, authenticated=True)
        if result['ok']:
            return {
                'ok':           True,
                'request_id':   result['data'].get('request_id'),
                'retailer_id':  result['data'].get('retailer_id'),
                'request_type': result['data'].get('request_type'),
                'from_date':    result['data'].get('from_date'),
                'to_date':      result['data'].get('to_date'),
                'remarks':      result['data'].get('remarks', ''),
                'product_ids':  result['data'].get('product_ids', '') or '',
                'generated_at': result['data'].get('generated_at'),
                'data':         result['data'].get('data', []),
                'error':        None,
            }
        return {'ok': False, 'data': [], 'error': result['error']}

    def update_status(self, request_id: int, new_status: str) -> dict:
        """
        Push a status update to the wholesaler.

        Valid transitions enforced by server:
            PENDING → PROCESSING
            PROCESSING → COMPLETED | FAILED

        Returns
        -------
        {
            'ok': bool,
            'error': str | None,
        }
        """
        url = self.server_url + self._PATH_UPDATE
        payload = {'request_id': request_id, 'status': new_status}
        result = self._post(url, payload, authenticated=True)
        if result['ok']:
            return {'ok': True, 'error': None}
        return {'ok': False, 'error': result['error']}

    def sync_pending_updates(self, pending_queue: list, on_success, on_fail) -> int:
        """
        Attempt to flush the offline queue.

        Parameters
        ----------
        pending_queue : list of dicts from RetailerCacheDB.get_pending_updates()
        on_success    : callable(queue_id, request_id, new_status)
        on_fail       : callable(queue_id)

        Returns
        -------
        int : number of updates successfully sent
        """
        sent = 0
        for item in pending_queue:
            result = self.update_status(item['request_id'], item['new_status'])
            if result['ok']:
                on_success(item['id'], item['request_id'], item['new_status'])
                sent += 1
                logger.info(
                    "Flushed queued update: request_id=%s status=%s",
                    item['request_id'], item['new_status'],
                )
            else:
                # If 404 = request deleted on wholesaler, remove from queue
                if 'Request not found' in result.get('error', '') or '404' in result.get('error', ''):
                    logger.warning(
                        "Request deleted on wholesaler, removing from queue: request_id=%s",
                        item['request_id']
                    )
                    on_success(item['id'], item['request_id'], item['new_status'])  # Remove from queue
                # If 400 = invalid transition (already COMPLETED), remove from queue silently
                elif 'Cannot transition' in result.get('error', '') or '400' in result.get('error', ''):
                    logger.info(
                        "Status already synced (transition not needed), removing from queue: request_id=%s status=%s",
                        item['request_id'], item['new_status']
                    )
                    on_success(item['id'], item['request_id'], item['new_status'])  # Remove from queue
                else:
                    on_fail(item['id'])
                    logger.warning(
                        "Failed to flush queued update: request_id=%s error=%s",
                        item['request_id'], result['error'],
                    )
        return sent

    def upload_csv(self, request_id: int, request_type: str, csv_file_path: str,
                   retailer_code: str = '', max_retries: int = 3) -> dict:
        """
        Upload CSV file to wholesaler server with automatic retry.

        Parameters
        ----------
        request_id    : wholesaler request ID
        request_type  : STOCK, PURCHASE, SALES, or RETURN
        csv_file_path : full path to CSV file on local filesystem
        retailer_code : retailer code sent as generated_by field
        max_retries   : number of upload attempts before giving up (default 3)

        Returns
        -------
        {'ok': bool, 'upload_id': int|None, 'file_url': str|None, 'error': str|None}
        """
        import os
        import time as _time

        if not os.path.exists(csv_file_path):
            return {'ok': False, 'upload_id': None, 'file_url': None, 'error': 'CSV file not found'}

        url       = self.server_url + '/api/retailer/upload-csv/'
        file_name = os.path.basename(csv_file_path)
        last_error = 'Unknown error'

        for attempt in range(1, max_retries + 1):
            logger.info(
                "CSV upload attempt %d/%d: request_id=%s file=%s",
                attempt, max_retries, request_id, file_name,
            )
            try:
                with open(csv_file_path, 'rb') as f:
                    file_content = f.read()

                boundary = '----MedicVistaBoundary' + os.urandom(8).hex()

                body_parts = []
                for field_name, field_value in [
                    ('request_id',   str(request_id)),
                    ('request_type', request_type),
                    ('generated_by', retailer_code or ''),
                ]:
                    body_parts.append(f'--{boundary}'.encode())
                    body_parts.append(f'Content-Disposition: form-data; name="{field_name}"'.encode())
                    body_parts.append(b'')
                    body_parts.append(field_value.encode())

                body_parts.append(f'--{boundary}'.encode())
                body_parts.append(
                    f'Content-Disposition: form-data; name="csv_file"; filename="{file_name}"'.encode()
                )
                body_parts.append(b'Content-Type: text/csv; charset=utf-8')
                body_parts.append(b'')
                body_parts.append(file_content)
                body_parts.append(f'--{boundary}--'.encode())
                body_parts.append(b'')

                body = b'\r\n'.join(body_parts)
                headers = {
                    'Content-Type': f'multipart/form-data; boundary={boundary}',
                    'X-API-KEY':    self.api_key,
                }

                req = urllib.request.Request(url, data=body, headers=headers, method='POST')
                ssl_ctx = ssl._create_unverified_context() if url.startswith('https://') else None

                with urllib.request.urlopen(req, timeout=self.timeout,
                                            **(({'context': ssl_ctx}) if ssl_ctx else {})) as resp:
                    result = json.loads(resp.read().decode('utf-8'))

                if result.get('ok'):
                    logger.info(
                        "CSV upload SUCCESS: request_id=%s file=%s rows=%s size=%sKB attempt=%d",
                        request_id, file_name,
                        result.get('row_count', '?'), result.get('file_size_kb', '?'), attempt,
                    )
                    return {
                        'ok':        True,
                        'upload_id': result.get('upload_id'),
                        'file_url':  result.get('file_url'),
                        'error':     None,
                    }
                last_error = result.get('error', 'Server returned ok=False')
                logger.warning("CSV upload attempt %d failed (server): %s", attempt, last_error)

            except urllib.error.HTTPError as e:
                body_text = ''
                try:
                    body_text = e.read().decode('utf-8')
                except Exception:
                    pass
                last_error = f"HTTP {e.code}: {body_text[:200]}"
                logger.error("CSV upload attempt %d HTTP error: %s", attempt, last_error)

            except urllib.error.URLError as e:
                last_error = f"Connection failed: {e.reason}"
                logger.warning("CSV upload attempt %d connection error: %s", attempt, last_error)

            except Exception as e:
                last_error = f"Unexpected error: {e}"
                logger.exception("CSV upload attempt %d unexpected error", attempt)

            if attempt < max_retries:
                wait = 2 ** attempt  # exponential back-off: 2s, 4s
                logger.info("Retrying CSV upload in %ds...", wait)
                _time.sleep(wait)

        logger.error(
            "CSV upload FAILED after %d attempts: request_id=%s error=%s",
            max_retries, request_id, last_error,
        )
        return {'ok': False, 'upload_id': None, 'file_url': None, 'error': last_error}

    def report_failed(self, request_id: int, error_message: str) -> dict:
        """
        Notify ERP that report generation failed.
        Stores the error message on the ERP side for visibility.

        Returns {'ok': bool, 'error': str|None}
        """
        url     = self.server_url + '/api/retailer/report-failed/'
        payload = {'request_id': request_id, 'error_message': error_message[:1000]}
        result  = self._post(url, payload, authenticated=True)
        if result['ok']:
            logger.info("report_failed sent: request_id=%s", request_id)
            return {'ok': True, 'error': None}
        logger.warning("report_failed send failed: request_id=%s error=%s",
                       request_id, result['error'])
        return {'ok': False, 'error': result['error']}

    # ------------------------------------------------------------------
    # Private HTTP helpers — stdlib only, no external dependencies
    # ------------------------------------------------------------------

    def _get(self, url: str, authenticated: bool) -> dict:
        headers = {'Content-Type': 'application/json'}
        if authenticated:
            headers['X-API-KEY'] = self.api_key
        return self._request('GET', url, headers=headers, body=None)

    def _post(self, url: str, payload: dict, authenticated: bool) -> dict:
        headers = {'Content-Type': 'application/json'}
        if authenticated:
            headers['X-API-KEY'] = self.api_key
        body = json.dumps(payload).encode('utf-8')
        return self._request('POST', url, headers=headers, body=body)

    def _request(self, method: str, url: str, headers: dict, body) -> dict:
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        # For CLOUD HTTPS: Create SSL context
        # DEVELOPMENT: Disable SSL verification for self-signed certificates
        # PRODUCTION: Use ssl.create_default_context() for proper certificate validation
        if url.startswith('https://'):
            # Temporarily disable SSL verification for development
            ssl_context = ssl._create_unverified_context()
            logger.warning("SSL verification disabled for development. Enable in production!")
        else:
            ssl_context = None  # HTTP doesn't need SSL context

        try:
            if ssl_context:
                with urllib.request.urlopen(req, timeout=self.timeout, context=ssl_context) as resp:
                    raw = resp.read().decode('utf-8')
                    data = json.loads(raw)
                    return {'ok': True, 'data': data, 'error': None}
            else:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode('utf-8')
                    data = json.loads(raw)
                    return {'ok': True, 'data': data, 'error': None}

        except urllib.error.HTTPError as e:
            body_text = ''
            try:
                body_text = e.read().decode('utf-8')
            except Exception:
                pass
            error_msg = f"HTTP {e.code}: {body_text[:200]}"
            logger.error("API error [%s %s]: %s", method, url, error_msg)
            return {'ok': False, 'data': {}, 'error': error_msg}

        except urllib.error.URLError as e:
            error_msg = f"Connection failed: {e.reason}"
            logger.warning("Connectivity issue [%s %s]: %s", method, url, error_msg)
            return {'ok': False, 'data': {}, 'error': error_msg}

        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
            error_msg = f"Connection reset by server: {e}"
            logger.warning("Connection reset [%s %s]: %s", method, url, error_msg)
            return {'ok': False, 'data': {}, 'error': error_msg}

        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.warning("Unexpected error in _request [%s %s]: %s", method, url, e)
            return {'ok': False, 'data': {}, 'error': error_msg}
