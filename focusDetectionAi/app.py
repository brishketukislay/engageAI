import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask

from facedetection.detector import start_detector_thread
from facedetection.state import state
from facedetection.alerts import AlertEngine

from routes.api import register_api_routes
from routes.views import register_view_routes

app = Flask(__name__)

frame_holder = {"frame": None}

# SINGLE SOURCE OF TRUTH
alert_engine = AlertEngine(state)

def start_system():
    start_detector_thread(state, frame_holder, alert_engine)

register_view_routes(app)
register_api_routes(app, state, frame_holder, alert_engine)

if __name__ == "__main__":
    start_system()
    app.run(debug=False, threaded=True)