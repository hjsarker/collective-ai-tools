import json
from pathlib import Path
import pytest
from pipeline.main import MARKET, validate_market, parse_vda_html, update, numeric


def fake_html():
    columns = ['Metric','September 2026','Veränderung 26/25 in %', 'Januar - September 2026','Veränderung 26/25 in %']
    rows = [
        ['Neuzulassungen in Deutschland','256.774','9','2.221.798','5'],
        ['Elektro','116.280','59','851.644','42'],
        ['darunter BEV','88.599','95','604.144','58'],
        ['PHEV','27.681','0','247.489','14'],
        ['Produktion in Deutschland','392.200','0','3.034.900','-4'],
        ['darunter Export','288.800','1','2.294.500','-4'],
    ]
    return '<html><table><thead><tr>'+''.join(f'<th>{x}</th>' for x in columns)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{x}</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></html>'


def test_baseline_reconciles():
    validate_market(json.loads(MARKET.read_text()))


def test_numeric_german_format():
    assert numeric('2.221.798') == 2221798
    assert numeric('-4') == -4


def test_parser_and_no_change():
    parsed=parse_vda_html(fake_html())
    assert parsed['period']=='2026-09'
    assert parsed['registrations']==256774
    assert parsed['exports_ytd']==2294500
    baseline=json.loads(MARKET.read_text())
    revised, changed=update(fake_html(),baseline)
    assert not changed
    assert revised==baseline


def test_rejects_missing_table():
    with pytest.raises((ValueError,AttributeError)):
        parse_vda_html('<table><tr><td>something else</td></tr></table>')


def test_rejects_inconsistent_ytd():
    baseline=json.loads(MARKET.read_text())
    baseline['latest']['registrations_ytd']=999
    with pytest.raises(AssertionError):
        validate_market(baseline)
