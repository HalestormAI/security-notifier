import enum
from dataclasses import dataclass
from datetime import datetime
from typing import List


class EventType(enum.Enum):
    LineCrossing = "line crossing"
    Motion = "Motion Detected"
    Intrusion = "intrusion"
    Misc = "misc"


@dataclass
class DetectionInfo:
    type: EventType
    camera_ids: List[int]
    date_and_time: datetime
