"""Eye Aspect Ratio calculation and one-shot blink event detection."""

from dataclasses import dataclass
import time
from typing import Dict, Optional, Sequence, Tuple

import numpy as np

from src.config import (
    EAR_CLOSED_THRESHOLD,
    MAX_BLINK_DURATION_SECONDS,
    MIN_BLINK_DURATION_SECONDS,
    MIN_CLOSED_FRAMES,
)

Point = Tuple[int, int]


@dataclass
class BlinkResult:
    """Measurements and state emitted once for each processed video frame."""

    left_ear: float
    right_ear: float
    average_ear: float
    eye_state: str
    blink_detected: bool = False
    blink_duration: Optional[float] = None
    blink_started: bool = False
    blink_start_time: Optional[float] = None
    blink_ended: bool = False


class BlinkDetector:
    """Recognize an OPEN -> CLOSED -> OPEN cycle from eye landmark points."""

    def __init__(
        self,
        closed_threshold: float = EAR_CLOSED_THRESHOLD,
        min_closed_frames: int = MIN_CLOSED_FRAMES,
        min_duration: float = MIN_BLINK_DURATION_SECONDS,
        max_duration: float = MAX_BLINK_DURATION_SECONDS,
    ) -> None:
        self.closed_threshold = closed_threshold
        self.min_closed_frames = min_closed_frames
        self.min_duration = min_duration
        self.max_duration = max_duration
        self._is_closed = False
        self._closed_frames = 0
        self._blink_start: Optional[float] = None
        self.last_blink_duration: Optional[float] = None

    @staticmethod
    def calculate_ear(points: Sequence[Point]) -> float:
        """Calculate EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)."""
        if len(points) != 6:
            raise ValueError("EAR requires exactly six ordered eye landmark points.")

        eye = np.asarray(points, dtype=np.float32)
        vertical_1 = np.linalg.norm(eye[1] - eye[5])
        vertical_2 = np.linalg.norm(eye[2] - eye[4])
        horizontal = np.linalg.norm(eye[0] - eye[3])
        return float((vertical_1 + vertical_2) / (2.0 * horizontal)) if horizontal else 0.0

    def update(
        self, eye_points: Dict[str, Sequence[Point]], timestamp: Optional[float] = None
    ) -> BlinkResult:
        """Process one frame and report a blink only when the eye reopens."""
        now = time.perf_counter() if timestamp is None else timestamp
        left_ear = self.calculate_ear(eye_points["left"])
        right_ear = self.calculate_ear(eye_points["right"])
        average_ear = (left_ear + right_ear) / 2.0
        is_now_closed = average_ear < self.closed_threshold

        if is_now_closed:
            if not self._is_closed:
                self._is_closed = True
                self._closed_frames = 0
                self._blink_start = now
            self._closed_frames += 1
            return BlinkResult(
                left_ear,
                right_ear,
                average_ear,
                "CLOSED",
                blink_started=self._closed_frames == 1,
                blink_start_time=self._blink_start,
            )

        blink_detected = False
        duration = None
        blink_ended = self._is_closed
        if self._is_closed and self._blink_start is not None:
            candidate_duration = now - self._blink_start
            if (
                self._closed_frames >= self.min_closed_frames
                and self.min_duration <= candidate_duration <= self.max_duration
            ):
                blink_detected = True
                duration = candidate_duration
                self.last_blink_duration = duration

        self._is_closed = False
        self._closed_frames = 0
        self._blink_start = None
        return BlinkResult(
            left_ear,
            right_ear,
            average_ear,
            "OPEN",
            blink_detected,
            duration,
            blink_ended=blink_ended,
        )

    def reset(self) -> None:
        """Discard an incomplete cycle, for example after losing the face."""
        self._is_closed = False
        self._closed_frames = 0
        self._blink_start = None
