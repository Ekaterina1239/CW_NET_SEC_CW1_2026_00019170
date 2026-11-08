from pathlib import Path

import crypto_modes as cm
from telemetry import make_reading, to_bytes

RESULTS = Path(__file__).resolve().parent.parent / "results"
ENCRYPT = {
    "AES-CTR": lambda k, n, p: cm.ctr_encrypt(k, n, p),
    "AES-GCM": lambda k, n, p: cm.gcm_encrypt(k, n, p)[:-16],       # attack uses ciphertext only
    "AES-GCM-SIV": lambda k, n, p: cm.siv_encrypt(k, n, p)[:-16],
}


def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def attack(mode):
    key = cm.new_key()                      # the attacker never sees the key
    counter = 0                             # RAM-only counter (the vulnerable design)

    p1 = to_bytes(make_reading(1, 6 * 60))  # day 1, 06:00, power 0 W
    n1 = cm.make_nonce(1, counter)
    c1 = ENCRYPT[mode](key, n1, p1)
    counter += 1

    counter = 0                             # POWER OUTAGE: RAM wiped

    p2 = to_bytes(make_reading(1, 12 * 60)) # day 2, 12:00
    n2 = cm.make_nonce(1, counter)
    c2 = ENCRYPT[mode](key, n2, p2)

    recovered = xor(c2, xor(c1, p1))        # keystream from (C1, P1), applied to C2
    n = min(len(p1), len(p2))
    success = recovered[:n] == p2[:n]
    return [
        f"--- {mode} ---",
        f"nonce day 1 : {n1.hex()}",
        f"nonce day 2 : {n2.hex()}  ({'SAME' if n1 == n2 else 'different'})",
        f"real        : {p2.decode()}",
        f"recovered   : {recovered[:n].decode(errors='replace')}",
        f"attack successful: {success}",
        "",
    ]


def main():
    lines = []
    for mode in ENCRYPT:
        lines += attack(mode)
    print("\n".join(lines))
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "nonce_reuse_demo.txt").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()