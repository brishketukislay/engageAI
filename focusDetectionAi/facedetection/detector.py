import time
import cv2
import threading

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from facedetection.config import (
    CAMERA_INDEX,
    FACE_LANDMARK_MODEL,
    FOCUS_THRESHOLD,
    ATTENTION_HISTORY_LENGTH,
    MOUTH_OPEN_SURPRISED,
    MOUTH_SAD_THRESHOLD,
    BROW_SAD_THRESHOLD
)

# EMOTION
def estimate_emotion(landmarks):

    mouth_top = landmarks[13]
    mouth_bottom = landmarks[14]

    left_brow = landmarks[70]
    right_brow = landmarks[300]

    mouth_open = abs(mouth_top.y - mouth_bottom.y)
    brow_avg = (left_brow.y + right_brow.y) / 2

    if mouth_open > MOUTH_OPEN_SURPRISED:
        return "surprised 😲"
    if mouth_open < MOUTH_SAD_THRESHOLD and brow_avg > BROW_SAD_THRESHOLD:
        return "sad 😔"
    if mouth_open < 0.02:
        return "neutral 😐"

    return "focused 😎"


# THREAD
def detector_loop(state, frame_holder, alert_engine):

    camera = cv2.VideoCapture(CAMERA_INDEX)

    base_options = python.BaseOptions(
        model_asset_path=FACE_LANDMARK_MODEL
    )

    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1
    )

    detector = vision.FaceLandmarker.create_from_options(options)

    last_time = time.time()

    while True:

        if state.paused:
            time.sleep(0.1)
            continue

        success, frame = camera.read()
        if not success:
            continue

        frame_holder["frame"] = frame.copy()

        now = time.time()
        dt = now - last_time
        last_time = now

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        result = detector.detect_for_video(mp_image, int(now * 1000))

        focused = False
        attention = 0
        emotion = "neutral 😐"

        if result.face_landmarks:

            landmarks = result.face_landmarks[0]

            nose = landmarks[1]

            h, w, _ = frame.shape
            nose_x = int(nose.x * w)
            center_x = w // 2

            distance = abs(nose_x - center_x)
            max_distance = w // 2

            attention = max(0, int(100 - (distance / max_distance) * 100))
            focused = attention > FOCUS_THRESHOLD
            emotion = estimate_emotion(landmarks)

        # ALERT ENGINE (ONLY TRUTH)
        alert_engine.update(dt, focused)

        # SYNC STATE FOR FRONTEND
        state.focused = focused
        state.attention = attention
        state.emotion = emotion

        state.message = "Focused on screen" if focused else "Looking away"

        state.current_away = alert_engine.current_away
        state.alert_triggered = alert_engine.alert_triggered
        state.alert_threshold = alert_engine.threshold
        state.alert_enabled = alert_engine.enabled

        # =========================
        # HISTORY
        # =========================
        state.history.append(attention)
        if len(state.history) > ATTENTION_HISTORY_LENGTH:
            state.history.pop(0)

        # EMOTION STATS
        if "surprised" in emotion:
            state.emotion_history["surprised"] += 1
        elif "sad" in emotion:
            state.emotion_history["sad"] += 1
        elif "focused" in emotion:
            state.emotion_history["focused"] += 1
        else:
            state.emotion_history["neutral"] += 1


def start_detector_thread(state, frame_holder, alert_engine):

    thread = threading.Thread(
        target=detector_loop,
        args=(state, frame_holder, alert_engine),
        daemon=True
    )
    thread.start()