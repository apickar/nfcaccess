import time
import board
import busio
import digitalio
from adafruit_pn532.i2c import PN532_I2C
import RPi.GPIO as GPIO
import cv2
import face_recognition
import numpy as np
import os

# GPIO setup
#RELAY_PIN = 18   # GPIO18 for relay control
LED_RED_PIN = 17  # GPIO17 for red LED (access denied)
BUZZER_PIN = 18   # GPIO22 for buzzer (access denied)
LED_GREEN_PIN = 27 #GPIO27 for green LED (access granted)

GPIO.setmode(GPIO.BCM)
#GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.setup(LED_RED_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(LED_GREEN_PIN, GPIO.OUT)

# Initialize I2C interface for PN532
i2c = busio.I2C(board.SCL, board.SDA)
pn532 = PN532_I2C(i2c, debug=False)
pn532.SAM_configuration()

# Define authorized UIDs
def is_authorized(uid):
    authorized_uids = [
        "4105b889",  # Blue NFC card
        "1234567890",
    ]
    return uid in authorized_uids
    
# Directories to store images
GRANTED_DIR = "granted_images"
DENIED_DIR = "denied_images"
REFERENCE_IMAGES_DIR = "reference_images"

# Ensure directories exist
os.makedirs(GRANTED_DIR, exist_ok=True)
os.makedirs(DENIED_DIR, exist_ok=True)

# Load and encode reference images
def load_reference_images():
    reference_encodings = []
    reference_names = []
    
    for filename in os.listdir(REFERENCE_IMAGES_DIR):
        if filename.endswith((".jpg", ".png")):
            image_path = os.path.join(REFERENCE_IMAGES_DIR, filename)
            image = face_recognition.load_image_file(image_path)
            
            encodings = face_recognition.face_encodings(image)
            if encodings:
                reference_encodings.append(encodings[0])
                reference_names.append(filename.split('.')[0])  # Store names without extension

    return reference_encodings, reference_names

# Initialize webcam
video_capture = cv2.VideoCapture(0)

def capture_image(status):
    """Capture an image and save it based on status (granted/denied)."""
    ret, frame = video_capture.read()
    if not ret:
        print("Error capturing image.")
        return None
    
    # Determine filename and path
    if status == "granted":
        count = len(os.listdir(GRANTED_DIR)) + 1
        filename = f"{GRANTED_DIR}/granted_{count}.jpg"
    else:
        count = len(os.listdir(DENIED_DIR)) + 1
        filename = f"{DENIED_DIR}/denied_{count}.jpg"

    cv2.imwrite(filename, frame)
    print(f"📸 Image saved as {filename}")
    return frame

def match_faces(captured_frame, known_encodings, known_names):
    """Compare captured image with stored reference images."""
    captured_encoding = face_recognition.face_encodings(captured_frame)
    
    if not captured_encoding:
        print("No face detected in captured image.")
        return None

    matches = face_recognition.compare_faces(known_encodings, captured_encoding[0])
    face_distances = face_recognition.face_distance(known_encodings, captured_encoding[0])

    best_match_index = np.argmin(face_distances) if matches else None
    return known_names[best_match_index] if best_match_index is not None else None

# Load all reference images
known_encodings, known_names = load_reference_images()

print("Waiting for NFC card...")
while True:
    uid = pn532.read_passive_target(timeout=0.5)
    if uid:
        uid_str = "".join(["{:02x}".format(i) for i in uid])
        print(f"Card UID: {uid_str}")
        
        if is_authorized(uid_str):
            print("✅ Access Granted! Capturing Image...")
           # GPIO.output(RELAY_PIN, GPIO.HIGH)
            captured_frame = capture_image("granted")
            
            if captured_frame is not None:
                print("Matching face with reference images...")
                matched_name = match_faces(captured_frame, known_encodings, known_names)
        
                if matched_name:
                    print(f"✅ Face Matched with {matched_name}! Access Confirmed.")
                else:
                    print("⚠️ Face not recognized, but access was granted.")
            GPIO.output(LED_GREEN_PIN, GPIO.HIGH)
            time.sleep(3)  # Keep relay open for 3 sec
            #GPIO.output(RELAY_PIN, GPIO.LOW)
            GPIO.output(LED_GREEN_PIN, GPIO.LOW)
        else:
            print("❌ Access Denied! Capturing Image...")
            capture_image("denied")
            GPIO.output(LED_RED_PIN, GPIO.HIGH)
            pwm = GPIO.PWM(BUZZER_PIN, 10000)
            pwm.start(20)
            #GPIO.output(BUZZER_PIN, GPIO.HIGH)
            time.sleep(3)  # Buzzer and LED stay on for 2 sec
            GPIO.output(LED_RED_PIN, GPIO.LOW)
            #GPIO.output(BUZZER_PIN, GPIO.LOW)
            pwm.stop()
    time.sleep(0.5)  # Poll every 500ms

   # Release resources
    video_capture.release()
    cv2.destroyAllWindows()
