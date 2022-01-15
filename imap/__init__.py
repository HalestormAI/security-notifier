from typing import List

import imap_tools.message
from imap_tools import MailBox, A

from config import Config
from imap.login import (
    get_imap_password,
    set_imap_password,
    imap_password_is_set
)


def fetch() -> List[imap_tools.message.MailMessage]:
    cfg = Config.instance()

    if not imap_password_is_set():
        set_imap_password()

    with MailBox(cfg.get("imap.server")).login(cfg.get("imap.username"), get_imap_password(), 'INBOX') as mailbox:

        messages = mailbox.fetch(A(
            seen=cfg.get("imap.unseen_only", default_val=False),
            from_=cfg.get("cctv_alerts.email_sender"),
            subject=cfg.get("cctv_alerts.email_subject_filter")
        ))

        data = [msg for msg in messages]
    return data