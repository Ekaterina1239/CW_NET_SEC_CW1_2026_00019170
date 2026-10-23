# src/keys.py
import secrets

def generate_key(bits=256):
    if bits not in (___, ___, ___):          
        raise ValueError("bad key size")
    return secrets.token_bytes(bits // ___)  

class NonceRegistry:
    def __init__(self):
        self.used = ___                      

    def fresh_nonce(self, key_id, size=12):
        used = self.used.setdefault(key_id, ___)   
        while True:
            nonce = secrets.token_bytes(___)      
            if nonce not in used:
                used.add(nonce)
                return nonce

    def register(self, key_id, nonce):
        used = self.used.setdefault(key_id, set())
        if nonce ___ used:                   
            raise ValueError("nonce reuse")
        used.add(nonce)