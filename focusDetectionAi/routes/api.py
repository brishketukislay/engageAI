from flask import jsonify, Response, request
import cv2


def register_api_routes(app, state, frame_holder, alert_engine):

    @app.route("/status")
    def status():
        return jsonify(state.to_dict())

    @app.route("/update_alert", methods=["POST"])
    def update_alert():

        data = request.get_json()

        threshold = int(data.get("threshold", 30))
        enabled = bool(data.get("enabled", True))

        alert_engine.set_config(threshold, enabled)

        return jsonify({
            "ok": True,
            "threshold": threshold,
            "enabled": enabled
        })

    @app.route("/start_session", methods=["POST"])
    def start_session():
        state.start_session()
        return jsonify({"ok": True, "session_active": state.session_active})

    @app.route("/end_session", methods=["POST"])
    def end_session():
        report = state.end_session()
        return jsonify({"ok": True, "session_active": state.session_active, "report": report})

    @app.route("/toggle_camera", methods=["POST"])
    def toggle_camera():
        state.paused = not state.paused
        return jsonify({"paused": state.paused})

    @app.route("/reset_stats", methods=["POST"])
    def reset_stats():
        state.reset_all()
        return jsonify({"ok": True})

    @app.route("/video_feed")
    def video_feed():

        def generate():
            while True:
                frame = frame_holder.get("frame")
                if frame is None:
                    continue

                success, buffer = cv2.imencode(".jpg", frame)
                if not success:
                    continue

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" +
                    buffer.tobytes() +
                    b"\r\n"
                )

        return Response(
            generate(),
            mimetype="multipart/x-mixed-replace; boundary=frame"
        )