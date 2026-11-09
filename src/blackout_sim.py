"""E4 (RQ4): 20 years of a solar logger with random power outages.
"""
import csv
import math
import random
import sys
from pathlib import Path

import nonce_strategies as ns
from stats import summary

RESULTS = Path(__file__).resolve().parent.parent / "results"
YEARS = 20
MSG_PER_DAY = 144                  # one message every 5 min from 06:00 to 18:00
MSG_PER_YEAR = MSG_PER_DAY * 365
SCENARIOS = {                      # expected outages per day (assumed, see report)
    "monthly (~1 per 30 days)": 1 / 30,
    "weekly (~1 per 7 days)": 1 / 7,
    "daily (~1 per day)": 1.0,
    "twice daily (~2 per day)": 2.0,        # stress scenario
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


def fmt(x, digits=1):
    return "inf" if math.isinf(x) else round(x, digits)


def main(seeds=10):
    """Every strategy x scenario is simulated with `seeds` different random seeds.

    We report the mean, the standard deviation (SD) and the 95% confidence
    interval half-width (CI95) across seeds, so the reader can see how much
    the result depends on the random timing of outages.
    """
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
            out = summary([r["outages"] for r in runs])
            reu = summary([r["reuses"] for r in runs])
            wr = summary([r["flash_writes"] for r in runs])
            lives = [r["flash_lifetime_years"] for r in runs]
            life = (math.inf, 0.0, 0.0) if math.isinf(lives[0]) else summary(lives)
            rows.append([scen, name, seeds, round(out[0]), round(reu[0]), round(reu[1]), round(reu[2]),
                         round(wr[0]), round(wr[1]), fmt(life[0]), fmt(life[1], 2), fmt(life[2], 2)])
            print(f"{scen:32} {name:26} reuses {reu[0]:>11,.0f} +/- {reu[2]:>7,.0f}   "
                  f"lifetime {fmt(life[0])} +/- {fmt(life[2], 2)} years")
    with open(RESULTS / "simulation.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["scenario", "strategy", "seeds", "outages_mean",
                                  "reuses_mean", "reuses_sd", "reuses_ci95",
                                  "flash_writes_mean", "flash_writes_sd",
                                  "lifetime_years_mean", "lifetime_years_sd", "lifetime_years_ci95"]] + rows)

    # Check the B rule: sweep B, simulate with several seeds, compare with the formula.
    sweep_seeds = min(seeds, 5)
    sweep = []
    for scen, rate in SCENARIOS.items():
        rule = b_min(rate * 365)
        for B in [10, 30, 100, 300, 1000, 3000, 10000]:
            runs = [simulate(lambda: ns.ReserveAhead(B), rate, seed) for seed in range(sweep_seeds)]
            life = summary([r["flash_lifetime_years"] for r in runs])
            sweep.append([scen, B, sum(r["reuses"] for r in runs), round(life[0], 1), round(life[2], 2), rule])
        print(f"{scen:32} formula B_min = {rule}")
    with open(RESULTS / "b_sweep.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["scenario", "B", "nonce_reuses_all_seeds", "lifetime_years_mean",
                                  "lifetime_years_ci95", "formula_B_min"]] + sweep)


if __name__ == "__main__":
    main(seeds=int(sys.argv[1]) if len(sys.argv) > 1 else 10)