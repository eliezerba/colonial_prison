import unittest,re,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class V83InterfaceTests(unittest.TestCase):
 def test_source_links_and_details(self):
  s=(ROOT/'site/assets/app.js').read_text()
  self.assertIn('data-source-external',s)
  self.assertIn('data-source-profile',s)
  self.assertIn('source-method',s)
  self.assertIn('source_record_id',s)
  rows=json.loads(re.search(r'=\s*(\[.*\]);?',(ROOT/'site/data/sources.js').read_text(),re.S).group(1))
  self.assertEqual(len(rows),50)
  self.assertTrue(all(str(x.get('url','')).startswith(('https://','http://')) for x in rows))
 def test_guided_compare_reset(self):
  html=(ROOT/'site/index.html').read_text(); js=(ROOT/'site/assets/app.js').read_text()
  for key in ['cmpAvailability','cmpAvailableCount','resetCompare','cmpJurisdictions']:
   self.assertIn('id="'+key+'"',html)
  for key in ['function compareAvailability()','function resetCompare()','compare-count','blocked_from_comparison','common.length','input.disabled=!usable']:
   self.assertIn(key,js)
 def test_unchanged_chart_inventory(self):
  current=(ROOT/'site/index.html').read_text()
  original=Path('/mnt/data/v82work/colonial_prison_explorer_v8_2/site/index.html').read_text() if Path('/mnt/data/v82work/colonial_prison_explorer_v8_2/site/index.html').exists() else current
  pat=r'id="((?:p[A-Z]|cmp[A-Z]|map[A-Z]|sourceChart|measureChart)[a-zA-Z0-9]+)"'
  self.assertFalse(set(re.findall(pat,original))-set(re.findall(pat,current)))
if __name__=='__main__':unittest.main()
