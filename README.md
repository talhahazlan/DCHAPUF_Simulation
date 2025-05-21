# DCHA-PUF: Dynamic Controlled Hybrid Arbiter PUF Authentication Framework

This project implements a lightweight, reconfigurable authentication framework for IoT devices using a custom PUF design called the DCHA-PUF (Dynamic Controlled Hybrid Arbiter PUF). It demonstrates both the PUF simulation and a secure mutual authentication protocol between an IoT device and a server using Python.

## Key Features

- Simulates a hybrid PUF combining Arbiter, Ring Oscillator (RO), and Bistable Ring (BR) PUFs with dynamic entropy
- Implements a mutual authentication protocol with PUF-derived session keys
- Evaluates resilience against machine learning attacks: logistic regression, weak and strong artificial neural networks (ANNs)
- Stores device, server, and CRP data in CSV format for traceability
- Visualizes attack performance using Matplotlib


## Requirements

- Python 3.8 (preferred since PyPUF does not support latest version of Python for now) 

## Project Structure

```text
hybrid_PUF/
├── ml_attacks/                         # Machine learning-based attack simulations
│   ├── base_attack.py                 # Common functions for attack models
│   ├── weak_attack.py                 # Basic ANN attack
│   ├── medium_attack.py               # Intermediate ANN attack
│   ├── strong_attack.py               # Deep ANN attack
│   ├── extreme_attack.py              # Aggressive ANN attack
│   └── run_attack.py                  # Combined attack execution script
    └── lr_attack.py                   # Logistic Regression attack
│
├── protocol/                           # Authentication protocol modules
│   ├── auth_setup.py                  # IoT device registration and setup
│   ├── auth_protocol.py               # Mutual authentication logic
│   └── auth_attacks.py                # Adversary attack simulation (MITM, replay, brute-force)
│
├── generate_crps.py                   # Generates CRPs using DCHA-PUF simulation
├── crps.csv                           # Generated challenge-response pairs
├── server_database.csv                # Server-stored device registration data
├── README.md                          # Project documentation
```

### How to Run the Simulation

1. **Clone Project:**

```bash
git clone https://github.com/talhahazlan/DCHAPUF_Simulation.git

```

2. **Install required libraries:**

```bash
pip install numpy pandas matplotlib scikit-learn cryptography tensorflow
```


3. **Generate Challenge–Response Pairs:**

```bash
python3.8 generate_crps.py 
```
- Generate crps.csv file that would be use throughout the simulation

4. **Register IoT Devices and Server:**

```bash
python3.8 auth_setup.py
```

- Simulates the secure registration phase
- Creates device-specific PUFs, generates keys and CRPs
- Outputs:
    - device records to device_data/
    - server records to server_database.csv

5. **Run the Mutual Authentication Protocol:**

```bash
python3.8 auth_protocol.py

```

- Simulates the challenge–response exchange between a device and the server
- Includes encrypted message verification using PUF-derived keys

6. **Simulate Adversarial Attacks:**

```bash
python3.8 ml_attacks/weak_attack.py

```

- Simulates the challenge–response exchange between a device and the server
- Includes encrypted message verification using PUF-derived keys

**Ahmad Talhah bin Mohd Azlan. "DCHA-PUF: A Dynamic Controlled Hybrid Arbiter PUF Authentication Framework for IoT Systems." University of Sheffield, 2025**


