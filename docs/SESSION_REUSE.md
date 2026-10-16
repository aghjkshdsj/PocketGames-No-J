# Session reuse

Settings → Performance → Play another game without restarting keeps Wine running after a
game ends. It is experimental and applies to games started after the setting is enabled.
The next game must use compatible controller and interpreter settings. Memory pressure can
require an app restart. A game can be asked to quit through Alt+F4 or force-quit from its menu.

`engine/wine/patches/session_reuse.py` updates the Wine server and app bridge. The app's
`wine_host.c` resets interpreter state before another program starts. FXI32 releases earlier
32-bit state when the next 32-bit game starts; some 64-bit allocations persist until app exit.
Steam Cloud syncs after a game ends before allowing saves to be uploaded.
