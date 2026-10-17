#!/usr/bin/env python3
"""Check the complete sideload bundle before an IPA can be published."""
import argparse
import gzip
import io
from pathlib import Path
import plistlib
import re
import tarfile
from port_source import metadata, PORT_ID
from prepare_licenses import validate_app
from prepare_licenses import digest, ROOT, LEGAL
import json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("app", type=Path)
args = parser.parse_args()
app = args.app
required = [
    "PocketGamesNoJ", "Info.plist", "prefix-template.tar.gz",
    "PrivacyInfo.xcprivacy", "PrivacyPolicy.txt",
    "arm64ec-windows/dockhost.exe", "i386-windows/ntdll.dll",
    "PE/wine/libntdll.dll.dylib", "PE/wine/libkernel32.dll.dylib",
    "PE/wine/libkernelbase.dll.dylib", "PE/wine/libuser32.dll.dylib",
    "PE/wine/libd3d11.dll.dylib", "PE/wine/libdxgi.dll.dylib", "PE/wine/xtajit64.dll",
    "PE/wine-a64/libntdll.dll.dylib", "PE/wine-a64/libwow64.dll.dylib",
    "PE/wine-a64/libxtajit.dll.dylib", "PE/wine-a64/xtajit.dll",
]
for relative in required:
    path = app / relative
    assert path.is_file() and path.stat().st_size, f"Required game runtime missing: {relative}"
info = plistlib.loads((app / "Info.plist").read_bytes())
assert info["CFBundleDisplayName"] == "PocketGames No J", "Unexpected app display name"
validate_app(app)
legal_hashes = {d['sha256'] for d in json.loads((ROOT / LEGAL / 'index.json').read_text(encoding='utf-8'))['documents']}
name = metadata(PORT_ID)["name"]
patterns = [re.compile(re.escape(name.encode()), re.I)]
patterns += [re.compile(re.escape(value.encode(encoding))) for encoding in ("utf-16-le", "utf-16-be")
             for value in (name, name.lower(), name.upper())]

def check(data, label):
    assert not any(pattern.search(data) for pattern in patterns), f"Former namespace found in {label}"

for path in app.rglob("*"):
    relative = path.relative_to(app).as_posix()
    check(relative.encode(), relative)
    if not path.is_file():
        continue
    data = path.read_bytes()
    # Legal notices preserve their original names/wording; their exact contents
    # are verified against the checked-in license manifest above.
    if relative.startswith("Legal/") or relative == "arm64ec-windows/dock-notices.txt" or (relative.startswith("d3d12/") and digest(data) in legal_hashes):
        continue
    check(data, relative)
    if path.name.endswith(".tar.gz"):
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            for member in archive:
                check(member.name.encode(), relative + ":" + member.name)
                if member.isfile():
                    check(archive.extractfile(member).read(), relative + ":" + member.name)
    elif path.suffix == ".gz":
        check(gzip.decompress(data), relative)
print("Verified complete game runtimes, app identity and namespace in bundle resources")
