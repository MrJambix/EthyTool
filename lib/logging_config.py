"""
EthyTool Logging — Structured logging for scripts and bots.
"""

import logging
import sys
from typing import Optional, Callable


def setup_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    script_name: Optional[str] = None,
) -> logging.Logger:
    """
    Configure EthyTool logging. Returns root ethytool logger.
    """
    fmt = format_string or "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt="%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    logger = logging.getLogger("ethytool")
    if script_name:
        logger = logger.getChild(script_name)
    return logger


def script_logger(name: str, log_fn: Optional[Callable[[str], None]] = None) -> logging.Logger:
    """
    Get a logger for a script. If log_fn is provided (e.g. GUI callback),
    messages are also sent there.
    """
    logger = logging.getLogger(f"ethytool.script.{name}")

    if log_fn:
        handler = _CallbackHandler(log_fn)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


class _CallbackHandler(logging.Handler):
    """Logging handler that forwards to a callback."""

    def __init__(self, callback: Callable[[str], None]):
        super().__init__()
        self._callback = callback

    def emit(self, record: logging.LogRecord):
        try:
            self._callback(self.format(record))
        except Exception:
            self.handleError(record)
