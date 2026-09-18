import logging
import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)
PIPELINE_LOG_FILE = LOGS_DIR / "pipeline.log"


def setup_pipeline_logger() -> logging.Logger:
    """Configures and returns the central pipeline logger writing to both console and logs/pipeline.log in text format."""
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if setup is called multiple times
    if logger.handlers:
        return logger

    # Log formatter: [Timestamp] [Level] [Module] Message
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File Handler: writes text logs to logs/pipeline.log
    file_handler = logging.FileHandler(PIPELINE_LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console Handler: writes to terminal output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


pipeline_logger = setup_pipeline_logger()


def get_pipeline_logger() -> logging.Logger:
    return pipeline_logger
