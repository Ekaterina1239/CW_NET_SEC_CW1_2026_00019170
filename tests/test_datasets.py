from datasets import load_outage_scenarios, load_pvgis

SAMPLE = """Latitude (decimal degrees):\t41.310
Radiation database:\tPVGIS-ERA5

time,P,G(i),H_sun,T2m,WS10m,Int
20200101:0010,0.0,0.0,0.0,1.0,2.0,0.0
20200101:0610,512.5,300.0,20.0,3.0,2.0,0.0

P: PV system power (W)
"""


def test_load_pvgis(tmp_path):
    f = tmp_path / "pvgis_test.csv"
    f.write_text(SAMPLE, encoding="utf-8")
    rows = load_pvgis(f)
    assert len(rows) == 2
    assert rows[1][1] == 512.5
    assert rows[0][0].hour == 5          # 00:10 UTC -> 05:10 in Uzbekistan (UTC+5)


def test_load_outages(tmp_path):
    f = tmp_path / "outages.csv"
    f.write_text("scenario,outages_per_month,year,source\naverage,1.9,2019,WB\n", encoding="utf-8")
    rate = list(load_outage_scenarios(f).values())[0]
    assert abs(rate - 1.9 / 30) < 1e-9