# Colonial Prison Statistics Explorer — v8.2

מערכת מחקרית סטטית עם פלסטין המנדטורית במרכז. v8.2 משמרת את נתוני v8 ואת כל שבעת המסכים והגרפים, ומוסיפה שכבת עיצוב וניווט.

## פרסום GitHub Pages

1. חילצו את הארכיון והעלו **את תוכן** התיקייה `colonial_prison_explorer_v8_2` לשורש המאגר, ולא את התיקייה המקיפה עצמה.
2. ודאו שקיימים בשורש: `index.html`, `.github/workflows/pages.yml`, `pipeline/`, `ui/`, `site/`.
3. ב־Settings → Pages בחרו Source: **GitHub Actions**.
4. בצעו Push ל־`main` (או `master`). GitHub Actions יבנה ויפרסם את `site/`, וכתובת ה־Pages תיפתח ב־`index.html` של האתר.
5. מקומית ניתן לפתוח `index.html` בשורש, שמפנה ל־`site/index.html`. אם הדפדפן חוסם קובצי JS מקומיים, הפעילו `python -m http.server 8000` ופתחו `http://localhost:8000/`.

**חשוב:** אין להעלות רק את `index.html` או רק את `ui/`. ללא קובצי `site/data/` הגרפים לא יעבדו.

## תכונות

- שבעה מסכים: פלסטין, השוואה, אטלס מקורות, מפה, נתונים, איכות וקישוריות, הורדות.
- כל התצפיות, הגרפים, המיפויים, מקורות הנתונים ומסנני הזמן של v8 נשמרו.
- חיפוש מהיר (Ctrl+K), מעבר ישיר לנושאים ולגרפים, מדריך שימוש קצר, תצוגה רספונסיבית, ניווט ברור ועיצוב קריא.
- לוגו מעבדת אליהו מתוך תיקיית הלוגו המקורית ב־Drive, מוטמע כ־SVG מקומי.
- מקור אמת לממשק: `ui/index.html`, `ui/styles.css`, `ui/assets/explorer-ux.js`; בנייה מחדש מעתיקה אותם ל־`site/`.

## בנייה ובדיקה

```bash
pip install -r pipeline/requirements.txt
python pipeline/enrich_v8.py
node --check site/assets/app.js
node --check site/assets/explorer-ux.js
python -m unittest discover -s tests -v
```

ראו גם `docs/DATA_EXPANSION_V8.md` ו־`docs/V8_QA_REPORT.md` לתיעוד קליטת הנתונים ולסייגים המחקריים.


## גרסה 8.2
נוסף מתג עברית/English בממשק, תוקנה היררכיית הפונטים הראשיים, ושמורות כל שבע התצוגות וכל רכיבי הגרפים. אפשר להעלות את תוכן התיקייה לשורש מאגר GitHub Pages.
