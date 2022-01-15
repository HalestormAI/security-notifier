import imap
import log_helper
from config import Config


def main():
    log_helper.setup(Config.LOG_LEVEL)

    # Get the initial config instance, so it's loaded when we need it later.
    Config.instance()

    messages = imap.fetch()


if __name__ == "__main__":
    main()
