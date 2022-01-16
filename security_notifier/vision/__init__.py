import datetime
import logging
import time
from pathlib import Path
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
from security_notifier.log_helper import get_logger

logger = get_logger(__name__, logging.DEBUG)


class NoFrameFromFeedException(Exception):
    pass


def get_dvr_password():
    if not dvr_password_is_set():
        set_dvr_password()
    return get_password("dvr.keyring_secret_name", 'dvr.username')


def set_dvr_password(dvr_passwd: Optional[Text] = None):
    set_password("DVR", "dvr.keyring_secret_name", 'dvr.username', dvr_passwd)


def dvr_password_is_set() -> bool:
    return password_is_set("dvr.keyring_secret_name", 'dvr.username')


def _get_rtsp_url(event: DetectionInfo, camera_idx: int = 0) -> Text:
    cfg = Config.instance()
    username = cfg.get("dvr.username", "admin")

    password = get_dvr_password()

    host = cfg.get("dvr.host")
    port = cfg.get("dvr.rtsp_port", 554)

    device_id = f"{event.camera_ids[camera_idx]}01"

    start_time = event.date_and_time.strftime("%Y%m%dT%H%M%SZ")

    time_delta = datetime.timedelta(seconds=cfg.get("stream_capture.detection_clip_length", 5))
    end_time = (event.date_and_time + time_delta).strftime("%Y%m%dT%H%M%SZ")

    return f"rtsp://{username}:{password}@{host}:{port}/Streaming/tracks/{device_id}/" \
           f"?starttime={start_time}&endtime={end_time}"


def _event_to_filename(event: DetectionInfo, camera_idx: int = 0) -> Path:
    day_time = event.date_and_time.strftime("%d-%H_%M_%S")

    cfg = Config.instance()
    output_directory = Path(cfg.get("stream_capture.storage_location"))
    output_directory = output_directory / f"{event.date_and_time.year}-{event.date_and_time.month:02d}"
    output_directory.mkdir(parents=True, exist_ok=True)

    filename = f"{day_time}__{event.type.name.lower()}_{event.camera_ids[camera_idx]}.mkv"
    return output_directory / filename


# TODO: Better support for multiple cameras
def get_rtsp_frame(event: DetectionInfo, camera_idx: int = 0):
    def create_writer(current_frame):
        output_path = str(_event_to_filename(event, camera_idx).absolute())
        logger.info(f"Writing capture to {output_path}")
        fourcc = cv2.VideoWriter_fourcc(*'X264')
        return cv2.VideoWriter(output_path, fourcc, fps, (current_frame.shape[1], current_frame.shape[0]))

    cfg = Config.instance()
    cam_uri = _get_rtsp_url(event, camera_idx)
    logger.info(f"Reading capture from {cam_uri}")

    fps = cfg.get("dvr.camera_fps", 15)

    cap = cv2.VideoCapture(cam_uri)

    # OpenCV / RTSP doesn't seem to kill the feed at "endtime", so we'll have to manually do it.
    # TODO: If find a way to fast-fwd this feed, will need to account for the time difference.
    run_time = time.time()
    end_time = run_time + cfg.get("stream_capture.detection_clip_length", 5)

    # TODO: This is a pretty rubbish implementation. Should not be blocking reads with time taken to write
    writer = None
    while run_time < end_time:
        run_time = time.time()
        ret, img = cap.read()
        if not ret:
            raise NoFrameFromFeedException("Failed to capture frame from RTSP feed.")

        if writer is None:
            writer = create_writer(img)
        writer.write(img)

    cap.release()
    writer.release()


if __name__ == "__main__":
    event = DetectionInfo(EventType.Motion, [1], datetime.datetime.now() - datetime.timedelta(hours=4))
    get_rtsp_frame(event, 0)
