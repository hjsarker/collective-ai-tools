# Auto Pulse: Global Automotive Market Intelligence

**Live dashboard:** https://german-auto-pulse.vercel.app/  
**Focus:** International EV adoption and market momentum, with a dedicated German passenger-car industry deep dive.

A public data-analytics portfolio project built to make country-level comparisons understandable in seconds. Uses real IEA data from Our World in Data (2020–2025) for international comparisons, plus published KBA/VDA figures through September 2026 for Germany.

## What to explore

1. **Global overview:** country picker, year selector, adoption share, EV sales volume, BEV mix, EV share of the car fleet, 32 searchable country markets, regional rankings and a short data-driven story.
2. **Compare countries:** select any two markets and the same annual metric. See a six-year trend chart, gap in percentage points or vehicle units, and annual change.
3. **Germany deep dive:** monthly 2026 passenger-car registrations, brand competition, September BEV/PHEV breakdown, production and vehicle export counts, data-quality checks.

The dashboard deliberately separates:

- **EV adoption share:** battery-electric plus plug-in hybrid as a percentage of *new* passenger cars sold.
- **EV sales:** number of new BEVs and PHEVs, not all cars produced.
- **BEV share of EV sales:** proportion of electric-car sales that were fully battery-electric, *not* percentage of all new cars.
- **EV stock share:** fraction of all cars currently in use that are EVs.
- **German production and exports:** 2026 KBA/VDA counts, not 2025 IEA EV sales, and not company revenue.

These figures are not ranked as a single overall measure of industrial competitiveness. A country can be a large manufacturer without having high domestic EV adoption.

## Data coverage and sources

| Component | Period | Source |
| --- | --- | --- |
| International adoption, EV sales, BEV sales mix, fleet share | 2020–2025 full calendar years | [Our World in Data, IEA Global EV Outlook 2026](https://ourworldindata.org/electric-car-sales) |
| Monthly car registrations and brand ranking, Germany | Jan–Sep 2026 | [KBA](https://www.kba.de/DE/Statistik/Fahrzeuge/Neuzulassungen/MonatlicheNeuzulassungen/monatl_neuzulassungen_node.html) and cross-checks |
| German production, factory exports, BEV/PHEV in latest September release | Sep 2026 | [VDA](https://www.vda.de/de/aktuelles/zahlen-und-daten/monatszahlen) |

See [methodology](docs/methodology.md) for definitions, scopes, limitations and source licences. Country comparison uses the *same* international data vintage and year. It must not be combined numerically with the newer German partial-year monthly view.

## Stack

- **Data ingestion:** Python standard library CSV and HTTP client, KBA/VDA parser.
- **SQL analytics:** SQLite (standard library) with LAG, DENSE_RANK and year-on-year volume/share changes, independent of external database services.
- **Data quality:** schema checks, country coverage, historical data checks, percentage bounds and reconciliation with published German YTD counts. 10 pytest tests.
- **Web:** vanilla JavaScript, semantic HTML, custom responsive CSS and accessible SVG charts. No runtime dependencies, no tracking and no backend.
- **Publishing:** static files suitable for GitHub Pages or Vercel. A one-file standalone production build is included for simple hosting.

## Quick start

```bash
cd german-auto-pulse
python -m http.server 8000 --directory web
# http://localhost:8000
```

No Node installation is required.

Run the tests and reproduce SQL analytics:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m pipeline.global_ev
python -m pipeline.main --offline
```

Update international data from Our World in Data when the annual IEA release changes:

```bash
python -m pipeline.global_ev --refresh
python -m pytest -q
python build_standalone.py
```

The global ingestion validates four independent CSV datasets **before** replacing either stored data file. If downloads fail or data are malformed, the previous validated snapshot is preserved. To refresh German monthly figures, use `python -m pipeline.main` (subject to VDA access and schema stability).

## Free deploy

To deploy to GitHub Pages from a dedicated public repository:

1. Upload the project directory to the repository root.
2. In **Settings > Pages**, select **GitHub Actions** as the build source.
3. Run `.github/workflows/refresh-and-deploy.yml` from **Actions** once.

The existing GitHub showcase folder is not itself a repository root, so nested workflows in that folder do not trigger automatically. This is a documented limitation rather than a silently assumed live refresh. The production Vercel snapshot is published separately, and is not necessarily linked to GitHub Actions until the project is connected to Git deployment.

## Portfolio story

This project demonstrates standardized cross-market analysis, correct denominator and reporting-period handling, SQL window functions, data validation, report-friendly storytelling, UI design and static delivery at near-zero running cost. The dashboard uses only source-grounded observations: no fictional time series and no unsupported forecasts.

## Credits and licences

Dashboard code: MIT (see LICENSE). Data: third-party sources retain their own licensing. OWID chart content is presented under CC BY with attribution to IEA Global EV Outlook 2026, and the individual publisher's usage terms also apply. This project is not affiliated with any source publisher.
