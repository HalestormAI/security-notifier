from typing import Text, Optional

import imap_tools
from imap_tools import MailBox

from ..config import Config
from ..keyring_helper import (
    get_password,
    set_password,
    password_is_set
)


def get_imap_password():
    return get_password("imap.keyring_secret_name", 'imap.username')


def set_imap_password(imap_passwd: Optional[Text] = None):
    return set_password("IMAP", "imap.keyring_secret_name", 'imap.username', imap_passwd)


def imap_password_is_set() -> bool:
    return password_is_set("imap.keyring_secret_name", 'imap.username')


def get_mailbox() -> imap_tools.MailBox:
    cfg = Config.instance()

    if not imap_password_is_set():
        set_imap_password()
    return MailBox(cfg.get("imap.server")).login(cfg.get("imap.username"), get_imap_password(), 'INBOX')
