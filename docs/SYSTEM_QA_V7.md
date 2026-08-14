# דוח איכות ונכונות המערכת — v7

## תוצאה כללית

המערכת נבנתה מחדש לאחר audit של הנתונים, המיפויים והממשק. **22/22 בדיקות יחידה ואינטגרציה עברו**. בדיקת Chromium מלאה על כל המסכים והלשוניות הסתיימה ללא page errors, ללא console errors, ללא render errors וללא data gaps בבחירות ברירת המחדל.

## שלמות נתונים ומקורות

- 1,977/1,977 observations כוללים URL, locator, source record ID ותיעוד transformation.
- כל 39 מזהי המקורות שמופיעים בנתונים רשומים ב־Source Registry.
- כל 151 צמדי מקור–מדד ממופים למושג ולבסיס זמן.
- כל 46 המקורות, כולל 7 מקורות ללא נתונים טעונים, מופיעים במטריצת הכיסוי ובאטלס המקורות.
- אין observation ID כפול.
- אין source relationship שמחבר מקור לעצמו.
- אין Grade A ללא `definition_verified`.

## בדיקת פלסטין מול קובץ המקור

- 1,010 observations מצביעים לתא פיזי ב־sheet `prison date`.
- 1,000 observations ניתנו להשוואה ישירה של טקסט או מספר.
- **1,000/1,000 התאימו לתא המקור**.
- עשרת ה־observations הנותרים הם תיקוני audit או חישובים נגזרים, וה־transformation שלהם מתועד במפורש.

## תוצאות בדיקת דפדפן

| מסך/לשונית | view | גרפים | פערי נתונים | שגיאות render | טבלאות |
| --- | --- | --- | --- | --- | --- |
| palestine_system | view-palestine | 7 | 0 | 0 | 0 |
| palestine_institutions | view-palestine | 14 | 0 | 0 | 0 |
| palestine_governance | view-palestine | 23 | 0 | 0 | 0 |
| palestine_events | view-palestine | 27 | 0 | 0 | 0 |
| compare | view-compare | 5 | 0 | 0 | 1 |
| atlas | view-atlas | 0 | 0 | 0 | 0 |
| atlas_measures | view-atlas | 3 | 0 | 0 | 1 |
| atlas_network | view-atlas | 4 | 0 | 0 | 0 |
| map | view-map | 5 | 0 | 0 | 0 |
| data | view-data | 0 | 0 | 0 | 1 |
| quality | view-quality | 2 | 0 | 0 | 1 |
| downloads | view-downloads | 0 | 0 | 0 | 0 |

Page errors: **0**. Console errors: **0**.

## תיקוני ממשק וגרפים בבדיקת v7

- תוקנה לולאת השנים במטריצת הכיסוי הגלובלית, שיכלה לגרום ל־`Invalid array length`.
- heatmaps הוחלפו במטריצות marker אינטראקטיביות יציבות; כך נמנעת שגיאת SVG `height=NaN` בסביבת file:// וב־GitHub Pages.
- כל כרטיס גרף מתעד `ok`, `data_gap` או `render_error` במסך האיכות.
- כל נקודה בגרף מחוברת ל־observation IDs ול־provenance drawer.

## ממצאי QA היסטוריים שנותרו פתוחים

המערכת אינה מוחקת או ״מתקנת״ סתירות במקור. כרגע נשמרים: 1 critical, 1 review, 12 warnings ו־7 info. אין שורת `error`.

הממצאים כוללים:

- שנים בפלסטין שבהן total אינו מתיישב עם convicted + non-convicted.
- פער גדול בפירוק admissions של 1940.
- תווית rate מטעה בגיליון V2; המערכת מחשבת rates מחדש מן המונים והמכנים המפורשים.
- סתירות בין שדות clean/raw בשנים מסוימות, הנשמרות כחלופות עם audit note.
- rates מודפסים בטבלת East Africa 1938 שאינם מתיישבים בדיוק עם המונה והמכנה.
- הטרוגניות מטבעית במדדי finance.
- 2 observations מסוג source/proxy שאינם משמשים כ־stock אוטומטי.

## דרגות אימות

| מחלקת אימות | מספר |
| --- | --- |
| definition_verified_with_comparability_caveat | 897 |
| definition_verified_direct | 585 |
| source_traceable_definition_pending | 474 |
| source/proxy_only | 21 |

| Grade | מספר |
| --- | --- |
| B | 889 |
| A | 585 |
| U | 474 |
| D | 21 |
| C | 8 |

## מגבלות ידועות

- שבעה מקורות רשומים עדיין ללא observations טעונים; הם נשארים גלויים כ־refreshable.
- סדרות WPB ההיסטוריות הן Grade B משום שבסיס התאריך בתוך השנה אינו תמיד מפורט דיו להשוואה מדויקת ל־31 בדצמבר.
- מדדים כספיים במטבעות שונים אינם מושווים בערכים נומינליים ללא normalization.
- הגדרות U נשארות מחוץ להשוואות ישירות כברירת מחדל, אך זמינות בסייר הנתונים.

## קבצי audit

- `provenance_audit.csv`
- `source_verification_audit.csv`
- `quality_audit.csv`
- `synchronisation_audit.csv`
- `source_measure_map.csv`
- `_qa/v7_full_runtime_report.json`
