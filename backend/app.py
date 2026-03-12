"""
========================================================
Main Flask Application
--------------------------------------------------------
This file is the entry point of the Driver Drowsiness
Detection System backend.

Responsibilities:
1. Start the Flask web server
2. Initialize webcam and detection engine
3. Stream video frames to the frontend
4. Provide APIs for driver monitoring
5. Provide admin dashboard APIs
6. Handle authentication routing
7. Provide profile and user management APIs

Author: Joys Johney
========================================================
"""

# -------------------------------------------------------
# Import Required Libraries
# -------------------------------------------------------

import cv2
import time
import os
import base64
import re
import threading
from datetime import datetime

from flask import (
    Flask,
    Response,
    jsonify,
    send_from_directory,
    session,
    redirect,
    request
)

from flask_cors import CORS
from werkzeug.security import generate_password_hash

# Project modules
from drowsiness_detector import DrowsinessDetector
from auth import auth_bp, User
from database import (
    get_latest_status,
    insert_admin_message,
    get_all_admin_messages
)


# -------------------------------------------------------
# Flask Application Setup
# -------------------------------------------------------

app = Flask(
    __name__,
    static_folder="../frontend",
    static_url_path=""
)

# Secret key for session management
app.config["SECRET_KEY"] = base64.b64encode(os.urandom(24)).decode("utf-8")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Enable CORS for frontend communication
CORS(app, supports_credentials=True)

# Register authentication blueprint
app.register_blueprint(auth_bp, url_prefix="/auth")


# -------------------------------------------------------
# Initialize Drowsiness Detector
# -------------------------------------------------------

detector = DrowsinessDetector()

camera = None
current_detection_results = {}

# Thread lock to protect shared data
lock = threading.Lock()

# FPS tracking
_fps_frame_times = []
_fps_lock = threading.Lock()
_current_fps = 0.0


# -------------------------------------------------------
# Camera Initialization
# -------------------------------------------------------

def get_camera():
    """
    Initialize webcam if not already started.
    """

    global camera

    if camera is None or not camera.isOpened():

        print("Attempting to open camera...")

        camera = cv2.VideoCapture(0)

        if camera.isOpened():
            print("Camera opened successfully")
        else:
            print("ERROR: Could not open camera")

        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)

    return camera


# -------------------------------------------------------
# Video Frame Generator
# -------------------------------------------------------

def generate_frames():
    """
    Continuously capture frames from webcam,
    process them using the detection engine,
    and stream them to the frontend.
    """

    global current_detection_results

    cam = get_camera()

    if not cam or not cam.isOpened():
        print("Camera not available")
        return

    while True:

        success, frame = cam.read()

        if not success:
            continue

        # Mirror the frame for natural viewing
        frame = cv2.flip(frame, 1)

        # Run drowsiness detection
        processed_frame, detection_results = detector.process_frame(frame)

        # Track real FPS
        global _current_fps
        now_fps = time.time()
        with _fps_lock:
            _fps_frame_times.append(now_fps)
            # keep only timestamps within the last 1 second
            cutoff = now_fps - 1.0
            while _fps_frame_times and _fps_frame_times[0] < cutoff:
                _fps_frame_times.pop(0)
            _current_fps = float(len(_fps_frame_times))

        # Store latest results safely
        with lock:
            current_detection_results = detection_results

        # Encode frame as JPEG
        ret, buffer = cv2.imencode(".jpg", processed_frame)
        frame_bytes = buffer.tobytes()

        # Stream frame using multipart response
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            frame_bytes +
            b"\r\n"
        )


# -------------------------------------------------------
# Page Routes
# -------------------------------------------------------

@app.route("/")
def index():
    """
    Redirect user based on role.
    """

    if "role" in session and session["role"] == "admin":
        return send_from_directory(app.static_folder, "admin.html")

    elif "role" in session and session["role"] == "user":
        return redirect("/driver")

    else:
        return redirect("/login.html")


@app.route("/driver")
def driver():
    """
    Serve driver dashboard (only for logged-in users).
    """

    if "role" in session and session["role"] == "user":
        return send_from_directory(app.static_folder, "driver.html")

    elif "role" in session and session["role"] == "admin":
        return redirect("/")

    else:
        return redirect("/login.html")


@app.route("/login.html")
def login_page():
    """Serve login page."""
    return send_from_directory(app.static_folder, "login.html")


@app.route("/register.html")
def register_page():
    """Serve registration page."""
    return send_from_directory(app.static_folder, "register.html")


@app.route("/admin")
def admin_page():
    """
    Serve admin dashboard — /admin route (in addition to /).
    """
    if "role" in session and session["role"] == "admin":
        return send_from_directory(app.static_folder, "admin.html")
    return redirect("/login.html")


@app.route("/user-management")
def user_management_page():
    """
    Serve driver management page for admin.
    """
    if "role" in session and session["role"] == "admin":
        return send_from_directory(app.static_folder, "user-management.html")
    return redirect("/login.html")


# -------------------------------------------------------
# Video Streaming API
# -------------------------------------------------------

@app.route("/video_feed")
def video_feed():
    """
    Stream MJPEG video feed (requires authentication).
    """

    if "user_id" not in session:
        return "Unauthorized", 401

    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# -------------------------------------------------------
# Driver Status API
# -------------------------------------------------------

@app.route("/drowsiness_status")
def drowsiness_status():
    """
    Return latest drowsiness detection results for the driver.
    """

    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    with lock:
        results = current_detection_results.copy()

    eye_data = results.get("eye_data", {})
    yawn_data = results.get("yawn_data", {})
    alert_info = results.get("alert_info", {})

    response = {
        "status":           alert_info.get("status", "Normal"),
        "drowsiness_score": alert_info.get("drowsiness_score", 0),
        "trigger_audio":    alert_info.get("trigger_audio", False),
        "trigger_toast":    alert_info.get("trigger_toast", False),
        "timestamp":        alert_info.get("timestamp", ""),
        "fps":              round(_current_fps, 1),
        "metrics": {
            "ear":         eye_data.get("avg_ear", 0),
            "mar":         yawn_data.get("mar", 0),
            "ear_percent": eye_data.get("ear_percent", 0),
            "mar_percent": yawn_data.get("mar_percent", 0),
            "blink_count": eye_data.get("blink_count", 0),
            "yawn_count":  yawn_data.get("yawn_count", 0)
        }
    }

    return jsonify(response)


# -------------------------------------------------------
# Admin: Latest Driver Metrics
# -------------------------------------------------------

@app.route("/latest_driver_status")
def latest_driver_status():
    """
    Return current driver metrics for admin dashboard.
    """

    if "role" not in session or session["role"] != "admin":
        return jsonify({"error": "Forbidden"}), 403

    with lock:
        results = current_detection_results.copy()

    eye_data = results.get("eye_data", {})
    yawn_data = results.get("yawn_data", {})
    alert_info = results.get("alert_info", {})

    stats = detector.get_current_status()

    return jsonify({
        "drowsiness_score": alert_info.get("drowsiness_score", 0),
        "ear": eye_data.get("avg_ear", 0),
        "mar": yawn_data.get("mar", 0),
        "blink_count": eye_data.get("blink_count", 0),
        "yawn_count": yawn_data.get("yawn_count", 0),
        "alert_count": stats["alert_stats"]["total_alerts"]
    })



# -------------------------------------------------------
# Timeline API (for admin drowsiness chart)
# -------------------------------------------------------

# In-memory ring buffer: stores last 60 seconds of scores
_timeline_buffer = []   # list of {"timestamp": float, "score": int}
_timeline_lock = threading.Lock()


def _record_timeline_point():
    """
    Background thread: samples drowsiness_score every second
    and keeps the last 120 seconds of history so admins who
    log in mid-session see a populated chart immediately.
    """
    while True:
        with lock:
            results = current_detection_results.copy()
        score = results.get("alert_info", {}).get("drowsiness_score", 0)
        entry = {"timestamp": time.time(), "score": score}
        with _timeline_lock:
            _timeline_buffer.append(entry)
            # keep last 120 seconds
            cutoff = entry["timestamp"] - 120
            while _timeline_buffer and _timeline_buffer[0]["timestamp"] < cutoff:
                _timeline_buffer.pop(0)
        time.sleep(1)


# Start background sampler thread
_tl_thread = threading.Thread(target=_record_timeline_point, daemon=True)
_tl_thread.start()


@app.route("/timeline")
def get_timeline():
    """
    Return the last 60 seconds of drowsiness scores for the admin chart.
    Response: [{age: seconds_ago, score: int}, ...]
    """
    if "role" not in session or session["role"] != "admin":
        return jsonify({"error": "Forbidden"}), 403

    from datetime import datetime
    with _timeline_lock:
        data = [
            {
                "time": datetime.fromtimestamp(e["timestamp"]).strftime("%H:%M:%S"),
                "score": e["score"]
            }
            for e in list(_timeline_buffer)
        ]

    return jsonify(data)

# -------------------------------------------------------
# Profile APIs (Driver Self‑Service)
# -------------------------------------------------------

@app.route("/api/profile", methods=["GET"])
def get_profile():
    """
    Return current user's profile information (fullname, email, vehicle).
    """
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user = User.find_by_id(session["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "fullname": user.fullname,
        "email": user.email,
        "vehicle_number": user.vehicle_number if user.role == "user" else ""
    })


@app.route("/api/update_profile", methods=["POST"])
def update_profile():
    """
    Update fullname, mobile_number, and vehicle_number for the current user.
    """
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    fullname       = data.get("fullname", "").strip()
    mobile_number  = data.get("mobile_number", "").strip()
    vehicle_number = data.get("vehicle_number", "").strip()

    # Validation — vehicle_number only required for drivers
    if not fullname:
        return jsonify({"success": False, "error": "Full name cannot be empty"}), 400

    user = User.find_by_id(session["user_id"])
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    # Build update fields
    update_fields = {"fullname": fullname}
    if mobile_number:
        update_fields["mobile_number"] = mobile_number
    # Only update vehicle_number for drivers
    if user.role == "user" and vehicle_number:
        update_fields["vehicle_number"] = vehicle_number

    user.update(**update_fields)

    return jsonify({"success": True})


# -------------------------------------------------------
# Admin: User Management APIs
# -------------------------------------------------------

@app.route("/api/users", methods=["GET"])
def get_all_users():
    """
    Get all users (admin only).
    """
    if "role" not in session or session["role"] != "admin":
        return jsonify({"error": "Forbidden"}), 403

    users = User.get_all()
    return jsonify(users)


@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """
    Get a single user by ID (admin only).
    """
    if "role" not in session or session["role"] != "admin":
        return jsonify({"error": "Forbidden"}), 403

    user = User.find_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict())


@app.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    """
    Update a user's fullname and vehicle_number (admin only).
    """
    if "role" not in session or session["role"] != "admin":
        return jsonify({"error": "Forbidden"}), 403

    user = User.find_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    fullname       = data.get("fullname")
    mobile_number  = data.get("mobile_number")
    vehicle_number = data.get("vehicle_number")

    # Collect all provided fields and update in one call
    update_fields = {}
    if fullname is not None:
        update_fields["fullname"] = fullname.strip()
    if mobile_number is not None:
        update_fields["mobile_number"] = mobile_number.strip()
    if vehicle_number is not None:
        update_fields["vehicle_number"] = vehicle_number.strip()

    if update_fields:
        user.update(**update_fields)

    return jsonify({"success": True})


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    """
    Delete a user (admin only).
    """
    if "role" not in session or session["role"] != "admin":
        return jsonify({"error": "Forbidden"}), 403

    user = User.find_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.delete()
    return jsonify({"success": True})


# -------------------------------------------------------
# Feedback API (Admin → Driver)
# -------------------------------------------------------

@app.route("/api/feedback", methods=["POST"])
def send_feedback():
    """
    Admin sends a message to the driver.
    """
    if "role" not in session or session["role"] != "admin":
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    insert_admin_message(message)

    return jsonify({"success": True})


@app.route("/api/feedback", methods=["GET"])
def get_feedback():
    """
    Driver retrieves all admin messages.
    """
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    messages = get_all_admin_messages()
    return jsonify(messages)


# -------------------------------------------------------
# Error Handling
# -------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    """
    Fallback: serve the appropriate dashboard or redirect to login.
    """
    if "role" in session and session["role"] == "admin":
        return send_from_directory(app.static_folder, "admin.html")

    elif "role" in session and session["role"] == "user":
        return send_from_directory(app.static_folder, "driver.html")

    else:
        return redirect("/login.html")


# -------------------------------------------------------
# Start Flask Server
# -------------------------------------------------------

if __name__ == "__main__":

    print("=" * 60)
    print("Driver Drowsiness Detection System")
    print("=" * 60)

    print("\nStarting Flask Server...")
    print("Open browser at:")
    print("http://127.0.0.1:5000\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )