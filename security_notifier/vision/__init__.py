import datetime
import logging
import time
from pathlib import Path
from typing import Optional, Text, List

import cv2
import numpy as np

from security_notifier.config import Config
from security_notifier.imap import DetectionInfo
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

    cam_id_str = "-".join(str(i) for i in event.camera_ids) if camera_idx is None else event.camera_ids[camera_idx]

    filename = f"{day_time}__{event.type.name.lower()}_{cam_id_str}.mkv"
    return output_directory / filename


def _get_capture_uris(event: DetectionInfo, camera_idx: Optional[int] = None) -> List[Text]:
    cams_to_capture = [camera_idx] if camera_idx is not None else range(len(event.camera_ids))
    return [_get_rtsp_url(event, c) for c in cams_to_capture]


def get_rtsp_frame(event: DetectionInfo, camera_idx: Optional[int] = None):
    def create_writer(width, height):
        output_path = str(_event_to_filename(event, camera_idx).absolute())
        logger.info(f"Writing capture to {output_path}")
        fourcc = cv2.VideoWriter_fourcc(*'X264')
        return cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    def write_all_frames(writer, imgs):
        if len(imgs) == 1:
            writer.write(imgs[0])
            return

        output = np.concatenate(imgs, axis=1)
        writer.write(output)

    cfg = Config.instance()

    cam_uris = _get_capture_uris(event, camera_idx)
    for c in cam_uris:
        logger.info(f"Reading capture from {c}")

    fps = cfg.get("dvr.camera_fps", 15)

    caps = [cv2.VideoCapture(u) for u in cam_uris]

    # OpenCV / RTSP doesn't seem to kill the feed at "endtime", so we'll have to manually do it.
    # TODO: If find a way to fast-fwd this feed, will need to account for the time difference.
    run_time = time.time()
    end_time = run_time + cfg.get("stream_capture.detection_clip_length", 5)

    # TODO: This is a pretty rubbish implementation. Should not be blocking reads with time taken to write
    writer = None
    while run_time < end_time:
        run_time = time.time()
        imgs = []
        for c_idx, cap in enumerate(caps):
            ret, img = cap.read()
            imgs.append(img)
            if not ret:
                raise NoFrameFromFeedException(f"Failed to capture frame from RTSP feed for capture {c_idx}.")

        if writer is None:
            # TODO: Just tiling horizontally for now. Probably want to be smarter than this later
            desired_width = imgs[0].shape[1] * len(caps)
            writer = create_writer(desired_width, imgs[0].shape[0])

        write_all_frames(writer, imgs)

    for cap in caps:
        cap.release()
    writer.release()
