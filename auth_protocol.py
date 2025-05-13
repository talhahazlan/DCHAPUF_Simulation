import hashlib
import pandas as pd
import os
import numpy as np
from pathlib import Path
from pypuf.io import random_inputs
from generate_crps import DCHPUF
from cryptography.fernet import Fernet

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
        return ''.join([str(np.random.randint(0, 9)) for _ in range(6)])

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

def setup_device():
    print("\n=== Device Setup Phase ===")
    server = AuthenticationServer()
    device = IoTDevice(f"DEV_{''.join(np.random.choice(list('ABCDEFGHJKLMNPQRSTUVWXYZ23456789'), 8))}")
    
    print(f"\nNew Device: {device.id}")
    print("Generating security parameters...")
    
    # Registration Protocol
    reg2_data = server.process_reg1(device.id)
    response = device.process_reg2(reg2_data)
    server.process_reg3(device.id, reg2_data['enc_key'], reg2_data['hash_key'], 
                      reg2_data['challenge'], response)
    
    print("\nSetup Complete")
    print(f"Encryption Key: {reg2_data['enc_key'][:12]}...")
    print(f"Hash Key: {reg2_data['hash_key']}")
    print(f"PUF Response: {response}")
    
    return device, server

def authenticate_device(device, server):
    print("\n=== Authentication Protocol ===")
    print(f"Authenticating Device: {device.id}")
    
    # First check if device is properly registered
    if device.security_data.empty:
        print("Authentication Failed: Device not properly registered - missing security credentials")
        return False
    
    try:
        # Phase 1: Device → Server
        print("\n[Phase 1] Device Authentication Request")
        session_key = os.urandom(32).hex()
        v0 = hashlib.sha256(f"{session_key}{device.security_data['hash_key'].iloc[0]}".encode()).hexdigest()
        cipher_suite = Fernet(device.security_data['enc_key'].iloc[0].encode())
        ev0 = cipher_suite.encrypt(v0.encode())
        
        print(f"Session Key: {session_key[:12]}...")
        print(f"Verification Hash (V0): {v0[:12]}...")
        
        # Server Verification
        print("\n[Phase 2] Server Verification")
        server_record = server.database[server.database['device_id'] == device.id]
        if server_record.empty:
            print("Authentication Failed: Device not registered in server database")
            return False
            
        try:
            server_cipher = Fernet(server_record['enc_key'].iloc[0].encode())
            decrypted_v0 = server_cipher.decrypt(ev0).decode()
            expected_v0 = hashlib.sha256(f"{session_key}{server_record['hash_key'].iloc[0]}".encode()).hexdigest()
            
            if decrypted_v0 != expected_v0:
                print("Authentication Failed: Verification failed - hash mismatch")
                return False
            print("Device verified successfully")
                
        except Exception as e:
            print(f"Authentication Error: {str(e)}")
            return False

        # Phase 2: Server → Device
        v1 = hashlib.sha256(f"{expected_v0}{server_record['response'].iloc[0]}".encode()).hexdigest()
        ev1 = server_cipher.encrypt(v1.encode())
        
        print("\n[Phase 3] Server Authentication")
        print(f"Verification Hash (V1): {v1[:12]}...")

        # Device Verification
        try:
            decrypted_v1 = cipher_suite.decrypt(ev1).decode()
            expected_v1 = hashlib.sha256(f"{v0}{device.security_data['response'].iloc[0]}".encode()).hexdigest()
            
            if decrypted_v1 != expected_v1:
                print("Authentication Failed: Server verification failed")
                return False
            print("Server verified successfully")
                
        except Exception as e:
            print(f"Authentication Error: {str(e)}")
            return False

        # Phase 3: Device → Server
        print("\n[Phase 4] Security Update")
        new_challenge = random_inputs(n=64, N=1, seed=int.from_bytes(os.urandom(4), 'big'))[0]
        new_response = device.puf.get_response(new_challenge)
        v2 = hashlib.sha256(f"{expected_v1}{new_response}".encode()).hexdigest()
        ev2 = cipher_suite.encrypt(v2.encode())
        
        print(f"New Challenge: {new_challenge[:5]}...")
        print(f"New Response: {new_response}")
        print(f"Verification Hash (V2): {v2[:12]}...")

        # Final Verification
        try:
            decrypted_v2 = server_cipher.decrypt(ev2).decode()
            expected_v2 = hashlib.sha256(f"{v1}{new_response}".encode()).hexdigest()
            
            if decrypted_v2 != expected_v2:
                print("Authentication Failed: Final verification failed")
                return False
                
            # Update records
            idx = server.database[server.database['device_id'] == device.id].index[0]
            server.database.at[idx, 'challenge'] = list(new_challenge)
            server.database.at[idx, 'response'] = new_response
            
            print("\nAUTHENTICATION SUCCESS")
            print("Mutual authentication completed successfully")
            print("Security credentials updated")
            return True
            
        except Exception as e:
            print(f"Authentication Error: {str(e)}")
            return False

    except IndexError:
        print("Authentication Failed: Device missing required security parameters")
        return False
    except Exception as e:
        print(f"Authentication Error: {str(e)}")
        return False

def main():
    # Setup phase
    device, server = setup_device()
    
    # Authentication phase
    authenticate_device(device, server)
    
    # Test failed authentication
    print("\n=== Testing Invalid Authentication ===")
    fake_device = IoTDevice("FAKE_DEVICE")
    authenticate_device(fake_device, server)

if __name__ == "__main__":
    main()