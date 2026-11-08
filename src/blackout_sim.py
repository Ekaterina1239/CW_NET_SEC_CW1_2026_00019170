import csv
import math
import random
import sys
from pathlib import Path

import nonce_strategies as ns

RESULTS = Path(__file__).resolve().parent.parent / "results"
YEARS = 20
MSG_PER_DAY = 144                  # one message every 5 min from 06:00 to 18:00
MSG_PER_YEAR = MSG_PER_DAY * 365
SCENARIOS = {                      # expected outages per day (assumed, see report)
    "monthly (~1 per 30 days)": 1 / 30,
    "weekly (~1 per 7 days)": 1 / 7,
    "daily (~1 per day)": 1.0,
}
ENDURANCE = 10_000                 # flash write cycles per cell (conservative assumption)
TARGET_YEARS = 20


def poisson(rng, lam):
    """Random number of outages in one day (Knuth's method)."""
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def simulate(make_strategy, outages_per_day, seed):
    rng = random.Random(seed)
    s = make_strategy()
    used = set()
    reuses = outages = 0
    for _day in range(YEARS * 365):
        cuts = sorted(rng.randrange(MSG_PER_DAY) for _ in range(poisson(rng, outages_per_day)))
        for m in range(MSG_PER_DAY):
            while cuts and cuts[0] == m:          # power fails before message m
                s.power_loss()
                outages += 1
                cuts.pop(0)
            value = s.next_counter()
            if value in used:
                reuses += 1
            else:
                used.add(value)
    writes = s.flash.writes
    lifetime = math.inf if writes == 0 else ENDURANCE / (writes / YEARS)
    return {"reuses": reuses, "outages": outages, "flash_writes": writes,
            "flash_lifetime_years": lifetime, "skipped": getattr(s, "skipped", 0)}


def b_min(outages_per_year, endurance=ENDURANCE, target=TARGET_YEARS, msgs=MSG_PER_YEAR):
    """Smallest B that keeps flash alive for `target` years.

    writes per year  W(B) = msgs / B + outages      (block refills + one write per reboot)
    lifetime         L(B) = endurance / W(B)  >=  target
    =>  B >= msgs / (endurance / target - outages)
    Returns None when outages alone exceed the write budget (no B is enough).

    The formula is conservative: after a reboot a new block starts, so real
    refills are fewer than msgs / B. The simulation checks this (b_sweep.csv).
    """
    budget = endurance / target - outages_per_year
    return None if budget <= 0 else math.ceil(msgs / budget)


def main(seeds=3):
    RESULTS.mkdir(exist_ok=True)
    strategies = {
        "RAM counter": ns.RamCounter,
        "Flash write per message": ns.FlashPerMessage,
        "Reserve-ahead (B=100)": lambda: ns.ReserveAhead(100),
        "Reserve-ahead (B=1000)": lambda: ns.ReserveAhead(1000),
        "Random 96-bit nonce": ns.RandomNonce,
    }
    rows = []
    for scen, rate in SCENARIOS.items():
        for name, make in strategies.items():
            runs = [simulate(make, rate, seed) for seed in range(seeds)]
            avg = {k: sum(r[k] for r in runs) / seeds for k in runs[0]}
            rows.append([scen, name, round(avg["outages"]), round(avg["reuses"]),
                         round(avg["flash_writes"]),
                         "inf" if math.isinf(avg["flash_lifetime_years"]) else round(avg["flash_lifetime_years"], 1),
                         round(avg["skipped"])])
            print(f"{scen:26} {name:26} reuses={rows[-1][3]:>9} writes={rows[-1][4]:>9} lifetime={rows[-1][5]}")
    with open(RESULTS / "simulation.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["scenario", "strategy", "outages_20y", "nonce_reuses_20y",
                                  "flash_writes_20y", "flash_lifetime_years", "counter_values_skipped"]] + rows)

    # Check the B rule: sweep B, simulate, compare with the formula.
    sweep = []
    for scen, rate in SCENARIOS.items():
        rule = b_min(rate * 365)
        for B in [10, 30, 100, 300, 1000, 3000, 10000]:
            r = simulate(lambda: ns.ReserveAhead(B), rate, seed=0)
            sweep.append([scen, B, r["reuses"], r["flash_writes"], round(r["flash_lifetime_years"], 1), rule])
        print(f"{scen:26} formula B_min = {rule}")
    with open(RESULTS / "b_sweep.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["scenario", "B", "nonce_reuses_20y", "flash_writes_20y",
                                  "flash_lifetime_years", "formula_B_min"]] + sweep)


if __name__ == "__main__":
    main(seeds=int(sys.argv[1]) if len(sys.argv) > 1 else 3)