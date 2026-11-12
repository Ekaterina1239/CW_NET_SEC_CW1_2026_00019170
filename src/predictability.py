import csv

from datasets import UZ_OFFSET, load_pvgis, pvgis_files
from blackout_sim import RESULTS

REPORT_FROM, REPORT_TO = 6, 18          # the logger reports from 06:00 to 18:00 local time
ZERO_W = 1.0                            # below 1 W counts as "0 W" (fully predictable)
LOW_W = 100.0                           # below 100 W: value nearly predictable


def analyse(rows):
    day = [p for t, p in rows if REPORT_FROM <= t.hour < REPORT_TO]
    years = sorted({(t - UZ_OFFSET).year for t, _ in rows})     # calendar years of the UTC data
    return {
        "years": f"{years[0]}-{years[-1]}",
        "reporting_hours": len(day),
        "share_zero_pct": round(100 * sum(p < ZERO_W for p in day) / len(day), 1),
        "share_below_100W_pct": round(100 * sum(p < LOW_W for p in day) / len(day), 1),
        "mean_power_W": round(sum(day) / len(day), 1),
    }


def main():
    files = pvgis_files()
    if not files:
        print("No data/pvgis_*.csv files found - download them first (see README).")
        return
    rows = []
    for city, path in files.items():
        r = analyse(load_pvgis(path))
        rows.append([city, r["years"], r["reporting_hours"], r["share_zero_pct"],
                     r["share_below_100W_pct"], r["mean_power_W"]])
        print(f"{city:12} {r['years']}  hours={r['reporting_hours']:6}  "
              f"0 W: {r['share_zero_pct']:5}%   <100 W: {r['share_below_100W_pct']:5}%")
    RESULTS.mkdir(exist_ok=True)
    with open(RESULTS / "predictability.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["city", "years", "reporting_hours", "share_zero_power_pct",
                                  "share_below_100W_pct", "mean_power_W"]] + rows)


if __name__ == "__main__":
    main()