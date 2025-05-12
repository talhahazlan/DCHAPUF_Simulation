import pandas as pd
import numpy as np
import hmac, hashlib, base64
from cryptography.fernet import Fernet
from generate_crps import DCHPUF

# Load stored CSVs
server_db = pd.read_csv("data/server_database.csv")
device_db = pd.read_csv("data/device_database.csv")

# Step 1: Retrieve values
device_id = device_db.loc[0, 'DeviceID']
server_id = device_db.loc[0, 'ServerID']
hash_key = int(device_db.loc[0, 'HashKey'])
encryption_key = device_db.loc[0, 'EncKey']
stored_challenge_str = server_db.loc[0, 'Challenge']

# Step 2: Convert challenge string to binary array
challenge_bits = [int(b) for b in stored_challenge_str]
challenge_array = np.array(challenge_bits, dtype=np.uint8)
challenge = np.where(challenge_array == 0, -1, 1)  # Convert to {-1, 1} for PyPUF

# Step 3: Regenerate DCH-PUF response
puf = DCHPUF(n=64)
response = puf.get_response(challenge)

# Step 4: Derive session key using HMAC (server + device both do this)
challenge_bytes = challenge_array.tobytes()
response_bytes = int(response).to_bytes(1, byteorder='big')
session_key_raw = hmac.new(str(hash_key).encode(), challenge_bytes + response_bytes, hashlib.sha256).digest()

# Step 5: Symmetric encryption using derived session key
fernet_key = base64.urlsafe_b64encode(session_key_raw[:32])  # Fernet requires 32 bytes
cipher = Fernet(fernet_key)

# Encrypt a message
message = b"This is a secure message."
ciphertext = cipher.encrypt(message)
decrypted = cipher.decrypt(ciphertext)

# Step 6: Output results
print("\n✅ Authentication Phase Complete")
print(f"Device ID: {device_id}")
print(f"Server ID: {server_id}")
print(f"PUF Response: {response}")
print(f"Session Key (first 16 bytes): {session_key_raw[:16].hex()}")
print(f"Encrypted Message: {ciphertext.decode()}")
print(f"Decrypted Message: {decrypted.decode()}")
