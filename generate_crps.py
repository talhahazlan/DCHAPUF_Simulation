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
        # Combine internal state and challenge input, hash them
        state_bytes = self.lfsr_state.to_bytes(8, 'big')
        challenge_bytes = challenge.astype(np.uint8).tobytes()
        
        digest = hashlib.sha256(state_bytes + challenge_bytes).digest()
        hash_bits = np.unpackbits(np.frombuffer(digest, dtype=np.uint8))

        # Use first n bits as XOR mask
        mask = 0
        for i in range(self.n):
            mask = (mask << 1) | hash_bits[i]

        # Use next few bits to generate a simple threshold (0-4)
        threshold = sum(hash_bits[self.n:self.n+4] << np.arange(4)) % 5

        return mask, threshold

class ROPUF:
    def __init__(self, n=64, lfsr_state=None):
        self.freqs = np.random.default_rng(lfsr_state).normal(1e6, 1e4, n)

    def get_response(self, challenge):
        idx = np.where(challenge == 1)[0]
        if len(idx) < 2:
            return 0
        i, j = np.random.choice(idx, 2, replace=False)
        return int(self.freqs[i] > self.freqs[j])

class BRPUF:
    def __init__(self, n=64, lfsr_state=None):
        self.bias = np.random.default_rng(lfsr_state).normal(0, 1, n)

    def get_response(self, challenge):
        return int(np.dot(self.bias, challenge) > 0)

class DCHPUF:
    def __init__(self, n=64, lfsr_state=None):
        self.n = n
        self.controller = DynamicController(n)
        seed = lfsr_state if lfsr_state else int.from_bytes(os.urandom(8), 'big')
        self.arbiter = ArbiterPUF(n=n, seed=seed)
        self.ro = ROPUF(n=n, lfsr_state=seed)
        self.br = BRPUF(n=n, lfsr_state=seed)

    def update_seed(self, new_seed):
        self.controller.lfsr_state = new_seed
        self.arbiter = ArbiterPUF(n=self.n, seed=new_seed)
        self.ro = ROPUF(n=self.n, lfsr_state=new_seed)
        self.br = BRPUF(n=self.n, lfsr_state=new_seed)

    def get_response(self, challenge, debug=False):
        challenge_bin = np.where(challenge == -1, 0, 1)
        mask, threshold = self.controller.get_mask_and_threshold(challenge_bin)

        mask_bits = np.array([(mask >> i) & 1 for i in reversed(range(self.n))], dtype=np.uint8)
        masked = challenge_bin ^ mask_bits
        masked_for_pypuf = np.where(masked == 0, -1, 1)

        arbiter_on = masked.sum() > threshold
        ro_on = self.controller.lfsr_state % 2 == 0
        br_on = not ro_on

        r_arbiter = ((self.arbiter.eval(masked_for_pypuf.reshape(1, -1))[0] + 1) // 2) if arbiter_on else 0
        r_ro = self.ro.get_response(masked) if ro_on else 0
        r_br = self.br.get_response(masked) if br_on else 0

        final_response = r_arbiter ^ r_ro ^ r_br

        if debug:
            print(f"Masked challenge (first 5 bits): {masked[:5]}")
            print(f"Components - Arbiter: {arbiter_on}, RO: {ro_on}, BR: {br_on}")
            print(f"Final response: {final_response}")

        return final_response

def verify_puf_behavior(puf):
    print("\n=== Checking PUF Determinism and Balance ===")

    # Determinism: same input will get same output
    test_chal = random_inputs(n=64, N=1, seed=42)[0]
    resp1 = puf.get_response(test_chal, debug=True)
    resp2 = puf.get_response(test_chal)
    print(f"Determinism check: {resp1 == resp2}")

    # Response balance test (rough idea)
    outputs = []
    for i in range(1000):
        c = random_inputs(n=64, N=1, seed=42 + i)[0]
        outputs.append(puf.get_response(c))
    print("Response distribution:")
    print(pd.Series(outputs).value_counts(normalize=True))

def generate_and_save_crps(filename='crps.csv', num_crps=10000, n=64):
    print("=== Starting CRP Generation ===")
    puf = DCHPUF(n=n)

    # Basic PUF checks before data generation
    verify_puf_behavior(puf)

    # Create challenges and get responses
    challenges = random_inputs(n=n, N=num_crps, seed=42)
    responses = np.array([puf.get_response(c) for c in challenges])

    # Convert -1/+1 to 0/1
    challenges_binary = np.where(challenges == -1, 0, 1)

    # Create DataFrame
    col_names = [f'bit_{i}' for i in range(n)]
    df = pd.DataFrame(challenges_binary, columns=col_names)
    df['response'] = responses

    print("\n=== Sample CRPs ===")
    print(df.head(3))
    print("\nDistribution of responses:")
    print(df['response'].value_counts(normalize=True))

    df.to_csv(filename, index=False)
    print(f"CRPs saved to {filename}")

if __name__ == "__main__":
    generate_and_save_crps(num_crps=10000)
