"""Synthetic end-to-end release tests. No live news or mail is sent."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from briefing.model import initialize, write, read, digest
from briefing.validate import check
from briefing.render import build
from paths import ROOT
from verify_authoritative import validate as verify
from validate_snapshot import validate as validate_snapshot


def fill_synthetic(folder):
    """Entirely fictional fixture, deliberately uses reserved example.com URLs."""
    now = '2026-10-03T10:00:00+00:00'
    write(folder / 'edition.json', {'schema_version': 1, 'issue_date': '2026-10-03', 'cutoff': now,
          'overview': '合成测试：示例实验室发布方法。', 'overview_en': 'SYNTHETIC TEST: an example lab publishes a method.',
          'events': [{'id':'event-one', 'headline':'合成测试：实验方法发布', 'headline_en':'Synthetic test: a lab publishes a method',
                      'section':'Core Developments','topic':'science','region':'Global','claim_ids':['claim-one'],
                      'why_it_matters':'仅用于测试。','why_it_matters_en':'This is fictional test data, not a news report.'}]})
    rows = []
    items = []
    for number in (1, 2):
        url = f'https://example.com/source-{number}'
        rows.append({'id':f'evidence-{number}','source_id':f'source-{number}','publisher':f'Synthetic publisher {number}',
                     'url':url,'published_at':now,'checked_at':now,'checked_by':'Synthetic fixture',
                     'level':'primary_document','dependency_group':f'chain-{number}',
                     'locator':'Synthetic paragraph 1','support':'Fictional fixture: an example method was published.'})
        items.append({'id':str(number),'source_id':f'source-{number}','publisher':f'Synthetic publisher {number}', 'url':url,'published_at':now})
    write(folder/'evidence/input.json', {'schema_version':5, 'snapshot_as_of':now,'completed_at':now,
          'run_args':{'max_age_hours':36,'limit':15},'sources':[], 'items':items,'summary':{'candidate_items':2}})
    write(folder/'evidence/claims.json', {'schema_version':1,'evidence':rows,'claims':[
          {'id':'claim-one','event_id':'event-one','kind':'reporting','status':'verified','text':'合成测试：方法已发布。',
           'text_en':'SYNTHETIC TEST: the method was published.','evidence_ids':['evidence-1','evidence-2']}]})
    write(folder/'evidence/selection-ledger.json', {'schema_version':2, 'issue_date':'2026-10-03','input_snapshot':'evidence/input.json',
          'coverage_review':[{'area':'science','status':'covered','note':'Synthetic test only.'}],
          'candidates':[{'event_id':'event-one','decision':'selected','reason':'Synthetic test.','cluster_key':'lab-method-20261003',
                        'story_id':'example-lab','information_gain':'First publication in synthetic scenario.',
                        'global_significance':'B','briefing_priority':'B','attention':'Medium','confidence':'High'}]})


def approve_synthetic(folder):
    report = check(folder, require_review=False)
    write(folder/'evidence/review.json', {'schema_version':1,'decision':'approved','input_sha256':digest(folder),
          'reviewed_by':'Synthetic test fixture only','reviewed_at':'2026-10-03T11:00:00+00:00',
          'checks_completed':['facts','translations','source_independence','coverage','prior_issue','headline_and_analysis'],
          'disclosures':{item['code']:'Synthetic test coverage is intentionally limited.' for item in report['findings'] if item['severity']=='P1'}})


class EditionTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'tmp').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='edition-tests-', dir=ROOT/'tmp')
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)/'edition'
        initialize(self.folder, '2026-10-03')
        fill_synthetic(self.folder)

    def mutate(self, name, fn):
        data = read(self.folder/name)
        fn(data)
        write(self.folder/name, data)

    def codes(self, review=False):
        return {row['code'] for row in check(self.folder, require_review=review)['findings']}

    def test_review_is_required_and_cannot_be_reused_after_content_change(self):
        self.assertFalse(check(self.folder)['ready'])
        approve_synthetic(self.folder)
        self.assertTrue(check(self.folder)['ready'])
        self.mutate('edition.json', lambda d:d.update(overview_en='Changed text'))
        self.assertIn('review.stale', self.codes(review=True))

    def test_dangling_evidence_blocks_build(self):
        self.mutate('evidence/claims.json', lambda d:d['claims'][0].update(evidence_ids=['missing']))
        self.assertIn('evidence.reference.missing',self.codes())
        with self.assertRaises(ValueError): build(self.folder)
        self.assertFalse((self.folder/'delivery').exists())

    def test_syndication_does_not_count_as_independent_confirmation(self):
        self.mutate('evidence/claims.json', lambda d:d['evidence'][1].update(dependency_group='chain-1'))
        self.assertIn('single-source.claim-one',self.codes())

    def test_selected_candidates_must_match_rendered_events(self):
        self.mutate('evidence/selection-ledger.json',lambda d:d['candidates'][0].update(decision='rejected'))
        self.assertIn('selection.mismatch',self.codes())

    def test_p1_requires_a_visible_disclosure(self):
        approve_synthetic(self.folder)
        self.mutate('evidence/review.json',lambda d:d.update(disclosures={}))
        self.assertIn('undisclosed.event.count',self.codes(review=True))

    def test_package_contains_english_body_and_matching_full_attachment(self):
        approve_synthetic(self.folder)
        manifest=build(self.folder)
        self.assertEqual(manifest['status'],'prepared_not_sent')
        self.assertIn('SYNTHETIC TEST: the method was published.',(self.folder/'delivery/email.html').read_text())
        self.assertIn('合成测试',(self.folder/'brief.md').read_text())
        self.assertEqual((self.folder/'brief.md').read_bytes(),(self.folder/'delivery/brief-full.md').read_bytes())
        for name, value in manifest['sha256'].items():
            self.assertEqual(hashlib.sha256((self.folder/'delivery'/name).read_bytes()).hexdigest(),value)
        with ZipFile(self.folder/'delivery/supporting-materials.zip') as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(archive.read('evidence/input.json'),(self.folder/'evidence/input.json').read_bytes())
        with self.assertRaises(ValueError):build(self.folder)

    def test_html_escapes_editorial_text(self):
        self.mutate('edition.json',lambda d:d.update(overview_en='<script>alert(1)</script>'))
        approve_synthetic(self.folder)
        build(self.folder)
        body=(self.folder/'delivery/email.html').read_text()
        self.assertNotIn('<script>',body)
        self.assertIn('&lt;script&gt;',body)

    def test_init_does_not_overwrite_existing_edition(self):
        with self.assertRaises(ValueError):initialize(self.folder,'2026-10-03')

    def test_malformed_and_naive_timestamps_fail_cleanly(self):
        self.mutate('edition.json',lambda d:d.update(cutoff='not-a-date'))
        self.assertIn('invalid.input',self.codes())
        snapshot=read(self.folder/'evidence/input.json')
        snapshot['items'][0]['published_at']='2026-10-03T10:00:00'
        self.assertTrue(any(level=='P0' for level,_ in validate_snapshot(snapshot)))

    def test_authoritative_window_uses_cutoff_not_completion(self):
        snapshot=read(ROOT/'editions/2026/10/03/evidence/input.json')
        snapshot['completed_at']='2030-01-01T00:00:00+00:00'
        self.assertEqual(verify(snapshot),[])
        snapshot['run_args']['max_age_hours']=0.001
        self.assertTrue(any('outside snapshot window' in message for message in verify(snapshot)))

    def test_legacy_edition_without_claims_is_not_ready(self):
        result=check(ROOT/'editions/2026/10/03')
        self.assertFalse(result['ready'])
        self.assertIn('missing.evidence/claims.json',{f['code'] for f in result['findings']})

    def test_content_only_never_marks_an_edition_ready(self):
        result=check(self.folder, require_review=False)
        self.assertTrue(result['passed'])
        self.assertFalse(result['ready'])

    def test_reading_does_not_count_as_a_news_event(self):
        self.mutate('edition.json',lambda d:d['events'][0].update(section='Worth Reading'))
        result=check(self.folder,require_review=False)
        self.assertEqual(result['coverage']['events'],0)
        self.assertEqual(result['coverage']['entries'],1)

    def test_uncertain_claim_cannot_receive_high_confidence(self):
        self.mutate('evidence/claims.json',lambda d:d['claims'][0].update(status='unconfirmed'))
        self.assertIn('confidence.overstated.event-one',self.codes())

    def test_source_url_must_be_http_or_https(self):
        self.mutate('evidence/claims.json',lambda d:d['evidence'][0].update(url='javascript:alert(1)'))
        self.assertIn('evidence.evidence-1.url',self.codes())

    def test_one_url_cannot_be_two_independent_sources(self):
        self.mutate('evidence/claims.json',lambda d:d['evidence'][1].update(url=d['evidence'][0]['url']))
        self.assertIn('evidence.evidence-2.dependency',self.codes())


if __name__=='__main__': unittest.main()
