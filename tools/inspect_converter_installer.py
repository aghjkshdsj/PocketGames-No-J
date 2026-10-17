#!/usr/bin/env python3
"""Collect terms from a locally acquired, exact pinned Apple installer on macOS.

This reads an already-authorized download. It does not download, accept an
agreement, redistribute the proprietary payload or determine legal permission.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def collect(installer, output, download_record, runner=subprocess.run):
    pin = json.loads((ROOT / 'compliance/source-lock.json').read_text())['converter']
    if sha(installer) != pin['installer_sha256']:
        raise ValueError('Installer differs from pinned Metal Shader Converter ' + pin['version'])
    if output.exists():
        raise ValueError('Use a new evidence directory')
    output.mkdir(parents=True)
    evidence = {'version': pin['version'], 'installer_sha256': pin['installer_sha256'],
                'owner_supplied_download_record': download_record,
                'accompanying_online_terms': 'owner-review-required',
                'redistribution_permission': 'not-determined', 'files': []}
    with tempfile.TemporaryDirectory(prefix='pocketgames-converter-review-') as tmp:
        expanded = Path(tmp) / 'expanded'
        runner(['pkgutil', '--expand-full', str(installer.resolve()), str(expanded)], check=True)
        libraries = list(expanded.rglob('lib_iOS/libmetalirconverter.dylib'))
        if len(libraries) != 1 or sha(libraries[0]) != pin['unsigned_dylib_sha256']:
            raise ValueError('Expanded iOS converter does not match pinned binary')
        evidence['ios_payload_matches_pin'] = True
        for path in sorted(expanded.rglob('*')):
            if not path.is_file() or path.is_symlink():
                continue
            name = path.name.lower()
            if not (name in ('distribution', 'packageinfo') or
                    (('license' in name or 'agreement' in name or 'acknowledgement' in name)
                     and path.suffix.lower() in ('.txt', '.rtf', '.html', '.htm', '.pdf', '.xml', ''))):
                continue
            relative = path.relative_to(expanded)
            dest = output / 'package-terms' / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
            evidence['files'].append({'file': dest.relative_to(output).as_posix(), 'sha256': sha(dest)})
    evidence['bundled_agreement_found_in_package'] = any(
        f['sha256'] == pin['agreement_sha256'] for f in evidence['files'])
    (output / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print('Collected installer terms; separately accepted terms and permission still require review.')
    return evidence


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('installer', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--download-record', required=True,
                   help='Owner-provided source/date reference; never include passwords or cookies')
    args = p.parse_args()
    collect(args.installer, args.output, args.download_record)
