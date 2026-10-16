#!/usr/bin/env python3
"""Wait for the separately dispatched runtime builds of this exact source revision."""
import json
import os
import subprocess
import time

workflows = ['wine-unix.yml', 'wine-i386.yml', 'dxmt.yml', 'dxmt-pe.yml']
repository = os.environ['GITHUB_REPOSITORY']
revision = os.environ['GITHUB_SHA']
deadline = time.monotonic() + 85 * 60
pending = set(workflows)
while pending:
    for workflow in sorted(pending):
        result = subprocess.check_output(['gh', 'api',
            f'repos/{repository}/actions/workflows/{workflow}/runs?per_page=20'], text=True)
        runs = [r for r in json.loads(result)['workflow_runs'] if r['head_sha'] == revision]
        if not runs:
            continue
        run = runs[0]
        if run['status'] != 'completed':
            continue
        if run['conclusion'] != 'success':
            raise SystemExit(f'{workflow} failed: {run["html_url"]} ({run["conclusion"]})')
        print(f'{workflow} succeeded: {run["html_url"]}', flush=True)
        pending.remove(workflow)
    if pending:
        if time.monotonic() >= deadline:
            raise SystemExit('Timed out waiting for runtime builds: ' + ', '.join(sorted(pending)))
        print('Waiting for: ' + ', '.join(sorted(pending)), flush=True)
        time.sleep(30)
