#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# The newest successful stage run for the exact validated runtime revision, on any branch.
#   tools/latest-run.sh <workflow file>    (GH_TOKEN, GITHUB_REPOSITORY, GITHUB_SHA set)
# verify_runtime_source.py first requires identical build inputs when reusing a revision;
# artifact_manifest.py then checks the downloaded payload's revision and stage identity.
set -euo pipefail
wf="${1:?workflow file}"
runtime_sha="${RUNTIME_SOURCE_SHA:-$GITHUB_SHA}"
if [[ ! "$runtime_sha" =~ ^[0-9a-f]{40}$ ]]; then
    echo "$wf: runtime revision must be a full commit SHA" >&2
    exit 1
fi
run=$(gh run list -R "$GITHUB_REPOSITORY" --workflow "$wf" --commit "$runtime_sha" --status success --limit 20 \
    --json databaseId,headSha --jq ".[] | select(.headSha == \"$runtime_sha\") | .databaseId" | head -1)
if [ -n "$run" ]; then
    echo "$wf: run $run (revision $runtime_sha)" >&2
    echo "$run"
    exit 0
fi
echo "$wf: no successful run for exact runtime revision $runtime_sha" >&2
exit 1
