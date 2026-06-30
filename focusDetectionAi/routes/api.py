from flask import jsonify, Response, request
import cv2
import os
import requests
import json

def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k.strip()] = v.strip()

def generate_local_analytical_report(focus_percentage, avg_attention, emotions):
    rec1 = "**Keep it up!** Your focus rate was excellent. Try to maintain this pattern." if focus_percentage >= 70 else "**Take a Short Break**: Your focus rate was lower than optimal. A 5-minute break is recommended to restore cognitive energy."
    rec2 = "Ensure your environment is free of distractions to maintain high attention scores." if avg_attention < 80 else "You showed high, steady attention. Great job setting up a productive environment!"
    rec3 = "The presence of sad/bored emotion counts suggests you might be experiencing fatigue. Try stretching or drinking water." if emotions.get("sad", 0) > emotions.get("focused", 0) else "The emotional distribution shows positive engagement. You seem to be enjoying the material!"
    
    return f"""#### 📊 Attention & Graph Trend Analysis
* **Overall Focus Rate**: **{focus_percentage:.1f}%**
* **Average Attention Score**: **{avg_attention:.1f}%**
* **Visual Graph Analysis**: The attention timeline indicates a {"steady focus pattern" if avg_attention >= 70 else "fluctuating attention trend, showing signs of fatigue or distraction"}.

#### 🎭 Emotional Engagement Analysis
The student's emotional states during this session were distributed as follows:
* **Neutral**: {emotions.get("neutral", 0)} frames (indicating active processing)
* **Focused**: {emotions.get("focused", 0)} frames (indicating high cognitive engagement)
* **Sad/Bored**: {emotions.get("sad", 0)} frames (indicating potential fatigue or disinterest)
* **Surprised**: {emotions.get("surprised", 0)} frames (indicating moments of discovery or confusion)

#### 💡 Actionable Recommendations
1. {rec1}
2. {rec2}
3. {rec3}"""

def generate_groq_report(state):
    load_env()
    api_key = os.environ.get("groq") or os.environ.get("GROQ_API_KEY")

    duration = round(state.get_session_duration())
    total_focus = state.focus_time
    total_away = state.away_time
    focus_percentage = (total_focus / duration * 100) if duration > 0 else 0
    avg_attention = sum(state.history) / len(state.history) if state.history else 0
    emotions = state.emotion_history

    # Attention trend over time
    history_trend = "No attention history recorded."
    if state.history:
        history_trend = f"Attention scores over time (sampled): {', '.join(map(str, state.history[-30:]))}"

    stats_summary = f"""
    Session statistics:
    - Duration: {duration} seconds
    - Focused Time: {total_focus:.1f} seconds ({focus_percentage:.1f}%)
    - Distracted Time: {total_away:.1f} seconds ({100.0 - focus_percentage:.1f}%)
    - Average Attention: {avg_attention:.1f}%
    - Attention Timeline Data: {history_trend}
    - Emotion counts:
      - Neutral: {emotions.get("neutral", 0)}
      - Focused: {emotions.get("focused", 0)}
      - Sad/Bored: {emotions.get("sad", 0)}
      - Surprised: {emotions.get("surprised", 0)}
    """

    if not api_key:
        local_report = generate_local_analytical_report(focus_percentage, avg_attention, emotions)
        return f"""### 📝 Student Focus Report (Simulation - No API Key)

*Warning: `groq` API key is not set in `.env`. Showing local analytical report based on session metrics.*

{local_report}"""

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""
        Analyze the following student focus session data and generate a professional, encouraging, and detailed student learning status report in Markdown format.
        
        {stats_summary}
        
        The report must contain:
        1. Executive Summary: A concise overview of the student's performance.
        2. Attention & Graph Trend Analysis: Analyze their focus vs. distraction percentage, and interpret the attention timeline graph.
        3. Emotional State Analysis: Explain what the emotional doughnut chart counts imply about their engagement, fatigue, or boredom.
        4. Actionable Recommendations: Specific suggestions to improve or maintain focus based on their timeline and emotions.
        
        Keep it structured, insightful, and formatted with clean Markdown.
        """
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "You are an expert AI tutor and educational psychologist analyzing real-time student focus telemetry to generate actionable feedback reports."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            local_report = generate_local_analytical_report(focus_percentage, avg_attention, emotions)
            return f"""### 📝 Student Focus Report (Local Fallback)
*Notice: Groq API returned code {response.status_code} ({response.reason if hasattr(response, 'reason') else ''}). Showing local analytical report based on session metrics.*

{local_report}"""
    except Exception as e:
        local_report = generate_local_analytical_report(focus_percentage, avg_attention, emotions)
        return f"""### 📝 Student Focus Report (Local Fallback)
*Notice: Could not connect to Groq API. Showing local analytical report based on session metrics.*

{local_report}"""


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
        report = generate_groq_report(state)
        state.end_session(report)
        return jsonify({
            "ok": True,
            "session_active": state.session_active,
            "session_report": state.session_report,
            "history": state.history,
            "emotion_history": state.emotion_history
        })

    @app.route("/calibrate", methods=["POST"])
    def calibrate():
        data = request.get_json()
        state.calib_yaw_center = float(data.get("yaw_center", 1.0))
        state.calib_pitch_center = float(data.get("pitch_center", 1.5))
        state.calib_ear_closed = float(data.get("ear_closed", 0.11))
        state.calibrated = True
        return jsonify({
            "ok": True,
            "calibrated": state.calibrated,
            "calib_yaw_center": state.calib_yaw_center,
            "calib_pitch_center": state.calib_pitch_center,
            "calib_ear_closed": state.calib_ear_closed
        })

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