"""Build self-contained static production HTML from tested repository components."""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parent
WEB = ROOT / 'web'
html = (WEB / 'index.html').read_text(encoding='utf8')
market = json.loads((WEB / 'market.json').read_text())
global_data = json.loads((WEB / 'global.json').read_text())
html = html.replace('<link rel="stylesheet" href="./style.css" />', '<style>\n' + (WEB / 'style.css').read_text() + '\n</style>')
html = html.replace('<script src="./global.js" defer></script>', '')
html = html.replace('<script src="./app.js" defer></script>', '')
inline = '<script>\n' + (WEB / 'global.js').read_text() + '\n</script>\n'
inline += '<script>\nwindow.__MARKET_DATA__=' + json.dumps(market, separators=(',', ':')).replace('<','\\u003c') + ';\n'
inline += 'window.__GLOBAL_DATA__=' + json.dumps(global_data, separators=(',', ':')).replace('<','\\u003c') + ';\n'
inline += (WEB / 'app.js').read_text() + '\n</script>\n'
html = html.replace('</body>', inline + '</body>')
(ROOT / 'deploy-index.html').write_text(html, encoding='utf8')
print(f'Built {len(html):,} character standalone HTML')
