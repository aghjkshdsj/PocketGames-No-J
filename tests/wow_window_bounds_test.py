"""Compile and run the patched pinned Wine placement function against device bounds."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bounds', ROOT / 'engine/wine/patches/wow_window_bounds.py')
bounds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bounds)
FIXTURE = ROOT / 'tests/fixtures/wow-window-band.c'


class WindowBoundsTests(unittest.TestCase):
    def test_patch_is_idempotent_and_rejects_changed_input(self):
        text = FIXTURE.read_text(encoding='utf-8')
        patched = bounds.patch(text)
        self.assertEqual(patched, bounds.patch(patched))
        with self.assertRaises(ValueError):
            bounds.patch(text.replace(bounds.ANCHOR, 'changed upstream placement'))
        with self.assertRaises(ValueError):
            bounds.patch(bounds.MARK)

    @unittest.skipUnless(shutil.which('cc'), 'C compiler required; exercised by CI host tests')
    def test_actual_patched_function_on_device_and_boundary_maps(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'bounds.c'
            exe = Path(tmp) / 'bounds-test'
            compiler = ['cc', '-std=c11', '-D_POSIX_C_SOURCE=200809L',
                        '-Wall', '-Wextra', '-Werror']
            source.write_text(FIXTURE.read_text(encoding='utf-8'), encoding='utf-8')
            subprocess.run(compiler + ['-DORIGINAL_BUG', str(source), '-o', str(exe)], check=True)
            subprocess.run([str(exe)], check=True)
            source.write_text(bounds.patch(FIXTURE.read_text(encoding='utf-8')), encoding='utf-8')
            subprocess.run(compiler + [str(source), '-o', str(exe)], check=True)
            subprocess.run([str(exe)], check=True)


if __name__ == '__main__':
    unittest.main()
