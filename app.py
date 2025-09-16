from vosk import Model, KaldiRecognizer
import sounddevice as sd, json
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
import csv, os, datetime
import cv2
import numpy as np
import speech_recognition as sr
from deepface import DeepFace

app = Flask(__name__)
app.secret_key = "attendify-demo"
STUDENTS_FILE = 'students.csv'
ATTENDANCE_DIR = 'data'

# Haar Cascade backup detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# ------------------ UTILS ------------------

def ensure_sample_students():
    """Create students.csv and attendance folder if missing"""
    if not os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['roll', 'name'])
            for i in range(1, 31):   # sample 30 students
                w.writerow([f'R{str(i).zfill(3)}', f'Student_{i}'])
    if not os.path.exists(ATTENDANCE_DIR):
        os.makedirs(ATTENDANCE_DIR)


def create_student_database(student_folder="students"):
    """Make dictionary: roll -> image path"""
    database = {}
    if not os.path.exists(student_folder):
        os.makedirs(student_folder)
    for file in os.listdir(student_folder):
        if file.lower().endswith(('.jpg', '.png', '.jpeg')):
            roll = os.path.splitext(file)[0]
            path = os.path.join(student_folder, file)
            database[roll] = path
    return database

student_db = create_student_database("students")


def load_students():
    students = []
    if os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, newline='') as f:
            r = csv.DictReader(f)
            for row in r:
                students.append(row)
    return students


def get_daily_attendance_file_path():
    today_str = datetime.date.today().isoformat()
    filename = f'attendance_{today_str}.csv'
    return os.path.join(ATTENDANCE_DIR, filename)


def overwrite_attendance(roll, status):
    """
    Always update student's latest status (Present/Absent),
    ensures no duplicates and correct dashboard count.
    """
    now = datetime.datetime.now().isoformat(timespec='seconds')
    header = ['timestamp', 'roll', 'status']
    file_path = get_daily_attendance_file_path()
    rows = []

    # Read existing rows except current roll
    if os.path.exists(file_path):
        with open(file_path, newline='') as f:
            r = csv.DictReader(f)
            for row in r:
                if row['roll'] != roll:
                    rows.append(row)

    # Add new entry
    rows.append({'timestamp': now, 'roll': roll, 'status': status})

    # Write back
    with open(file_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def mark_attendance(roll):
    overwrite_attendance(roll, "Present")

# ------------------ ROUTES ------------------

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        if user == 'teacher' and pwd == 'password':
            return redirect(url_for('dashboard'))
        flash('Invalid credentials. Demo: teacher / password')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    students = load_students()
    attendance = []
    today_file_path = get_daily_attendance_file_path()
    present_today = set()

    if os.path.exists(today_file_path):
        with open(today_file_path, newline='') as f:
            r = csv.DictReader(f)
            for row in r:
                attendance.append(row)
        # ✅ Only keep latest status per student
        latest_status = {}
        for row in attendance:
            latest_status[row['roll']] = row['status']
        present_today = {roll for roll, status in latest_status.items() if status == "Present"}

    total_students = len(students)
    today_count = len(present_today)

    return render_template(
        'dashboard.html',
        students=students,
        attendance=attendance,
        today_count=today_count,
        total_students=total_students
    )

@app.route('/mark/<roll>')
def mark(roll):
    mark_attendance(roll)
    flash(f'Marked present: {roll}')
    return redirect(url_for('dashboard'))

@app.route('/mark_absent/<roll>')
def mark_absent(roll):
    overwrite_attendance(roll, "Absent")
    flash(f'Marked absent: {roll}')
    return redirect(url_for('dashboard'))

@app.route('/download_report')
def download_report():
    file_path = get_daily_attendance_file_path()
    if not os.path.exists(file_path):
        flash('No attendance recorded today.')
        return redirect(url_for('dashboard'))
    return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))

# ------------------ QR Attendance ------------------

@app.route('/scan_qr', methods=['GET','POST'])
def scan_qr():
    if request.method == 'POST':
        f = request.files.get('qr_image')
        if not f:
            return jsonify({'success': False, 'message': "Upload a QR code image"})

        file_bytes = np.frombuffer(f.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(img)

        if not data:
            return jsonify({'success': False, 'message': "No QR detected"})

        mark_attendance(data)
        return jsonify({'success': True, 'message': f"Marked present: {data}"})

    return render_template('scan_qr.html')

# ------------------ Voice Attendance ------------------

@app.route('/voice_attendance', methods=['GET', 'POST'])
def voice_attendance():
    if request.method == 'POST':
        r = sr.Recognizer()
        with sr.Microphone() as source:
            flash("🎤 Listening... Please speak now")
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=5)
                text = r.recognize_google(audio).lower()
                print("Heard (raw):", text)

                # corrections
                corrections = {
                    "percent": "present",
                    "presence": "present",
                    "absence": "absent",
                    "absinthe": "absent",
                    "are": "r"
                }
                for wrong, right in corrections.items():
                    text = text.replace(wrong, right)

                print("After corrections:", text)

                roll, status = None, None
                words = text.split()

                # detect roll like "r5"
                for i, w in enumerate(words):
                    if w.startswith("r"):
                        num_part = w[1:] if len(w) > 1 else (words[i+1] if i+1 < len(words) else "")
                        if num_part.isdigit():
                            roll = f"R{int(num_part):03d}"

                if "present" in words:
                    status = "Present"
                elif "absent" in words:
                    status = "Absent"

                if roll and status:
                    overwrite_attendance(roll, status)
                    flash(f"✅ Heard: '{text}' → Marked {roll} as {status}")
                else:
                    flash(f"❌ Heard: '{text}' → Could not detect roll/status. Say 'Mark R5 present'")
            except Exception as e:
                flash(f"Error: {str(e)}")

        return redirect(url_for('voice_attendance'))

    return render_template('voice_attendance.html')

# ------------------ Face Recognition ------------------

from deepface import DeepFace
import pandas as pd

@app.route('/scan_faces', methods=['GET', 'POST'])
def scan_faces():
    if request.method == 'GET':
        return render_template('scan_faces.html')

    if 'group_photo' not in request.files:
        flash("No file uploaded")
        return redirect(url_for('scan_faces'))

    file = request.files['group_photo']
    if file.filename == '':
        flash("No selected file")
        return redirect(url_for('scan_faces'))

    try:
        # Save uploaded image temporarily
        temp_path = "temp_group.jpg"
        file.save(temp_path)

        # Search all faces in uploaded image against student database
        results = DeepFace.find(
            img_path=temp_path,
            db_path="students",
            model_name="ArcFace",
            detector_backend="retinaface",
            enforce_detection=False
        )

        found_students = []
        if isinstance(results, list):  # DeepFace returns a list of DataFrames (one per face)
            for df in results:
                if not df.empty:
                    # best match is first row
                    best_match = df.iloc[0]
                    roll = os.path.splitext(os.path.basename(best_match['identity']))[0]
                    if roll not in found_students:
                        found_students.append(roll)
                        mark_attendance(roll)

        os.remove(temp_path)

        if not found_students:
            flash("❌ No known students recognized")
            return redirect(url_for('scan_faces'))

        flash(f"✅ Marked present: {', '.join(found_students)}")
        return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f"Error: {str(e)}")
        return redirect(url_for('scan_faces'))

# ------------------ MAIN ------------------

if __name__ == '__main__':
    ensure_sample_students()
    app.run(debug=True)
