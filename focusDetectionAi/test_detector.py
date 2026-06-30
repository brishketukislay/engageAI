# test_detector.py
from engagement_detector import EngagementDetector
import cv2

print("🚀 Testing Engagement Detector...")

# Initialize detector
detector = EngagementDetector()

# Open webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Could not open webcam!")
    exit()

print("✅ Webcam opened successfully!")
print("Press 'q' to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame")
        break
    
    # Process frame
    metrics = detector.process_frame(frame)
    
    # Display metrics
    print(f"State: {metrics['state']}, Confidence: {metrics['confidence']:.2f}")
    print(f"Detections: {metrics['detections']}")
    print("-" * 50)
    
    # Show frame
    cv2.imshow('Engagement Detection', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("✅ Test complete!")