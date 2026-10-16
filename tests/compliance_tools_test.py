"""Read-only binary auditing and source-kit integrity checks."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
audit = module('audit_ipa_licenses')
kit = module('collect_source_kit')


class ComplianceTests(unittest.TestCase):
    def test_defined_macho_symbols_exclude_undefined_imports(self):
        strings = b'\0_ff_j_rev_dct\0_undefined\0'
        commands = struct.pack('<IIIIII', 2, 24, 56, 2, 88, len(strings))
        header = struct.pack('<IIIIIIII', 0xfeedfacf, 0x100000c, 0, 2, 1, len(commands), 0, 0)
        symbols = struct.pack('<IBBHQ', 1, 0x0f, 1, 0, 4096)
        symbols += struct.pack('<IBBHQ', 15, 1, 0, 0, 0)
        _, names = audit.macho(header + commands + symbols + strings)
        self.assertEqual(names, ['_ff_j_rev_dct'])
        with self.assertRaises(ValueError):
            audit.macho(header + commands)
        with self.assertRaises(ValueError):
            audit.macho(b'not a binary')

    def test_sections_detect_payload_changes(self):
        header = struct.pack('<IIIIIIII', 0xfeedfacf, 0x100000c, 0, 2, 1, 152, 0, 0)
        command = struct.pack('<II16sQQQQIIII', 0x19, 152, b'__TEXT', 0, 4096, 0, 188, 5, 5, 1, 0)
        section = struct.pack('<16s16sQQIIIIIIII', b'__text', b'__TEXT', 4096, 4, 184, 2, 0, 0, 0, 0, 0, 0)
        a, _ = audit.macho(header + command + section + b'abcd')
        b, _ = audit.macho(header + command + section + b'abce')
        self.assertNotEqual(a, b)

    def test_port_filter_retains_notices_and_exact_sources_omits_binaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = root / 'original.tar.gz'
            source = b'exact release archive'
            expected = [{'name': 'library.tar.xz', 'sha256': hashlib.sha256(source).hexdigest()}]
            with tarfile.open(original, 'w:gz') as archive:
                for name, data in [('source/LICENSE', b'Original copyright and permission'),
                                   ('source/lib.dylib', b'proprietary binary'),
                                   ('source/guest.dll', b'prebuilt guest'),
                                   ('source/library.tar.xz', source)]:
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    archive.addfile(info, io.BytesIO(data))
            result = kit.filter_port(original, root / 'filtered.tar.gz', expected)
            with tarfile.open(root / 'filtered.tar.gz') as archive:
                self.assertEqual(set(archive.getnames()), {'source/LICENSE', 'source/library.tar.xz'})
                self.assertEqual(archive.extractfile('source/LICENSE').read(), b'Original copyright and permission')
            self.assertEqual(len(result['excluded_prebuilt_files']), 2)
            with self.assertRaises(ValueError):
                kit.filter_port(original, root / 'bad.tar.gz', [{'name': 'library.tar.xz', 'sha256': '0' * 64}])

    def test_kit_rejects_missing_tampered_and_escaping_materials(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'source.tar'
            path.write_bytes(b'original source')
            manifest = {'files': [{'file': path.name, 'sha256': kit.sha(path)}]}
            (root / 'manifest.json').write_text(json.dumps(manifest))
            kit.verify(root)
            path.write_bytes(b'tampered')
            with self.assertRaises(ValueError):
                kit.verify(root)
            path.unlink()
            with self.assertRaises(ValueError):
                kit.verify(root)
            manifest['files'][0]['file'] = '../outside'
            (root / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                kit.verify(root)


if __name__ == '__main__':
    unittest.main()
