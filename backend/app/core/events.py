import os
import time
import logging
from threading import Thread
from typing import Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
from app.core.config import settings
from app.services.rag_engine import rag_engine

logger = logging.getLogger("watchdog_daemon")

class MarkdownChangeHandler(FileSystemEventHandler):
    def __init__(self, debounce_seconds: float = 1.5):
        super().__init__()
        self.debounce_seconds = debounce_seconds
        self.last_triggered: Dict[str, float] = {}

    def on_modified(self, event):
        self._handle_event(event)

    def on_created(self, event):
        self._handle_event(event)

    def _handle_event(self, event):
        if event.is_directory:
            return
        file_path = event.src_path
        if not file_path.endswith(".md"):
            return

        now = time.time()
        last_time = self.last_triggered.get(file_path, 0.0)
        if (now - last_time) < self.debounce_seconds:
            return

        self.last_triggered[file_path] = now
        logger.info(f"File event detected on Markdown note: {os.path.basename(file_path)}")

        # Kích hoạt RAG re-index ngầm
        try:
            Thread(target=rag_engine.index_markdown_file, args=(file_path,), daemon=True).start()
        except Exception as e:
            logger.error(f"Failed to auto-index file {file_path}: {e}")

class WatchdogDaemon:
    def __init__(self):
        self.observer: Optional[Observer] = None
        self.is_running = False

    def start(self):
        if not settings.WATCHDOG_ENABLED:
            logger.info("Watchdog daemon disabled by configuration.")
            return

        content_path = settings.CONTENT_DIR
        if not os.path.exists(content_path):
            logger.warning(f"Content directory does not exist for Watchdog: {content_path}")
            return

        logger.info(f"Starting Watchdog file listener on: {content_path}")
        self.observer = Observer()
        handler = MarkdownChangeHandler()
        self.observer.schedule(handler, path=content_path, recursive=True)
        self.observer.daemon = True
        self.observer.start()
        self.is_running = True

    def stop(self):
        if self.observer and self.is_running:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            logger.info("Watchdog daemon stopped.")

watchdog_daemon = WatchdogDaemon()
