import numpy as np
import random
import csv
from pypuf.simulation import ArbiterPUF, BistableRingPUF

class LFSR:
    def __init__(self, size, taps):
        self.size = size
        self.state = np.random.choice([-1, 1], size=size)
        self.taps = taps

    def shift(self, input_bit):
        feedback = np.prod(self.state[self.taps])
        new_state = np.roll(self.state, -1)
        new_state[-1] = input_bit * feedback
        self.state = new_state
        return new_state

class RingOscillatorPUF:
    def __init__(self, num_osc=8):
        self.m = num_osc
        self.frequencies = [random.uniform(1.0, 2.0) for _ in range(num_osc)]

    def get_response(self, challenge_bin):
        # Convert -1/+1 challenge to 0/1 int
        chal_int = int(''.join(['1' if b == 1 else '0' for b in challenge_bin]), 2)
        idx1 = chal_int & 0x7
        idx2 = (chal_int >> 3) & 0x7
        if idx1 == idx2:
            idx2 = (idx2 + 1) % self.m
        return 1 if self.frequencies[idx1] > self.frequencies[idx2] else 0

class HybridCTPUF:
    def __init__(self, lfsr_size=128, taps=[1, 3, 5, 8, 13, 21, 55]):
        self.arbiter_mask = ArbiterPUF(n=64, seed=1)
        self.arbiter_main = ArbiterPUF(n=64, seed=2)
        self.ro_puf1 = RingOscillatorPUF()
        self.ro_puf2 = RingOscillatorPUF()
        self.br_puf1 = BistableRingPUF(n=64, weights=np.random.randn(65))
        self.br_puf2 = BistableRingPUF(n=64, weights=np.random.randn(65))
        self.lfsr = LFSR(size=lfsr_size, taps=taps)
        self.config = np.random.choice([-1, 1], size=64)

    def get_response(self, challenge):
        # Apply config from LFSR to challenge
        adjusted_challenge = challenge * self.config
        R_mask = 1 if self.arbiter_mask.eval(adjusted_challenge.reshape(1, -1))[0] > 0 else 0
        C_effective = -adjusted_challenge if R_mask == 1 else adjusted_challenge

        # Mode Selection (parity-based)
        even_parity = np.sum(C_effective[0::2])
        odd_parity = np.sum(C_effective[1::2])
        mode = 'arbiter' if odd_parity == 0 else 'ro' if even_parity % 2 == 0 and odd_parity % 2 == 1 else 'br'

        if mode == 'arbiter':
            R_main = 1 if self.arbiter_main.eval(C_effective.reshape(1, -1))[0] > 0 else 0
        elif mode == 'ro':
            r1 = self.ro_puf1.get_response(C_effective)
            r2 = self.ro_puf2.get_response(C_effective)
            R_main = r1 ^ r2
        else:
            b1 = 1 if self.br_puf1.eval(C_effective.reshape(1, -1))[0] > 0 else 0
            b2 = 1 if self.br_puf2.eval(C_effective.reshape(1, -1))[0] > 0 else 0
            R_main = b1 ^ b2

        response = R_main ^ R_mask

        # Update config using LFSR
        new_state = self.lfsr.shift(1 if response == 1 else -1)
        self.config = new_state[:64]

        return response

    def generate_crps(self, num_crps):
        challenges = np.random.choice([-1, 1], size=(num_crps, 64))
        responses = np.array([self.get_response(chal) for chal in challenges])
        return challenges, responses

if __name__ == "__main__":
    model = HybridCTPUF()
    num_crps = 10000
    challenges, responses = model.generate_crps(num_crps)

    # Save to CSV
    with open("crps.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["challenge", "response"])
        for chal, resp in zip(challenges, responses):
            chal_bin = ''.join(['1' if b == 1 else '0' for b in chal])
            writer.writerow([chal_bin, resp])

    print(f"\n✅ {num_crps} CRPs saved to 'crps_hybrid_ct_pypuf.csv'")
