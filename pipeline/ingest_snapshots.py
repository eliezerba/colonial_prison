import pandas as pd
from common import SNAPSHOTS, canonicalize, status, year_span


def _canonical_snapshot(filename, source_id, jurisdiction, message, default_level='system'):
    p=SNAPSHOTS/filename
    df=pd.read_csv(p,dtype=str).fillna('')
    if 'jurisdiction' not in df or not df['jurisdiction'].astype(str).str.strip().any(): df['jurisdiction']=jurisdiction
    # Snapshot filename/version labels are provenance details; source_dataset must match the registry ID.
    df['source_dataset']=source_id
    if 'measure_class' not in df: df['measure_class']=''
    if 'geography_level' not in df: df['geography_level']=default_level
    if 'geography_name' not in df: df['geography_name']=jurisdiction
    if 'historical_source_url' not in df: df['historical_source_url']=df.get('source_url','')
    if 'source_record_id' not in df: df['source_record_id']=[f'{filename}:{i+2}' for i in range(len(df))]
    if 'transformation' not in df: df['transformation']='verified_snapshot_transcription'
    if 'definition_verified' not in df: df['definition_verified']='true'
    if 'quality_flag' not in df: df['quality_flag']='verified_snapshot'
    if 'notes' not in df: df['notes']=message
    out=canonicalize(df.to_dict('records'))
    return out,status(source_id,'loaded',message,len(out),year_span(out),'verified_snapshot')


def ingest_nz_snapshot():
    return _canonical_snapshot('nz_verified_snapshot.csv','NZ_OYB','New Zealand','Verified bundled Official Yearbook snapshot; network refresh can extend coverage.')

def ingest_canada_snapshot():
    return _canonical_snapshot('canada_verified_snapshot.csv','CAN_HSC_Z','Canada','Verified bundled transcription of Statistics Canada Historical Statistics Section Z tables Z173–226.')

def ingest_hong_kong_snapshot():
    return _canonical_snapshot('hong_kong_verified_snapshot.csv','HKG_ADMIN','Hong Kong','Verified values transcribed from digitised Hong Kong Administrative Reports / Yearbooks; each observation retains its report URL.')

def ingest_nz_ajhr_snapshot():
    return _canonical_snapshot('nz_ajhr_verified_snapshot.csv','NZ_AJHR_PRISONS','New Zealand','Verified retrospective statistics from the official New Zealand Prisons Department report for 1929, digitised by Papers Past.')

def ingest_microdata_source_snapshots():
    p=SNAPSHOTS/'microdata_source_snapshot.csv'; df=pd.read_csv(p,dtype=str).fillna('')
    outs=[]; sts=[]
    for sid,g in df.groupby('source_dataset'):
        out=canonicalize(g.to_dict('records')); outs.append(out)
        msg='Bundled source-layer record-count observation. Explicitly proxy/non-population; network refresh can load person-level records.'
        sts.append(status(sid,'loaded',msg,len(out),year_span(out),'verified_source_metadata_snapshot'))
    return outs,sts


def ingest_additional_verified_snapshots():
    p=SNAPSHOTS/'additional_verified_snapshots.csv'
    df=pd.read_csv(p,dtype=str).fillna('')
    outs=[]; sts=[]
    for sid,g in df.groupby('source_dataset'):
        out=canonicalize(g.to_dict('records')); outs.append(out)
        msg='Bundled verified transcription from a structured published table; each observation retains the source URL and table label.'
        sts.append(status(sid,'loaded',msg,len(out),year_span(out),'verified_web_table_snapshot'))
    return outs,sts
