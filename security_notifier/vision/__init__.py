import datetime
import time
from typing import Optional, Text

import cv2

from security_notifier.config import Config
from security_notifier.imap import DetectionInfo
from security_notifier.imap.detection_info import EventType
from security_notifier.keyring_helper import (
    get_password,
    set_password,
    password_is_set
)


def get_dvr_password():
    return get_password("dvr.keyring_secret_name", 'dvr.username')


def set_dvr_password(dvr_passwd: Optional[Text] = None):
    return set_password("DVR", "dvr.keyring_secret_name", 'dvr.username', dvr_passwd)


def dvr_password_is_set() -> bool:
    return password_is_set("dvr.keyring_secret_name", 'dvr.username')


def _get_rtsp_url(event: DetectionInfo, camera_idx: int = 0):
    cfg = Config.instance()
    username = cfg.get("dvr.username", "admin")

    if not dvr_password_is_set():
        set_dvr_password()

    password = get_dvr_password()

    host = cfg.get("dvr.host")
    port = cfg.get("dvr.rtsp_port", 554)

    device_id = f"{event.camera_ids[camera_idx]}01"

    start_time = event.date_and_time.strftime("%Y%m%dT%H%M%SZ")

    time_delta = datetime.timedelta(seconds=cfg.get("stream_capture.detection_clip_length", 5))
    end_time = (event.date_and_time + time_delta).strftime("%Y%m%dT%H%M%SZ")

    return f"rtsp://{username}:{password}@{host}:{port}/Streaming/tracks/{device_id}/" \
           f"?starttime={start_time}&endtime={end_time}"


# TODO: Better support for multiple cameras
def get_rtsp_frame(event: DetectionInfo, camera_idx: int = 0):
    cam_uri = _get_rtsp_url(event, camera_idx)
    print(cam_uri)

    cap = cv2.VideoCapture(cam_uri)

    # OpenCV / RTSP doesn't seem to kill the feed at "endtime", so we'll have to manually do it.
    # TODO: If find a way to fast-fwd this feed, will need to account for the time difference.
    run_time = time.time()
    end_time = run_time + 5

    # For now we'll just output the frame to the display
    # TOOD: Store the video somewhere.
    while run_time < end_time:
        ret, img = cap.read()
        if ret:
            cv2.imshow('video output', img)
            run_time = time.time()
            k = cv2.waitKey(2) & 0xff
            if k == 27:
                break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    event = DetectionInfo(EventType.Motion, [1], datetime.datetime.now() - datetime.timedelta(hours=4))
    get_rtsp_frame(event, 0)
