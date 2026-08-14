from __future__ import annotations
import csv, hashlib, json, re, shutil, time
from pathlib import Path
from typing import Any, Iterable
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PIPE = ROOT / 'pipeline'
SITE = ROOT / 'site'
CONFIG = PIPE / 'config'
SNAPSHOTS = PIPE / 'snapshots'
RAW = PIPE / 'raw_cache'
BUILD = PIPE / 'build'
CANONICAL_COLUMNS = [
    'observation_id','jurisdiction','year','reporting_period','year_start','year_end','reference_date',
    'geography_level','geography_name','facility_id','facility_name','facility_type','measure','measure_class',
    'legal_status','sex','age_group','sentence_band','labour_status','value','unit','denominator',
    'source_dataset','source_sheet','source_column','source_header','source_table','source_url','historical_source_url',
    'raw_value_text','transformation','comparability_grade','quality_flag','definition_verified','source_record_id','notes'
]

def ensure_dirs():
    for p in [SITE/'data', SITE/'downloads', BUILD, RAW]: p.mkdir(parents=True, exist_ok=True)

def norm_text(x: Any) -> str:
    if x is None or (isinstance(x,float) and pd.isna(x)): return ''
    return re.sub(r'\s+', ' ', str(x)).strip()

def num(x: Any):
    if x is None: return None
    if isinstance(x, bool): return None
    if isinstance(x,(int,float)) and not pd.isna(x): return float(x)
    s=norm_text(x).replace(',','')
    if not s or s.lower() in {'na','n/a','nil','-','—','..'}: return None
    m=re.fullmatch(r'[-+]?\d+(?:\.\d+)?',s)
    return float(s) if m else None

def parse_year(x: Any):
    if isinstance(x,(int,float)) and not isinstance(x,bool) and not pd.isna(x):
        y=int(x); return (str(y),y,y,y)
    s=norm_text(x)
    m=re.match(r'^(\d{4})\s*[-–/]\s*(\d{2,4})$',s)
    if m:
        a=int(m.group(1)); b=int(m.group(2));
        if b<100: b=(a//100)*100+b
        return (s,a,b,b)
    m=re.search(r'(?<!\d)(18\d{2}|19\d{2}|20\d{2})(?!\d)',s)
    if m:
        y=int(m.group(1)); return (s,y,y,y)
    return (s,None,None,None)

def stable_id(row: dict) -> str:
    keys=['jurisdiction','year','geography_level','facility_id','facility_name','measure','legal_status','sex','age_group','sentence_band','source_dataset','source_sheet','source_column','source_record_id']
    raw='|'.join(norm_text(row.get(k,'')) for k in keys)
    return 'obs_'+hashlib.sha1(raw.encode('utf-8')).hexdigest()[:18]

def canonicalize(rows: Iterable[dict]) -> pd.DataFrame:
    out=[]
    for r in rows:
        x={c:r.get(c,'') for c in CANONICAL_COLUMNS}
        if not x['observation_id']: x['observation_id']=stable_id(x)
        out.append(x)
    df=pd.DataFrame(out, columns=CANONICAL_COLUMNS)
    if not df.empty:
        df['year']=pd.to_numeric(df['year'],errors='coerce').astype('Int64')
        df['value']=pd.to_numeric(df['value'],errors='coerce')
        df=df.drop_duplicates('observation_id', keep='last')
    return df

def write_js(path: Path, varname: str, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    text=json.dumps(obj, ensure_ascii=False, separators=(',',':'), default=str)
    path.write_text(f'window.{varname} = {text};\n', encoding='utf-8')

def append_js(path: Path, varname: str, records: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    text=json.dumps(records,ensure_ascii=False,separators=(',',':'),default=str)
    path.write_text(f'window.{varname} = (window.{varname} || []).concat({text});\n',encoding='utf-8')

def read_registry() -> pd.DataFrame:
    return pd.read_csv(CONFIG/'source_registry.csv', dtype=str).fillna('')

def save_status(statuses: list[dict]):
    pd.DataFrame(statuses).to_csv(BUILD/'build_status.csv',index=False,encoding='utf-8-sig')
    (BUILD/'build_status.json').write_text(json.dumps(statuses,ensure_ascii=False,indent=2),encoding='utf-8')

def status(source_id, state, message='', rows=0, years='', mode='', updated=None):
    return {'source_id':source_id,'state':state,'message':message,'rows':int(rows),'years_loaded':years,'mode':mode,'updated_at':updated or time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}

def year_span(df):
    if df is None or df.empty or 'year' not in df: return ''
    ys=pd.to_numeric(df['year'],errors='coerce').dropna().astype(int)
    return f'{ys.min()}–{ys.max()}' if len(ys) else ''

def http_get(url: str, timeout=45, binary=False):
    import requests
    h={'User-Agent':'ColonialPrisonExplorer/1.0 (+research data pipeline)'}
    r=requests.get(url,headers=h,timeout=timeout)
    r.raise_for_status()
    return r.content if binary else r.text

def download(url: str, dest: Path, timeout=90):
    dest.parent.mkdir(parents=True,exist_ok=True)
    data=http_get(url,timeout=timeout,binary=True)
    dest.write_bytes(data)
    return dest

def copy_configs_to_site():
    (SITE/'downloads').mkdir(parents=True,exist_ok=True)
    for name in ['source_registry.csv','variable_crosswalk.csv','facility_crosswalk.csv','canonical_schema.csv','validation_rules.csv','coverage_matrix.csv']:
        src=CONFIG/name
        if src.exists(): shutil.copy2(src,SITE/'downloads'/name)
