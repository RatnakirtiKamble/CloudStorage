# worker/utils/crypto.py
import os
import hashlib
import base64

# CPU AES wrappers (same as gateway)
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def aes_gcm_encrypt(key: bytes, plaintext: bytes):
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    return {"ciphertext": ciphertext, "iv": iv, "tag": encryptor.tag, "sha256": hashlib_sha(ciphertext)}

def hashlib_sha(b: bytes):
    import hashlib
    return hashlib.sha256(b).hexdigest()

# GPU transform using PyTorch (actual GPU compute)
try:
    import torch
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False

def gpu_transform(plaintext: bytes, key_like: bytes = None):
    """
    Real GPU work: copy plaintext to GPU, XOR with a key-like stream (fast vector op), copy back.
    This is actual CUDA computation (requires PyTorch with CUDA).
    """
    if not TORCH_AVAILABLE or not torch.cuda.is_available():
        raise RuntimeError("PyTorch CUDA not available")
    arr = torch.frombuffer(plaintext, dtype=torch.uint8).to("cuda")
    if key_like:
        # repeat key_like bytes into a tensor on CUDA
        rep = (len(plaintext) // len(key_like)) + 1
        key_stream = (key_like * rep)[:len(plaintext)]
        kb = torch.frombuffer(key_stream, dtype=torch.uint8).to("cuda")
    else:
        kb = torch.randint(0, 256, arr.shape, dtype=torch.uint8, device="cuda")
    transformed = arr ^ kb  # elementwise xor on GPU
    out = transformed.to("cpu").numpy().tobytes()
    return out
