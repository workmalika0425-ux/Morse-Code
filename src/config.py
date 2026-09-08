"""Central settings for the EyeMorse AI camera, blink, and Morse pipeline."""

from pathlib import Path

CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# MediaPipe Face Mesh settings.  Refined landmarks are enabled so the model
# uses its most detailed face-landmark configuration; no blink logic is here.
MAX_NUM_FACES = 2
MIN_DETECTION_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.6
REFINE_LANDMARKS = True

# MediaPipe Tasks (version 1.x) loads a Face Landmarker model from disk.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FACE_LANDMARKER_MODEL = PROJECT_ROOT / "models" / "face_landmarker.task"

WINDOW_NAME = "EyeMorse AI"

# Ordered contours from MediaPipe's 468-point face mesh.  "Left" and "right"
# use the person's anatomical perspective, not the mirrored camera view.
LEFT_EYE_LANDMARKS = (
    33, 246, 161, 160, 159, 158, 157, 173,
    133, 155, 154, 153, 145, 144, 163, 7,
)
RIGHT_EYE_LANDMARKS = (
    263, 466, 388, 387, 386, 385, 384, 398,
    362, 382, 381, 380, 374, 373, 390, 249,
)

# The six points used by the Eye Aspect Ratio (EAR) formula.  They are ordered
# as: outer corner, upper 1, upper 2, inner corner, lower 2, lower 1.
LEFT_EAR_LANDMARKS = (33, 160, 158, 133, 153, 144)
RIGHT_EAR_LANDMARKS = (362, 385, 387, 263, 373, 380)

# Blink detection tuning.  Lower EAR values mean the eyelids are closer.
# Start with 0.22, then calibrate per user/camera if needed.
EAR_CLOSED_THRESHOLD = 0.22
CALIBRATION_EAR_RATIO = 0.72
MIN_CLOSED_FRAMES = 2
MIN_BLINK_DURATION_SECONDS = 0.05
MAX_BLINK_DURATION_SECONDS = 1.00
BLINK_MESSAGE_SECONDS = 3.0

# International Morse timing is defined in units.  A dot lasts one unit and a
# dash lasts three.  The tolerance accommodates natural variation in blinks.
MORSE_TIME_UNIT_SECONDS = 0.20
MORSE_TIMING_TOLERANCE = 0.45

DOT_UNITS = 1
DASH_UNITS = 3
SYMBOL_GAP_UNITS = 1
LETTER_GAP_UNITS = 3
WORD_GAP_UNITS = 7

DOT_TARGET_DURATION_SECONDS = DOT_UNITS * MORSE_TIME_UNIT_SECONDS
DASH_TARGET_DURATION_SECONDS = DASH_UNITS * MORSE_TIME_UNIT_SECONDS
DOT_MIN_DURATION_SECONDS = DOT_TARGET_DURATION_SECONDS * (1 - MORSE_TIMING_TOLERANCE)
DOT_MAX_DURATION_SECONDS = DOT_TARGET_DURATION_SECONDS * (1 + MORSE_TIMING_TOLERANCE)
DASH_MIN_DURATION_SECONDS = DASH_TARGET_DURATION_SECONDS * (1 - MORSE_TIMING_TOLERANCE)
DASH_MAX_DURATION_SECONDS = DASH_TARGET_DURATION_SECONDS * (1 + MORSE_TIMING_TOLERANCE)

# These gaps are used by the decoder to determine symbol, character, and word
# boundaries under the same Morse timing model.
SYMBOL_GAP_SECONDS = SYMBOL_GAP_UNITS * MORSE_TIME_UNIT_SECONDS
LETTER_GAP_SECONDS = LETTER_GAP_UNITS * MORSE_TIME_UNIT_SECONDS
WORD_GAP_SECONDS = WORD_GAP_UNITS * MORSE_TIME_UNIT_SECONDS

# Decoder boundaries. These are aliases of the standard 3-unit character and
# 7-unit word gaps, kept separate so they can be tuned without code changes.
CHARACTER_PAUSE_SECONDS = LETTER_GAP_SECONDS
WORD_PAUSE_SECONDS = WORD_GAP_SECONDS
# Keep recently recognized output visible long enough for manual testing.
# The full sentence remains visible until the application is closed.
DECODE_MESSAGE_SECONDS = 5.0
