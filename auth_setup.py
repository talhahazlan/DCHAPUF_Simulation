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
        """Process Message B from server"""
        response = self.puf.get_response(msg_b['challenge'])
        self.security_data.loc[len(self.security_data)] = {
            'server_id': msg_b['server_id'],
            'enc_key': msg_b['enc_key'],
            'hash_key': msg_b['hash_key'],
            'challenge': msg_b['challenge'],
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
        return hashlib.sha256(os.urandom(32)).hexdigest()[:16]  # 16-character hash key

    def process_msg_a(self, device_id):
        """Handle Message A: DeviceID sent to server"""
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
        """Handle Message C: Final response from device"""
        if self.current_registration:
            self.database.loc[len(self.database)] = {
                **self.current_registration,
                'server_id': self.id,
                'response': response
            }
            self.current_registration = None

def simulate_setup_phase(device_count=3):
    print(f"\n=== Setup Phase for {device_count} Devices ===")
    server = RegistrationServer()
    devices = []
    
    device_data_dir = Path("device_data")
    device_data_dir.mkdir(exist_ok=True)

    for i in range(device_count):
        device_id = f"DEV_{''.join(np.random.choice(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'), 8))}"
        device = IoTDevice(device_id)
        devices.append(device)

        print(f"\n--- Device {i+1}: {device_id} ---")
        
        # Message A: Device sends DeviceID
        print("1. Device → Server: Message A (Device ID)")
        msg_b = server.process_msg_a(device_id)

        # Message B: Server sends security material
        print("2. Server → Device: Message B (SID, ek, hk, C)")
        print(f"   Encryption Key: {msg_b['enc_key'][:10]}...")
        print(f"   Hash Key: {msg_b['hash_key']}")
        print(f"   Challenge: {msg_b['challenge'][:5]}...")

        # Message C: Device sends response
        response = device.receive_registration_parameters(msg_b)
        print("3. Device → Server: Message C (Response)")
        print(f"   PUF Response: {response}")

        # Finalize registration
        server.process_msg_c(response)
        print("4. Server stores registration entry")

        # Save device data
        device_file = device_data_dir / f"{device_id}_security.csv"
        device.security_data.to_csv(device_file, index=False)
        print(f"   Saved device data to: {device_file}")

    # Save final server database
    server.database.to_csv("server_database.csv", index=False)
    print("\n=== Setup Phase Complete ===")

    print(server.database[['device_id', 'server_id', 'response']])

    # Display example of a device's 
    print(f"\n=== Device Details for {devices[0].id} ===\n")
    print(f"server_id: {devices[0].security_data['server_id'].iloc[0]}")
    print(f"enc_key: {devices[0].security_data['enc_key'].iloc[0][:12]}...")  # First 12 chars
    print(f"hash_key: {devices[0].security_data['hash_key'].iloc[0]}")
    print(f"challenge: {list(devices[0].security_data['challenge'].iloc[0][:4])}...")  # First 4 values
    print(f"response: {devices[0].security_data['response'].iloc[0]}")

    return server, devices


# Run the setup simulation
if __name__ == "__main__":
    server, devices = simulate_setup_phase(3)
