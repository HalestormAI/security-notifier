from security_notifier.config import Config
from security_notifier.imap import get_events
from security_notifier.imap.poller import PollerManager
from security_notifier.log_helper import setup_logger
from security_notifier.vision import multi_process_capture


def main():
    setup_logger(Config.LOG_LEVEL)

    # Get the initial config instance, so it's loaded when we need it later.
    Config.instance()

    mail_poll_mgr = PollerManager(get_events, multi_process_capture)
    mail_poll_mgr.start()
    mail_poll_mgr.join()


if __name__ == "__main__":
    main()
