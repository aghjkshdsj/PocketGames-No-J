#!/usr/bin/env python3
"""Fetch pinned source by repository ID and apply the DanPort namespace consistently."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request

PORT_ID = 1175417517
DOCK_ID = 1393407380


def request(url, raw=False):
    headers = {"User-Agent": "PocketGames-No-J", "Accept": "application/vnd.github.raw+json" if raw else "application/vnd.github+json"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
        return response.read()


def metadata(repo_id):
    return json.loads(request(f"https://api.github.com/repositories/{repo_id}"))


def namespace(text, original):
    def replace(match):
        value = match.group()
        return "DANPORT" if value.isupper() else "danport" if value.islower() else "DanPort"
    return re.sub(re.escape(original), replace, text, flags=re.I)


def normalize(root, original):
    """Keep byte lengths intact in PE resources, imports and UTF-16 strings."""
    assert len(original) == len("DanPort"), "Review the pinned dependency namespace length"
    pattern = re.compile(re.escape(original.encode()), re.I)

    def replace(match):
        value = match.group()
        return b"DANPORT" if value.isupper() else b"danport" if value.islower() else b"DanPort"

    files = []
    excluded = {".git", "toolchains", "obj", "obj-wineserver", "out", "out-pe"}
    for base, directories, names in os.walk(root):
        directories[:] = [name for name in directories if name not in excluded]
        for name in names:
            path = Path(base) / name
            if name in (".git", ".gitmodules") or path.is_symlink() or name.upper().startswith(("LICENSE", "COPYING", "NOTICE", "THIRD-PARTY-NOTICES", "METAL-SHADER-CONVERTER-AGREEMENT")):
                continue
            files.append(path)
    for path in files:
        data = path.read_bytes()
        updated = pattern.sub(replace, data)
        for encoding in ("utf-16-le", "utf-16-be"):
            for old, new in ((original, "DanPort"), (original.lower(), "danport"), (original.upper(), "DANPORT")):
                updated = updated.replace(old.encode(encoding), new.encode(encoding))
        if updated != data:
            path.write_bytes(updated)
    # Rename from the leaves up so parent paths stay valid during the walk.
    paths = []
    for base, directories, names in os.walk(root):
        directories[:] = [name for name in directories if name not in excluded]
        paths.extend(Path(base) / name for name in directories + names if name != ".git")
    for path in sorted(paths, key=lambda item: len(item.parts), reverse=True):
        if path.is_symlink():
            before = os.readlink(path)
            after = namespace(before, original)
            if after != before:
                is_directory = path.is_dir()
                path.unlink()
                path.symlink_to(after, target_is_directory=is_directory)
        name = namespace(path.name, original)
        if name != path.name:
            target = path.with_name(name)
            if target.exists():
                raise RuntimeError(f"Namespace destination already exists: {target}")
            path.rename(target)


def checkout(path, repo_id, ref):
    if not (path / ".git").exists():
        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", str(path)], check=True)
        subprocess.run(["git", "-C", str(path), "remote", "add", "origin", metadata(repo_id)["clone_url"]], check=True)
    head = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True)
    if head.returncode or head.stdout.strip() != ref:
        subprocess.run(["git", "-C", str(path), "fetch", "-q", "--depth", "1", "origin", ref], check=True)
        subprocess.run(["git", "-C", str(path), "checkout", "-q", "FETCH_HEAD"], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("checkout", "normalize", "file"))
    parser.add_argument("path")
    parser.add_argument("--repository-id", type=int, default=PORT_ID)
    parser.add_argument("--ref")
    parser.add_argument("--source-path")
    args = parser.parse_args()
    path = Path(args.path)
    if args.command == "file":
        # The source folder name follows the pinned port; it is normalized locally afterwards.
        name = metadata(PORT_ID)["name"]
        source_path = args.source_path.replace("{port}", name)
        data = request(f"https://api.github.com/repositories/{args.repository_id}/contents/{source_path}?ref={args.ref}", raw=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return
    if args.command == "checkout":
        checkout(path, args.repository_id, args.ref)
    normalize(path, metadata(PORT_ID)["name"])


if __name__ == "__main__":
    main()
