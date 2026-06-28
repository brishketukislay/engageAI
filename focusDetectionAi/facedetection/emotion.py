from facedetection.config import (
    MOUTH_OPEN_SURPRISED,
    MOUTH_SAD_THRESHOLD,
    BROW_SAD_THRESHOLD
)


# EMOTION ENGINE

def estimate_emotion(landmarks):

    """
    Very lightweight rule-based emotion estimator.
    Works on MediaPipe face landmarks.
    """

    mouth_top = landmarks[13]
    mouth_bottom = landmarks[14]

    left_brow = landmarks[70]
    right_brow = landmarks[300]

    mouth_open = abs(mouth_top.y - mouth_bottom.y)
    brow_avg = (left_brow.y + right_brow.y) / 2

    # SURPRISED
    if mouth_open > MOUTH_OPEN_SURPRISED:
        return "surprised 😲"

    # SAD
    if mouth_open < MOUTH_SAD_THRESHOLD and brow_avg > BROW_SAD_THRESHOLD:
        return "sad 😔"

    # NEUTRAL
    if mouth_open < 0.02:
        return "neutral 😐"

    # DEFAULT
    return "focused 😎"