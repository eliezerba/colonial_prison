# מיפוי המקורות, המדדים והמושגים — v7

## מטרת המיפוי

מסמך זה מתעד את שכבת הסנכרון שעליה נשענת המערכת. המטרה אינה לכפות על מקורות היסטוריים שונים הגדרה אחידה מלאכותית, אלא לשמור כל observation במונחי המקור שלו, ולחבר אותו למושג מחקרי, לבסיס זמן, ליחידה ולדרגת השוואה מתועדת.

## תמונת מצב

- **1,977 observations**.
- **41 מרחבים**.
- **46 מקורות רשומים**, מהם **39 טעונים** ו־**7 refreshable**.
- **92 מדדים גולמיים**.
- **19 מושגים מחקריים**.
- **151 צמדי מקור–מדד ממופים**.
- **1,135 observations של פלסטין**, ב־58 מדדים וב־27 מוסדות/יחידות בעלי שם.

## כללי הסנכרון

1. **Stock, average ו־flow אינם מתאחדים.** `stock_eoy_total`, `population_point_total`, `avg_daily_total` ו־`admissions_total` נשמרים כמדדים נפרדים.
2. **מושג משותף אינו שקילות.** מקור יכול להיות מחובר לאותו concept בלי שהערכים שלו יהיו חלופות זהות.
3. **שקילות מדויקת דורשת התאמה מלאה** של מרחב, שנה, תקופת דיווח, תאריך ייחוס, רמת גאוגרפיה, מוסד, מדד, בסיס זמן, סטטוס משפטי, מין, גיל, קבוצת עונש, סטטוס עבודה ויחידה.
4. **אין בחירה שקטה בין מקורות.** מנגנון ה־preferred observation משתמש ב־Grade, אימות ההגדרה וסוג המקור; כל החלופות נשארות בסייר הנתונים וב־provenance.
5. **פלסטין היא נקודת הייחוס.** השוואה מיושרת נעצרת אם אין observation פלסטיני מתאים.
6. **יחידות כספיות אינן מומרות אוטומטית.** השוואת finance גולמית נחסמת או מסומנת כאשר המטבעות אינם אחידים.
7. **Proxy נשאר proxy.** אינדקסי רשומות אישיים אינם מומרים אוטומטית ל־prison population.

## מילון המושגים

| concept_id | תווית | observations | מדדים | מקורות | מרחבים |
| --- | --- | --- | --- | --- | --- |
| custodial_population_total | אוכלוסיית כלואים – נקודת זמן | 518 | 2 | 31 | 30 |
| custodial_population_average | אוכלוסיית כלואים – ממוצע | 326 | 5 | 11 | 16 |
| finance | הוצאות והכנסות | 202 | 9 | 4 | 4 |
| admissions_flow | קבלות וכניסות | 199 | 9 | 7 | 6 |
| custodial_population_composition | הרכב אוכלוסיית הכלואים | 139 | 5 | 2 | 2 |
| movement_and_outcomes | תנועות ותוצאות | 105 | 7 | 1 | 1 |
| population_rate | שיעורי כליאה | 95 | 8 | 8 | 12 |
| discipline_and_punishment | משמעת וענישה | 70 | 8 | 2 | 2 |
| recidivism | רצידיביזם | 69 | 12 | 2 | 2 |
| prison_labour | עבודת אסירים | 60 | 6 | 2 | 2 |
| special_detention | מעצר מיוחד ומנהלי | 55 | 8 | 1 | 1 |
| sentence_structure | מבנה עונשים | 49 | 2 | 1 | 1 |
| national_population | אוכלוסייה כללית | 37 | 1 | 3 | 9 |
| qualitative_notes | הערות איכותניות | 23 | 1 | 1 | 1 |
| capacity_and_occupancy | קיבולת ותפוסה | 14 | 1 | 1 | 1 |
| institutions | מוסדות ומבנה מערכתי | 7 | 2 | 1 | 1 |
| demography | מאפיינים דמוגרפיים | 5 | 2 | 2 | 2 |
| source_proxy | Proxy / אינדקס מקור | 2 | 2 | 2 | 2 |
| other | אחר | 2 | 2 | 2 | 2 |

## רישום כל המקורות

כל המקורות הרשומים מופיעים באטלס המקורות. מקור שלא נטען אינו נעלם: הוא מופיע כ־refreshable עם קישור, אסטרטגיית ingest ומצב טעינה.

| source_id | מרחב | מצב | observations | שנים | מושגים טעונים | רמת ראיה | קישור |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ADEN_QDL_ADMIN | Aden | loaded | 6 | 1921.0–1921.0 | אוכלוסיית כלואים – ממוצע / הוצאות והכנסות / עבודת אסירים / קבלות וכניסות | A/B | https://www.qdl.qa/en/archive/81055/vdc_100148842067.0x000014 |
| AUS_ABS_HIST | Australia | loaded | 33 | 1900.0–1950.0 | שיעורי כליאה / אוכלוסיית כלואים – ממוצע / אוכלוסייה כללית | A/B | https://www.abs.gov.au/ausstats/abs%40.nsf/Lookup/4524A092E30E4486CA2569DE00256331 |
| BHS_WPB_HIST | Bahamas | loaded | 4 | 1932.0–1950.0 | אוכלוסיית כלואים – נקודת זמן | B | https://www.prisonstudies.org/country/bahamas?language_content_entity=en-gb |
| BRB_WPB_HIST | Barbados | loaded | 4 | 1929.0–1950.0 | אוכלוסיית כלואים – נקודת זמן | B | https://prisonstudies.org/country/barbados |
| BAS_WPB_HIST | Basutoland | loaded | 2 | 1937.0–1945.0 | אוכלוסיית כלואים – נקודת זמן | B | https://prisonstudies.org/country/lesotho |
| BEC_WPB_HIST | Bechuanaland | loaded | 1 | 1938.0–1938.0 | אוכלוסיית כלואים – נקודת זמן | B | https://prisonstudies.org/country/botswana |
| BMD_WPB_HIST | Bermuda | loaded | 3 | 1920.0–1950.0 | אוכלוסיית כלואים – נקודת זמן | B | https://www.prisonstudies.org/country/bermuda-united-kingdom |
| BOM_QDL_ADMIN | Bombay Presidency | loaded | 6 | 1923.0–1923.0 | אוכלוסיית כלואים – ממוצע / משמעת וענישה / מאפיינים דמוגרפיים / אוכלוסיית כלואים – נקודת זמן / אחר | A/B | https://www.qdl.qa/en/archive/81055/vdc_100152998489.0x00005e |
| EAF_1938_JSH | British African colonies | loaded | 28 | 1938.0–1938.0 | שיעורי כליאה / אוכלוסיית כלואים – ממוצע / אוכלוסייה כללית | B/C | https://doi.org/10.1093/jsh/shaf099 |
| BGU_WPB_HIST | British Guiana | loaded | 4 | 1921.0–1947.0 | אוכלוסיית כלואים – נקודת זמן | B | https://prisonstudies.org/country/guyana |
| IND_HANSARD_ADM | British India | loaded | 27 | 1920.0–1928.0 | קבלות וכניסות | A/B | https://hansard.parliament.uk/Commons/1930-11-06/debates/9ec4e995-09f7-475d-a234-ba0b2f3b5d15/WrittenAnswers |
| NGA_AO | British Nigeria | loaded | 57 | 1920.0–1938.0 | אוכלוסיית כלואים – ממוצע | A/B | https://www.nber.org/papers/w31637 |
| CAN_HSC_Z | Canada | loaded | 361 | 1900.0–1950.0 | קבלות וכניסות / אוכלוסיית כלואים – ממוצע / הוצאות והכנסות / אוכלוסיית כלואים – נקודת זמן | A/B | https://www150.statcan.gc.ca/n1/pub/11-516-x/sectionz/4147446-eng.htm |
| CEYLON_WPB_HIST | Ceylon | loaded | 5 | 1920.0–1938.0 | אוכלוסיית כלואים – נקודת זמן | B | https://www.prisonstudies.org/country/sri-lanka?language_content_entity=en-gb |
| CYP_WPB_HIST | Cyprus | loaded | 7 | 1920.0–1950.0 | אוכלוסיית כלואים – נקודת זמן | B | https://prisonstudies.org/country/cyprus-republic?language_content_entity=en-gb |
| DMA_WPB_HIST | Dominica | loaded | 4 | 1933.0–1950.0 | אוכלוסיית כלואים – נקודת זמן | B | https://prisonstudies.org/country/dominica |
| EAW_PARL_HIST | England & Wales | loaded | 18 | 1900.0–1950.0 | אוכלוסיית כלואים – ממוצע | A/B | https://publications.parliament.uk/pa/cm201314/cmselect/cmjust/92/92vw47.htm |
| FIJ_WPB_HIST | Fiji | loaded | 1 | 1920.0–1920.0 | אוכלוסיית כלואים – נקודת זמן | B | https://prisonstudies.org/country/fiji |
| GMB_WPB_HIST | Gambia | loaded | 4 | 1922.0–1950.0 | אוכלוסיית כלואים – נקודת זמן | B | https://prisonstudies.org/country/gambia?language_content_entity=en-gb |
| GCO_WPB_HIST | Gold Coast | loaded | 3 | 1920.0–1937.0 | אוכלוסיית כלואים – נקודת זמן | B | https://prisonstudies.org/country/ghana?language_content_entity=en-gb |
| HKG_ADMIN | Hong Kong | loaded | 27 | 1924.0–1949.0 | קבלות וכניסות / אוכלוסיית כלואים – ממוצע / אוכלוסיית כלואים – נקודת זמן | A/B | https://digitalrepository.lib.hku.hk/catalog/pc28gw81r |
| IRL_WPB_TREND | Ireland | loaded | 12 | 1922.0–1950.0 | שיעורי כליאה / אוכלוסיית כלואים – נקודת זמן | B | https://prisonstudies.org/country/ireland-republic?language_content_entity=en-gb |
| JAM_WPB_HIST | Jamaica | loaded | 7 | 1920.0–1950.0 | אוכלוסיית כלואים – נקודת זמן | B | https://www.prisonstudies.org/country/jamaica?language_content_entity=en-gb |
| KEN_WPB_TREND | Kenya | loaded | 5 | 1928.0–1948.0 | שיעורי כליאה / אוכלוסיית כלואים – נקודת זמן | B | https://www.prisonstudies.org/country/kenya |
| MLT_WPB_HIST | Malta | loaded | 5 | 1921.0–1950.0 | אוכלוסיית כלואים – נקודת זמן | B | https://www.prisonstudies.org/country/malta?language_content_entity=en-gb |
| PAL_V2 | Mandatory Palestine | loaded | 1135 | 1921.0–1948.0 | קבלות וכניסות / שיעורי כליאה / מאפיינים דמוגרפיים / אוכלוסיית כלואים – ממוצע / מעצר מיוחד ומנהלי / מבנה עונשים / תנועות ותוצאות / משמעת וענישה / אחר / עבודת אסירים / אוכלוסייה כללית / הוצאות והכנסות / מוסדות ומבנה מערכתי / רצידיביזם / הערות איכותניות / הרכב אוכלוסיית הכלואים / אוכלוסיית כלואים – נקודת זמן | A/B | https://docs.google.com/spreadsheets/d/10vGVgHP7JdODpGXGYcmaavthDNfoTCJo6hMO_u5CSTE/edit?usp=sharing |
| MUS_WPB_HIST | Mauritius | loaded | 4 | 1920.0–1948.0 | אוכלוסיית כלואים – נקודת זמן | B | https://www.prisonstudies.org/country/mauritius?language_content_entity=en-gb |
| NZ_AJHR_PRISONS | New Zealand | loaded | 55 | 1925.0–1930.0 | קבלות וכניסות / אוכלוסיית כלואים – ממוצע / שיעורי כליאה / הוצאות והכנסות / אוכלוסיית כלואים – נקודת זמן | A/B | https://paperspast.natlib.govt.nz/parliamentary/AJHR1930-I.2.3.2.23 |
| NZ_OYB | New Zealand | loaded | 125 | 1919.0–1943.0 | קבלות וכניסות / אוכלוסיית כלואים – ממוצע / רצידיביזם / קיבולת ותפוסה / הרכב אוכלוסיית הכלואים / אוכלוסיית כלואים – נקודת זמן | A/B | https://www3.stats.govt.nz/New_Zealand_Official_Yearbooks/1920/NZOYB_1920.html |
| MWI_WPB_TREND | Nyasaland | loaded | 4 | 1928.0–1950.0 | שיעורי כליאה / אוכלוסיית כלואים – נקודת זמן | B | https://prisonstudies.org/country/malawi |
| QLD_STHELENA | Queensland – St Helena Penal Establishment | loaded | 1 | 1936.0–1936.0 | Proxy / אינדקס מקור | C/D | https://www.data.qld.gov.au/dataset/st-helena-prisoner-index-1863-to-1936 |
| SLE_WPB_HIST | Sierra Leone | loaded | 3 | 1920.0–1938.0 | אוכלוסיית כלואים – נקודת זמן | B | https://prisonstudies.org/country/sierra-leone?language_content_entity=en-gb |
| SGP_WPB_TREND | Singapore | loaded | 1 | 1947.0–1947.0 | אוכלוסיית כלואים – נקודת זמן | B | https://www.prisonstudies.org/country/singapore?language_content_entity=en-gb |
| SLB_WPB_HIST | Solomon Islands | loaded | 2 | 1931.0–1938.0 | אוכלוסיית כלואים – נקודת זמן | B | https://prisonstudies.org/country/solomon-islands |
| ZAF_WPB_TREND | South Africa | loaded | 2 | 1936.0–1936.0 | שיעורי כליאה / אוכלוסיית כלואים – נקודת זמן | B | https://www.prisonstudies.org/country/south-africa |
| SWZ_WPB_TREND | Swaziland | loaded | 1 | 1938.0–1938.0 | אוכלוסיית כלואים – נקודת זמן | B | https://prisonstudies.org/country/eswatiniswaziland |
| TZA_WPB_TREND | Tanganyika | loaded | 4 | 1927.0–1946.0 | אוכלוסיית כלואים – נקודת זמן | B | https://prisonstudies.org/country/tanzania |
| TAS_PRISONERS | Tasmania – Hobart Gaol | loaded | 1 | 1938.0–1938.0 | Proxy / אינדקס מקור | C/D | https://data.gov.au/data/dataset/d2c27ee7-8be8-425b-a028-b96ef3847fac |
| TTO_WPB_HIST | Trinidad & Tobago | loaded | 5 | 1920.0–1950.0 | אוכלוסיית כלואים – נקודת זמן | B | https://www.prisonstudies.org/country/trinidad-tobago?language_content_entity=en-gb |
| GUY_MNS | British Guiana / Guyana | refreshable | 0 | — | טרם נטען | C/D | https://reshare.ukdataservice.ac.uk/856077/ |
| IND_DSAL | British India | refreshable | 0 | — | טרם נטען | C/D | https://dsal.uchicago.edu/statistics/1910_excel/index.html |
| IRL_REGISTERS | Ireland under British rule | refreshable | 0 | — | טרם נטען | C/D | https://reshare.ukdataservice.ac.uk/857702/ |
| QLD_BRISBANE | Queensland, Australia | refreshable | 0 | — | טרם נטען | C/D | https://www.data.qld.gov.au/dataset/register-of-prisoners-gaol-brisbane-1850-1901 |
| QLD_PHOTO | Queensland, Australia | refreshable | 0 | — | טרם נטען | C/D | https://www.data.qld.gov.au/dataset/photographic-records-of-prisoners-1875-1936 |
| QLD_TOOWOOMBA | Queensland, Australia | refreshable | 0 | — | טרם נטען | C/D | https://www.data.qld.gov.au/dataset/indextoprisonerstriedtoowoomba1864-1903-csv |
| WA_BLUEBOOKS | Western Australia | refreshable | 0 | — | טרם נטען | C/D | https://research-repository.uwa.edu.au/en/datasets/wa-blue-books/ |

## מקורות שעדיין ממתינים ל־ingest

| source_id | שם | מרחב | סיבה/סטטוס | קישור |
| --- | --- | --- | --- | --- |
| IND_DSAL | Statistical Abstract relating to British India - DSAL Excel series | British India | ready for XLS parser | https://dsal.uchicago.edu/statistics/1910_excel/index.html |
| QLD_PHOTO | Photographic records of prisoners 1875-1936 | Queensland, Australia | candidate | https://www.data.qld.gov.au/dataset/photographic-records-of-prisoners-1875-1936 |
| QLD_TOOWOOMBA | Toowoomba prison records 1864-1906 | Queensland, Australia | low chronological priority | https://www.data.qld.gov.au/dataset/indextoprisonerstriedtoowoomba1864-1903-csv |
| QLD_BRISBANE | Brisbane Gaol Prisoners 1850-1901 | Queensland, Australia | low chronological priority | https://www.data.qld.gov.au/dataset/register-of-prisoners-gaol-brisbane-1850-1901 |
| IRL_REGISTERS | General Prison Registers for Two Irish Prisons, 1840-1910 | Ireland under British rule | available | https://reshare.ukdataservice.ac.uk/857702/ |
| WA_BLUEBOOKS | WA Blue Books dataset | Western Australia | partial prison relevance | https://research-repository.uwa.edu.au/en/datasets/wa-blue-books/ |
| GUY_MNS | Mental, Neurological, and Substance Abuse Disorders in Guyana's Jails, 1825-2022 | British Guiana / Guyana | do not ingest into population panel until structured variables verified | https://reshare.ukdataservice.ac.uk/856077/ |

## שכבות מכונה

- `site/downloads/observations.csv` — הטבלה הקנונית.
- `source_registry.csv` — רישום המקורות.
- `measure_registry.csv` — מילון 92 המדדים.
- `concept_registry.csv` — מילון 19 המושגים.
- `source_measure_map.csv` — כל צמדי מקור–מדד.
- `source_concept_coverage.csv` — מטריצת מקור–מושג, כולל מקורות ללא observations.
- `source_relationships.csv` — קשרים בין מקורות שונים באותו מרחב ומושג.
- `observation_equivalence_groups.csv` — חלופות מדויקות בלבד; כרגע אין קבוצה שעומדת בכל תנאי השקילות.
- `provenance_audit.csv` — audit ברמת כל observation.
- `synchronisation_audit.csv` — בדיקות שלמות המיפוי.

## חזרה למקור

כל observation כולל `source_url`, `source_locator`, `source_record_id` ו־`transformation`. לחיצה על נקודה בגרף פותחת drawer שמציג את כל ארבעת השדות, את שדה המקור, Grade, quality flags, observations קשורים ומקורות מקבילים.
