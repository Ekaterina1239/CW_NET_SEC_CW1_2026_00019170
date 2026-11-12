import csv
import datetime as dt
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
UZ_OFFSET = dt.timedelta(hours=5)          # PVGIS time is UTC; Uzbekistan is UTC+5


def load_pvgis(path):
    rows = []
    with open(path, encoding="utf-8", errors="replace") as f:
        header = None
        for line in f:
            line = line.strip()
            if header is None:
                if line.startswith("time,"):
                    header = line.split(",")
                    p_col = header.index("P")             # the PV power column
                continue
            if not line or not line[0].isdigit():          # end of the data block
                break
            cells = line.split(",")
            utc = dt.datetime.strptime(cells[0], "%Y%m%d:%H%M")
            rows.append((utc + UZ_OFFSET, float(cells[p_col])))
    if header is None:
        raise ValueError(f"{path}: no line starting with 'time,' - is this a PVGIS hourly CSV with PV power (pvcalculation=1)?")
    return rows


def pvgis_files():
    """{city: path} for every data/pvgis_*.csv file (city = the part after 'pvgis_')."""
    files = sorted(DATA.glob("pvgis_*.csv"))
    return {p.stem.replace("pvgis_", "").split("_")[0].capitalize(): p for p in files}


def load_outage_scenarios(path=None):
    path = path or DATA / "outages_uzbekistan.csv"
    scenarios = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            per_month = float(row["outages_per_month"])
            label = f'{row["scenario"]} ({per_month:g}/month, {row["year"]})'
            scenarios[label] = per_month / 30
    return scenarios