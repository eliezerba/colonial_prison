#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, math, re, shutil, subprocess, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PIPE = ROOT / 'pipeline'
CONFIG = PIPE / 'config'
SNAP = PIPE / 'snapshots'
SITE = ROOT / 'site'
DOWNLOADS = SITE / 'downloads'
DATA = SITE / 'data'
UI = ROOT / 'ui'

NEW_SOURCES = [
    dict(source_id='KEN_WPB_TREND', name='World Prison Brief – Kenya historical prison population', jurisdiction='Kenya', institution='Institute for Crime & Justice Policy Research / World Prison Brief', years_available='1928, 1938, 1948', overlap_with_palestine='1928–1948', data_level='year×national system', format='structured HTML historical table', structured_access='HTML table', api='none', population_measures='historical prison population point; reported rate where available', other_measures='historical trend', automation_level='high', comparability_role='secondary historical population-point comparator; Grade B', priority='P2', status='bundled verified snapshot', url='https://www.prisonstudies.org/country/kenya', ingest_strategy='HTML historical trend -> verified snapshot; reference basis flagged'),
    dict(source_id='TZA_WPB_TREND', name='World Prison Brief – Tanganyika/Tanzania historical prison population', jurisdiction='Tanganyika', institution='Institute for Crime & Justice Policy Research / World Prison Brief', years_available='1927, 1932, 1938, 1946', overlap_with_palestine='1927–1946', data_level='year×national system', format='structured HTML historical table', structured_access='HTML table', api='none', population_measures='historical prison population point', other_measures='historical trend', automation_level='high', comparability_role='secondary historical population-point comparator; Grade B', priority='P2', status='bundled verified snapshot', url='https://prisonstudies.org/country/tanzania', ingest_strategy='HTML historical trend -> verified snapshot; historical name normalised to Tanganyika'),
    dict(source_id='MWI_WPB_TREND', name='World Prison Brief – Nyasaland/Malawi historical prison population', jurisdiction='Nyasaland', institution='Institute for Crime & Justice Policy Research / World Prison Brief', years_available='1928, 1938, 1950', overlap_with_palestine='1928–1948', data_level='year×national system', format='structured HTML historical table', structured_access='HTML table', api='none', population_measures='historical prison population point; reported rate where available', other_measures='historical trend', automation_level='high', comparability_role='secondary historical population-point comparator; Grade B', priority='P2', status='bundled verified snapshot', url='https://prisonstudies.org/country/malawi', ingest_strategy='HTML historical trend -> verified snapshot; historical name normalised to Nyasaland'),
    dict(source_id='SWZ_WPB_TREND', name='World Prison Brief – Swaziland historical prison population', jurisdiction='Swaziland', institution='Institute for Crime & Justice Policy Research / World Prison Brief', years_available='1938', overlap_with_palestine='1938', data_level='year×national system', format='structured HTML historical table', structured_access='HTML table', api='none', population_measures='historical prison population point', other_measures='historical trend', automation_level='high', comparability_role='secondary historical population-point comparator; Grade B', priority='P2', status='bundled verified snapshot', url='https://prisonstudies.org/country/eswatiniswaziland', ingest_strategy='HTML historical trend -> verified snapshot; historical name retained'),
    dict(source_id='ZAF_WPB_TREND', name='World Prison Brief – South Africa historical prison population', jurisdiction='South Africa', institution='Institute for Crime & Justice Policy Research / World Prison Brief', years_available='1936', overlap_with_palestine='1936', data_level='year×national system', format='structured HTML historical table', structured_access='HTML table', api='none', population_measures='historical prison population point and rate', other_measures='historical trend', automation_level='high', comparability_role='Dominion comparator; secondary historical series; Grade B', priority='P2', status='bundled verified snapshot', url='https://www.prisonstudies.org/country/south-africa', ingest_strategy='HTML historical trend -> verified snapshot'),
    dict(source_id='IRL_WPB_TREND', name='World Prison Brief – Ireland historical prison population', jurisdiction='Ireland', institution='Institute for Crime & Justice Policy Research / World Prison Brief', years_available='1922, 1930, 1935, 1940, 1945, 1950', overlap_with_palestine='1922–1948', data_level='year×national system', format='structured HTML historical table', structured_access='HTML table', api='none', population_measures='historical prison population point and rate', other_measures='historical trend', automation_level='high', comparability_role='post-imperial comparator; Grade B', priority='P3', status='bundled verified snapshot', url='https://prisonstudies.org/country/ireland-republic?language_content_entity=en-gb', ingest_strategy='HTML historical trend -> verified snapshot; political-status caveat retained'),
    dict(source_id='SGP_WPB_TREND', name='World Prison Brief – Singapore historical prison population', jurisdiction='Singapore', institution='Institute for Crime & Justice Policy Research / World Prison Brief', years_available='1947', overlap_with_palestine='1947', data_level='year×national system', format='structured HTML historical table', structured_access='HTML table', api='none', population_measures='historical prison population point', other_measures='historical trend', automation_level='high', comparability_role='colonial comparator; Grade B', priority='P2', status='bundled verified snapshot', url='https://www.prisonstudies.org/country/singapore?language_content_entity=en-gb', ingest_strategy='HTML historical trend -> verified snapshot'),
]

WPB_SERIES = {
    'KEN_WPB_TREND': ('Kenya', 'https://www.prisonstudies.org/country/kenya', {1928:(2390,None),1938:(4700,138),1948:(8214,195)}),
    'TZA_WPB_TREND': ('Tanganyika', 'https://prisonstudies.org/country/tanzania', {1927:(2043,None),1932:(2616,None),1938:(2978,None),1946:(3425,None)}),
    'MWI_WPB_TREND': ('Nyasaland', 'https://prisonstudies.org/country/malawi', {1928:(641,None),1938:(736,None),1950:(981,33)}),
    'SWZ_WPB_TREND': ('Swaziland', 'https://prisonstudies.org/country/eswatiniswaziland', {1938:(246,None)}),
    'ZAF_WPB_TREND': ('South Africa', 'https://www.prisonstudies.org/country/south-africa', {1936:(19077,200)}),
    'IRL_WPB_TREND': ('Ireland', 'https://prisonstudies.org/country/ireland-republic?language_content_entity=en-gb', {1922:(674,23),1930:(643,22),1935:(617,21),1940:(493,17),1945:(733,25),1950:(521,18)}),
    'SGP_WPB_TREND': ('Singapore', 'https://www.prisonstudies.org/country/singapore?language_content_entity=en-gb', {1947:(1921,None)}),
}

KEY_LABELS_HE = {
 'stock_eoy_total':'מצבת אסירים בסוף שנה','population_point_total':'אוכלוסיית אסירים בנקודת דיווח','avg_daily_total':'ממוצע יומי של אסירים','admissions_total':'קבלות / admissions','stock_eoy_convicted':'מורשעים בסוף שנה','stock_eoy_nonconvicted':'לא־מורשעים בסוף שנה','stock_eoy_debtors':'חייבים בסוף שנה','admissions_convicted':'קבלות מורשעים','admissions_safe_custody':'קבלות למשמורת בטוחה','admissions_debtors':'קבלות חייבים','population_denominator':'אוכלוסייה כללית','stock_eoy_rate_per_100000':'מצבת סוף שנה ל־100,000','population_point_rate_per_100000':'אוכלוסיית אסירים ל־100,000','avg_daily_rate_per_100000':'ממוצע יומי ל־100,000','admissions_rate_per_100000':'קבלות ל־100,000','prison_expenditure':'הוצאות בתי סוהר','prison_expenditure_total':'סך הוצאות בתי סוהר','expenditure_per_avg_prisoner':'הוצאה ממוצעת לאסיר','expenditure_per_prisoner_day':'הוצאה לאסיר־יום','prison_labour_count':'אסירים בעבודה','prison_labour_value':'ערך עבודת אסירים','employed_avg_daily_total':'מועסקים בממוצע יומי','disciplinary_offences':'עבירות משמעת','recidivists_total':'עבריינים חוזרים','recidivism_rate_pct':'שיעור רצידיביזם','detention_stock_eoy':'עצורים במחנות בסוף שנה','detention_avg_daily':'ממוצע יומי במחנות מעצר','illegal_immigrant_detention':'מעצר מהגרים בלתי־לגליים','stock_eoy_sentence_band':'התפלגות לפי אורך עונש','escapes_reported_count':'בריחות מדווחות','executions':'הוצאות להורג','prison_visitors':'מבקרי בתי סוהר','prison_visitor_visits':'ביקורי מבקרים','remarks':'הערות מקור',
}

CONCEPTS = {
 'custodial_population_total':('אוכלוסיית כלואים – נקודת זמן','Custodial population – point in time','population','point_or_stock'),
 'custodial_population_average':('אוכלוסיית כלואים – ממוצע','Custodial population – average','population','annual_average'),
 'custodial_population_composition':('הרכב אוכלוסיית הכלואים','Custodial population composition','composition','point_or_average'),
 'admissions_flow':('קבלות וכניסות','Admissions and entries','flow','annual_flow'),
 'population_rate':('שיעורי כליאה','Imprisonment rates','rate','derived_or_reported_rate'),
 'national_population':('אוכלוסייה כללית','National population','denominator','point_or_estimate'),
 'capacity_and_occupancy':('קיבולת ותפוסה','Capacity and occupancy','capacity','point'),
 'prison_labour':('עבודת אסירים','Prison labour','labour','annual_or_average'),
 'finance':('הוצאות והכנסות','Finance','finance','fiscal_year'),
 'discipline_and_punishment':('משמעת וענישה','Discipline and punishment','discipline','annual_flow'),
 'recidivism':('רצידיביזם','Recidivism','recidivism','annual_or_stock'),
 'sentence_structure':('מבנה עונשים','Sentence structure','sentence','point_or_flow'),
 'special_detention':('מעצר מיוחד ומנהלי','Special and administrative detention','detention','mixed'),
 'movement_and_outcomes':('תנועות ותוצאות','Movements and outcomes','events','annual_flow'),
 'demography':('מאפיינים דמוגרפיים','Demography','demography','mixed'),
 'institutions':('מוסדות ומבנה מערכתי','Institutions and system structure','institution','mixed'),
 'qualitative_notes':('הערות איכותניות','Qualitative notes','text','text'),
 'source_proxy':('Proxy / אינדקס מקור','Source proxy/index','proxy','record_index'),
 'other':('אחר','Other','other','mixed'),
}

COORDS = {
'Mandatory Palestine':(31.8,35.2),'New Zealand':(-41.3,174.8),'British Nigeria':(9.1,8.7),'Canada':(56.1,-106.3),'British India':(22.5,78.9),'Queensland – St Helena Penal Establishment':(-27.39,153.23),'Tasmania – Hobart Gaol':(-42.88,147.33),'Hong Kong':(22.32,114.17),'Australia':(-25.3,133.8),'Ceylon':(7.87,80.77),'Kenya':(-0.02,37.9),'Uganda':(1.37,32.29),'Tanganyika':(-6.3,34.8),'Somaliland':(9.55,46.2),'Zanzibar':(-6.16,39.2),'Nyasaland':(-13.25,34.3),'Northern Rhodesia':(-13.1,27.8),'England & Wales':(52.4,-1.5),'Aden':(12.78,45.03),'Bombay Presidency':(19.08,72.88),'Mauritius':(-20.2,57.5),'Jamaica':(18.1,-77.3),'Malta':(35.94,14.38),'Cyprus':(35.1,33.4),'Trinidad & Tobago':(10.7,-61.2),'Fiji':(-17.7,178.1),'Sierra Leone':(8.46,-11.78),'Bermuda':(32.3,-64.75),'Barbados':(13.19,-59.54),'Bahamas':(25.04,-77.4),'Gold Coast':(7.95,-1.02),'Gambia':(13.44,-15.31),'Bechuanaland':(-22.3,24.7),'British Guiana':(4.86,-58.93),'Basutoland':(-29.6,28.2),'Solomon Islands':(-9.65,160.2),'Dominica':(15.4,-61.37),'Swaziland':(-26.5,31.5),'South Africa':(-30.6,22.9),'Ireland':(53.2,-8.2),'Singapore':(1.35,103.82),
}

REGION = {
'Mandatory Palestine':'Middle East','New Zealand':'Oceania','British Nigeria':'Africa','Canada':'North America','British India':'South Asia','Hong Kong':'East Asia','Australia':'Oceania','Ceylon':'South Asia','Kenya':'East Africa','Uganda':'East Africa','Tanganyika':'East Africa','Somaliland':'East Africa','Zanzibar':'East Africa','Nyasaland':'Southern Africa','Northern Rhodesia':'Southern Africa','England & Wales':'Europe','Aden':'Middle East','Bombay Presidency':'South Asia','Mauritius':'Indian Ocean','Jamaica':'Caribbean','Malta':'Mediterranean','Cyprus':'Mediterranean','Trinidad & Tobago':'Caribbean','Fiji':'Oceania','Sierra Leone':'West Africa','Bermuda':'Atlantic','Barbados':'Caribbean','Bahamas':'Caribbean','Gold Coast':'West Africa','Gambia':'West Africa','Bechuanaland':'Southern Africa','British Guiana':'Caribbean/South America','Basutoland':'Southern Africa','Solomon Islands':'Oceania','Dominica':'Caribbean','Swaziland':'Southern Africa','South Africa':'Southern Africa','Ireland':'Europe','Singapore':'Southeast Asia','Queensland – St Helena Penal Establishment':'Oceania','Tasmania – Hobart Gaol':'Oceania'
}

FACILITY_COORDS = {
'Acre Central Prison':(32.9236,35.0719),'Jerusalem Central Prison':(31.778,35.229),'Howard Home':(32.31,35.02),'Jerusalem Remand Home':(31.78,35.22),'Girls Home':(32.82,34.99),'Bethlehem Women Prison':(31.705,35.202),'Bethlehem Detention Camp':(31.705,35.202),'Acre Farm Labour Camp':(32.93,35.08),'Northern/Haifa District Lock-ups':(32.79,34.99),'Jerusalem District Lock-ups':(31.78,35.22),'Nazareth District Lock-ups':(32.70,35.30),'Southern/Jaffa-Lydda District Lock-ups':(31.95,34.89),'Jaffa Lock-up':(32.05,34.75),'Samaria/Nablus District Lock-ups':(32.22,35.26),'Beersheba/Gaza District Lock-ups':(31.25,34.79),'Acre Detention Camp':(32.93,35.08),'Sarafand Detention Camp':(31.96,34.84),'Athlit Detention Camp':(32.70,34.94),'Latrun Detention Camp':(31.84,34.98)
}

def boolish(x): return str(x).strip().lower() in {'1','true','yes'}

def family_for_measure(m:str):
    m=str(m)
    if m in {'stock_eoy_total','population_point_total'}: return 'custodial_population_total'
    if m.startswith('stock_eoy_'):
        if 'sentence' in m: return 'sentence_structure'
        if any(x in m for x in ['defence','criminal_lunatics']): return 'special_detention'
        return 'custodial_population_composition'
    if m.startswith('avg_daily'):
        if 'rate' in m: return 'population_rate'
        return 'custodial_population_average'
    if m.startswith('admissions') or m in {'distinct_persons_received','distinct_convicted_admissions','prisoners_handled_during_year'}:
        if 'rate' in m: return 'population_rate'
        return 'admissions_flow'
    if 'rate_per_100000' in m or 'rate_per_1000' in m or m.endswith('_rate_pct') or m.endswith('_rate_per_10000'): return 'population_rate'
    if m=='population_denominator': return 'national_population'
    if 'capacity' in m or 'occupancy' in m: return 'capacity_and_occupancy'
    if 'labour' in m or 'employed' in m or 'industry_receipts' in m: return 'prison_labour'
    if 'expenditure' in m or 'cost' in m or 'credits' in m: return 'finance'
    if 'disciplin' in m or 'punishment' in m or 'leg_irons' in m: return 'discipline_and_punishment'
    if 'recidiv' in m or 'prior_convictions' in m or 'offenders_distinct' in m: return 'recidivism'
    if 'sentence' in m or 'convictions_count' in m: return 'sentence_structure'
    if 'detention' in m or 'safe_custody' in m or 'bound_prevention' in m: return 'special_detention'
    if any(x in m for x in ['escapes','executions','extraditions','deportations']): return 'movement_and_outcomes'
    if any(x in m for x in ['female','male','juvenile','age','religion']): return 'demography'
    if any(x in m for x in ['visitor','lunatics']): return 'institutions'
    if m=='remarks': return 'qualitative_notes'
    if 'indexed_prisoner_records' in m: return 'source_proxy'
    return 'other'

def time_basis_for_measure(m:str):
    if m.startswith('stock_eoy_'): return 'end_of_year_stock'
    if m=='population_point_total' or m=='population_point_rate_per_100000': return 'single_date_or_annual_average_unspecified'
    if m.startswith('avg_daily'): return 'annual_daily_average'
    if m.startswith('admissions') or 'received' in m or 'handled_during_year' in m: return 'annual_flow'
    if 'expenditure' in m or 'credits' in m: return 'fiscal_or_calendar_year'
    if m=='remarks': return 'qualitative_year_note'
    if 'rate' in m: return 'reported_or_derived_rate'
    return 'mixed_or_source_specific'

def default_chart(m,concept):
    if concept in {'custodial_population_total','custodial_population_average','admissions_flow','population_rate','finance','prison_labour','recidivism','movement_and_outcomes'}: return 'line'
    if concept in {'custodial_population_composition','sentence_structure','discipline_and_punishment','demography'}: return 'stacked_area_or_bar'
    if concept in {'special_detention','institutions'}: return 'line_or_map'
    if concept=='qualitative_notes': return 'timeline'
    return 'table'

def source_family(row):
    sid=str(row.get('source_id',''))
    if sid=='PAL_V2': return ('research_compilation','A/B','primary_case')
    if sid in {'NZ_OYB','CAN_HSC_Z','NZ_AJHR_PRISONS','AUS_ABS_HIST','EAW_PARL_HIST','IND_HANSARD_ADM','ADEN_QDL_ADMIN','BOM_QDL_ADMIN','HKG_ADMIN'}: return ('official_publication','A/B','official')
    if sid in {'NGA_AO'}: return ('research_replication','A/B','research')
    if 'WPB' in sid: return ('secondary_structured_database','B','secondary')
    if sid in {'EAF_1938_JSH'}: return ('peer_reviewed_research_table','B/C','research')
    if sid in {'QLD_STHELENA','TAS_PRISONERS','QLD_PHOTO','QLD_TOOWOOMBA','QLD_BRISBANE','IRL_REGISTERS','WA_BLUEBOOKS','GUY_MNS','IND_DSAL'}: return ('structured_repository_or_microdata','C/D','repository')
    return ('other','U','other')

def add_new_sources_and_snapshots():
    regp=CONFIG/'source_registry.csv'; reg=pd.read_csv(regp,dtype=str).fillna('')
    known=set(reg.source_id)
    add=[r for r in NEW_SOURCES if r['source_id'] not in known]
    if add: reg=pd.concat([reg,pd.DataFrame(add,columns=reg.columns)],ignore_index=True)
    reg.to_csv(regp,index=False,encoding='utf-8-sig')

    sp=SNAP/'additional_verified_snapshots.csv'; snap=pd.read_csv(sp,dtype=str).fillna('')
    # Correct the canonical semantics for all WPB historical values: these are population points whose exact within-year basis can be a point or annual average.
    mask=snap['source_dataset'].str.contains('WPB',na=False) & snap['measure'].eq('stock_eoy_total')
    snap.loc[mask,'measure']='population_point_total'; snap.loc[mask,'measure_class']='point_population'
    snap.loc[mask,'quality_flag']=snap.loc[mask,'quality_flag'].astype(str).str.replace('reference_date_unspecified','reference_basis_single_date_or_average_unspecified',regex=False)
    rows=[]
    for sid,(jur,url,series) in WPB_SERIES.items():
        for year,(pop,rate) in series.items():
            rows.append(dict(source_dataset=sid,jurisdiction=jur,year=year,reporting_period=str(year),reference_date='single date in year or annual average; exact basis not specified in WPB historical table',geography_level='system',geography_name=jur,facility_name='',facility_type='',measure='population_point_total',measure_class='point_population',legal_status='all',value=pop,unit='persons',source_table='World Prison Brief - Prison population trend up to 2000',source_header='Prison population total',source_url=url,historical_source_url=url,transformation='direct transcription from World Prison Brief historical trend table',comparability_grade='B',quality_flag='secondary_historical_series|reference_basis_single_date_or_average_unspecified',definition_verified='True',source_record_id=f'{sid}:historical:{year}:population_total',notes='Published historical prison population point. Exact within-year single-date versus annual-average basis is not sufficiently specified for Grade A equivalence to Palestine 31 December stock.'))
            if rate is not None:
                rows.append(dict(source_dataset=sid,jurisdiction=jur,year=year,reporting_period=str(year),reference_date='reported historical rate; same reference basis as population point',geography_level='system',geography_name=jur,facility_name='',facility_type='',measure='population_point_rate_per_100000',measure_class='rate',legal_status='all',value=rate,unit='per_100000',source_table='World Prison Brief - Prison population trend up to 2000',source_header='Prison population rate per 100,000',source_url=url,historical_source_url=url,transformation='direct transcription from World Prison Brief historical trend table',comparability_grade='B',quality_flag='secondary_historical_series|reported_rate|reference_basis_unspecified',definition_verified='True',source_record_id=f'{sid}:historical:{year}:population_rate',notes='Source-reported historical prison population rate. Approximation markers such as c. are retained in notes where applicable.'))
    adddf=pd.DataFrame(rows,columns=snap.columns)
    snap=snap[~snap['source_dataset'].isin(WPB_SERIES.keys())]
    snap=pd.concat([snap,adddf],ignore_index=True)
    snap.to_csv(sp,index=False,encoding='utf-8-sig')

def run_base_build():
    subprocess.run([sys.executable,str(PIPE/'build_all.py')],cwd=PIPE,check=True)

def stable_id(row):
    keys=['jurisdiction','year','geography_level','facility_id','facility_name','measure','legal_status','sex','age_group','sentence_band','source_dataset','source_sheet','source_column','source_record_id']
    raw='|'.join('' if pd.isna(row.get(k,'')) else str(row.get(k,'')) for k in keys)
    return 'obs_'+hashlib.sha1(raw.encode()).hexdigest()[:18]

def build_measure_registry(obs):
    rows=[]
    for m in sorted(obs.measure.dropna().astype(str).unique()):
        cid=family_for_measure(m); he,en,kind,tbasis=CONCEPTS[cid]
        label_en=m.replace('source_specific__','').replace('_',' ').title()
        label_he=KEY_LABELS_HE.get(m,label_en)
        comparable = cid in {'custodial_population_total','custodial_population_average','admissions_flow','population_rate','finance'} and m not in {'admissions_male','admissions_female'}
        rows.append(dict(measure=m,label_he=label_he,label_en=label_en,concept_id=cid,concept_label_he=he,concept_label_en=en,concept_kind=kind,time_basis=time_basis_for_measure(m),aggregation_default='mean' if any(x in m for x in ['avg','rate','per_']) else ('sum' if any(x in m for x in ['admissions','events','escapes','executions']) else 'last_or_point'),comparable_across_jurisdictions=comparable,requires_denominator='population_denominator' if 'rate_per_100000' in m and not m.startswith('source_reported') and m!='population_point_rate_per_100000' else '',preferred_chart=default_chart(m,cid),notes='Raw measure retained; cross-jurisdiction comparisons are mediated by concept/time-basis metadata rather than name equality alone.'))
    return pd.DataFrame(rows)

def extend_registry(reg,obs,sm):
    reg=reg.copy()
    for col in ['source_family','evidence_tier','source_role','region','latitude','longitude','political_status','loaded_concepts','loaded_measures','loaded_geography_levels']:
        if col not in reg.columns: reg[col]=''
    actual=obs.groupby('source_dataset').agg(loaded_observations_v7=('observation_id','count'),loaded_min_year_v7=('year','min'),loaded_max_year_v7=('year','max')).reset_index().rename(columns={'source_dataset':'source_id'})
    reg=reg.merge(actual,on='source_id',how='left')
    concept_map=sm.groupby('source_dataset').agg(loaded_concepts=('concept_id',lambda s:' | '.join(sorted(set(s)))),loaded_measures=('measure',lambda s:' | '.join(sorted(set(s)))),loaded_geography_levels=('geography_levels','first')).reset_index().rename(columns={'source_dataset':'source_id'})
    reg=reg.drop(columns=['loaded_concepts','loaded_measures','loaded_geography_levels'],errors='ignore').merge(concept_map,on='source_id',how='left')
    for i,r in reg.iterrows():
        fam,tier,role=source_family(r); reg.at[i,'source_family']=fam; reg.at[i,'evidence_tier']=tier; reg.at[i,'source_role']=role
        j=r['jurisdiction']; reg.at[i,'region']=REGION.get(j,'Other')
        latlon=COORDS.get(j); reg.at[i,'latitude']=latlon[0] if latlon else ''; reg.at[i,'longitude']=latlon[1] if latlon else ''
        reg.at[i,'political_status']='primary Mandate case' if j=='Mandatory Palestine' else ('British colony/protectorate/mandate or imperial comparator; inspect source notes' if j not in {'Canada','Australia','New Zealand','South Africa','Ireland','England & Wales'} else 'Dominion/metropolitan/post-imperial comparator')
    reg['loaded_observations']=reg['loaded_observations_v7'].fillna(reg.get('loaded_observations',0)).fillna(0).astype(int)
    reg['loaded_min_year']=reg['loaded_min_year_v7'].fillna(reg.get('loaded_min_year',''))
    reg['loaded_max_year']=reg['loaded_max_year_v7'].fillna(reg.get('loaded_max_year',''))
    reg=reg.drop(columns=['loaded_observations_v7','loaded_min_year_v7','loaded_max_year_v7'],errors='ignore')
    return reg

def create_maps_and_audits():
    op=DOWNLOADS/'observations.csv'; obs=pd.read_csv(op)
    # Recalculate IDs for WPB rows whose canonical measure was corrected.
    obs['observation_id']=obs.apply(stable_id,axis=1)
    mr=build_measure_registry(obs)
    mmap=mr.set_index('measure').to_dict('index')
    obs['concept_id']=obs['measure'].map(lambda m:mmap.get(m,{}).get('concept_id','other'))
    obs['concept_label_he']=obs['measure'].map(lambda m:mmap.get(m,{}).get('concept_label_he','אחר'))
    obs['time_basis']=obs['measure'].map(lambda m:mmap.get(m,{}).get('time_basis','mixed_or_source_specific'))
    obs['comparison_eligible']=obs['measure'].map(lambda m:bool(mmap.get(m,{}).get('comparable_across_jurisdictions',False)))
    def clean_text(value):
        if pd.isna(value):
            return ''
        text=str(value).strip()
        return '' if text.lower() in {'nan','none','null'} else text

    def make_locator(r):
        table=clean_text(r.get('source_table',''))
        if table:
            return table
        sheet=clean_text(r.get('source_sheet',''))
        field=clean_text(r.get('source_column','')) or clean_text(r.get('source_header',''))
        locator=' / '.join(x for x in [sheet,field] if x)
        if locator:
            return locator
        record=clean_text(r.get('source_record_id',''))
        if record:
            return record
        return clean_text(r.get('source_dataset',''))

    obs['source_locator']=obs.apply(make_locator,axis=1)
    obs.to_csv(op,index=False,encoding='utf-8-sig')

    # Rebuild the row-level provenance audit after enrichment, so the published
    # audit evaluates the same canonical locators used by the dashboard.
    pa_cols=['observation_id','source_dataset','jurisdiction','year','measure','comparability_grade','definition_verified','source_url','historical_source_url','source_sheet','source_column','source_header','source_table','source_locator','source_record_id','transformation','quality_flag']
    pa=obs[pa_cols].copy()
    pa['source_url_present']=pa['source_url'].fillna('').astype(str).str.startswith('http')
    pa['source_locator_present']=pa['source_locator'].fillna('').astype(str).str.strip().ne('')
    pa['source_record_id_present']=pa['source_record_id'].fillna('').astype(str).str.strip().ne('')
    pa['transformation_documented']=pa['transformation'].fillna('').astype(str).str.strip().ne('')
    pa['provenance_complete']=pa[['source_url_present','source_locator_present','source_record_id_present','transformation_documented']].all(axis=1)
    def verification_class(r):
        if 'proxy' in str(r.get('quality_flag','')).lower() or str(r.get('comparability_grade',''))=='D':
            return 'source/proxy_only'
        verified=str(r.get('definition_verified','')).lower() in {'true','1','yes'}
        if verified and str(r.get('comparability_grade',''))=='A':
            return 'definition_verified_direct'
        if verified:
            return 'definition_verified_with_comparability_caveat'
        return 'source_traceable_definition_pending'
    pa['verification_class']=pa.apply(verification_class,axis=1)
    pa.to_csv(DOWNLOADS/'provenance_audit.csv',index=False,encoding='utf-8-sig')

    # source-measure map covers every loaded pair.
    def joinuniq(s): return ' | '.join(sorted(set(str(x) for x in s.dropna() if str(x))))
    sm=obs.groupby(['source_dataset','measure','concept_id','concept_label_he','time_basis'],dropna=False).agg(observations=('observation_id','count'),min_year=('year','min'),max_year=('year','max'),units=('unit',joinuniq),grades=('comparability_grade',joinuniq),geography_levels=('geography_level',joinuniq),jurisdictions=('jurisdiction',joinuniq),definition_verified_pct=('definition_verified',lambda s:round(100*sum(boolish(x) for x in s)/len(s),1))).reset_index()
    reg=pd.read_csv(DOWNLOADS/'source_registry.csv',dtype=str).fillna('')
    reg=extend_registry(reg,obs,sm)
    reg.to_csv(DOWNLOADS/'source_registry.csv',index=False,encoding='utf-8-sig')
    CONFIG_REG=CONFIG/'source_registry.csv'
    # keep base config concise; extended registry is published in downloads/data.

    sm=sm.merge(reg[['source_id','name','source_family','evidence_tier','state','url','region']],left_on='source_dataset',right_on='source_id',how='left')
    sm['mapped']=True
    sm.to_csv(DOWNLOADS/'source_measure_map.csv',index=False,encoding='utf-8-sig')
    mr.to_csv(DOWNLOADS/'measure_registry.csv',index=False,encoding='utf-8-sig')
    conceptdf=pd.DataFrame([dict(concept_id=k,concept_label_he=v[0],concept_label_en=v[1],concept_kind=v[2],default_time_basis=v[3]) for k,v in CONCEPTS.items()])
    conceptdf.to_csv(DOWNLOADS/'concept_registry.csv',index=False,encoding='utf-8-sig')

    # Registry×concept coverage, including zero-loaded sources so no source disappears.
    concepts=sorted(mr.concept_id.unique())
    cov=[]
    for _,s in reg.iterrows():
        g=sm[sm.source_dataset.eq(s.source_id)]
        row={'source_id':s.source_id,'name':s['name'],'jurisdiction':s['jurisdiction'],'state':s.get('state',''),'loaded_observations':int(s.get('loaded_observations',0) or 0)}
        present=set(g.concept_id)
        for c in concepts: row[c]=int(c in present)
        cov.append(row)
    covdf=pd.DataFrame(cov); covdf.to_csv(DOWNLOADS/'source_concept_coverage.csv',index=False,encoding='utf-8-sig')

    # Exact alternative-source groups. Values are only treated as alternatives when
    # the raw measure, unit, time basis and every substantive dimension match.
    # Related components (male/female/total, sentence bands, etc.) remain linked by
    # concept in the UI but are never silently treated as equivalent observations.
    exact_sem=['jurisdiction','year','reporting_period','reference_date','geography_level','geography_name','facility_id','facility_name','measure','time_basis','legal_status','sex','age_group','sentence_band','labour_status','unit']
    eq=[]
    for key,g in obs.groupby(exact_sem,dropna=False):
        sources=sorted(set(g.source_dataset.astype(str)))
        if len(sources) < 2:
            continue
        gid='eq_'+hashlib.sha1('|'.join(str(x) for x in key).encode()).hexdigest()[:14]
        vals=pd.to_numeric(g.value,errors='coerce').dropna()
        eq.append(dict(equivalence_group_id=gid,jurisdiction=key[0],year=key[1],reporting_period=key[2],reference_date=key[3],geography_level=key[4],geography_name=key[5],facility_id=key[6],facility_name=key[7],measure=key[8],concept_id=g.concept_id.iloc[0],time_basis=key[9],legal_status=key[10],sex=key[11],age_group=key[12],sentence_band=key[13],labour_status=key[14],unit=key[15],observation_count=len(g),source_count=len(sources),sources=' | '.join(sources),min_value=vals.min() if len(vals) else '',max_value=vals.max() if len(vals) else '',absolute_spread=(vals.max()-vals.min()) if len(vals)>1 else 0,relative_spread_pct=(100*(vals.max()-vals.min())/abs(vals.mean())) if len(vals)>1 and vals.mean()!=0 else 0,agreement_status='exact' if len(vals)>1 and vals.max()==vals.min() else 'conflict',observation_ids=' | '.join(g.observation_id.astype(str))))
    eqcols=['equivalence_group_id','jurisdiction','year','reporting_period','reference_date','geography_level','geography_name','facility_id','facility_name','measure','concept_id','time_basis','legal_status','sex','age_group','sentence_band','labour_status','unit','observation_count','source_count','sources','min_value','max_value','absolute_spread','relative_spread_pct','agreement_status','observation_ids']
    eqdf=pd.DataFrame(eq,columns=eqcols); eqdf.to_csv(DOWNLOADS/'observation_equivalence_groups.csv',index=False,encoding='utf-8-sig')

    # Source relationships: one edge per pair of DISTINCT sources, jurisdiction and
    # concept. Overlap is computed on actual years and the edge records whether the
    # sources contain an exactly matching raw measure/time basis or only related
    # measures under the same research concept.
    rel=[]
    for (jur,cid),gobs in obs.groupby(['jurisdiction','concept_id'],dropna=False):
        sources=sorted(set(gobs.source_dataset.astype(str)))
        for i,sa in enumerate(sources):
            for sb in sources[i+1:]:
                ga=gobs[gobs.source_dataset.eq(sa)]; gb=gobs[gobs.source_dataset.eq(sb)]
                ya=set(pd.to_numeric(ga.year,errors='coerce').dropna().astype(int)); yb=set(pd.to_numeric(gb.year,errors='coerce').dropna().astype(int)); ov=sorted(ya&yb)
                exact_pairs=set(zip(ga.measure.astype(str),ga.time_basis.astype(str))) & set(zip(gb.measure.astype(str),gb.time_basis.astype(str)))
                relation='alternative_exact_measure' if exact_pairs and ov else ('overlapping_same_concept' if ov else 'complementary_same_concept')
                rel.append(dict(jurisdiction=jur,concept_id=cid,source_a=sa,source_b=sb,relation_type=relation,overlap_years=' | '.join(map(str,ov)),overlap_count=len(ov),exact_measure_time_pairs=' | '.join(sorted(f'{m} [{t}]' for m,t in exact_pairs)),source_a_observations=len(ga),source_b_observations=len(gb),source_a_grades=' | '.join(sorted(set(ga.comparability_grade.astype(str)))),source_b_grades=' | '.join(sorted(set(gb.comparability_grade.astype(str))))))
    relcols=['jurisdiction','concept_id','source_a','source_b','relation_type','overlap_years','overlap_count','exact_measure_time_pairs','source_a_observations','source_b_observations','source_a_grades','source_b_grades']
    reldf=pd.DataFrame(rel,columns=relcols); reldf.to_csv(DOWNLOADS/'source_relationships.csv',index=False,encoding='utf-8-sig')

    # Jurisdiction registry and facility coordinates.
    jrows=[]
    for j in sorted(set(obs.jurisdiction.dropna().astype(str)) | set(reg.jurisdiction.dropna().astype(str))):
        latlon=COORDS.get(j,('', '')); jrows.append(dict(jurisdiction=j,region=REGION.get(j,'Other'),latitude=latlon[0],longitude=latlon[1],loaded_observations=int((obs.jurisdiction==j).sum()),sources=' | '.join(sorted(set(obs.loc[obs.jurisdiction==j,'source_dataset'].astype(str))))))
    pd.DataFrame(jrows).to_csv(DOWNLOADS/'jurisdiction_registry.csv',index=False,encoding='utf-8-sig')
    fp=DOWNLOADS/'facility_crosswalk.csv'; fac=pd.read_csv(fp,dtype=str).fillna('')
    fac['latitude']=fac['facility_name'].map(lambda x:FACILITY_COORDS.get(x,('',''))[0]); fac['longitude']=fac['facility_name'].map(lambda x:FACILITY_COORDS.get(x,('',''))[1])
    fac.to_csv(fp,index=False,encoding='utf-8-sig')

    # Synchronisation audit.
    issues=[]
    if len(obs)!=obs.observation_id.nunique(): issues.append(dict(severity='error',check='duplicate observation_id',count=len(obs)-obs.observation_id.nunique(),message='Observation identifiers must be unique.'))
    missing_sources=set(obs.source_dataset)-set(reg.source_id)
    issues.append(dict(severity='pass' if not missing_sources else 'error',check='all observation sources registered',count=len(missing_sources),message=' | '.join(sorted(missing_sources)) if missing_sources else 'Every observation source is in the registry.'))
    unmapped=obs[~obs.measure.isin(mr.measure)]
    issues.append(dict(severity='pass' if unmapped.empty else 'error',check='all observations mapped to concepts',count=len(unmapped),message='No observation may fall outside the measure registry.'))
    pairs=obs[['source_dataset','measure']].drop_duplicates(); mapped=sm[['source_dataset','measure']].drop_duplicates(); check=pairs.merge(mapped,how='left',indicator=True)
    issues.append(dict(severity='pass' if (check._merge=='left_only').sum()==0 else 'error',check='all source-measure pairs mapped',count=int((check._merge=='left_only').sum()),message='Every loaded source-measure pair has a mapping row.'))
    prov=pd.read_csv(DOWNLOADS/'provenance_audit.csv')
    complete=prov['provenance_complete'].astype(str).str.lower().isin(['true','1'])
    issues.append(dict(severity='pass' if complete.all() else 'error',check='complete observation provenance',count=int((~complete).sum()),message=f'{int(complete.sum())}/{len(prov)} observations have URL, locator, source record id and transformation.'))
    unloaded=reg[pd.to_numeric(reg.loaded_observations,errors='coerce').fillna(0).eq(0)]
    issues.append(dict(severity='info',check='registered sources without loaded observations',count=len(unloaded),message=' | '.join(unloaded.source_id.astype(str))))
    issues.append(dict(severity='info',check='alternative/equivalence groups',count=len(eqdf),message='Groups preserve competing or duplicate observations rather than silently dropping them.'))
    sync=pd.DataFrame(issues); sync.to_csv(DOWNLOADS/'synchronisation_audit.csv',index=False,encoding='utf-8-sig')

    # JS exports.
    def write_js(name,var,records):
        (DATA/name).write_text(f'window.{var} = '+json.dumps(records,ensure_ascii=False,separators=(',',':'),default=str)+';\n',encoding='utf-8')
    # replace observations JS with enriched records
    records=obs.where(pd.notna(obs),None).to_dict('records')
    write_js('observations.js','CPE_OBSERVATIONS',records)
    write_js('sources.js','CPE_SOURCES',reg.where(pd.notna(reg),None).to_dict('records'))
    write_js('measure_registry.js','CPE_MEASURE_REGISTRY',mr.where(pd.notna(mr),None).to_dict('records'))
    write_js('concept_registry.js','CPE_CONCEPT_REGISTRY',conceptdf.where(pd.notna(conceptdf),None).to_dict('records'))
    write_js('source_measure_map.js','CPE_SOURCE_MEASURE_MAP',sm.where(pd.notna(sm),None).to_dict('records'))
    write_js('source_relationships.js','CPE_SOURCE_RELATIONSHIPS',reldf.where(pd.notna(reldf),None).to_dict('records'))
    write_js('equivalence_groups.js','CPE_EQUIVALENCE_GROUPS',eqdf.where(pd.notna(eqdf),None).to_dict('records'))
    write_js('source_concept_coverage.js','CPE_SOURCE_CONCEPT_COVERAGE',covdf.where(pd.notna(covdf),None).to_dict('records'))
    write_js('jurisdictions.js','CPE_JURISDICTIONS',pd.DataFrame(jrows).where(pd.notna(pd.DataFrame(jrows)),None).to_dict('records'))
    write_js('sync_audit.js','CPE_SYNC_AUDIT',sync.where(pd.notna(sync),None).to_dict('records'))
    write_js('facility_crosswalk.js','CPE_FACILITY_CROSSWALK',fac.where(pd.notna(fac),None).to_dict('records'))
    # metadata
    meta=json.loads((DATA/'metadata.js').read_text(encoding='utf-8').split('=',1)[1].rsplit(';',1)[0])
    meta.update({'title':'Colonial Prison Statistics Explorer v7','observation_count':len(obs),'source_count_loaded':obs.source_dataset.nunique(),'source_count_registered':len(reg),'jurisdiction_count':obs.jurisdiction.nunique(),'measure_count':obs.measure.nunique(),'concept_count':mr.concept_id.nunique(),'unmapped_observations':int(len(unmapped)),'synchronisation_status':'pass' if all(x['severity']!='error' for x in issues) else 'error'})
    write_js('metadata.js','CPE_META',meta)
    return obs,reg,mr,sm,sync

def restore_ui():
    """Restore the hand-authored v7 interface after the data pipeline rebuild."""
    if not UI.exists():
        return
    shutil.copy2(UI/'index.html',SITE/'index.html')
    (SITE/'assets').mkdir(parents=True,exist_ok=True)
    shutil.copy2(UI/'app.js',SITE/'assets'/'app.js')
    shutil.copy2(UI/'styles.css',SITE/'assets'/'styles.css')
    # Keep research documentation downloadable after every rebuild.
    for src in [ROOT/'README_HE.md', ROOT/'DATA_SOURCES.md', ROOT/'docs'/'SOURCE_MAPPING_V7.md', ROOT/'docs'/'SYSTEM_QA_V7.md']:
        if src.exists():
            shutil.copy2(src, DOWNLOADS/src.name)
    runtime_report=ROOT/'docs'/'browser_qa_v7.json'
    if runtime_report.exists():
        shutil.copy2(runtime_report, DOWNLOADS/'browser_qa_v7.json')

def main():
    add_new_sources_and_snapshots()
    run_base_build()
    create_maps_and_audits()
    restore_ui()
    print('v7 enrichment complete')

if __name__=='__main__': main()
