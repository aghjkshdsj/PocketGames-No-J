"""Regression tests for packaging detection and the LGPL replacement witness."""
import importlib.util
from pathlib import Path
import plistlib
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


audit = module('audit_app_store')
lgpl = module('lgpl_relink_validation')


class AppStoreTests(unittest.TestCase):
    def test_native_library_detection_is_not_based_on_filename(self):
        image = struct.pack('<IIIIIIII', 0xfeedfacf, 0x100000c, 0, 6, 0, 0, 0, 0)
        files = {'PE/renamed-module': image, 'PE/readme.dylib': b'plain text',
                 'PocketGamesNoJ': b'setDisplaySyncEnabled:'}
        result = audit.audit(files, files.__getitem__)
        self.assertEqual(result['standalone_dynamic_libraries'], ['PE/renamed-module'])
        self.assertEqual(len(result['structural_blockers']), 4)
        self.assertFalse(result['app_store_clearance'])
        # A framework suffix alone must not hide malformed bundle metadata.
        files = {'Frameworks/Test.framework/Test': image,
                 'Frameworks/Test.framework/Info.plist': plistlib.dumps({'CFBundlePackageType': 'APPL'})}
        result = audit.audit(files, files.__getitem__)
        self.assertTrue(any('Invalid framework' in x for x in result['structural_blockers']))
        files['Frameworks/Test.framework/Info.plist'] = plistlib.dumps({
            'CFBundlePackageType': 'FMWK', 'CFBundleExecutable': 'Test'})
        self.assertFalse(any('framework' in x for x in audit.audit(files, files.__getitem__)['structural_blockers']))

    def test_witness_preserves_original_function_and_rejects_unexpected_source(self):
        original = ('/* original copyright */\n#include "gnutls_int.h"\n'
                    'int gnutls_init(gnutls_session_t *session, unsigned int flags)\n{\n'
                    '\treturn original_validation(session, flags);\n}\n')
        marker = 'PocketGames-LGPL-relink-' + '1' * 40
        modified = lgpl.mark_source(original, marker)
        self.assertIn('fprintf(stderr, "' + marker + '\\n");', modified)
        self.assertIn('return original_validation(session, flags);', modified)
        self.assertLess(modified.index('gnutls_int.h'), modified.index('<stdio.h>'))
        self.assertTrue(modified.startswith('/* original copyright */'))
        with self.assertRaises(ValueError):
            lgpl.mark_source(modified, marker)
        with self.assertRaises(ValueError):
            lgpl.mark_source(original.replace('unsigned int flags', 'unsigned flags'), marker)
        with self.assertRaises(ValueError):
            lgpl.mark_source(original, 'untrusted"; code();')


if __name__ == '__main__':
    unittest.main()
