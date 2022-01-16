from typing import List

import imap_tools.message
from imap_tools import A

from .detection_info import DetectionInfo
from .login import (
    get_imap_password,
    set_imap_password,
    imap_password_is_set, get_mailbox
)
from .message_parser import parse_message
from .utils import _full_mailbox_name, move_processed_messages
from ..config import Config
from ..log_helper import get_logger

logger = get_logger(__name__)


def _fetch_cctv_alerts() -> List[imap_tools.message.MailMessage]:
    """Fetch messages from the IMAP server. Filter them based on the sender, subject and seen-status; based on the
    parameters in the application config.

    We explicitly convert to a list here to allow us to release the mailbox connection and retain the data on-host.
    Memory cost should be relatively small."""
    cfg = Config.instance()

    with get_mailbox() as mailbox:
        filters = {
            "from_": cfg.get("cctv_alerts.email_sender"),
            "subject": cfg.get("cctv_alerts.email_subject_filter")
        }

        if cfg.get("imap.unseen_only", default_val=False):
            filters["seen"] = False

        messages = mailbox.fetch(A(**filters))
        data = [msg for msg in messages]
    return data


def get_events() -> List[DetectionInfo]:
    """Fetch all new events from the inbox"""
    messages = _fetch_cctv_alerts()
    logger.info(f"Downloaded {len(messages)} events since last pull")
    ids = [m.uid for m in messages]

    detections: List[DetectionInfo] = []

    for m in messages:
        det = parse_message(m.text)
        logger.debug(det)
        if det is not None:
            detections.append(det)
    move_processed_messages(ids)
    return detections
