#!/usr/bin/env python3
"""Remove the unused executable-pool setup from the pinned app-side Wine bridge."""
from pathlib import Path
import sys
p=Path(sys.argv[1]) / "WineProcessBridge.m"
s=p.read_text()
s=s.replace('#include "FEXBridge.h"  // fex_get_jit_write_offset()\n', '')
start='        /* iOS-Madeira 2026-07-02: publish the TRUE JIT-pool RX->RW offset'
end='        /* iOS-Madeira: TSO stays ENABLED'
if start in s:
    a=s.index(start); b=s.index(end,a)
    s=s[:a]+s[b:]
assert 'fex_get_jit_write_offset' not in s, 'Pinned bridge changed: review its execution setup'
s=s.replace('madeira-log.txt', 'wine-log.txt')
p.write_text(s)
