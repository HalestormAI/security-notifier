import logging

import cv2
import numpy as np

from security_notifier.config import Config
from security_notifier.log_helper import get_logger
from .utils import (
    event_to_filename
)

logger = get_logger(__name__, logging.DEBUG)


def create_writer(event, camera_idx, imgs):
    output_path = str(event_to_filename(event, camera_idx).absolute())
    logger.info(f"Writing capture to {output_path}")

    fps = Config.instance().get("dvr.camera_fps", 15)
    fourcc = cv2.VideoWriter_fourcc(*'X264')

    # TODO: Just tiling horizontally for now. Probably want to be smarter than this later
    desired_width = imgs[0].shape[1] * len(imgs)
    return cv2.VideoWriter(output_path, fourcc, fps, (desired_width, imgs[0].shape[0]))


def write_all_frames(writer, imgs):
    if len(imgs) == 1:
        writer.write(imgs[0])
        return
    output = np.concatenate(imgs, axis=1)
    writer.write(output)
