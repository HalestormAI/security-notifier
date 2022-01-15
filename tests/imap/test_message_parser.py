import contextlib
import datetime
from pathlib import Path
from typing import List, Text, Dict, Optional

import pytest
import toml

from security_notifier.imap.detection_info import DetectionInfo, EventType
from security_notifier.imap.message_parser import parse_message, MessageParseFailure


@pytest.fixture
def examples() -> Dict[Text, Text]:
    example_file = Path(__file__).parent / "message_contents.toml"
    return toml.load(example_file)["message_examples"]


def _check_detection(detection: DetectionInfo,
                     cameras: List[int],
                     event_type: EventType,
                     date_time: datetime.datetime):
    assert len(detection.camera_ids) == len(cameras)
    for i in detection.camera_ids:
        assert i in detection.camera_ids

    assert detection.type == event_type
    assert detection.date_and_time == date_time


def test_parse_motion_single_camera(examples: Dict[Text, Text]):
    detection: DetectionInfo = parse_message(examples["motion_cam1"])
    _check_detection(detection,
                     [1],
                     EventType.Motion,
                     datetime.datetime(2022, 1, 15, 19, 30, 57))

    detection: DetectionInfo = parse_message(examples["motion_cam2"])
    _check_detection(detection,
                     [2],
                     EventType.Motion,
                     datetime.datetime(2022, 1, 15, 19, 37, 36))


def test_parse_motion_two_camera(examples: Dict[Text, Text]):
    detection: DetectionInfo = parse_message(examples["motion_multi_cameras"])
    _check_detection(detection,
                     [1, 2],
                     EventType.Motion,
                     datetime.datetime(2022, 1, 15, 19, 30, 49))


def usion(examples: Dict[Text, Text]):
    detection: DetectionInfo = parse_message(examples["intrusion"])
    _check_detection(detection,
                     [1],
                     EventType.Intrusion,
                     datetime.datetime(2022, 1, 15, 19, 37, 30))


def test_parse_line_crossing(examples: Dict[Text, Text]):
    detection: DetectionInfo = parse_message(examples["line_crossing"])
    _check_detection(detection,
                     [1],
                     EventType.LineCrossing,
                     datetime.datetime(2022, 1, 15, 19, 37, 36))


@pytest.mark.parametrize(
    "example_name, expected_error",
    (
            ("intrusion", None),
            ("line_crossing", None),
            ("motion_cam1", None),
            ("motion_cam2", None),
            ("motion_multi_cameras", None),
            ("invalid_email", "Could not extract the event type from the email"),
            ("motion_invalid_date", "Could not extract the event date/time from the email"),
            ("motion_invalid_cameras", "Could not extract the camera IDs from the email"),
            ("missing_event", "Could not extract the event type from the email"),
            ("invalid_event", None),
    )
)
def test_invalid_example(examples: Dict[Text, Text], example_name: Text, expected_error: Optional[Text]):
    ctx = contextlib.nullcontext() if expected_error is None else pytest.raises(MessageParseFailure)
    with ctx as excinfo:
        parse_message(examples[example_name])

    if expected_error is not None:
        assert expected_error in str(excinfo.value)


def test_invalid_event(caplog, examples: Dict[Text, Text]):
    detection: DetectionInfo = parse_message(examples["invalid_event"])

    assert "Could not determine the event type" in caplog.text

    _check_detection(detection,
                     [2],
                     EventType.Misc,
                     datetime.datetime(2022, 1, 15, 19, 30, 49))
