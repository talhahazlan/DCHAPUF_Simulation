import hmac, hashlib, base64, secrets, csv
from cryptography.fernet import Fernet

def PUF_response(puf_key: bytes, challenge: bytes) -> bytes:
    return hmac.new(puf_key, challenge, digestmod=hashlib.sha256).digest()

server_master_key = Fernet.generate_key()
server_cipher = Fernet(server_master_key)

device_id = "device01"
device_puf_secret = secrets.token_bytes(32)  # 256-bit secret
encrypted_secret = server_cipher.encrypt(device_puf_secret).decode()

with open('server_db.csv', mode='w', newline='') as db:
    writer = csv.writer(db)
    writer.writerow(["device_id", "puf_secret"])
    writer.writerow([device_id, encrypted_secret])
print(f"Device ID: {device_id}")

device_nonce = secrets.token_bytes(16)
sent_id = device_id
sent_device_nonce = device_nonce

with open('server_db.csv', newline='') as db:
    reader = csv.DictReader(db)
    device_entry = next((row for row in reader if row['device_id'] == sent_id), None)

stored_secret = server_cipher.decrypt(device_entry['puf_secret'].encode())
server_nonce = secrets.token_bytes(16)
combined_challenge = device_nonce + server_nonce
server_K_session = PUF_response(stored_secret, combined_challenge)
HMAC_server = hmac.new(server_K_session, device_nonce, hashlib.sha256).hexdigest()
print(f"Server Nonce: {server_nonce.hex()}")

sent_server_nonce = server_nonce
sent_HMAC_server = HMAC_server
print(f"Server HMAC: {HMAC_server}")

combined = device_nonce + sent_server_nonce
device_K_session = PUF_response(device_puf_secret, combined)
expected_HMAC = hmac.new(device_K_session, device_nonce, hashlib.sha256).hexdigest()

if expected_HMAC != sent_HMAC_server:
    raise Exception("Server authentication failed.")
print("Server authentication successful.")

HMAC_device = hmac.new(device_K_session, sent_server_nonce, hashlib.sha256).hexdigest()
sent_HMAC_device = HMAC_device
print(f"Device HMAC: {HMAC_device}")

expected_HMAC_device = hmac.new(server_K_session, server_nonce, hashlib.sha256).hexdigest()

if expected_HMAC_device != sent_HMAC_device:
    raise Exception("Device authentication failed.")

print("✅ Mutual authentication successful!")
print(f"Device K_session: {device_K_session.hex()}")

fernet_key = base64.urlsafe_b64encode(server_K_session)
session_cipher = Fernet(fernet_key)

message = b"This is a secure message."
ciphertext = session_cipher.encrypt(message)
print("Encrypted:", ciphertext)

decrypted = session_cipher.decrypt(ciphertext)
print("Decrypted:", decrypted.decode())
print("Original:", message.decode())
