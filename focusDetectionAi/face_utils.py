# face_utils.py
import numpy as np
import math

class FaceUtils:
    @staticmethod
    def eye_aspect_ratio(eye_points):
        """
        Calculate the Eye Aspect Ratio (EAR)
        EAR = (||p2-p6|| + ||p3-p5||) / (2||p1-p4||)
        """
        # Compute the euclidean distances between the vertical eye landmarks
        A = np.linalg.norm(eye_points[1] - eye_points[5])
        B = np.linalg.norm(eye_points[2] - eye_points[4])
        
        # Compute the euclidean distance between the horizontal eye landmarks
        C = np.linalg.norm(eye_points[0] - eye_points[3])
        
        # Compute the EAR
        ear = (A + B) / (2.0 * C)
        return ear
    
    @staticmethod
    def mouth_aspect_ratio(mouth_points):
        """
        Calculate the Mouth Aspect Ratio (MAR)
        MAR = (||p2-p10|| + ||p4-p8||) / (2||p1-p7||)
        """
        # Vertical distances
        A = np.linalg.norm(mouth_points[2] - mouth_points[10])
        B = np.linalg.norm(mouth_points[4] - mouth_points[8])
        
        # Horizontal distance
        C = np.linalg.norm(mouth_points[0] - mouth_points[6])
        
        # Compute MAR
        mar = (A + B) / (2.0 * C)
        return mar
    
    @staticmethod
    def mouth_width_height_ratio(mouth_points):
        """
        Calculate smile ratio (width/height)
        Higher ratio = smiling
        """
        # Width (left to right)
        width = np.linalg.norm(mouth_points[0] - mouth_points[6])
        
        # Height (top to bottom)
        height = np.linalg.norm(mouth_points[3] - mouth_points[9])
        
        if height == 0:
            return 0
        return width / height
    
    @staticmethod
    def head_pose_estimation(face_landmarks, frame_width, frame_height):
        """
        Estimate head pose from facial landmarks
        Returns pitch, yaw, roll in degrees
        """
        # This is a simplified version
        # For more accuracy, use solvePnP with 3D model
        
        # Get nose tip and chin for pitch estimation
        nose_tip = face_landmarks[1]  # Index 1 is nose tip in MediaPipe
        chin = face_landmarks[152]    # Index 152 is chin
        
        # Get left and right eye corners for yaw
        left_eye_outer = face_landmarks[33]
        right_eye_outer = face_landmarks[263]
        
        # Calculate approximate angles
        # Pitch: vertical difference between nose and chin
        pitch = np.arctan2(chin[1] - nose_tip[1], chin[0] - nose_tip[0]) * 180 / np.pi
        
        # Yaw: horizontal difference between eyes
        yaw = np.arctan2(right_eye_outer[1] - left_eye_outer[1], 
                        right_eye_outer[0] - left_eye_outer[0]) * 180 / np.pi
        
        # Roll: angle of eye line
        roll = np.arctan2(right_eye_outer[1] - left_eye_outer[1],
                         right_eye_outer[0] - left_eye_outer[0]) * 180 / np.pi
        
        return pitch, yaw, roll
    
    @staticmethod
    def calculate_movement(landmarks_history, current_frame_index):
        """
        Calculate head movement between frames
        """
        if len(landmarks_history) < 2:
            return 0
        
        # Get nose position from current and previous frames
        current_nose = landmarks_history[-1][1] if len(landmarks_history[-1]) > 1 else None
        previous_nose = landmarks_history[-2][1] if len(landmarks_history[-2]) > 1 else None
        
        if current_nose is None or previous_nose is None:
            return 0
        
        # Calculate Euclidean distance
        movement = np.linalg.norm(current_nose - previous_nose)
        return movement
    
    @staticmethod
    def gaze_direction(eye_landmarks, face_landmarks):
        """
        Estimate gaze direction (left, right, center)
        Returns: 'left', 'right', 'center'
        """
        # Get pupil positions (approximated from eye landmarks)
        left_eye_center = np.mean(eye_landmarks[0:6], axis=0)
        right_eye_center = np.mean(eye_landmarks[6:12], axis=0)
        
        # Get head position
        head_center = face_landmarks[1]  # Nose tip
        
        # Calculate gaze vector
        gaze_center = (left_eye_center + right_eye_center) / 2
        gaze_vector = gaze_center - head_center
        
        # Determine direction
        if gaze_vector[0] > 10:  # Looking right
            return 'right'
        elif gaze_vector[0] < -10:  # Looking left
            return 'left'
        else:
            return 'center'