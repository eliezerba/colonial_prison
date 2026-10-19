# Colonial Prison Statistics Explorer v8 — Data expansion and source decisions

## Scope and version policy

Version 8 is a data-and-statistical-quality upgrade to v7. It **preserves the seven-section v7 UI, all Palestine source records and all previously mapped sources**. It does not introduce unreviewed new measures into the Palestinian corpus. The site runs entirely from bundled static files, and the build is reproducible offline.

| Item | v7 | v8 | Note |
|---|---:|---:|---|
| Canonical observations | 1,977 | 2,248 | +271 net = 289 v8 curated rows minus 18 E&W legacy rows reclassified/replaced |
| Jurisdictions | 41 | 43 | Scotland and Northern Ireland added |
| Registered source datasets | 46 | 50 | Four source IDs added: Scotland, Northern Ireland, Basutoland official report, Uganda historic WPB |
| Loaded source datasets | 39 | 43 | Seven existing un-ingested/refreshable datasets remain identified |
| Raw measures | 92 | 107 | Definitions and sex / conviction / age categories retained, not collapsed |
| Research concepts | 19 | 19 | v7 taxonomy preserved |
| Palestine observations | 1,135 | 1,135 | No Palestinian source rows deleted or silently changed |

The **289 new curated observations** comprise:

| Source | New rows | Years | Value and caveat |
|---|---:|---|---|
| England & Wales / EAW_PARL_HIST | 99 | 1900; 1910; annually 1920–1950 | 12 monthly end-of-month snapshots averaged; NOT a daily mean; disaggregated female/male/total |
| Scotland / SCT_UK_PARL_2017 | 31 | 1920–1950 | Historical published annual prison population means |
| Northern Ireland / NIR_AAS_1937_47 | 110 | 1937–1947 | Admissions, sex, daily avg convicted/unconvicted, convicted persons and previous proved offences |
| New Zealand / NZ_AJHR_PRISONS | 30 | 1932–1938 | Receptions net of transfers, distinct persons, daily avg, rate per 10,000; plus gross/transfer totals for 1938 |
| Hong Kong / HKG_ADMIN | 8 | 1931–1933, 1939, 1946 | Committals, daily average, juveniles; postwar **sentenced-only** daily mean |
| Basutoland / BAS_COL_REPORT_1937 | 6 | 1936–1937 | Total admissions, penal-commitment subset, **adult-only** daily average |
| Uganda / UGA_WPB_HIST | 5 | 1921, 1927, 1934, 1938, 1944 | Source-specific historical population points; **blocked from comparisons and mapped aggregate statistics** |
| **Total** | **289** | | |

## Primary/secondary sources and exact locators

1. **England & Wales:** House of Commons Library, *Prison Population Statistics*, Table 1a, printed p.19. https://researchbriefings.files.parliament.uk/documents/CBP-8161/CBP-8161.pdf . Mean of the 12 end-of-month counts, not a mean of 365 daily observations. All 18 `avg_daily_*` v7 observations attributed to this historical source were removed and replaced by the new, explicitly named `avg_month_end_male/female/total` series (99 observations). Original row list archived as `docs/EAW_V7_RECLASSIFICATION_AUDIT.csv`.
2. **Scotland:** House of Commons Library, *Historical Scottish Prison Population*, Table 10a, printed p.39, archived mirror of 2017 SN04334. https://www.breizh-info.com/wp-content/uploads/2017/11/SN04334.pdf . Values 1920–1950, daily-average population. Mirrored document provenance is stated rather than disguising this as an original governmental host.
3. **New Zealand:** *Prisons Department Report* (1938–39), retrospective receptions table for 1932–1938 and narrative for 1938. https://paperspast.natlib.govt.nz/parliamentary/AJHR1939-I.2.3.2.23 . **1938**: gross receipts 4,328 − transfers 792 = net receptions 3,536; distinct people received 2,224; daily mean 870. Receptions, admissions, persons and daily mean are not interchangeable. **1937 source discrepancy**: retrospective table daily mean 860; narrative cites 866. Data preserve 860 with QA warning rather than merging the figures.
4. **Northern Ireland:** *Annual Abstract of Statistics 1937–1947*, Tables 72–73, printed p.68. https://escoe-website.s3.amazonaws.com/wp-content/uploads/2022/12/11173048/Annual-Abstract-of-Statistics-1937-1947.pdf . Across all 11 reported years, male + female receptions = total receptions and convicted + unconvicted daily mean = overall daily mean. The percentage of convicted men with previously proved offences is an **historical characteristic of entrants/convicted persons**, **not** a measured future recidivism rate.
5. **Hong Kong:** transcribed colonial Annual Reports 1931–39 at https://www.histsyn.com/2023/02/CAR1931-1939.html and later 1946 report https://www.histsyn.com/2023/01/EYB1946.html . Descriptive occupations of work are not presented as numbers of prison laborers. Daily average for 1946 concerns *sentenced persons only*, and cannot substitute for system-wide daily average.
6. **Basutoland:** Official colonial annual report 1937, prisons, printed p.42. https://libsysdigi.library.illinois.edu/ilharvest/Africana/Books2011-05/469256/469256_1937/469256_1937_opt.pdf . Annual admissions and adult daily averages for 1936/37, with adult-only qualification.
7. **Uganda:** World Prison Brief historical series https://prisonstudies.org/country/uganda?language_content_entity=en-gb . Published 1938 historical total 1,318, compared with *different source's* 1938 colonial table daily average 4,225 (`EAF_1938_JSH`). A numerical discrepancy **does not establish** the error or explain whether institution inclusion, date, or definition differs. Grade U records remain searchable in the source atlas and data explorer; an explicit `blocked_from_comparison` flag prevents their use in comparison labs and maps.

## Comparison rules and limitations

- Raw `measure`, `concept_id`, `time_basis`, units, legal status and sex are all preserved. Concepts group related questions; they do **not** establish that two observations use identical populations or periods.
- `avg_month_end_total` is eligible for **qualified concept-level population-average comparisons** with Palestine's daily mean, but the interface warns of the underlying timing difference. It is not silently relabelled to `avg_daily_total`.
- `avg_daily_adults` (Basutoland), `avg_daily_sentenced` (Hong Kong), `avg_daily_convicted` / `avg_daily_unconvicted` (Northern Ireland) remain distinct and are not inserted into the aligned **total daily mean** series by automatic measure preference.
- `male_convicted_prior_offences_pct` is not `recidivism_rate_pct` and is not in the automated recidivism alignment preference.
- Uganda's restricted historical series **must never be considered a validated comparable population stock** until the annual-report discrepancy has been resolved.
- Sources tagged refreshable remain discoverable in the atlas but are not misrepresented as ingested data. They are `IND_DSAL`, `QLD_PHOTO`, `QLD_TOOWOOMBA`, `QLD_BRISBANE`, `IRL_REGISTERS`, `WA_BLUEBOOKS`, `GUY_MNS`.

## Provenance, audit and reproduction

All 2,248 observations have `source_url`, source table/sheet locator, `source_record_id` and `transformation`. The version-8 curated data snapshot is committed at `pipeline/snapshots/v8_verified_snapshots.csv`. Its generation script is `pipeline/generate_v8_data.py`. The full site is rebuilt **without network calls** using:

```bash
python pipeline/enrich_v8.py
node --check site/assets/app.js
python -m unittest discover -s tests -v
```

Manual transcriptions were checked against the published web-rendered tables and internally cross-checked for arithmetical reconciliation; this is **not a complete independent source-image rekeying by two transcribers**. Source-specific inconsistencies are not erased. See `docs/V8_QA_REPORT.md` and downloadable row-level `provenance_audit.csv`.
