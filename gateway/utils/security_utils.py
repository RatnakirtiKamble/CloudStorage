from passlib.context import CryptContext
import os
from Crypto.Cipher import AES
from config import Settings
from hashlib import sha256

ROOT_KEY = sha256(Settings().ROOT_KEY.encode()).digest()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# -----------------------------
# Master key encryption utility
# -----------------------------
def encrypt_master_key_with_local_key(user_master_key: bytes) -> bytes:
    """
    Encrypts the user's master key using the app's root key.
    Returns: iv + tag + ciphertext
    """
    iv = os.urandom(12)  # GCM nonce
    cipher = AES.new(ROOT_KEY, AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(user_master_key)
    return iv + tag + ciphertext