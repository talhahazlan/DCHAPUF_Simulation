import numpy as np
import pandas as pd
from cryptography.fernet import Fernet
from pypuf.io import random_inputs
from auth_protocol import IoTDevice, authenticate_device, AuthenticationServer
import ast

def load_server_database(csv_path="server_database.csv"):
    if not Path(csv_path).exists():
        print(f"[!] Server database file not found: {csv_path}")
        return None

    df = pd.read_csv(csv_path, converters={"challenge": ast.literal_eval})
    server = AuthenticationServer()
    server.database = df
    print(f"[✓] Loaded server database with {len(df)} devices.")
    return server



def simulate_adversary_attacks(server):
    print("\n=== Simulating Adversary Attacks ===")

    if server.database.empty:
        print("[!] No registered devices found. Check server database.")
        return

    legit_device_id = server.database.iloc[0]['device_id']
    print(f"[+] Testing with device ID: {legit_device_id}")

    # === Replay Attack ===
    print("\n[Attack 1] Replay Attack")
    attacker = IoTDevice(legit_device_id)  # No security data loaded
    result = authenticate_device(attacker, server)
    print("Result:", "✅ Attack Blocked" if not result else "❌ ERROR: Attack Succeeded")

    # === MITM Attack ===
    print("\n[Attack 2] Man-in-the-Middle (MITM) Attack")
    mitm = IoTDevice(legit_device_id)
    mitm.security_data.loc[0] = {
        'server_id': "Fake_Server",
        'enc_key': Fernet.generate_key().decode(),
        'hash_key': '123456',
        'challenge': random_inputs(n=64, N=1, seed=123)[0],
        'response': 1
    }
    result = authenticate_device(mitm, server)
    print("Result:", "✅ Attack Blocked" if not result else "❌ ERROR: Attack Succeeded")

    # === Brute Force Attack ===
    print("\n[Attack 3] Brute Force Attack")
    brute = IoTDevice(legit_device_id)
    brute.security_data.loc[0] = {
        'server_id': server.id,
        'enc_key': Fernet.generate_key().decode(),
        'hash_key': ''.join(str(np.random.randint(10)) for _ in range(6)),
        'challenge': random_inputs(n=64, N=1, seed=456)[0],
        'response': np.random.randint(0, 2)
    }
    result = authenticate_device(brute, server)
    print("Result:", "✅ Attack Blocked" if not result else "❌ ERROR: Attack Succeeded")

    print("\n[✓] All simulated attacks completed.")


if __name__ == "__main__":
    from pathlib import Path

    print("=== AUTHENTICATION ATTACK TEST (FROM SAVED DATABASE) ===")
    server = load_server_database("server_database.csv")
    if server:
        simulate_adversary_attacks(server)
