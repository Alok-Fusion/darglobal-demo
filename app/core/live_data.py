"""
Live knowledge base: keeps the chatbot's data fresh in the background.

A daemon thread refreshes the data on a schedule while the chatbot keeps
answering. Every question asks `get_engine()`, which hot-reloads the search
index when knowledge_base.json has changed, so new data is used from the next
question on with no restart. Files are swapped atomically, so a question never
sees half-written data.

Two refresh modes, picked automatically:
  * live   - Playwright is installed (local machine, or a Docker image built with
             the browser): scrape darglobal.co.uk + wasalt.sa and merge the
             new records into the existing data.
  * remote - no browser in this container (e.g. Render free tier): pull the
             knowledge base that the scheduled GitHub Action scraped and
             published, if it is newer than what this server has.
"""

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

from app.core.rag_engine import RAGEngine
from scraper.run_scrapers import KB_PATH, META_PATH, last_scrape_info, run_pipeline, write_json_atomic

logger = logging.getLogger("LiveData")

DATA_SYNC_BASE_URL = os.getenv(
    "DATA_SYNC_BASE_URL", "https://raw.githubusercontent.com/Alok-Fusion/darglobal-demo/main/data")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


class LiveKnowledgeBase:
    def __init__(self, kb_path: str = KB_PATH):
        self.kb_path = kb_path
        mode = os.getenv("REFRESH_MODE", "auto").lower()
        if mode == "auto":
            mode = "live" if _playwright_available() else "remote"
        self.mode = mode  # live | remote | off
        default_minutes = 360 if mode == "live" else 30
        self.interval = 60 * float(os.getenv("REFRESH_INTERVAL_MINUTES", default_minutes))
        self._engine: Optional[RAGEngine] = None
        self._mtime = 0.0
        self._reload_lock = threading.Lock()
        self._refresh_lock = threading.Lock()
        self._wake = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.status: Dict[str, Any] = {"mode": self.mode, "running": False, "last_run": None,
                                       "last_result": "not run yet", "next_run": None, "reloads": 0}
        self.get_engine()

    # ------------------------------------------------------------ reading
    def get_engine(self) -> RAGEngine:
        """The current search index; reloads it if the knowledge base file changed."""
        try:
            mtime = os.path.getmtime(self.kb_path)
        except OSError:
            mtime = 0.0
        if self._engine is None or mtime != self._mtime:
            with self._reload_lock:
                if self._engine is None or mtime != self._mtime:
                    if not os.path.exists(self.kb_path):
                        run_pipeline(live=False)  # rebuild from data/raw snapshots
                        mtime = os.path.getmtime(self.kb_path)
                    engine = RAGEngine(self.kb_path)
                    self._engine, self._mtime = engine, mtime
                    self.status["reloads"] += 1
                    self.status["loaded_at"] = _now()
                    self.status["records"] = len(engine.documents)
                    logger.info("knowledge base loaded: %d records", len(engine.documents))
        return self._engine

    @property
    def version(self) -> str:
        return str(last_scrape_info().get("built_at") or self._mtime)

    # ------------------------------------------------------------ refreshing
    def refresh_once(self) -> str:
        if self.mode == "off":
            return "refresh disabled"
        if not self._refresh_lock.acquire(blocking=False):
            return "a refresh is already running"
        self.status["running"] = True
        try:
            result = self._refresh_live() if self.mode == "live" else self._refresh_remote()
        except Exception as exc:
            logger.exception("background refresh failed")
            result = f"failed: {type(exc).__name__}: {exc}"[:300]
        finally:
            self.status["running"] = False
            self._refresh_lock.release()
        self.status["last_run"] = _now()
        self.status["last_result"] = result
        self.get_engine()  # pick up the new file right away
        return result

    def _refresh_live(self) -> str:
        before = self.status.get("records")
        run_pipeline(live=True, only=os.getenv("REFRESH_SOURCES", "all"))
        meta = last_scrape_info()
        parts = []
        for key in ("darglobal", "wasalt"):
            m = meta.get(key) or {}
            if m.get("status") == "live":
                parts.append(f"{key}: +{m.get('added', 0)} new, {m.get('updated', 0)} updated")
            else:
                parts.append(f"{key}: kept snapshot ({m.get('note', '')[:80]})")
        return f"live scrape done ({before} -> {meta.get('total_records')} records); " + "; ".join(parts)

    def _refresh_remote(self) -> str:
        meta_resp = requests.get(f"{DATA_SYNC_BASE_URL}/scrape_meta.json", timeout=20)
        if meta_resp.status_code == 404:
            return "no published data found yet; using the data bundled with this deploy"
        meta_resp.raise_for_status()
        remote_meta = meta_resp.json()
        local_built = str(last_scrape_info().get("built_at") or "")
        remote_built = str(remote_meta.get("built_at") or "")
        if not remote_built or remote_built <= local_built:
            return f"up to date (data built {local_built or 'unknown'})"
        resp = requests.get(f"{DATA_SYNC_BASE_URL}/knowledge_base.json", timeout=60)
        resp.raise_for_status()
        corpus = resp.json()
        if not isinstance(corpus, list) or len(corpus) < 10 or "search_text" not in corpus[0]:
            return "remote data looked invalid; kept current data"
        write_json_atomic(KB_PATH, corpus)
        write_json_atomic(META_PATH, remote_meta)
        return f"pulled newer data built {remote_built} ({len(corpus)} records)"

    # ------------------------------------------------------------ scheduling
    def start(self) -> "LiveKnowledgeBase":
        if self.mode == "off" or (self._thread and self._thread.is_alive()):
            return self
        self._thread = threading.Thread(target=self._loop, name="kb-refresher", daemon=True)
        self._thread.start()
        return self

    def trigger_now(self) -> None:
        """Ask the background thread to refresh now (returns immediately)."""
        self._wake.set()

    def _loop(self) -> None:
        # Remote mode checks soon after start so a fresh container picks up the latest data;
        # live mode waits one interval because the bundled data was just scraped.
        delay = 15 if self.mode == "remote" else self.interval
        while True:
            self.status["next_run"] = datetime.fromtimestamp(time.time() + delay, timezone.utc).strftime(
                "%Y-%m-%d %H:%M UTC")
            self._wake.wait(timeout=delay)
            self._wake.clear()
            self.refresh_once()
            delay = self.interval
