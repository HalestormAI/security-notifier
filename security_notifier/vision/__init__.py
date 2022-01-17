import logging
import multiprocessing
import time
from typing import Optional, List, Callable

import cv2

from security_notifier.config import Config
from security_notifier.imap import DetectionInfo
from security_notifier.log_helper import get_logger
from security_notifier.vision.login import get_dvr_password
from security_notifier.vision.utils import (
    event_to_filename,
    get_capture_uris,
    NoFrameFromFeedException
)
from security_notifier.vision.writer import (
    create_writer,
    write_all_frames
)

logger = get_logger(__name__, logging.DEBUG)


def get_rtsp_capture(event: DetectionInfo, camera_idx: Optional[int] = None) -> bool:
    cfg = Config.instance()

    cam_uris = get_capture_uris(event, camera_idx)
    for c in cam_uris:
        logger.info(f"Reading capture from {c}")

    caps = [cv2.VideoCapture(u) for u in cam_uris]

    # OpenCV / RTSP doesn't seem to kill the feed at "endtime", so we'll have to manually do it.
    # TODO: If find a way to fast-fwd this feed, will need to account for the time difference.
    run_time = time.time()
    end_time = run_time + cfg.get("stream_capture.detection_clip_length", 5)

    # TODO: This is a pretty rubbish implementation. Should not be blocking reads with time taken to write
    writer = None
    try:
        while run_time < end_time:
            run_time = time.time()
            imgs = []
            for c_idx, cap in enumerate(caps):
                ret, img = cap.read()
                imgs.append(img)
                if not ret:
                    raise NoFrameFromFeedException(f"Failed to capture frame from RTSP feed for capture {c_idx}.")

            if writer is None:
                writer = create_writer(event, camera_idx, imgs)

            write_all_frames(writer, imgs)
    except NoFrameFromFeedException:
        logger.warning(f"Failed to process event {event} - logging for retry")
        return False
    finally:
        for cap in caps:
            cap.release()

        if writer is not None:
            writer.release()
    return True


def _run_retry_loop(all_events: List[DetectionInfo], handler: Callable, p: multiprocessing.Pool, status: List[bool]):
    retry_events = all_events
    while not all(status):
        retry_events = [retry_events[i] for i, r in enumerate(status) if not r]
        status = p.map(handler, retry_events)


# TODO: At the moment, when the capture fails, the whole application crashes out. Needs handling.
def multi_process_capture(events: List[DetectionInfo], handler: Callable = get_rtsp_capture):
    cfg = Config.instance()
    max_processes = cfg.get("stream_capture.max_capture_processes", 5)

    # Issue in Python < 3.8 where just using multiprocessing.Pool causes processes to fail due to fork safety
    # https://stackoverflow.com/a/69405247/168735
    with multiprocessing.get_context("spawn").Pool(max_processes) as pool:
        result_flag = pool.map(handler, events)
        if not all(result_flag):
            _run_retry_loop(events, handler, pool, result_flag)
