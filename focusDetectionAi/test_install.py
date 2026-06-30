import cv2
import mediapipe as mp
import numpy as np

print("✅ Testing imports...")

# Test OpenCV
print(f"OpenCV version: {cv2.__version__}")

# Test MediaPipe
print(f"MediaPipe version: {mp.__version__}")

# Test NumPy
print(f"NumPy version: {np.__version__}")

print("✅ All imports successful!")

# Quick test with MediaPipe - FIXED
try:
    mp_face_mesh = mp.solutions.face_mesh
    print("✅ MediaPipe Face Mesh ready!")
except AttributeError:
    # Alternative way to access face_mesh
    from mediapipe.python.solutions import face_mesh as mp_face_mesh
    print("✅ MediaPipe Face Mesh ready (alternative method)!")

# Also test if we can create an instance
try:
    face_mesh = mp.solutions.face_mesh.FaceMesh()
    print("✅ MediaPipe Face Mesh instance created successfully!")
except Exception as e:
    print(f"⚠️ Could not create FaceMesh instance: {e}")