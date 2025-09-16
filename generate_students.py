# generate_students.py
import csv, os, qrcode

STUDENTS_FILE = 'students.csv'
QR_DIR = os.path.join('static', 'qr_codes')
os.makedirs(QR_DIR, exist_ok=True)

# Create sample students file if not exists
if not os.path.exists(STUDENTS_FILE):
    with open(STUDENTS_FILE, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['roll','name'])
        for i in range(1, 31):  # change 31 -> 71 for 70 students
            roll = f"R{str(i).zfill(3)}"
            name = f"Student_{i}"
            w.writerow([roll, name])

# Generate QR codes
with open(STUDENTS_FILE, newline='') as f:
    r = csv.DictReader(f)
    for row in r:
        roll = row['roll']
        img = qrcode.make(roll)
        img.save(os.path.join(QR_DIR, f"{roll}.png"))

print(f"✅ QR codes saved in {QR_DIR}")
