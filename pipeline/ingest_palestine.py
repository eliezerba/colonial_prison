from pathlib import Path
import csv, re
import pandas as pd
from openpyxl import load_workbook
from common import CONFIG, SNAPSHOTS, canonicalize, norm_text, parse_year, status, year_span

SHEET_URL='https://docs.google.com/spreadsheets/d/10vGVgHP7JdODpGXGYcmaavthDNfoTCJo6hMO_u5CSTE/edit?usp=sharing'
EXPORT_URL='https://docs.google.com/spreadsheets/d/10vGVgHP7JdODpGXGYcmaavthDNfoTCJo6hMO_u5CSTE/export?format=xlsx'

def maybe_download_live(dest: Path):
    from common import download
    try:
        download(EXPORT_URL,dest,timeout=45)
        if dest.stat().st_size < 10000: raise RuntimeError('download too small')
        return dest, 'live_google_sheet_export'
    except Exception:
        snap=SNAPSHOTS/'palestine_snapshot.xlsx'
        return snap, 'bundled_snapshot_fallback'


def enrich_raw_text(df):
    """Parse clearly structured values retained as raw text, without discarding the original observation."""
    if df is None or df.empty: return df
    extra=[]
    def derive(base, measure, value, unit='persons', notes='', measure_class=None, legal_status='', facility_name=None, facility_type=None, geography_level=None, geography_name=None):
        if value is None: return
        r=base.to_dict()
        r['observation_id']=''
        r['measure']=measure; r['value']=float(value); r['unit']=unit
        if measure_class is not None: r['measure_class']=measure_class
        if legal_status: r['legal_status']=legal_status
        if facility_name is not None: r['facility_name']=facility_name
        if facility_type is not None: r['facility_type']=facility_type
        if geography_level is not None: r['geography_level']=geography_level
        if geography_name is not None: r['geography_name']=geography_name
        r['raw_value_text']=base.get('raw_value_text','')
        r['transformation']='parsed_from_raw_source_text'
        r['comparability_grade']='B'
        r['quality_flag']='parsed_from_source_text'
        r['definition_verified']='true'
        r['source_record_id']=str(base.get('source_record_id',''))+':'+measure
        r['notes']=(str(base.get('notes',''))+' | '+notes).strip(' |')
        extra.append(r)

    # Recidivism: manually audited parsing of the structured strings in the source workbook.
    rec={
      1930:(736,399,125,212,5.61),1931:(717,381,123,213,5.32),1932:(817,435,141,241,4.27),
      1934:(1594,872,308,419,10.7),1935:(1404,774,292,429,13.1),1936:(1184,590,254,340,11.2),
      1937:(1778,884,349,545,15.1),1939:(887,372,186,329,13.3),1940:(1837,None,None,None,15.1),
      1941:(2056,972,366,718,18.3),1942:(2142,995,395,752,22.34),1943:(2177,911,415,851,26.79),
      1944:(2655,1112,490,1053,30.75)}
    for _,b in df[(df['source_dataset']=='PAL_V2') & (df['measure']=='recidivists')].iterrows():
        y=int(b['year']) if pd.notna(b['year']) else None
        if y in rec:
            total,once,twice,three,rate=rec[y]
            derive(b,'recidivists_total',total,'persons','Total recidivists parsed from source text.','flow')
            if once is not None: derive(b,'recidivists_once',once,'persons','One previous conviction.','flow')
            if twice is not None: derive(b,'recidivists_twice',twice,'persons','Two previous convictions.','flow')
            if three is not None: derive(b,'recidivists_three_plus',three,'persons','Three or more previous convictions.','flow')
            derive(b,'recidivism_rate_pct',rate,'percent','Percentage as printed in source text; denominator wording varies in the workbook and is retained in raw text.','rate')

    # Escape counts. Reformatory escapes are kept out when the prison total is separately stated; 1940 includes Defence-Regulation detainees; 1944 sums listed escape categories.
    escape_counts={1921:16,1922:4,1924:17,1926:6,1927:12,1928:22,1929:17,1930:22,1931:22,1932:15,1933:13,1934:12,1935:30,1936:53,1937:54,1938:61,1939:71,1940:37,1941:22,1942:21,1943:23,1944:50}
    for _,b in df[(df['source_dataset']=='PAL_V2') & (df['measure']=='escapes')].iterrows():
        y=int(b['year']) if pd.notna(b['year']) else None
        if y in escape_counts: derive(b,'escapes_reported_count',escape_counts[y],'persons','Reported prison/detention escape count parsed from workbook narrative.','event')

    # Extradition directions.
    for _,b in df[(df['source_dataset']=='PAL_V2') & (df['measure']=='extraditions')].iterrows():
        t=str(b.get('raw_value_text',''))
        mf=re.search(r'(\d+)\s+from\s+palestine',t,re.I); mt=re.search(r'(\d+)\s+to\s+palestine',t,re.I)
        if mf: derive(b,'extraditions_from_palestine',int(mf.group(1)),'persons','Parsed directional extradition count.','event')
        if mt: derive(b,'extraditions_to_palestine',int(mt.group(1)),'persons','Parsed directional extradition count.','event')

    # Visitor visits where a total is recoverable from the narrative.
    visitor_visits={1941:78,1943:74,1944:133}
    for _,b in df[(df['source_dataset']=='PAL_V2') & (df['measure']=='prison_visitors')].iterrows():
        y=int(b['year']) if pd.notna(b['year']) else None
        if y in visitor_visits: derive(b,'prison_visitor_visits',visitor_visits[y],'visits','Total visits parsed from narrative; 1943 sums listed facilities.','flow')

    # Special detention / camp facts explicitly stated in narrative cells.
    for _,b in df[(df['source_dataset']=='PAL_V2') & (df['measure'].isin(['detention_camp_population_raw','farm_labour_camp_population_raw']))].iterrows():
        y=int(b['year']) if pd.notna(b['year']) else None; f=str(b.get('facility_name','')); t=str(b.get('raw_value_text',''))
        key=(f,y)
        facts={
          ('Acre Detention Camp',1938): [('detention_stock_eoy',871,'persons')],
          ('Athlit Detention Camp',1938): [('detention_stock_eoy',295,'persons')],
          ('Sarafand Detention Camp',1938): [('detention_stock_eoy',426,'persons')],
          ('Athlit Detention Camp',1940): [('detention_avg_daily',1299,'persons')],
          ('Athlit Detention Camp',1941): [('detention_stock_eoy',857,'persons'),('detention_admissions',1560,'admissions')],
          ('Athlit Detention Camp',1942): [('detention_admissions',607,'admissions'),('detention_avg_daily',368,'persons')],
          ('Athlit Detention Camp',1943): [('detention_stock_eoy',3410,'persons'),('illegal_immigrant_detention',3334,'persons')],
          ('Athlit Detention Camp',1944): [('detention_stock_eoy',203,'persons'),('illegal_immigrant_detention',203,'persons')],
          ('Acre Farm Labour Camp',1937): [('detention_stock_eoy',457,'persons')],
          ('Acre Farm Labour Camp',1941): [('detention_avg_daily',987,'persons')],
          ('Acre Farm Labour Camp',1942): [('detention_stock_eoy',372,'persons'),('detention_admissions',174,'admissions'),('detention_avg_daily',474,'persons')],
        }
        for measure,value,unit in facts.get(key,[]): derive(b,measure,value,unit,'Explicit numeric fact parsed from camp narrative.', 'stock' if 'stock' in measure else ('average' if 'avg' in measure else 'flow'))

    # Facility year-end stocks 1930–1938 that are written as status components rather than a single numeric cell.
    stock_fac=df[(df['source_dataset']=='PAL_V2') & (df['measure']=='stock_eoy_total') & (df['geography_level']=='facility')]
    for _,b in stock_fac.iterrows():
        y=int(b['year']) if pd.notna(b['year']) else None; t=str(b.get('raw_value_text','')).strip()
        if not t or y is None or not (1930 <= y <= 1938): continue
        if not re.search(r'convict|awaiting|unconvicted|defence',t,re.I): continue
        nums=[int(x) for x in re.findall(r'\d+',t)]
        if not nums: continue
        total=None
        m=re.match(r'^\s*(\d+)\s*\((.*)\)\s*$',t)
        if m:
            first=int(m.group(1)); inside=[int(x) for x in re.findall(r'\d+',m.group(2))]
            total=first if inside and sum(inside)==first else first+sum(inside)
        else:
            total=sum(nums)
        derive(b,'stock_eoy_total',total,'persons','Facility total reconstructed by summing explicitly printed legal-status components in the original cell.','stock',geography_level='facility',geography_name='Palestine')

    # Prison labour: values printed in narrative cells but not entered as simple numerics in the workbook.
    labour_counts={1939:3037,1940:7272,1942:3397,1943:1634,1944:1111}
    for _,b in df[(df['source_dataset']=='PAL_V2') & (df['measure']=='prison_labour_count')].iterrows():
        y=int(b['year']) if pd.notna(b['year']) else None
        if (pd.isna(b.get('value')) or b.get('value') in ('',None)) and y in labour_counts:
            derive(b,'prison_labour_count',labour_counts[y],'persons','Numeric penal-labour count audited and parsed from the original narrative cell.','flow',geography_level='system',geography_name='Palestine',facility_name='',facility_type='')

    labour_values={1940:19471,1941:19315.309,1942:27768.851,1944:36560}
    for _,b in df[(df['source_dataset']=='PAL_V2') & (df['measure']=='prison_labour_value')].iterrows():
        y=int(b['year']) if pd.notna(b['year']) else None
        if (pd.isna(b.get('value')) or b.get('value') in ('',None)) and y in labour_values:
            derive(b,'prison_labour_value',labour_values[y],'LP','Total value printed in the original narrative cell; component detail remains in raw_value_text.','financial',geography_level='system',geography_name='Palestine',facility_name='',facility_type='')

    # Average daily employed prisoners. 1939-40 are sums of the two explicitly numeric aggregate rows; 1941-44 are totals stated in narrative cells.
    employed_totals={1939:883,1940:1182,1941:1153,1942:1316,1943:1350,1944:1466}
    employed_base=df[(df['source_dataset']=='PAL_V2') & (df['measure']=='employed_avg_daily')]
    for y,total in employed_totals.items():
        yy=employed_base[employed_base['year'].astype(str).str.extract(r'(\d{4})',expand=False).eq(str(y))]
        if len(yy):
            b=yy.iloc[0]
            derive(b,'employed_avg_daily_total',total,'persons','System total audited from the original employed-prisoners cells; 1939-40 sum central-prison and Jail Labour Company aggregates, 1941-44 parse the stated total.','average',geography_level='system',geography_name='Palestine',facility_name='',facility_type='')
    # Audited corrections/additions from the live V2 sheet PDF export (14 Aug 2026).
    # These do not overwrite source rows: they add explicit, higher-quality derived observations with provenance notes.
    def base_for(year, measure):
        z=df[(df['source_dataset']=='PAL_V2') & (df['year'].astype(str).str.extract(r'(\d{4})',expand=False).eq(str(year))) & (df['measure']==measure)]
        z=z[z['geography_level']=='system']
        return z.iloc[0] if len(z) else None

    # Population denominators visible in the current V2 chart/source tab but missing from the bundled XLSX cached values.
    for y,v in {1930:843132,1946:1912112}.items():
        b=base_for(y,'stock_eoy_total')
        if b is None: b=base_for(y,'admissions_total')
        if b is not None:
            derive(b,'population_denominator',v,'persons','Audited from the current V2 Google Sheet PDF export; cached XLSX formula value was missing.','denominator',geography_level='system',geography_name='Palestine',facility_name='',facility_type='')
            extra[-1]['comparability_grade']='A'; extra[-1]['quality_flag']='audited_live_v2_pdf'; extra[-1]['transformation']='audited_from_live_v2_pdf_export'

    # Two clean admissions values conflict with the narrative/source totals and fail exact component reconciliation.
    # Keep the original rows for audit, add corrected preferred observations rather than silently changing them.
    for y,v,note in [
        (1932,19161,'Live V2/raw annual-report text states 19,161 convicted admissions; clean cell contains 10,161.')]:
        b=base_for(y,'admissions_convicted')
        if b is not None:
            derive(b,'admissions_convicted',v,'admissions',note,'flow',legal_status='convicted',geography_level='system',geography_name='Palestine',facility_name='',facility_type='')
            extra[-1]['comparability_grade']='A'; extra[-1]['quality_flag']='audited_conflict_corrected_keep_original'; extra[-1]['transformation']='audited_correction_from_live_v2_and_raw_source_text'

    if extra:
        df=canonicalize(pd.concat([df,canonicalize(extra)],ignore_index=True).to_dict('records'))

    # Prefer audited live-V2 values when the bundled XLSX snapshot is stale or shifted.
    # Original snapshot observations remain, but are downgraded so every discrepancy is inspectable.
    stale=((df['source_dataset']=='PAL_V2') & (((pd.to_numeric(df['year'],errors='coerce')==1932) & (df['measure']=='admissions_convicted') & (pd.to_numeric(df['value'],errors='coerce')==10161)) | ((pd.to_numeric(df['year'],errors='coerce').isin([1946,1947])) & (df['measure'].isin(['stock_eoy_convicted','stock_eoy_nonconvicted','stock_eoy_total'])))))
    df.loc[stale,'comparability_grade']='D'
    df.loc[stale,'quality_flag']=df.loc[stale,'quality_flag'].fillna('').astype(str).apply(lambda x:(x+'|conflicts_live_v2_pdf').strip('|'))
    df.loc[stale,'definition_verified']='false'

    live_rows=[]
    template=df[(df['source_dataset']=='PAL_V2') & (df['geography_level']=='system')].iloc[0].to_dict()
    late={1945:(1840,875,2715),1946:(1775,2186,3961),1947:(1918,2043,3979),1948:(1709,1284,2999)}
    for y,(conv,non,total) in late.items():
        for measure,value,legal in [('stock_eoy_convicted',conv,'convicted'),('stock_eoy_nonconvicted',non,'nonconvicted'),('stock_eoy_total',total,'')]:
            r=template.copy(); r.update({'observation_id':'','year':y,'reporting_period':str(y),'year_start':y,'year_end':y,'reference_date':f'{y}-12-31','geography_level':'system','geography_name':'Palestine','facility_id':'','facility_name':'','facility_type':'','measure':measure,'measure_class':'stock','legal_status':legal,'value':float(value),'unit':'persons','denominator':'','source_dataset':'PAL_V2','source_sheet':'live V2 PDF export','source_column':'AK/AM/AN','source_header':'Total convicts / non-convicts / prisoners, 31 Dec.','source_table':'V2 summary table, years 1922-1948','source_url':SHEET_URL,'historical_source_url':'','raw_value_text':'','transformation':'audited_from_live_v2_pdf_export','comparability_grade':'A','quality_flag':'audited_live_v2_pdf_supersedes_stale_snapshot','definition_verified':'true','source_record_id':f'PAL_LIVE_V2:{y}:{measure}','notes':'Audited against current V2 Google Sheet PDF export; original bundled snapshot row retained where present.'})
            live_rows.append(r)
    if live_rows:
        df=canonicalize(pd.concat([df,canonicalize(live_rows)],ignore_index=True).to_dict('records'))

    # Compute rate series only from explicit numerator + population denominator observations.
    # This intentionally does NOT use the V2 chart columns mislabeled “prisoners per 1,000”, whose printed values use admissions as numerator.
    rate_rows=[]
    for y in sorted(set(pd.to_numeric(df['year'],errors='coerce').dropna().astype(int))):
        sy=df[(df['jurisdiction']=='Mandatory Palestine') & (df['geography_level']=='system') & (pd.to_numeric(df['year'],errors='coerce')==y)]
        den=sy[(sy['measure']=='population_denominator') & pd.to_numeric(sy['value'],errors='coerce').notna()]
        if den.empty: continue
        d=den.sort_values('comparability_grade',key=lambda x:x.map({'A':0,'B':1,'C':2,'U':3,'D':4}).fillna(9)).iloc[0]
        dv=float(d['value'])
        if not dv: continue
        for measure,out_measure,label in [
            ('stock_eoy_total','stock_eoy_rate_per_100000','Year-end prison stock'),
            ('admissions_total','admissions_rate_per_100000','Admissions'),
            ('admissions_convicted','admissions_convicted_rate_per_100000','Convicted admissions'),
            ('avg_daily_total','avg_daily_rate_per_100000','Daily average')]:
            num=sy[(sy['measure']==measure) & pd.to_numeric(sy['value'],errors='coerce').notna()]
            if num.empty: continue
            num=num.sort_values('comparability_grade',key=lambda x:x.map({'A':0,'B':1,'C':2,'U':3,'D':4}).fillna(9)).iloc[0]
            r=num.to_dict(); r['observation_id']=''; r['measure']=out_measure; r['measure_class']='rate'; r['value']=float(num['value'])/dv*100000; r['unit']='per_100000'; r['denominator']='population_denominator'; r['raw_value_text']=''; r['transformation']=f'{measure} / population_denominator * 100000'; r['comparability_grade']='B'; r['quality_flag']='derived_from_explicit_numerator_and_denominator'; r['definition_verified']='true'; r['source_record_id']=f'PALRATE:{y}:{out_measure}'; r['notes']=f'{label} rate calculated by dashboard from explicit V2 numerator and population denominator; not copied from mislabeled chart-rate columns.'
            rate_rows.append(r)
    if rate_rows:
        df=canonicalize(pd.concat([df,canonicalize(rate_rows)],ignore_index=True).to_dict('records'))

    # The live workbook contains two equivalent system-wide daily-average fields in 1941.
    # Preserve both for provenance, but keep only one as the preferred Grade-A observation.
    alias=((df['source_dataset']=='PAL_V2') & (pd.to_numeric(df['year'],errors='coerce')==1941) &
           (df['geography_level']=='system') & (df['measure']=='avg_daily_total') &
           (df['source_header'].astype(str).str.strip().str.lower()=='daily average in prisons'))
    df.loc[alias,'comparability_grade']='B'
    df.loc[alias,'quality_flag']=df.loc[alias,'quality_flag'].fillna('').astype(str).apply(lambda x:(x+'|duplicate_equivalent_source_field').strip('|'))
    df.loc[alias,'notes']=df.loc[alias,'notes'].fillna('').astype(str)+' | Same 1941 value is also reported in the preferred system average field; retained as secondary provenance.'
    return df


def ingest(network=False):
    workbook, mode = maybe_download_live(SNAPSHOTS/'palestine_live.xlsx') if network else (SNAPSHOTS/'palestine_snapshot.xlsx','bundled_snapshot')
    wb=load_workbook(workbook,data_only=True,read_only=False)
    dd=pd.read_csv(CONFIG/'palestine_data_dictionary.csv',dtype=str).fillna('')
    rows=[]
    for _,d in dd.iterrows():
        if d.get('pipeline_action')=='retain_for_provenance_only': continue
        sheet=d['sheet']
        if sheet not in wb.sheetnames: continue
        ws=wb[sheet]; col=int(float(d['column_index'])); start=3 if sheet=='prison date' else 2
        for r in range(start,ws.max_row+1):
            period,ys,ye,y=parse_year(ws.cell(r,1).value)
            if y is None: continue
            raw=ws.cell(r,col).value
            if raw is None or raw=='': continue
            numeric=isinstance(raw,(int,float)) and not isinstance(raw,bool)
            q=[]
            if not numeric: q.append('manual_parse_required')
            if d.get('qa_status') not in ('','ready'): q.append(d.get('qa_status'))
            row={
                'jurisdiction':'Mandatory Palestine','year':y,'reporting_period':period,'year_start':ys,'year_end':ye,
                'reference_date':f'{y}-12-31' if d.get('measure_class')=='stock' and ys==ye else '',
                'geography_level':d.get('geography_level'),'geography_name':'Palestine','facility_id':d.get('facility_id'),
                'facility_name':d.get('facility_name'),'facility_type':d.get('facility_type'),'measure':d.get('measure'),
                'measure_class':d.get('measure_class'),'legal_status':d.get('legal_status'),'sex':d.get('sex'),
                'age_group':d.get('age_group'),'sentence_band':d.get('sentence_band'),'labour_status':d.get('labour_status'),
                'value':float(raw) if numeric else None,'unit':d.get('unit'),'denominator':'','source_dataset':'PAL_V2',
                'source_sheet':sheet,'source_column':d.get('column_letter'),'source_header':d.get('original_header'),'source_table':'',
                'source_url':SHEET_URL,'historical_source_url':'','raw_value_text':'' if numeric else str(raw),
                'transformation':'direct_numeric' if numeric else 'raw_text_preserved','comparability_grade':('A' if numeric and d.get('qa_status') in ('','ready') else 'U'),
                'quality_flag':'|'.join(dict.fromkeys(x for x in q if x)),'definition_verified':('true' if numeric and d.get('qa_status') in ('','ready') else 'false'),
                'source_record_id':f'{sheet}!{d.get("column_letter")}{r}','notes':f'Ingest mode: {mode}'
            }
            rows.append(row)
    df=enrich_raw_text(canonicalize(rows))
    st=status('PAL_V2','loaded',f'{mode}; workbook={workbook.name}',len(df),year_span(df),mode)
    return df,st
