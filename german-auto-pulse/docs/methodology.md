# Methodology and caveats

## Definitions

- **New registrations**: newly registered passenger cars in Germany, not sales revenue, factory output, or all vehicle inventory.
- **BEV**: Battery-electric vehicle. **PHEV**: Plug-in hybrid. Conventional hybrids are not counted as BEV or PHEV.
- **Production**: passenger cars manufactured in Germany; manufacturer brand origin is not an equivalent classification.
- **Exports**: VDA physical factory export count. It is not Eurostat customs trade value and must not be directly subtracted from domestic new registrations.
- **Year to date**: cumulative January to latest data month, not a full year.

## Source provenance

The initial dataset is a curated, sourced **September 2026** published snapshot, with January through September monthly registration totals and an additional KBA-derived top 20 brand year-to-date list. Registrations reconcile to VDA/KBA's reported YTD total of 2,221,798. It is NOT a model-predicted dataset. Brand figures are from publicly accessible KBA-derived statistical summaries and should be verified against original KBA FZ10 files before expanded reuse.

The VDA release labels portions of the production and export data preliminary and can issue revisions. On future successful daily checks, the ingestion uses VDA's current monthly HTML table and stores a reporting-period timestamp. If schema changes or data cannot be reconciled, no updated data is committed. Brand rankings currently remain on the September 2026 snapshot until a separately verified KBA monthly parser is added. No invented brand data fills newer periods. There may be a discrepancy of 11 between VDA's YTD combined electric total and sum of its YTD BEV/PHEV subtotals, therefore only the *monthly* EV reconciliation is asserted as exact.

This is an independent portfolio project, not affiliated with VDA or KBA. Brand names are used descriptively.

## International EV market comparisons (added October 2026)

**Source**: International Energy Agency (IEA), Global EV Outlook 2026, accessed through four Our World in Data chart CSVs. The 2026 IEA publication covers annual data through 2025. View source at https://ourworldindata.org/electric-car-sales and https://www.iea.org/reports/global-ev-outlook-2026 .

**Data series**: `electric-car-sales-share` (BEV + PHEV share of all new car sales); `electric-car-sales` (BEV + PHEV sales volume); `bev-share-new-ev` (BEV proportion of EV sales); `share-car-stocks-electric` (EV share of passenger-car stock). The international analytical tables use 2020–2025 full calendar years and retain missing values rather than interpolating. All data are rounded to no more than 3 decimals for published JSON and are not fabricated or extrapolated.

**Percentage points versus percentage change**: 2024 Germany EV share of 20% versus 2025 share of 30% is **+10 percentage points**, not +10% relative growth. The same comparison is +50% as a relative increase, but the interface intentionally emphasizes pp changes to prevent misreading. For vehicle volumes, changes are expressed in units rather than pp.

**International sales versus German registrations**: The Germany tabs use a different set of reporting agencies and more recent partial-year monthly data; they cannot be compared directly to full-year international IEA results. The international leaderboard applies one IEA methodology to all compared countries and years.

**Manufacturing versus market size**: EV sales are not the same as domestic production, automaker headquarters, export revenues, profit or domestic vehicle registrations. Production can be added to the international comparison only after adopting a suitably harmonized production source and consistent vehicle definitions. No global manufacturing quantities are implied by the EV leaderboard.

**Coverage**: 32 country markets, plus World and EU (27) aggregates used for global benchmarks. Year availability depends on individual observations. Missing observations are explicitly marked as unavailable, not zero. IEA data are occasionally revised by OWID on publication of the subsequent edition.

**Refresh and source checks**: `pipeline.global_ev` downloads all four CSVs from OWID and validates market coverage, plausible shares, latest year, and metric completeness for key countries before committing the refreshed dataset. CI requires passing unit tests. The public Vercel deployment has its own publication lifecycle; an up-to-date GitHub data file is not proof the deployed site has refreshed.
