"""EyeMorse AI Streamlit application: UI coordination only."""

import av
import streamlit as st
from streamlit_webrtc import webrtc_streamer
from pathlib import Path
import tempfile

from src.stream_processor import StreamProcessor
from src.video_analyzer import VideoAnalyzer


st.set_page_config(page_title="EyeMorse AI", page_icon="👁️", layout="wide")


def get_processor() -> StreamProcessor:
    """Create one stateful processing pipeline for this Streamlit session."""
    if "eyemorse_processor" not in st.session_state:
        st.session_state.eyemorse_processor = StreamProcessor()
    return st.session_state.eyemorse_processor


def render_card(title: str, value: str, help_text: str = "") -> None:
    """Render a compact, consistently styled status card."""
    st.markdown(f"#### {title}")
    st.markdown(f"### {value or '—'}")
    if help_text:
        st.caption(help_text)


def main() -> None:
    st.markdown(
        """
        <style>
        .block-container { max-width: 1450px; padding-top: 1.5rem; }
        div[data-testid="stMetric"] { background: #f5f8fc; border: 1px solid #d9e2ef;
            border-radius: 12px; padding: 14px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("EyeMorse AI")
    st.caption("Live and uploaded-video blink-controlled Morse interpretation")
    processor = get_processor()

    camera_column, status_column = st.columns((1.55, 1), gap="large")
    with camera_column:
        st.subheader("Camera")
        st.caption("Use START/STOP below to control the live webcam stream.")

        def video_frame_callback(frame):
            image = frame.to_ndarray(format="bgr24")
            annotated = processor.process_frame(image)
            return av.VideoFrame.from_ndarray(annotated, format="bgr24")

        webrtc_streamer(
            key="eyemorse-camera",
            video_frame_callback=video_frame_callback,
            media_stream_constraints={"video": True, "audio": False},
            media_toggle_controls=False,
            async_processing=True,
        )
        st.caption("If the camera does not start, allow browser camera access and ensure no other app has locked it.")

    with status_column:
        st.subheader("Detection")
        status_placeholder = st.empty()

    st.divider()
    st.subheader("Upload video for analysis")
    st.caption("Upload a recording of one person using blink Morse. The analysis uses the video timeline, so blink timing does not depend on computer speed.")
    uploaded_video = st.file_uploader("Video file", type=["mp4", "mov", "avi", "mkv"])
    if uploaded_video is not None:
        st.video(uploaded_video)
        if st.button("Analyze uploaded video", type="primary"):
            suffix = Path(uploaded_video.name).suffix.lower() or ".mp4"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as input_file:
                input_file.write(uploaded_video.getbuffer())
                input_path = Path(input_file.name)
            progress = st.progress(0, text="Preparing video analysis…")
            try:
                analyzer = VideoAnalyzer()
                result = analyzer.analyze(
                    input_path,
                    lambda value: progress.progress(int(value * 100), text=f"Analyzing frames: {int(value * 100)}%"),
                )
                st.session_state.upload_analysis = result
                progress.progress(100, text="Analysis complete")
            except RuntimeError as error:
                st.error(str(error))
            finally:
                input_path.unlink(missing_ok=True)

    upload_result = st.session_state.get("upload_analysis")
    if upload_result is not None:
        st.success(f"Processed {upload_result.frames_processed} frames at {upload_result.fps:.1f} FPS.")
        output_bytes = upload_result.output_path.read_bytes()
        st.video(output_bytes)
        result_col, sentence_col = st.columns(2)
        result_col.metric("Uploaded-video last decoded", upload_result.snapshot.last_decoded)
        sentence_col.metric("Interpreted sentence", upload_result.snapshot.sentence or "No complete Morse sentence detected")
        st.download_button("Download annotated video", output_bytes, "eyemorse_annotated.mp4", "video/mp4")

    st.divider()
    controls = st.columns(5)
    actions = (
        ("Space", processor.add_space),
        ("Delete", processor.delete),
        ("Clear", processor.clear),
        ("Reset", processor.reset),
        ("Calibration", processor.calibrate),
    )
    for column, (label, action) in zip(controls, actions):
        with column:
            if st.button(label, use_container_width=True):
                action()
                st.rerun()

    @st.fragment(run_every="0.25s")
    def live_dashboard() -> None:
        snapshot = processor.snapshot()
        with status_placeholder.container():
            face_col, eyes_col = st.columns(2)
            face_col.metric("Face", snapshot.face)
            eyes_col.metric("Eyes", snapshot.eyes)
            st.info(snapshot.message)

        st.subheader("Blink information")
        blink_duration, blink_classification, ear = st.columns(3)
        blink_duration.metric("Blink duration", snapshot.blink_duration)
        blink_classification.metric("Blink classification", snapshot.blink_classification)
        ear.metric("EAR / threshold", f"{snapshot.ear:.3f}" if snapshot.ear is not None else "—", f"Threshold: {snapshot.ear_threshold:.3f}")

        st.subheader("Morse")
        morse_col, character_col = st.columns(2)
        with morse_col:
            render_card("Current Morse", snapshot.current_morse or "(empty)")
        with character_col:
            render_card("Last decoded", snapshot.last_decoded)

        st.subheader("Decoded text")
        word_col, sentence_col = st.columns((1, 2))
        with word_col:
            render_card("Current word", snapshot.current_word or "(empty)")
        with sentence_col:
            render_card("Sentence", snapshot.sentence or "(empty)")

    live_dashboard()


if __name__ == "__main__":
    main()
