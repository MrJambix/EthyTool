"""
EthyTool Hot Reload — Watch script files and reload on change (dev mode).
"""

import logging
import threading
import time
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger("ethytool.hotreload")

try:
    import watchdog
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object


class ScriptReloadHandler(FileSystemEventHandler):
    """Emit callback when a watched script changes."""

    def __init__(self, script_path: Path, on_change: Callable[[], None]):
        super().__init__()
        self.script_path = Path(script_path).resolve()
        self.on_change = on_change

    def on_modified(self, event):
        if event.is_directory:
            return
        p = Path(event.src_path).resolve()
        if p == self.script_path or p.suffix == ".py":
            try:
                self.on_change()
            except Exception as e:
                logger.exception("Reload callback error: %s", e)


def watch_script(
    script_path: Path,
    on_change: Callable[[], None],
    poll_interval: float = 1.0,
) -> Optional[object]:
    """
    Watch a script file for changes. When changed, calls on_change().
    Returns an observer object; call observer.stop() to stop watching.

    If watchdog is not installed, returns None (no watching).
    """
    if not WATCHDOG_AVAILABLE:
        logger.warning("watchdog not installed. pip install watchdog for hot reload.")
        return None

    path = Path(script_path).resolve()
    if not path.exists():
        logger.warning("Script not found: %s", path)
        return None

    observer = Observer()
    handler = ScriptReloadHandler(path, on_change)
    watch_dir = path.parent
    observer.schedule(handler, str(watch_dir), recursive=False)
    observer.start()
    return observer


def poll_file_mtime(path: Path, interval: float = 1.0) -> "tuple[float, threading.Thread]":
    """
    Fallback: poll file mtime in a thread. Returns (last_mtime, thread).
    Use thread.stop() or stop_event to stop. (Thread doesn't have stop - use daemon.)
    """
    last_mtime = [path.stat().st_mtime]
    stop = threading.Event()

    def _poll():
        while not stop.is_set():
            try:
                m = path.stat().st_mtime
                if m != last_mtime[0]:
                    last_mtime[0] = m
                    # Could call on_change here but we don't have it in this API
            except Exception:
                pass
            stop.wait(timeout=interval)

    t = threading.Thread(target=_poll, daemon=True)
    t.start()
    return last_mtime[0], t
