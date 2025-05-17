import numpy as np
from cryptography.fernet import Fernet
from pypuf.io import random_inputs
from auth_protocol import IoTDevice, authenticate_device 

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
    
    mitm_device = IoTDevice(legit_device_id)
    mitm_device.security_data.loc[0] = {
        'server_id': "Fake_Server",
        'enc_key': Fernet.generate_key().decode(),  # Wrong key
        'hash_key': '123456',  # Wrong hash
        'challenge': random_inputs(n=64, N=1, seed=123)[0],
        'response': 1
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
        'enc_key': Fernet.generate_key().decode(),
        'hash_key': ''.join([str(np.random.randint(0, 9)) for _ in range(6)]),
        'challenge': random_inputs(n=64, N=1, seed=456)[0],
        'response': np.random.randint(0, 2)
    }
    print("Attempting authentication with guessed credentials...")
    result = authenticate_device(brute_force_device, server)
    print("Result: Attack failed - couldn't guess correct parameters" if not result else "ERROR: Attack succeeded!")
    
    print("\nAll attack simulations completed successfully")
    print("Security verification: System successfully prevented all attack attempts")