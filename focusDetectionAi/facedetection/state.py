import threading


class State:

    def __init__(self):

        self.lock = threading.Lock()

        # ===== UI STATE =====
        self.paused = False
        self.focused = False
        self.attention = 0
        self.emotion = "neutral 😐"
        self.message = "Starting..."

        # ===== TIMERS =====
        self.focus_time = 0
        self.away_time = 0
        self.current_away = 0

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

    # =========================
    # SAFE JSON OUTPUT (FIX)
    # =========================
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
        }

    # =========================
    # TIMER METHODS
    # =========================
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
# SINGLE GLOBAL INSTANCE (IMPORTANT)
state = State()