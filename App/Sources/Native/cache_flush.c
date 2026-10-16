// SPDX-License-Identifier: GPL-3.0-or-later
#if defined(__APPLE__) && defined(__aarch64__)
#include <libkern/OSCacheControl.h>
#include <stdint.h>

// Wine's NtFlushInstructionCache uses the compiler-runtime entry point, which
// the iOS SDK does not export. Forward it to Apple's public cache-control API.
void __clear_cache(void *begin, void *end) {
    uintptr_t first = (uintptr_t)begin, last = (uintptr_t)end;
    if (last > first) sys_icache_invalidate(begin, last - first);
}
#endif
