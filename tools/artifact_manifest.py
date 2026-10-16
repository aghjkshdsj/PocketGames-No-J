#!/usr/bin/env python3
"""Require runtime artifacts to come from the source revision being packaged."""
import argparse
import json
import os
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("command", choices=("write", "check"))
parser.add_argument("directory", type=Path)
parser.add_argument("kind")
args = parser.parse_args()
sha = os.environ["GITHUB_SHA"]
manifest = args.directory / "build-manifest.json"
if args.command == "write":
    args.directory.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"source_sha": sha, "kind": args.kind}, indent=2) + "\n")
else:
    data = json.loads(manifest.read_text())
    assert data == {"source_sha": sha, "kind": args.kind}, f"Runtime artifact revision mismatch: {manifest}"
    print(f"Verified {args.kind} artifact for {sha}")
