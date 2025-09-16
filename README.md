Attendify 🎓

Attendify is a smart attendance management system with multiple modes:
✔️ QR Code Scanning
✔️ Face Recognition (DeepFace + RetinaFace + ArcFace)
✔️ Voice Commands
✔️ Manual Marking (Present/Absent)

It ensures accuracy, saves time, prevents proxy attendance, and provides secure record-keeping.
Designed for classrooms, offices, and events, Attendify is scalable and easy to use.

🚀 Features

📋 Dashboard – shows real-time attendance summary & logs.

📷 QR Attendance – scan student QR codes to mark presence.

👥 Face Recognition Attendance – group photo analysis with DeepFace (supports multiple backends).

🎤 Voice Attendance – mark attendance using speech commands (e.g., "Mark R005 present").

🖊 Manual Entry – teachers can directly mark students present/absent.

📊 CSV Reports – download daily attendance reports.

🔒 Duplicate Protection – one student cannot be marked twice for the same status.

🛠 Core Technologies

Backend: Flask (Python)

Frontend: HTML, CSS (custom styling with static/style.css)

Computer Vision: OpenCV, DeepFace (ArcFace + RetinaFace)

Voice Recognition: SpeechRecognition / Vosk

Data Storage: CSV-based daily logs (data/attendance_YYYY-MM-DD.csv)

📂 Project Structure
Attendify/
│── app.py                # Main Flask app
│── generate_students.py  # Generate sample students.csv
│── train_faces.py        # Train face recognition model (optional, if used)
│── students/             # Student face images (R001.jpg, R002.jpg, …)
│── data/                 # Attendance CSV logs (auto-generated)
│── templates/            # HTML files (login, dashboard, scan_qr, scan_faces, voice_attendance)
│── static/               # style.css, logo.png
│── README.md             # Project documentation
│── requirements.txt      # Dependencies

⚡ Installation & Setup

Clone the repo

git clone https://github.com/rohit7806/Attendify.git
cd Attendify


Create virtual environment (optional but recommended)

python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux/Mac


Install dependencies

pip install -r requirements.txt


Example requirements.txt:

flask
opencv-python
numpy
deepface
speechrecognition
vosk
sounddevice


Run the app

python app.py


Open in browser:
👉 http://127.0.0.1:5000/

Login credentials (demo):

Username: teacher
Password: password

📸 Screenshots

Login Page

Dashboard

QR Scan

Face Recognition Upload

Voice Attendance

(Add screenshots here after running the app locally)

📌 Future Enhancements

Cloud integration for central attendance storage

Mobile app version

Multi-language speech support

Face recognition live webcam mode

📜 License

This project is licensed under the MIT License – free to use and modify.
