import cv2
import os
import numpy as np

# Path to student images
DATASET_DIR = "student_faces"   # create this folder
MODEL_FILE = "face_model.yml"

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def train_model():
    faces = []
    labels = []

    # Loop over all student images
    for filename in os.listdir(DATASET_DIR):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            path = os.path.join(DATASET_DIR, filename)
            roll = int(os.path.splitext(filename)[0].replace("R", ""))  # e.g. R001 → 1

            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            detected = face_cascade.detectMultiScale(img, 1.3, 5)

            for (x, y, w, h) in detected:
                face = cv2.resize(img[y:y+h, x:x+w], (100, 100))
                faces.append(face)
                labels.append(roll)

    if not faces:
        print("⚠ No faces found in dataset.")
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))
    recognizer.save(MODEL_FILE)
    print(f"✅ Model trained and saved as {MODEL_FILE}")

if __name__ == "__main__":
    train_model()
