import pandas as pd
import secrets
import hmac, hashlib
from cryptography.fernet import Fernet

# === 1. SETUP MULTIPLE DEVICES ===

def setup_devices(num_devices=5):
    server_id = "Demo_Server"
    server_db = []
    device_db = []

    for i in range(1, num_devices + 1):
        device_id = f"Device_{str(i).zfill(3)}"
        puf_seed = secrets.randbelow(10000)
        fernet_key = Fernet.generate_key()
        hash_key = secrets.randbelow(10**8)

        # Add to server DB
        server_db.append({'DID': device_id, 'hk': hash_key})

        # Add to device DB
        device_db.append({
            'DeviceID': device_id,
            'ServerID': server_id,
            'PUF seed': puf_seed,
            'encryptionKey': fernet_key.decode(),
            'hashkey': hash_key
        })

    # Save to CSV
    pd.DataFrame(server_db).to_csv('server_database.csv', index=False)
    pd.DataFrame(device_db).to_csv('device_database.csv', index=False)
    print(f"✅ Setup complete for {num_devices} devices.")

# === 2. AUTHENTICATION FOR A GIVEN DEVICE_ID ===

def authenticate_device(device_id):
    device_df = pd.read_csv('device_database.csv')
    server_df = pd.read_csv('server_database.csv')

    row = device_df[device_df['DeviceID'] == device_id].iloc[0]
    server_entry = server_df[server_df['DID'] == device_id].iloc[0]

    # Extract info
    fernet_key = row['encryptionKey'].encode()
    hash_key = int(row['hashkey'])
    server_hash_key = int(server_entry['hk'])
    cipher = Fernet(fernet_key)

    # Device and server nonces
    device_nonce = secrets.token_bytes(16)
    server_nonce = secrets.token_bytes(16)

    def derive_session_key(secret: int, challenge: bytes) -> bytes:
        return hmac.new(str(secret).encode(), challenge, digestmod=hashlib.sha256).digest()

    # Combine and derive keys
    combined = device_nonce + server_nonce
    server_K_session = derive_session_key(server_hash_key, combined)
    device_K_session = derive_session_key(hash_key, combined)

    # Mutual HMAC exchange
    server_HMAC = hmac.new(server_K_session, device_nonce, hashlib.sha256).hexdigest()
    expected_HMAC = hmac.new(device_K_session, device_nonce, hashlib.sha256).hexdigest()
    server_verified = (expected_HMAC == server_HMAC)

    device_HMAC = hmac.new(device_K_session, server_nonce, hashlib.sha256).hexdigest()
    expected_HMAC_device = hmac.new(server_K_session, server_nonce, hashlib.sha256).hexdigest()
    device_verified = (device_HMAC == expected_HMAC_device)

    print(f"\n🔐 Mutual Authentication for {device_id}:")
    print(f"✔️ Device verified server: {server_verified}")
    print(f"✔️ Server verified device: {device_verified}")
    print(f"🔑 Session Key: {device_K_session.hex()[:32]}...")

# === RUN ===

if __name__ == "__main__":
    setup_devices(num_devices=5)  # You can change the number here
    authenticate_device("Device_003")  # You can try any device from Device_001 to Device_005
