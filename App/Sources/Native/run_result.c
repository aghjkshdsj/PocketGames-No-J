// SPDX-License-Identifier: GPL-3.0-or-later
#include "run_result.h"
const char *mid_run_result_output(const mid_run_result *r) { return r->output; }
const char *mid_run_result_error(const mid_run_result *r) { return r->error; }
