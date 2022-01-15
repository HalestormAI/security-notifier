
import security_notifier.imap as imap
from .log_helper import setup_logger
from .config import Config


def main():
    setup_logger(Config.LOG_LEVEL)

    # Get the initial config instance, so it's loaded when we need it later.
    Config.instance()

    messages = imap.fetch()


if __name__ == "__main__":
    main()
