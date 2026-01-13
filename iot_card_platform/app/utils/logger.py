"""
日志工具
"""
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "app.log")


def setup_logger() -> logging.Logger:
    log = logging.getLogger("iot_card_platform")
    log.setLevel(logging.INFO)
    log.propagate = False

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)

    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(log_format)
    file_handler.setFormatter(log_format)

    log.addHandler(console_handler)
    log.addHandler(file_handler)

    return log


logger = setup_logger()
