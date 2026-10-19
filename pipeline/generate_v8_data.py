#!/usr/bin/env python3
"""Version 8: curated, source-traceable transcriptions checked against published tables.

Run only deliberately when changing source transcriptions. The ordinary build consumes
pipeline/snapshots/v8_verified_snapshots.csv and never contacts the network.
"""
from pathlib import Path
import pandas as pd
from common import SNAPSHOTS

# Every number below is directly transcribed from the tables/paragraphs linked below.
EW = '''1920 9573 1427 11000
1921 10791 1388 12179
1922 10557 1209 11766
1923 10117 1031 11148
1924 9808 942 10750
1925 9635 874 10509
1926 9972 888 10860
1927 10300 879 11179
1928 10305 804 11109
1929 10094 767 10861
1930 10561 785 11346
1931 10884 792 11676
1932 11992 811 12803
1933 12180 806 12986
1934 11493 745 12238
1935 10587 719 11306
1936 9939 674 10613
1937 9894 668 10562
1938 10388 698 11086
1939 9662 664 10326
1940 8443 934 9377
1941 9667 968 10635
1942 11223 1177 12400
1943 11430 1360 12790
1944 11438 1477 12915
1945 13180 1528 14708
1946 14556 1233 15789
1947 15986 1081 17067
1948 18621 1144 19765
1949 18783 1096 19879
1950 19367 1107 20474'''
# Commons Library archived Table 10a (daily average Scotland, year series).
SCOT = '''1920 1874
1921 2115
1922 2028
1923 2028
1924 1891
1925 1688
1926 1781
1927 1735
1928 1715
1929 1670
1930 1661
1931 1636
1932 1677
1933 1856
1934 1851
1935 1694
1936 1636
1937 1593
1938 1543
1939 1350
1940 1320
1941 1337
1942 1559
1943 1560
1944 1606
1945 1955
1946 1983
1947 1889
1948 1902
1949 1835
1950 1781'''
# New Zealand Report 1938-39, retrospective table for 1932–1938.
# year, total receptions WITHOUT transfers, distinct persons, ratio per 10k, daily average.
NZ = '''1932 5198 3401 22.29 1669
1933 4157 2731 17.75 1543
1934 3816 2376 15.33 1360
1935 3409 2158 13.76 1212
1936 2980 1790 11.36 1005
1937 3213 1991 12.52 860
1938 3536 2224 13.84 870'''
# Northern Ireland Annual Abstract of Statistics 1937–47, TABLE 72.
# year, receptions all, male, female, daily average all, convicted, unconvicted.
NI = '''1937 2355 1904 451 357 334 23
1938 2482 1953 529 376 353 23
1939 2183 1743 440 373 352 21
1940 2115 1699 416 363 332 31
1941 1991 1676 315 445 417 28
1942 2243 1828 415 550 521 29
1943 1836 1378 458 499 463 36
1944 1977 1517 460 516 495 21
1945 1866 1502 364 490 464 26
1946 1422 1153 269 456 427 29
1947 1541 1274 267 413 382 31'''
# Northern Ireland TABLE 73: convicted prisoners total, males, females;
# male percentage with known previous proven offences. Distinct from a follow-up recidivism rate.
NI_PRIOR = '''1937 2005 1586 419 74
1938 2083 1588 495 66
1939 1841 1428 413 81
1940 1818 1426 392 83
1941 1448 1177 271 57
1942 1560 1196 364 57
1943 1329 921 408 69
1944 1464 1032 432 60
1945 1261 933 328 60
1946 1053 806 247 61
1947 1097 864 233 62'''

URL_EW='https://researchbriefings.files.parliament.uk/documents/CBP-8161/CBP-8161.pdf'
URL_SC='https://www.breizh-info.com/wp-content/uploads/2017/11/SN04334.pdf'
URL_NZ='https://paperspast.natlib.govt.nz/parliamentary/AJHR1939-I.2.3.2.23'
URL_NI='https://escoe-website.s3.amazonaws.com/wp-content/uploads/2022/12/11173048/Annual-Abstract-of-Statistics-1937-1947.pdf'
URL_HK='https://www.histsyn.com/2023/02/CAR1931-1939.html'
URL_HK46='https://www.histsyn.com/2023/01/EYB1946.html'
URL_BAS='https://libsysdigi.library.illinois.edu/ilharvest/Africana/Books2011-05/469256/469256_1937/469256_1937_opt.pdf'
URL_UGA='https://prisonstudies.org/country/uganda?language_content_entity=en-gb'
rows=[]

def add(sid,jur,year,measure,value,source,table,heading,*,unit='persons',grade='B',timebasis='',flags='',note='',sex='',legal='all_or_unspecified',trans='manual_transcription_checked_against_published_table'):
    assert source.startswith('https://'),source
    rows.append(dict(source_dataset=sid,jurisdiction=jur,year=year,reporting_period=str(year),reference_date=timebasis or str(year),geography_level='system',geography_name=jur,facility_name='',facility_type='',measure=measure,measure_class='rate' if unit.startswith('per_') else 'count',legal_status=legal,sex=sex,value=value,unit=unit,source_table=table,source_header=heading,source_url=source,historical_source_url=source,transformation=trans,comparability_grade=grade,quality_flag='v8_curated|'+flags,definition_verified='True' if grade in {'A','B'} else 'False',source_record_id=f'{sid}:{table}:{year}:{measure}:{sex}:{legal}',notes=note))

# England & Wales: month-end average is NOT an average of 365 daily counts.
for year,male,female,total in [(1900,14459,2976,17435),(1910,18323,2581,20904)]+[tuple(map(int,x.split())) for x in EW.splitlines()]:
    assert male+female == total,(year,male,female,total)
    for meas,val,sex in [('avg_month_end_male',male,'male'),('avg_month_end_female',female,'female'),('avg_month_end_total',total,'all')]:
        add('EAW_PARL_HIST','England & Wales',year,meas,val,URL_EW,'Table 1a, printed p.19',{'avg_month_end_male':'Males','avg_month_end_female':'Females','avg_month_end_total':'Total'}[meas],grade='B',timebasis='calendar year: average of 12 end-of-month population snapshots',flags='month_end_mean_not_daily_mean|exact_definition_verified',note='Not interchangeable with Palestine daily average; 12 month-end snapshot mean. Existing v7 mislabeled avg_daily_* has been remapped.',sex=sex)

for year,val in [tuple(map(int,x.split())) for x in SCOT.splitlines()]:
    add('SCT_UK_PARL_2017','Scotland',year,'avg_daily_total',val,URL_SC,'Table 10a, printed p.39','Daily average prison population — Scotland',grade='A',timebasis='calendar-year daily average for 1900–1995',flags='official_commons_archived_table',note='Commons Library SN04334 (20 April 2017), Table 10a, reproducing Scottish Government prison statistics.')

for year,recs,distinct,rate,avg in [(int(p[0]),int(p[1]),int(p[2]),float(p[3]),int(p[4])) for p in (line.split() for line in NZ.splitlines())]:
    for measure,val,heading,unit in [('receptions_excluding_transfers',recs,'Total Receptions, inter-institutional transfers eliminated','admissions'),('distinct_persons_received',distinct,'Number of distinct persons received','persons'),('distinct_receptions_rate_per_10000',rate,'Ratio to 10,000 general population','per_10000'),('avg_daily_total',avg,'Daily average','persons')]:
        add('NZ_AJHR_PRISONS','New Zealand',year,measure,val,URL_NZ,'Receptions retrospective table, 1932–1938',heading,unit=unit,grade='A' if measure=='avg_daily_total' else 'B',timebasis='calendar year; 1938 Prisons Department retrospective table',flags='receptions_separate_from_distinct_persons'+('|1937_860_table_vs_866_prose' if year==1937 and measure=='avg_daily_total' else ''),note=('1937 discrepancy: retrospective table states 860 daily average; narrative states 866; 860 transcribed from table, unresolved.' if year==1937 and measure=='avg_daily_total' else 'Do not conflate total receptions net of transfers with distinct persons received or gross admissions.'))
# The 1938 report prose explicitly supplies gross and inter-institutional transfer counts.
for measure,val,heading in [('receptions_gross_including_transfers',4328,'Aggregate number of receptions'),('interinstitutional_transfers',792,'Inter-institutional transfers included in aggregate')]:
    add('NZ_AJHR_PRISONS','New Zealand',1938,measure,val,URL_NZ,'1938 Prison Statistics narrative',heading,unit='admissions',grade='B',timebasis='calendar 1938',flags='reception_components',note='4328 gross receptions − 792 inter-institutional transfers = 3536 receptions net of transfers.')

for yr,rt,rm,rf,av,ac,au in [tuple(map(int,x.split())) for x in NI.splitlines()]:
    assert rm+rf==rt,(yr,'receptions')
    assert ac+au==av,(yr,'daily')
    specs=[('admissions_total',rt,'Receptions total','all'),('admissions_male',rm,'Receptions males','male'),('admissions_female',rf,'Receptions females','female'),('avg_daily_total',av,'Daily average population total','all'),('avg_daily_convicted',ac,'Daily average population convicted','all'),('avg_daily_unconvicted',au,'Daily average population unconvicted','all')]
    for m,val,h,sex in specs:
        add('NIR_AAS_1937_47','Northern Ireland',yr,m,val,URL_NI,'Table 72, printed p.68',''+h,unit='admissions' if m.startswith('admissions_') else 'persons',grade='A',timebasis='calendar year 1937–1947',flags='table_72_direct',sex=sex,note='Unconvicted includes remand/awaiting trial and civil process as defined in the table.' if 'unconvicted' in m else 'Northern Ireland Annual Abstract of Statistics, Ministry of Home Affairs.')
for yr,total,male,female,prior_pct in [tuple(map(int,x.split())) for x in NI_PRIOR.splitlines()]:
    assert male+female==total,(yr,'convicted')
    for m,val,head,sex,unit in [('convicted_prisoners_count',total,'Number of convicted prisoners: persons','all','persons'),('convicted_prisoners_male',male,'Number of convicted prisoners: males','male','persons'),('convicted_prisoners_female',female,'Number of convicted prisoners: females','female','persons'),('male_convicted_prior_offences_pct',prior_pct,'Percentage of convicted males with known previous proved offences','male','percent')]:
        add('NIR_AAS_1937_47','Northern Ireland',yr,m,val,URL_NI,'Table 73, printed p.68',head,unit=unit,grade='B',timebasis='1937–1947 reporting year',flags='previous_offence_not_reconviction_rate',sex=sex,legal='convicted',note='Prior proved offence prevalence among convicted men is NOT a prospective reconviction or reoffending rate.' if 'prior_offences' in m else 'Table 73 count of convicted prisoners.')

# Hong Kong: only new values and expressly differentiated sentencing basis for 1946.
for year,measure,val,head,link,flag in [
    (1933,'admissions_total',11439,'Persons committed to prison',URL_HK,'committals_scope_source_label'),
    (1933,'avg_daily_total',1472,'Daily average prisoners in prisons',URL_HK,'reported_daily_average'),
    (1931,'avg_daily_juveniles',4.5,'Daily average number of juveniles',URL_HK,'juveniles_within_prison_system'),
    (1932,'avg_daily_juveniles',3.7,'Daily average number of juveniles',URL_HK,'juveniles_within_prison_system'),
    (1933,'avg_daily_juveniles',4.1,'Daily average number of juveniles',URL_HK,'juveniles_within_prison_system'),
    (1939,'admissions_total',16146,'Persons committed to prisons in 1939 (reported retrospectively in 1946)',URL_HK46,'retrospective_1939_statement'),
    (1946,'admissions_total',8963,'Persons committed to prisons in 1946',URL_HK46,'postwar_reporting_scope_review'),
    (1946,'avg_daily_sentenced',1214,'Daily average of persons serving sentences',URL_HK46,'sentenced_only_not_all_prisoners')]:
    add('HKG_ADMIN','Hong Kong',year,measure,val,link,'Prisons paragraph, Hong Kong annual report '+('1946' if year in (1939,1946) else str(year)),head,unit='admissions' if 'admissions' in measure else 'persons',grade='B',timebasis=str(year)+' calendar year',flags=flag,note='1946 sentenced prisoners are not equivalent to daily average of all prisoners.' if measure=='avg_daily_sentenced' else 'Transcribed from Hong Kong administration report; source printed figure.')

# Basutoland primary report: adults only for mean, avoid harmonizing with overall daily average.
for year,admissions,penal,avg in [(1936,3364,2341,550.4),(1937,2650,1672,432.8)]:
    for m,val,heading,unit in [('admissions_total',admissions,'Persons admitted to prison','admissions'),('admissions_penal_imprisonment',penal,'Committed to penal imprisonment','admissions'),('avg_daily_adults',avg,'Daily average of adults confined','persons')]:
        add('BAS_COL_REPORT_1937','Basutoland',year,m,val,URL_BAS,'Colonial Annual Report 1937, printed p.42',heading,unit=unit,grade='B',timebasis='calendar '+str(year),flags='historical_adult_only_mean',note='Primary report. Adult-only daily average cannot be treated as whole-system mean without checking juvenile coverage.')

# Uganda WPB values are provisionally SOURCE-SPECIFIC, explicitly excluded from comparison.
for year,number in [(1921,1477),(1927,1681),(1934,1859),(1938,1318),(1944,2036)]:
    add('UGA_WPB_HIST','Uganda',year,'population_point_total',number,URL_UGA,'Prison population trend up to 2000','Prison population total',grade='U',timebasis='WPB historic point (date or mean not specified)',flags='blocked_from_comparison|definition_unresolved|1938_conflicts_EAF_1938_JSH',note='Unresolved: WPB 1938 = 1,318 vs 1938 colonial comparative table DAILY AVERAGE = 4,225. Do not infer cause or combine before verifying institution universe and dates.')

path=SNAPSHOTS/'v8_verified_snapshots.csv'
pd.DataFrame(rows).to_csv(path,index=False,encoding='utf-8-sig')
print('Wrote',len(rows),'observations to',path)
print(pd.DataFrame(rows).groupby('source_dataset').size())
