from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

LOG_FILE = "house_finding.log"


def setup_logging() -> None:
    Path(LOG_FILE).touch(exist_ok=True)

    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        encoding="utf-8",
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_input(logger: logging.Logger, label: str, value: Any) -> None:
    logger.info("INPUT | %s | %r", label, value)


def log_output(logger: logging.Logger, label: str, value: Any) -> None:
    logger.info("OUTPUT | %s | %r", label, value)


def log_event(logger: logging.Logger, message: str, *args: Any) -> None:
    logger.info("EVENT | " + message, *args)


def log_error(logger: logging.Logger, message: str) -> None:
    logger.exception("ERROR | %s", message)