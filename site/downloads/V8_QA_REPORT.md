# V8 system and data QA — 19 October 2026

## What was actually tested

- Offline data pipeline rebuild and publication from original v7 source project, including all original 1,135 Palestine observations.
- Total observation count, uniqueness and complete source, locator, record ID and transformation traceability.
- All registered sources accounted for, including 7 sources without extracted observations; all source–measure pairs mapped to one of 19 research concepts.
- Corrected E&W `avg_month_end_*` semantics and 33-year male + female = total reconciliation.
- Complete 1920–1950 Scotland time sequence; 1938 1,543 daily-average cross-check.
- New Zealand 1938 gross − transfer = net receipts, distinct-person and daily-average distinction; discrepancy in 1937 preserved.
- Northern Ireland yearly admissions and daily-average sex/status reconciling; separate conviction history percentage definition.
- Hong Kong 1946 sentenced-only mean and Basutoland adults-only mean excluded from generic total daily mean alignment.
- Uganda five source-specific historical records excluded from **comparison lab and spatial comparison map** and `comparison_eligible=False` in exported CSV; 1938 conflicting value surfaced as explicit critical source research issue.
- Legacy Palestinian workbook cell-fidelity test against the bundled workbook (more than 750 checked entries).
- JavaScript syntax validation, static file presence and links, source/data/mapping QA.
- Browser load and navigation through seven main views using Chromium Playwright `set_content` with all site assets inlined (navigation to `file://` is administrator-blocked in this runtime). Verified rendering, loaded observation count and absence of page/console errors. This is not a network deployment smoke-test.

## Outstanding research issues (not masked as test passes)

- **Uganda 1938:** 1,318 in WPB vs 4,225 in the colonial comparative table, with potentially different statistic/definition. Neither number was fabricated or suppressed. The WPB source is searchable but specifically barred from comparisons and map aggregates pending verification.
- **New Zealand 1937:** historical table gives 860 daily average, narrative gives 866; table value retained with a review flag.
- **England & Wales:** full data series uses month-end mean rather than daily mean; compare view displays a time-basis caveat.
- **Northern Ireland:** prior-offence percentages are not directly equivalent to Palestinian recidivism indicators.
- **Basutoland, Hong Kong:** specified populations differ from whole-system totals.
- **Palestine:** source totals/components conflicts and V2 source label error documented from v7; preserved, not silently reconciled.
- **Seven refreshable datasets** remain visible without ingestion; live source downloads are unavailable in this build environment, so the curated bundled data are the actual deliverable.

## Reproduction commands

```bash
python pipeline/enrich_v8.py
node --check site/assets/app.js
python -m unittest discover -s tests -v
```

Data available in `site/downloads/`. This note distinguishes technical success and basic arithmetic cross-checks from full historical-definition equivalence. Historic documents/HTML transcriptions were not independently rekeyed against source page scans by two researchers; conclusions should be cited at source-table level and audited before publication.

## Additional visual QA limit

The initial browser run confirmed successful navigation of all seven main sections and the later focused run verified a Scotland comparison plot, the England & Wales comparability caveat, Northern Ireland atlas lookup and Uganda data visibility, with zero page/console errors and zero registered render errors across 19 initialized chart states. A subsequent *exhaustive* attempt to load every Palestine and atlas chart tab ran into the browser test environment's time limit. **This exhaustive chart-by-chart pass is not claimed as completed**, and actual GitHub Pages deployment remains to be checked in a live browser.
