import time


class AlertEngine:

    def __init__(self, state):
        self.state = state

        self.threshold = 30
        self.enabled = True

        self.current_away = 0
        self.last_alert_time = 0
        self.alert_triggered = False

    def set_config(self, threshold, enabled):
        self.threshold = threshold
        self.enabled = enabled

    def update(self, dt, focused):

        if focused:
            self.current_away = 0
            self.alert_triggered = False
            return

        self.current_away += dt

        if not self.enabled:
            return

        if self.current_away >= self.threshold:
            if time.time() - self.last_alert_time > 10:
                self.alert_triggered = True
                self.last_alert_time = time.time()
            else:
                self.alert_triggered = False
        else:
            self.alert_triggered = False

    def to_dict(self):
        return {
            "current_away": self.current_away,
            "alert_triggered": self.alert_triggered,
            "alert_threshold": self.threshold,
            "alert_enabled": self.enabled
        }