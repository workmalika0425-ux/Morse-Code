"""Analyze uploaded video files with the existing EyeMorse processing pipeline."""

from dataclasses import dataclass
from pathlib import Path
import tempfile
from typing import Callable, Optional

import cv2

from src.stream_processor import AppSnapshot, StreamProcessor


@dataclass(frozen=True)
class VideoAnalysisResult:
    """Output artifact and final decoded state from a video analysis run."""

    output_path: Path
    snapshot: AppSnapshot
    frames_processed: int
    fps: float


class VideoAnalyzer:
    """Decode blink Morse from a file while preserving video timestamps."""

    def analyze(
        self,
        input_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> VideoAnalysisResult:
        """Return an annotated MP4 path and final decoded sentence.

        The input is processed frame-by-frame. Any unreadable frame is skipped;
        an unreadable or unsupported file raises a clear ``RuntimeError``.
        """
        capture = cv2.VideoCapture(str(input_path))
        if not capture.isOpened():
            raise RuntimeError("Unable to open the uploaded video.")

        fps = capture.get(cv2.CAP_PROP_FPS)
        fps = fps if fps and fps > 1 else 30.0
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width <= 0 or height <= 0:
            capture.release()
            raise RuntimeError("The uploaded video has no readable image frames.")

        output_file = Path(tempfile.NamedTemporaryFile(suffix="_eyemorse.mp4", delete=False).name)
        writer = cv2.VideoWriter(
            str(output_file), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
        )
        if not writer.isOpened():
            capture.release()
            raise RuntimeError("Unable to create the annotated video output.")

        processor = StreamProcessor()
        frames_processed = 0
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                # Frame index / FPS is the original video clock, not processing speed.
                annotated = processor.process_frame(frame, frames_processed / fps)
                writer.write(annotated)
                frames_processed += 1
                if progress_callback and total_frames:
                    progress_callback(min(frames_processed / total_frames, 1.0))
            processor.finalize_pending_character(frames_processed / fps)
        finally:
            capture.release()
            writer.release()
            processor.close()

        if frames_processed == 0:
            output_file.unlink(missing_ok=True)
            raise RuntimeError("No frames could be read from the uploaded video.")
        if progress_callback:
            progress_callback(1.0)
        return VideoAnalysisResult(output_file, processor.snapshot(), frames_processed, fps)
