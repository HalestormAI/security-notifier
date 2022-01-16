import getpass
from os import getenv
from typing import Text, Optional

import imap_tools
from imap_tools import MailBox
from keyrings.cryptfile.cryptfile import CryptFileKeyring

from ..config import Config


def _get_keyring():
    keyring = CryptFileKeyring()
    keyring.keyring_key = getenv("KEYRING_CRYPTFILE_PASSWORD") or getpass.getpass("Enter your keyring password: ")
    return keyring


def get_imap_password():
    cfg = Config.instance()
    keyring = _get_keyring()
    return keyring.get_password(cfg.get("imap.keyring_secret_name"), cfg.get('imap.username'))


def set_imap_password(imap_passwd: Optional[Text] = None):
    if imap_passwd is None:
        imap_passwd = getpass.getpass("Enter your IMAP password to store in the keyring: ")

    cfg = Config.instance()
    keyring = _get_keyring()
    keyring.set_password(cfg.get("imap.keyring_secret_name"), cfg.get('imap.username'), imap_passwd)


def imap_password_is_set() -> bool:
    return get_imap_password() is not None


def get_mailbox() -> imap_tools.MailBox:
    cfg = Config.instance()

    if not imap_password_is_set():
        set_imap_password()
    return MailBox(cfg.get("imap.server")).login(cfg.get("imap.username"), get_imap_password(), 'INBOX')
