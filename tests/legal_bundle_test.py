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
    def test_generated_dock_notice_retains_all_original_notices(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / legal.LEGAL, root / legal.LEGAL)
            for source in legal.COPIES.values():
                target = root / source
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / source, target)
            dock = root / 'App/Generated/pedylib/winepe/dock-notices.txt'
            dock.parent.mkdir(parents=True)
            data = b'\n\n'.join((root / legal.LEGAL / name).read_bytes() for name in (
                'Dock-LICENSE.txt', 'Dock-LICENSE-EXCEPTION.txt', 'Dock-MinGW-w64-runtime.txt', 'Dock-LLVM.txt'))
            dock.write_bytes(data)
            import os
            from unittest.mock import patch
            with patch.dict(os.environ, {'GITHUB_SHA':'a' * 40}):
                legal.prepare(root=root)
                self.assertEqual((root / legal.LEGAL / 'Dock-Combined-Notices.txt').read_bytes(), data)
                dock.write_bytes(b'Truncated notices')
                with self.assertRaises(AssertionError):
                    legal.prepare(root=root)

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
