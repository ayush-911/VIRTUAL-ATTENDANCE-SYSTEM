import cv2
import os
import numpy as np

DATASET_DIR = "dataset"
TRAINER_DIR = "trainer"
MODEL_PATH = os.path.join(TRAINER_DIR, "trainer.yml")
MAPPING_PATH = os.path.join(TRAINER_DIR, "labels.txt")

face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def register_face_images(name, frame, max_images=10):
    """
    Saves face images from current frame (Flask sends last_frame)
    """
    if frame is None:
        return False, "❌ No frame received. Start camera first!"

    os.makedirs(DATASET_DIR, exist_ok=True)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        return False, "❌ No face detected. Try again!"

    if len(faces) > 1:
        return False, "❌ Multiple faces detected. Only 1 face allowed!"

    (x, y, w, h) = faces[0]
    face_img = gray[y:y+h, x:x+w]

    safe_name = "".join(c for c in name if c.isalnum() or c in ["_", "-"]).strip()
    if not safe_name:
        return False, "❌ Invalid name!"

    existing = [f for f in os.listdir(DATASET_DIR) if f.startswith(safe_name + ".")]
    start_index = len(existing) + 1

    saved = 0
    for i in range(start_index, start_index + max_images):
        path = os.path.join(DATASET_DIR, f"{safe_name}.{i}.jpg")
        cv2.imwrite(path, face_img)
        saved += 1

    return True, f"✅ Saved {saved} images for {name}"


def train_model():
    """
    Trains LBPH model from dataset images
    """
    if not os.path.exists(DATASET_DIR):
        return False, "❌ Dataset folder not found. Register faces first!"

    images = [f for f in os.listdir(DATASET_DIR) if f.endswith(".jpg")]
    if len(images) == 0:
        return False, "❌ No images found. Register face first!"

    os.makedirs(TRAINER_DIR, exist_ok=True)

    recognizer = cv2.face.LBPHFaceRecognizer_create()

    faces = []
    labels = []
    name_to_id = {}
    current_id = 1

    for file in images:
        name = file.split(".")[0]

        if name not in name_to_id:
            name_to_id[name] = current_id
            current_id += 1

        label_id = name_to_id[name]
        path = os.path.join(DATASET_DIR, file)

        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue

        detected = face_detector.detectMultiScale(img, 1.2, 5)
        for (x, y, w, h) in detected:
            faces.append(img[y:y+h, x:x+w])
            labels.append(label_id)

    if len(faces) == 0:
        return False, "❌ No usable faces found. Register again!"

    recognizer.train(faces, np.array(labels))
    recognizer.write(MODEL_PATH)

    # Save mapping ID -> Name
    with open(MAPPING_PATH, "w") as f:
        for name, id_ in name_to_id.items():
            f.write(f"{id_}:{name}\n")

    return True, "✅ Training complete! Model saved."


def recognize_face(frame):
    """
    Returns: annotated frame, recognized_name, face_count
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray, 1.2, 5)
    face_count = len(faces)

    if not os.path.exists(MODEL_PATH):
        # Draw face boxes even without training
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, "Not Trained", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        return frame, "Unknown", face_count

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_PATH)

    # Load mapping
    id_to_name = {}
    if os.path.exists(MAPPING_PATH):
        with open(MAPPING_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if ":" in line:
                    id_, name = line.split(":", 1)
                    id_to_name[int(id_)] = name

    recognized_name = "Unknown"

    for (x, y, w, h) in faces:
        roi = gray[y:y+h, x:x+w]
        id_, confidence = recognizer.predict(roi)

        if confidence < 70:
            recognized_name = id_to_name.get(id_, "Unknown")
            label = recognized_name
        else:
            label = "Unknown"

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, label, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    return frame, recognized_name, face_count
