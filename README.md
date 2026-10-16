# PocketGames No J

Maintained by **Dan**. An experimental iOS game library and Windows compatibility app using
FXI, FXI32 and FXR interpreters, Wine, Direct3D on Metal, and optional Blink benchmarks.

The app starts games through the interpreter and loads Windows libraries from signed app files.
It includes Steam sign-in, library and downloads, Steam Cloud, controller input, touch controls,
per-game settings, and custom game folders. Compatibility and performance vary by game.
32-bit support and session reuse remain experimental. This is a research project.

## Install

Download an IPA from [Releases](../../releases) and sideload it using your preferred iOS
installer. Open PocketGames No J, sign in to Steam or add a game folder, and choose Play.
Windows games require a build containing the Wine and signed-library resources.

## Build

The workflows in `.github/workflows` build interpreter tests, Wine, DXMT and the iOS app.
For a complete build, run Wine unix, Wine i386, DXMT and DXMT PE workflows first, then
Build IPA. The first app build can contain only the engines whose resources are available.
On a Mac, run `mkdir -p App/Generated/PE`, then `xcodegen generate` and build
`PocketGamesNoJ.xcodeproj`, scheme `PocketGamesNoJ`.
The generated Xcode project is intentionally untracked.

## License and provenance

GPL-3.0-or-later: see [LICENSE](LICENSE), [LICENSE-EXCEPTION.md](LICENSE-EXCEPTION.md),
and [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md). Original author credits and
pinned dependency references are preserved so the retained code remains attributable and buildable.
Steam is a trademark of Valve Corporation. This project is not affiliated with Valve or Apple.
