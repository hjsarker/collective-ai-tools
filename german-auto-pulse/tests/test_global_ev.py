import csv
import io
import json
from pathlib import Path
from pipeline.global_ev import DATASETS, parse_datasets, validate, export_sql_analytics

ROOT = Path(__file__).resolve().parents[1]


def test_bundled_world_data_is_real_and_consistent():
    data = json.loads((ROOT / 'data/global.json').read_text())
    validate(data)
    assert data['last_report_year'] == 2025
    assert len(data['countries']) >= 30
    assert data['countries']['DEU']['series']['2025'][0] == 30
    assert data['countries']['CHN']['series']['2025'][0] == 53
    assert data['countries']['OWID_WRL']['series']['2025'][0] == 25
    assert data['countries']['JPN']['series']['2025'][0] == 3
    assert data['countries']['DEU']['series']['2024'][0] == 20


def test_market_share_change_is_percentage_points():
    d = json.loads((ROOT / 'data/global.json').read_text())['countries']['DEU']['series']
    assert d['2025'][0] - d['2024'][0] == 10
    assert d['2025'][1] - d['2024'][1] == 290000


def test_sql_analytics_delta(tmp_path):
    data = json.loads((ROOT / 'data/global.json').read_text())
    dest = tmp_path / 'analytics.csv'
    export_sql_analytics(data, dest)
    records = list(csv.DictReader(dest.open()))
    germany = next(r for r in records if r['code'] == 'DEU' and r['year'] == '2025')
    assert float(germany['share_change_pp']) == 10
    assert int(germany['ev_sales_change']) == 290000


def test_parser_disallows_incomplete_data():
    row = 'Entity,Code,Year,Value\nGermany,DEU,2025,25\n'
    try:
        parse_datasets({k: row for k in DATASETS})
    except ValueError as e:
        assert 'Not enough comparable markets' in str(e)
    else:
        raise AssertionError('Missing markets must not pass validation')


def test_percentages_cannot_exceed_one_hundred():
    d = json.loads((ROOT / 'data/global.json').read_text())
    d['countries']['DEU']['series']['2025'][0] = 105
    try:
        validate(d)
    except ValueError as e:
        assert 'outside' in str(e)
    else:
        raise AssertionError('Out-of-range shares must fail validation')
