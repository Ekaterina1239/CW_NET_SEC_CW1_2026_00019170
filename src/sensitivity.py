"""how do the conclusions change with flash endurance"""
import csv

import blackout_sim as bs
import nonce_strategies as ns

ENDURANCES = [10_000, 100_000]


def main():
    rows = []
    for endurance in ENDURANCES:
        bs.ENDURANCE = endurance                     # change the assumption
        for scen, rate in bs.SCENARIOS.items():
            rule = bs.b_min(rate * 365, endurance=endurance)
            per_msg = bs.simulate(ns.FlashPerMessage, rate, seed=0)
            ra1000 = bs.simulate(lambda: ns.ReserveAhead(1000), rate, seed=0)
            rows.append([endurance, scen, rule if rule else "none (impossible)",
                         round(per_msg["flash_lifetime_years"], 2),
                         round(ra1000["flash_lifetime_years"], 1)])
            print(rows[-1])
    bs.ENDURANCE = 10_000                            # restore the default
    with open(bs.RESULTS / "sensitivity.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["flash_endurance_cycles", "scenario", "formula_B_min",
                                  "lifetime_flash_per_message_years",
                                  "lifetime_reserve_ahead_B1000_years"]] + rows)


if __name__ == "__main__":
    main()