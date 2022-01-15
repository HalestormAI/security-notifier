import datetime
import re
from typing import Text, List

from .detection_info import (
    DetectionInfo,
    EventType
)
from ..log_helper import get_logger

logger = get_logger(__name__)


class MessageParseFailure(Exception):
    pass


def _get_event_type(message_text: Text) -> EventType:
    match = re.search(r"EVENT TYPE:\s+([\w ]+)", message_text)
    if match is None:
        raise MessageParseFailure("Could not extract the event type from the email.")

    raw_event_type = match.group(1)
    try:
        return EventType(raw_event_type)
    except ValueError:
        logger.warning(f"Could not determine the event type '{raw_event_type}'")
        return EventType.Misc


def _get_camera_ids(message_text: Text) -> List[int]:
    match = re.search(r"CAMERA NAME\(NUM\):\s+(.+)", message_text)
    if match is None:
        raise MessageParseFailure("Could not extract the camera IDs from the email.")

    camera_ids_text = match.group(1)
    matches = re.findall(r"Camera (\d\d)", camera_ids_text)
    if not matches:
        raise MessageParseFailure("Could not extract the camera IDs from the email.")

    return [int(m) for m in matches]


def _get_date_time(message_text: Text) -> datetime.datetime:
    match = re.search(r"EVENT TIME:\s+(\d{4}-\d{2}-\d{2},\d{2}:\d{2}:\d{2})", message_text)
    if match is None:
        raise MessageParseFailure("Could not extract the event date/time from the email.")

    return datetime.datetime.strptime(match.group(1), "%Y-%m-%d,%H:%M:%S")


def parse_message(message_text: Text) -> DetectionInfo:
    event_type = _get_event_type(message_text)
    camera_ids = _get_camera_ids(message_text)
    date_time = _get_date_time(message_text)

    return DetectionInfo(
        event_type,
        camera_ids,
        date_time
    )
