#!/usr/bin/env python3
"""Build-test evidence for a modified GnuTLS, never a legal-clearance certificate."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
LIBRARIES = ('libgmp.a', 'libnettle.a', 'libhogweed.a', 'libgnutls.a')


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def mark_source(original, marker):
    if not re.fullmatch(r'PocketGames-LGPL-relink-[0-9a-f]{40}', marker):
        raise ValueError('Unexpected witness marker')
    anchor = 'int gnutls_init(gnutls_session_t *session, unsigned int flags)\n{\n'
    include = '#include "gnutls_int.h"\n'
    if original.count(anchor) != 1 or original.count(include) != 1 or marker in original:
        raise ValueError('GnuTLS source differs from the expected pristine function')
    # A one-line diagnostic on session creation, with no credentials or changes
    # to TLS settings, validation, protocol selection or return values.
    return original.replace(include, include + '#include <stdio.h>\n').replace(anchor, anchor +
        '/* PocketGames validation only: record replacement-library use. */\n' +
        f'\tfprintf(stderr, "{marker}\\n");\n')


def save(out, value):
    (out / 'evidence.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def prepare(port, out, revision):
    if not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('A full application revision is required')
    if out.exists():
        raise ValueError('Use a new evidence directory; do not reuse a validation build')
    build = port / 'build/gnutls-ios'
    if (build / 'obj').exists() or (port / 'toolchains/gnutls-ios').exists():
        raise ValueError('Expected a clean dependency build directory')
    lock = json.loads((ROOT / 'compliance/source-lock.json').read_text(encoding='utf-8'))
    sources = [x for x in lock['embedded_archives'] if not x['name'].startswith('ffmpeg-')]
    for item in sources:
        if sha(build / 'src' / item['name']) != item['sha256']:
            raise ValueError('Source archive mismatch: ' + item['name'])
    out.mkdir(parents=True)
    for item in sources:
        shutil.copy2(build / 'src' / item['name'], out / item['name'])
    shutil.copy2(build / 'build.sh', out / 'dependency-build.sh')
    shutil.copy2(ROOT / 'compliance/source-lock.json', out / 'source-lock.json')
    obj = build / 'obj'
    obj.mkdir()
    with tarfile.open(build / 'src/gnutls-3.8.9.tar.xz') as archive:
        archive.extractall(obj, filter='data')
    source = obj / 'gnutls-3.8.9/lib/state.c'
    original = source.read_text(encoding='utf-8')
    marker = 'PocketGames-LGPL-relink-' + revision
    modified = mark_source(original, marker)
    source.write_text(modified, encoding='utf-8')
    shutil.copy2(source, out / 'modified-state.c')
    patch = ''.join(difflib.unified_diff(original.splitlines(True), modified.splitlines(True),
                                        'a/lib/state.c', 'b/lib/state.c'))
    (out / 'gnutls-witness.patch').write_text(patch, encoding='utf-8')
    save(out, {'application_revision': revision, 'marker': marker,
               'stage': 'prepared', 'archives': sources,
               'modified_source_sha256': sha(source),
               'complete_corresponding_source_verified': False,
               'device_installation_test': 'not-run', 'app_store_clearance': False})


def stage(port, out):
    data = json.loads((out / 'evidence.json').read_text(encoding='utf-8'))
    if data['stage'] != 'prepared':
        raise ValueError('Replacement libraries have already been staged')
    libs = port / 'toolchains/gnutls-ios/lib'
    target = ROOT / 'engine/wine/out'
    # The normal runtime manifests must have been verified by the workflow
    # before these test-only replacements. Preserve both hashes for comparison.
    hashes = {}
    for name in LIBRARIES:
        replacement = libs / name
        if not replacement.is_file() or not replacement.stat().st_size:
            raise ValueError('Replacement library missing: ' + name)
        if name == 'libgnutls.a' and data['marker'].encode() not in replacement.read_bytes():
            raise ValueError('Replacement GnuTLS archive lacks the witness')
        hashes[name] = {'original_runtime_sha256': sha(target / name),
                        'modified_build_sha256': sha(replacement)}
    for name in LIBRARIES:
        shutil.copy2(libs / name, target / name)
        shutil.copy2(libs / name, out / name)
    # Configure logs, headers and recipes accompany the original archives/patch.
    obj = port / 'build/gnutls-ios/obj'
    for path in obj.rglob('*'):
        if path.is_file() and (path.name in ('config.h', 'config.log', 'config.status') or
                               (path.parent == obj and path.suffix == '.log')):
            dest = out / 'configuration' / path.relative_to(obj)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
    data.update(stage='libraries-staged', replacement_libraries=hashes)
    save(out, data)


def verify(app, out):
    data = json.loads((out / 'evidence.json').read_text(encoding='utf-8'))
    if data['stage'] != 'libraries-staged':
        raise ValueError('Expected staged replacement libraries')
    executable = app / 'PocketGamesNoJ'
    if data['marker'].encode() not in executable.read_bytes():
        raise ValueError('Modified GnuTLS witness absent from the linked application')
    source = json.loads((app / 'Legal/build-info.json').read_text(encoding='utf-8'))
    if source['revision'] != data['application_revision']:
        raise ValueError('Application revision mismatch')
    (out / 'application-source.tar').write_bytes(subprocess.check_output(
        ['git', 'archive', data['application_revision']], cwd=ROOT))
    # Preserve app objects/link lists without copying SDKs, signing keys or the
    # proprietary converter. This supplements, and does not replace, the full
    # source reconstruction still required for the shipped runtime farms.
    intermediate = ROOT / 'build/dd/Build/Intermediates.noindex'
    with tarfile.open(out / 'application-link-materials.tar.gz', 'w:gz') as archive:
        for path in sorted(intermediate.rglob('*')):
            if path.is_file() and path.suffix in ('.o', '.LinkFileList', '.resp'):
                archive.add(path, arcname=path.relative_to(intermediate), recursive=False)
    data.update(stage='modified-library-linked-in-complete-app', executable_sha256=sha(executable))
    data['evidence_files'] = {p.relative_to(out).as_posix(): sha(p) for p in sorted(out.rglob('*'))
                              if p.is_file() and p.name != 'evidence.json'}
    save(out, data)
    print('Modified GnuTLS witness verified in the complete app; device test remains pending.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('prepare', 'stage', 'verify'))
    p.add_argument('--port', type=Path, default=ROOT / 'engine/wine/danport')
    p.add_argument('--output', type=Path, default=ROOT / 'build/lgpl-validation')
    p.add_argument('--revision')
    p.add_argument('--app', type=Path)
    args = p.parse_args()
    if args.action == 'prepare':
        prepare(args.port, args.output, args.revision or '')
    elif args.action == 'stage':
        stage(args.port, args.output)
    else:
        verify(args.app, args.output)


if __name__ == '__main__':
    main()
