"""Validate native framework identities, load commands and preserved sections."""
import json
from pathlib import PurePosixPath
import plistlib
import struct

from audit_ipa_licenses import macho


def linkage(data):
    if len(data) < 32 or data[:4] != b'\xcf\xfa\xed\xfe':
        raise ValueError('Expected arm64 Mach-O')
    cpu, _, kind, count, size = struct.unpack_from('<IIIII', data, 4)
    if cpu != 0x100000c:
        raise ValueError('Expected native arm64 library')
    end, offset = 32 + size, 32
    if end > len(data) or count > size // 8:
        raise ValueError('Invalid Mach-O commands')
    identity, imports, platforms = None, [], []
    for _ in range(count):
        if offset + 8 > end:
            raise ValueError('Truncated Mach-O command')
        cmd, length = struct.unpack_from('<II', data, offset)
        if length < 8 or length % 8 or offset + length > end:
            raise ValueError('Invalid Mach-O command')
        if cmd in (0xd, 0xc, 0x80000018, 0x8000001f, 0x20, 0x80000023):
            if length < 24:
                raise ValueError('Truncated dylib command')
            start = struct.unpack_from('<I', data, offset + 8)[0]
            last = data.find(b'\0', offset + start, offset + length)
            if start < 24 or start >= length or last < 0:
                raise ValueError('Invalid dylib command string')
            name = data[offset + start:last].decode('utf-8')
            if cmd == 0xd:
                if identity is not None:
                    raise ValueError('Duplicate library identity')
                identity = name
            else:
                imports.append(name)
        elif cmd == 0x32:  # LC_BUILD_VERSION
            if length < 24:
                raise ValueError('Truncated build version')
            platforms.append(struct.unpack_from('<I', data, offset + 8)[0])
        elif cmd == 0x25:  # LC_VERSION_MIN_IPHONEOS
            platforms.append(2)
        offset += length
    if offset != end:
        raise ValueError('Mach-O command size mismatch')
    return {'type': kind, 'identity': identity, 'imports': imports, 'platforms': platforms}


def validate(files, read, expected_revision=None):
    manifest = json.loads(read('RuntimeFrameworks.json'))
    if manifest.get('schema') != 1 or manifest.get('layout') != 'frameworks-v1':
        raise ValueError('Unknown native framework manifest')
    if expected_revision and manifest['revision'] != expected_revision:
        raise ValueError('Framework source revision mismatch')
    records = manifest.get('libraries', [])
    if not records:
        raise ValueError('Empty native framework inventory')
    identities, executables, sources, bundle_ids = set(), set(), set(), set()
    for record in records:
        name = record['executable']
        path = PurePosixPath(name)
        if len(path.parts) != 3 or path.parts[0] != 'Frameworks' or path.parts[1] != path.parts[2] + '.framework':
            raise ValueError('Invalid native framework path: ' + name)
        if name in executables or record['source'] in sources or record['bundle_identifier'] in bundle_ids:
            raise ValueError('Duplicate native framework identity')
        executables.add(name)
        sources.add(record['source'])
        bundle_ids.add(record['bundle_identifier'])
        if record['source'] in files:
            raise ValueError('Legacy native library remains: ' + record['source'])
        data = read(name)
        info = plistlib.loads(read(str(path.parent / 'Info.plist')))
        if (info.get('CFBundleExecutable') != path.name or info.get('CFBundlePackageType') != 'FMWK'
                or info.get('CFBundleIdentifier') != record['bundle_identifier']
                or info.get('CFBundleSupportedPlatforms') != ['iPhoneOS']):
            raise ValueError('Invalid framework metadata: ' + name)
        binary = linkage(data)
        expected = '@rpath/' + path.parts[1] + '/' + path.name
        if binary['type'] != 6 or binary['identity'] != expected or record['install_name'] != expected:
            raise ValueError('Invalid native library identity: ' + name)
        if binary['platforms'] != [2]:
            raise ValueError('Framework is not built for iOS devices: ' + name)
        if macho(data)[0] != record['sections']:
            raise ValueError('Framework section layout or payload changed: ' + name)
        identities.add(expected)
    for name in sorted(executables | {'PocketGamesNoJ'}):
        for dependency in linkage(read(name))['imports']:
            if dependency.startswith(('/usr/lib/', '/System/Library/')):
                continue
            if dependency not in identities:
                raise ValueError('Unresolved non-system dependency in ' + name + ': ' + dependency)
    return len(records)
