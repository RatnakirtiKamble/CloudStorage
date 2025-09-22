# gateway/utils/crypto.py
import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# AES-GCM helper (CPU) — secure encryption used to store final data
def aes_gcm_encrypt(key: bytes, plaintext: bytes):
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    tag = encryptor.tag
    sha = hashlib.sha256(ciphertext).hexdigest()
    return {"ciphertext": ciphertext, "iv": iv, "tag": tag, "sha256": sha}

def aes_gcm_decrypt(key: bytes, iv: bytes, tag: bytes, ciphertext: bytes):
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()

# File-key wrap/unwarp with server HSM/root key (demo)
# In your real flow, replace these with local_hsm.encrypt_master_key and decrypt_master_key
ROOT_WRAP_KEY = os.environ.get("ROOT_WRAP_KEY")
if ROOT_WRAP_KEY:
    ROOT_WRAP_KEY = base64.b64decode(ROOT_WRAP_KEY)
else:
    # for dev only: generate ephemeral root key (not for production)
    ROOT_WRAP_KEY = os.urandom(32)

def wrap_file_key_with_root(file_key: bytes) -> bytes:
    # AES-GCM wrap with server root key -> store ciphertext
    return aes_gcm_encrypt(ROOT_WRAP_KEY, file_key)["ciphertext"]

def unwrap_file_key_with_root(ciphertext: bytes, iv: bytes, tag: bytes) -> bytes:
    return aes_gcm_decrypt(ROOT_WRAP_KEY, iv, tag, ciphertext)
