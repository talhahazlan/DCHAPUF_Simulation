import hashlib
import pandas as pd
import os
import numpy as np
from pathlib import Path
from pypuf.io import random_inputs
from generate_crps import DCHPUF
from cryptography.fernet import Fernet


# --- Device and Server Classes ---

class IoTDevice:
    def __init__(self, device_id):
        self.id = device_id
        self.puf = DCHPUF(n=64)
        self.security_data = pd.DataFrame(columns=[
            'server_id', 'enc_key', 'hash_key', 'challenge', 'response'
        ])

    def process_reg2(self, reg2_data):
        response = self.puf.get_response(reg2_data['challenge'])
        self.security_data.loc[len(self.security_data)] = {
            'server_id': reg2_data['server_id'],
            'enc_key': reg2_data['enc_key'],
            'hash_key': reg2_data['hash_key'],
            'challenge': list(reg2_data['challenge']),
            'response': response
        }
        return response

class AuthenticationServer:
    def __init__(self):
        self.id = "Demo_Server"
        self.database = pd.DataFrame(columns=[
            'device_id', 'server_id', 'enc_key',
            'hash_key', 'challenge', 'response'
        ])

    def generate_enc_key(self):
        return Fernet.generate_key().decode()

    def generate_hash_key(self):
        return hashlib.sha256(os.urandom(32)).hexdigest()[:16]

    def process_reg1(self, device_id):
        return {
            'server_id': self.id,
            'enc_key': self.generate_enc_key(),
            'hash_key': self.generate_hash_key(),
            'challenge': random_inputs(n=64, N=1, seed=int.from_bytes(os.urandom(4), 'big'))[0]
        }

    def process_reg3(self, device_id, enc_key, hash_key, challenge, response):
        self.database.loc[len(self.database)] = {
            'device_id': device_id,
            'server_id': self.id,
            'enc_key': enc_key,
            'hash_key': hash_key,
            'challenge': list(challenge),
            'response': response
        }

# --- Setup & Authentication ---

def setup_device():
    print("\n=== DEVICE REGISTRATION PHASE ===")
    server = AuthenticationServer()
    device_id = f"DEV_{''.join(np.random.choice(list('ABCDEFGHJKLMNPQRSTUVWXYZ23456789'), 8))}"
    device = IoTDevice(device_id)

    print(f"Registering new device: {device_id}")
    reg2_data = server.process_reg1(device_id)
    response = device.process_reg2(reg2_data)
    server.process_reg3(device_id, reg2_data['enc_key'], reg2_data['hash_key'], reg2_data['challenge'], response)

    print("\nSetup complete.")
    print(f"Encryption Key: {reg2_data['enc_key'][:12]}...")
    print(f"Hash Key: {reg2_data['hash_key']}")
    print(f"PUF Response: {response}")

    return device, server

def authenticate_device(device, server):
    print("\n" + "="*50)
    print("  STARTING AUTHENTICATION PROTOCOL")
    print("="*50)

    if device.security_data.empty:
        print("[!] Device has no security data. Not registered.")
        return False

    try:
        # Session setup
        session_key = os.urandom(32).hex()
        hash_key = device.security_data['hash_key'].iloc[0]
        enc_key = device.security_data['enc_key'].iloc[0]
        cipher = Fernet(enc_key.encode())

        v0 = hashlib.sha256((session_key + hash_key).encode()).hexdigest()
        ev0 = cipher.encrypt(v0.encode())

        print("\n[Phase 1: Device → Server]")
        print(f"Generated Session Key: {session_key[:12]}...")
        print(f"Encrypted V0: {ev0[:12]}...")

        # Server receives and validates
        server_record = server.database[server.database['device_id'] == device.id]
        if server_record.empty:
            print("[!] Server has no matching record.")
            return False

        server_cipher = Fernet(server_record['enc_key'].iloc[0].encode())
        decrypted_v0 = server_cipher.decrypt(ev0).decode()
        expected_v0 = hashlib.sha256((session_key + server_record['hash_key'].iloc[0]).encode()).hexdigest()

        print("\n[Phase 2: Server Verification]")
        if decrypted_v0 != expected_v0:
            print("[!] Server validation failed.")
            return False
        print("[✓] Device verified.")

        # Server authenticates itself
        v1 = hashlib.sha256((expected_v0 + str(server_record['response'].iloc[0])).encode()).hexdigest()
        ev1 = server_cipher.encrypt(v1.encode())

        print("\n[Phase 3: Server → Device]")
        print(f"Encrypted V1: {ev1[:12]}...")

        # Device validates server
        decrypted_v1 = cipher.decrypt(ev1).decode()
        expected_v1 = hashlib.sha256((v0 + str(device.security_data['response'].iloc[0])).encode()).hexdigest()

        print("\n[Phase 4: Device Verification]")
        if decrypted_v1 != expected_v1:
            print("[!] Server authentication failed.")
            return False
        print("[✓] Server verified.")

        # CRP Update
        new_challenge = random_inputs(n=64, N=1, seed=int.from_bytes(os.urandom(4), 'big'))[0]
        new_response = device.puf.get_response(new_challenge)

        v2 = hashlib.sha256((expected_v1 + str(new_response)).encode()).hexdigest()
        ev2 = cipher.encrypt(v2.encode())

        decrypted_v2 = server_cipher.decrypt(ev2).decode()
        expected_v2 = hashlib.sha256((v1 + str(new_response)).encode()).hexdigest()

        print("\n[Phase 5: CRP Update]")
        if decrypted_v2 != expected_v2:
            print("[!] Final verification failed.")
            return False

        # Update server DB
        idx = server.database[server.database['device_id'] == device.id].index[0]
        server.database.at[idx, 'challenge'] = list(new_challenge)
        server.database.at[idx, 'response'] = new_response

        print("[✓] CRP updated successfully.")
        print("="*50)
        print("[SUCCESS] Mutual authentication completed.")
        return True

    except Exception as e:
        print(f"[ERROR] Authentication failed: {str(e)}")
        return False

# --- Attack Simulations ---

def simulate_adversary_attacks(server):
    print("\n=== ADVERSARY ATTACK SIMULATION ===")

    if server.database.empty:
        print("No devices to attack. Run setup first.")
        return

    device_id = server.database.iloc[0]['device_id']

    print(f"\n[Attack 1] Replay Attack - using device ID: {device_id}")
    fake_device = IoTDevice(device_id)
    result = authenticate_device(fake_device, server)
    print("Result: Replay Attack Blocked" if not result else "Replay Attack Bypassed [!]")

    print(f"\n[Attack 2] MITM Attack")
    mitm = IoTDevice(device_id)
    mitm.security_data.loc[0] = {
        'server_id': "FAKE",
        'enc_key': Fernet.generate_key().decode(),
        'hash_key': '000000',
        'challenge': random_inputs(n=64, N=1, seed=999)[0],
        'response': 1
    }
    result = authenticate_device(mitm, server)
    print("Result: MITM Blocked" if not result else "MITM Succeeded [!]")

    print(f"\n[Attack 3] Brute Force Attack")
    brute = IoTDevice(device_id)
    brute.security_data.loc[0] = {
        'server_id': server.id,
        'enc_key': Fernet.generate_key().decode(),
        'hash_key': ''.join(str(np.random.randint(10)) for _ in range(6)),
        'challenge': random_inputs(n=64, N=1, seed=1234)[0],
        'response': np.random.randint(0, 2)
    }
    result = authenticate_device(brute, server)
    print("Result: Brute Force Blocked" if not result else "Brute Force Succeeded [!]")

    print("\nAll simulated attacks completed.")

# --- Main Simulation ---

def main():
    # Setup phase
    print("=== PUF-Based Authentication System ===")
    device, server = setup_device()
    
    # Valid authentication
    authenticate_device(device, server)
    
    # # Invalid authentication
    # print("\n=== Testing Invalid Authentication ===")
    # fake_device = IoTDevice("FAKE_DEVICE")
    # authenticate_device(fake_device, server)
    
    # Security attack simulations
    # simulate_adversary_attacks(server)

if __name__ == "__main__":
    main()

    