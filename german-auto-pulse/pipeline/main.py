"""Update the German Auto Pulse dashboard from VDA's published monthly table.

This intentionally uses guarded parsing, and never invents missing historical or
brand-level data. All existing validated snapshot data remains in place when a
source cannot be parsed or reconciled.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
MARKET = ROOT / "data" / "market.json"
WEB = ROOT / "web" / "market.json"
VDA_URL = "https://www.vda.de/de/aktuelles/zahlen-und-daten/monatszahlen"
MONTHS = {"Januar": 1, "Februar": 2, "März": 3, "April": 4, "Mai": 5, "Juni": 6,
          "Juli": 7, "August": 8, "September": 9, "Oktober": 10, "November": 11, "Dezember": 12}


def numeric(value: object) -> int:
    """Parse a German-formatted number from VDA text or HTML tables."""
    if isinstance(value, (int, float)) and not pd.isna(value):
        return int(value)
    s = str(value).replace("\xa0", " ").strip()
    if s in {"", "nan", "-", "—"}:
        raise ValueError(f"not a number: {value!r}")
    match = re.search(r"-?\d[\d.,\s]*", s)
    if not match:
        raise ValueError(f"not a number: {value!r}")
    return int(match.group(0).strip().replace(".", "").replace(" ", "").split(",")[0])


def find_report_period(header: str) -> str:
    for name, m in MONTHS.items():
        match = re.search(rf"\b{name}\s+(20\d\d)\b", header, re.IGNORECASE)
        if match:
            return f"{int(match.group(1)):04d}-{m:02d}"
    raise ValueError("No German month/year header found in the source table")


def parse_vda_html(html: str) -> dict:
    """Read the actual table rows; refuse to map ambiguous labels to data."""
    tables = pd.read_html(StringIO(html), decimal=",", thousands=".")
    table = None
    for candidate in tables:
        string = candidate.astype(str).to_string(index=False)
        if "Neuzulassungen in Deutschland" in string and "Produktion in Deutschland" in string:
            table = candidate
            break
    if table is None:
        raise ValueError("VDA passenger-car table not found")
    col_titles = [" ".join(map(str, col)) if isinstance(col, tuple) else str(col) for col in table.columns]
    period = find_report_period(" ".join(col_titles))
    # HTML structure can have multi-level headers. Rows are mapped by their
    # exact German definitions, rather than relying on an unversioned column index.
    rows: list[tuple[str, list[object]]] = []
    for _, row in table.iterrows():
        values = row.tolist()
        if not values:
            continue
        label = re.sub(r"\s+", " ", str(values[0])).strip()
        rows.append((label, values[1:]))

    def extract(label: str, index: int) -> int:
        matched = [r for name, r in rows if name == label]
        if len(matched) != 1:
            raise ValueError(f"Expected one row named {label!r}, found {len(matched)}")
        return numeric(matched[0][index])

    # The published table is: month, month YoY %, YTD, YTD YoY %.
    result = {
        "period": period,
        "registrations": extract("Neuzulassungen in Deutschland", 0),
        "registrations_yoy_pct": extract("Neuzulassungen in Deutschland", 1),
        "registrations_ytd": extract("Neuzulassungen in Deutschland", 2),
        "registrations_ytd_yoy_pct": extract("Neuzulassungen in Deutschland", 3),
        "production": extract("Produktion in Deutschland", 0),
        "production_yoy_pct": extract("Produktion in Deutschland", 1),
        "production_ytd": extract("Produktion in Deutschland", 2),
        "production_ytd_yoy_pct": extract("Produktion in Deutschland", 3),
        "bev": extract("darunter BEV", 0),
        "bev_yoy_pct": extract("darunter BEV", 1),
        "bev_ytd": extract("darunter BEV", 2),
        "phev": extract("PHEV", 0),
        "phev_ytd": extract("PHEV", 2),
        "electric_combined": extract("Elektro", 0),
        "electric_ytd": extract("Elektro", 2),
    }
    # VDA 'darunter Export' label is distinct from other table's general exports.
    result.update({
        "exports": extract("darunter Export", 0),
        "exports_yoy_pct": extract("darunter Export", 1),
        "exports_ytd": extract("darunter Export", 2),
        "exports_ytd_yoy_pct": extract("darunter Export", 3),
    })
    if result["bev"] + result["phev"] != result["electric_combined"]:
        raise ValueError("VDA monthly electrified categories do not reconcile")
    if result["bev"] > result["registrations"] or result["exports"] > result["production"] * 2:
        raise ValueError("Implausible VDA values")
    return result


def validate_market(d: dict) -> None:
    l = d["latest"]
    items = d["registrations_monthly"]
    assert items and len(items) == len({x["month"] for x in items}), "duplicated month"
    assert all(isinstance(x["count"], int) and x["count"] > 0 for x in items)
    assert items == sorted(items, key=lambda x: x["month"]), "months must be ordered"
    assert sum(x["count"] for x in items if x["month"].startswith(d["metadata"]["reporting_period"][:4])) == l["registrations_ytd"], "YTD reconciliation"
    assert l["bev"] + l["phev"] == l["electric_combined"], "monthly EV categories"
    assert l["registrations"] >= l["electric_combined"]
    assert sum(x["registrations"] for x in d["brands_ytd"]) <= l["registrations_ytd"] if d["metadata"].get("brand_reporting_period") == d["metadata"]["reporting_period"] else True
    for brand in d["brands_ytd"]:
        assert brand["registrations"] >= 0


def update(html: str, current: dict) -> tuple[dict, bool]:
    parsed = parse_vda_html(html)
    old_period = current["metadata"]["reporting_period"]
    if parsed["period"] < old_period:
        raise ValueError(f"Source is older ({parsed['period']}) than snapshot ({old_period})")
    if parsed["period"] == old_period and all(current["latest"].get(k) == v for k, v in parsed.items() if k != "period"):
        return current, False
    if parsed["period"][:4] != old_period[:4]:
        raise ValueError("New calendar year requires explicit annual roll-over procedure")
    new = json.loads(json.dumps(current))
    period = parsed.pop("period")
    rows = {x["month"]: x["count"] for x in new["registrations_monthly"]}
    # A gap invalidates the snapshot rather than backfilling invented values.
    last = max(rows)
    expected_next = f"{int(last[:4]):04d}-{int(last[5:])+1:02d}"
    if period not in rows and period != expected_next:
        raise ValueError(f"Missing intermediate months before {period}")
    rows[period] = parsed["registrations"]
    new["registrations_monthly"] = [{"month": k, "count": rows[k]} for k in sorted(rows)]
    new["latest"].update(parsed)
    new["metadata"]["reporting_period"] = period
    new["metadata"]["last_successful_refresh"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    new["metadata"]["status"] = "automatically refreshed official VDA snapshot"
    validate_market(new)
    return new, True


def analytics_sql(d: dict, db_path: Path) -> None:
    """Exercise reproducible SQL analytics with DuckDB, using SQLite fallback locally."""
    try:
        import duckdb  # type: ignore
        conn = duckdb.connect(str(db_path))
    except ImportError:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE IF NOT EXISTS registrations(month TEXT PRIMARY KEY, count INTEGER NOT NULL)")
    conn.execute("DELETE FROM registrations")
    conn.executemany("INSERT INTO registrations(month,count) VALUES (?,?)", [(x["month"], x["count"]) for x in d["registrations_monthly"]])
    query = """SELECT month, count,
        LAG(count) OVER (ORDER BY month) AS previous_month,
        ROUND(AVG(count) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS rolling_3m,
        RANK() OVER (ORDER BY count DESC) AS volume_rank
        FROM registrations ORDER BY month"""
    rows = conn.execute(query).fetchall()
    csv_path = ROOT / "data" / "registration_analytics.csv"
    csv_path.write_text("month,registrations,previous_month,rolling_3m,volume_rank\n"+"\n".join(
        ",".join("" if v is None else str(v) for v in r) for r in rows)+"\n",encoding="utf-8")
    conn.close()


def run() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Validate and rebuild the existing verified dataset without network")
    parser.add_argument("--source-html", type=Path, help="Read a locally downloaded VDA table for reproducible tests")
    parser.add_argument("--check-only", action="store_true", help="Test ingestion and validation without writing updated snapshots")
    args = parser.parse_args()
    existing = json.loads(MARKET.read_text(encoding="utf-8"))
    validate_market(existing)
    new = existing
    changed = False
    if not args.offline:
        if args.source_html:
            html = args.source_html.read_text(encoding="utf-8")
        else:
            response = requests.get(VDA_URL, timeout=35, headers={"User-Agent":"GermanAutoPulse/1.0 (portfolio analytics; https://github.com/hjsarker)"})
            response.raise_for_status()
            html = response.text
        new, changed = update(html, existing)
        if not changed:
            new = json.loads(json.dumps(existing))
        new["metadata"]["last_source_check"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    validate_market(new)
    print(f"Validated {new['metadata']['reporting_period']} | changed={changed} | {len(new['registrations_monthly'])} months")
    if not args.check_only:
        MARKET.write_text(json.dumps(new, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        shutil.copyfile(MARKET, WEB)
        analytics_sql(new, ROOT / "data" / "analytics.duckdb")


if __name__ == "__main__":
    run()
