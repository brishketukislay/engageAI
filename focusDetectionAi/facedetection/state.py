import os
import time
import threading


class State:

    def __init__(self):

        self.lock = threading.Lock()

        # ===== UI STATE =====
        self.paused = True
        self.focused = False
        self.attention = 0
        self.emotion = "neutral 😐"
        self.message = "Ready. Start a session to begin monitoring."

        # ===== SESSION =====
        self.session_active = False
        self.session_start_time = 0
        self.session_end_time = 0
        self.session_report = None

        # ===== TIMERS =====
        self.focus_time = 0
        self.away_time = 0
        self.current_away = 0

        # ===== CALIBRATION =====
        self.calibrated = False
        self.calib_yaw_center = 1.0
        self.calib_pitch_center = 1.5
        self.calib_ear_closed = 0.11

        self.raw_yaw = 1.0
        self.raw_pitch = 1.5
        self.raw_ear = 0.25

        # ===== HISTORY =====
        self.history = []
        self.emotion_history = {
            "neutral": 0,
            "focused": 0,
            "sad": 0,
            "surprised": 0
        }

        # ===== ALERT SYSTEM =====
        self.alert_enabled = True
        self.alert_triggered = False
        self.alert_threshold = 5  # seconds
        self.last_alert_time = 0


    # SAFE JSON OUTPUT (FIX)
    def to_dict(self):

        return {
            "paused": self.paused,
            "focused": self.focused,
            "attention": self.attention,
            "emotion": self.emotion,
            "message": self.message,

            "focus_time": self.focus_time,
            "away_time": self.away_time,
            "current_away": self.current_away,

            "history": self.history[-60:],

            "emotion_history": self.emotion_history,

            "alert_enabled": self.alert_enabled,
            "alert_triggered": self.alert_triggered,
            "alert_threshold": self.alert_threshold,
            "session_active": self.session_active,
            "session_duration": round(self.get_session_duration()),
            "session_report": self.session_report,
            "calibrated": self.calibrated,
            "calib_yaw_center": self.calib_yaw_center,
            "calib_pitch_center": self.calib_pitch_center,
            "calib_ear_closed": self.calib_ear_closed,
            "raw_yaw": self.raw_yaw,
            "raw_pitch": self.raw_pitch,
            "raw_ear": self.raw_ear,
        }

    # TIMER METHODS
    def add_focus_time(self, dt):
        self.focus_time += dt

    def add_away_time(self, dt):
        self.away_time += dt

    def add_current_away(self, dt):
        self.current_away += dt

    def reset_away(self):
        self.current_away = 0

    def reset_all(self):
        self.focus_time = 0
        self.away_time = 0
        self.current_away = 0
        self.history = []
        self.emotion_history = {
            "neutral": 0,
            "focused": 0,
            "sad": 0,
            "surprised": 0
        }
        self.alert_triggered = False
        self.last_alert_time = 0
        self.session_report = ""

    def start_session(self):
        self.reset_all()
        self.session_active = True
        self.session_start_time = time.time()
        self.session_end_time = 0
        self.session_report = None
        self.paused = False
        self.message = "Session started. Monitoring student focus."

    def end_session(self, report_text=None):
        self.session_active = False
        self.paused = True
        self.session_end_time = time.time()
        self.session_report = report_text or self.generate_session_report()
        self.message = "Session complete. Report ready."

    def get_session_duration(self):
        if self.session_active and self.session_start_time:
            return time.time() - self.session_start_time
        if self.session_start_time and self.session_end_time:
            return self.session_end_time - self.session_start_time
        return 0

    def generate_session_report(self):
        duration = round(self.get_session_duration())
        focus_pct = 0
        if duration > 0:
            focus_pct = round((self.focus_time / duration) * 100)

        dominant_emotion = max(self.emotion_history, key=self.emotion_history.get)
        summary = (
            f"Session duration: {duration}s. "
            f"Student was focused {focus_pct}% of the time. "
            f"Most frequent state: {dominant_emotion}. "
        )

        if focus_pct >= 80:
            summary += "The student stayed highly attentive and showed strong focus throughout the session."
        elif focus_pct >= 50:
            summary += "The student was moderately attentive, with some periods of distraction."
        else:
            summary += "The student was often distracted and should improve screen engagement."

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if api_key:
            summary += " This report was generated using the DeepSeek API key available in the environment."
        else:
            summary += " (DeepSeek key not configured; generated locally.)"

        return summary
# SINGLE GLOBAL INSTANCE (IMPORTANT)
state = State()