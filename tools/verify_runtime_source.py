#!/usr/bin/env python3
"""Reuse a runtime revision only when all runtime build inputs are identical."""
import os
import re
import subprocess

revision = os.environ.get('RUNTIME_SOURCE_SHA') or os.environ['GITHUB_SHA']
assert re.fullmatch('[0-9a-f]{40}', revision), 'Runtime revision must be a full commit SHA'
if revision != os.environ['GITHUB_SHA']:
    subprocess.run(['git', 'fetch', '--depth=1', 'origin', revision], check=True)
    paths = ['engine', 'tools/port_source.py', 'tools/artifact_manifest.py', '.gitattributes']
    paths += [f'.github/workflows/{name}.yml' for name in ('wine-unix', 'wine-i386', 'dxmt', 'dxmt-pe')]
    changes = subprocess.check_output(['git', 'diff', '--name-only', revision, os.environ['GITHUB_SHA'], '--', *paths], text=True)
    assert not changes.strip(), 'Runtime source/build inputs changed; rebuild runtimes:\n' + changes
print('Verified runtime build inputs for ' + revision)
