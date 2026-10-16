"""Reject missing/stale legal resources before an IPA can be published."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('legal', ROOT / 'tools/prepare_licenses.py')
legal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legal)


class LegalBundleTests(unittest.TestCase):
    def test_checked_in_notices_match_originals(self):
        legal.prepare(check=True)

    def test_missing_or_changed_notices_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = Path(tmp)
            shutil.copytree(ROOT / legal.LEGAL, app / 'Legal')
            index = legal.validate(app / 'Legal')
            doc = app / 'Legal' / index['documents'][-1]['file']
            doc.write_text('incomplete notice', encoding='utf-8')
            with self.assertRaises(AssertionError):
                legal.validate(app / 'Legal')
            doc.unlink()
            with self.assertRaises(FileNotFoundError):
                legal.validate(app / 'Legal')

    def test_app_contains_exact_reviewed_manifest_and_source_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = Path(tmp)
            shutil.copytree(ROOT / legal.LEGAL, app / 'Legal')
            revision = 'a' * 40
            import os
            from unittest.mock import patch
            (app / 'Legal/build-info.json').write_text(json.dumps({
                'revision': revision, 'sourceURL': f'{legal.REPOSITORY}/tree/{revision}',
            }))
            with patch.dict(os.environ, {'GITHUB_SHA':revision}):
                legal.validate_app(app)
            with patch.dict(os.environ, {'GITHUB_SHA':'b' * 40}):
                with self.assertRaises(AssertionError):
                    legal.validate_app(app)


if __name__ == '__main__':
    unittest.main()
