from routes import register_routes

from flask import Flask
import cv2
import threading
import time

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

app = Flask(__name__)

camera = cv2.VideoCapture(0)

# =========================
# GLOBAL STATE
# =========================

state = {
    "focused": False,
    "attention": 0,
    "emotion": "neutral",
    "message": "Starting...",
    "paused": False,

    "away_time": 0,
    "focus_time": 0,

    # For charts
    "history": [],

    # Emotion analytics
    "emotion_history": {
        "neutral": 0,
        "focused": 0,
        "sad": 0,
        "surprised": 0
    }
}

last_time = time.time()

latest_frame = None

# =========================
# MEDIAPIPE SETUP
# =========================

base_options = python.BaseOptions(
    model_asset_path="face_landmarker.task"
)

options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_faces=1
)

detector = vision.FaceLandmarker.create_from_options(options)

# =========================
# EMOTION DETECTION
# =========================

def estimate_emotion(landmarks):

    mouth_top = landmarks[13]
    mouth_bottom = landmarks[14]

    left_brow = landmarks[70]
    right_brow = landmarks[300]

    mouth_open = abs(mouth_top.y - mouth_bottom.y)

    brow_avg = (left_brow.y + right_brow.y) / 2

    if mouth_open > 0.07:
        return "surprised 😲"

    if mouth_open < 0.015 and brow_avg > 0.45:
        return "sad 😔"

    if mouth_open < 0.02:
        return "neutral 😐"

    return "focused 😎"

# =========================
# DETECTION THREAD
# =========================

def detect_focus():

    global last_time
    global latest_frame
    global state

    while True:

        if state["paused"]:
            time.sleep(0.1)
            continue

        success, frame = camera.read()

        if not success:
            continue

        latest_frame = frame.copy()

        now = time.time()

        dt = now - last_time
        last_time = now

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        timestamp_ms = int(now * 1000)

        result = detector.detect_for_video(
            mp_image,
            timestamp_ms
        )

        focused = False
        attention = 0
        emotion = "neutral 😐"

        if result.face_landmarks:

            landmarks = result.face_landmarks[0]

            # =========================
            # ATTENTION
            # =========================

            nose = landmarks[1]

            h, w, _ = frame.shape

            nose_x = int(nose.x * w)

            center_x = w // 2

            distance = abs(
                nose_x - center_x
            )

            max_distance = w // 2

            attention = max(
                0,
                int(
                    100 -
                    (distance / max_distance) * 100
                )
            )

            focused = attention > 70

            # =========================
            # EMOTION
            # =========================

            emotion = estimate_emotion(
                landmarks
            )

        # =========================
        # TIMERS
        # =========================

        if focused:
            state["focus_time"] += dt
        else:
            state["away_time"] += dt

        # =========================
        # STATE UPDATE
        # =========================

        state["focused"] = focused
        state["attention"] = attention
        state["emotion"] = emotion

        state["message"] = (
            "Focused on screen"
            if focused
            else "Looking away"
        )

        # =========================
        # ATTENTION HISTORY
        # =========================

        state["history"].append(
            int(attention)
        )

        if len(state["history"]) > 60:
            state["history"].pop(0)

        # =========================
        # EMOTION STATS
        # =========================

        if "surprised" in emotion:
            state["emotion_history"]["surprised"] += 1

        elif "sad" in emotion:
            state["emotion_history"]["sad"] += 1

        elif "focused" in emotion:
            state["emotion_history"]["focused"] += 1

        else:
            state["emotion_history"]["neutral"] += 1

# =========================
# START DETECTION THREAD
# =========================

thread = threading.Thread(
    target=detect_focus
)

thread.daemon = True

thread.start()

# =========================
# VIDEO STREAM
# =========================

def generate_frames():

    global latest_frame

    while True:

        if latest_frame is None:
            continue

        ret, buffer = cv2.imencode(
            '.jpg',
            latest_frame
        )

        frame = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + frame +
            b'\r\n'
        )

# =========================
# ROUTES
# =========================

register_routes(
    app,
    state,
    generate_frames
)

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(
        debug=True,
        threaded=True
    )