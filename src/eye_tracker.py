"""Extract and draw the two eye contours from Face Mesh landmarks."""

from typing import Dict, List, Sequence, Tuple

import cv2
import numpy as np

from src.config import (
    LEFT_EAR_LANDMARKS,
    LEFT_EYE_LANDMARKS,
    RIGHT_EAR_LANDMARKS,
    RIGHT_EYE_LANDMARKS,
)

Point = Tuple[int, int]


class EyeTracker:
    """Map normalized face landmarks to pixel coordinates for both eyes."""

    @staticmethod
    def _to_pixels(
        landmarks: Sequence, indices: Sequence[int], width: int, height: int
    ) -> List[Point]:
        return [
            (int(landmarks[index].x * width), int(landmarks[index].y * height))
            for index in indices
        ]

    def get_eye_landmarks(
        self, face_landmarks: Sequence, frame_shape
    ) -> Dict[str, List[Point]]:
        """Return ordered pixel contours for anatomical left and right eyes."""
        height, width = frame_shape[:2]
        return {
            "left": self._to_pixels(
                face_landmarks, LEFT_EYE_LANDMARKS, width, height
            ),
            "right": self._to_pixels(
                face_landmarks, RIGHT_EYE_LANDMARKS, width, height
            ),
        }

    def get_ear_points(
        self, face_landmarks: Sequence, frame_shape
    ) -> Dict[str, List[Point]]:
        """Return the six ordered points needed to calculate each eye's EAR."""
        height, width = frame_shape[:2]
        return {
            "left": self._to_pixels(
                face_landmarks, LEFT_EAR_LANDMARKS, width, height
            ),
            "right": self._to_pixels(
                face_landmarks, RIGHT_EAR_LANDMARKS, width, height
            ),
        }

    @staticmethod
    def draw(frame, eyes: Dict[str, List[Point]]) -> None:
        """Overlay a closed eye contour and each landmark point."""
        colours = {"left": (0, 255, 0), "right": (0, 255, 255)}
        for eye_name, points in eyes.items():
            contour = np.asarray(points, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(
                frame, [contour], isClosed=True, color=colours[eye_name], thickness=1
            )
            for point in points:
                cv2.circle(frame, point, radius=2, color=colours[eye_name], thickness=-1)
