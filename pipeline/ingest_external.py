from __future__ import annotations
import io, json, re, tempfile, zipfile
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
from common import RAW, canonicalize, download, http_get, norm_text, num, parse_year, status, year_span


def slug(s):
    s=norm_text(s).lower(); s=re.sub(r'[^a-z0-9]+','_',s).strip('_'); return s[:80] or 'value'

def keyword_measure(label, context=''):
    x=(label+' '+context).lower()
    if 'daily average' in x or 'average daily' in x or ('average' in x and 'prison' in x): return ('avg_daily_total','average','A')
    if ('31st december' in x or '31 december' in x or 'end of year' in x or 'last day' in x or 'on register' in x) and ('prison' in x or 'confinement' in x or 'inmate' in x): return ('stock_eoy_total','stock','B')
    if 'awaiting trial' in x or 'on remand' in x or 'remand' in x: return ('stock_eoy_remand','stock','B')
    if 'undergoing sentence' in x or ('convict' in x and ('number' in x or 'prisoner' in x)): return ('stock_eoy_convicted','stock','B')
    if 'admission' in x or 'received during' in x or 'committed' in x: return ('admissions_total','flow','B')
    if 'previously convicted' in x or 'recidiv' in x: return ('recidivists','flow','B')
    if 'expenditure' in x or 'operating cost' in x or 'cost of' in x: return ('expenditure_total','finance','B')
    if 'death' in x or 'mortality' in x: return ('deaths_in_custody','flow','C')
    return ('source_specific__'+slug(label),'source_specific','U')

def generic_year_table(df, jurisdiction, source_id, source_url, source_table, context='', geography='system'):
    """Conservative table normalizer. It maps only labels with unambiguous keywords; otherwise retains source-specific measures."""
    rows=[]
    if df is None or df.empty: return canonicalize([])
    df=df.copy()
    df.columns=[norm_text(' '.join(map(str,c)) if isinstance(c,tuple) else c) for c in df.columns]
    # Form A: year is a row field
    year_col=next((c for c in df.columns if c.lower() in {'year','date','calendar year','reporting year'} or c.lower().startswith('year ')),None)
    if year_col:
        for _,r in df.iterrows():
            period,ys,ye,y=parse_year(r.get(year_col))
            if y is None: continue
            for c in df.columns:
                if c==year_col: continue
                v=num(r.get(c))
                if v is None: continue
                measure,mclass,grade=keyword_measure(c,context+' '+source_table)
                rows.append({'jurisdiction':jurisdiction,'year':y,'reporting_period':period,'year_start':ys,'year_end':ye,
                    'geography_level':geography,'geography_name':jurisdiction,'measure':measure,'measure_class':mclass,'value':v,'unit':'persons' if mclass in {'stock','flow','average'} else '',
                    'source_dataset':source_id,'source_header':c,'source_table':source_table,'source_url':source_url,'historical_source_url':source_url,
                    'transformation':'direct_numeric_from_structured_table','comparability_grade':grade,'quality_flag':'heuristic_column_mapping' if grade!='A' else '',
                    'definition_verified':'false','source_record_id':f'{source_table}:{y}:{c}','notes':context})
        return canonicalize(rows)
    # Form B: years are columns, row labels on left
    years={c:parse_year(c)[3] for c in df.columns}
    ycols={c:y for c,y in years.items() if y and 1800<=y<=2100}
    if ycols:
        nonyears=[c for c in df.columns if c not in ycols]
        labelcol=nonyears[0] if nonyears else None
        for idx,r in df.iterrows():
            label=norm_text(r.get(labelcol)) if labelcol else f'row_{idx}'
            if not label: label=f'row_{idx}'
            measure,mclass,grade=keyword_measure(label,context+' '+source_table)
            for c,y in ycols.items():
                v=num(r.get(c))
                if v is None: continue
                rows.append({'jurisdiction':jurisdiction,'year':y,'reporting_period':str(y),'year_start':y,'year_end':y,
                    'geography_level':geography,'geography_name':jurisdiction,'measure':measure,'measure_class':mclass,'value':v,'unit':'persons' if mclass in {'stock','flow','average'} else '',
                    'source_dataset':source_id,'source_header':label,'source_table':source_table,'source_url':source_url,'historical_source_url':source_url,
                    'transformation':'direct_numeric_from_structured_table','comparability_grade':grade,'quality_flag':'heuristic_row_mapping','definition_verified':'false',
                    'source_record_id':f'{source_table}:{idx}:{y}','notes':context})
    return canonicalize(rows)


def ingest_new_zealand(network=True):
    if not network: return canonicalize([]), status('NZ_OYB','refreshable','Network refresh not requested; bundled verified snapshot used separately.',0,'','network_disabled')
    allrows=[]; successes=0; failures=[]
    for year in range(1900,1951):
        urls=[f'https://www3.stats.govt.nz/New_Zealand_Official_Yearbooks/{year}/NZOYB_{year}.html',f'https://www3.stats.govt.nz/New_Zealand_Official_Yearbooks/{year}/NZOYB%20{year}.html']
        html=None; used=None
        for u in urls:
            try: html=http_get(u,timeout=20); used=u; break
            except Exception: pass
        if not html: failures.append(year); continue
        try: tables=pd.read_html(io.StringIO(html))
        except Exception: continue
        for i,t in enumerate(tables):
            probe=(' '.join(map(str,t.columns))+' '+t.astype(str).head(8).to_string()).lower()
            if not any(k in probe for k in ['prison','gaol','confinement','prisoner']): continue
            c=generic_year_table(t,'New Zealand','NZ_OYB',used,f'NZOYB {year} table {i+1}',context=f'Official Yearbook {year}')
            if len(c): allrows.extend(c.to_dict('records'))
            else:
                # Facility tables often omit an explicit Year column; the yearbook normally reports the preceding calendar year.
                tt=t.copy(); tt.columns=[norm_text(' '.join(map(str,x)) if isinstance(x,tuple) else x) for x in tt.columns]
                textcols=[c0 for c0 in tt.columns if not pd.to_numeric(tt[c0],errors='coerce').notna().mean()>0.65]
                facility_col=textcols[0] if textcols else tt.columns[0]
                report_year=year-1
                facility_rows=[]
                for ridx,rr in tt.iterrows():
                    facility=norm_text(rr.get(facility_col))
                    if not facility or facility.lower() in {'total','totals'}: facility=facility or 'System total'
                    for col in tt.columns:
                        if col==facility_col: continue
                        vv=num(rr.get(col))
                        if vv is None: continue
                        mm,mc,gg=keyword_measure(col,probe)
                        if mm.startswith('source_specific__') and not any(k in col.lower() for k in ['capacity','prison','gaol']): continue
                        facility_rows.append({'jurisdiction':'New Zealand','year':report_year,'reporting_period':str(report_year),'year_start':report_year,'year_end':report_year,'geography_level':'system' if facility.lower().startswith('system total') else 'facility','geography_name':'New Zealand','facility_name':'' if facility.lower().startswith('system total') else facility,'facility_type':'prison','measure':mm,'measure_class':mc,'value':vv,'unit':'persons' if mc in {'stock','flow','average'} else '','source_dataset':'NZ_OYB','source_url':used,'historical_source_url':used,'source_header':col,'source_table':f'NZOYB {year} table {i+1}','transformation':'direct numeric; report year inferred as yearbook year - 1','comparability_grade':gg,'quality_flag':'year_inferred_from_yearbook' if gg!='U' else 'source_specific|year_inferred_from_yearbook','definition_verified':'false','source_record_id':f'{year}:{i}:{ridx}:{col}'})
                if facility_rows: allrows.extend(canonicalize(facility_rows).to_dict('records'))
        successes+=1
    out=canonicalize(allrows)
    msg=f'Scraped {successes} yearbooks; {len(failures)} unavailable. Conservative heuristic mapping; review source-specific measures.'
    return out,status('NZ_OYB','loaded' if len(out) else 'failed',msg,len(out),year_span(out),'network_html')


def ingest_canada(network=True):
    url='https://www150.statcan.gc.ca/n1/pub/11-516-x/sectionz/4147446-eng.htm'
    if not network: return canonicalize([]), status('CAN_HSC_Z','refreshable','Network refresh not requested.',0,'','network_disabled')
    try: html=http_get(url,timeout=45)
    except Exception as e: return canonicalize([]),status('CAN_HSC_Z','failed',str(e),0,'','network')
    soup=BeautifulSoup(html,'html.parser')
    frames=[]
    # Direct HTML tables
    try:
        for i,t in enumerate(pd.read_html(io.StringIO(html))): frames.append((f'Section Z HTML table {i+1}',t,url))
    except Exception: pass
    # Linked CSVs, if present
    for a in soup.find_all('a',href=True):
        h=a['href']; text=norm_text(a.get_text(' '))
        if '.csv' not in (h+' '+text).lower(): continue
        from urllib.parse import urljoin
        u=urljoin(url,h)
        try:
            content=http_get(u,timeout=30)
            frames.append((text or Path(h).name,pd.read_csv(io.StringIO(content)),u))
        except Exception: pass
    rows=[]
    for title,df,u in frames:
        probe=(title+' '+' '.join(map(str,df.columns))).lower()
        if not any(k in probe for k in ['prison','penitenti','jail','penal','correction','z173','z174','z198','z201','z223','z226']): continue
        c=generic_year_table(df,'Canada','CAN_HSC_Z',u,title,context='Historical Statistics of Canada, Section Z')
        rows.extend(c.to_dict('records'))
    out=canonicalize(rows)
    return out,status('CAN_HSC_Z','loaded' if len(out) else 'requires_review',f'Found {len(frames)} structured tables/files; {len(out)} canonical/source-specific observations.',len(out),year_span(out),'network_official')


def ingest_india(network=True):
    base='https://dsal.uchicago.edu/statistics'
    if not network: return canonicalize([]), status('IND_DSAL','refreshable','Network refresh not requested.',0,'','network_disabled')
    rows=[]; got=[]; errors=[]
    for block in ['1894','1903','1910']:
        for no in range(37,43):
            url=f'{base}/{block}_excel/{block}.{no:03d}.XLS'
            dest=RAW/f'india_{block}_{no:03d}.xls'
            try:
                download(url,dest,timeout=60)
                xl=pd.ExcelFile(dest,engine='xlrd')
                for s in xl.sheet_names:
                    raw=pd.read_excel(dest,sheet_name=s,header=None,engine='xlrd')
                    # Try multiple header rows because these Victorian tables are multi-row.
                    best=[]
                    for hdr in range(min(12,len(raw))):
                        d=pd.read_excel(dest,sheet_name=s,header=hdr,engine='xlrd')
                        c=generic_year_table(d,'British India','IND_DSAL',url,f'DSAL {block} table {no}, sheet {s}',context=f'Statistical Abstract table {no}')
                        if len(c)>len(best): best=c.to_dict('records')
                    rows.extend(best)
                got.append(f'{block}.{no:03d}')
            except Exception as e: errors.append(f'{block}.{no:03d}:{type(e).__name__}')
    out=canonicalize(rows)
    msg=f'Loaded {len(got)}/18 XLS tables (37–42 in three blocks). Failures: {", ".join(errors[:6])}'
    return out,status('IND_DSAL','loaded' if len(out) else 'failed',msg,len(out),year_span(out),'network_xls')


def ckan_records(base, resource_id, limit=100000):
    import requests
    records=[]; offset=0
    while True:
        r=requests.get(base.rstrip('/')+'/api/action/datastore_search',params={'resource_id':resource_id,'limit':min(10000,limit-len(records)),'offset':offset},timeout=45,headers={'User-Agent':'ColonialPrisonExplorer/1.0'})
        r.raise_for_status(); payload=r.json(); result=payload['result']; batch=result.get('records',[]); records.extend(batch)
        if not batch or len(records)>=result.get('total',len(records)) or len(records)>=limit: break
        offset+=len(batch)
    return pd.DataFrame(records)


def ingest_st_helena(network=True):
    source_url='https://www.data.qld.gov.au/dataset/st-helena-prisoner-index-1863-to-1936/resource/00927ffb-3ff7-4732-b209-744750541d38'
    if not network: return canonicalize([]), status('QLD_STHELENA','refreshable','Network refresh not requested.',0,'','network_disabled')
    try: df=ckan_records('https://www.data.qld.gov.au','00927ffb-3ff7-4732-b209-744750541d38')
    except Exception as e: return canonicalize([]),status('QLD_STHELENA','failed',str(e),0,'','network_api')
    rows=[]
    sy=next((c for c in df.columns if c.lower().replace('_',' ')=='start year'),None); ey=next((c for c in df.columns if c.lower().replace('_',' ')=='end year'),None)
    if sy:
        starts=pd.to_numeric(df[sy],errors='coerce').dropna().astype(int)
        for y,n in starts.value_counts().sort_index().items():
            if 1863<=y<=1936: rows.append({'jurisdiction':'Queensland – St Helena','year':y,'geography_level':'facility','geography_name':'St Helena Penal Establishment','facility_name':'St Helena Penal Establishment','facility_type':'prison','measure':'indexed_admissions_proxy','measure_class':'proxy','value':int(n),'unit':'person records','source_dataset':'QLD_STHELENA','source_url':source_url,'historical_source_url':source_url,'source_header':sy,'source_table':'St Helena prisoner index','transformation':'count records by Start Year','comparability_grade':'C','quality_flag':'proxy_not_official_admissions','definition_verified':'false','source_record_id':f'start:{y}'})
    if sy and ey:
        pairs=df[[sy,ey]].copy(); pairs[sy]=pd.to_numeric(pairs[sy],errors='coerce'); pairs[ey]=pd.to_numeric(pairs[ey],errors='coerce')
        for y in range(1863,1937):
            n=((pairs[sy]<=y)&(pairs[ey]>=y)).sum()
            if n: rows.append({'jurisdiction':'Queensland – St Helena','year':y,'geography_level':'facility','geography_name':'St Helena Penal Establishment','facility_name':'St Helena Penal Establishment','facility_type':'prison','measure':'active_record_proxy','measure_class':'proxy','value':int(n),'unit':'person records','source_dataset':'QLD_STHELENA','source_url':source_url,'historical_source_url':source_url,'source_header':f'{sy}/{ey}','source_table':'St Helena prisoner index','transformation':'count records where Start Year <= year <= End Year','comparability_grade':'C','quality_flag':'proxy_semantics_require_review','definition_verified':'false','source_record_id':f'active:{y}'})
    out=canonicalize(rows)
    return out,status('QLD_STHELENA','loaded',f'{len(df)} person records staged; annual proxy series derived and explicitly labelled.',len(out),year_span(out),'network_api')


def ingest_tasmania(network=True):
    source_url='https://data.gov.au/data/dataset/d2c27ee7-8be8-425b-a028-b96ef3847fac'
    if not network: return canonicalize([]), status('TAS_PRISONERS','refreshable','Network refresh not requested.',0,'','network_disabled')
    # Resource id verified in portal
    try: df=ckan_records('https://data.gov.au/data','2dc53c91-40a6-4eac-8b12-949bf0278bf2')
    except Exception:
        # DataStore may be incomplete/disabled; try resource download page URL discovered via metadata
        try:
            html=http_get(source_url,timeout=45); soup=BeautifulSoup(html,'html.parser'); candidates=[]
            from urllib.parse import urljoin
            for a in soup.find_all('a',href=True):
                if 'csv' in (a.get_text(' ')+' '+a['href']).lower(): candidates.append(urljoin(source_url,a['href']))
            if not candidates: raise RuntimeError('CSV resource not discovered')
            df=pd.read_csv(io.StringIO(http_get(candidates[0],timeout=60)))
        except Exception as e: return canonicalize([]),status('TAS_PRISONERS','failed',str(e),0,'','network')
    yc=next((c for c in df.columns if c.upper()=='YEAR'),None)
    if not yc: return canonicalize([]),status('TAS_PRISONERS','requires_review',f'{len(df)} records loaded but YEAR field not found.',0,'','network')
    years=pd.to_numeric(df[yc],errors='coerce').dropna().astype(int); rows=[]
    for y,n in years.value_counts().sort_index().items():
        rows.append({'jurisdiction':'Tasmania – Hobart Gaol','year':y,'geography_level':'facility','geography_name':'Hobart Gaol','facility_name':'Hobart Gaol','facility_type':'gaol','measure':'indexed_prisoner_records','measure_class':'proxy','value':int(n),'unit':'indexed records','source_dataset':'TAS_PRISONERS','source_url':source_url,'historical_source_url':source_url,'source_header':yc,'source_table':'Tasmanian Prisoners index','transformation':'count indexed records by YEAR','comparability_grade':'D','quality_flag':'index_records_not_prison_population','definition_verified':'true','source_record_id':f'year:{y}'})
    out=canonicalize(rows)
    return out,status('TAS_PRISONERS','loaded',f'{len(df)} person/index records staged; counts explicitly labelled as indexed records.',len(out),year_span(out),'network')


def ingest_nigeria(network=True):
    landing='https://www.nber.org/data-appendix/w31637'
    if not network: return canonicalize([]), status('NGA_AO','refreshable','Network refresh not requested.',0,'','network_disabled')
    try: html=http_get(landing,timeout=45)
    except Exception as e: return canonicalize([]),status('NGA_AO','failed',str(e),0,'','network')
    soup=BeautifulSoup(html,'html.parser'); from urllib.parse import urljoin
    links=[]
    for a in soup.find_all('a',href=True):
        u=urljoin(landing,a['href']); low=u.lower()
        if any(low.endswith(ext) for ext in ['.csv','.dta','.xlsx','.xls','.zip']): links.append(u)
    rows=[]; inventory=[]
    for j,u in enumerate(dict.fromkeys(links)):
        try:
            dest=RAW/('nigeria_'+str(j)+Path(u.split('?')[0]).suffix)
            download(u,dest,timeout=90)
            files=[]
            if dest.suffix.lower()=='.zip':
                zdir=RAW/f'nigeria_zip_{j}'; zdir.mkdir(exist_ok=True)
                with zipfile.ZipFile(dest) as z: z.extractall(zdir)
                files=[p for p in zdir.rglob('*') if p.suffix.lower() in {'.csv','.dta','.xlsx','.xls'}]
            else: files=[dest]
            for p in files:
                try:
                    if p.suffix.lower()=='.csv': frames={'data':pd.read_csv(p)}
                    elif p.suffix.lower()=='.dta': frames={'data':pd.read_stata(p)}
                    else:
                        xl=pd.ExcelFile(p); frames={s:pd.read_excel(p,sheet_name=s) for s in xl.sheet_names}
                    for s,df in frames.items():
                        inventory.append({'file':p.name,'sheet':s,'rows':len(df),'columns':' | '.join(map(str,df.columns))})
                        c=generic_year_table(df,'British colonial Nigeria','NGA_AO',u,f'{p.name}:{s}',context='Archibong & Obikili replication data')
                        rows.extend(c.to_dict('records'))
                except Exception: pass
        except Exception: pass
    if inventory: pd.DataFrame(inventory).to_csv(RAW/'nigeria_schema_inventory.csv',index=False,encoding='utf-8-sig')
    out=canonicalize(rows)
    state='loaded' if len(out) else 'requires_review'
    msg=f'Discovered {len(links)} structured download links; {len(inventory)} tables inventoried; conservative auto-map emitted {len(out)} observations.' if links else 'NBER landing page reached, but no structured replication download links were discoverable automatically.'
    return out,status('NGA_AO',state,msg,len(out),year_span(out),'network_replication_inventory')


def ingest_all(network=True):
    funcs=[ingest_new_zealand,ingest_canada,ingest_india,ingest_nigeria,ingest_st_helena,ingest_tasmania,ingest_qld_photo,ingest_qld_toowoomba,ingest_qld_brisbane,ingest_ireland,ingest_wa,ingest_guyana]
    dfs=[]; statuses=[]
    for fn in funcs:
        try:
            d,s=fn(network=network); dfs.append(d); statuses.append(s)
        except Exception as e:
            name=fn.__name__.replace('ingest_','').upper(); statuses.append(status(name,'failed',repr(e),0,'','exception'))
    return dfs,statuses

# ---- Additional microdata / source-layer adapters ----
def ckan_package(base, dataset_id):
    import requests
    r=requests.get(base.rstrip('/')+'/api/3/action/package_show',params={'id':dataset_id},timeout=45,headers={'User-Agent':'ColonialPrisonExplorer/1.0'})
    if r.status_code==404:
        r=requests.get(base.rstrip('/')+'/api/action/package_show',params={'id':dataset_id},timeout=45,headers={'User-Agent':'ColonialPrisonExplorer/1.0'})
    r.raise_for_status(); return r.json()['result']

def ckan_first_tabular_resource(base,dataset_id):
    pkg=ckan_package(base,dataset_id)
    rs=pkg.get('resources',[])
    rs=sorted(rs,key=lambda r:(not r.get('datastore_active',False), str(r.get('format','')).upper() not in {'CSV','JSON','XLSX','XLS'}))
    return rs[0] if rs else None

def ingest_ckan_year_index(source_id,jurisdiction,dataset_id,landing,base,measure,year_candidates=('Year','YEAR','Start Year'),grade='D',note='index records, not official prison population'):
    try:
        res=ckan_first_tabular_resource(base,dataset_id)
        if not res: raise RuntimeError('No tabular resource found')
        rid=res.get('id')
        if res.get('datastore_active') and rid:
            df=ckan_records(base,rid)
        else:
            u=res.get('url'); content=http_get(u,timeout=90)
            if str(res.get('format','')).upper()=='CSV': df=pd.read_csv(io.StringIO(content))
            else: raise RuntimeError('Non-DataStore resource is not CSV')
        yc=next((c for c in df.columns if norm_text(c).lower() in {x.lower() for x in year_candidates}),None)
        if not yc:
            # inspect date-like field
            yc=next((c for c in df.columns if 'year' in norm_text(c).lower()),None)
        if not yc: raise RuntimeError('No year field detected: '+', '.join(map(str,df.columns[:30])))
        yrs=pd.to_numeric(df[yc],errors='coerce').dropna().astype(int)
        rows=[]
        for y,cnt in yrs.value_counts().sort_index().items():
            rows.append({'jurisdiction':jurisdiction,'year':int(y),'geography_level':'facility','geography_name':jurisdiction,'facility_name':jurisdiction,'facility_type':'historical_prison_index','measure':measure,'measure_class':'proxy','value':int(cnt),'unit':'indexed records','source_dataset':source_id,'source_url':landing,'historical_source_url':landing,'source_header':yc,'source_table':res.get('name') or pkg.get('title'),'transformation':f'count structured records by {yc}','comparability_grade':grade,'quality_flag':'index_records_not_official_population','definition_verified':'true','source_record_id':f'{yc}:{y}','notes':note})
        out=canonicalize(rows); return out,status(source_id,'loaded',f'{len(df)} records staged from CKAN resource {rid}; annual counts are labelled proxy/index measures.',len(out),year_span(out),'network_ckan')
    except Exception as e:
        return canonicalize([]),status(source_id,'failed',str(e),0,'','network_ckan')

def ingest_qld_photo(network=True):
    if not network:return canonicalize([]),status('QLD_PHOTO','refreshable','Network refresh not requested.',0,'','network_disabled')
    return ingest_ckan_year_index('QLD_PHOTO','Queensland – Prisoner photographic index','photographic-records-of-prisoners-1875-1936','https://www.data.qld.gov.au/dataset/photographic-records-of-prisoners-1875-1936','https://www.data.qld.gov.au','indexed_prisoner_photo_records',('Year','YEAR'),grade='D')

def ingest_qld_toowoomba(network=True):
    if not network:return canonicalize([]),status('QLD_TOOWOOMBA','refreshable','Network refresh not requested.',0,'','network_disabled')
    return ingest_ckan_year_index('QLD_TOOWOOMBA','Queensland – Toowoomba Prison','indextoprisonerstriedtoowoomba1864-1903-csv','https://www.data.qld.gov.au/dataset/indextoprisonerstriedtoowoomba1864-1903-csv','https://www.data.qld.gov.au','indexed_admission_records',('Year','YEAR','Date'),grade='D')

def ingest_qld_brisbane(network=True):
    if not network:return canonicalize([]),status('QLD_BRISBANE','refreshable','Network refresh not requested.',0,'','network_disabled')
    return ingest_ckan_year_index('QLD_BRISBANE','Queensland – Brisbane Gaol','register-of-prisoners-gaol-brisbane-1850-1901','https://www.data.qld.gov.au/dataset/register-of-prisoners-gaol-brisbane-1850-1901','https://www.data.qld.gov.au','indexed_prisoner_records',('Year','YEAR','Date'),grade='D')

def ingest_wa(network=True):
    landing='https://research-repository.uwa.edu.au/en/datasets/wa-blue-books/'
    if not network:return canonicalize([]),status('WA_BLUEBOOKS','refreshable','Network refresh not requested.',0,'','network_disabled')
    try:
        html=http_get(landing,timeout=45); soup=BeautifulSoup(html,'html.parser'); from urllib.parse import urljoin
        links=[]
        for a in soup.find_all('a',href=True):
            u=urljoin(landing,a['href']); text=(u+' '+a.get_text(' ')).lower()
            if '.xls' in text or '.xlsx' in text: links.append(u)
        rows=[]
        for i,u in enumerate(dict.fromkeys(links)):
            ext='.xlsx' if '.xlsx' in u.lower() else '.xls'; dest=RAW/f'wa_bluebooks_{i}{ext}';download(u,dest)
            xl=pd.ExcelFile(dest)
            for s in xl.sheet_names:
                if 'convict' not in s.lower(): continue
                df=pd.read_excel(dest,sheet_name=s)
                c=generic_year_table(df,'Western Australia','WA_BLUEBOOKS',u,f'WA Blue Books: {s}',context='Convicts sheet; UWA notes coverage is partial')
                rows.extend(c.to_dict('records'))
        out=canonicalize(rows); st='loaded' if len(out) else 'requires_review'
        return out,status('WA_BLUEBOOKS',st,f'Discovered {len(links)} workbook links; emitted only sheets explicitly containing “convict”.',len(out),year_span(out),'network_repository')
    except Exception as e:return canonicalize([]),status('WA_BLUEBOOKS','failed',str(e),0,'','network_repository')

def ingest_reshare(source_id,jurisdiction,landing,network=True):
    if not network:return canonicalize([]),status(source_id,'refreshable','Network refresh not requested.',0,'','network_disabled')
    try:
        html=http_get(landing,timeout=45);soup=BeautifulSoup(html,'html.parser');from urllib.parse import urljoin
        links=[]
        for a in soup.find_all('a',href=True):
            u=urljoin(landing,a['href']);
            if any(u.lower().split('?')[0].endswith(x) for x in ['.csv','.dta','.xlsx','.xls','.zip']):links.append(u)
        rows=[]; inventory=[]
        for i,u in enumerate(dict.fromkeys(links)):
            dest=RAW/f'{source_id.lower()}_{i}{Path(u.split("?")[0]).suffix}';download(u,dest,timeout=90)
            fs=[]
            if dest.suffix.lower()=='.zip':
                zdir=RAW/f'{source_id.lower()}_zip_{i}';zdir.mkdir(exist_ok=True)
                with zipfile.ZipFile(dest) as z:z.extractall(zdir)
                fs=[p for p in zdir.rglob('*') if p.suffix.lower() in {'.csv','.dta','.xlsx','.xls'}]
            else:fs=[dest]
            for p in fs:
                try:
                    if p.suffix.lower()=='.csv':frames={'data':pd.read_csv(p)}
                    elif p.suffix.lower()=='.dta':frames={'data':pd.read_stata(p)}
                    else:
                        xl=pd.ExcelFile(p);frames={s:pd.read_excel(p,sheet_name=s) for s in xl.sheet_names}
                    for sn,df in frames.items():
                        inventory.append({'file':p.name,'sheet':sn,'rows':len(df),'columns':' | '.join(map(str,df.columns))})
                        c=generic_year_table(df,jurisdiction,source_id,u,f'{p.name}:{sn}',context='ReShare structured file; auto-map only unambiguous year series')
                        rows.extend(c.to_dict('records'))
                except Exception:pass
        if inventory:pd.DataFrame(inventory).to_csv(RAW/f'{source_id.lower()}_schema_inventory.csv',index=False,encoding='utf-8-sig')
        out=canonicalize(rows); st='loaded' if len(out) else 'requires_review'
        return out,status(source_id,st,f'Discovered {len(links)} structured files; inventoried {len(inventory)} tables; emitted {len(out)} year-series observations.',len(out),year_span(out),'network_repository_inventory')
    except Exception as e:return canonicalize([]),status(source_id,'failed',str(e),0,'','network_repository')

def ingest_ireland(network=True):return ingest_reshare('IRL_REGISTERS','Ireland – Kilmainham/Clonmel','https://reshare.ukdataservice.ac.uk/857702/',network)
def ingest_guyana(network=True):return ingest_reshare('GUY_MNS','British Guiana / Guyana','https://reshare.ukdataservice.ac.uk/856077/',network)
