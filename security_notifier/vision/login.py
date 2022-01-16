from typing import Optional, Text

from security_notifier.keyring_helper import (
    get_password,
    set_password,
    password_is_set
)


def get_dvr_password():
    if not dvr_password_is_set():
        set_dvr_password()
    return get_password("dvr.keyring_secret_name", 'dvr.username')


def set_dvr_password(dvr_passwd: Optional[Text] = None):
    set_password("DVR", "dvr.keyring_secret_name", 'dvr.username', dvr_passwd)


def dvr_password_is_set() -> bool:
    return password_is_set("dvr.keyring_secret_name", 'dvr.username')
