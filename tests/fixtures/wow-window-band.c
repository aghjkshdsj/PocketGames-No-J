// SPDX-License-Identifier: GPL-3.0-or-later
// The pinned port's ios_wow_band function, with host stubs for deterministic tests.
// Source: repository ID 1175417517, revision 65e6fe8f0da45b28b610c71fda9791e89d1060a6,
// build/ntdll-unix/virtual_ios.c. Only the namespace is normalized before patching.
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uintptr_t ULONG_PTR;
#define GB ((ULONG_PTR)1 << 30)
#define IOS_WOW_WINDOW_SIZE (4 * GB)
#define IOS_WOW_CEF_POOLS_START ((ULONG_PTR)0x7400000000)
#define IOS_WOW_MAX_WINDOWS 8
static ULONG_PTR map_end, ios_jit_pool_size_global;
static ULONG_PTR user_space_limit = 512 * GB;
static const ULONG_PTR ios_furniture_ceiling = 0x73ffff0000;
#define ios_usable_va_floor (448 * GB + (ios_jit_pool_size_global ? ios_jit_pool_size_global : (896UL << 20)))
static unsigned ios_wow_small_va_slots;
static ULONG_PTR ios_wow_map_end(void) { return map_end; }
static ULONG_PTR ios_wow_guard_size(void) { return 16384; }
static unsigned long ios_wow_env_ulong(const char *key, unsigned long fallback) {
    const char *value = getenv(key);
    return value && *value ? strtoul(value, NULL, 10) : fallback;
}
static void ios_wow_band( ULONG_PTR *floor, ULONG_PTR *ceil )
{
    static int announced;
    ULONG_PTR kern_max = ios_wow_map_end();

    *floor = ios_usable_va_floor;
    *ceil  = ios_furniture_ceiling ? ios_furniture_ceiling : (ULONG_PTR)user_space_limit;
    if (*ceil > IOS_WOW_CEF_POOLS_START) *ceil = IOS_WOW_CEF_POOLS_START;

    if (kern_max && kern_max < *floor + IOS_WOW_WINDOW_SIZE)
    {
        ULONG_PTR top = kern_max & ~(IOS_WOW_WINDOW_SIZE - 1);
        ULONG_PTR lo  = (ULONG_PTR)0x400000000ULL;                      /* 16 GB */
        ULONG_PTR hi  = top > 2 * IOS_WOW_WINDOW_SIZE ? top - 2 * IOS_WOW_WINDOW_SIZE : 0;
        unsigned long want = ios_wow_env_ulong( "DANPORT_WOW_SMALL_VA_SLOTS", 2 );

        if (want < 1) want = 1;
        if (want > IOS_WOW_MAX_WINDOWS) want = IOS_WOW_MAX_WINDOWS;
        ios_wow_small_va_slots = (unsigned)want;
        if (hi > (ULONG_PTR)0xb00000000ULL) hi = (ULONG_PTR)0xb00000000ULL;   /* 44 GB */
        if (hi > lo + IOS_WOW_WINDOW_SIZE)
        {
            *floor = lo;
            *ceil  = hi;
        }
        if (!announced)
        {
            announced = 1;
            dprintf( 2, "[wow-window] small address map: it ends at %p, below the normal "
                        "guest-window band -- candidates come from [%p,%p), at most %u window(s) "
                        "at once\n", (void *)kern_max, (void *)*floor, (void *)*ceil,
                     ios_wow_small_va_slots );
        }
    }
}

static ULONG_PTR first_slot(ULONG_PTR floor) {
    return (floor + IOS_WOW_WINDOW_SIZE - 1) & ~(IOS_WOW_WINDOW_SIZE - 1);
}
int main(void) {
    ULONG_PTR floor, ceil;
    map_end = 454 * GB;
    setenv("WINE_IOS_NOJIT", "1", 1);
    ios_wow_band(&floor, &ceil);
#ifdef ORIGINAL_BUG
    assert(first_slot(floor) == 452 * GB);
    assert(first_slot(floor) + IOS_WOW_WINDOW_SIZE > map_end);
    (void)ios_wow_guard_size();
    puts("Reproduced: original band selects 452..456 GiB on a 454 GiB map");
    return 0;
#else
    assert(floor == 448 * GB && ceil == map_end);
    assert(first_slot(floor) + IOS_WOW_WINDOW_SIZE + ios_wow_guard_size() <= ceil);
    // Full map, interpreter: the vacant slot is still available.
    map_end = 512 * GB;
    ios_wow_band(&floor, &ceil);
    assert(floor == 448 * GB && ceil == ios_furniture_ceiling);
    // An actual allocated pool is never overlapped, even with the interpreter flag.
    ios_jit_pool_size_global = 896UL << 20;
    ios_wow_band(&floor, &ceil);
    assert(floor == 448 * GB + ios_jit_pool_size_global && first_slot(floor) == 452 * GB);
    // On a short map, a pool or disabled interpreter uses the existing low band.
    map_end = 454 * GB;
    ios_wow_band(&floor, &ceil);
    assert(floor == 16 * GB && ceil == 44 * GB);
    ios_jit_pool_size_global = 0;
    unsetenv("WINE_IOS_NOJIT");
    ios_wow_band(&floor, &ceil);
    assert(floor == 16 * GB && ceil == 44 * GB);
    setenv("WINE_IOS_NOJIT", "0", 1);
    ios_wow_band(&floor, &ceil);
    assert(floor == 16 * GB && ceil == 44 * GB);
    // Boundary: an exactly fitting 4 GiB range without room for its guard is insufficient.
    map_end = 456 * GB;
    ios_wow_band(&floor, &ceil);
    assert(floor == 16 * GB && ceil == 44 * GB);
    // 63 GiB device maps keep the original low band and configured slot limit.
    setenv("WINE_IOS_NOJIT", "1", 1);
    setenv("DANPORT_WOW_SMALL_VA_SLOTS", "99", 1);
    map_end = 63 * GB;
    ios_wow_band(&floor, &ceil);
    assert(floor == 16 * GB && ceil == 44 * GB && ios_wow_small_va_slots == 8);
    setenv("DANPORT_WOW_SMALL_VA_SLOTS", "0", 1);
    ios_wow_band(&floor, &ceil);
    assert(ios_wow_small_va_slots == 1);
    // Unknown map: preserve the port's ceiling and let its safe reservation decide.
    map_end = 0;
    ios_wow_band(&floor, &ceil);
    assert(floor == 448 * GB && ceil == ios_furniture_ceiling);
    // Very small maps never produce a candidate beyond the reported end.
    map_end = 19 * GB;
    ios_wow_band(&floor, &ceil);
    assert(ceil <= map_end && first_slot(floor) + IOS_WOW_WINDOW_SIZE > ceil);
    puts("PASS: no-pool interpreter slot, map bounds, alignment, guard and pool protection");
    return 0;
#endif
}
