// SPDX-License-Identifier: GPL-3.0-or-later
#include "wine_startup.h"
#include "wine_host.h"

#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static pthread_mutex_t failure_lock = PTHREAD_MUTEX_INITIALIZER;
/* A fatal main-process initialization failure poisons this Wine session. Never
 * clear it for session reuse: the host must be restarted before another boot. */
static int address_space_failed;

void mid_wine_configure_address_space(void) {
    const char *interpreter = getenv("WINE_IOS_NOJIT");
    if (interpreter && strcmp(interpreter, "1") == 0) {
        /* Reserve the complete 4 GiB guest window and keep 2 GiB outside it.
         * The port's default 8 GiB headroom rejects the 7,525 MiB free-VA map
         * observed on an iPhone 15 Pro Max before even trying a reservation.
         * Signed-library/interpreter sessions do not allocate a translation
         * arena. Wine still checks the map size, contiguous window and guard. */
        setenv("DANPORT_WOW_MIN_FREE_GB", "2", 1);
    }
}

void mid_wine_observe_startup_log(const char *line) {
    if (!line || !strstr(line, "[wow-window] main-process reserve FAILED") ||
        !strstr(line, "a 32-bit main image cannot run without a guest window")) return;
    pthread_mutex_lock(&failure_lock);
    address_space_failed = 1;
    pthread_mutex_unlock(&failure_lock);
}

int mid_wine_startup_error(char *err, size_t errlen) {
    pthread_mutex_lock(&failure_lock);
    int failed = address_space_failed;
    pthread_mutex_unlock(&failure_lock);
    if (err && errlen) {
        snprintf(err, errlen, "%s", failed
            ? "Wine could not reserve the address space needed by this 32-bit game. "
              "Swipe PocketGames No J away in the app switcher and reopen it before trying again. "
              "If it still fails, share the new app log."
            : "");
    }
    return failed;
}
