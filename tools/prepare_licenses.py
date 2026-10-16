#!/usr/bin/env python3
"""Synchronize the offline legal bundle, record source revision, or verify a built app."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LEGAL = Path('App/Resources/Legal')
COPIES = {
    'PocketGames-GPL-3.0.txt': 'LICENSE',
    'PocketGames-Exception.txt': 'LICENSE-EXCEPTION.md',
    'Port-Exception.txt': 'LICENSES/DanPort-LICENSE-EXCEPTION.md',
    'Third-Party-Notices.txt': 'THIRD-PARTY-NOTICES.md',
}
REPOSITORY = 'https://github.com/aghjkshdsj/PocketGames-No-J'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate(folder, expected=None):
    index = json.loads((folder / 'index.json').read_text(encoding='utf-8'))
    docs = index['documents']
    assert docs and len({d['id'] for d in docs}) == len(docs), 'Missing or duplicate license entries'
    assert len({d['file'] for d in docs}) == len(docs), 'Duplicate license files'
    if expected is not None:
        assert index == expected, 'Built license index differs from reviewed source'
    for doc in docs:
        name = doc['file']
        assert Path(name).name == name and '/' not in name and '\\' not in name, 'Invalid license path'
        data = (folder / name).read_bytes()
        assert data.strip() and digest(data) == doc['sha256'], f'Missing or changed legal notice: {name}'
        data.decode('utf-8')
    assert set(COPIES).issubset(d['file'] for d in docs), 'Missing project license notices'
    return index


def prepare(root=ROOT, check=False):
    folder = root / LEGAL
    index = json.loads((folder / 'index.json').read_text(encoding='utf-8'))
    for doc in index['documents']:
        if doc['file'] in COPIES:
            original = (root / COPIES[doc['file']]).read_bytes()
            target = folder / doc['file']
            if check:
                assert target.read_bytes() == original, f'Stale legal copy: {target.name}'
            else:
                target.write_bytes(original)
                doc['sha256'] = digest(original)
    if not check:
        (folder / 'index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        revision = os.environ.get('GITHUB_SHA') or subprocess.check_output(
            ['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
        assert re.fullmatch('[0-9a-f]{40}', revision), 'Invalid source revision'
        (folder / 'build-info.json').write_text(json.dumps({
            'revision': revision, 'sourceURL': f'{REPOSITORY}/tree/{revision}',
        }, indent=2) + '\n', encoding='utf-8')
    validate(folder)


def validate_app(app, root=ROOT):
    expected = validate(root / LEGAL)
    validate(app / 'Legal', expected)
    info = json.loads((app / 'Legal/build-info.json').read_text(encoding='utf-8'))
    assert re.fullmatch('[0-9a-f]{40}', info['revision']), 'Invalid bundled source revision'
    assert info['sourceURL'] == f'{REPOSITORY}/tree/{info["revision"]}', 'Incorrect corresponding-source link'
    if os.environ.get('GITHUB_SHA'):
        assert info['revision'] == os.environ['GITHUB_SHA'], 'Source revision does not match build'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--app', type=Path)
    args = parser.parse_args()
    if args.app:
        validate_app(args.app)
    else:
        prepare(check=args.check)
    print('Verified bundled license texts, notices and source information')
