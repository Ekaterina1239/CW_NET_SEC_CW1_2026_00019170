"""E3 (RQ3): does each mode detect a modified packet? -> results/tamper_results.csv"""
import csv
from pathlib import Path

from cryptography.exceptions import InvalidTag

import crypto_modes as cm
from telemetry import make_reading, to_bytes

RESULTS = Path(__file__).resolve().parent.parent / "results"


def flip(data, i, mask):
    b = bytearray(data)
    b[i] ^= mask
    return bytes(b)


def check(mode, name, func):
    try:
        result = func()
        print(f"{mode:8}| {name:24}| NOT detected | {result[:45]}")
        return [mode, name, "NO", result[:45].decode(errors="replace")]
    except (InvalidTag, ValueError) as e:
        print(f"{mode:8}| {name:24}| DETECTED     | {type(e).__name__}")
        return [mode, name, "YES", type(e).__name__]


def main():
    key, wrong_key = cm.new_key(), cm.new_key()
    plain = to_bytes(make_reading(1, 720))          # noon reading
    nonce = cm.make_nonce(1, 42)
    other_header = cm.make_nonce(2, 42)             # attacker relabels the sender
    pos = plain.index(b'"p_w":') + 6                # first digit of the power value
    mask = plain[pos] ^ ord("9")                    # turns that digit into '9'
    rows = []

    c = cm.gcm_encrypt(key, nonce, plain)
    rows.append(check("AES-GCM", "1 bit flipped", lambda: cm.gcm_decrypt(key, nonce, flip(c, 0, 1))))
    rows.append(check("AES-GCM", "power value changed", lambda: cm.gcm_decrypt(key, nonce, flip(c, pos, mask))))
    rows.append(check("AES-GCM", "tag changed", lambda: cm.gcm_decrypt(key, nonce, flip(c, len(c) - 1, 1))))
    rows.append(check("AES-GCM", "header (AAD) changed", lambda: cm.gcm_decrypt(key, other_header, c)))
    rows.append(check("AES-GCM", "wrong key", lambda: cm.gcm_decrypt(wrong_key, nonce, c)))

    c = cm.ctr_encrypt(key, nonce, plain)
    rows.append(check("AES-CTR", "1 bit flipped", lambda: cm.ctr_decrypt(key, nonce, flip(c, 0, 1))))
    rows.append(check("AES-CTR", "power value changed", lambda: cm.ctr_decrypt(key, nonce, flip(c, pos, mask))))
    rows.append(check("AES-CTR", "header changed", lambda: cm.ctr_decrypt(key, other_header, c)))
    rows.append(check("AES-CTR", "wrong key", lambda: cm.ctr_decrypt(wrong_key, nonce, c)))

    c = cm.cbc_encrypt(key, plain)                  # IV (16 B) || ciphertext
    rows.append(check("AES-CBC", "IV changed (device id)", lambda: cm.cbc_decrypt(key, flip(c, 15, plain[15] ^ ord("7")))))
    rows.append(check("AES-CBC", "1 bit flipped", lambda: cm.cbc_decrypt(key, flip(c, 16, 1))))
    rows.append(check("AES-CBC", "wrong key", lambda: cm.cbc_decrypt(wrong_key, c)))

    RESULTS.mkdir(exist_ok=True)
    with open(RESULTS / "tamper_results.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["mode", "tampering", "detected", "outcome"]] + rows)


if __name__ == "__main__":
    main()