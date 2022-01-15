import security_notifier.imap as imap
from .config import Config
from .imap.message_parser import parse_message
from .log_helper import setup_logger


def main():
    setup_logger(Config.LOG_LEVEL)

    # Get the initial config instance, so it's loaded when we need it later.
    Config.instance()

    messages = imap.fetch()
    for m in messages:
        det = parse_message(m.text)
        print(det)


if __name__ == "__main__":
    main()
