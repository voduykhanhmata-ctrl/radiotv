# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Local, bounded diagnostic logging with no stream URLs or user data."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def create_logger(directory: Path) -> logging.Logger:
    logger = logging.Logger("radiotv", level=logging.INFO)
    logger.propagate = False
    try:
        directory.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            directory / "radiotv.log", maxBytes=256 * 1024, backupCount=2,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        logger.addHandler(handler)
    except OSError:
        logger.addHandler(logging.NullHandler())
    return logger


def close_logger(logger: logging.Logger) -> None:
    for handler in tuple(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
