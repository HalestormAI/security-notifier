from security_notifier.imap import get_events
from security_notifier.vision import get_rtsp_capture
from security_notifier.config import Config
from security_notifier.log_helper import setup_logger


def main():
    setup_logger(Config.LOG_LEVEL)

    # Get the initial config instance, so it's loaded when we need it later.
    Config.instance()
    events = get_events()
    [print(e) for e in events]

    for e in events:
        get_rtsp_capture(e)


if __name__ == "__main__":
    main()
