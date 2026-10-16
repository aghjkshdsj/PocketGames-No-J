// SPDX-License-Identifier: GPL-3.0-or-later
#include "wine_host.h"
#include "wine_startup.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    char err[512] = "previous error";
    assert(!mid_wine_startup_error(err, sizeof err));
    assert(!*err);
    unsetenv("WINE_IOS_NOJIT");
    unsetenv("DANPORT_WOW_MIN_FREE_GB");
    mid_wine_configure_address_space();
    assert(!getenv("DANPORT_WOW_MIN_FREE_GB"));
    setenv("WINE_IOS_NOJIT", "0", 1);
    setenv("DANPORT_WOW_MIN_FREE_GB", "8", 1);
    mid_wine_configure_address_space();
    assert(!strcmp(getenv("DANPORT_WOW_MIN_FREE_GB"), "8"));
    setenv("WINE_IOS_NOJIT", "1", 1);
    mid_wine_configure_address_space();
    unsigned long headroom = strtoul(getenv("DANPORT_WOW_MIN_FREE_GB"), NULL, 10);
    assert(headroom >= 2);
    /* Actual Forager log: 7,525 MiB free. Previously 4 + 8 GiB rejected
     * the launch before the contiguous 4 GiB reservation was attempted. */
    assert(7525 < (4 + 8) * 1024);
    assert(7525 >= (4 + headroom) * 1024);

    mid_wine_observe_startup_log(NULL);
    mid_wine_observe_startup_log("[wow-window] session armed: a 32-bit process is expected");
    mid_wine_observe_startup_log("[wow-window] refused: map too small (7525 MB free VA)");
    mid_wine_observe_startup_log("[wow-window] child reserve FAILED 0xc0000017");
    mid_wine_observe_startup_log("[wow-window] main-process reserve FAILED (retrying)");
    assert(!mid_wine_startup_error(err, sizeof err));
    /* The final fatal line, unlike a recoverable failed reservation probe,
     * must end the launch UI even if wine_process_is_running stays true. */
    mid_wine_observe_startup_log("[winelog] [wow-window] main-process reserve FAILED 0xc0000017 — a 32-bit main image cannot run without a guest window; terminating this process");
    assert(mid_wine_startup_error(err, sizeof err));
    assert(strstr(err, "32-bit game"));
    assert(strstr(err, "reopen"));
    char tiny[2] = {'x', 'x'};
    assert(mid_wine_startup_error(tiny, sizeof tiny) && tiny[1] == 0);
    assert(mid_wine_startup_error(NULL, 0));
    mid_wine_observe_startup_log("[wow-window] reserved 4GB");
    assert(mid_wine_startup_error(err, sizeof err));
    puts("PASS: interpreter VA policy and fatal Wine startup reporting");
    return 0;
}
