from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

import time
import numpy as np

from camera_text import  get_timestamp


FeatureId = int


@dataclass
class State:
    frame_counter: int = 0
    frames_since_reinit: int = 0

    line_lengths: Dict[FeatureId, int] = \
        field(default_factory=lambda: defaultdict(int))

    flagged_detections: Dict[FeatureId, List[Optional[int]]] = \
        field(default_factory=lambda: defaultdict(lambda: [None, None]))

    start_time: int = -1
    fps: int = -1

    frame_time: Optional[datetime] = None

    def reset(self):
        self.start_time = time.time()
        self.line_lengths.clear()
        self.flagged_detections.clear()
        self.frames_since_reinit = 0

    def print(self):
        print(f"Frame {self.frame_counter:06d} | [{self.current_frame_time}] | FPS: {self.fps:.3f} img/sec")
        print(self.flagged_detections)

    def update_fps(self) -> int:
        frame_time = time.time()
        self.fps = self.frames_since_reinit / (frame_time - self.start_time)
        return self.fps

    def increment(self):
        self.frame_counter += 1
        self.frames_since_reinit += 1
    
    def update_frame_time(self, grey: np.ndarray, tesseract_opts: str,  scale: int = 1, debug: bool = False):
        self.frame_time = get_timestamp(grey, scale, tesseract_opts,  debug)
    
    @property
    def current_frame_time(self) -> str:
        return self.frame_time.strftime('%Y-%m-%d %H:%M:%S') if self.frame_time else "UNKNOWN"

