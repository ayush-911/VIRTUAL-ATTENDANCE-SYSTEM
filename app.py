from flask import Flask, render_template, Response, jsonify, request, send_file
from face_engine import register_face_images, train_model, recognize_face
from attendance_manager import mark_attendance, today_file, ensure_today_file

import cv2
import time
import os

from pdf_report import csv_to_pdf

app = Flask(__name__)

camera = None
camera_active = False

latest_name = "Unknown"
latest_faces = 0
latest_status = "Waiting..."
last_frame = None


def gen_frames():
    global latest_name, latest_faces, latest_status, last_frame
    global camera, camera_active

    while True:
        if not camera_active or camera is None:
            time.sleep(0.05)
            continue

        success, frame = camera.read()
        if not success:
            time.sleep(0.05)
            continue

        last_frame = frame.copy()

        frame, name, face_count = recognize_face(frame)
        latest_name = name
        latest_faces = face_count

        if face_count == 0:
            latest_status = "No face detected"
        elif face_count > 1:
            latest_status = "⚠️ Multiple faces detected (Proxy blocked)"
        elif name == "Unknown":
            latest_status = "Unknown face (Register + Train first)"
        else:
            latest_status = f"Recognized: {name}"

        _, buffer = cv2.imencode(".jpg", frame)
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/status")
def status():
    return jsonify({
        "name": latest_name,
        "faces": latest_faces,
        "status": latest_status
    })


@app.route("/start_camera", methods=["POST"])
def start_camera():
    global camera, camera_active
    if camera is None:
        camera = cv2.VideoCapture(0)

    camera_active = True
    return jsonify({"success": True, "message": "Camera started"})


@app.route("/stop_camera", methods=["POST"])
def stop_camera():
    global camera_active
    camera_active = False
    return jsonify({"success": True, "message": "Camera stopped"})


@app.route("/capture_register", methods=["POST"])
def capture_register():
    global last_frame
    name = request.form.get("name", "").strip()

    if not name:
        return jsonify({"success": False, "message": "Name is required!"})

    if last_frame is None:
        return jsonify({"success": False, "message": "Start camera first!"})

    ok, msg = register_face_images(name, last_frame, max_images=10)
    return jsonify({"success": ok, "message": msg})


@app.route("/train", methods=["POST"])
def train():
    ok, msg = train_model()
    return jsonify({"success": ok, "message": msg})


@app.route("/mark_attendance", methods=["POST"])
def mark_attendance_api():
    global latest_name, latest_faces

    if latest_faces == 0:
        return jsonify({"success": False, "message": "No face detected!"})

    if latest_faces > 1:
        return jsonify({"success": False, "message": "Multiple faces detected! Proxy blocked."})

    if latest_name == "Unknown":
        return jsonify({"success": False, "message": "Unknown face. Register + Train first!"})

    ensure_today_file()
    marked = mark_attendance(latest_name)

    if marked:
        return jsonify({"success": True, "message": f"✅ Attendance marked for {latest_name}"})
    else:
        return jsonify({"success": True, "message": f"✅ Already marked today for {latest_name}"})


# ✅ PDF DOWNLOAD ROUTE (instead of CSV)
@app.route("/download_today")
def download_today():
    ensure_today_file()

    csv_path = today_file()

    # Make PDF path from CSV
    pdf_path = csv_path.replace(".csv", ".pdf")

    # Convert CSV -> PDF
    csv_to_pdf(csv_path, pdf_path)

    return send_file(pdf_path, as_attachment=True)


if __name__ == "__main__":
    print("✅ Server started at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
