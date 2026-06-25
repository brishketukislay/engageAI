from flask import Flask, render_template, Response, jsonify

def register_routes(app, state, generate_frames): 
    @app.route('/')
    def index():
        return render_template('index.html')


    @app.route('/video_feed')
    def video_feed():
        return Response(generate_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')


    @app.route('/status')
    def status():
        return jsonify(state)


    @app.route('/toggle_camera', methods=['POST'])
    def toggle_camera():
        state["paused"] = not state["paused"]
        return jsonify({"paused": state["paused"]})


    @app.route('/reset_stats', methods=['POST'])
    def reset_stats():
        state["focus_time"] = 0
        state["away_time"] = 0
        return jsonify({"status": "reset"})