# Session reuse

PocketGames No J keeps the interpreter's Wine session ready after a game ends. This is now
normal launch behavior, including for installations that saved the old `sessionReuse=false`
preference. The old opt-in toggle is removed. Only the Wine system session stays; the game
must actually exit before another game can start. Memory pressure can still require an app
restart, and all 64-bit games in an app run use the first 64-bit game's FXR/FXI choice.

Save in the game, open its menu (the ellipsis button, a three-finger tap, or a controller's
Home button / View + Menu chord), then choose **Quit game (keep app open)** and confirm.
The app sends Alt+F4, allowing the game to run its exit/save dialog. Answer any question in
the game. A slow exit remains running until it finishes or the player explicitly confirms
**Force quit game…**. No timeout or repeated Quit automatically discards unsaved progress.
Force quit uses the existing wineserver process-termination path and can lose unsaved work.
Both paths wait for Wine's completion before clearing the surface and returning to Library.
**Hide game (keeps running)** and **Quit game and close PocketGames No J…** remain separate.

`engine/wine/patches/session_reuse.py` updates the Wine server and app bridge. The app's
`wine_host.c` resets interpreter state before another program starts. FXI32 releases earlier
32-bit state when the next 32-bit game starts; some 64-bit allocations persist until app exit.
The existing Wine `.finished` / `.failed` notification triggers Steam Cloud's end-of-game
sync after native cleanup, including Steam Dock cleanup. Requesting Quit or confirming Force
quit alone does not mark the game finished or upload saves. Cloud conflict confirmations,
the Dokimon Windows profile, and five-backup retention are unchanged.

Regression checks: `tests/host/run.sh` includes the quit state machine (normal and forced
exit, slow exit, retries, repeated requests and stale callbacks after the next launch).

Device acceptance (a full Wine build is required; source-only iOS verification cannot run it):

1. From a fresh install and an upgrade with `sessionReuse=false`, launch Forager, save, choose
   Quit game and confirm; verify Library appears while PocketGames remains open. Relaunch
   Forager, then try another game; confirm saved progress, picture, audio and controls work.
2. Launch Dokimon **With Steam**, save, quit through its normal confirmation, and verify Dock
   cleanup and the existing end-of-game cloud sync. Relaunch With Steam and check saves.
3. Cancel each quit confirmation; the same game should resume. Leave an in-game exit dialog
   open for longer than ten seconds; it must stay alive and accept cancel/confirm.
4. Force quit a stuck game only after confirming the unsaved-progress warning. Verify the
   library waits for Wine, game audio/overlays/input stop, and another game can launch.
5. Quit and relaunch the same title quickly; old callbacks must not alter the new game.
   Repeat with 32-bit / 64-bit games and with a controller held while opening the menu.
6. Check existing cloud download/manual upload, backup retention, and conflict confirmations.
