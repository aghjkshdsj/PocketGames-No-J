"""Validate source, path, environment-key and PE byte-preserving namespace updates."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

source = Path(__file__).resolve().parents[1] / "tools/port_source.py"
spec = importlib.util.spec_from_file_location("port_source", source)
port = importlib.util.module_from_spec(spec)
spec.loader.exec_module(port)


class NamespaceTests(unittest.TestCase):
    def test_symbols_and_environment_keys(self):
        self.assertEqual(port.namespace("OldPort oldport OLDPORT", "OldPort"), "DanPort danport DANPORT")

    def test_paths_and_binary_offsets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "app/OldPort"
            folder.mkdir(parents=True)
            binary = b"\0prefix\0OLDPORT_EXE\0oldport.dll\0" + "OldPort.exe".encode("utf-16-le")
            (folder / "oldport.dll").write_bytes(binary)
            (folder / "Bridge.c").write_text('getenv("OLDPORT_EXE"); oldport_display();')
            port.normalize(root, "OldPort")
            output = root / "app/DanPort/danport.dll"
            self.assertEqual(len(output.read_bytes()), len(binary))
            self.assertIn(b"DANPORT_EXE", output.read_bytes())
            self.assertIn("DanPort.exe".encode("utf-16-le"), output.read_bytes())
            self.assertEqual((output.parent / "Bridge.c").read_text(), 'getenv("DANPORT_EXE"); danport_display();')
            port.normalize(root, "OldPort")
            self.assertTrue(output.exists())

    def test_git_metadata_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            (root / ".git/config").write_text("OldPort")
            port.normalize(root, "OldPort")
            self.assertEqual((root / ".git/config").read_text(), "OldPort")

    def test_legal_wording_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('LICENSE.txt', 'NOTICE.txt', 'COPYING', 'THIRD-PARTY-NOTICES.md'):
                (root / name).write_text('Original OldPort copyright and license')
            port.normalize(root, 'OldPort')
            for name in ('LICENSE.txt', 'NOTICE.txt', 'COPYING', 'THIRD-PARTY-NOTICES.md'):
                self.assertEqual((root / name).read_text(), 'Original OldPort copyright and license')


if __name__ == "__main__":
    unittest.main()
