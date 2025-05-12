import numpy as np
import pandas as pd
from pypuf.simulation import ArbiterPUF
from pypuf.io import random_inputs

class DynamicController:
    def __init__(self, seed=0xDEADBEEF, n=64):
        self.seed = seed
        self.n = n
        self.lfsr_state = seed

    def lfsr_step(self):
        feedback = (self.lfsr_state >> 0) ^ (self.lfsr_state >> 1) ^ (self.lfsr_state >> 3) ^ (self.lfsr_state >> 4)
        self.lfsr_state = (self.lfsr_state >> 1) | ((feedback & 1) << 63)

    def get_mask(self):
        mask = 0
        for _ in range(self.n):
            mask = (mask << 1) | (self.lfsr_state & 1)
            self.lfsr_step()
        return mask

    def dynamic_threshold(self):
        return (self.lfsr_state & 0b1111) % 5

class ROPUF:
    def __init__(self, n=64):
        np.random.seed(42)  # Fixed seed for reproducibility
        self.freqs = np.random.normal(1e6, 1e4, n)

    def get_response(self, challenge):
        idx = np.where(challenge == 1)[0]
        if len(idx) < 2: return 0
        i, j = np.random.choice(idx, 2, replace=False)
        return 1 if self.freqs[i] > self.freqs[j] else 0

class BRPUF:
    def __init__(self, n=64):
        np.random.seed(42)  # Fixed seed for reproducibility
        self.bias = np.random.normal(0, 1, n)

    def get_response(self, challenge):
        return 1 if np.dot(self.bias, challenge) > 0 else 0

class DCHPUF:
    def __init__(self, n=64):
        self.n = n
        self.controller = DynamicController(n=n)
        self.arbiter = ArbiterPUF(n=n, seed=42)
        self.ro = ROPUF(n=n)
        self.br = BRPUF(n=n)

    def get_response(self, challenge, debug=False):
        challenge_binary = np.where(challenge == -1, 0, 1)
        mask = self.controller.get_mask()
        mask_bits = np.array([(mask >> i) & 1 for i in reversed(range(self.n))], dtype=np.uint8)
        masked_challenge = challenge_binary ^ mask_bits
        masked_challenge_pypuf = np.where(masked_challenge == 0, -1, 1)
        
        threshold = self.controller.dynamic_threshold()
        arbiter_active = (masked_challenge.sum() > threshold)
        ro_active = (masked_challenge.sum() % 2 == 0)
        br_active = not ro_active

        # Convert all responses to 0/1 format before XOR
        r_arbiter = (self.arbiter.eval(masked_challenge_pypuf.reshape(1, -1))[0] + 1) // 2
        r_ro = self.ro.get_response(masked_challenge)
        r_br = self.br.get_response(masked_challenge)
        response = r_arbiter ^ r_ro ^ r_br

        if debug:
            print(f"\nChallenge: {challenge[:5]}... (first 5 bits)")
            print(f"Mask: {mask:064b}"[:20]+"...")
            print(f"Threshold: {threshold}")
            print(f"Arbiter: {r_arbiter}, RO: {r_ro}, BR: {r_br}")
            print(f"Final Response: {response}")
            

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