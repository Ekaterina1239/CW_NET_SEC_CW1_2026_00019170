import csv
import platform
import statistics
import sys
import time
from pathlib import Path

import cryptography

import crypto_modes as cm
from telemetry import DATA_SIZES

RESULTS = Path(__file__).resolve().parent.parent / "results"
RUNS, WARMUP = 100, 5


def mode_functions(key):
    """For each mode: (encrypt(data, i) -> packet, decrypt(packet, i) -> data)."""
    n = lambda i: cm.make_nonce(1, i)          # a new nonce for every run: no reuse even here
    return {
        "AES-GCM": (lambda d, i: cm.gcm_encrypt(key, n(i), d), lambda c, i: cm.gcm_decrypt(key, n(i), c)),
        "AES-CTR": (lambda d, i: cm.ctr_encrypt(key, n(i), d), lambda c, i: cm.ctr_decrypt(key, n(i), c)),
        "AES-CBC": (lambda d, i: cm.cbc_encrypt(key, d), lambda c, i: cm.cbc_decrypt(key, c)),
        "AES-GCM-SIV": (lambda d, i: cm.siv_encrypt(key, n(i), d), lambda c, i: cm.siv_decrypt(key, n(i), c)),
    }


def time_ns(func):
    t0 = time.perf_counter_ns()
    func()
    return time.perf_counter_ns() - t0


def main():
    RESULTS.mkdir(exist_ok=True)
    key = cm.new_key()
    raw, summary = [], []
    for size_name, make in DATA_SIZES.items():
        data = make()
        for mode, (enc, dec) in mode_functions(key).items():
            for i in range(WARMUP):                       # warm-up: caches, first-call overheads
                dec(enc(data, i), i)
            for op in ("encrypt", "decrypt"):
                times = []
                for i in range(RUNS):
                    if op == "encrypt":
                        times.append(time_ns(lambda: enc(data, i)))
                    else:
                        packet = enc(data, i)            # prepared outside the timed part
                        times.append(time_ns(lambda: dec(packet, i)))
                raw += [[size_name, len(data), mode, op, r, t] for r, t in enumerate(times)]
                med = statistics.median(times)
                summary.append([size_name, len(data), mode, op, round(med / 1000, 2),
                                round(statistics.mean(times) / 1000, 2), round(statistics.stdev(times) / 1000, 2),
                                round(len(data) / (med / 1e9) / 1e6, 1)])
                print(f"{size_name:17} {mode:12} {op:8} median {summary[-1][4]:>10} us  {summary[-1][7]:>9} MB/s")
    with open(RESULTS / "benchmark_raw.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["data", "bytes", "mode", "operation", "run", "time_ns"]] + raw)
    with open(RESULTS / "benchmark_summary.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["data", "bytes", "mode", "operation", "median_us", "mean_us",
                                  "stdev_us", "throughput_MBps"]] + summary)
    env = (f"OS: {platform.platform()}\nCPU: {platform.processor() or platform.machine()}\n"
           f"Python: {sys.version.split()[0]}\ncryptography: {cryptography.__version__}\n")
    (RESULTS / "environment.txt").write_text(env, encoding="utf-8")
    print(env)


if __name__ == "__main__":
    main()