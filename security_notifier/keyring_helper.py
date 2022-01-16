import getpass
from os import getenv
from typing import Text, Optional

from keyrings.cryptfile.cryptfile import CryptFileKeyring

from .config import Config


def _get_keyring():
    keyring = CryptFileKeyring()
    keyring.keyring_key = getenv("KEYRING_CRYPTFILE_PASSWORD") or getpass.getpass("Enter your keyring password: ")
    return keyring


def get_password(cfg_pwd_key, cfg_username_key):
    cfg = Config.instance()
    keyring = _get_keyring()
    return keyring.get_password(cfg.get(cfg_pwd_key), cfg.get(cfg_username_key))


def set_password(pwd_name, cfg_pwd_key, cfg_username_key, passwd_text: Optional[Text] = None):
    if passwd_text is None:
        passwd_text = getpass.getpass(f"Enter your {pwd_name} password to store in the keyring: ")

    cfg = Config.instance()
    keyring = _get_keyring()
    keyring.set_password(cfg.get(cfg_pwd_key), cfg.get(cfg_username_key), passwd_text)


def password_is_set(cfg_pwd_key, cfg_username_key) -> bool:
    return get_password(cfg_pwd_key, cfg_username_key) is not None
