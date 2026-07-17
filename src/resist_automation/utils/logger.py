from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(log_directory: Path, *, level: int = logging.INFO) -> Path:
    log_directory.mkdir(parents=True, exist_ok=True)
    log_path = log_directory / "resist_automation.log"
    root = logging.getLogger("resist_automation")
    root.setLevel(level)
    if not any(isinstance(handler, logging.FileHandler) for handler in root.handlers):
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
        root.addHandler(handler)
    return log_path
