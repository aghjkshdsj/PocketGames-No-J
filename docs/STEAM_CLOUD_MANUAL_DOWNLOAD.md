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
transfer results, without account data or file paths. The empty-result message
distinguishes no remote files from unsupported destinations. The UI explains
that manual Download fetches fresh copies of matching files too.

Host regression tests reproduce the three matching-file case, verify that
automatic synchronization still skips matching copies, exclude local-only files
from downloads, and retain the existing upload rules. Device testing must still
confirm the fresh download, backup count, actual progress in Dokimon and normal
Steam launch. If fresh copies do not restore progress, inspect the game's actual
save destination and the PC cloud revision; do not remap or overwrite other
profiles by guesswork.
