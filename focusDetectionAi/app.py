from routes import register_routes

from flask import Flask, render_template, Response, jsonify
import cv2
import threading
import time

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

app = Flask(__name__)

camera = cv2.VideoCapture(0)

# GLOBAL STATE

state = {
    "focused": False,
    "attention": 0,
    "emotion": "neutral",
    "message": "Starting...",
    "paused": False,
    "away_time": 0,
    "focus_time": 0
}

last_time = time.time()

latest_frame = None

# MEDIA PIPE SETUP

base_options = python.BaseOptions(
    model_asset_path="face_landmarker.task"
)

options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_faces=5  # <--- Changed from 1 to 5
)

detector = vision.FaceLandmarker.create_from_options(options)

# EMOTION FUNCTION

def estimate_emotion(landmarks):

    mouth_top = landmarks[13]
    mouth_bottom = landmarks[14]

    left_eye_top = landmarks[159]
    right_eye_top = landmarks[386]

    left_brow = landmarks[70]
    right_brow = landmarks[300]

    mouth_open = abs(mouth_top.y - mouth_bottom.y)

    eye_open = abs(left_eye_top.y - left_eye_top.y) + abs(right_eye_top.y - right_eye_top.y)

    brow_avg = (left_brow.y + right_brow.y) / 2

    # FIXED LOGIC (less sensitive)


    if mouth_open > 0.07:
        return "surprised 😲"

    if mouth_open < 0.015 and brow_avg > 0.45:
        return "sad / tired 😔"

    if mouth_open < 0.02:
        return "neutral 😐"

    return "focused 😐"

    mouth_top = landmarks[13]
    mouth_bottom = landmarks[14]

    left_eye_top = landmarks[159]
    right_eye_top = landmarks[386]

    brow_left = landmarks[70]
    brow_right = landmarks[300]

    nose = landmarks[1]

    mouth_open = abs(mouth_top.y - mouth_bottom.y)
    eye_openness = (left_eye_top.y + right_eye_top.y) / 2 - nose.y
    brow_raise = (brow_left.y + brow_right.y) / 2 - nose.y

    if mouth_open > 0.06:
        return "surprised 😲"

    if brow_raise < -0.02:
        return "angry 😠"

    if eye_openness < -0.03:
        return "sad / tired 😔"

    if mouth_open < 0.01:
        return "neutral 😐"

    return "focused 😐"


# DETECTION THREAD

def detect_focus():
    global last_time, latest_frame, state

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

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        timestamp_ms = int(now * 1000)

        result = detector.detect_for_video(mp_image, timestamp_ms)

        focused = False
        attention = 0
        emotion = "neutral"

        if result.face_landmarks:
            # 1. Find the nearest face by checking the distance between left eye (386) and right eye (159)
            nearest_landmarks = None
            max_face_size = 0

            for face in result.face_landmarks:
                # Calculate approximate face width using eye landmarks
                left_eye = face[386]
                right_eye = face[159]
                
                # Euclidean distance in normalized coordinates
                face_size = ((left_eye.x - right_eye.x)**2 + (left_eye.y - right_eye.y)**2)**0.5
                
                if face_size > max_face_size:
                    max_face_size = face_size
                    nearest_landmarks = face

            # 2. Use the nearest face for calculations
            landmarks = nearest_landmarks

            # FOCUS
            
            nose = landmarks[1]

            h, w, _ = frame.shape
            nose_x = int(nose.x * w)
            center_x = w // 2

            distance = abs(nose_x - center_x)

            attention = max(0, 100 - distance)

            focused = distance < 80

            # EMOTION
            
            emotion = estimate_emotion(landmarks)

        # TIMERS
        
        if focused:
            state["focus_time"] += dt
        else:
            state["away_time"] += dt

        # UPDATE STATE

        state["focused"] = focused
        state["attention"] = int(attention)
        state["emotion"] = emotion

        state["message"] = (
            "Focused on screen" if focused else "Looking away"
        )


# Start thread
thread = threading.Thread(target=detect_focus)
thread.daemon = True
thread.start()


# VIDEO STREAM

def generate_frames():
    global latest_frame

    while True:
        if latest_frame is None:
            continue

        ret, buffer = cv2.imencode('.jpg', latest_frame)
        frame = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
        )

register_routes(app, state, generate_frames)

if __name__ == "__main__":
    app.run(debug=False)