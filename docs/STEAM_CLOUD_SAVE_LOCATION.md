# Selecting a game's Windows save location

The build 13 device log mapped Dokimon's matching cloud files to
`C:/users/mobile/AppData/Local/dokimon`. Archiving the phone-only temporary file
worked but did not restore the PC progress. The user then reported one minute
of progress on the phone versus twelve on the PC, and a separate `save.sav`,
`volume.ini` and `startup.ini` under the prefix's `users/mythic/AppData/Local/dokimon`.
This is evidence of two save locations; the proposed correction still needs
on-device confirmation of which file the running game loads.

The Steam Cloud page now provides **Save location**, listing existing Windows
user directories. Selecting a folder changes only the chosen game/account's
mapping after a confirmation dialog. No registry is rewritten, no directory
is renamed or deleted, and no other game's mapping changes. Records without an
explicit choice retain the existing automatic mapping. Invalid, ambiguous,
public or symlinked profile choices are refused; an unavailable pinned folder
fails rather than silently falling back to another directory.

When the directory changes, the old sync baseline is cleared and a persisted
pending-choice flag blocks automatic transfers. Without that guard, the old
baseline could mistake a one-minute save in the newly selected directory for
newer local progress and upload it over the PC's twelve-minute cloud save.
The decision engine also returns a held, non-clear plan while the choice is
pending. A successful confirmed manual transfer clears the flag. A failed or
cancelled transfer leaves automatic syncing paused. The confirmation is bound
to its full path mapping and cannot be reused after a directory/account change.

For the reported Dokimon case: stop the game, choose **Save location > mythic**,
confirm, then choose **Download saves** and confirm the overwrite in that folder.
The existing `save.sav` is backed up before replacement; the cloud's
`world_save.sav` is created alongside it. The `mobile` copies and unrelated
settings remain in place. A read-only comparison follows, with no implicit
upload. The user must confirm that launching With Steam now shows the PC's
progress; do not label the issue fixed before that test.

Host tests exercise the actual profile selector and download storage commit
with two real temporary profile directories. They preserve the old one-minute
save in a completed backup while installing the twelve-minute fixture into
the selected directory, leave the other profile and volume settings untouched,
reject invalid/symlinked paths, hold automatic uploads/downloads after selection,
and check record compatibility and persistence of the pending state. Hashing in
storage tests uses its existing deterministic stand-in. These tests cannot prove
Dokimon's runtime save path on the user's phone.
