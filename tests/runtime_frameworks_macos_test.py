"""Exercise real iOS linking, converter install-name editing and framework signing.

This macOS-only check does not execute iOS code or assert device compatibility.
"""
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from package_runtime_frameworks import package
from runtime_framework_audit import validate


def run(*command):
    subprocess.run(command, check=True)


def main():
    with tempfile.TemporaryDirectory(prefix='pocketgames-real-frameworks-') as tmp:
        app = Path(tmp) / 'PocketGamesNoJ.app'
        app.mkdir()
        source = Path(tmp) / 'native.c'
        source.write_text('const char payload[] = "section preservation"; int writable = 7; int main(void) { return writable; }\n')
        flags = ('xcrun', '--sdk', 'iphoneos', 'clang', '-arch', 'arm64', '-miphoneos-version-min=17.0')
        for relative in ('PE/wine/libntdll.dll.dylib', 'PE/wine-a64/libntdll.dll.dylib',
                         'PE/wine-a64/libxtajit.dll.dylib', 'PE/libspike-arm64ec.dylib'):
            path = app / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            run(*flags, '-dynamiclib', '-Wl,-headerpad_max_install_names',
                '-install_name', '@rpath/' + path.name, str(source), '-o', str(path))
        run(*flags, str(source), '-o', str(app / 'PocketGamesNoJ'))
        (app / 'Info.plist').write_bytes(plistlib.dumps({
            'CFBundleExecutable': 'PocketGamesNoJ', 'CFBundleIdentifier': 'com.pocketgamesnoj.framework-test',
            'CFBundlePackageType': 'APPL', 'CFBundleShortVersionString': '0.1.0',
            'CFBundleVersion': '1', 'MinimumOSVersion': '17.0'}))
        lock = json.loads((ROOT / 'compliance/source-lock.json').read_text())
        port = next(s for s in lock['sources'] if s['id'] == 'port')
        run(sys.executable, str(ROOT / 'tools/port_source.py'), 'file',
            str(app / 'd3d12/libmetalirconverter.dylib'), '--repository-id', '1175417517',
            '--ref', port['revision'], '--source-path', 'app/{port}/d3d12/libmetalirconverter.dylib')
        manifest = package(app, os.environ['GITHUB_SHA'])
        for record in manifest['libraries']:
            bundle = (app / record['executable']).parent
            run('codesign', '--force', '--sign', '-', '--timestamp=none', str(bundle))
            run('codesign', '--verify', '--strict', str(bundle))
        run('codesign', '--force', '--sign', '-', '--timestamp=none', str(app))
        run('codesign', '--verify', '--deep', '--strict', str(app))
        files = {p.relative_to(app).as_posix() for p in app.rglob('*') if p.is_file()}
        assert validate(files, lambda n: (app / n).read_bytes(), os.environ['GITHUB_SHA']) == 5
        print('Real iOS framework linking, pinned converter payload, metadata and signing checks passed; device execution not tested')


if __name__ == '__main__':
    main()
