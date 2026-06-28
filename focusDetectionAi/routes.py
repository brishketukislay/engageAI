from flask import (
    render_template,
    Response,
    jsonify,
    request
)


def register_routes(app, state, generate_frames):

    # ===========================
    # Dashboard
    # ===========================

    @app.route("/")
    def index():
        return render_template("index.html")

    # ===========================
    # Video Feed
    # ===========================

    @app.route("/video_feed")
    def video_feed():
        return Response(
            generate_frames(),
            mimetype="multipart/x-mixed-replace; boundary=frame"
        )

    # ===========================
    # Status
    # ===========================

    @app.route("/status")
    def status():

        return jsonify({

            "focused": state["focused"],
            "attention": state["attention"],
            "emotion": state["emotion"],
            "message": state["message"],

            "focus_time": state["focus_time"],
            "away_time": state["away_time"],

            "history": state["history"],
            "emotion_history": state["emotion_history"],

            # Alert information
            "alert": state["alert_triggered"],
            "current_away": round(state["current_away"], 1),
            "alert_threshold": state["alert_threshold"],
            "alert_enabled": state["alert_enabled"]

        })

    # ===========================
    # Pause / Resume Camera
    # ===========================

    @app.route("/toggle_camera", methods=["POST"])
    def toggle_camera():

        state["paused"] = not state["paused"]

        return jsonify({

            "paused": state["paused"]

        })

    # ===========================
    # Reset Statistics
    # ===========================

    @app.route("/reset_stats", methods=["POST"])
    def reset_stats():

        state["focus_time"] = 0
        state["away_time"] = 0
        state["current_away"] = 0
        state["alert_triggered"] = False

        state["history"] = []

        state["emotion_history"] = {

            "neutral": 0,
            "focused": 0,
            "sad": 0,
            "surprised": 0

        }

        return jsonify({

            "success": True

        })

    # ===========================
    # Update Alert Settings
    # ===========================

    @app.route("/update_alert", methods=["POST"])
    def update_alert():

        data = request.get_json()

        if data is None:
            return jsonify({
                "success": False
            }), 400

        threshold = data.get("threshold", 30)
        enabled = data.get("enabled", True)

        try:

            threshold = int(threshold)

            if threshold < 1:
                threshold = 1

        except Exception:

            threshold = 30

        state["alert_threshold"] = threshold
        state["alert_enabled"] = bool(enabled)

        # Reset current alert when settings change
        state["alert_triggered"] = False
        state["current_away"] = 0

        return jsonify({

            "success": True,
            "threshold": state["alert_threshold"],
            "enabled": state["alert_enabled"]

        })