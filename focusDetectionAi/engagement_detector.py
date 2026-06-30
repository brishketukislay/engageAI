# engagement_detector.py (UPDATED)
import cv2
import mediapipe as mp
import numpy as np
from collections import deque
import time
from config import EngagementConfig
from face_utils import FaceUtils

class EngagementDetector:
    def __init__(self):
        # Initialize MediaPipe Face Mesh - FIXED
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize FaceUtils
        self.face_utils = FaceUtils()
        
        # State tracking
        self.ear_history = deque(maxlen=30)
        self.mar_history = deque(maxlen=30)
        self.landmarks_history = deque(maxlen=10)
        self.yawn_count = 0
        self.blink_count = 0
        self.frozen_frames = 0
        self.movement_history = deque(maxlen=30)
        
        # Timing
        self.start_time = time.time()
        self.frame_count = 0
        self.last_yawn_time = 0
        self.last_blink_time = 0
        
        # State variables
        self.current_state = 'engaged'
        self.state_confidence = 0.0
        self.detection_results = {}
        
        # Feature trackers
        self.eye_open_history = deque(maxlen=15)
        self.mouth_open_history = deque(maxlen=15)
        self.head_position_history = deque(maxlen=20)
        
        print("✅ Engagement Detector initialized successfully!")
        
    def process_frame(self, frame):
        """
        Process a single frame and return engagement metrics
        """
        self.frame_count += 1
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process with MediaPipe
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return self._get_empty_results()
        
        # Get face landmarks
        face_landmarks = results.multi_face_landmarks[0]
        landmarks = []
        for landmark in face_landmarks.landmark:
            x = int(landmark.x * frame.shape[1])
            y = int(landmark.y * frame.shape[0])
            landmarks.append([x, y])
        
        # Store landmarks for history
        self.landmarks_history.append(landmarks)
        
        # Extract key features
        features = self._extract_features(landmarks, frame.shape)
        
        # Analyze engagement
        engagement_metrics = self._analyze_engagement(features, landmarks, frame)
        
        # Update state
        self._update_state(engagement_metrics)
        
        return engagement_metrics
    
    def _extract_features(self, landmarks, frame_shape):
        """
        Extract all relevant features from facial landmarks
        """
        features = {}
        
        # Get specific landmark groups
        left_eye = [landmarks[i] for i in EngagementConfig.LEFT_EYE_INDICES]
        right_eye = [landmarks[i] for i in EngagementConfig.RIGHT_EYE_INDICES]
        mouth = [landmarks[i] for i in EngagementConfig.MOUTH_INDICES]
        
        # Calculate ratios
        left_ear = self.face_utils.eye_aspect_ratio(left_eye)
        right_ear = self.face_utils.eye_aspect_ratio(right_eye)
        features['ear'] = (left_ear + right_ear) / 2.0
        
        features['mar'] = self.face_utils.mouth_aspect_ratio(mouth)
        features['smile_ratio'] = self.face_utils.mouth_width_height_ratio(mouth)
        
        # Head pose
        pitch, yaw, roll = self.face_utils.head_pose_estimation(landmarks, 
                                                                frame_shape[1], 
                                                                frame_shape[0])
        features['pitch'] = pitch
        features['yaw'] = yaw
        features['roll'] = roll
        
        # Movement
        features['movement'] = self.face_utils.calculate_movement(self.landmarks_history, 
                                                                   self.frame_count)
        
        # Gaze direction
        all_eye_landmarks = left_eye + right_eye
        features['gaze'] = self.face_utils.gaze_direction(all_eye_landmarks, landmarks)
        
        # Store in history
        self.ear_history.append(features['ear'])
        self.mar_history.append(features['mar'])
        self.movement_history.append(features['movement'])
        
        return features
    
    def _analyze_engagement(self, features, landmarks, frame):
        """
        Analyze all engagement metrics
        """
        metrics = {
            'ear': features['ear'],
            'mar': features['mar'],
            'smile_ratio': features['smile_ratio'],
            'movement': features['movement'],
            'gaze': features['gaze'],
            'state': 'engaged',
            'confidence': 0.0,
            'detections': {}
        }
        
        # 1. Detect yawning
        if features['mar'] > EngagementConfig.MAR_THRESHOLD:
            if time.time() - self.last_yawn_time > 1.0:  # Avoid double counting
                self.yawn_count += 1
                self.last_yawn_time = time.time()
                metrics['detections']['yawning'] = True
            else:
                metrics['detections']['yawning'] = False
        else:
            metrics['detections']['yawning'] = False
        
        # 2. Detect blinking (rapid EAR decrease)
        if len(self.ear_history) > 2:
            ear_rate = self.ear_history[-1] - self.ear_history[-2]
            if abs(ear_rate) > EngagementConfig.BLINK_SPEED_THRESHOLD:
                if time.time() - self.last_blink_time > 0.5:
                    self.blink_count += 1
                    self.last_blink_time = time.time()
                    metrics['detections']['blinking'] = True
                else:
                    metrics['detections']['blinking'] = False
            else:
                metrics['detections']['blinking'] = False
        
        # 3. Detect staring (low EAR for sustained period)
        if features['ear'] < EngagementConfig.EAR_THRESHOLD:
            if len(self.ear_history) > EngagementConfig.EAR_CONSEC_FRAMES:
                if all(e < EngagementConfig.EAR_THRESHOLD for e in list(self.ear_history)[-EngagementConfig.EAR_CONSEC_FRAMES:]):
                    metrics['detections']['staring'] = True
                else:
                    metrics['detections']['staring'] = False
            else:
                metrics['detections']['staring'] = False
        else:
            metrics['detections']['staring'] = False
        
        # 4. Detect smiling
        if features['smile_ratio'] > EngagementConfig.SMILE_RATIO_THRESHOLD:
            metrics['detections']['smiling'] = True
        else:
            metrics['detections']['smiling'] = False
        
        # 5. Detect frozen/blank state
        if len(self.movement_history) > EngagementConfig.FROZEN_FRAMES:
            recent_movement = list(self.movement_history)[-EngagementConfig.FROZEN_FRAMES:]
            if all(m < 5 for m in recent_movement):  # Very little movement
                self.frozen_frames += 1
                if self.frozen_frames > EngagementConfig.FROZEN_FRAMES:
                    metrics['detections']['frozen'] = True
                    self.frozen_frames = 0
                else:
                    metrics['detections']['frozen'] = False
            else:
                self.frozen_frames = 0
                metrics['detections']['frozen'] = False
        else:
            metrics['detections']['frozen'] = False
        
        # 6. Detect wandering eyes (gaze changes)
        if features['gaze'] in ['left', 'right']:
            metrics['detections']['wandering_eyes'] = True
        else:
            metrics['detections']['wandering_eyes'] = False
        
        # 7. Detect head movement (distraction)
        if features['movement'] > EngagementConfig.HEAD_MOVEMENT_THRESHOLD:
            metrics['detections']['head_movement'] = True
        else:
            metrics['detections']['head_movement'] = False
        
        # Calculate overall engagement state
        metrics['state'], metrics['confidence'] = self._determine_state(metrics['detections'], features)
        
        return metrics
    
    def _determine_state(self, detections, features):
        """
        Determine the overall engagement state
        """
        # Count detection flags
        bored_indicators = 0
        distracted_indicators = 0
        sleepy_indicators = 0
        engaged_indicators = 0
        
        # Bored indicators (yawning, frozen, blank stare)
        if detections.get('yawning', False):
            bored_indicators += 2
        if detections.get('frozen', False):
            bored_indicators += 2
        if features['ear'] < EngagementConfig.EAR_THRESHOLD:
            bored_indicators += 1
        
        # Distracted indicators (wandering eyes, head movement)
        if detections.get('wandering_eyes', False):
            distracted_indicators += 2
        if detections.get('head_movement', False):
            distracted_indicators += 1
        
        # Sleepy indicators (closed eyes, yawning)
        if features['ear'] < EngagementConfig.EAR_THRESHOLD:
            sleepy_indicators += 2
        if detections.get('yawning', False):
            sleepy_indicators += 1
        
        # Engaged indicators (smiling, focused gaze)
        if detections.get('smiling', False):
            engaged_indicators += 1
        if features['gaze'] == 'center' and features['ear'] > EngagementConfig.EAR_THRESHOLD:
            engaged_indicators += 1
        if detections.get('blinking', True):  # Normal blinking indicates alertness
            engaged_indicators += 0.5
        
        # Determine state based on highest score
        states = {
            'bored': bored_indicators,
            'distracted': distracted_indicators,
            'sleepy': sleepy_indicators,
            'engaged': engaged_indicators
        }
        
        # Normalize confidence
        total = sum(states.values())
        if total == 0:
            return 'engaged', 0.5
        
        # Find dominant state
        dominant_state = max(states, key=states.get)
        confidence = states[dominant_state] / total
        
        return dominant_state, confidence
    
    def _update_state(self, metrics):
        """
        Update current engagement state
        """
        self.current_state = metrics['state']
        self.state_confidence = metrics['confidence']
        self.detection_results = metrics['detections']
    
    def _get_empty_results(self):
        """
        Return empty results when no face detected
        """
        return {
            'ear': 0,
            'mar': 0,
            'smile_ratio': 0,
            'movement': 0,
            'gaze': 'unknown',
            'state': 'no_face',
            'confidence': 0,
            'detections': {
                'yawning': False,
                'blinking': False,
                'staring': False,
                'smiling': False,
                'frozen': False,
                'wandering_eyes': False,
                'head_movement': False
            }
        }
    
    def get_statistics(self):
        """
        Get summary statistics
        """
        fps = self.frame_count / (time.time() - self.start_time)
        return {
            'fps': fps,
            'frame_count': self.frame_count,
            'yawn_count': self.yawn_count,
            'blink_count': self.blink_count,
            'current_state': self.current_state,
            'state_confidence': self.state_confidence
        }