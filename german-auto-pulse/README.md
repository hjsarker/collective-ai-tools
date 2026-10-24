# German Auto Pulse

**Live dashboard:** https://german-auto-pulse.vercel.app/  
**Public source code:** https://github.com/hjsarker/collective-ai-tools/tree/main/german-auto-pulse

**An interactive, source-aware portfolio dashboard for Germany's passenger-car market.**

Track new passenger car registrations, brand competition, battery-electric adoption, German production and factory exports. The frontend is a fast static website and the update pipeline is Python + SQL. No paid API, backend, or database hosting is required.

## Data through September 2026

Built from VDA/KBA public monthly figures and KBA-derived registration summaries. Includes January–September 2026 monthly registrations, 2022–2025 completed annual totals, September 2026 VDA data for BEV/PHEV and production/export, top 20 brand YTD ranking and top 8 September brands. These are **verified snapshot values**, not simulated time series. Official definitions and limitations are in [`docs/methodology.md`](docs/methodology.md).

## Features

- Modern responsive single-page dashboard, accessible on phones or desktops
- Monthly time-series chart with per-point tooltips
- Brand ranking, live search and year-to-date/month toggle
- Market-share calculations and electrification breakdown
- Manufacturing output and factory export indicators
- Three data-driven analytical insights and downloadable JSON
- Source and dataset freshness transparency, source links, data checks
- Python ingestion of the official current VDA table, strict validation, SQL window analytics and CI tests
- GitHub Pages deployment plus daily source checks, with safe failure behavior

## Run locally

```bash
cd german-auto-pulse
python -m http.server 8000 --directory web
# Open http://localhost:8000
```

Run offline validation and SQL analytics:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m pipeline.main --offline
```

Fetch and verify the latest VDA release:

```bash
python -m pipeline.main
```

This fetch may fail if VDA changes its published table structure or blocks automated traffic. In that case it fails visibly rather than storing guessed data. The original validated snapshot is left unchanged.

## Deploy to free GitHub Pages after moving to a standalone repository

1. For a standalone repository, create a **new public repository** `german-auto-pulse` and push this directory to its `main` branch.
2. Under **Settings → Pages → Build and deployment**, select **GitHub Actions**.
3. Run the `Refresh official data and deploy` workflow once using **Actions → Run workflow**.
4. Your URL should be `https://YOUR-USERNAME.github.io/german-auto-pulse/`.

The current live Vercel site is a deployed, self-contained **September 2026 snapshot**. It does not automatically republish updated data, since the connected Vercel account does not currently have a GitHub Git integration. When running from a standalone repository with Actions and Pages configured, the workflow can refresh and publish automatically. Because this is a static site, it has no always-on compute cost. GitHub Actions normally runs free for public repositories. Newer VDA data is ingested when accessible and reconcilable. The workflow does not currently ingest updated brand rankings from KBA automatically; those remain visibly scoped to their reporting month.

## Architecture

```text
VDA monthly official HTML ─┐
                           ├─> Python ingestion + validation ─> market.json
KBA-sourced baseline ──────┘                                      │
                                                                  v
                                       SQL analytic windows (DuckDB)
                                                                  │
                                                                  v
                                                  Static JavaScript dashboard
                                                                  │
                                                                  v
                                                        GitHub Pages
```

## Reproducibility and data quality

Automated checks ensure that monthly counts sum to the current YTD official figure and the BEV+PHEV monthly total matches the electrified total. Data for missing months is never fabricated. If a new calendar year begins, the automation requests a manual rollover rather than blending incompatible YTD windows. Source access, preliminary figures, revision risk and licence caveats are documented.

## Technology

Python, pandas, DuckDB or local SQLite compatibility for offline analytics, SQL window functions, pytest, vanilla JavaScript, semantic HTML, modern CSS, SVG visualization, GitHub Actions and GitHub Pages. Designed with no frontend dependencies for a lightweight static site.

## License

The project code is released under the MIT licence. Source datasets retain their original attribution/licence conditions. The project is not affiliated with the data publishers.
