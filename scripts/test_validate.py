import json
from pathlib import Path
import shutil
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
        self.assertEqual(validate.validate_repository(self.root), 5)

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
