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
