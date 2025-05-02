# Hybrid LFSR + Configurable Tristate PUF (CT-PUF) with Machine Learning Attack Evaluation

This project presents a hybrid hardware security architecture combining a Linear Feedback Shift Register (LFSR) with a Configurable Tristate Physically Unclonable Function (CT-PUF). The design aims to improve unpredictability and resilience against machine learning (ML) attacks using Logistic Regression and Artificial Neural Networks (ANN).

## Project Overview

The system includes:

- **HybridCTPUF Model**: A software simulation of an advanced PUF integrating Arbiter, Ring Oscillator (RO), and Bistable Ring (BR) PUF modules.
- **Dynamic LFSR Input**: Generates unpredictable challenges for each authentication round.
- **Challenge-Response Pair Generation**: Produces CRPs to simulate device authentication behavior.
- **ML Attack Evaluation**: Uses Logistic Regression and ANN to test the model’s resistance against modeling attacks.

---

## How to Use

### 1. Generate CRPs
Run the hybrid PUF simulation to create a dataset of 10,000 challenge-response pairs:

```bash
python hybrid_ct_puf.py



