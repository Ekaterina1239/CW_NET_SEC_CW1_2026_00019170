"""Probability that random 96-bit nonces collide (birthday bound).
p ~= n^2 / 2^(b+1)   for n messages and b-bit nonces (valid while p is small).
NIST SP 800-38D also limits random 96-bit nonces to 2^32 messages per key.
"""
import blackout_sim as bs

BITS = 96
NIST_LIMIT = 2 ** 32


def collision_probability(n, bits=BITS):
    return n * (n - 1) / 2 / 2 ** bits


def main():
    n = bs.YEARS * 365 * bs.MSG_PER_DAY                  # messages in 20 years
    lines = [
        f"messages per key over {bs.YEARS} years : {n:,}",
        f"collision probability (birthday bound): {collision_probability(n):.2e}",
        f"NIST SP 800-38D limit (random nonces) : {NIST_LIMIT:,} messages per key",
        f"share of the NIST limit used          : {100 * n / NIST_LIMIT:.3f} %",
        f"messages for a 1-in-a-billion risk    : {int((2 * 2 ** BITS * 1e-9) ** 0.5):,}",
    ]
    print("\n".join(lines))
    (bs.RESULTS / "nonce_collision.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()