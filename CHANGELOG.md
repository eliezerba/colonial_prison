# Changelog

## v7 — complete source–measure mapping and connected research interface

- Rebuilt the canonical layer around 19 research concepts and 92 raw measures.
- Registered 46 sources; loaded 39; kept 7 refreshable sources visible rather than dropping them.
- Mapped all 151 loaded source–measure pairs and all 1,977 observations.
- Added source, measure and concept atlases; source–concept network; source detail views; connected maps; complete Data Explorer; and observation-level related-data links.
- Expanded the Palestine dashboard to 27 interactive plots/timelines across system flows, institutions, labour, discipline, recidivism, detention and events.
- Added synchronized period comparisons with Palestine fixed as the analytical baseline.
- Enforced complete source URL, locator, source record ID and transformation for every observation.
- Corrected the global coverage year loop and replaced unstable Plotly raster heatmaps with interactive square-marker matrices.
- Added reusable `ui/` templates so data rebuilds do not overwrite the v7 interface.
- 22 automated tests pass; full Chromium QA reports no page, console, render or default-view data-gap errors.

## v4 — Palestine-centered quality audit and source expansion

- Made Mandatory Palestine the fixed baseline of every comparison view and the visual reference on maps.
- Comparison Lab can no longer remove Palestine; it stops when Palestine lacks a comparable observation.
- Pinned Palestine first in overview/coverage views and highlighted it in comparative traces.
- Replaced silent comparator omissions with explicit data-gap messages.
- Added full data QA: preferred-observation uniqueness, rate arithmetic, source-universe checks, component reconciliation and proxy/unit guards.
- Corrected Canada `Z175–182` from `admissions_total` to `admissions_male`.
- Audited Palestine V2 mislabeled per-1,000 series and recomputed canonical rates from explicit numerators/denominators.
- Preserved and downgraded the duplicate equivalent 1941 Palestine daily-average field.
- Preserved source-reported East Africa 1938 rates separately and recomputed canonical rates from population/daily average.
- Added loaded data from England & Wales, British India Hansard, Aden and Bombay Presidency.
- Added structured historical series from Jamaica, Mauritius and Malta.
- Expanded New Zealand historical tables and retained DSAL British India as verified-but-refreshable when XLS download is unavailable.
- Current bundled build: 1,865 observations, 23 jurisdictions, 18 loaded source datasets.
- 27 automated tests pass; JavaScript syntax passes; QA contains no `error` rows.

## v6 - source verification run (2026-08-14)
- Preserved v5 HTML/CSS structure exactly.
- Enforced complete row-level provenance in the build.
- Added `provenance_audit.csv` and `source_verification_audit.csv`.
- Added cell-level Palestine snapshot fidelity test.
- Added Cyprus, Trinidad & Tobago, Fiji, Sierra Leone, Bermuda, Barbados, Bahamas, Gold Coast, Gambia, Bechuanaland, British Guiana, Basutoland, Solomon Islands and Dominica historical structured series.
- Extended NZ AJHR with 1924/25-1929/30 finance measures.
- Re-audited refreshable DSAL, Queensland, ReShare and WA sources; no fabricated values added.
- 28 automated tests passing.
