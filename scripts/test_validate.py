import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import validate


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'examples'
        shutil.copytree(validate.ROOT, self.root, ignore=shutil.ignore_patterns('.git', '__pycache__'))

    def manifest(self):
        return json.loads((self.root / 'manifest.json').read_text())

    def save(self, manifest):
        (self.root / 'manifest.json').write_text(json.dumps(manifest))

    def test_current_canonical_collection(self):
        self.assertEqual(validate.validate_repository(self.root), 6)

    def test_duplicate_recipe_is_rejected(self):
        manifest = self.manifest()
        manifest['recipes'].append(manifest['recipes'][0])
        self.save(manifest)
        with self.assertRaisesRegex(ValueError, 'distinct recipes'):
            validate.validate_repository(self.root)

    def test_advanced_demo_destination_readback(self):
        recipe = self.root / 'recipes/settlement-review'
        expected = json.loads((recipe / 'expected.json').read_text())
        for name in ('comparisons', 'totals'):
            self.assertEqual(json.loads((recipe / ('observed-' + name + '.json')).read_text())['rows'], expected[name])

    def test_advanced_checker_rejects_corrupt_destination_fields(self):
        recipe = self.root / 'recipes/settlement-review'
        command = [sys.executable, str(recipe / 'check-results.py'), str(recipe / 'observed-comparisons.json'), str(recipe / 'observed-totals.json')]
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        for name, field in [('comparisons', 'reported_net'), ('totals', 'matched_count')]:
            path = recipe / ('observed-' + name + '.json')
            data = json.loads(path.read_text())
            data['rows'][0][field] += 1
            path.write_text(json.dumps(data))
            with self.subTest(output=name):
                self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            path.write_text(json.dumps({"rows": json.loads((recipe / 'expected.json').read_text())[name]}))

    def test_external_asset_is_rejected(self):
        manifest = self.manifest()
        manifest['recipes'][0]['assets'].append('../private-key')
        self.save(manifest)
        with self.assertRaisesRegex(ValueError, 'out-of-repository'):
            validate.validate_repository(self.root)

    def test_markdown_symlink_cannot_read_outside_repository(self):
        outside = Path(self.temp.name) / 'outside.md'
        outside.write_text('external content')
        (self.root / 'unexpected.md').symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'out-of-repository'):
            validate.validate_repository(self.root)

    def test_changed_spec_cannot_reuse_old_evidence(self):
        recipe = self.manifest()['recipes'][0]
        spec = self.root / recipe['spec']
        spec.write_text(spec.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'stale validation evidence'):
            validate.validate_repository(self.root)

    def test_changed_fixture_cannot_reuse_old_execution(self):
        fixture = self.root / 'recipes/http-customer-enrichment/fixtures/orders.json'
        fixture.write_text(fixture.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'stale execution input/expected evidence'):
            validate.validate_repository(self.root)

    def test_missing_qualification_hash_is_rejected(self):
        for recipe in self.manifest()['recipes']:
            evidence = self.root / recipe['execution']['evidence']
            original = evidence.read_text()
            data = json.loads(original)
            hashes = data['qualification_asset_hashes']
            for omitted in [None, *hashes]:
                with self.subTest(recipe=recipe['slug'], omitted=omitted):
                    data['qualification_asset_hashes'] = {} if omitted is None else {k: v for k, v in hashes.items() if k != omitted}
                    evidence.write_text(json.dumps(data))
                    with self.assertRaisesRegex(ValueError, 'missing qualification input hashes'):
                        validate.validate_repository(self.root)
                evidence.write_text(original)

    def test_incomplete_run_cannot_claim_execution(self):
        recipe = self.manifest()['recipes'][0]
        evidence = self.root / recipe['execution']['evidence']
        data = json.loads(evidence.read_text())
        data['events'] = [e for e in data['events'] if e.get('step') != 'export-orders']
        evidence.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'complete step/destination evidence'):
            validate.validate_repository(self.root)


if __name__ == '__main__':
    unittest.main()
