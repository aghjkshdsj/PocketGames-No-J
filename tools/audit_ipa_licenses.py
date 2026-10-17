#!/usr/bin/env python3
"""Read-only evidence for an IPA's notices, FFmpeg symbols and converter payload."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'Payload/PocketGamesNoJ.app/'


def macho(data):
    if len(data) < 32 or data[:4] != b'\xcf\xfa\xed\xfe':
        raise ValueError('Expected a little-endian 64-bit Mach-O image')
    count, command_bytes = struct.unpack_from('<II', data, 16)
    end = 32 + command_bytes
    if end > len(data):
        raise ValueError('Truncated load commands')
    offset, symtab, sections = 32, None, {}
    for _ in range(count):
        if offset + 8 > end:
            raise ValueError('Truncated load command')
        cmd, size = struct.unpack_from('<II', data, offset)
        if size < 8 or offset + size > end:
            raise ValueError('Invalid load command size')
        if cmd == 2:  # LC_SYMTAB
            if size < 24:
                raise ValueError('Truncated symbol table command')
            symtab = struct.unpack_from('<IIII', data, offset + 8)
        if cmd == 0x19:  # LC_SEGMENT_64
            if size < 72:
                raise ValueError('Truncated segment')
            nsects = struct.unpack_from('<I', data, offset + 64)[0]
            if 72 + nsects * 80 > size:
                raise ValueError('Truncated section table')
            for i in range(nsects):
                pos = offset + 72 + i * 80
                name, segment, address, length, file_offset = struct.unpack_from('<16s16sQQI', data, pos)
                flags = struct.unpack_from('<I', data, pos + 64)[0]
                if flags & 0xff in (1, 12, 18):  # zero-fill sections have no file payload
                    continue
                if file_offset + length > len(data):
                    raise ValueError('Truncated section data')
                key = segment.rstrip(b'\0').decode() + '/' + name.rstrip(b'\0').decode()
                if key in sections:
                    raise ValueError('Duplicate section')
                sections[key] = {'address': address, 'size': length,
                                 'sha256': hashlib.sha256(data[file_offset:file_offset + length]).hexdigest()}
        offset += size
    symbols = []
    if symtab:
        start, count, strings, string_size = symtab
        if start + count * 16 > len(data) or strings + string_size > len(data):
            raise ValueError('Truncated symbol data')
        for i in range(count):
            name, kind = struct.unpack_from('<IB', data, start + i * 16)
            if kind & 0xe0 or kind & 0x0e not in (2, 14):
                continue  # skip debug records and undefined imports
            if name >= string_size:
                raise ValueError('Invalid symbol string index')
            last = data.find(b'\0', strings + name, strings + string_size)
            if last < 0:
                raise ValueError('Unterminated symbol')
            symbols.append(data[strings + name:last].decode('utf-8', errors='replace'))
    return sections, symbols


def audit(ipa, original=None):
    lock = json.loads((ROOT / 'compliance/source-lock.json').read_text(encoding='utf-8'))
    with zipfile.ZipFile(ipa) as z:
        if z.testzip() is not None:
            raise ValueError('IPA ZIP integrity check failed')
        info = json.loads(z.read(PREFIX + 'Legal/build-info.json'))
        docs = json.loads(z.read(PREFIX + 'Legal/index.json'))['documents']
        for doc in docs:
            if Path(doc['file']).name != doc['file'] or '/' in doc['file'] or '\\' in doc['file']:
                raise ValueError('Unsafe notice filename')
            data = z.read(PREFIX + 'Legal/' + doc['file'])
            if not data.strip() or hashlib.sha256(data).hexdigest() != doc['sha256']:
                raise ValueError('Missing or changed legal notice: ' + doc['file'])
        app = z.read(PREFIX + 'PocketGamesNoJ')
        _, symbols = macho(app)
        ijg = sorted(s for s in symbols if re.search(r'ff_jpeg_fdct|ff_j_rev_dct', s))
        converter_path = ('Frameworks/PGShaderConverter.framework/PGShaderConverter'
                          if PREFIX + 'RuntimeFrameworks.json' in z.namelist()
                          else 'd3d12/libmetalirconverter.dylib')
        converter = z.read(PREFIX + converter_path)
        sections, _ = macho(converter)
        result = {
            'ipa': str(ipa.resolve()), 'ipa_sha256': hashlib.sha256(ipa.read_bytes()).hexdigest(),
            'source_revision': info['revision'], 'verified_notice_count': len(docs),
            'ffmpeg_defined_ijg_symbols': ijg,
            'ffmpeg_configuration_strings_found': {flag: flag.encode() in app for flag in
                ('--disable-gpl', '--disable-nonfree', '--disable-version3')},
            'symbol_audit_limit': 'Defined symbols establish retention when present; absence is inconclusive after stripping or inlining.',
            'configuration_audit_limit': 'Absent configuration strings do not establish which configure options were used; retain the source/build artifact evidence.',
            'converter_shipped_sha256': hashlib.sha256(converter).hexdigest(),
            'converter_path': converter_path,
            'converter_version_from_build_pin': lock['converter']['version'],
            'converter_sections': sections,
            'legal_clearance': False,
        }
        if original:
            data = original.read_bytes()
            if hashlib.sha256(data).hexdigest() != lock['converter']['unsigned_dylib_sha256']:
                raise ValueError('Original converter does not match the pinned unsigned binary')
            original_sections, _ = macho(data)
            if not sections or sections != original_sections:
                raise ValueError('Shipped converter payload sections differ from pinned original')
            result['converter_payload_matches_pinned_original'] = True
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('ipa', type=Path)
    p.add_argument('--converter-original', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = audit(args.ipa, args.converter_original)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('Verified', result['verified_notice_count'], 'notices; IJG symbols:', result['ffmpeg_defined_ijg_symbols'])
