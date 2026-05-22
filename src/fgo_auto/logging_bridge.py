from __future__ import annotations

import logging
import queue


class QueueLogHandler(logging.Handler):
    """Forward log records to a queue for the UI main thread."""

    def __init__(self, target: queue.Queue[str]) -> None:
        super().__init__()
        self._target = target

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._target.put(self.format(record))
        except Exception:
            self.handleError(record)
