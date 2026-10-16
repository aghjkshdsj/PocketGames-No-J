// SPDX-License-Identifier: GPL-3.0-or-later
#include "wine_host.h"
#include "wine_startup.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "fxi.h"
#include "runtime_support.h"

#include <fcntl.h>
#include <pthread.h>

#if __has_include("wine_version.h")
#include "wine_version.h"
#endif

static void *stdio_reader(void *arg) {
    int fd = (int)(intptr_t)arg;
    char buf[4096], line[1024];
    size_t used = 0;
    for (;;) {
        ssize_t n = read(fd, buf, sizeof buf);
        if (n <= 0) break;
        for (ssize_t i = 0; i < n; i++) {
            if (buf[i] == '\n' || used == sizeof line - 1) {
                line[used] = 0;
                if (used) {
                    mid_wine_observe_startup_log(line);
                    mid_log("[stdio] %s", line);
                }
                used = 0;
            } else {
                line[used++] = buf[i];
            }
        }
    }
    return NULL;
}

void mid_capture_stdio(void) {
    static int done;
    if (done) return;
    int p[2];
    if (pipe(p) != 0) return;
    setvbuf(stdout, NULL, _IOLBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    dup2(p[1], 1);
    dup2(p[1], 2);
    close(p[1]);
    pthread_t t;
    if (pthread_create(&t, NULL, stdio_reader, (void *)(intptr_t)p[0]) == 0) pthread_detach(t);
    done = 1;
}


/* DanPort's bridge points Wine's stdout/stderr (and wineserver's log) at
 * Documents/wine-log.txt. Follow that file and copy its lines into the
 * PocketGamesNoJ log so one log has everything. */
static void *wine_log_follower(void *arg) {
    char *path = arg;
    int fd = -1;
    for (int i = 0; i < 200 && fd < 0; i++) {
        fd = open(path, O_RDONLY);
        if (fd < 0) usleep(50000);
    }
    if (fd < 0) {
        mid_log("[wine] no Wine log at %s", path);
        free(path);
        return NULL;
    }
    char buf[8192], line[1024];
    size_t used = 0;
    unsigned idle = 0;
    for (;;) {
        ssize_t n = read(fd, buf, sizeof buf);
        if (n <= 0) {
            usleep(100000);
            /* 60 s quiet after exit, unless the session stays for another program (the file goes on) */
            if (++idle > 600 && !mid_wine_running() && !mid_wine_session_reusable()) break;
            continue;
        }
        idle = 0;
        for (ssize_t i = 0; i < n; i++) {
            if (buf[i] == '\n' || used == sizeof line - 1) {
                line[used] = 0;
                if (used) {
                    mid_wine_observe_startup_log(line);
                    mid_log("[winelog] %s", line);
                }
                used = 0;
            } else {
                line[used++] = buf[i];
            }
        }
    }
    close(fd);
    free(path);
    return NULL;
}

static void follow_wine_log(const char *prefix) {
    /* The prefix lives in Documents; the log sits next to it. */
    char *path = malloc(1024);
    snprintf(path, 1024, "%s", prefix);
    char *slash = strrchr(path, '/');
    if (!slash) { free(path); return; }
    snprintf(slash, 1024 - (size_t)(slash - path), "/wine-log.txt");
    unlink(path); /* start fresh for this session */
    pthread_t t;
    if (pthread_create(&t, NULL, wine_log_follower, path) == 0) pthread_detach(t);
    else free(path);
}

#if PocketGamesNoJ_WITH_WINE

#include "WineProcessBridge.h"
#include "WineServerBridge.h"

static int g_booted;
static int g_programs;     /* Windows programs started in this app run (session reuse) */
static int g_reuse_armed;  /* the running session started with PocketGamesNoJ_SESSION_REUSE=1 */

/* DanPort's IOSDisplayShim.m and Winios.m (staged app sources). */
extern void danport_display_set_layer(void *layer);
extern void winios_screen_size(int *w, int *h);
extern void winios_set_compositor_frame(double x, double y, double w, double h);
extern void winios_set_desktop_rect(double x, double y, double w, double h, int set);

#include "Winios/WiniosGamepad.h"

void mid_pad_set(int slot, int connected, uint16_t buttons, uint8_t lt, uint8_t rt,
                 int16_t lx, int16_t ly, int16_t rx, int16_t ry) {
    if (slot < 0 || slot >= WINIOS_GAMEPAD_MAX) return;
    if (!connected) { winios_gamepad_set_state(slot, NULL); return; }
    struct winios_gamepad s = {0};
    s.connected = 1;
    s.buttons = buttons;
    s.left_trigger = lt; s.right_trigger = rt;
    s.lx = lx; s.ly = ly; s.rx = rx; s.ry = ry;
    winios_gamepad_set_state(slot, &s);
}

void mid_hidpad_set(int connected, uint32_t buttons, uint8_t lt, uint8_t rt,
                    int16_t lx, int16_t ly, int16_t rx, int16_t ry) {
    if (!connected) { winios_hidpad_set_state(NULL); return; }
    struct winios_hidpad h = {0};
    h.connected = 1;
    h.buttons = buttons;
    if (lt > 25) h.buttons |= WINIOS_HIDPAD_L2;
    if (rt > 25) h.buttons |= WINIOS_HIDPAD_R2;
    h.left_trigger = lt; h.right_trigger = rt;
    h.lx = lx; h.ly = ly; h.rx = rx; h.ry = ry;
    h.battery = WINIOS_HIDPAD_BATTERY_UNKNOWN;
    winios_hidpad_set_state(&h);
}

int mid_hidpad_gate(void) {
#ifdef PocketGamesNoJ_HIDPAD_GATE
    return 1;
#else
    return 0;
#endif
}

/* DanPort's PadOutput.m (staged app source; its GCController parameter is an object pointer). */
extern void danport_pad_output_configure(int xinput, int hid);
extern void danport_pad_output_set_slot(int slot, void *controller);
extern void danport_pad_output_set_active(int active);
void mid_pad_output_configure(int xinput, int hid) { danport_pad_output_configure(xinput, hid); }
void mid_pad_output_set_slot(int slot, void *controller) { danport_pad_output_set_slot(slot, controller); }
void mid_pad_output_set_active(int active) { danport_pad_output_set_active(active); }

extern void winios_post_key(int vk, int down);
extern void winios_pointer(int x, int y, unsigned int flags, unsigned int data);
void mid_post_key(int vk, int down) { winios_post_key(vk, down); }
void mid_post_mouse_button(unsigned int flags) { winios_pointer(0, 0, flags, 0); }
void mid_post_pointer(int x, int y, unsigned int flags, int data) { winios_pointer(x, y, flags, (unsigned int)data); }
extern void winios_post_touch_down(int x, int y);
extern void winios_post_touch_move(int x, int y);
extern void winios_post_touch_up(int x, int y);
void mid_post_touch(int phase, int x, int y) {
    if (phase == 0) winios_post_touch_down(x, y);
    else if (phase == 1) winios_post_touch_move(x, y);
    else winios_post_touch_up(x, y);
}
extern void winios_game_overlay_show(int shown, void *window);   /* Winios.m, engine/wine/stage-app.sh */
void mid_game_overlay_show(int shown, void *window) { winios_game_overlay_show(shown, window); }
extern int winios_game_picture_rect(int dw, int dh, int *x, int *y, int *w, int *h);   /* Winios.m, engine/wine/stage-app.sh */
int mid_game_picture_rect(int dw, int dh, int *x, int *y, int *w, int *h) { return winios_game_picture_rect(dw, dh, x, y, w, h); }

extern void danport_seed_prefix_if_needed(const char *prefix_path);
void mid_wine_seed_prefix(const char *prefix) { danport_seed_prefix_if_needed(prefix); }

void mid_display_set_layer(void *metal_layer) { danport_display_set_layer(metal_layer); }
void mid_display_screen_size(int *w, int *h) { winios_screen_size(w, h); }
void mid_display_layout(double fx, double fy, double fw, double fh,
                        double rx, double ry, double rw, double rh) {
    winios_set_compositor_frame(fx, fy, fw, fh);
    winios_set_desktop_rect(rx, ry, rw, rh, 1);
}

bool mid_wine_linked(void) { return true; }
int mid_wine_running(void) { return wine_process_is_running(); }

/* Session reuse (docs/SESSION_REUSE.md): WineProcessBridge.m as patched by
 * engine/wine/patches/session_reuse.py. */
extern int wine_session_reusable(void);
int mid_wine_session_reusable(void) {
    return g_reuse_armed && g_booted && wine_session_reusable();
}

/* Force quit: the in-process wineserver terminates every program of the session as
 * TerminateProcess does (engine/wine/patches/session_reuse.py, pocketgamesnoj_kill_programs), on its own
 * thread. Kept sessions only: a killed program's main thread then ends it through its exit path. */
extern void wineserver_kill_programs(int exit_code);
int mid_wine_force_quit(void) {
    if (!g_reuse_armed || !g_booted || !mid_wine_running()) return 0;
    mid_log("[session-reuse] force quit: the Wine server terminates the running programs");
    wineserver_kill_programs(1);
    return 1;
}

static int reuse_requested(void) {
    const char *reuse = getenv("PocketGamesNoJ_SESSION_REUSE");
    return reuse && *reuse == '1';
}

unsigned mid_fxr_win_invalidate_all(void);   /* fxr_win_shim.c */

/* Another program in the running session: a new top-level Windows process (the bridge boots it
 * like a child of no one). Nothing of the session's own start runs again: the JIT pool, the
 * wineserver, the log (it goes on in the same file). */
static bool boot_next(const char *prefix, const char *exe, const char *args, char *err, size_t errlen) {
    const char *nojit = getenv("WINE_IOS_NOJIT");
    if (!mid_wine_session_reusable() || !nojit || *nojit != '1') {
        snprintf(err, errlen, "Wine already ran in this app session; restart PocketGamesNoJ to start another program");
        return false;
    }
    wine_exit_status_reset();   /* the last program's error is not this one's */
    setenv("DANPORT_EXE", exe, 1);
    if (args && *args) setenv("DANPORT_ARGS", args, 1); else unsetenv("DANPORT_ARGS");
    /* The x64 blocks (FXI's, and FXR's: fxr_win_shim.c) are shared by the session's processes: an
     * earlier program's code may be gone and its addresses reused by this one. */
    unsigned dropped = fxi_win_invalidate_all() + mid_fxr_win_invalidate_all();
    g_reuse_armed = reuse_requested();   /* what the bridge does when this program ends */
    if (wine_process_start(prefix) != 0) {
        snprintf(err, errlen, "Wine process failed to start");
        return false;
    }
    g_programs++;
    mid_log("[session-reuse] started %s in the running Wine session (program %d of this app run; %u x64 blocks dropped)",
            exe, g_programs, dropped);
    return true;
}

/* Builds 163-164: the app ended while a second Steins;Gate started, with no crash report from
 * iOS, as when something calls exit(). If anything does while Wine runs, the log says who. */
#include <dlfcn.h>
#include <execinfo.h>
static void exit_report(void) {
    void *frames[32];
    int n = backtrace(frames, 32);
    mid_log("[exit] the app is ending through exit() while Wine was started (%d frames):", n);
    for (int i = 1; i < n; i++) {
        Dl_info d;
        if (dladdr(frames[i], &d) && d.dli_sname)
            mid_log("[exit]   %s+%#lx", d.dli_sname, (unsigned long)((char *)frames[i] - (char *)d.dli_saddr));
        else
            mid_log("[exit]   %p", frames[i]);
    }
}

bool mid_wine_boot(const char *prefix, const char *exe, const char *args, char *err, size_t errlen) {
    if (mid_wine_startup_error(err, errlen)) return false;
    if (g_booted) return boot_next(prefix, exe, args, err, errlen);
    setenv("WINE_IOS_NOJIT", "1", 1);
    mid_wine_configure_address_space();
    mid_log("[wine] interpreter address-space policy: 4 GiB guest window, %s GiB free VA headroom",
            getenv("DANPORT_WOW_MIN_FREE_GB"));
    char buf[32];
    uint64_t wb, ws;
    if (mid_exe_window(&wb, &ws)) {
        snprintf(buf, sizeof buf, "%llx:%llx", (unsigned long long)wb, (unsigned long long)ws);
        setenv("WINE_IOS_EXE_WINDOW", buf, 1);
    } else {
        mid_log("[wine] WARNING: 0x140000000 window not held; fixed-base .exe images will be displaced");
    }
    setenv("DANPORT_EXE", exe, 1);
    if (args && *args) setenv("DANPORT_ARGS", args, 1); else unsetenv("DANPORT_ARGS");
    mid_capture_stdio();
    follow_wine_log(prefix);
    mid_log("[wine] signed DLLs from %s", getenv("PocketGamesNoJ_PE_DIR"));

    if (wineserver_start(prefix) != 0) {
        snprintf(err, errlen, "wineserver failed to start");
        return false;
    }
    for (int i = 0; i < 300 && !wineserver_is_ready(); i++) usleep(20000);
    if (!wineserver_is_ready()) {
        snprintf(err, errlen, "wineserver did not become ready in 6 s");
        return false;
    }
    g_reuse_armed = reuse_requested();   /* the bridge keeps the wineserver when it ends */
    if (wine_process_start(prefix) != 0) {
        snprintf(err, errlen, "Wine process failed to start");
        return false;
    }
    g_booted = 1;
    g_programs = 1;
    atexit(exit_report);
    mid_log("[wine] started %s%s", exe, g_reuse_armed ? " (session reuse: the session stays when it ends)" : "");
    return true;
}

#else

void mid_wine_seed_prefix(const char *prefix) { (void)prefix; }
void mid_post_key(int vk, int down) { (void)vk; (void)down; }
void mid_post_mouse_button(unsigned int flags) { (void)flags; }
void mid_post_pointer(int x, int y, unsigned int flags, int data) { (void)x; (void)y; (void)flags; (void)data; }
void mid_post_touch(int phase, int x, int y) { (void)phase; (void)x; (void)y; }
void mid_game_overlay_show(int shown, void *window) { (void)shown; (void)window; }
int mid_game_picture_rect(int dw, int dh, int *x, int *y, int *w, int *h) { (void)dw; (void)dh; (void)x; (void)y; (void)w; (void)h; return 0; }
void mid_pad_set(int slot, int connected, uint16_t buttons, uint8_t lt, uint8_t rt,
                 int16_t lx, int16_t ly, int16_t rx, int16_t ry) {
    (void)slot; (void)connected; (void)buttons; (void)lt; (void)rt; (void)lx; (void)ly; (void)rx; (void)ry;
}
int mid_hidpad_gate(void) { return 0; }
void mid_pad_output_configure(int xinput, int hid) { (void)xinput; (void)hid; }
void mid_pad_output_set_slot(int slot, void *controller) { (void)slot; (void)controller; }
void mid_pad_output_set_active(int active) { (void)active; }
void mid_hidpad_set(int connected, uint32_t buttons, uint8_t lt, uint8_t rt,
                    int16_t lx, int16_t ly, int16_t rx, int16_t ry) {
    (void)connected; (void)buttons; (void)lt; (void)rt; (void)lx; (void)ly; (void)rx; (void)ry;
}
void mid_display_set_layer(void *metal_layer) { (void)metal_layer; }
void mid_display_screen_size(int *w, int *h) { *w = 1024; *h = 768; }
void mid_display_layout(double fx, double fy, double fw, double fh,
                        double rx, double ry, double rw, double rh) {
    (void)fx; (void)fy; (void)fw; (void)fh; (void)rx; (void)ry; (void)rw; (void)rh;
}

bool mid_wine_linked(void) { return false; }
int mid_wine_running(void) { return 0; }
int mid_wine_session_reusable(void) { return 0; }
int mid_wine_force_quit(void) { return 0; }
int wine_crash_exit_status(uint32_t *status) { (void)status; return 0; }
bool mid_wine_boot(const char *prefix, const char *exe, const char *args, char *err, size_t errlen) {
    (void)prefix; (void)exe; (void)args;
    snprintf(err, errlen, "This build does not include Wine yet (stage 2 in progress)");
    return false;
}

#endif
