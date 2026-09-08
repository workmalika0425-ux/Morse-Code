"""Small, explicit wrapper around OpenCV's webcam capture."""

import sys

import cv2

from src.config import CAMERA_INDEX, FRAME_HEIGHT, FRAME_WIDTH


class Camera:
    """Open, read from, and release one webcam safely."""

    def __init__(
        self,
        index: int = CAMERA_INDEX,
        width: int = FRAME_WIDTH,
        height: int = FRAME_HEIGHT,
    ) -> None:
        # DirectShow avoids a common slow-start issue on Windows.  On other
        # systems let OpenCV choose its normal native capture backend.
        backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else cv2.CAP_ANY
        self.capture = cv2.VideoCapture(index, backend)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        if not self.capture.isOpened():
            self.release()
            raise RuntimeError(
                f"Could not open webcam {index}. Check the camera connection, "
                "permissions, and whether another application is using it."
            )

    def read(self):
        """Return the next BGR frame, or ``None`` if capture failed."""
        ok, frame = self.capture.read()
        return frame if ok else None

    def release(self) -> None:
        """Release hardware if it was opened."""
        if self.capture is not None:
            self.capture.release()
