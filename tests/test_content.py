"""Integrity and evidence-boundary checks for records and generated views."""

import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import build_lab


class ContentTests(unittest.TestCase):
    def test_measurements_require_observed_provenance(self):
        data=build_lab.load_content()
        experiment={'id':'TEST-PROVENANCE','system':'observatory','type':'planned',
                    'measurements':[{'label':'Fixture latency','value':1,'unit':'µs'}],
                    'source':{'label':'Test fixture','url':'https://example.invalid/fixture'}}
        data['experiments'].append(experiment)
        with self.assertRaises(ValueError):
            build_lab.validate_content(data)
        experiment['type']='measured'
        source=experiment.pop('source')
        with self.assertRaises(ValueError):
            build_lab.validate_content(data)
        experiment['source']=source
        build_lab.validate_content(data)

    def test_unknown_system_references_are_rejected(self):
        data=build_lab.load_content()
        data['field-logs'].append({'id':'TEST-REFERENCE','system':'unrecorded-system'})
        with self.assertRaises(ValueError):
            build_lab.validate_content(data)

    def test_counts_are_from_content_not_fixed_ui_numbers(self):
        data=build_lab.load_content()
        result=build_lab.outputs(data)
        counts=json.loads(result['content/derived.json'])['counts']
        self.assertEqual(counts['experiments'],len(data['experiments']))
        data['experiments']=[]
        data['current-signal']['latestExperiment']=None
        result=build_lab.outputs(data)
        self.assertEqual(json.loads(result['content/derived.json'])['counts']['experiments'],0)
        self.assertIn('NO RECORDS YET',result['index.html'])

    def test_empty_archives_and_transmissions_render_honestly(self):
        data=build_lab.load_content()
        data['failures']=[]
        data['transmissions']=[]
        result=build_lab.outputs(data)
        rendered=result['index.html']
        self.assertIn('NO TRANSMISSIONS YET',rendered)
        self.assertIn('An empty archive does not imply',rendered)
        self.assertIn('No transmissions yet.',result['README.md'])

    def test_content_is_escaped_and_terminal_data_cannot_close_script(self):
        data=build_lab.load_content()
        data['site']['intro']='</script><img src=x onerror=alert(1)>'
        rendered=build_lab.outputs(data)['index.html']
        self.assertNotIn('</script><img',rendered)
        self.assertIn('\\u003c/script>',rendered)
        self.assertIn('&lt;/script&gt;',rendered)

    def test_unsafe_evidence_urls_are_rejected(self):
        for value in ['javascript:alert(1)','//example.com','../private','https://user:password@example.com']:
            with self.subTest(value=value),self.assertRaises(ValueError):
                build_lab.valid_url(value)

    def test_missing_completion_is_not_zero_or_success(self):
        metric={'label':'Job completion','value':None,'unit':'µs'}
        self.assertIn('Not completed',build_lab.metrics([metric]))

    def test_generated_files_match_source(self):
        for name,value in build_lab.outputs(build_lab.load_content()).items():
            with self.subTest(name=name):
                self.assertEqual((ROOT/name).read_text(),value)


if __name__=='__main__':unittest.main()
