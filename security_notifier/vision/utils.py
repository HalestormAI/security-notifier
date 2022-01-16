import datetime
from pathlib import Path
from typing import Optional, Text, List

from security_notifier.config import Config
from security_notifier.imap import DetectionInfo
from .login import get_dvr_password


class NoFrameFromFeedException(Exception):
    pass


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


def event_to_filename(event: DetectionInfo, camera_idx: int = 0) -> Path:
    day_time = event.date_and_time.strftime("%d-%H_%M_%S")

    cfg = Config.instance()
    output_directory = Path(cfg.get("stream_capture.storage_location"))
    output_directory = output_directory / f"{event.date_and_time.year}-{event.date_and_time.month:02d}"
    output_directory.mkdir(parents=True, exist_ok=True)

    cam_id_str = "-".join(str(i) for i in event.camera_ids) if camera_idx is None else event.camera_ids[camera_idx]

    filename = f"{day_time}__{event.type.name.lower()}_{cam_id_str}.mkv"
    return output_directory / filename


def get_capture_uris(event: DetectionInfo, camera_idx: Optional[int] = None) -> List[Text]:
    cams_to_capture = [camera_idx] if camera_idx is not None else range(len(event.camera_ids))
    return [_get_rtsp_url(event, c) for c in cams_to_capture]
