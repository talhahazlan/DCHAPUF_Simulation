import numpy as np
import os
import hashlib
import pandas as pd
from pypuf.simulation import ArbiterPUF
from pypuf.io import random_inputs

class DynamicController:
    def __init__(self, n=64, initial_state=None):
        self.n = n
        self.lfsr_state = initial_state if initial_state else int.from_bytes(os.urandom(8), 'big')

    def get_mask_and_threshold(self, challenge):
        # Convert state and challenge to bytes for hashing
        state_bytes = self.lfsr_state.to_bytes(8, 'big')
        challenge_bytes = challenge.astype(np.uint8).tobytes()
        
        # Create SHA-256 hash of state + challenge
        h = hashlib.sha256()
        h.update(state_bytes + challenge_bytes)
        digest = h.digest()
        
        # Convert hash to bit array
        hash_bits = np.unpackbits(np.frombuffer(digest, dtype=np.uint8))
        
        # Generate mask from first n bits
        mask = 0
        for i in range(self.n):
            mask = (mask << 1) | hash_bits[i]
            
        # Generate threshold from next 4 bits
        threshold = sum(hash_bits[self.n:self.n+4] << np.arange(4)) % 5
        
        return mask, threshold

class ROPUF:
    def __init__(self, n=64, lfsr_state=None):
        self.freqs = np.random.default_rng(lfsr_state).normal(1e6, 1e4, n)

    def get_response(self, challenge):
        idx = np.where(challenge == 1)[0]
        if len(idx) < 2: return 0
        i, j = np.random.choice(idx, 2, replace=False)
        return 1 if self.freqs[i] > self.freqs[j] else 0

class BRPUF:
    def __init__(self, n=64, lfsr_state=None):
        self.bias = np.random.default_rng(lfsr_state).normal(0, 1, n)

    def get_response(self, challenge):
        return 1 if np.dot(self.bias, challenge) > 0 else 0

class DCHPUF:
    def __init__(self, n=64, lfsr_state=None):
        self.n = n
        self.controller = DynamicController(n=n)
        seed = lfsr_state if lfsr_state is not None else int.from_bytes(os.urandom(8), 'big')
        self.arbiter = ArbiterPUF(n=n, seed=seed)
        self.ro = ROPUF(n=n, lfsr_state=seed)
        self.br = BRPUF(n=n, lfsr_state=seed)

    def update_seed(self, new_seed: int):
        """Persist LFSR state across sessions"""
        self.controller.lfsr_state = new_seed
        self.arbiter = ArbiterPUF(n=self.n, seed=new_seed)
        self.ro = ROPUF(n=self.n, lfsr_state=new_seed)
        self.br = BRPUF(n=self.n, lfsr_state=new_seed)

    def get_response(self, challenge, debug=False):
        challenge_binary = np.where(challenge == -1, 0, 1)
        mask, threshold = self.controller.get_mask_and_threshold(challenge_binary) 
        mask_bits = np.array([(mask >> i) & 1 for i in reversed(range(self.n))], dtype=np.uint8)
        masked_challenge = challenge_binary ^ mask_bits
        masked_challenge_pypuf = np.where(masked_challenge == 0, -1, 1)

        arbiter_active = (masked_challenge.sum() > threshold)
        ro_active = (self.controller.lfsr_state % 2 == 0)
        br_active = not ro_active

        r_arbiter = (self.arbiter.eval(masked_challenge_pypuf.reshape(1, -1))[0] + 1) // 2 if arbiter_active else 0
        r_ro = self.ro.get_response(masked_challenge) if ro_active else 0
        r_br = self.br.get_response(masked_challenge) if br_active else 0

        response = r_arbiter ^ r_ro ^ r_br

        if debug:
            print(f"Masked challenge: {masked_challenge[:5]}...")
            print(f"Arbiter active: {arbiter_active}, RO active: {ro_active}, BR active: {br_active}")
            print(f"Response: {response}")

        return response

def verify_puf_behavior(puf):
    """Verify basic PUF properties"""
    print("\n=== PUF Verification ===")
    
    # Test determinism with fixed seed
    test_challenge = random_inputs(n=64, N=1, seed=42)[0]
    response1 = puf.get_response(test_challenge, debug=True)
    response2 = puf.get_response(test_challenge)
    print(f"Consistency Check: {response1 == response2} (should be True)")
    
    # Test response distribution with fixed seed
    responses = []
    for _ in range(1000):
        c = random_inputs(n=64, N=1, seed=42+_)[0]  # Different seed for each
        responses.append(puf.get_response(c))
    print(f"Response Distribution:\n{pd.Series(responses).value_counts(normalize=True)}")

def generate_and_save_crps(filename='crps.csv', num_crps=10000, n=64):
    """Generate and save CRPs with verification"""
    print("=== Generating CRPs ===")
    dch_puf = DCHPUF(n=n)
    
    # Verify PUF behavior first
    verify_puf_behavior(dch_puf)
    
    # Generate challenges with fixed seed for reproducibility
    challenges = random_inputs(n=n, N=num_crps, seed=42)
    responses = np.array([dch_puf.get_response(c) for c in challenges])
    
    # Convert challenges to binary (0,1)
    challenges_binary = np.where(challenges == -1, 0, 1)
    
    # Create DataFrame
    challenge_columns = [f'bit_{i}' for i in range(n)]
    df = pd.DataFrame(challenges_binary, columns=challenge_columns)
    df['response'] = responses
    
    # Verify CRP quality
    print("\n=== CRP Verification ===")
    print(f"Generated {len(df)} CRPs")
    print("Sample CRPs:")
    print(df.head(3))
    print("\nResponse distribution:")
    print(df['response'].value_counts(normalize=True))
    
    # Save to CSV
    df.to_csv(filename, index=False)
    print(f"\nSuccessfully saved CRPs to {filename}")

if __name__ == "__main__":
    generate_and_save_crps(num_crps=10000)