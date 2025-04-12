import firebase_admin
from firebase_admin import credentials, firestore
import google.cloud
import time
import board
import busio
from adafruit_pn532.i2c import PN532_I2C
import os
import codecs
import sys

# Initialize I2C connection
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize PN532 NFC reader
pn532 = PN532_I2C(i2c, debug=False)

# Wake up the PN532 (get firmware to confirm communication)
ic, ver, rev, support = pn532.firmware_version
print(f"PN532 ready - Firmware version: {ver}.{rev}")

# Configure PN532 to read RFID tags
pn532.SAM_configuration()

print("Waiting for NFC card...")

# Initialize Firebase app
cred = credentials.Certificate("nfc-access-control-d88af-firebase-adminsdk-fbsvc-4993d99aee.json")
firebase_admin.initialize_app(cred)

# Connect to Firestore
db = firestore.client()
"""
doc_ref = db.collection(u'NFC-access').limit(2)

print('test')
try:
    docs = doc_ref.get()
    for doc in docs:
        print(u'Doc Data:{}'.format(doc.to_dict()))
        
except google.cloud.exceptions.NotFound:
    print(u'Missing data')
"""
def is_card_authorized(scanned_card_id: str) -> bool:
    
    logs_ref = db.collection('NFC-access')
    query = logs_ref.where(filter=firestore.FieldFilter('uid', '==', scanned_card_id)).limit(1)
    results = query.stream()
    print(results)
    for doc in results:
        image = doc.to_dict().get("image")
        #print(image)
        build_image(image)
        print("Finished building image")
        #rint(f"Authorized card: {doc.to_dict()}")
        return True  # Card ID found

    print("Unauthorized card")
    return False  # Not found
    
def build_image(binaryData):
    #filename = sys.argv[1]
    #binFile = open(filename,'rb')
    #binaryData = binFile.read()
    hexData = '%0*X' % ((len(binaryData) + 3) // 4, int(binaryData, 2))

    decode_hex = codecs.getdecoder("hex_codec")
    hexData = decode_hex(hexData)[0]

    #parsed_filename = os.path.splitext(os.path.basename(filename))[0]
    png_filename = 'aaron' + '_from_binary.jpg'
    with open(png_filename, 'wb') as file:
        file.write(hexData)
    
    """
    print("📡 Fetching all documents in 'access_logs'...")
    docs = db.collection('NFC-access').stream()
    found = False
    print(len(docs))
    for doc in docs:
        print(f"🔍 Found document: {doc.id} => {doc.to_dict()}")
        found = True
    if not found:
        print("⚠️ No documents found in 'access_logs'")
        
    
    users_ref = db.collection('NFC-access')
    docs = users_ref.stream()
    
    for doc in docs:
        print(f"{doc.id} => {doc.to_dict()}")
    """

while True:
    uid = pn532.read_passive_target(timeout=0.5)
    if uid is not None:
        uid_str = ''.join(f'{byte:02x}' for byte in uid)
        print(type(uid_str))
        print(uid_str)
        is_card_authorized(uid_str)
    """
    if uid is not None:
        uid_hex = ''.join(f'{byte:02X}' for byte in uid)
        print(f"Card detected! UID: {uid_hex}")
    """
    time.sleep(0.5)  # Delay to reduce CPU usage
