// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef struct {
    bool ok;               ///< ran to exit(); false on load/translate failure
    int64_t exit_code;
    double seconds;        ///< host wall time
    uint64_t syscalls;
    char output[8192];     ///< what the guest wrote to stdout/stderr
    size_t output_len;
    char error[256];
} mid_run_result;

/// Swift does not import C arrays this large, so read them through these.
const char *mid_run_result_output(const mid_run_result *r);
const char *mid_run_result_error(const mid_run_result *r);


#ifdef __cplusplus
}
#endif
