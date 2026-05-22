from __future__ import annotations

import logging
import queue
from typing import Callable


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


def attach_queue_handler(
    target: queue.Queue[str],
    formatter: Callable[[logging.LogRecord], str] | None = None,
) -> QueueLogHandler:
    handler = QueueLogHandler(target)
    if formatter:
        handler.setFormatter(logging.Formatter(formatter))
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logging.getLogger().addHandler(handler)
    return handler
