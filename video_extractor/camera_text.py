from datetime import datetime
from typing import Optional

import cv2 as cv
import numpy as np
import pytesseract

CAMERA_TEXT_POSITIONS = np.array([
    [(35, 40), (550, 90)],
    [(250, 950), (400, 990)],
    [(1380, 960), (1600, 990)]
])


def rescale_text_pos(pos: np.ndarray, rescale_prop: float) -> np.ndarray:
    return (pos * rescale_prop).astype(np.int32)


def generate_text_mask(frame: np.ndarray, rescale: float):
    feature_mask = np.ones_like(frame)
    for p in CAMERA_TEXT_POSITIONS:
        pos = rescale_text_pos(p, rescale)
        feature_mask = cv.rectangle(
            feature_mask, pos[0], pos[1], (0, 0, 0), -1)
    return feature_mask


def extract_camera_text(roi: np.ndarray, custom_config: str, debug: bool = False) -> str:
    _, roit = cv.threshold(roi, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

    k = int(roit.shape[1]/3)
    k = k if k % 2 == 1 else k - 1
    roit_bg_mask = cv.medianBlur(roit, k)
    inv_bg_mask = 255 - roit_bg_mask
    lhs_on = (roit - inv_bg_mask)

    # For some reason, this is throwing a bunch of "1"s in where it should be 255...
    lhs_on[lhs_on > 0] = 255

    if debug:
        cv.imshow("debug:roit", roit)
        cv.imshow("debug:roit_bg_mask", roit_bg_mask)
        cv.imshow("debug:inv_bg_mask", inv_bg_mask)
        cv.imshow("debug:lhs_on", lhs_on)
    return pytesseract.image_to_string(255-lhs_on, config=custom_config)


def get_timestamp(img: np.ndarray, rescale: float, tesseract_opts: str, debug: bool =  False) -> Optional[datetime]:
    (x1, y1), (x2, y2) = rescale_text_pos(CAMERA_TEXT_POSITIONS[0], rescale)
    roi = img[y1:y2, x1:x2]
    timestamp_str = extract_camera_text(roi, tesseract_opts, debug=debug)
    try:
        d = datetime.strptime(timestamp_str.strip(), '%m-%d-%Y %a %H:%M:%S')
    except ValueError as err:
        print(f"Could not read timestamp: {timestamp_str}")
        # cv.imshow("debug:roi", roi)
        # extract_camera_text(roi, tesseract_opts, True)
        # cv.waitKey(0)
        return None
    return d
