"""Thread-safe real-time frame processing for the Streamlit WebRTC UI."""

from dataclasses import dataclass, replace
import threading
import time

import cv2
import numpy as np

from src.blink_detector import BlinkDetector
from src.config import (
    CALIBRATION_EAR_RATIO,
    CHARACTER_PAUSE_SECONDS,
    EAR_CLOSED_THRESHOLD,
)
from src.eye_tracker import EyeTracker
from src.face_detector import FaceDetector
from src.morse_decoder import DecodeResult, MorseDecoder
from src.morse_encoder import MorseEncoder
from src.sentence_builder import SentenceBuilder


@dataclass(frozen=True)
class AppSnapshot:
    """Read-only state shown by Streamlit; safe to copy across threads."""

    camera: str = "Waiting for camera"
    face: str = "Not Detected"
    eyes: str = "Unknown"
    blink_duration: str = "—"
    blink_classification: str = "—"
    current_morse: str = ""
    last_decoded: str = "—"
    current_word: str = ""
    sentence: str = ""
    ear: float | None = None
    ear_threshold: float = EAR_CLOSED_THRESHOLD
    message: str = "Press START in the camera card to begin."


class StreamProcessor:
    """Own the CV pipeline and text state used by a single browser session."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.detector = FaceDetector()
        self.eye_tracker = EyeTracker()
        self.blink_detector = BlinkDetector()
        self.morse_encoder = MorseEncoder()
        self.morse_decoder = MorseDecoder()
        self.sentence_builder = SentenceBuilder()
        self._snapshot = AppSnapshot()

    def snapshot(self) -> AppSnapshot:
        with self._lock:
            return replace(self._snapshot)

    def process_frame(
        self, frame_bgr: np.ndarray, timestamp: float | None = None
    ) -> np.ndarray:
        """Process a frame using live time or an optional source-media timeline."""
        with self._lock:
            try:
                self._snapshot = replace(self._snapshot, camera="Live")
                now = time.perf_counter() if timestamp is None else timestamp
                faces = self.detector.detect_faces(frame_bgr, now)
                if not faces:
                    self._handle_no_usable_face("Not Detected")
                    return self._overlay(frame_bgr)
                if len(faces) > 1:
                    self._handle_no_usable_face("Multiple Faces")
                    self._snapshot = replace(
                        self._snapshot,
                        message="Multiple faces found. Keep only one face in view.",
                    )
                    return self._overlay(frame_bgr)

                face_landmarks = faces[0]
                if self._near_frame_edge(face_landmarks):
                    self._handle_no_usable_face("Moving Outside Frame")
                    return self._overlay(frame_bgr)

                eyes = self.eye_tracker.get_eye_landmarks(face_landmarks, frame_bgr.shape)
                self.eye_tracker.draw(frame_bgr, eyes)
                ear_points = self.eye_tracker.get_ear_points(face_landmarks, frame_bgr.shape)
                blink = self.blink_detector.update(ear_points, now)

                if blink.blink_started:
                    self._apply_decode(self.morse_decoder.begin_blink(blink.blink_start_time))
                if blink.blink_detected and blink.blink_duration is not None:
                    encoded = self.morse_encoder.encode_blink(blink.blink_duration)
                    if encoded.accepted and encoded.symbol is not None:
                        self.morse_decoder.add_symbol(encoded.symbol, now)
                        blink_classification = encoded.signal or "—"
                        message = f"{blink_classification} recorded"
                    else:
                        blink_classification = "Rejected noise"
                        message = f"Blink ignored: {encoded.rejection_reason}."
                else:
                    blink_classification = self._snapshot.blink_classification
                    message = self._snapshot.message
                    if blink.blink_ended:
                        self.morse_decoder.finish_blink()

                self._apply_decode(self.morse_decoder.update(now))
                self.sentence_builder.set_current_morse(self.morse_decoder.current_morse)
                self._snapshot = replace(
                    self._snapshot,
                    face="Detected",
                    eyes=blink.eye_state.title(),
                    ear=blink.average_ear,
                    blink_duration=(f"{blink.blink_duration:.2f} sec" if blink.blink_detected and blink.blink_duration is not None else self._snapshot.blink_duration),
                    blink_classification=blink_classification,
                    current_morse=self.sentence_builder.current_morse,
                    current_word=self.sentence_builder.current_word,
                    sentence=self.sentence_builder.current_sentence,
                    message=message,
                )
                return self._overlay(frame_bgr)
            except Exception as error:  # Keep the webcam UI alive after model/device errors.
                self.blink_detector.reset()
                self.morse_decoder.finish_blink()
                self._snapshot = replace(
                    self._snapshot,
                    camera="Error",
                    face="Unavailable",
                    eyes="Unknown",
                    message=f"Processing error: {type(error).__name__}. Restart the camera if it continues.",
                )
                return self._overlay(frame_bgr)

    def add_space(self) -> None:
        with self._lock:
            self.sentence_builder.handle_command("SPACE")
            self._sync_text("Space added")

    def delete(self) -> None:
        with self._lock:
            self.sentence_builder.handle_command("DELETE")
            self._sync_text("Last character deleted")

    def clear(self) -> None:
        with self._lock:
            self.morse_decoder.clear_current_morse()
            self.morse_encoder.clear()
            self.sentence_builder.clear_current_morse()
            self.sentence_builder.handle_command("CLEAR")
            self._sync_text("Current Morse and current word cleared")

    def reset(self) -> None:
        with self._lock:
            self.morse_decoder.clear()
            self.morse_encoder.clear()
            self.sentence_builder.handle_command("RESET")
            self._sync_text("Sentence reset")

    def calibrate(self) -> bool:
        """Set a user-specific closed-eye threshold from the latest open-eye EAR."""
        with self._lock:
            baseline = self._snapshot.ear
            if baseline is None or self._snapshot.eyes != "Open":
                self._snapshot = replace(self._snapshot, message="Look at the camera with eyes open, then calibrate.")
                return False
            threshold = baseline * CALIBRATION_EAR_RATIO
            self.blink_detector.closed_threshold = threshold
            self._snapshot = replace(self._snapshot, ear_threshold=threshold, message=f"Calibrated EAR threshold to {threshold:.3f}.")
            return True

    def close(self) -> None:
        with self._lock:
            self.detector.close()

    def finalize_pending_character(self, timestamp: float) -> None:
        """Flush a final Morse character after a finite uploaded video ends."""
        with self._lock:
            result = self.morse_decoder.update(timestamp + CHARACTER_PAUSE_SECONDS)
            self._apply_decode(result)
            self.sentence_builder.set_current_morse(self.morse_decoder.current_morse)
            self._sync_text("Video analysis complete")

    def _apply_decode(self, result: DecodeResult) -> None:
        if result.decoded_character:
            self.sentence_builder.add_character(result.decoded_character)
            self.morse_encoder.clear()
            self._snapshot = replace(self._snapshot, last_decoded=result.decoded_character)
        elif result.unknown_morse:
            self.sentence_builder.add_character("?")
            self.morse_encoder.clear()
            self._snapshot = replace(self._snapshot, last_decoded="Unknown Morse")
        if result.word_completed:
            self.sentence_builder.add_space()

    def _handle_no_usable_face(self, status: str) -> None:
        self.blink_detector.reset()
        self.morse_decoder.finish_blink()
        self._snapshot = replace(
            self._snapshot,
            face=status,
            eyes="Unknown",
            ear=None,
            message="Center one face in the camera frame.",
        )

    @staticmethod
    def _near_frame_edge(landmarks) -> bool:
        xs = [point.x for point in landmarks]
        ys = [point.y for point in landmarks]
        return min(xs) < 0.01 or max(xs) > 0.99 or min(ys) < 0.01 or max(ys) > 0.99

    def _sync_text(self, message: str) -> None:
        self._snapshot = replace(
            self._snapshot,
            current_morse=self.sentence_builder.current_morse,
            current_word=self.sentence_builder.current_word,
            sentence=self.sentence_builder.current_sentence,
            message=message,
        )

    def _overlay(self, frame: np.ndarray) -> np.ndarray:
        """Draw a compact diagnostic overlay on the returned WebRTC frame."""
        snapshot = self._snapshot
        colour = (0, 255, 0) if snapshot.face == "Detected" else (0, 165, 255)
        cv2.putText(frame, f"Face: {snapshot.face}", (16, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, colour, 2)
        cv2.putText(frame, f"Eyes: {snapshot.eyes}", (16, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.65, colour, 2)
        if snapshot.ear is not None:
            cv2.putText(frame, f"EAR: {snapshot.ear:.3f}", (16, 86), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        return frame
