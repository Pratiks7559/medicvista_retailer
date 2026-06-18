from __future__ import annotations

import logging
from datetime import datetime


class SyncService:
    def __init__(self, app, db, poll_seconds: int):
        self.app = app
        self.db = db
        self.poll_ms = max(15, poll_seconds) * 1000
        self._job = None
        self.running = False

    def start(self) -> None:
        self.running = True
        self.sync_now(schedule_next=True)

    def stop(self) -> None:
        self.running = False
        if self._job:
            self.app.after_cancel(self._job)
            self._job = None

    def schedule(self) -> None:
        if self.running:
            self._job = self.app.after(self.poll_ms, lambda: self.sync_now(schedule_next=True))

    def sync_now(self, schedule_next: bool = False) -> None:
        try:
            self.app.set_status("Syncing retailer requests...")
            requests = self.db.fetch_requests(only_pending=True)
            processed = 0
            for request in requests:
                request_id = int(request["id"])
                try:
                    self.app.process_request(request)
                    self.db.mark_request_processed(request_id)
                    processed += 1
                except Exception as exc:
                    logging.exception("Request processing failed: %s", request_id)
                    self.db.mark_request_failed(request_id, str(exc))
            self.app.last_sync_at = datetime.now()
            self.app.on_sync_complete(processed)
        except Exception as exc:
            logging.exception("Sync failed")
            self.app.set_connection_state(False, str(exc))
        finally:
            if schedule_next:
                self.schedule()
