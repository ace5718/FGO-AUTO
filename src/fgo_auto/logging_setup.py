from __future__ import annotations

import logging
import queue
import sys

import structlog

from fgo_auto.logging_bridge import QueueLogHandler


def _shared_processors() -> list:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="%H:%M:%S"),
    ]


def _human_renderer() -> structlog.dev.ConsoleRenderer:
    return structlog.dev.ConsoleRenderer(colors=False)


def configure_logging(
    level: int = logging.INFO,
    *,
    gui_queue: queue.Queue[str] | None = None,
) -> None:
    """Structlog → stdlib; GUI 與終端機使用同一套可讀格式。"""
    shared = _shared_processors()
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            _human_renderer(),
        ],
    )

    handlers: list[logging.Handler] = []
    stderr = logging.StreamHandler(sys.stderr)
    stderr.setFormatter(formatter)
    handlers.append(stderr)

    if gui_queue is not None:
        gui = QueueLogHandler(gui_queue)
        gui.setFormatter(formatter)
        handlers.append(gui)

    root = logging.getLogger()
    root.handlers.clear()
    for handler in handlers:
        root.addHandler(handler)
    root.setLevel(level)

    structlog.configure(
        processors=shared + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
