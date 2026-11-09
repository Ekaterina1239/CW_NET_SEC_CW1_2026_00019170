import csv
from pathlib import Path

import crypto_modes as cm
from server import TelemetryServer, seal
from telemetry import make_reading, to_bytes

RESULTS = Path(__file__).resolve().parent.parent / "results"
DEV = 1


def reading(minute):
    return to_bytes(make_reading(DEV, minute))


def scenario_packets(key, mode):
    """Returns {scenario: (packets sent normally, the packet under test)}."""
    p = [seal(mode, key, DEV, c, reading(360 + 5 * c)) for c in range(5)]       # counters 0..4
    return {
        "A. replay of the last genuine packet": (p, p[4]),
        "B. injection of an older genuine packet": (p, p[1]),
        "C. logger reset: RAM counter restarts at 0": (p, seal(mode, key, DEV, 0, reading(720))),
        "D. reserve-ahead after outage: counter jumps to 1000": (p, seal(mode, key, DEV, 1000, reading(720))),
        "E. replay with forged header (counter set to 99)": (p, cm.make_nonce(DEV, 99) + p[4][12:]),
    }


def main():
    rows = []
    for mode in ("AES-GCM", "AES-CTR"):
        key = cm.new_key()
        for scen, (normal, test_packet) in scenario_packets(key, mode).items():
            for check in (False, True):
                server = TelemetryServer(key, mode, check_counter=check)
                for pkt in normal:
                    server.receive(pkt)
                accepted, reason = server.receive(test_packet)
                rows.append([mode, scen, "yes" if check else "no", "ACCEPTED" if accepted else "REJECTED", reason])
                print(f"{mode} | {scen:54} | counter check: {'yes' if check else 'no ':3} | {reason}")
    RESULTS.mkdir(exist_ok=True)
    with open(RESULTS / "replay_results.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["mode", "scenario", "server_counter_check", "result", "reason"]] + rows)


if __name__ == "__main__":
    main()