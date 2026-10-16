// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef POCKETGAMES_WINE_STARTUP_H
#define POCKETGAMES_WINE_STARTUP_H

/* Called before Wine reads its address-space policy, and by both log readers. */
void mid_wine_configure_address_space(void);
void mid_wine_observe_startup_log(const char *line);

#endif
