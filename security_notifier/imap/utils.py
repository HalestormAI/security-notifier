from typing import Iterable

from . import get_mailbox
from ..config import Config
from ..log_helper import get_logger

logger = get_logger(__name__)


def _full_mailbox_name(delim="/"):
    """Get the full mailbox name, including 'INBOX'. Allows the user to specify the delimiter as we need pipe '|' for
    creating / querying the folder and a slash '/' for using it."""
    cfg = Config.instance()
    fld = cfg.get('imap.processed_folder', False)
    if not fld:
        return None

    return f"INBOX{delim}{fld}"


def create_processed_folder_if_not_exist():
    """Create a folder to archive all processed messages (if it doesn't already exist).

    As the inbox grows, operations on it will become less and less efficient. It's useful to keep the old emails for
    looking back on when detections happened, but we'll move them to a sub-folder once they've been downloaded and
    parsed.

    This behaviour can be disabled by setting the `imap.processed_folder` option in the config to null."""
    fld = _full_mailbox_name("|")
    if fld is None:
        logger.warning("Folder for processed messages isn't configured. INBOX size will grow, affecting performance.")
        return

    with get_mailbox() as mailbox:
        if not mailbox.folder.exists(fld):
            mailbox.folder.create(fld)


def move_processed_messages(message_ids: Iterable[str]):
    """Move a set of messages to the processed folder.

    As the inbox grows, operations on it will become less and less efficient. It's useful to keep the old emails for
    looking back on when detections happened, but we'll move them to a sub-folder once they've been downloaded and
    parsed.

    This behaviour can be disabled by setting the `imap.processed_folder` option in the config to null."""
    fld = _full_mailbox_name("/")
    if fld is None:
        logger.warning("Folder for processed messages isn't configured. INBOX size will grow, affecting performance.")
        return

    with get_mailbox() as mailbox:
        mailbox.move(message_ids, fld)
