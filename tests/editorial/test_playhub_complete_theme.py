import copy, json, runpy, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MODULE=runpy.run_path(str(ROOT/'content/expansion/integrate_playhub_theme_complete.py'))

class CompleteThemeTests(unittest.TestCase):
 def test_exact_source_text_order_and_original_archive(self):
  doc=MODULE['checked_document'](ROOT)
  original=json.loads((ROOT/doc['previous_record_archive']).read_text(encoding='utf8'))['source_record']
  records=[copy.deepcopy(original),{'id':'sentinel','body':['Unrelated narrative remains unchanged.'],'images':[]}]
  before=copy.deepcopy(records)
  report=MODULE['integrate'](records,ROOT)
  self.assertEqual(len(records[0]['body']),11)
  self.assertEqual(records[0]['body'],doc['body'])
  self.assertEqual(report['previous_projection']['body'],before[0]['body'])
  self.assertEqual(records[1],before[1])
  first=copy.deepcopy(records)
  MODULE['integrate'](records,ROOT)
  self.assertEqual(records,first)
 def test_every_paragraph_unique_hd_image_and_official_films(self):
  doc=MODULE['checked_document'](ROOT)
  self.assertEqual({i['story_paragraph'] for i in doc['images'] if i['story_paragraph']>=0},set(range(11)))
  self.assertEqual(len({i['source_pixel_sha256'] for i in doc['images']}),13)
  self.assertTrue(all(max(i['width'],i['height'])>=1000 for i in doc['images']))
  self.assertFalse(any('youth' in i['url'] for i in doc['images']))
  self.assertEqual([v['youtube_id'] for v in doc['videos']],['6thnV_sV96M','r1f4LuF74cM'])
  self.assertTrue(all(v['verification']['avc_format_count']>0 and v['verification']['aac_format_count']>0 for v in doc['videos']))
  self.assertFalse(any('playhub' in i['credit'].lower() or 'lozazamastro' in i['credit'].lower() for i in doc['images']))

if __name__=='__main__':unittest.main()
