# Explicit Steam Cloud download

The Dokimon Quest report showed `3 files, 3 identical here` for `save.sav`,
`world_save.sav` and `world_temp_data.sav`, while the PC's progress was not seen
in-game. Launching the game With Steam was confirmed working. The supplied log
contained sign-in/library activity but no cloud operations, so it does not
establish the runtime destination or the reason progress was missing.

An "identical" comparison checks both size and SHA-1, not just file existence.
Previously, manual Download selected only cloud-only or differing entries and
would skip all three matching entries. It now selects every mapped cloud file,
including matching entries, and presents the existing confirmation sheet.
After confirmation it fetches all selected bytes, verifies cloud checksums,
backs up existing local files before replacement, and writes the fresh copies.
An unmappable selected destination fails rather than silently skipping a file.

The post-transfer operation is a read-only comparison. Manual Download must not
silently run a two-way sync that could upload saves, including after a failed
download. Automatic pre/post-game synchronization retains its normal change and
conflict rules. Manual Upload retains its original file selection rules.

The log records request intent, preparation stage, file/matching counts and
transfer results. The empty-result message
distinguishes no remote files from unsupported destinations. The UI explains
that manual Download fetches fresh copies of matching files too.

Host regression tests reproduce the three matching-file case, verify that
automatic synchronization still skips matching copies, exclude local-only files
from downloads, and retain the existing upload rules. Device testing must still
confirm the fresh download, backup count, actual progress in Dokimon and normal
Steam launch. If fresh copies do not restore progress, inspect the game's actual
save destination and the PC cloud revision; do not remap or overwrite other
profiles by guesswork.

## Build 12 device evidence and phone-only recovery

The next supplied device log identifies build 12 and confirms a two-file manual
download after overwrite confirmation: both files were fetched, two local copies
were backed up, and the comparison before launch remained identical. The user
identified `save.sav` and `world_save.sav` as in sync, while
`world_temp_data.sav` was phone-only. The cloud listing has two files and one
formerly synced file remains local after its removal from the cloud.

This establishes that re-download is working, but does not establish that the
game loads the two cloud copies. A retained temporary file may mask that state;
neither that behavior nor a profile mismatch has been proven on-device. Ordinary
Download and automatic sync continue preserving extra local files.

For an explicit, reversible test, the Files list now offers **Move to backup**
only for phone-only files. With the game stopped, the user selects
`world_temp_data.sav` and confirms a dialog explaining active-copy removal and
five-backup retention. The handler rechecks Steam's listing and the local hash,
publishes a complete backup before removing the selected active file, and then
performs only a read-only comparison. A file now present in the cloud, changed
since selection, unreadable, symlinked, or not successfully backed up is left
active. Other local and remote saves are not removed. Backup Restore can put the
archived bytes back; its existing documented synchronization behavior still
applies.

New `[steam-cloud-file]` diagnostics report each file's state, byte counts and
relative Windows destination (up to 100 files per comparison). Steam account
components are redacted; save contents and authentication data are not logged.
These logs remain on-device unless shared by the user. They can distinguish a
profile/location mismatch if moving aside the temporary file does not help.
No profile remapping or copying across profiles is performed by this change.

Storage regression tests use the production archive operation on temporary
files: the temporary world is archived with exact restorable bytes, the two
cloud-matching saves and a remote-file stand-in remain unchanged, the five-set
cap holds, and hash mismatch, backup failure and symlinks prevent removal.
