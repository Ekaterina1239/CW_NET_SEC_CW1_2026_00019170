""" data logger (deterministic, reproducible)."""
import json
import math
import random

READING_EVERY_MIN = 5          # one reading every 5 minutes


def make_reading(device_id, minute_of_day):
    hour = minute_of_day / 60
    sun = max(0.0, math.sin(math.pi * (hour - 6) / 12))   # 0 at 06:00 and 18:00, 1 at noon
    return {
        "dev": f"UZ-PV-{device_id:06d}",
        "min": minute_of_day,
        "p_w": round(5000 * sun, 1),                     # power, W
        "v_dc": round(380 * min(1.0, 3 * sun), 1),        # panel voltage, V
        "status": "OK",
    }


def to_bytes(reading):
    return json.dumps(reading, separators=(",", ":")).encode("utf-8")



def telemetry_packet():
    """One reading (~70 bytes): sent every 5 minutes."""
    return to_bytes(make_reading(1, 720))


def batch_log():
    """One day of readings (288 readings, ~20 KB): uploaded after a connection loss."""
    readings = [make_reading(1, m) for m in range(0, 24 * 60, READING_EVERY_MIN)]
    return json.dumps(readings, separators=(",", ":")).encode("utf-8")


def firmware_dump(size=1024 * 1024):
    """1 MiB of pseudo-random bytes standing in for a firmware image (seeded)."""
    return random.Random(2026).randbytes(size)


DATA_SIZES = {"telemetry packet": telemetry_packet, "batch log": batch_log, "firmware dump": firmware_dump}