from cryptography.fernet import Fernet
import pandas as pd
import numpy as np
import hashlib
import os
from pathlib import Path
from pypuf.io import random_inputs
from generate_crps import DCHPUF

class IoTDevice:
    def __init__(self, device_id):
        self.id = device_id
        self.puf = DCHPUF(n=64)
        self.security_data = pd.DataFrame(columns=[
            'server_id', 'enc_key', 'hash_key', 'challenge', 'response'
        ])

    def receive_registration_parameters(self, msg_b):
        # Generate response using the received challenge
        response = self.puf.get_response(msg_b['challenge'])
        self.security_data.loc[len(self.security_data)] = {
            'server_id': msg_b['server_id'],
            'enc_key': msg_b['enc_key'],
            'hash_key': msg_b['hash_key'],
            'challenge': msg_b['challenge'].tolist(),  # ✅ Ensure list format
            'response': response
        }
        return response

class RegistrationServer:
    def __init__(self):
        self.id = "Demo_Server"
        self.database = pd.DataFrame(columns=[
            'device_id', 'server_id', 'enc_key',
            'hash_key', 'challenge', 'response'
        ])
        self.current_registration = None

    def create_encryption_key(self):
        return Fernet.generate_key().decode()

    def create_hash_key(self):
        return hashlib.sha256(os.urandom(32)).hexdigest()[:16]

    def process_msg_a(self, device_id):
        # Device sends ID → Server creates registration info
        self.current_registration = {
            'device_id': device_id,
            'enc_key': self.create_encryption_key(),
            'hash_key': self.create_hash_key(),
            'challenge': random_inputs(n=64, N=1, seed=int.from_bytes(os.urandom(4), 'big'))[0]
        }
        return {
            'server_id': self.id,
            'enc_key': self.current_registration['enc_key'],
            'hash_key': self.current_registration['hash_key'],
            'challenge': self.current_registration['challenge']
        }

    def process_msg_c(self, response):
        # Final message: device response → server stores data
        if self.current_registration:
            self.database.loc[len(self.database)] = {
                'device_id': self.current_registration['device_id'],
                'server_id': self.id,
                'enc_key': self.current_registration['enc_key'],
                'hash_key': self.current_registration['hash_key'],
                'challenge': self.current_registration['challenge'].tolist(),  # ✅ Convert to list
                'response': response
            }
            self.current_registration = None

def simulate_setup_phase(device_count=3):
    print(f"\n=== Simulating Setup Phase for {device_count} Devices ===")
    server = RegistrationServer()
    devices = []

    Path("device_data").mkdir(exist_ok=True)

    for i in range(device_count):
        device_id = f"DEV_{''.join(np.random.choice(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'), 8))}"
        device = IoTDevice(device_id)
        devices.append(device)

        print(f"\n--- Device {i+1}: {device_id} ---")

        # Step 1: Device → Server (sends ID)
        print("1. Device sends Message A (Device ID)")
        msg_b = server.process_msg_a(device_id)

        # Step 2: Server → Device (sends encryption material)
        print("2. Server sends Message B (SID, Encryption Key, Hash Key, Challenge)")
        print(f"   Encryption Key (partial): {msg_b['enc_key'][:10]}...")
        print(f"   Hash Key: {msg_b['hash_key']}")
        print(f"   Challenge Preview: {msg_b['challenge'][:5]}...")

        # Step 3: Device responds using PUF
        response = device.receive_registration_parameters(msg_b)
        print("3. Device sends Message C (PUF Response)")
        print(f"   Response: {response}")

        # Step 4: Server stores the registration entry
        server.process_msg_c(response)
        print("4. Server saves the registration record")

        # Save this device's data
        file_path = Path("device_data") / f"{device_id}_security.csv"
        device.security_data.to_csv(file_path, index=False)
        print(f"   Device data saved to: {file_path}")

    # Save full server-side database
    server.database.to_csv("server_database.csv", index=False)
    print("\n=== Registration Complete ===")

    print(server.database[['device_id', 'server_id', 'response']])

    # Print first device's stored data (for inspection)
    print(f"\n=== Stored Details for Device {devices[0].id} ===")
    print(f"Server ID:   {devices[0].security_data['server_id'].iloc[0]}")
    print(f"Enc. Key:    {devices[0].security_data['enc_key'].iloc[0][:12]}...")
    print(f"Hash Key:    {devices[0].security_data['hash_key'].iloc[0]}")
    print(f"Challenge:   {list(devices[0].security_data['challenge'].iloc[0][:4])}...")
    print(f"Response:    {devices[0].security_data['response'].iloc[0]}")

    return server, devices

if __name__ == "__main__":
    server, devices = simulate_setup_phase(3)
    print("\n=== Setup Phase Simulation Complete ===")
