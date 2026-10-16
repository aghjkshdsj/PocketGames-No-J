#!/usr/bin/env python3
"""Collect pinned source for a release; rebuild/relink validation remains separate."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import subprocess
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BINARY_SUFFIXES = ('.dylib', '.dll', '.exe', '.a', '.o', '.so', '.pkg', '.dmg',
                   '.msi', '.metallib', '.ipa', '.zip', '.7z', '.xip', '.bin')


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def safe_name(name):
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and '..' not in path.parts and '\\' not in name and ':' not in name


def filter_port(source, dest, embedded):
    """Retain pristine source, notices and the four checked source tarballs.

    Do not redistribute Apple's proprietary converter or prebuilt guest farms
    as part of this source preparation kit. Never extract upstream members.
    """
    expected = {x['name']: x['sha256'] for x in embedded}
    verified, excluded = {}, []
    with tarfile.open(source, 'r:gz') as src, tarfile.open(dest, 'w:gz') as out:
        for item in src:
            if not safe_name(item.name):
                raise ValueError('Unsafe source archive path')
            if item.issym() or item.islnk():
                target = posixpath.normpath(posixpath.join(posixpath.dirname(item.name), item.linkname)
                                            if item.issym() else item.linkname)
                if (not safe_name(target) or PurePosixPath(target).parts[0] != PurePosixPath(item.name).parts[0]
                        or item.linkname.startswith('/') or '\\' in item.linkname or ':' in item.linkname):
                    raise ValueError('Source archive link requires review: ' + item.name)
            if not (item.isfile() or item.isdir() or item.issym() or item.islnk()):
                raise ValueError('Unexpected special source archive entry')
            name = PurePosixPath(item.name).name
            if item.isfile() and name in expected:
                data = src.extractfile(item).read()
                digest = hashlib.sha256(data).hexdigest()
                if digest != expected[name]:
                    raise ValueError('Embedded source archive changed: ' + name)
                verified[name] = digest
            elif item.isfile() and (item.name.lower().endswith(BINARY_SUFFIXES) or
                    name == 'prefix-template.tar.gz' or name.endswith(('.tar.gz', '.tar.xz', '.tar.bz2'))):
                excluded.append(item.name)
                continue
            out.addfile(item, src.extractfile(item) if item.isfile() else None)
    if verified != expected:
        raise ValueError('Missing embedded LGPL source archives')
    return {'excluded_prebuilt_files': excluded, 'embedded_source_sha256': verified}


def download(url, path):
    if path.exists():
        return
    request = urllib.request.Request(url, headers={'User-Agent': 'PocketGames-source-kit'})
    partial = path.with_suffix(path.suffix + '.part')
    with urllib.request.urlopen(request, timeout=60) as response, partial.open('wb') as out:
        shutil.copyfileobj(response, out)
    partial.replace(path)


def verify(folder):
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        if not safe_name(entry['file']) or len(PurePosixPath(entry['file']).parts) != 1:
            raise ValueError('Unsafe kit file path')
        path = folder / entry['file']
        if path.is_symlink() or not path.is_file() or not path.stat().st_size or sha(path) != entry['sha256']:
            raise ValueError('Missing or changed kit material: ' + entry['file'])
    return manifest


def collect(revision, output, cache):
    if not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('Use the exact full application revision')
    subprocess.run(['git', '-C', str(ROOT), 'cat-file', '-e', revision + '^{commit}'], check=True)
    lock = json.loads((ROOT / 'compliance/source-lock.json').read_text(encoding='utf-8'))
    revisions = {x['id']: x['revision'] for x in lock['sources']}
    for filename, variables in (
        ('engine/wine/PIN', {'DANPORT_SHA': 'port', 'WINE_SHA': 'wine'}),
        ('engine/dxmt/PIN', {'DXMT_SHA': 'dxmt'}),
        ('engine/blink/PIN', {'SHA': 'blink'}),
        ('engine/pedylib/build-spike.sh', {'DOCK_SHA': 'dock'}),
    ):
        text = subprocess.check_output(['git', '-C', str(ROOT), 'show', revision + ':' + filename], text=True)
        for variable, identity in variables.items():
            if not re.search(r'^' + variable + '=' + re.escape(revisions[identity]) + r'\s*$', text, re.M):
                raise ValueError('Source lock differs from requested application pin: ' + identity)
    output.mkdir(parents=True, exist_ok=False)
    cache.mkdir(parents=True, exist_ok=True)
    manifest = {'schema': 1, 'application_revision': revision, 'files': [], 'sources': [],
                'source_collection_complete': False, 'modified_library_app_relink_test': 'not-run',
                'prebuilt_guest_source_equivalence': 'not-verified', 'app_store_licensing_clearance': False}
    def record(path):
        manifest['files'].append({'file': path.name, 'sha256': sha(path), 'bytes': path.stat().st_size})
    def save():
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    app = output / 'application-source.tar'
    with app.open('wb') as out:
        subprocess.run(['git', '-C', str(ROOT), 'archive', '--format=tar', revision], stdout=out, check=True)
    record(app)
    for relative in ('compliance/source-lock.json', 'docs/LGPL_REBUILD.md', 'tools/collect_source_kit.py'):
        target = output / Path(relative).name
        shutil.copyfile(ROOT / relative, target)
        record(target)
    save()
    for component in lock['sources']:
        identity, commit, repo = component['id'], component['revision'], component['repository']
        if not re.fullmatch('[a-z0-9-]+', identity) or not re.fullmatch('[0-9a-f]{40}', commit) or not repo.startswith('https://api.github.com/'):
            raise ValueError('Invalid dependency source lock')
        url = repo + '/tarball/' + commit
        cached = cache / (identity + '-' + commit + '.tar.gz')
        print('Collecting', identity, commit, flush=True)
        download(url, cached)
        dest = output / (identity + '-source.tar.gz')
        entry = {'id': identity, 'revision': commit, 'url': url, 'download_sha256': sha(cached)}
        if component.get('filter_binaries'):
            entry.update(filter_port(cached, dest, lock['embedded_archives']))
        else:
            # Retain original archive bytes and original license texts.
            with tarfile.open(cached, 'r:gz') as archive:
                if not archive.next():
                    raise ValueError('Empty dependency source archive')
            shutil.copyfile(cached, dest)
        record(dest)
        manifest['sources'].append(entry)
        save()
    manifest['source_collection_complete'] = True
    save()
    verify(output)
    print('Pinned source collection verified. Full app relink/install test remains pending.', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--revision')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--cache', type=Path)
    p.add_argument('--verify', action='store_true')
    args = p.parse_args()
    if args.verify:
        result = verify(args.output)
        print('Kit file hashes verified; relink test:', result['modified_library_app_relink_test'])
    else:
        if not args.revision or not args.cache:
            p.error('--revision and --cache are required for collection')
        collect(args.revision, args.output, args.cache)
