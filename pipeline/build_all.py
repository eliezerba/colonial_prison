#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, shutil
from pathlib import Path
import pandas as pd
from common import ROOT,SITE,BUILD,CONFIG,CANONICAL_COLUMNS,ensure_dirs,canonicalize,read_registry,save_status,append_js,write_js,copy_configs_to_site,status,year_span
from ingest_palestine import ingest as ingest_palestine
from ingest_snapshots import ingest_nz_snapshot, ingest_canada_snapshot, ingest_hong_kong_snapshot, ingest_nz_ajhr_snapshot, ingest_microdata_source_snapshots, ingest_additional_verified_snapshots
from ingest_external import ingest_all

def _best_value(g, measure):
    x=g[(g['measure']==measure) & pd.to_numeric(g['value'],errors='coerce').notna()].copy()
    if x.empty: return None, None
    rr={'A':0,'B':1,'C':2,'U':3,'D':4}
    x['_r']=x['comparability_grade'].map(rr).fillna(9)
    r=x.sort_values(['_r']).iloc[0]
    return float(r['value']), r


def full_qa(df):
    """Research-oriented QA: preserve source disagreements; flag rather than silently reconcile."""
    qa=[]
    # Structural checks.
    if df['observation_id'].duplicated().any():
        qa.append({'source':'system','severity':'error','check':'duplicate observation ids','observed':int(df['observation_id'].duplicated().sum()),'message':'Observation IDs must be unique.'})
    neg=pd.to_numeric(df['value'],errors='coerce')<0
    if neg.any(): qa.append({'source':'system','severity':'error','check':'negative values','observed':int(neg.sum()),'message':'Negative counts/rates require explicit review.'})
    missing_url=df['source_url'].fillna('').astype(str).str.strip().eq('')
    if missing_url.any(): qa.append({'source':'system','severity':'error','check':'missing source URL','observed':int(missing_url.sum()),'message':'Every observation must return to a source URL.'})
    missing_record=df['source_record_id'].fillna('').astype(str).str.strip().eq('')
    if missing_record.any(): qa.append({'source':'system','severity':'error','check':'missing source record id','observed':int(missing_record.sum()),'message':'Every observation must have a stable source_record_id.'})
    locator=(df['source_table'].fillna('').astype(str).str.strip().ne('') | (df['source_sheet'].fillna('').astype(str).str.strip().ne('') & (df['source_column'].fillna('').astype(str).str.strip().ne('') | df['source_header'].fillna('').astype(str).str.strip().ne(''))))
    if (~locator).any(): qa.append({'source':'system','severity':'error','check':'missing source locator','observed':int((~locator).sum()),'message':'Every observation must identify a source table, or a source sheet plus column/header.'})
    grade_a=df['comparability_grade'].fillna('').eq('A')
    def_ok=df['definition_verified'].fillna(False).astype(str).str.lower().isin(['true','1','yes'])
    if (grade_a & ~def_ok).any(): qa.append({'source':'system','severity':'error','check':'Grade A definition not verified','observed':int((grade_a & ~def_ok).sum()),'message':'Grade A is reserved for observations whose definition has been explicitly verified.'})
    missing_transformation=df['transformation'].fillna('').astype(str).str.strip().eq('')
    if missing_transformation.any(): qa.append({'source':'system','severity':'error','check':'missing transformation documentation','observed':int(missing_transformation.sum()),'message':'Every observation must document whether it was transcribed directly, derived, recomputed, or retained as a proxy.'})

    # Preferred-observation uniqueness: within one source and semantic key, there should be at most one Grade-A row.
    pref=df[df['comparability_grade'].eq('A')].copy()
    sem_key=['source_dataset','jurisdiction','year','geography_level','geography_name','facility_name','measure','legal_status','sex','age_group','sentence_band']
    if len(pref):
        dup=pref.groupby(sem_key,dropna=False).size()
        bad=dup[dup>1]
        if len(bad): qa.append({'source':'system','severity':'error','check':'multiple preferred observations','observed':int(len(bad)),'message':'More than one Grade-A observation exists for the same source/year/geography/measure semantic key. Resolve the preferred field or downgrade aliases.'})

    # Arithmetic rate validation when numerator and denominator are both present.
    rate_specs=[('avg_daily_total','avg_daily_rate_per_100000'),('stock_eoy_total','stock_eoy_rate_per_100000'),('admissions_total','admissions_rate_per_100000'),('admissions_convicted','admissions_convicted_rate_per_100000')]
    for (j,y),g in df[df['geography_level'].eq('system')].groupby(['jurisdiction','year']):
        pop,_=_best_value(g,'population_denominator')
        if pop is None or pop==0: continue
        for num_m,rate_m in rate_specs:
            num,_=_best_value(g,num_m); rate,_=_best_value(g,rate_m)
            if num is None or rate is None: continue
            expected=num/pop*100000
            tol=max(0.25,abs(expected)*0.0075)
            if abs(rate-expected)>tol:
                qa.append({'source':'system','severity':'error','jurisdiction':j,'year':int(float(y)),'check':'rate arithmetic','observed':round(rate-expected,4),'message':f'{rate_m} does not reconcile to {num_m} / population_denominator × 100000 within rounding tolerance.'})

    # Palestine component checks – explicitly compare published components to published totals.
    sysdf=df[df['geography_level'].isin(['system','territory','jurisdiction'])]
    for (j,y),g in sysdf.groupby(['jurisdiction','year']):
        total,_=_best_value(g,'stock_eoy_total'); conv,_=_best_value(g,'stock_eoy_convicted'); non,_=_best_value(g,'stock_eoy_nonconvicted')
        if total is not None and conv is not None and non is not None:
            delta=total-conv-non
            if abs(delta)>0.5:
                qa.append({'source':'PAL_V2' if j=='Mandatory Palestine' else 'derived','severity':'warning','jurisdiction':j,'year':int(float(y)),'check':'stock components reconcile','observed':round(delta,3),'message':'Reported stock total differs from convicted + non-convicted. Source figures are preserved; definitions/reference dates may differ.'})
        if j=='Mandatory Palestine':
            adm,_=_best_value(g,'admissions_total'); ac,_=_best_value(g,'admissions_convicted'); saf,_=_best_value(g,'admissions_safe_custody'); deb,_=_best_value(g,'admissions_debtors')
            if all(v is not None for v in [adm,ac,saf,deb]):
                delta=adm-ac-saf-deb
                if abs(delta)>0.5:
                    sev='warning' if abs(delta)<100 else 'review'
                    qa.append({'source':'PAL_V2','severity':sev,'jurisdiction':j,'year':int(float(y)),'check':'admissions components reconcile','observed':round(delta,3),'message':'Total admissions differs from convicted + safe-custody + debtor admissions. Do not force reconciliation; inspect category universe/transfers/special detention.'})

    # Known live-V2 audit finding: the chart/rate columns are mislabeled if interpreted as stock rates.
    qa.append({'source':'PAL_V2','severity':'critical','jurisdiction':'Mandatory Palestine','check':'V2 derived-rate label audit','observed':'admissions numerator','message':'The live V2 table labels a derived series as prisoners per 1,000, but printed values equal admissions/population (e.g. 1930). Dashboard ignores that derived label and recalculates stock/admissions rates from explicit numerators.'})
    qa.append({'source':'PAL_V2','severity':'info','jurisdiction':'Mandatory Palestine','year':1932,'check':'audited clean-field conflict','observed':'10,161 vs 19,161','message':'Convicted admissions clean cell conflicts with raw/source breakdown. Preferred audited observation = 19,161; original row retained for provenance.'})
    qa.append({'source':'PAL_V2','severity':'info','jurisdiction':'Mandatory Palestine','year':1944,'check':'live-V2 summary/raw conflict','observed':'8,663 vs 8,633','message':'The live V2 summary table prints 8,663 convicted admissions, while the raw annual-report row gives 8,633 and the latter exactly reconciles the admissions components. Dashboard keeps 8,633 and flags the summary discrepancy.'})

    # Comparability semantics: Canadian Z173-174 penitentiary rows must never masquerade as whole-system totals.
    can=df[(df['source_dataset']=='CAN_HSC_Z') & (df['source_table'].astype(str).str.contains('Z173-174',na=False))]
    bad=can[can['geography_level']=='system']
    if len(bad): qa.append({'source':'CAN_HSC_Z','severity':'error','check':'institution universe','observed':len(bad),'message':'Z173-174 penitentiary-only rows must not be classified as whole-system.'})

    # Canadian admissions semantics: Z175-182 is explicitly male admissions, never system total admissions.
    can_adm=df[(df['source_dataset']=='CAN_HSC_Z') & (df['source_table'].astype(str).str.contains('Z175-182',na=False))]
    bad_total=can_adm[can_adm['measure']=='admissions_total']
    if len(bad_total): qa.append({'source':'CAN_HSC_Z','severity':'error','check':'admissions universe','observed':len(bad_total),'message':'Z175-182 contains male penitentiary admissions and must not be mapped to admissions_total.'})

    # Preserve and audit source-reported rates separately when a table also supplies numerator and denominator.
    eaf=df[df['source_dataset'].eq('EAF_1938_JSH')]
    for (j,y),g in eaf.groupby(['jurisdiction','year']):
        a,_=_best_value(g,'avg_daily_total'); pop,_=_best_value(g,'population_denominator'); sr,_=_best_value(g,'source_reported_avg_daily_rate_per_100000')
        if a is None or pop in (None,0) or sr is None: continue
        expected=a/pop*100000
        if abs(sr-expected)>max(0.25,abs(expected)*0.0075):
            qa.append({'source':'EAF_1938_JSH','severity':'warning','jurisdiction':j,'year':int(float(y)),'check':'source-reported rate consistency','observed':round(sr-expected,4),'message':'Published per-100,000 rate does not reconcile to the population and daily-average values printed in the same table. Published rate is preserved as source-specific; comparison charts use a recomputed canonical rate.'})

    # World Prison Brief historical trend rows are useful secondary comparisons, but the exact within-year reference date is not specified.
    wpb=df[df['source_dataset'].astype(str).str.endswith('_WPB_HIST')]
    if len(wpb):
        bad=wpb[~wpb['comparability_grade'].isin(['B','C','D'])]
        if len(bad): qa.append({'source':'WPB_HIST','severity':'error','check':'historical reference-date semantics','observed':len(bad),'message':'Historical World Prison Brief trend rows must not be Grade A unless an exact reference date is independently verified.'})
        qa.append({'source':'WPB_HIST','severity':'info','check':'historical reference-date semantics','observed':len(wpb),'message':'World Prison Brief historical population totals are retained as Grade B because the precise within-year reference date is not stated at the level required for exact 31 December equivalence.'})

    # Raw cross-jurisdiction unit audit. Different original currencies are preserved but must not be compared as raw magnitudes.
    for m,g in df.groupby('measure'):
        units=sorted(set(str(x) for x in g['unit'].dropna() if str(x).strip()))
        if len(units)>1 and len(set(g['jurisdiction'].dropna().astype(str)))>1:
            qa.append({'source':'system','severity':'info','check':'cross-jurisdiction unit heterogeneity','observed':f'{m}: {units}','message':'Raw cross-jurisdiction comparison must normalize units or use an index; the dashboard comparison lab blocks/flags incompatible raw units.'})

    # Proxy discipline.
    proxies=df[df['measure_class'].astype(str).str.lower().eq('proxy')]
    if len(proxies): qa.append({'source':'system','severity':'info','check':'proxy observations','observed':len(proxies),'message':'Proxy rows are retained in source/data explorer layers and must not be silently substituted for official prison stock.'})
    return qa

def build(network=False):
    ensure_dirs(); statuses=[]; dfs=[]
    pal,st=ingest_palestine(network=network); dfs.append(pal); statuses.append(st)
    nz,st=ingest_nz_snapshot(); dfs.append(nz); statuses.append(st)
    for fn in [ingest_canada_snapshot, ingest_hong_kong_snapshot, ingest_nz_ajhr_snapshot]:
        d,st=fn(); dfs.append(d); statuses.append(st)
    mdfs,msts=ingest_microdata_source_snapshots(); dfs.extend(mdfs); statuses.extend(msts)
    adfs,asts=ingest_additional_verified_snapshots(); dfs.extend(adfs); statuses.extend(asts)
    if network:
        ex,sts=ingest_all(network=True); dfs.extend(ex); statuses.extend(sts)
    else:
        reg=read_registry(); loaded_ids={str(x.get('source_id')) for x in statuses if x.get('state')=='loaded'}
        for sid in reg['source_id']:
            if sid not in loaded_ids: statuses.append(status(sid,'refreshable','Run pipeline/build_all.py --network or use the included GitHub Actions workflow to attempt structured-source refresh.',0,'','not_run'))
    all_df=canonicalize(pd.concat([d for d in dfs if d is not None and not d.empty],ignore_index=True).to_dict('records'))
    # Prefer bundled verified NZ snapshot for overlapping canonical concepts; network rows extend coverage.
    if len(all_df):
        nzmask=all_df['source_dataset'].eq('NZ_OYB')
        nz=all_df[nzmask].copy(); other=all_df[~nzmask].copy()
        if len(nz):
            nz['_snapshot_rank']=nz['notes'].fillna('').str.contains('Verified retrospective').map({True:0,False:1})
            key=['source_dataset','jurisdiction','year','geography_level','facility_name','measure','legal_status','sex','age_group','sentence_band']
            nz=nz.sort_values(['_snapshot_rank']).drop_duplicates(key,keep='first').drop(columns=['_snapshot_rank'])
            all_df=pd.concat([other,nz],ignore_index=True)
    # deterministic sort
    if not all_df.empty: all_df=all_df.sort_values(['jurisdiction','year','geography_level','facility_name','measure','observation_id'],na_position='last')
    out=SITE/'downloads'/'observations.csv'; all_df.to_csv(out,index=False,encoding='utf-8-sig')
    # JS chunks by jurisdiction: local file:// compatible, no fetch required
    data_dir=SITE/'data'; data_dir.mkdir(exist_ok=True)
    for old in data_dir.glob('observations_*.js'): old.unlink()
    chunk_files=[]
    for i,(jur,g) in enumerate(all_df.groupby('jurisdiction',dropna=False)):
        name=f'observations_{i:02d}_{str(jur).lower().replace(" ","_").replace("–","-")[:35]}.js'
        append_js(data_dir/name,'CPE_OBSERVATIONS',g.where(pd.notna(g),None).to_dict('records')); chunk_files.append(name)
    write_js(data_dir/'observations.js','CPE_OBSERVATIONS',all_df.where(pd.notna(all_df),None).to_dict('records'))
    reg=read_registry()
    statdf=pd.DataFrame(statuses)
    if len(statdf):
        rank={'loaded':0,'requires_review':1,'refreshable':2,'not_run':3,'failed':4}
        statdf['_rank']=statdf['state'].map(rank).fillna(9)
        # choose best usable state, concatenate messages from all attempts
        msgs=statdf.groupby('source_id')['message'].apply(lambda x:' | '.join(dict.fromkeys(str(v) for v in x if str(v)))).to_dict()
        statdf=statdf.sort_values(['source_id','_rank','rows'],ascending=[True,True,False]).drop_duplicates('source_id').drop(columns=['_rank'])
        statdf['message']=statdf['source_id'].map(msgs)
    merged=reg.merge(statdf,on='source_id',how='left')
    merged['state']=merged['state'].fillna('not_run'); merged['rows']=pd.to_numeric(merged['rows'],errors='coerce').fillna(0).astype(int)
    # calculate actual loaded ranges/counts, preferred over status estimates
    actual=all_df.groupby('source_dataset').agg(loaded_observations=('observation_id','count'),loaded_min_year=('year','min'),loaded_max_year=('year','max')).reset_index().rename(columns={'source_dataset':'source_id'}) if len(all_df) else pd.DataFrame(columns=['source_id','loaded_observations','loaded_min_year','loaded_max_year'])
    merged=merged.merge(actual,on='source_id',how='left'); merged['loaded_observations']=merged['loaded_observations'].fillna(0).astype(int)
    sources=merged.where(pd.notna(merged),None).to_dict('records')
    qa=full_qa(all_df)
    registered=set(reg['source_id'].astype(str))
    unregistered=sorted(set(all_df['source_dataset'].dropna().astype(str))-registered)
    if unregistered:
        qa.append({'source':'system','severity':'error','check':'unregistered source dataset','observed':' | '.join(unregistered),'message':'Every observation source_dataset must exist in source_registry.csv.'})
    # Row-level provenance audit. This does not claim historical truth; it verifies that every published value is traceable to the dataset/source location from which it was taken.
    pa=all_df[['observation_id','source_dataset','jurisdiction','year','measure','comparability_grade','definition_verified','source_url','historical_source_url','source_sheet','source_column','source_header','source_table','source_record_id','transformation','quality_flag']].copy()
    pa['source_url_present']=pa['source_url'].fillna('').astype(str).str.startswith('http')
    pa['source_locator_present']=pa['source_table'].fillna('').astype(str).str.strip().ne('') | (pa['source_sheet'].fillna('').astype(str).str.strip().ne('') & (pa['source_column'].fillna('').astype(str).str.strip().ne('') | pa['source_header'].fillna('').astype(str).str.strip().ne('')))
    pa['source_record_id_present']=pa['source_record_id'].fillna('').astype(str).str.strip().ne('')
    pa['transformation_documented']=pa['transformation'].fillna('').astype(str).str.strip().ne('')
    pa['provenance_complete']=pa[['source_url_present','source_locator_present','source_record_id_present','transformation_documented']].all(axis=1)
    def _verification_class(r):
        if str(r.get('quality_flag','')).find('proxy')>=0 or str(r.get('comparability_grade',''))=='D': return 'source/proxy_only'
        if str(r.get('definition_verified','')).lower() in {'true','1','yes'} and str(r.get('comparability_grade',''))=='A': return 'definition_verified_direct'
        if str(r.get('definition_verified','')).lower() in {'true','1','yes'}: return 'definition_verified_with_comparability_caveat'
        return 'source_traceable_definition_pending'
    pa['verification_class']=pa.apply(_verification_class,axis=1)
    pa.to_csv(SITE/'downloads'/'provenance_audit.csv',index=False,encoding='utf-8-sig')
    # Source-level verification summary generated from the row-level audit.
    src_rows=[]
    for sid,g in all_df.groupby('source_dataset',dropna=False):
        pg=pa[pa['source_dataset'].eq(sid)]
        grades=g['comparability_grade'].fillna('').astype(str).value_counts().to_dict()
        defs=g['definition_verified'].fillna(False).astype(str).str.lower().isin(['true','1','yes'])
        classes=pg['verification_class'].value_counts().to_dict()
        src_rows.append({
            'source_id':sid,'loaded_observations':len(g),'min_year':pd.to_numeric(g['year'],errors='coerce').min(),'max_year':pd.to_numeric(g['year'],errors='coerce').max(),
            'provenance_complete':int(pg['provenance_complete'].sum()),'provenance_complete_pct':round(100*pg['provenance_complete'].mean(),2) if len(pg) else 0,
            'definition_verified':int(defs.sum()),'definition_verified_pct':round(100*defs.mean(),2) if len(g) else 0,
            'grade_A':int(grades.get('A',0)),'grade_B':int(grades.get('B',0)),'grade_C':int(grades.get('C',0)),'grade_U':int(grades.get('U',0)),'grade_D':int(grades.get('D',0)),
            'definition_verified_direct':int(classes.get('definition_verified_direct',0)),
            'definition_verified_with_caveat':int(classes.get('definition_verified_with_comparability_caveat',0)),
            'source_traceable_definition_pending':int(classes.get('source_traceable_definition_pending',0)),
            'source_proxy_only':int(classes.get('source/proxy_only',0))
        })
    sv=pd.DataFrame(src_rows).merge(reg[['source_id','name','url']],on='source_id',how='left')
    sv.to_csv(SITE/'downloads'/'source_verification_audit.csv',index=False,encoding='utf-8-sig')
    # add source statuses requiring attention
    for s in sources:
        if s.get('state') in {'failed','requires_review'}: qa.append({'source':s['source_id'],'severity':'warning','check':'ingest status','observed':s.get('state'),'message':s.get('message','')})
    # dataset metadata
    measures=sorted(x for x in all_df['measure'].dropna().astype(str).unique() if x)
    jurisdictions=sorted(x for x in all_df['jurisdiction'].dropna().astype(str).unique() if x)
    years=pd.to_numeric(all_df['year'],errors='coerce').dropna().astype(int)
    meta={'title':'Colonial Prison Statistics Explorer','build_mode':'network' if network else 'offline_snapshots','observation_count':len(all_df),'jurisdictions':jurisdictions,'measures':measures,'min_year':int(years.min()) if len(years) else None,'max_year':int(years.max()) if len(years) else None,'observation_chunks':chunk_files}
    write_js(data_dir/'metadata.js','CPE_META',meta); write_js(data_dir/'sources.js','CPE_SOURCES',sources); write_js(data_dir/'qa.js','CPE_QA',qa)
    pd.DataFrame(qa).to_csv(SITE/'downloads'/'quality_audit.csv',index=False,encoding='utf-8-sig')
    for cfg,var in [('variable_crosswalk.csv','CPE_VARIABLE_CROSSWALK'),('facility_crosswalk.csv','CPE_FACILITY_CROSSWALK'),('validation_rules.csv','CPE_VALIDATION_RULES')]:
        p=CONFIG/cfg
        if p.exists(): write_js(data_dir/cfg.replace('.csv','.js'),var,pd.read_csv(p,dtype=str).fillna('').to_dict('records'))
    # Site data loader with static script tags. This is regenerated every build.
    loader=['window.CPE_OBSERVATIONS = [];']+[f'/* {x} */' for x in chunk_files]
    (data_dir/'chunk_manifest.json').write_text(json.dumps(chunk_files,ensure_ascii=False,indent=2),encoding='utf-8')
    (BUILD/'chunk_tags.html').write_text('\n'.join(f'<script src="data/{x}"></script>' for x in chunk_files),encoding='utf-8')
    copy_configs_to_site(); save_status(statuses)
    # Publish the enriched registry (including actual loaded counts/ranges) after static configs are copied.
    merged.to_csv(SITE/'downloads'/'source_registry.csv',index=False,encoding='utf-8-sig')
    shutil.copy2(BUILD/'build_status.csv',SITE/'downloads'/'build_status.csv')
    shutil.copy2(CONFIG/'palestine_data_dictionary.csv',SITE/'downloads'/'palestine_data_dictionary.csv')
    audit_md=ROOT/'docs'/'QUALITY_AUDIT.md'
    if audit_md.exists(): shutil.copy2(audit_md,SITE/'downloads'/'QUALITY_AUDIT.md')
    verify_md=ROOT/'docs'/'SOURCE_VERIFICATION_RUN_2026-08-14.md'
    if verify_md.exists(): shutil.copy2(verify_md,SITE/'downloads'/'SOURCE_VERIFICATION_RUN_2026-08-14.md')
    print(json.dumps(meta,ensure_ascii=False,indent=2))
    return meta, chunk_files

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--network',action='store_true'); args=ap.parse_args(); build(args.network)
