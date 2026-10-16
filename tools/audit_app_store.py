#!/usr/bin/env python3
"""Read-only structural checks; passing is not an App Store approval assessment."""
import argparse
import json
from pathlib import Path, PurePosixPath
import plistlib
import struct
import zipfile

PREFIX = 'Payload/PocketGamesNoJ.app/'


def dylib(data):
    if len(data) < 16:
        return False
    if data[:4] in (b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe'):
        return struct.unpack_from('<I', data, 12)[0] == 6  # MH_DYLIB
    if data[:4] in (b'\xfe\xed\xfa\xcf', b'\xfe\xed\xfa\xce'):
        return struct.unpack_from('>I', data, 12)[0] == 6
    if data[:4] == b'\xca\xfe\xba\xbe':  # fat Mach-O, 32-bit architecture table
        count = struct.unpack_from('>I', data, 4)[0]
        if count > 64 or 8 + count * 20 > len(data):
            raise ValueError('Invalid fat Mach-O architecture table')
        for i in range(count):
            offset, size = struct.unpack_from('>II', data, 8 + i * 20 + 8)
            if offset + size > len(data) or offset < 8 + count * 20:
                raise ValueError('Invalid fat Mach-O slice')
            if dylib(data[offset:offset + size]):
                return True
    return False


def audit(files, read):
    files = set(files)
    blockers, loose, frameworks = [], [], []
    for name in sorted(files):
        data = read(name)
        if not dylib(data):
            continue
        parts = PurePosixPath(name).parts
        if len(parts) != 3 or parts[0] != 'Frameworks' or not parts[1].endswith('.framework'):
            loose.append(name)
            continue
        stem = parts[1][:-len('.framework')]
        info_path = '/'.join(parts[:2]) + '/Info.plist'
        info = plistlib.loads(read(info_path)) if info_path in files else {}
        if parts[2] != stem or info.get('CFBundleExecutable') != stem or info.get('CFBundlePackageType') != 'FMWK':
            blockers.append('Invalid framework metadata or executable name: ' + name)
        frameworks.append(name)
    if loose:
        blockers.append(f'{len(loose)} standalone dynamic libraries require framework packaging')
    manifest = None
    if 'PrivacyInfo.xcprivacy' not in files:
        blockers.append('PrivacyInfo.xcprivacy is missing from the application root')
    else:
        manifest = plistlib.loads(read('PrivacyInfo.xcprivacy'))
        if not isinstance(manifest, dict) or not isinstance(manifest.get('NSPrivacyTracking'), bool):
            blockers.append('Privacy manifest has no valid tracking declaration')
    if 'PrivacyPolicy.txt' not in files or not read('PrivacyPolicy.txt').strip():
        blockers.append('Offline privacy policy is missing or empty')
    if 'PocketGamesNoJ' not in files:
        blockers.append('Application executable is missing')
    elif b'setDisplaySyncEnabled:' in read('PocketGamesNoJ'):
        blockers.append('Known non-iOS-public displaySyncEnabled selector remains in the executable')
    return {'structural_blockers': blockers, 'standalone_dynamic_libraries': loose,
            'framework_executables': frameworks,
            'privacy_collection_declaration': 'present-needs-review' if isinstance(manifest, dict) and
                'NSPrivacyCollectedDataTypes' in manifest else 'pending-data-flow-review',
            'app_store_clearance': False,
            'limitations': ['No code-signing, provisioning or entitlement authorization validation',
                           'No complete private-API or required-reason-API scan',
                           'No runtime, licensing, Steam authorization or content-policy clearance']}


def audit_ipa(path):
    with zipfile.ZipFile(path) as z:
        if len(z.namelist()) != len(set(z.namelist())) or z.testzip() is not None:
            raise ValueError('Duplicate ZIP paths or corrupt IPA')
        files = [n[len(PREFIX):] for n in z.namelist() if n.startswith(PREFIX) and not n.endswith('/')]
        return audit(files, lambda n: z.read(PREFIX + n))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument('--ipa', type=Path)
    source.add_argument('--app', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--require-structural-pass', action='store_true')
    args = p.parse_args()
    if args.ipa:
        result = audit_ipa(args.ipa)
    else:
        files = [p.relative_to(args.app).as_posix() for p in args.app.rglob('*') if p.is_file()]
        result = audit(files, lambda n: (args.app / n).read_bytes())
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('App Store structural blockers:', len(result['structural_blockers']))
    if args.require_structural_pass and result['structural_blockers']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
