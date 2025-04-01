# NFC Facial Authentication with Cryptography and FreeRTOS

import time
import board
import busio
import digitalio
import asyncio
import cv2
import face_recognition
import numpy as np
import os
import RPi.GPIO as GPIO
from cryptography.fernet import Fernet
from adafruit_pn532.i2c import PN532_I2C

# GPIO setup
LED_RED_PIN = 17  # GPIO17 for red LED (access denied)
BUZZER_PIN = 18   # GPIO22 for buzzer (access denied)
LED_GREEN_PIN = 27 # GPIO27 for green LED (access granted)

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_RED_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(LED_GREEN_PIN, GPIO.OUT)

# Initialize I2C interface for PN532
i2c = busio.I2C(board.SCL, board.SDA)
pn532 = PN532_I2C(i2c, debug=False)
pn532.SAM_configuration()

# Cryptography setup
SECRET_KEY = Fernet.generate_key()  # This should be stored securely in a real implementation
cipher = Fernet(SECRET_KEY)

def encrypt_uid(uid):
    return cipher.encrypt(uid.encode()).decode()

def decrypt_uid(encrypted_uid):
    return cipher.decrypt(encrypted_uid.encode()).decode()

# Define authorized UIDs (encrypted)
authorized_uids = [encrypt_uid("4105b889"), encrypt_uid("1234567890")]

def is_authorized(uid):
    encrypted_uid = encrypt_uid(uid)
    return encrypted_uid in authorized_uids

# Directories to store images
GRANTED_DIR = "granted_images"
DENIED_DIR = "denied_images"
REFERENCE_IMAGES_DIR = "reference_images"

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
                reference_names.append(filename.split('.')[0])
    return reference_encodings, reference_names

# Initialize webcam
video_capture = cv2.VideoCapture(0)

async def capture_image(status):
    ret, frame = video_capture.read()
    if not ret:
        print("Error capturing image.")
        return None
    
    if status == "granted":
        count = len(os.listdir(GRANTED_DIR)) + 1
        filename = f"{GRANTED_DIR}/granted_{count}.jpg"
    else:
        count = len(os.listdir(DENIED_DIR)) + 1
        filename = f"{DENIED_DIR}/denied_{count}.jpg"

    cv2.imwrite(filename, frame)
    print(f"📸 Image saved as {filename}")
    return frame

async def match_faces(captured_frame, known_encodings, known_names):
    captured_encoding = face_recognition.face_encodings(captured_frame)
    if not captured_encoding:
        print("No face detected in captured image.")
        return None
    matches = face_recognition.compare_faces(known_encodings, captured_encoding[0])
    face_distances = face_recognition.face_distance(known_encodings, captured_encoding[0])
    best_match_index = np.argmin(face_distances) if any(matches) else None
    return known_names[best_match_index] if best_match_index is not None else None

async def nfc_reader():
    print("Waiting for NFC card...")
    while True:
        uid = pn532.read_passive_target(timeout=0.5)
        if uid:
            uid_str = "".join(["{:02x}".format(i) for i in uid])
            print(f"Card UID: {uid_str}")
            if is_authorized(uid_str):
                print("✅ Access Granted! Capturing Image...")
                captured_frame = await capture_image("granted")
                if captured_frame is not None:
                    print("Matching face with reference images...")
                    matched_name = await match_faces(captured_frame, known_encodings, known_names)
                    if matched_name:
                        print(f"✅ Face Matched with {matched_name}! Access Confirmed.")
                        GPIO.output(LED_GREEN_PIN, GPIO.HIGH)
                        await asyncio.sleep(3)
                        GPIO.output(LED_GREEN_PIN, GPIO.LOW)
                    else:
                        print("⚠️ Face not recognized. Access denied.")
                        await capture_image("denied")
                        GPIO.output(LED_RED_PIN, GPIO.HIGH)
                        pwm = GPIO.PWM(BUZZER_PIN, 10000)
                        pwm.start(20)
                        await asyncio.sleep(3)
                        GPIO.output(LED_RED_PIN, GPIO.LOW)
                        pwm.stop()
            else:
                print("❌ Access Denied! Capturing Image...")
                await capture_image("denied")
                GPIO.output(LED_RED_PIN, GPIO.HIGH)
                pwm = GPIO.PWM(BUZZER_PIN, 10000)
                pwm.start(20)
                await asyncio.sleep(3)
                GPIO.output(LED_RED_PIN, GPIO.LOW)
                pwm.stop()
        await asyncio.sleep(0.5)

async def main():
    global known_encodings, known_names
    known_encodings, known_names = load_reference_images()
    await nfc_reader()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        video_capture.release()
        cv2.destroyAllWindows()
