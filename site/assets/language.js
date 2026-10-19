(()=>{'use strict';
// UI localization only: source values, archival titles, provenance, and raw data remain unchanged.
const dict={
'אטלס נתוני כליאה היסטוריים':'Historical incarceration statistics atlas','פלסטין כמקרה הייחוס':'Palestine as the reference case',
'פלסטין · מקרה הייחוס':'Palestine · reference case','חיפוש בכל המערכת':'Search the atlas',
'מרחב מחקר':'Research workspace','בחרו במה תרצו לעיין':'Choose an area to explore',
'פלסטין':'Palestine','הדשבורד המרכזי':'Main dashboard','השוואה':'Comparison','פלסטין מול מרחבים אחרים':'Palestine and comparators',
'אטלס מקורות':'Source atlas','כל מקור וכל מדד':'Every source and measure','מפה':'Map','מרחבים ומוסדות':'Regions and facilities',
'נתונים':'Data','כל ה־observations':'All observations','איכות וקישוריות':'Quality & links','הורדות':'Downloads','CSV ותיעוד':'CSV & documentation',
'איך משתמשים?':'How to use','בחרו נושא, הגדירו שנים, ולחצו על נקודה בגרף כדי להגיע למקור.':'Choose a topic and years, then click a chart point to inspect its source.',
'מדריך שימוש קצר ↗':'Quick guide ↗','מחקר היסטורי':'Historical research','? הסבר למשתמש':'? User guide',
'מה השתנה במערכת הכליאה של פלסטין, ואיך מתחברים אוכלוסייה, admissions, מוסדות, עבודה, משמעת ומעצר מנהלי?':'How did incarceration in Palestine change, and how do population, admissions, institutions, labour, discipline and administrative detention relate?',
'כל גרף במסך זה מבוסס על נתוני פלסטין. לחיצה על נקודה פותחת את התא, הטבלה, הטרנספורמציה והמקור שמאחוריה.':'All charts in this view use Palestine data. Click any point to inspect its source, table, cell and transformation.',
'משנה':'From year','עד שנה':'To year','אופן הצגה':'Display mode','ערכים שנתיים':'Annual values','ממוצע נע — 3 שנים':'3-year moving average','ממוצע נע — 5 שנים':'5-year moving average',
'ממוצע רב־שנתי לתקופה':'Period average','מדד 100 בתחילת התקופה':'Index 100 (start of period)','שינוי מצטבר באחוזים':'Cumulative % change',
'תקופות מהירות':'Quick periods','שנות ה־20':'1920s','הכול':'All','עדכון':'Update',
'מערכת הכליאה':'Prison system','בתי סוהר ומחנות':'Prisons and detention camps','מינהל, עבודה וענישה':'Administration, labour & punishment','אירועים והערות':'Events and notes',
'השוואה מסונכרנת':'Aligned comparison','פלסטין נשארת קבועה. המערכת מציגה רק סדרות שניתן ליישר לפי מושג, בסיס זמן ומדד — ומסמנת במפורש השוואה מעורבת.':'Palestine remains fixed. The system aligns series by concept, time basis and measure, and flags mixed comparisons.',
'מושג מחקרי':'Research concept','גרסת מדד':'Measure variant','רמת גאוגרפיה':'Geographic level','מערכת ארצית':'Countrywide system','אזור':'Region','מוסד':'Facility',
'עיבוד זמן':'Time processing','שנתי':'Annual','ממוצע נע 3 שנים':'3-year moving average','ממוצע נע 5 שנים':'5-year moving average','ממוצע רב־שנתי':'Multi-year average',
'שינוי % מתחילת התקופה':'Change % from start','מ־':'From','עד':'To','רק שנות חפיפה עם פלסטין':'Only years overlapping Palestine',
'איפוס בחירות':'Reset choices','דף המקור והנתונים':'Source profile & data','מקור באינטרנט ↗':'Open original source ↗','אין נתונים':'No data','אין שנים משותפות':'No common years','אין כתובת אינטרנט ברשומה':'No source URL recorded','אופן הקליטה:':'Ingestion method:','מצב אימות:':'Verification status:','מקור רשמי:':'Original source:','רמת נתונים:':'Data level:','גישה:':'Access:','תיאור המקור והיקף הקליטה:':'Source description and ingested content:','מרחבים':'Jurisdictions','הרצת ההשוואה':'Run comparison','כל המקורות':'All sources','כל המדדים':'All measures',
'בחירת מקור':'Select source','מקורות':'Sources','איכות נתונים':'Data quality','שרשרת מקור':'Provenance chain',
'מקור':'Source','מדד':'Measure','מושג':'Concept','שנה':'Year','ערך':'Value','יחידה':'Unit','הצג':'Show',
'טבלה':'Table','תצפיות':'Observations','מיון':'Sort','סינון':'Filter','חפש':'Search',
'אוכלוסיית כלואים':'Custodial population','ממוצע יומי':'Daily average','קבלות':'Admissions','משמעת':'Discipline',
'עבודת אסירים':'Prison labour','הוצאות':'Expenditure','איכות':'Quality','כיסוי נתונים':'Data coverage',
'פתיחת תפריט':'Open menu','סגירה':'Close','סגור':'Close','הורדה ↓':'Download ↓',
'כיצד השתנתה אוכלוסיית הכלואים לאורך התקופה?':'How did the prison population change over time?',
'כיצד השתנה תמהיל הקבלות למערכת?':'How did the mix of admissions change?',
'כמה קבלות היו לכל אסיר בממוצע יומי?':'How many admissions occurred per prisoner in the daily average?',
'האם היקף הכליאה עלה מהר יותר מן האוכלוסייה?':'Did incarceration grow faster than the population?',
'מה היה היחס בין הממוצע היומי לבין מצבת סוף השנה?':'What was the ratio of daily average to year-end stock?',
'באילו שנים נרשמו השינויים השנתיים החדים ביותר?':'In which years were the largest annual changes?',
'האם מרכז הכובד של הכליאה עבר בין עכו לירושלים?':'Did incarceration shift between Acre and Jerusalem?',
'כיצד השתנו admissions בבתי הסוהר המרכזיים?':'How did admissions to the central prisons change?',
'אילו district lock-ups נשאו את ה־stock הגדול ביותר?':'Which district lock-ups held the largest stocks?',
'היכן הייתה תחלופת האסירים המחוזית הגדולה ביותר?':'Where was prisoner turnover highest?',
'מתי נעשו מחנות המעצר רכיב מרכזי במערכת?':'When did detention camps become central?',
'אילו מוסדות היו הגדולים ביותר בממוצע לאורך התקופה שנבחרה?':'Which institutions were largest on average over the selected period?',
'באילו שנים ובאילו מוסדות יש כיסוי נתונים?':'Which facilities and years have data coverage?',
'כמה אסירים הועסקו, ובאילו מסגרות?':'How many prisoners worked, and where?',
'איזה חלק מן הממוצע היומי הועסק בעבודה?':'What share of the daily average was employed?',
'כיצד השתנה הערך המדווח של עבודת האסירים?':'How did the reported value of prison labour change?',
'כיצד השתנו ההוצאות המדווחות של מערכת בתי הסוהר?':'How did reported prison expenditure change?',
'האם עבירות המשמעת התרבו ביחס לאוכלוסיית הכלא?':'Did disciplinary offences increase relative to the prison population?',
'באילו אמצעי ענישה משמעתיים נעשה שימוש?':'Which disciplinary punishments were used?',
'כיצד השתנה שיעור הרצידיביזם?':'How did recidivism change?',
'מה היה הרכב ההרשעות הקודמות?':'What was the distribution of previous convictions?',
'האם חל מעבר לעונשי מאסר ארוכים יותר?':'Did prison sentences become longer?',
'כיצד השתנו בריחות והוצאות להורג?':'How did escapes and executions change?',
'כיצד השתנו הסגרות וגירושים?':'How did extraditions and deportations change?',
'כמה criminal lunatics הוחזקו במערכת?':'How many criminal lunatics were held?',
'כיצד פעלה מערכת מבקרי בתי הסוהר?':'How did the prison visitors system operate?',
'מה מספרות ההערות האיכותניות על נקודות המפנה?':'What do qualitative notes reveal about turning points?'
};
const reverse=new Map(Object.entries(dict).map(([a,b])=>[b,a]));
const btn=document.getElementById('langToggle');if(!btn)return;
const originals=new WeakMap(); let lang=localStorage.getItem('cpe-language')==='en'?'en':'he';let busy=false;
const excluded='script,style,svg,pre,code,.js-plotly-plot,.plotly,.modebar,.chart,.chart-lg,.chart-xl,.map-chart,#sourceDrawer,#sourceDetail,#dataTable,#sourceTable,#qaTable';
function apply(){busy=true;document.documentElement.lang=lang;document.documentElement.dir=lang==='en'?'ltr':'rtl';btn.setAttribute('aria-pressed',String(lang==='en'));
const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let node;while((node=walker.nextNode())){const p=node.parentElement;if(!p||p.closest(excluded)||p.closest('#langToggle'))continue;
const raw=node.nodeValue,trim=raw.trim();if(!trim)continue;
let original=originals.get(node);if(!original){original=reverse.get(trim)||trim; originals.set(node,original);}const translated=lang==='en'?dict[original]:original;
if(translated){const leading=raw.match(/^\s*/)?.[0]||'';const trailing=raw.match(/\s*$/)?.[0]||'';const result=leading+translated+trailing;if(raw!==result)node.nodeValue=result;}}
// Dynamic string labels are intentionally not reinterpreted as historical source data.
busy=false;}
btn.addEventListener('click',()=>{lang=lang==='he'?'en':'he';localStorage.setItem('cpe-language',lang);apply();});
let queued=false;const observer=new MutationObserver(()=>{if(busy||lang!=='en'||queued)return;queued=true;requestAnimationFrame(()=>{queued=false;apply();});});observer.observe(document.body,{childList:true,subtree:true,characterData:false});apply();
})();
