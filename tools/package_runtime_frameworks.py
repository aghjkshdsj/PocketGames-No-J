#!/usr/bin/env python3
"""Package already-built native dylibs as iOS frameworks, before signing.

Only explicit candidate builds call this. PE data farms, prefix and saves are
untouched. An interrupted conversion is disposable build output, not an IPA.
"""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import re
import shutil
import subprocess

from audit_app_store import dylib
from audit_ipa_licenses import macho

PREFIXES = {'ec': 'PGEC_', 'a64': 'PGA64_', 'test': 'PGTest_'}
CONVERTER = 'PGShaderConverter'
ROOT = Path(__file__).resolve().parents[1]


def framework_name(group, module):
    if group not in PREFIXES or not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', module):
        raise ValueError('Unsafe framework module: ' + module)
    return PREFIXES[group] + re.sub(r'[.-]', '_', module.lower())


def plan(app):
    entries = []
    for relative, group in [('PE', 'test'), ('PE/wine', 'ec'), ('PE/wine-a64', 'a64')]:
        for path in sorted((app / relative).glob('lib*.dylib')):
            entries.append((path, framework_name(group, path.name[3:-6])))
    converter = app / 'd3d12/libmetalirconverter.dylib'
    if not converter.is_file():
        raise ValueError('Missing pinned shader converter')
    entries.append((converter, CONVERTER))
    seen = set()
    for path, name in entries:
        if path.is_symlink() or not path.is_file() or not dylib(path.read_bytes()):
            raise ValueError('Expected a real native dynamic library: ' + str(path))
        if name.lower() in seen or (app / 'Frameworks' / (name + '.framework')).exists():
            raise ValueError('Framework name collision: ' + name)
        seen.add(name.lower())
    for required in ('PGEC_ntdll_dll', 'PGA64_ntdll_dll', 'PGA64_xtajit_dll'):
        if required.lower() not in seen:
            raise ValueError('Incomplete runtime family: ' + required)
    return entries


def package(app, revision, runner=subprocess.run, converter_sha256=None):
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('Expected immutable application revision')
    manifest_path = app / 'RuntimeFrameworks.json'
    if manifest_path.exists():
        raise ValueError('Runtime frameworks already packaged; use a fresh build')
    entries = plan(app)  # validate every input and collision before modifying output
    if converter_sha256 is None:
        converter_sha256 = json.loads((ROOT / 'compliance/source-lock.json').read_text())['converter']['unsigned_dylib_sha256']
    converter = next(path for path, name in entries if name == CONVERTER)
    if hashlib.sha256(converter.read_bytes()).hexdigest() != converter_sha256:
        raise ValueError('Shader converter differs from pinned pristine iOS payload')
    app_info = plistlib.loads((app / 'Info.plist').read_bytes())
    manifest = {'schema': 1, 'layout': 'frameworks-v1', 'revision': revision, 'libraries': []}
    for source, name in entries:
        original = source.read_bytes()
        sections, _ = macho(original)
        if not sections:
            raise ValueError('Native library has no file-backed sections: ' + str(source))
        bundle = app / 'Frameworks' / (name + '.framework')
        bundle.mkdir(parents=True)
        executable = bundle / name
        shutil.copyfile(source, executable)
        executable.chmod(0o755)
        install_name = '@rpath/' + name + '.framework/' + name
        runner(['xcrun', 'install_name_tool', '-id', install_name, str(executable)], check=True)
        packaged_sections, _ = macho(executable.read_bytes())
        if packaged_sections != sections:
            raise ValueError('Packaging changed native section layout or payload: ' + name)
        identifier = 'com.pocketgamesnoj.runtime.' + name.lower().replace('_', '-')
        info = {
            'CFBundleExecutable': name, 'CFBundleIdentifier': identifier,
            'CFBundleName': name, 'CFBundlePackageType': 'FMWK',
            'CFBundleInfoDictionaryVersion': '6.0',
            'CFBundleShortVersionString': app_info['CFBundleShortVersionString'],
            'CFBundleVersion': app_info['CFBundleVersion'],
            'MinimumOSVersion': app_info['MinimumOSVersion'],
            'CFBundleSupportedPlatforms': ['iPhoneOS'],
            'UIDeviceFamily': [1, 2],
        }
        (bundle / 'Info.plist').write_bytes(plistlib.dumps(info, sort_keys=True))
        manifest['libraries'].append({
            'source': source.relative_to(app).as_posix(),
            'executable': executable.relative_to(app).as_posix(),
            'bundle_identifier': identifier, 'install_name': install_name,
            'original_sha256': hashlib.sha256(original).hexdigest(),
            'sections': sections,
        })
        source.unlink()  # no loose binary or legacy-path alias in the finished app
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('app', type=Path)
    p.add_argument('--revision', required=True)
    args = p.parse_args()
    result = package(args.app, args.revision)
    print('Packaged', len(result['libraries']), 'native libraries as frameworks; device testing pending')
