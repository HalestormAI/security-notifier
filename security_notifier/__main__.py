from security_notifier.imap import get_events
from .config import Config
from .log_helper import setup_logger


def main():
    setup_logger(Config.LOG_LEVEL)

    # Get the initial config instance, so it's loaded when we need it later.
    Config.instance()
    [print(e) for e in get_events()]


if __name__ == "__main__":
    main()
