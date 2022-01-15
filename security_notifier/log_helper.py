import logging
from typing import Text, Optional

LogLevel = int


def setup_logger(level: LogLevel = logging.INFO):
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG)
    logging.getLogger().setLevel(level)


def get_logger(name: Text, level: Optional[LogLevel] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    return logger
