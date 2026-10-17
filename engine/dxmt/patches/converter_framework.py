#!/usr/bin/env python3
"""Prefer the bundled converter framework; retain legacy builds' path."""
from pathlib import Path
import sys


def patch(text):
    anchor = 'NSString *p = [base stringByAppendingPathComponent:@"d3d12/libmetalirconverter.dylib"];'
    replacement = '''/* PocketGamesNoJ converter framework lookup */
        BOOL packaged = [[NSFileManager defaultManager] fileExistsAtPath:
                         [base stringByAppendingPathComponent:@"RuntimeFrameworks.json"]];
        NSString *p = [base stringByAppendingPathComponent:packaged
                      ? @"Frameworks/PGShaderConverter.framework/PGShaderConverter"
                      : @"d3d12/libmetalirconverter.dylib"];'''
    fallback = 'if (!g_ir.handle) {\n            /* Also try a plain name:'
    if 'PocketGamesNoJ converter framework lookup' in text:
        return text
    if text.count(anchor) != 1 or text.count(fallback) != 1:
        raise ValueError('Unexpected converter loader; inspect pinned source')
    return text.replace(anchor, replacement).replace(
        fallback, 'if (!g_ir.handle && !packaged) {\n            /* Also try a plain name:')


if __name__ == '__main__':
    path = Path(sys.argv[1]) / 'danport-d3d12/src/unix/danport_ir_unix.mm'
    path.write_text(patch(path.read_text()), encoding='utf-8')
