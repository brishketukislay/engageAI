import math
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
            h, w, _ = frame.shape

            # 1. Yaw deviation (horizontal rotation of head)
            # Left corner of right eye (33), right corner of left eye (263), nose tip (1)
            left_eye_outer = landmarks[263]
            right_eye_outer = landmarks[33]
            nose_tip = landmarks[1]

            dx_left = abs(nose_tip.x - left_eye_outer.x)
            dx_right = abs(nose_tip.x - right_eye_outer.x)
            yaw_ratio = dx_left / (dx_right + 1e-6)
            yaw_dev = abs(yaw_ratio - 1.0)
            yaw_score = max(0.0, 100.0 - (yaw_dev * 180.0))

            # 2. Pitch deviation (vertical rotation of head)
            # Forehead (10), chin (152), nose tip (1)
            forehead = landmarks[10]
            chin = landmarks[152]
            
            dy_top = abs(nose_tip.y - forehead.y)
            dy_bottom = abs(chin.y - nose_tip.y)
            pitch_ratio = dy_top / (dy_bottom + 1e-6)
            pitch_dev = abs(pitch_ratio - 1.5)
            pitch_score = max(0.0, 100.0 - (pitch_dev * 130.0))

            # 3. Eye Aspect Ratio (EAR) for closed eyes
            # Left Eye: top (159), bottom (145), inner (133), outer (33)
            # Right Eye: top (386), bottom (374), inner (362), outer (263)
            ear_left = abs(landmarks[159].y - landmarks[145].y) / (abs(landmarks[33].x - landmarks[133].x) + 1e-6)
            ear_right = abs(landmarks[386].y - landmarks[374].y) / (abs(landmarks[362].x - landmarks[263].x) + 1e-6)
            avg_ear = (ear_left + ear_right) / 2.0

            # Determine focus
            if avg_ear < 0.11:
                attention = 0
                focused = False
                emotion = "eyes closed 😴"
                state.message = "Eyes closed or sleeping detected."
            else:
                attention = int((yaw_score + pitch_score) / 2)
                
                # Check face size/distance
                xs = [lm.x for lm in landmarks]
                ys = [lm.y for lm in landmarks]
                face_width = max(xs) - min(xs)
                face_height = max(ys) - min(ys)
                
                if face_width < 0.15 or face_height < 0.15:
                    attention = max(0, attention - 30)
                    focused = False
                    state.message = "Too far from camera. Move closer."
                else:
                    attention = max(0, min(100, attention))
                    focused = attention > FOCUS_THRESHOLD
                    emotion = estimate_emotion(landmarks)
                    
                    if not focused:
                        if yaw_dev > 0.4:
                            state.message = "Looking away (left or right)."
                        elif pitch_dev > 0.5:
                            state.message = "Looking away (up or down)."
                        else:
                            state.message = "Distracted/Not focused."
                    else:
                        state.message = "Focused on screen"

        # ALERT ENGINE (ONLY TRUTH)
        alert_engine.update(dt, focused)

        # SYNC STATE FOR FRONTEND
        state.focused = focused
        state.attention = attention
        state.emotion = emotion

        if not result.face_landmarks:
            state.message = "No face detected. Please face the camera."

        state.current_away = alert_engine.current_away
        state.alert_triggered = alert_engine.alert_triggered
        state.alert_threshold = alert_engine.threshold
        state.alert_enabled = alert_engine.enabled

        # Only accumulate session statistics if session is active!
        if state.session_active:
            # Update focus/away time metrics
            if focused:
                state.add_focus_time(dt)
            else:
                state.add_away_time(dt)

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