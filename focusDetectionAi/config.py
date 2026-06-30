# config.py
# All thresholds and configuration settings

class EngagementConfig:
    # Eye Aspect Ratio (EAR) thresholds
    EAR_THRESHOLD = 0.25        # Below this = eyes closed/staring
    EAR_CONSEC_FRAMES = 15      # Frames before triggering stare alert
    
    # Mouth Aspect Ratio (MAR) thresholds
    MAR_THRESHOLD = 0.65        # Above this = yawning
    MAR_CONSEC_FRAMES = 3       # Frames before triggering yawn alert
    
    # Movement thresholds (for wandering eyes/head movement)
    HEAD_MOVEMENT_THRESHOLD = 30  # Pixel movement threshold
    GAZE_ANGLE_THRESHOLD = 15     # Degrees for wandering eyes
    
    # Smile detection (Mouth width to height ratio)
    SMILE_RATIO_THRESHOLD = 0.8   # Above this = smiling
    
    # Blink detection
    BLINK_SPEED_THRESHOLD = 0.15  # EAR change rate for blink detection
    
    # Frozen/blank detection
    FROZEN_FRAMES = 30           # Frames with no movement = frozen
    
    # Frequency tracking
    YAWN_FREQUENCY_WINDOW = 300   # Frames to track yawn frequency (10 sec at 30fps)
    YAWN_THRESHOLD_PER_WINDOW = 3 # More than 3 yawns in window = bored
    
    # Video settings
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    FPS = 30
    
    # Landmark indices for MediaPipe Face Mesh
    # Left eye landmarks
    LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
    # Right eye landmarks
    RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
    # Mouth landmarks
    MOUTH_INDICES = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185]
    
    # Engagement states
    STATES = {
        'ENGAGED': 'engaged',
        'BORED': 'bored',
        'CONFUSED': 'confused',
        'SLEEPY': 'sleepy',
        'DISTRACTED': 'distracted'
    }