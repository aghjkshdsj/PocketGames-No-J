"""Framework migration must preserve code/data and keep architecture families distinct."""
import hashlib
from pathlib import Path
import plistlib
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import package_runtime_frameworks as package
import runtime_framework_audit as audit


def binary(identity='@rpath/old.dylib', kind=6, platform=2, payload=b'CODE'):
    string = identity.encode() + b'\0'
    command = struct.pack('<IIIIII', 0xd, 256, 24, 0, 0x10000, 0x10000) + string
    command += b'\0' * (256 - len(command))
    version = struct.pack('<IIIIII', 0x32, 24, platform, 0x110000, 0x1a0000, 0)
    offset = 32 + 256 + 24 + 152
    segment = struct.pack('<II16sQQQQIIII', 0x19, 152, b'__TEXT', 0, 4096, 0, offset + 4, 5, 5, 1, 0)
    section = struct.pack('<16s16sQQIIIIIIII', b'__text', b'__TEXT', 4096, 4, offset, 2, 0, 0, 0, 0, 0, 0)
    return struct.pack('<IIIIIIII', 0xfeedfacf, 0x100000c, 0, kind, 3, 432, 0, 0) + command + version + segment + section + payload


def rename_fixture(command, check):
    assert check and command[:3] == ['xcrun', 'install_name_tool', '-id']
    path = Path(command[-1])
    data = bytearray(path.read_bytes())
    identity = command[3].encode() + b'\0'
    data[56:288] = identity.ljust(232, b'\0')
    path.write_bytes(data)


class RuntimeFrameworkTests(unittest.TestCase):
    def package(self, app):
        return package.package(app, 'a' * 40, runner=rename_fixture,
                               converter_sha256=hashlib.sha256(binary()).hexdigest())

    def fixture(self, app):
        (app / 'Info.plist').write_bytes(plistlib.dumps({
            'CFBundleShortVersionString': '0.1.0', 'CFBundleVersion': '16', 'MinimumOSVersion': '17.0'}))
        (app / 'PocketGamesNoJ').write_bytes(binary(kind=2))
        for name in ('PE/wine/libntdll.dll.dylib', 'PE/wine-a64/libntdll.dll.dylib',
                     'PE/wine-a64/libxtajit.dll.dylib', 'PE/libspike-arm64ec.dylib',
                     'd3d12/libmetalirconverter.dylib'):
            path = app / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(binary())
        (app / 'PE/wine/xtajit64.dll').write_bytes(b'PE resource must stay put')

    def test_architecture_names_and_unsafe_modules(self):
        self.assertEqual(package.framework_name('ec', 'ntdll.dll'), 'PGEC_ntdll_dll')
        self.assertEqual(package.framework_name('a64', 'ntdll.dll'), 'PGA64_ntdll_dll')
        self.assertEqual(package.framework_name('test', 'Spike-ARM64EC'), 'PGTest_spike_arm64ec')
        for module in ('', '../ntdll', 'a\\b', 'a:b', '\u00e9.dll', 'a' * 101):
            with self.assertRaises(ValueError):
                package.framework_name('ec', module)

    def test_complete_conversion_preserves_sections_data_and_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = Path(tmp)
            self.fixture(app)
            result = self.package(app)
            files = {p.relative_to(app).as_posix() for p in app.rglob('*') if p.is_file()}
            self.assertEqual(len(result['libraries']), 5)
            self.assertEqual(audit.validate(files, lambda p: (app / p).read_bytes(), 'a' * 40), 5)
            self.assertEqual((app / 'PE/wine/xtajit64.dll').read_bytes(), b'PE resource must stay put')
            self.assertFalse(list(app.rglob('*.dylib')))
            with self.assertRaises(ValueError):
                self.package(app)
            target = app / result['libraries'][0]['executable']
            target.write_bytes(target.read_bytes()[:-1] + b'X')
            with self.assertRaisesRegex(ValueError, 'payload changed'):
                audit.validate(files, lambda p: (app / p).read_bytes())

    def test_collisions_rejected_before_removing_any_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = Path(tmp)
            self.fixture(app)
            for name in ('a-b', 'a_b'):
                (app / ('PE/wine/lib' + name + '.dylib')).write_bytes(binary())
            with self.assertRaisesRegex(ValueError, 'collision'):
                self.package(app)
            self.assertEqual(len(list(app.rglob('*.dylib'))), 7)
            self.assertFalse((app / 'RuntimeFrameworks.json').exists())

    def test_reject_changed_code_and_wrong_platform_identity_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = Path(tmp)
            self.fixture(app)
            result = self.package(app)
            files = {p.relative_to(app).as_posix() for p in app.rglob('*') if p.is_file()}
            read = lambda p: (app / p).read_bytes()
            target = app / result['libraries'][0]['executable']
            original = target.read_bytes()
            target.write_bytes(binary(result['libraries'][0]['install_name'], platform=7))
            with self.assertRaisesRegex(ValueError, 'not built for iOS'):
                audit.validate(files, read)
            target.write_bytes(binary('@rpath/wrong.dylib'))
            with self.assertRaisesRegex(ValueError, 'identity'):
                audit.validate(files, read)
            target.write_bytes(original)
            info_path = target.parent / 'Info.plist'
            info = plistlib.loads(info_path.read_bytes())
            info['CFBundleExecutable'] = 'wrong'
            info_path.write_bytes(plistlib.dumps(info))
            with self.assertRaisesRegex(ValueError, 'metadata'):
                audit.validate(files, read)

    def test_parser_rejects_malformed_load_commands(self):
        for data in (b'bad', binary()[:100], binary()[:36] + b'\0' * 4 + binary()[40:]):
            with self.assertRaises(ValueError):
                audit.linkage(data)

    def test_converter_pin_mismatch_rejected_before_moving_libraries(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = Path(tmp)
            self.fixture(app)
            with self.assertRaisesRegex(ValueError, 'pinned pristine'):
                package.package(app, 'a' * 40, runner=rename_fixture, converter_sha256='0' * 64)
            self.assertEqual(len(list(app.rglob('*.dylib'))), 5)
            self.assertFalse((app / 'RuntimeFrameworks.json').exists())


if __name__ == '__main__':
    unittest.main()
