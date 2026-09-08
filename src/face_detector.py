"""MediaPipe Tasks Face Landmarker adapter for the Day 1 application."""

import time
from typing import Optional, Sequence

import cv2
import mediapipe as mp

from src.config import (
    FACE_LANDMARKER_MODEL,
    MAX_NUM_FACES,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
    REFINE_LANDMARKS,
)


class FaceDetector:
    """Detect one face and expose its normalized MediaPipe landmarks."""

    def __init__(self) -> None:
        if not FACE_LANDMARKER_MODEL.is_file():
            raise FileNotFoundError(
                "Face Landmarker model is missing: "
                f"{FACE_LANDMARKER_MODEL}. Download it using the project setup command."
            )

        base_options = mp.tasks.BaseOptions(model_asset_path=str(FACE_LANDMARKER_MODEL))
        options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_faces=MAX_NUM_FACES,
            min_face_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_face_presence_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
        )
        self._landmarker = mp.tasks.vision.FaceLandmarker.create_from_options(options)
        self._started_at = time.perf_counter()

    def detect(self, frame_bgr, timestamp: Optional[float] = None) -> Optional[Sequence]:
        """Return landmarks for the first face, or ``None`` when no face exists."""
        faces = self.detect_faces(frame_bgr, timestamp)
        return faces[0] if faces else None

    def detect_faces(
        self, frame_bgr, timestamp: Optional[float] = None
    ) -> list[Sequence]:
        """Return landmarks for up to ``MAX_NUM_FACES`` faces in the frame.

        ``timestamp`` is seconds on the source media timeline.  Supplying it
        makes prerecorded-video blink durations independent of CPU speed.
        """
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        elapsed = time.perf_counter() - self._started_at if timestamp is None else timestamp
        timestamp_ms = int(elapsed * 1000)
        result = self._landmarker.detect_for_video(image, timestamp_ms)
        return list(result.face_landmarks)

    def close(self) -> None:
        self._landmarker.close()
