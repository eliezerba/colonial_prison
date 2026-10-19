"""v8 regression tests: semantic normalization, source reconciliation and UI guardrails."""
import unittest
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'site'/'downloads'
NEW={'EAW_PARL_HIST','SCT_UK_PARL_2017','NIR_AAS_1937_47','NZ_AJHR_PRISONS','HKG_ADMIN','BAS_COL_REPORT_1937','UGA_WPB_HIST'}

class V8ExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obs=pd.read_csv(D/'observations.csv').fillna('')
        cls.reg=pd.read_csv(D/'source_registry.csv').fillna('')
        cls.mr=pd.read_csv(D/'measure_registry.csv').fillna('')
        cls.script=(ROOT/'site'/'assets'/'app.js').read_text('utf8')
        cls.html=(ROOT/'site'/'index.html').read_text('utf8')
    def group(self,source): return self.obs[self.obs.source_dataset==source]
    def value(self,source,year,measure):
        z=self.obs[(self.obs.source_dataset==source)&(self.obs.year==year)&(self.obs.measure==measure)]
        self.assertEqual(len(z),1,(source,year,measure,len(z)))
        return float(z.iloc[0].value)
    def test_snapshot_count_and_registered_sources(self):
        v=pd.read_csv(ROOT/'pipeline'/'snapshots'/'v8_verified_snapshots.csv')
        self.assertEqual(len(v),289)
        self.assertEqual(len(v[v.source_dataset=='EAW_PARL_HIST']),99)
        self.assertEqual(len(self.obs[self.obs.quality_flag.astype(str).str.contains('v8_curated')]),289)
        self.assertTrue(NEW.issubset(set(self.reg.source_id)))
    def test_england_wales_corrected_semantics(self):
        d=self.group('EAW_PARL_HIST')
        self.assertEqual(len(d),99)
        self.assertFalse(d.measure.str.startswith('avg_daily').any())
        self.assertTrue(d.time_basis.eq('mean_of_12_month_end_snapshots').all())
        self.assertTrue(d.comparability_grade.eq('B').all())
        for y in sorted(d.year.unique()):
            self.assertEqual(self.value('EAW_PARL_HIST',y,'avg_month_end_male')+
                             self.value('EAW_PARL_HIST',y,'avg_month_end_female'),
                             self.value('EAW_PARL_HIST',y,'avg_month_end_total'))
    def test_scotland_continuous_daily_mean(self):
        x=self.group('SCT_UK_PARL_2017')
        self.assertEqual(set(x.year),set(range(1920,1951)))
        self.assertTrue(x.measure.eq('avg_daily_total').all())
        self.assertEqual(self.value('SCT_UK_PARL_2017',1938,'avg_daily_total'),1543)
    def test_new_zealand_receptions_distinct_and_daily(self):
        self.assertEqual(self.value('NZ_AJHR_PRISONS',1938,'receptions_gross_including_transfers'),4328)
        self.assertEqual(self.value('NZ_AJHR_PRISONS',1938,'interinstitutional_transfers'),792)
        self.assertEqual(self.value('NZ_AJHR_PRISONS',1938,'receptions_excluding_transfers'),3536)
        self.assertEqual(self.value('NZ_AJHR_PRISONS',1938,'distinct_persons_received'),2224)
        self.assertEqual(self.value('NZ_AJHR_PRISONS',1938,'avg_daily_total'),870)
    def test_new_zealand_1937_discrepancy_retained(self):
        r=self.group('NZ_AJHR_PRISONS')
        q=r[(r.year==1937)&(r.measure=='avg_daily_total')]
        self.assertTrue((q.value==860).any())
        self.assertTrue(q.quality_flag.str.contains('1937_860_table_vs_866_prose').any())
    def test_northern_ireland_table_72_consistency(self):
        x=self.group('NIR_AAS_1937_47')
        self.assertEqual(len(x),110)
        for year in range(1937,1948):
            self.assertEqual(self.value('NIR_AAS_1937_47',year,'admissions_male')+
                             self.value('NIR_AAS_1937_47',year,'admissions_female'),
                             self.value('NIR_AAS_1937_47',year,'admissions_total'))
            self.assertEqual(self.value('NIR_AAS_1937_47',year,'avg_daily_convicted')+
                             self.value('NIR_AAS_1937_47',year,'avg_daily_unconvicted'),
                             self.value('NIR_AAS_1937_47',year,'avg_daily_total'))
            self.assertEqual(self.value('NIR_AAS_1937_47',year,'convicted_prisoners_male')+
                             self.value('NIR_AAS_1937_47',year,'convicted_prisoners_female'),
                             self.value('NIR_AAS_1937_47',year,'convicted_prisoners_count'))
    def test_northern_ireland_prior_offences_not_reoffending_rate(self):
        x=self.group('NIR_AAS_1937_47')
        rows=x[x.measure=='male_convicted_prior_offences_pct']
        self.assertEqual(len(rows),11)
        self.assertTrue(rows.quality_flag.str.contains('previous_offence_not_reconviction_rate').all())
        self.assertFalse((x.measure=='recidivism_rate_pct').any())
    def test_hong_kong_postwar_average_is_sentenced_only(self):
        self.assertEqual(self.value('HKG_ADMIN',1946,'avg_daily_sentenced'),1214)
        x=self.group('HKG_ADMIN')
        q=x[(x.year==1946)&x.measure.eq('avg_daily_total')]
        self.assertTrue(q.empty)
    def test_basutoland_average_is_adults_only(self):
        x=self.group('BAS_COL_REPORT_1937')
        self.assertEqual(len(x),6)
        self.assertEqual(set(x.measure),{'admissions_total','admissions_penal_imprisonment','avg_daily_adults'})
        self.assertTrue(x[x.measure=='avg_daily_adults'].time_basis.eq('annual_daily_average_adults_only').all())
    def test_uganda_restricted_in_comparison_and_map(self):
        x=self.group('UGA_WPB_HIST')
        self.assertEqual(len(x),5)
        self.assertTrue(x.comparability_grade.eq('U').all())
        self.assertTrue(x.quality_flag.str.contains('blocked_from_comparison').all())
        self.assertEqual(self.value('UGA_WPB_HIST',1938,'population_point_total'),1318)
        self.assertEqual(self.script.count("!String(r.quality_flag||'').includes('blocked_from_comparison')"),2)
    def test_v8_sources_provenance_and_mapping(self):
        v=self.obs[self.obs.quality_flag.str.contains('v8_curated')]
        for name in ('source_url','source_locator','source_record_id','transformation','concept_id'):
            self.assertTrue(v[name].astype(str).str.strip().ne('').all(),name)
        self.assertFalse(v.observation_id.duplicated().any())
        self.assertTrue(set(v.measure).issubset(set(self.mr.measure)))
    def test_interface_atlas_and_downloads_include_new_docs(self):
        self.assertIn('50 המקורות',self.html)
        self.assertIn('107 המדדים',self.html)
        for name in ('DATA_EXPANSION_V8.md','V8_QA_REPORT.md'):
            self.assertTrue((D/name).exists(),name)

if __name__=='__main__':unittest.main()
