import logging
import re
from typing import Text, Optional

LogLevel = int


# Remove passwords from logs
# https://stackoverflow.com/a/48503066/168735
# CC BY-SA 4.0
# No modifications except Python formatting
class SensitiveFormatter(logging.Formatter):
    """Formatter that removes sensitive information in urls."""

    @staticmethod
    def _filter(s):
        return re.sub(r':\/\/(.*?)\@', r'://', s)

    def format(self, record):
        original = logging.Formatter.format(self, record)
        return self._filter(original)


def setup_logger(level: LogLevel = logging.INFO):
    fmt_template = '%(asctime)s %(levelname)s:%(message)s'
    logging.basicConfig(format=fmt_template, level=logging.DEBUG)
    logging.getLogger().setLevel(level)
    for handler in logging.getLogger().handlers:
        handler.setFormatter(SensitiveFormatter(fmt_template))


def get_logger(name: Text, level: Optional[LogLevel] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    for handler in logger.handlers:
        handler.setFormatter(SensitiveFormatter())
    if level is not None:
        logger.setLevel(level)
    return logger
