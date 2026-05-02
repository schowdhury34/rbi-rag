# utils/logger.py
# Central logging setup — import and call setup_logging() at entry points.
#
# Usage:
#   from utils.logger import setup_logging
#   setup_logging()

import logging
import sys
from pathlib import Path

LOG_DIR  = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "rbi_rag.log"


def setup_logging(level: str = "INFO"):
    LOG_DIR.mkdir(exist_ok=True)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)

    # File handler — rotates daily
    from logging.handlers import TimedRotatingFileHandler
    file_h = TimedRotatingFileHandler(
        LOG_FILE, when="midnight", backupCount=7, encoding="utf-8"
    )
    file_h.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.addHandler(console)
    root.addHandler(file_h)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
