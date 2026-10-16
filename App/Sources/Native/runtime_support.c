// SPDX-License-Identifier: GPL-3.0-or-later
// Shared logging, memory accounting and fixed-image address reservation.
#include "runtime_support.h"
#include <mach/mach.h>
#include <os/log.h>
#include <os/proc.h>
#include <stdarg.h>
#include <stdio.h>
static mid_log_fn g_sink;

void mid_set_log_sink(mid_log_fn sink) { g_sink = sink; }

void mid_log(const char *fmt, ...) {
    char buf[1024];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof buf, fmt, ap);
    va_end(ap);
    os_log(OS_LOG_DEFAULT, "%{public}s", buf);
    if (g_sink) g_sink(buf);
}


static vm_address_t g_win_base;
static const vm_address_t kExeWin = 0x140000000ul, kExeWinSize = 0x8000000ul;
__attribute__((constructor(101), used)) static void mid_early_va_claim(void) {
    vm_address_t a = kExeWin;
    if (vm_allocate(mach_task_self(), &a, kExeWinSize, VM_FLAGS_FIXED) == KERN_SUCCESS && a == kExeWin) {
        vm_protect(mach_task_self(), a, kExeWinSize, 0, VM_PROT_NONE);
        g_win_base = a;
    }
}
bool mid_exe_window(uint64_t *base, uint64_t *size) {
    if (!g_win_base) return false;
    *base = g_win_base; *size = kExeWinSize;
    return true;
}
uint64_t mid_available_memory(void) { return (uint64_t)os_proc_available_memory(); }

uint64_t mid_phys_footprint(void) {
    task_vm_info_data_t vmi;
    mach_msg_type_number_t cnt = TASK_VM_INFO_COUNT;
    if (task_info(mach_task_self(), TASK_VM_INFO, (task_info_t)&vmi, &cnt) != KERN_SUCCESS) return 0;
    return vmi.phys_footprint;
}

uint64_t mid_task_max_address(void) {
    task_vm_info_data_t vmi;
    mach_msg_type_number_t cnt = TASK_VM_INFO_COUNT;
    if (task_info(mach_task_self(), TASK_VM_INFO, (task_info_t)&vmi, &cnt) != KERN_SUCCESS) return 0;
    return vmi.max_address;
}
