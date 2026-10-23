# src/modes.py
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from keys import NonceRegistry

registry = NonceRegistry()

def gcm_encrypt(key, plaintext, key_id, associated_data=b""):
    nonce = registry.fresh_nonce(key_id, ___)     
    aesgcm = AESGCM(___)                          
    ct = aesgcm.encrypt(___, ___, ___)            
    return nonce, ct                              

def gcm_decrypt(key, nonce, ct, associated_data=b""):
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(___, ___, ___)         