# EyeMorse AI

EyeMorse AI is a local, webcam- and video-based accessibility prototype that converts **intentional eye blinks** into International Morse symbols and then into English text.

It supports two input modes:

- **Live camera**: browser webcam → face landmarks → eye landmarks → blink duration → Morse → text.
- **Uploaded video**: video file → the same pipeline using the video's original timestamps → annotated video and interpreted text.

> This project interprets deliberate blink-Morse signals only. It does **not** perform speech recognition, lip-reading, emotion recognition, or general eye-movement interpretation.

---

## Current project status

| Stage | Result |
| --- | --- |
| Day 1 | Webcam, face detection, facial landmarks, and both eye contours |
| Day 2 | Eye Aspect Ratio (EAR) blink detection and duration measurement |
| Day 3 | Dot/dash classification with noise filtering |
| Day 4 | International Morse decoding for letters, digits, and selected punctuation |
| Day 5 | Sentence builder, word state, spaces, delete, clear, and reset |
| Day 6 | Streamlit user interface, live browser camera, and uploaded-video analysis |

The current automated test suite contains **14 passing unit tests**.

---

## End-to-end flow

```text
Live browser camera / uploaded video
        ↓
MediaPipe Face Landmarker
        ↓
Face landmarks
        ↓
Left and right eye landmarks
        ↓
EAR for each eye → average EAR
        ↓
OPEN → CLOSED → OPEN blink state machine
        ↓
Completed blink duration
        ↓
DOT (.) / DASH (-) / rejected noise
        ↓
Current Morse character
        ↓
Character pause → Morse decoder
        ↓
Sentence builder
        ↓
English text shown in Streamlit
```

---

## Project structure

```text
Morse code/
├── app.py                    # Streamlit layout, UI controls, WebRTC coordination
├── requirements.txt          # Python dependencies
├── models/
│   └── face_landmarker.task  # Required MediaPipe Face Landmarker model
├── src/
│   ├── camera.py             # Legacy local OpenCV camera wrapper
│   ├── config.py             # All adjustable settings and timings
│   ├── face_detector.py      # MediaPipe Tasks face-landmark wrapper
│   ├── eye_tracker.py        # Eye contours and EAR-point extraction
│   ├── blink_detector.py     # EAR calculation and blink state machine
│   ├── morse_encoder.py      # Blink duration → dot or dash
│   ├── morse_decoder.py      # Morse sequence → character
│   ├── sentence_builder.py   # Camera-independent word/sentence editing state
│   ├── stream_processor.py   # Thread-safe frame pipeline used by the UI
│   └── video_analyzer.py     # Uploaded-video frame-by-frame analysis
└── tests/
    ├── test_morse_decoder.py
    └── test_sentence_builder.py
```

`app.py` does not contain vision or Morse algorithms. It renders the Streamlit dashboard and calls the modular components in `src/`.

---

## Installation

### 1. Open PowerShell in the project folder

```powershell
cd "C:\Users\narendra\Morse code"
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this once in the current PowerShell window:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again.

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Required packages

```text
opencv-python>=4.8
mediapipe>=1.0.1
numpy>=1.24
streamlit>=1.51.0
streamlit-webrtc>=0.76.1
```

---

## Running the application

Start the Streamlit application:

```powershell
cd "C:\Users\narendra\Morse code"
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

Open the address Streamlit prints, normally:

```text
http://localhost:8501
```

For the currently configured local server, the address is:

```text
http://127.0.0.1:8501
```

To stop the server, return to the terminal and press `Ctrl+C`.

---

## Streamlit interface

### Camera

- Click **START** in the WebRTC camera component.
- Allow browser camera permission when prompted.
- Click **STOP** in the same component to end the stream.
- The returned video is annotated with face state, eye state, and EAR.

### Detection cards

| Card | Meaning |
| --- | --- |
| Face | `Detected`, `Not Detected`, `Multiple Faces`, or `Moving Outside Frame` |
| Eyes | `Open`, `Closed`, or `Unknown` |
| EAR / threshold | Current average EAR and the current closed-eye threshold |

### Blink information

| Item | Meaning |
| --- | --- |
| Blink duration | Time from the start of eye closure until reopening |
| Blink classification | `DOT`, `DASH`, `Rejected noise`, or no value yet |

### Morse and text

| Item | Meaning |
| --- | --- |
| Current Morse | Symbols being collected for the present character, such as `.-..` |
| Last decoded | Latest completed character, such as `L` |
| Current word | Current word being built, such as `HEL` |
| Sentence | Entire interpreted text, such as `HELLO WORLD` |

### Controls

| Control | Effect |
| --- | --- |
| Space | Adds one word boundary; leading and duplicate spaces are ignored |
| Delete | Removes the final written character or space |
| Clear | Clears the current Morse character and current word only |
| Reset | Clears all Morse and text state |
| Calibration | Sets the EAR closed threshold from the current open-eye EAR |

Calibration should be used while one face is centered in the camera and the user's eyes are clearly open.

---

## Live-camera workflow

1. Start the app and click **START** in the Camera section.
2. Face the camera in even lighting.
3. Wait until `Face: Detected` and `Eyes: Open` appear.
4. Optionally click **Calibration** while looking normally at the camera.
5. Send short and long intentional blinks.
6. Pause after a character and after a word according to the timing rules below.
7. Read the result from `Sentence`.

Example: to send `A`:

```text
short blink → .
brief inside-character pause
long blink  → -
character pause

.- → A
```

---

## Uploaded-video workflow

1. In **Upload video for analysis**, choose an `MP4`, `MOV`, `AVI`, or `MKV` file.
2. Preview the selected file.
3. Click **Analyze uploaded video**.
4. Wait for the frame-processing progress indicator to complete.
5. Review the annotated video, final decoded character, and interpreted sentence.
6. Use **Download annotated video** to save the processed MP4.

The analyzer uses `frame_index / video_fps` as the timestamp. Therefore, a `0.20 sec` blink remains `0.20 sec` regardless of whether analysis takes 10 seconds or 10 minutes to run.

For best results, upload a video with:

- one visible face;
- stable, front-facing framing;
- good lighting;
- clear, intentional eye closures;
- enough open-eye time between Morse elements, characters, and words.

---

## Eye Aspect Ratio (EAR)

The project measures each eye with six landmarks. EAR is calculated as:

```text
EAR = (||p2 - p6|| + ||p3 - p5||) / (2 × ||p1 - p4||)
```

The vertical eyelid distances are in the numerator and the horizontal eye width is in the denominator. During a blink, the eyelids come together, so the vertical distances shrink and EAR falls.

Both eyes are measured independently, then averaged. A blink is recognized only through the complete transition:

```text
OPEN → CLOSED → OPEN
```

This prevents a single sustained closure from producing repeated blink events.

### MediaPipe eye landmarks

The full eye contours use the following Face Landmarker indices:

- Anatomical left eye: `33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7`
- Anatomical right eye: `263, 466, 388, 387, 386, 385, 384, 398, 362, 382, 381, 380, 374, 373, 390, 249`

The six EAR points are:

- Left: `33, 160, 158, 133, 153, 144`
- Right: `362, 385, 387, 263, 373, 380`

---

## Morse timing and classification

The application uses a single configurable unit of time:

```python
MORSE_TIME_UNIT_SECONDS = 0.20
MORSE_TIMING_TOLERANCE = 0.45
```

Standard International Morse ratios are preserved:

| Element | Units | Current target duration |
| --- | ---: | ---: |
| Dot | 1 | 0.20 sec |
| Dash | 3 | 0.60 sec |
| Gap between symbols in one character | 1 | 0.20 sec |
| Gap between characters | 3 | 0.60 sec |
| Gap between words | 7 | 1.40 sec |

With the present ±45% tolerance, the accepted blink durations are:

| Signal | Accepted range |
| --- | --- |
| Dot | 0.11–0.29 sec |
| Dash | 0.33–0.87 sec |

The gap between `0.29` and `0.33 sec` is deliberately rejected as ambiguous. Extremely short closures and closures longer than the accepted dash limit are rejected as noise.

### Important decoder behavior

When a new blink starts, the decoder pauses the character timer. This preserves a standard one-unit dot-to-dash gap. Without this protection, a dot could be decoded as `E` while the following dash was still being held.

---

## Configuration reference

All project tuning is in [src/config.py](src/config.py).

| Setting | Current value | Purpose |
| --- | ---: | --- |
| `CAMERA_INDEX` | `0` | Default OpenCV camera index; legacy local-camera wrapper only |
| `FRAME_WIDTH` / `FRAME_HEIGHT` | `1280 / 720` | Requested legacy local-camera resolution |
| `MAX_NUM_FACES` | `2` | Lets the UI report a multiple-face warning |
| `MIN_DETECTION_CONFIDENCE` | `0.6` | Minimum MediaPipe face-detection confidence |
| `MIN_TRACKING_CONFIDENCE` | `0.6` | Minimum MediaPipe landmark-tracking confidence |
| `EAR_CLOSED_THRESHOLD` | `0.22` | Default value below which eyes are closed |
| `CALIBRATION_EAR_RATIO` | `0.72` | Open-eye EAR multiplier used by Calibration |
| `MIN_CLOSED_FRAMES` | `2` | Minimum closed-frame count for a blink |
| `MIN_BLINK_DURATION_SECONDS` | `0.05` | Lowest valid raw blink duration |
| `MAX_BLINK_DURATION_SECONDS` | `1.00` | Highest valid raw blink duration |
| `MORSE_TIME_UNIT_SECONDS` | `0.20` | Base dot-duration unit |
| `MORSE_TIMING_TOLERANCE` | `0.45` | Accepted variation around dot/dash targets |
| `CHARACTER_PAUSE_SECONDS` | `0.60` | Finalizes a Morse character |
| `WORD_PAUSE_SECONDS` | `1.40` | Adds a word space |

### Tuning guidance

- If normal open eyes show `Closed`, lower `EAR_CLOSED_THRESHOLD` by about `0.01` or calibrate.
- If blinks never register, raise it by about `0.01` or improve lighting.
- If normal blinks are rejected as too short, lower `MORSE_TIME_UNIT_SECONDS` slightly.
- If normal long blinks are rejected as too short, increase `MORSE_TIME_UNIT_SECONDS` or use a more deliberate dash.
- Change values in `config.py`, restart Streamlit, and retest.

---

## Morse dictionary

The decoder supports complete International Morse mappings for:

- English alphabet: `A–Z`
- Digits: `0–9`
- Punctuation: `. , ? ! / ( ) :`

Examples:

```text
.-    → A
-...  → B
-.-.  → C
....  → H
.     → E
.-..  → L
---   → O
...   → S
```

Invalid Morse is handled safely. The UI reports `Unknown Morse`, and the sentence builder appends `?` rather than crashing.

---

## Testing

Run all unit tests:

```powershell
cd "C:\Users\narendra\Morse code"
.\.venv\Scripts\Activate.ps1
python -m unittest discover -s tests -v
```

### Current test coverage

`tests/test_morse_decoder.py` checks:

- A, B, C
- all A–Z letters
- HELLO
- SOS
- numbers
- invalid Morse
- word-space timing
- safe dot-to-dash internal timing

`tests/test_sentence_builder.py` checks:

- HELLO
- HELLO WORLD
- deletion
- no duplicate spaces
- reset
- invalid character, Morse, and command input

---

## Error handling behavior

| Situation | Application behavior |
| --- | --- |
| Camera not allowed or unavailable | WebRTC does not start; allow browser access and retry |
| Camera disconnects | UI remains active; the stream can be stopped and started again |
| No face | Shows `Not Detected`; partial blink is discarded safely |
| Multiple faces | Shows `Multiple Faces`; no Morse input is accepted until one face remains |
| Face at an image edge | Shows `Moving Outside Frame`; no unreliable signal is accepted |
| MediaPipe/frame exception | Frame pipeline catches the error and displays a restart message instead of crashing the app |
| Unreadable upload | Shows a clear upload-analysis error message |
| Invalid Morse | Shows `Unknown Morse` and adds `?` to the sentence |

---

## Performance design

- The browser sends camera frames through **WebRTC**, avoiding a blocking OpenCV camera loop inside Streamlit.
- The video callback handles one frame at a time and returns an annotated frame.
- Shared UI values use a lock because the WebRTC callback runs independently of Streamlit's normal UI execution.
- Only one primary face is processed; multiple-face frames are stopped early.
- Uploaded-video processing uses the same pipeline in a sequential frame loop and updates a progress indicator.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'cv2'`, `streamlit`, or `mediapipe`

Activate the project environment and install requirements again:

```powershell
cd "C:\Users\narendra\Morse code"
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### `AttributeError: module 'mediapipe' has no attribute 'solutions'`

This project uses the newer MediaPipe Tasks API (`mp.tasks`), not the older `mp.solutions` API. Keep the current [src/face_detector.py](src/face_detector.py) implementation and ensure `models/face_landmarker.task` exists.

### Face Landmarker model missing

The required file is:

```text
models/face_landmarker.task
```

It must be present beside `app.py` in the project directory.

### Camera will not start

- Click **START** in the Streamlit camera component.
- Approve the browser camera-permission prompt.
- Close Zoom, Teams, Windows Camera, or another app that may own the camera.
- Refresh the Streamlit page and try again.

### Face or eye detection is unstable

- Use even front lighting.
- Keep one face centered and visible.
- Remove reflections from glasses where possible.
- Avoid fast head movement and extreme profile angles.
- Use Calibration with eyes open.

### Morse character ends too early

The character pause is currently `0.60 sec`. Start the next blink before waiting that long if it belongs to the same character. The decoder pauses its timer while the next blink is held.

### Uploaded video gives no meaningful text

Confirm that the recording contains intentional dot/dash blinks and has pauses consistent with the configured timing. A normal conversational blink pattern is not Morse input.

---

## Known limitations

- The system is a local prototype, not a medical or assistive-device certification.
- It assumes one primary, reasonably front-facing face.
- It has not been tested across all lighting conditions, webcams, eye shapes, glasses, or camera frame rates.
- Calibration is manual and based on one open-eye EAR sample; a future version could average multiple stable frames.
- Uploaded video analysis writes an annotated MP4 to a temporary local file for the current Streamlit session.
- The project currently recognizes blink-Morse only; it does not infer natural-language intent from arbitrary eye movement.

---

## Suggested manual test script

1. Start the Streamlit app.
2. Begin live camera and wait for `Face: Detected`, `Eyes: Open`.
3. Click Calibration.
4. Send `....` and pause: expected `H`.
5. Send `.` and pause: expected `E`.
6. Send `.-..` and pause: expected `L`.
7. Send `.-..` and pause: expected another `L`.
8. Send `---` and pause: expected `O`.
9. Wait a word pause or click Space.
10. Confirm the sentence reads `HELLO `.
11. Upload a prepared blink-Morse video and compare its annotated result with the live behavior.

---

## License and attribution

This repository is a learning/project prototype. Before distributing it, add the project's chosen license and review the licenses for OpenCV, MediaPipe, Streamlit, Streamlit-WebRTC, and the MediaPipe Face Landmarker model.
