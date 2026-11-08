"""
  AES-GCM     : confidentiality + integrity (AEAD)        - mandatory mode
  AES-CTR     : confidentiality only                      - second mode
  AES-CBC     : confidentiality only, PKCS#7, random IV   - third mode
  AES-GCM-SIV : AEAD that tolerates nonce reuse (RFC 8452) - countermeasure
"""
import os
import struct

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, AESGCMSIV


def new_key():
    """256-bit key from the operating system's CSPRNG."""
    return AESGCM.generate_key(bit_length=256)


def make_nonce(device_id, counter):
    """96-bit nonce = 4-byte device id || 8-byte message counter."""
    return struct.pack(">IQ", device_id, counter)


# ---- AES-GCM (the header = nonce is also passed as AAD)
def gcm_encrypt(key, nonce, plaintext):
    return AESGCM(key).encrypt(nonce, plaintext, nonce)        # ciphertext || 16-byte tag


def gcm_decrypt(key, nonce, data):
    return AESGCM(key).decrypt(nonce, data, nonce)             # raises InvalidTag if changed


# ---- AES-CTR (16-byte start block = nonce || 4-byte block counter)
def ctr_encrypt(key, nonce, plaintext):
    enc = Cipher(algorithms.AES(key), modes.CTR(nonce + b"\x00" * 4)).encryptor()
    return enc.update(plaintext) + enc.finalize()


def ctr_decrypt(key, nonce, data):
    dec = Cipher(algorithms.AES(key), modes.CTR(nonce + b"\x00" * 4)).decryptor()
    return dec.update(data) + dec.finalize()                   # never raises: no integrity


# ---- AES-CBC (fresh random IV per message, PKCS#7 padding)
def cbc_encrypt(key, plaintext):
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    enc = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    return iv + enc.update(padded) + enc.finalize()


def cbc_decrypt(key, data):
    iv, ct = data[:16], data[16:]
    dec = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = dec.update(ct) + dec.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()       # ValueError if padding broken


# ---- AES-GCM-SIV (countermeasure against nonce reuse)
def siv_encrypt(key, nonce, plaintext):
    return AESGCMSIV(key).encrypt(nonce, plaintext, nonce)


def siv_decrypt(key, nonce, data):
    return AESGCMSIV(key).decrypt(nonce, data, nonce)