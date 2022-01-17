import datetime
from typing import Optional

import security_notifier.vision
from security_notifier.imap.detection_info import (
    EventType,
    DetectionInfo
)
from security_notifier.vision import multi_process_capture

handled_failures = []


def mock_handler(event: DetectionInfo, camera_idx: Optional[int] = None):
    print("EventType", event.type)
    if event.type == EventType.Intrusion and event not in handled_failures:
        handled_failures.append(event)
        return False
    return True


def test_failure_retries(mocker):
    spy = mocker.spy(security_notifier.vision, "_run_retry_loop")

    mock_events = [
        DetectionInfo(EventType.Motion, [0], datetime.datetime.now()),
        DetectionInfo(EventType.Motion, [1], datetime.datetime.now()),
        DetectionInfo(EventType.Intrusion, [1, 2], datetime.datetime.now()),
        DetectionInfo(EventType.Motion, [1, 2], datetime.datetime.now()),
        DetectionInfo(EventType.Intrusion, [1, 2], datetime.datetime.now())
    ]

    multi_process_capture(mock_events, mock_handler)
    spy.assert_called_once()
    assert spy.call_args[0][3] == [True, True, False, True, False]
