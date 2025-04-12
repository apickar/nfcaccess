# next step

import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase app
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)

# Connect to Firestore
db = firestore.client()

third step: 

def is_card_authorized(scanned_card_id: str) -> bool:
    logs_ref = db.collection('access_logs')
    query = logs_ref.where('card_id', '==', scanned_card_id).limit(1)
    results = query.stream()

    for doc in results:
        print(f"Authorized card: {doc.to_dict()}")
        return True  # Card ID found

    print("Unauthorized card")
    return False  # Not found




scanned_card_id = "123456ABC"  # Read from NFC reader

if is_card_authorized(scanned_card_id):
    print("✅ Access Granted")
    # Optionally: light green LED
else:
    print("❌ Access Denied")
    # 🔴 Trigger red LED or buzzer (your part!)
