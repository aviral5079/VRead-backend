import logging
from logging.handlers import RotatingFileHandler

log_file_path = "logs/app.log"
max_log_size_bytes = 9e6
backup_count = 3


logging.basicConfig(
    handlers=[
        RotatingFileHandler(
            log_file_path, maxBytes=max_log_size_bytes, backupCount=backup_count
        )
    ],
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(funcName)s] [%(name)s] - %(message)s",
)

logger = logging.getLogger(__name__)


def log_info(message):
    logger.info(message)


def log_error(message):
    logger.error(message)


def log_critical(message):
    logger.critical(message)


def log_debug(message):
    logger.debug(message)
