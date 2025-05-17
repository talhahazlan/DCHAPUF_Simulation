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

    def process_reg2(self, reg2_data):
        """Process REG2 message from server"""
        response = self.puf.get_response(reg2_data['challenge'])
        self.security_data.loc[len(self.security_data)] = {
            'server_id': reg2_data['server_id'],
            'enc_key': reg2_data['enc_key'],
            'hash_key': reg2_data['hash_key'],
            'challenge': reg2_data['challenge'],
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
        self.current_registration = None

    def generate_enc_key(self):
        return Fernet.generate_key().decode()

    def generate_hash_key(self):
        return hashlib.sha256(os.urandom(32)).hexdigest()[:16]  # 16-byte key

    def process_reg1(self, device_id):
        """Process REG1 message from device"""
        self.current_registration = {
            'device_id': device_id,
            'enc_key': self.generate_enc_key(),
            'hash_key': self.generate_hash_key(),
            'challenge': random_inputs(n=64, N=1, seed=int.from_bytes(os.urandom(4), 'big'))[0]
        }
        return {
            'server_id': self.id,
            'enc_key': self.current_registration['enc_key'],
            'hash_key': self.current_registration['hash_key'],
            'challenge': self.current_registration['challenge']
        }

    def process_reg3(self, response):
        """Process REG3 message from device"""
        if self.current_registration:
            self.database.loc[len(self.database)] = {
                **self.current_registration,
                'server_id': self.id,
                'response': response
            }
            self.current_registration = None

def simulate_multi_device_setup(num_devices=3):
    print(f"=== Setup Phase for {num_devices} Devices ===")
    server = AuthenticationServer()
    devices = []
    
    # Create device_data folder if it doesn't exist
    device_data_dir = Path("device_data")
    device_data_dir.mkdir(exist_ok=True)
    
    for i in range(num_devices):
        device_id = f"DEV_{''.join(np.random.choice(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'), 8))}"
        device = IoTDevice(device_id)
        devices.append(device)
        
        print(f"\n=== Device {i+1}: {device_id} ===")
        
        # REG1: Device registration request
        print("\n1. Device -> Server: REG1")
        
        # REG2: Server responds with security parameters
        reg2_data = server.process_reg1(device_id)
        print("\n2. Server -> Device: REG2")
        print(f"   Encryption Key: {reg2_data['enc_key'][:10]}...")
        print(f"   Hash Key: {reg2_data['hash_key']}")
        print(f"   Challenge: {reg2_data['challenge'][:5]}...")
        
        # REG3: Device responds with PUF response
        response = device.process_reg2(reg2_data)
        print("\n3. Device -> Server: REG3")
        print(f"   PUF Response: {response}")
        
        # Server finalizes registration
        server.process_reg3(response)
        print("\n4. Server stores registration")
        
        # Save device data to device_data folder
        device_file = device_data_dir / f"{device_id}_security.csv"
        device.security_data.to_csv(device_file, index=False)
        print(f"   Saved device data to: {device_file}")
    
    # Save server database
    server.database.to_csv('server_database.csv', index=False)
    
    print("\n=== Setup Complete ===")
    print(f"\nServer Database ({len(server.database)} devices):")
    print(server.database[['device_id', 'server_id', 'response']])
    
    return server, devices

# Simulate setup for 3 devices
server, devices = simulate_multi_device_setup(3)