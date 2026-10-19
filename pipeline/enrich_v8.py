#!/usr/bin/env python3
"""Version 8 orchestration: v7 data semantics and UI retained with curated source extensions."""
from pathlib import Path
import json,shutil
import pandas as pd
import enrich_v7 as base

NEW_SOURCES=[
 dict(source_id='SCT_UK_PARL_2017',name='Scottish prison population, historical daily averages (Commons Library 2017)',jurisdiction='Scotland',institution='House of Commons Library / Scottish Government',years_available='1920-1950',overlap_with_palestine='1920-1948',data_level='annual system average',format='PDF historical table',structured_access='curated CSV included',api='none',population_measures='daily-average prison population total',other_measures='',automation_level='offline verified snapshot',comparability_role='metropolitan comparator; daily average',priority='P1',status='loaded',url='https://www.breizh-info.com/wp-content/uploads/2017/11/SN04334.pdf',ingest_strategy='manual transcribed Table 10a, p.39, archived Commons report'),
 dict(source_id='NIR_AAS_1937_47',name='Northern Ireland Annual Abstract of Statistics, Tables 72-73, 1937-1947',jurisdiction='Northern Ireland',institution='Ministry of Home Affairs / UK Government',years_available='1937-1947',overlap_with_palestine='1937-1947',data_level='annual system aggregate and legal-status breakdown',format='historical statistical PDF',structured_access='curated CSV included',api='none',population_measures='receptions; daily-average populations by conviction status',other_measures='convicted persons; prior-offence prevalence',automation_level='offline verified snapshot',comparability_role='domestic comparator; reporting scopes documented',priority='P1',status='loaded',url='https://escoe-website.s3.amazonaws.com/wp-content/uploads/2022/12/11173048/Annual-Abstract-of-Statistics-1937-1947.pdf',ingest_strategy='manual transcribed Tables 72 and 73, printed p.68'),
 dict(source_id='BAS_COL_REPORT_1937',name='Basutoland colonial administration annual report 1937: prisons',jurisdiction='Basutoland',institution='Colonial Office / British Government (University of Illinois digital archive)',years_available='1936-1937',overlap_with_palestine='1936-1937',data_level='territorial prison system and adults only',format='historical PDF',structured_access='curated CSV included',api='none',population_measures='admissions; adult daily-average',other_measures='penal imprisonment commitments',automation_level='offline verified snapshot',comparability_role='colonial comparator; adult-only mean qualified',priority='P2',status='loaded',url='https://libsysdigi.library.illinois.edu/ilharvest/Africana/Books2011-05/469256/469256_1937/469256_1937_opt.pdf',ingest_strategy='manual transcribed p.42 prison statistics'),
 dict(source_id='UGA_WPB_HIST',name='Uganda World Prison Brief historical population (comparison blocked pending source audit)',jurisdiction='Uganda',institution='ICPR World Prison Brief',years_available='1921, 1927, 1934, 1938, 1944',overlap_with_palestine='1921-1944',data_level='uncertain historic point or average',format='HTML historical table',structured_access='curated CSV included',api='none',population_measures='historical population point unverified reference basis',other_measures='source conflict with 1938 colonial table',automation_level='offline verified snapshot',comparability_role='source-specific only; blocked from comparison',priority='P1 review',status='loaded restricted',url='https://prisonstudies.org/country/uganda?language_content_entity=en-gb',ingest_strategy='historical values retained, blocked in compare until scope resolved')
]
# Extend without changing the existing taxonomy's underlying meanings.
_old_family=base.family_for_measure
def v8_family(m):
    if m.startswith('avg_month_end_') or m in {'avg_daily_convicted','avg_daily_unconvicted','avg_daily_adults','avg_daily_sentenced','avg_daily_juveniles'}:
        return 'custodial_population_average'
    if m.startswith('male_convicted_prior_offences'):
        return 'recidivism'  # descriptive category only; never infer a repeat-offending rate
    if m.startswith('convicted_prisoners_') or m=='convicted_prisoners_count':
        return 'custodial_population_composition'
    if m=='interinstitutional_transfers': return 'movement_and_outcomes'
    if 'receptions' in m or m=='admissions_penal_imprisonment': return 'admissions_flow'
    return _old_family(m)
base.family_for_measure=v8_family
_old_basis=base.time_basis_for_measure
def v8_basis(m):
    if m.startswith('avg_month_end_'):return 'mean_of_12_month_end_snapshots'
    if m=='avg_daily_adults':return 'annual_daily_average_adults_only'
    if m=='avg_daily_sentenced':return 'annual_daily_average_sentenced_only'
    if m.startswith('avg_daily_'):return 'annual_daily_average'
    if m=='interinstitutional_transfers' or 'receptions' in m:return 'annual_flow'
    if 'prior_offences' in m:return 'annual_convicted_prevalence_not_recidivism_rate'
    return _old_basis(m)
base.time_basis_for_measure=v8_basis
_old_source=base.source_family
def v8_source(r):
    sid=str(r.get('source_id',''))
    if sid in {'SCT_UK_PARL_2017','NIR_AAS_1937_47','BAS_COL_REPORT_1937'}:return ('official_publication','A/B','official')
    if sid=='UGA_WPB_HIST':return ('secondary_structured_database','U','secondary_review')
    return _old_source(r)
base.source_family=v8_source
base.KEY_LABELS_HE.update({
 'avg_month_end_total':'ממוצע של 12 מצבות סוף־חודש',
 'avg_month_end_male':'ממוצע 12 מצבות סוף־חודש — גברים',
 'avg_month_end_female':'ממוצע 12 מצבות סוף־חודש — נשים',
 'receptions_excluding_transfers':'קבלות בניכוי העברות בין־מוסדיות',
 'receptions_gross_including_transfers':'כל הקבלות לרבות העברות',
 'interinstitutional_transfers':'העברות בין־מוסדיות',
 'avg_daily_convicted':'ממוצע יומי — מורשעים',
 'avg_daily_unconvicted':'ממוצע יומי — לא־מורשעים',
 'avg_daily_adults':'ממוצע יומי — מבוגרים בלבד',
 'avg_daily_juveniles':'ממוצע יומי — קטינים',
 'avg_daily_sentenced':'ממוצע יומי — נושאי עונש בלבד',
 'convicted_prisoners_count':'מורשעים בתקופת הדיווח',
 'convicted_prisoners_male':'מורשעים — גברים',
 'convicted_prisoners_female':'מורשעים — נשים',
 'male_convicted_prior_offences_pct':'שיעור גברים מורשעים עם עבירות קודמות מוכחות',
 'admissions_penal_imprisonment':'קבלות למאסר עונשי'
})
base.REGION.update({'Scotland':'Europe','Northern Ireland':'Europe'})
base.COORDS.update({'Scotland':(56.4907,-4.2026),'Northern Ireland':(54.7877,-6.4923)})

def append_v8_qa():
    """Surface source-specific research issues alongside the inherited source audits."""
    f=base.DOWNLOADS/'quality_audit.csv'
    qa=pd.read_csv(f,dtype=str).fillna('').to_dict('records')
    qa.extend([
      dict(source='UGA_WPB_HIST',severity='critical',jurisdiction='Uganda',year=1938,
           check='source universe discrepancy / compare blocked',observed='1,318 vs 4,225',
           message='World Prison Brief historic prison population = 1,318, while colonial comparative 1938 table reports daily average 4,225. Differences in reference period, universe or category not resolved. All 5 Uganda WPB historical rows are explicitly excluded from comparison and map figures.'),
      dict(source='NZ_AJHR_PRISONS',severity='review',jurisdiction='New Zealand',year=1937,
           check='daily average narrative versus retrospective table',observed='860 vs 866',
           message='1938 official report retrospective table shows 860 daily average in 1937; narrative says 866. Table value is transcribed with caveat. No silent numerical reconciliation.'),
      dict(source='EAW_PARL_HIST',severity='info',jurisdiction='England & Wales',year='',
           check='mean of twelve month-end snapshots (not daily mean)',observed='99 corrected observations',
           message='In v7 this source was labelled avg_daily. V8 replaces all 18 old rows with 99 accurately labelled records from table 1a; any concept-level comparison against Palestine daily averages is explicitly qualified.'),
      dict(source='NIR_AAS_1937_47',severity='info',jurisdiction='Northern Ireland',year='',
           check='prior-offence prevalence != reoffending rate',observed='11 historical percentages',
           message='Table 73 describes previous proved offences among convicted men. This is not a prospective reconviction or recidivism incidence rate.'),
      dict(source='BAS_COL_REPORT_1937',severity='info',jurisdiction='Basutoland',year='',
           check='adult-only mean',observed='2 adult daily means',
           message='Colonial report daily mean covers adult prisoners, not necessarily all persons in detention. No direct substitution into total mean trend.'),
      dict(source='HKG_ADMIN',severity='info',jurisdiction='Hong Kong',year=1946,
           check='sentenced-only daily mean',observed='1,214',
           message='1946 annual report daily average is for persons serving sentence; this must not be presented as total average custodial population.')
    ])
    pd.DataFrame(qa).to_csv(f,index=False,encoding='utf-8-sig')
    (base.DATA/'qa.js').write_text('window.CPE_QA = '+json.dumps(qa,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')

def main():
    base.add_new_sources_and_snapshots()
    rp=base.CONFIG/'source_registry.csv'
    reg=pd.read_csv(rp,dtype=str).fillna('')
    incoming=[x for x in NEW_SOURCES if x['source_id'] not in set(reg['source_id'])]
    if incoming:reg=pd.concat([reg,pd.DataFrame(incoming,columns=reg.columns)],ignore_index=True)
    reg.to_csv(rp,index=False,encoding='utf-8-sig')
    base.run_base_build()
    append_v8_qa()
    obs,reg,mr,sm,sync=base.create_maps_and_audits()
    base.restore_ui()
    meta_path=base.DATA/'metadata.js'
    s=meta_path.read_text(encoding='utf-8');meta=json.loads(s.split('=',1)[1].rsplit(';',1)[0])
    meta.update({'title':'Colonial Prison Statistics Explorer v8.2','version':'8.2','palestine_role':'fixed_case_reference','v8_new_sources':['SCT_UK_PARL_2017','NIR_AAS_1937_47','BAS_COL_REPORT_1937','UGA_WPB_HIST']})
    meta_path.write_text('window.CPE_META = '+json.dumps(meta,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    for f in [base.ROOT/'docs'/'DATA_EXPANSION_V8.md',base.ROOT/'docs'/'V8_QA_REPORT.md',base.ROOT/'docs'/'browser_qa_v8.json',base.ROOT/'docs'/'EAW_V7_RECLASSIFICATION_AUDIT.csv',base.ROOT/'docs'/'V8_1_UX_AND_DEPLOYMENT.md']:
        if f.exists():shutil.copy2(f,base.DOWNLOADS/f.name)
    print('v8 complete:',len(obs),'observations;',len(reg),'sources;',obs.jurisdiction.nunique(),'jurisdictions')

if __name__=='__main__':main()
