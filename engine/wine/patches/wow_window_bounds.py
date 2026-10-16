#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Use the unoccupied pool slot for interpreted WoW64, within the kernel map."""
from pathlib import Path
import sys

REL = 'build/ntdll-unix/virtual_ios.c'
MARK = '/* PocketGamesNoJ wow-window-bounds */'
ANCHOR = '''    if (*ceil > IOS_WOW_CEF_POOLS_START) *ceil = IOS_WOW_CEF_POOLS_START;

    if (kern_max && kern_max < *floor + IOS_WOW_WINDOW_SIZE)
'''
REPLACEMENT = '''    if (*ceil > IOS_WOW_CEF_POOLS_START) *ceil = IOS_WOW_CEF_POOLS_START;
    /* PocketGamesNoJ wow-window-bounds */
    /* The normal floor skips an 896 MiB code-generation pool even when none
     * exists. With a 454 GiB map this skips the usable 448..452 GiB slot,
     * and rounding the old floor up selects 452..456 GiB, past the map end.
     * Reuse only the empty slot in interpreter sessions; never overlap a pool.
     * This changes guest-window candidates, not 64-bit furniture placement. */
    {
        const char *interpreter = getenv( "WINE_IOS_NOJIT" );
        if (interpreter && interpreter[0] == '1' && !ios_jit_pool_size_global)
            *floor = (ULONG_PTR)0x7000000000ULL;
    }
    if (kern_max && *ceil > kern_max) *ceil = kern_max;

    /* A complete aligned slot AND its guard must fit. Comparing the unaligned
     * floor alone missed the 454 GiB device map. Unknown maps keep the port's
     * bounds and let the actual non-overwriting reservation decide. */
    if (kern_max && ((kern_max < *floor) ||
        ((*floor + IOS_WOW_WINDOW_SIZE - 1) & ~(IOS_WOW_WINDOW_SIZE - 1)) > kern_max ||
        kern_max - ((*floor + IOS_WOW_WINDOW_SIZE - 1) & ~(IOS_WOW_WINDOW_SIZE - 1)) <
            IOS_WOW_WINDOW_SIZE + ios_wow_guard_size()))
'''


def patch(text):
    if MARK in text:
        if REPLACEMENT not in text:
            raise ValueError('wow_window_bounds: incomplete or changed previous patch')
        return text
    if text.count(ANCHOR) != 1:
        raise ValueError('wow_window_bounds: pinned window-band anchor changed')
    return text.replace(ANCHOR, REPLACEMENT)


if __name__ == '__main__':
    path = Path(sys.argv[1]) / REL
    path.write_text(patch(path.read_text()), encoding='utf-8')
    print('wow_window_bounds: verified interpreter window placement')
