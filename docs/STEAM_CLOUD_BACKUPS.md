# Steam Cloud backup management

Each game retains its five newest completed backup sets. A set holds all files
saved before one replacement operation, so a three-file game save still counts
as one backup. A completed sixth set removes the oldest set for that same game.
Opening the game's backup list also reduces an existing larger collection to
five. There is no age-based exemption.

New sets are written to a hidden staging directory. The complete manifest and
files are published together before retention runs; an incomplete or failed
backup does not evict a completed set. A new set is protected against immediate
eviction if the device's clock moved backward. Filesystem failures are surfaced
rather than counted as successful deletions.

The game's Steam Cloud section has Restore and Delete beside each backup.
Delete asks for confirmation and removes that backup set only. It does not
delete live game saves or remote Steam Cloud files. Controls are unavailable
while the game or its cloud operation is running. Deletion validates the app ID,
one directory component, manifest identity and resolved directory boundaries;
symbolic links cannot redirect it into another game's backups or elsewhere.

Host tests cover the fifth/sixth transition, old collections, equal timestamps,
clock rollback, incomplete staging, per-game isolation, deletion, live-save
preservation and traversal/symlink refusal. The production backup store is
compiled into the filesystem tests; only its hashing/logging collaborators have
test stand-ins.

The continuing Dokimon progress report is a separate unresolved issue. The
supplied log reported two identical remote files and one local-only file, with
the older zero-file manual-download diagnostic, while the user reported build
11 installed. The startup log now includes the version/build so a fresh report
can be associated with the installed candidate. These backup controls do not
claim to resolve the game's actual cloud-save destination or PC progress.
