import pandas as pd
import secrets
from generate_crps import DCHPUF
from pypuf.io import random_inputs
import numpy as np

# Configuration
device_id = "Device_TALHAH01"
server_id = "Demo_Server"
puf_seed = 1234  # Just for tracking in simulation
challenge_size = 64

# Generate one challenge using seed
challenge = random_inputs(n=challenge_size, N=1, seed=42)[0]

# Convert challenge to binary {0,1}
challenge_binary = np.where(challenge == -1, 0, 1)
challenge_str = ''.join(map(str, challenge_binary))  # Store as clean string

# Simulate PUF response using DCHPUF
puf = DCHPUF(n=challenge_size)
response = puf.get_response(challenge)

# Generate encryption key and hash key (simulated)
encryption_key = secrets.token_urlsafe(32)
hash_key = secrets.randbelow(10**8)

# Server-side storage
server_entry = pd.DataFrame([{
    "DeviceID": device_id,
    "HashKey": hash_key,
    "EncKey": encryption_key,
    "Challenge": challenge_str,
    "Response": response
}])
server_entry.to_csv("data/server_database.csv", index=False)

# Device-side storage
device_entry = pd.DataFrame([{
    "DeviceID": device_id,
    "ServerID": server_id,
    "PUF_Seed": puf_seed,
    "EncKey": encryption_key,
    "HashKey": hash_key
}])
device_entry.to_csv("data/device_database.csv", index=False)

print("Setup Phase Complete: CSV files generated in the data folder for server and device database.")
