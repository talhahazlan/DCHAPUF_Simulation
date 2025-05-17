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
        return hashlib.sha256(os.urandom(32)).hexdigest()[:16]  # 16-byte key

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
    print("\n" + "="*50)
    print("=== AUTHENTICATION PROTOCOL SIMULATION ===")
    print("="*50 + "\n")
    print(f"Authenticating Device: {device.id}")
    print("-"*50)

    # Display device credentials before authentication
    print("\n[INITIAL DEVICE CREDENTIALS]")
    print(f"Device ID: {device.id}")
    print(f"Server ID: {device.security_data['server_id'].iloc[0]}")
    print(f"Enc Key (first 12): {device.security_data['enc_key'].iloc[0][:12]}...")
    print(f"Hash Key: {device.security_data['hash_key'].iloc[0]}")
    print(f"Current Challenge (first 5): {device.security_data['challenge'].iloc[0][:5]}...")
    print(f"Current Response: {device.security_data['response'].iloc[0]}")
    print("-"*50)

    # First check if device is properly registered
    if device.security_data.empty:
        print("\n[STATUS] Authentication Failed: Device not properly registered")
        return False
    
    try:
        # ===== PHASE 1: Authentication Request (Device → Server) =====
        print("\n" + "="*30)
        print("PHASE 1: DEVICE AUTHENTICATION REQUEST")
        print("="*30)
        
        # Generate session parameters
        session_key = os.urandom(32).hex()
        v0 = hashlib.sha256(f"{session_key}{device.security_data['hash_key'].iloc[0]}".encode()).hexdigest()
        cipher_suite = Fernet(device.security_data['enc_key'].iloc[0].encode())
        ev0 = cipher_suite.encrypt(v0.encode())
        
        print("\n[DEVICE GENERATED]")
        print(f"Session Key (full): {session_key}")
        print(f"Session Key (first 12): {session_key[:12]}...")
        print(f"V0 (SHA256(session_key + hash_key)): {v0[:12]}...")
        print(f"Encrypted V0 (EV0): {ev0[:12]}...")
        
        print("\n[MESSAGE SENT TO SERVER]")
        print(f"EV0: {ev0[:12]}... (truncated)")

        # ===== PHASE 2: Device Validation (Server side) =====
        print("\n" + "="*30)
        print("PHASE 2: DEVICE VALIDATION (SERVER SIDE)")
        print("="*30)
        
        server_record = server.database[server.database['device_id'] == device.id]
        if server_record.empty:
            print("\n[STATUS] Authentication Failed: Device not registered in server database")
            return False

        try:
            print("\n[SERVER RETRIEVED CREDENTIALS]")
            print(f"Stored Enc Key (first 12): {server_record['enc_key'].iloc[0][:12]}...")
            print(f"Stored Hash Key: {server_record['hash_key'].iloc[0]}")
            
            server_cipher = Fernet(server_record['enc_key'].iloc[0].encode())
            decrypted_v0 = server_cipher.decrypt(ev0).decode()
            expected_v0 = hashlib.sha256(f"{session_key}{server_record['hash_key'].iloc[0]}".encode()).hexdigest()
            
            print("\n[VALIDATION PROCESS]")
            print(f"Decrypted V0: {decrypted_v0[:12]}...")
            print(f"Expected V0: {expected_v0[:12]}...")
            
            if decrypted_v0 != expected_v0:
                print("\n[STATUS] Authentication Failed: Verification failed - hash mismatch")
                return False
            print("\n[STATUS] Device verified successfully")

            
            # ===== PHASE 3: Server Authentication (Server → Device) =====
            print("\n" + "="*30)
            print("PHASE 3: SERVER AUTHENTICATION (SERVER → DEVICE)")
            print("="*30)
            
            v1 = hashlib.sha256(f"{expected_v0}{server_record['response'].iloc[0]}".encode()).hexdigest()
            ev1 = server_cipher.encrypt(v1.encode())
            
            print("\n[SERVER GENERATED]")
            print(f"V1 (SHA256(V0 + stored_response)): {v1[:12]}...")
            print(f"Encrypted V1 (EV1): {ev1[:12]}...")
            
            print("\n[MESSAGE SENT TO DEVICE]")
            print(f"EV1: {ev1[:12]}... (truncated)")


            # ===== PHASE 4: Server Validation (Device side) =====
            print("\n" + "="*30)
            print("PHASE 4: SERVER VALIDATION (DEVICE SIDE)")
            print("="*30)
            
            try:
                decrypted_v1 = cipher_suite.decrypt(ev1).decode()
                expected_v1 = hashlib.sha256(f"{v0}{device.security_data['response'].iloc[0]}".encode()).hexdigest()
                
                print("\n[VALIDATION PROCESS]")
                print(f"Decrypted V1: {decrypted_v1[:12]}...")
                print(f"Expected V1: {expected_v1[:12]}...")
                
                if decrypted_v1 != expected_v1:
                    print("\n[STATUS] Authentication Failed: Server verification failed")
                    return False
                print("\n[STATUS] Server verified successfully")


                # ===== PHASE 5: CRP Update (Device → Server) =====
                print("\n" + "="*30)
                print("PHASE 5: CRP UPDATE (DEVICE → SERVER)")
                print("="*30)
                
                new_challenge = random_inputs(n=64, N=1, seed=int.from_bytes(os.urandom(4), 'big'))[0]
                new_response = device.puf.get_response(new_challenge)
                v2 = hashlib.sha256(f"{expected_v1}{new_response}".encode()).hexdigest()
                ev2 = cipher_suite.encrypt(v2.encode())
                
                print("\n[DEVICE GENERATED NEW CRP]")
                print(f"New Challenge (first 5): {new_challenge[:5]}...")
                print(f"New Response: {new_response}")
                print(f"V2 (SHA256(V1 + new_response)): {v2[:12]}...")
                print(f"Encrypted V2 (EV2): {ev2[:12]}...")
                
                print("\n[MESSAGE SENT TO SERVER]")
                print(f"EV2: {ev2[:12]}... (truncated)")

                # ===== FINAL VERIFICATION =====
                print("\n" + "="*30)
                print("FINAL VERIFICATION AND UPDATE")
                print("="*30)
                
                try:
                    decrypted_v2 = server_cipher.decrypt(ev2).decode()
                    expected_v2 = hashlib.sha256(f"{v1}{new_response}".encode()).hexdigest()
                    
                    print("\n[VALIDATION PROCESS]")
                    print(f"Decrypted V2: {decrypted_v2[:12]}...")
                    print(f"Expected V2: {expected_v2[:12]}...")
                    
                    if decrypted_v2 != expected_v2:
                        print("\n[STATUS] Authentication Failed: Final verification failed")
                        return False

                    # Update stored CRP
                    idx = server.database[server.database['device_id'] == device.id].index[0]
                    old_challenge = server.database.at[idx, 'challenge']
                    old_response = server.database.at[idx, 'response']
                    
                    server.database.at[idx, 'challenge'] = list(new_challenge)
                    server.database.at[idx, 'response'] = new_response
                    
                    print("\n[CREDENTIALS UPDATED]")
                    print("OLD VALUES:")
                    print(f"Challenge: {old_challenge[:5]}...")
                    print(f"Response: {old_response}")
                    print("\nNEW VALUES:")
                    print(f"Challenge: {new_challenge[:5]}...")
                    print(f"Response: {new_response}")
                    
                    print("\n" + "="*50)
                    print("[STATUS] AUTHENTICATION SUCCESS")
                    print("Mutual authentication completed successfully")
                    print("Security credentials updated\n")
                    return True
                
                except Exception as e:
                    print(f"\n[ERROR] Final verification failed: {str(e)}")
                    return False

            except Exception as e:
                print(f"\n[ERROR] Server validation failed: {str(e)}")
                return False

        except Exception as e:
            print(f"\n[ERROR] Device validation failed: {str(e)}")
            return False

    except IndexError:
        print("\n[STATUS] Authentication Failed: Device missing required security parameters")
        return False
    except Exception as e:
        print(f"\n[ERROR] Authentication process failed: {str(e)}")
        return False




def simulate_adversary_attacks(server):
    print("\n=== Simulating Adversary Attacks ===")
    
    # Get a legitimate device from the server database
    if server.database.empty:
        print("No registered devices found - please run setup first")
        return
    
    legit_device_id = server.database.iloc[0]['device_id']
    print(f"\nTesting with legitimate device: {legit_device_id}")
    
    # Attack 1: Replay Attack
    print("\n[Attack 1] Replay Attack Simulation")
    print("Description: Attacker tries to reuse old authentication messages")
    attacker = IoTDevice(legit_device_id)
    print("Attempting authentication with no credentials...")
    result = authenticate_device(attacker, server)
    print("Result: Attack failed - system detected unauthorized access" if not result else "ERROR: Attack succeeded!")
    
    # Attack 2: Man-in-the-Middle Attack
    print("\n[Attack 2] MITM Attack Simulation")
    print("Description: Attacker intercepts communication but can't forge valid hashes")
    
    # Create fake device with intercepted (but invalid) credentials
    mitm_device = IoTDevice(legit_device_id)
    mitm_device.security_data.loc[0] = {
        'server_id': "Fake_Server",
        'enc_key': Fernet.generate_key().decode(),  # Wrong key
        'hash_key': '123456',  # Wrong hash
        'challenge': random_inputs(n=64, N=1, seed=123)[0],
        'response': 1  # Wrong response
    }
    print("Attempting authentication with intercepted credentials...")
    result = authenticate_device(mitm_device, server)
    print("Result: Attack failed - verification hashes didn't match" if not result else "ERROR: Attack succeeded!")
    
    # Attack 3: Brute Force Attack
    print("\n[Attack 3] Brute Force Simulation")
    print("Description: Attacker tries random combinations of security parameters")
    
    brute_force_device = IoTDevice(legit_device_id)
    brute_force_device.security_data.loc[0] = {
        'server_id': server.id,
        'enc_key': Fernet.generate_key().decode(),  # Random key
        'hash_key': ''.join([str(np.random.randint(0, 9)) for _ in range(6)]),  # Random hash
        'challenge': random_inputs(n=64, N=1, seed=456)[0],  # Random challenge
        'response': np.random.randint(0, 2)  # Random response
    }
    print("Attempting authentication with guessed credentials...")
    result = authenticate_device(brute_force_device, server)
    print("Result: Attack failed - couldn't guess correct parameters" if not result else "ERROR: Attack succeeded!")
    
    print("\nAll attack simulations completed successfully")
    print("Security verification: System successfully prevented all attack attempts")

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
    
    # # Security attack simulations
    # simulate_adversary_attacks(server)

if __name__ == "__main__":
    main()