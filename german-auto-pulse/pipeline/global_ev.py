"""Reproducible IEA/OWID electric-car market dataset builder.

The public dashboard uses precomputed JSON. This module can rebuild that JSON
from four OWID Grapher CSV datasets with the same definitions globally. It is
safe to run in CI: all sources must be valid before either output is overwritten.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sqlite3
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_BASE = "https://ourworldindata.org/grapher/"
DATASETS = (
    "electric-car-sales-share",  # new EV sales (BEV+PHEV) / all new sales, percent
    "electric-car-sales",  # electric passenger cars sold in units
    "bev-share-new-ev",  # BEV / all EVs sold, percent
    "share-car-stocks-electric",  # BEV+PHEV stock / all car stock, percent
)
SELECTED = {
    "DEU", "FRA", "GBR", "ITA", "ESP", "NOR", "SWE", "NLD", "DNK", "BEL", "AUT", "POL",
    "CHE", "CZE", "FIN", "PRT", "IRL", "HUN", "SVK", "ROU", "ISL", "CHN", "USA", "JPN",
    "KOR", "IND", "CAN", "BRA", "MEX", "TUR", "AUS", "VNM",
}
SOURCE_CREDIT = "Our World in Data / IEA Global EV Outlook 2026"


def get_csv(dataset: str) -> str:
    url = f"{CSV_BASE}{dataset}.csv?tab=chart"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; GermanAutoPulse/1.0)"})
    with urllib.request.urlopen(request, timeout=35) as response:
        result = response.read(3_000_000).decode("utf-8-sig")
    if not result.startswith("Entity,Code,Year,"):
        raise ValueError(f"Unexpected CSV structure: {url}")
    return result


def parse_datasets(csv_text_by_name: dict[str, str]) -> dict:
    countries: dict[str, dict] = {}
    for metric, dataset in enumerate(DATASETS):
        reader = csv.DictReader(io.StringIO(csv_text_by_name[dataset]))
        if not reader.fieldnames or not {"Entity", "Code", "Year"}.issubset(reader.fieldnames):
            raise ValueError(f"Invalid header: {dataset}")
        metric_cols = [c for c in reader.fieldnames if c not in ("Entity", "Code", "Year")]
        if len(metric_cols) != 1:
            raise ValueError(f"Expected one value column: {dataset}")
        for row in reader:
            name = row["Entity"]
            code = row["Code"]
            if code not in SELECTED and name not in ("World", "European Union (27)"):
                continue
            year = int(row["Year"])
            if year < 2020:
                continue
            raw = row[metric_cols[0]]
            if not raw:
                continue
            value = float(raw)
            if value < 0 or (metric != 1 and value > 100):
                raise ValueError(f"Invalid {dataset} value for {code}/{year}: {value}")
            cid = code or ("OWID_WRL" if name == "World" else "OWID_EU27")
            country = countries.setdefault(cid, {"name": name, "series": {}})
            country["series"].setdefault(str(year), [None] * 4)[metric] = int(value) if metric == 1 else round(value, 3)
    years = [int(y) for d in countries.values() for y in d["series"]]
    latest = max(years, default=0)
    payload = {"source": SOURCE_CREDIT, "last_report_year": latest, "countries": countries}
    validate(payload)
    return payload


def validate(payload: dict) -> None:
    if payload["last_report_year"] < 2025:
        raise ValueError("Global EV data is unexpectedly old")
    countries = payload["countries"]
    if len(countries) < 25:
        raise ValueError("Not enough comparable markets")
    for code in ("DEU", "USA", "CHN", "JPN", "FRA", "GBR", "NOR", "OWID_WRL"):
        if code not in countries:
            raise ValueError(f"Required country missing: {code}")
        if str(payload["last_report_year"]) not in countries[code]["series"]:
            raise ValueError(f"Current year missing: {code}")
        values = countries[code]["series"][str(payload["last_report_year"])]
        if not all(v is not None for v in values):
            raise ValueError(f"Metrics missing: {code}")
    for code, country in countries.items():
        for year, values in country["series"].items():
            if len(values) != 4:
                raise ValueError(f"Bad metric tuple: {code}/{year}")
            if any((v is not None and not 0 <= v <= 100) for j, v in enumerate(values) if j != 1):
                raise ValueError(f"Percentage outside 0..100: {code}/{year}")
            if values[1] is not None and values[1] < 0:
                raise ValueError(f"Negative sales: {code}/{year}")


def export_sql_analytics(payload: dict, destination: Path) -> None:
    """Calculate reproducible year-on-year percentage-point and volume changes with SQL."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE observations(code TEXT, year INTEGER, ev_share REAL, ev_sales INTEGER)")
    rows = [(code, int(year), vals[0], vals[1]) for code, country in payload["countries"].items()
            for year, vals in country["series"].items()]
    conn.executemany("INSERT INTO observations VALUES(?,?,?,?)", rows)
    results = conn.execute("""
        SELECT code, year, ev_share, ev_sales,
               ROUND(ev_share - LAG(ev_share) OVER (PARTITION BY code ORDER BY year), 3) AS share_change_pp,
               ev_sales - LAG(ev_sales) OVER (PARTITION BY code ORDER BY year) AS ev_sales_change,
               DENSE_RANK() OVER (PARTITION BY year ORDER BY ev_share DESC) AS adoption_rank
        FROM observations ORDER BY year DESC, adoption_rank ASC, code
    """).fetchall()
    import csv as csv_module
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf8") as file:
        writer = csv_module.writer(file)
        writer.writerow(["code", "year", "ev_share", "ev_sales", "share_change_pp", "ev_sales_change", "adoption_rank"])
        writer.writerows(results)
    conn.close()


def refresh() -> dict:
    source = {dataset: get_csv(dataset) for dataset in DATASETS}
    payload = parse_datasets(source)
    # Only write after all external calls, parsing and data quality checks succeed.
    normalized = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    for destination in (ROOT / "data/global.json", ROOT / "web/global.json"):
        destination.write_text(normalized, encoding="utf8")
    export_sql_analytics(payload, ROOT / "data/global_analytics.csv")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="Download the latest annual OWID/IEA data")
    args = parser.parse_args()
    if args.refresh:
        data = refresh()
        print(f"Updated global EV snapshot: {len(data['countries'])} entries through {data['last_report_year']}")
    else:
        data = json.loads((ROOT / "data/global.json").read_text())
        validate(data)
        export_sql_analytics(data, ROOT / "data/global_analytics.csv")
        print(f"Validated global snapshot: {len(data['countries'])} entries through {data['last_report_year']}")


if __name__ == "__main__":
    main()
