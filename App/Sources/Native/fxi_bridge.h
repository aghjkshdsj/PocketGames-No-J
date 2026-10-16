// SPDX-License-Identifier: GPL-3.0-or-later
// FXI (engine/fxi, docs/FAST_INTERPRETER.md): PocketGamesNoJ's own fast x86-64
// interpreter. No executable memory, so it always works, with or without JIT.

#ifndef PocketGamesNoJ_FXI_BRIDGE_H
#define PocketGamesNoJ_FXI_BRIDGE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "run_result.h" // mid_run_result

#ifdef __cplusplus
extern "C" {
#endif

/// Runs an ELF image using FXI. Serialised.
bool mid_fxi_run_elf(const uint8_t *elf, size_t len, int argc, const char *const *argv, mid_run_result *out);
const char *mid_fxi_version(void);

#ifdef __cplusplus
}
#endif

#endif
