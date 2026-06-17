#!/usr/bin/env python3

# ------------------------------------------------------------------
# cuda_check.py
# Diagnostics: Python / PyTorch versions and CUDA availability/devices
# ------------------------------------------------------------------

import torch
import subprocess
import sys

print("=== CUDA DIAGNOSTICS ===")

# Python
print(f"Python version        : {sys.version}")

# PyTorch view
print(f"torch version        : {torch.__version__}")
print(f"torch.cuda.is_available: {torch.cuda.is_available()}")
print(f"torch CUDA runtime   : {torch.version.cuda}")

if torch.cuda.is_available():
    print(f"CUDA device count    : {torch.cuda.device_count()}")
    print(f"CUDA device name     : {torch.cuda.get_device_name(0)}")
else:
    print("CUDA not available to PyTorch")

# Driver view (host)
try:
    smi = subprocess.check_output(["nvidia-smi"], stderr=subprocess.STDOUT).decode()
    print("\n--- nvidia-smi ---")
    print(smi)
except Exception as e:
    print("nvidia-smi not available:", e)

torch.cuda.init()
print("CUDA init OK")

print("=== END CUDA DIAGNOSTICS ===")
