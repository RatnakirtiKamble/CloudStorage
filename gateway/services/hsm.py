import os
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from base64 import b64encode, b64decode
from config import Settings

ROOT_KEY = bytes.fromhex(Settings().ROOT_KEY)
HSM_FILE = "hsm_keys.json"  # encrypted storage of HSM keys


class LocalHSM:
    def __init__(self, hsm_file=HSM_FILE):
        self.hsm_file = hsm_file
        self.keys = {}  # in-memory cache {kms_key_id: key_bytes}
        self._load_keys()

    def _load_keys(self):
        """Load HSM keys from encrypted disk"""
        if not os.path.exists(self.hsm_file):
            return
        with open(self.hsm_file, "rb") as f:
            data = f.read()
        iv = data[:16]
        ciphertext = data[16:]
        cipher = Cipher(algorithms.AES(ROOT_KEY), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        raw = unpadder.update(padded) + unpadder.finalize()
        self.keys = {k: b64decode(v) for k, v in json.loads(raw).items()}

    def _save_keys(self):
        """Save HSM keys to encrypted disk"""
        raw = json.dumps({k: b64encode(v).decode() for k, v in self.keys.items()}).encode()
        padder = padding.PKCS7(128).padder()
        padded = padder.update(raw) + padder.finalize()
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(ROOT_KEY), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()
        with open(self.hsm_file, "wb") as f:
            f.write(iv + ciphertext)

    def generate_hsm_key(self, kms_key_id: str):
        """Generate a new HSM key (32 bytes)"""
        if kms_key_id in self.keys:
            raise ValueError("Key already exists")
        key = os.urandom(32)
        self.keys[kms_key_id] = key
        self._save_keys()
        return kms_key_id

    def encrypt_master_key(self, master_key: bytes, kms_key_id: str) -> bytes:
        """Encrypt user master key using HSM key (AES-GCM)"""
        if kms_key_id not in self.keys:
            raise ValueError("Invalid KMS key ID")
        hsm_key = self.keys[kms_key_id]
        iv = os.urandom(12)
        cipher = Cipher(algorithms.AES(hsm_key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(master_key) + encryptor.finalize()
        tag = encryptor.tag
        return iv + tag + ciphertext

    def decrypt_master_key(self, encrypted_master_key: bytes, kms_key_id: str) -> bytes:
        """Decrypt user master key using HSM key (AES-GCM)"""
        if kms_key_id not in self.keys:
            raise ValueError("Invalid KMS key ID")
        hsm_key = self.keys[kms_key_id]
        iv = encrypted_master_key[:12]
        tag = encrypted_master_key[12:28]
        ciphertext = encrypted_master_key[28:]
        cipher = Cipher(algorithms.AES(hsm_key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext


# Singleton instance
local_hsm = LocalHSM()
