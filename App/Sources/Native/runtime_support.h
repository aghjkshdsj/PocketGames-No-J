// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef void (*mid_log_fn)(const char *line);
void mid_set_log_sink(mid_log_fn sink);
void mid_log(const char *fmt, ...) __attribute__((format(printf, 1, 2)));
bool mid_exe_window(uint64_t *base, uint64_t *size);
uint64_t mid_available_memory(void);
uint64_t mid_phys_footprint(void);
uint64_t mid_task_max_address(void);
#ifdef __cplusplus
}
#endif
