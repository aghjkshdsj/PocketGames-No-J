# Third-party notices

| Component | Use in PocketGamesNoJ | License |
|---|---|---|
| [DanPort](https://api.github.com/repositories/1175417517) | x18-instruction classifier ported to Python for the no-JIT DLL audit (`engine/pedylib/pe2dylib.py`, from `build/ntdll-unix/virtual_ios.c`) | GPL-3.0-or-later with the DanPort Converter Exception |
| [DanPort](https://api.github.com/repositories/1175417517) SwiftSteam | Native Steam client (sign-in, library, depot downloads), vendored in `App/Sources/Steam/SwiftSteam/`, unchanged but for one added call in `Core/SteamSession.swift` (`callServiceMethodResult`: the response's EResult, for Steam Cloud) | GPL-3.0-or-later with the DanPort Converter Exception |
| [DanPort Dock](https://api.github.com/repositories/1393407380) (commit e0007841) | `dockhost.exe`, the headless host for Valve's own Steam client, built from source in CI (`engine/pedylib/build-spike.sh`, with `danport-dock-signin-wait.patch` and `danport-dock-cm-transport.patch`) and shipped with its notices (`dock-notices.txt`) | GPL-3.0-or-later with the DanPort Converter Exception, Copyright 2026 125hz |
| [DanPort](https://api.github.com/repositories/1175417517) Dock app side | `App/Sources/Steam/SteamDock.swift` (launch contract, sign-in transfer, report) and `SteamRuntime.swift` (Valve client download and verification), vendored from DanPort 65e6fe8f with small adaptations noted in each file | GPL-3.0-or-later with the DanPort Converter Exception
| [DroidDeck](https://github.com/Droid-Deck/DroidDeck) | Product design blueprint (no code copied) | GPL-3.0 |
| [SteamOS ARM Port](https://github.com/hashtagbasit/SteamOS-ARM-Port) | Preset naming (compat / fast / fastest) | GPL-2.0 (no code copied) |
| [Wine](https://www.winehq.org) via [DanPort's fork](https://github.com/willfaust/wine) (`engine/wine/PIN`) | Windows DLL farms: ARM64EC and aarch64 (DanPort's prebuilt PE files, also wrapped as signed dylibs; `wow64win.dll` rebuilt from the same source with `engine/wine/patches/wow64win_atoms.py`), i386 (built from source in CI, `engine/wine/build-i386.sh`, for 32-bit games; its `dinput.dll` gets `engine/wine/patches/dinput_ios_pad.py`); unix side linked statically, with session-reuse changes to the wineserver's `process.c` and `thread.c` and to ntdll's `sync.c` (`engine/wine/patches/session_reuse.py`, docs/SESSION_REUSE.md) | LGPL-2.1-or-later |
| [DXMT](https://github.com/3Shain/dxmt) via [DanPort's fork](https://github.com/willfaust/dxmt) (`engine/dxmt/PIN`) | Direct3D 9/10/11 → Metal: ARM64EC and i386 DLLs built from source in CI, unix side linked statically; `engine/dxmt/patches/metal_owner.py` adds a record of each 32-bit process's Metal textures and buffers to its winemetal_unix.c (docs/SESSION_REUSE.md) | MIT (upstream); D3D9 import LGPL-2.1-or-later; DanPort's changes GPL-3.0-or-later (with the DanPort Converter Exception for 125hz's) |
| [FEX-Emu](https://github.com/FEX-Emu/FEX) WOW64 module (`Source/Windows/WOW64/Module.cpp`, via DanPort's fork) | The BTCpu* contract, the BOP-page convention and the unwind-frame trampoline, ported to C in `engine/pedylib/emu/xtajit_wow.c` (the no-JIT WoW64 CPU module) | MIT (upstream); DanPort's guest-window changes GPL-3.0-or-later with the DanPort Converter Exception |
| [DanPort](https://api.github.com/repositories/1175417517) `tests/x86/hello-x86.c` | `hello-x86.exe`, the 32-bit (WoW64) smoke test, built in CI | GPL-3.0-or-later with the DanPort Converter Exception |
| [DanPort](https://api.github.com/repositories/1175417517) input (`app/DanPort/HardwareInput.swift`, `ContentView.swift`, `PadKeyboardMouse.swift` at 65e6fe8f) | Touch-as-mouse gestures, the HID usage to virtual-key table, text entry as key presses and the right-stick mouse, ported to `App/Sources/Engine/GameInput.swift` and `ControllerBridge.swift` | GPL-3.0-or-later with the DanPort Converter Exception |
| [DanPort](https://api.github.com/repositories/1175417517) app-side Wine sources (`app/DanPort`, at `engine/wine/PIN`) | The Wine bridge and iOS display driver compiled into the app, with small additions applied by `engine/wine/stage-app.sh`: the no-JIT CPU modules and session reuse (`engine/wine/patches/session_reuse.py`, docs/SESSION_REUSE.md) in `WineProcessBridge.m`; in `Winios/Winios.m`, the game-mode overlay above the game view and the presenting window's client rect, dropped with a new session | GPL-3.0-or-later with the DanPort Converter Exception |
| [DanPort](https://api.github.com/repositories/1175417517) Quit game (`app/DanPort/Library.swift` `requestQuit`, at 65e6fe8f) | The game menu's Quit game as Alt+F4 through the game's own input, so it can save and confirm, ported to `App/Sources/UI/LibraryView.swift` | GPL-3.0-or-later with the DanPort Converter Exception |
| [DanPort](https://api.github.com/repositories/1175417517) Steam Cloud (`app/DanPort/SteamCloud.swift` and the cloud part of `SteamOwnedLibrary.swift`, at 65e6fe8f) | Steam Cloud service messages and parsing, the cloud-path to Wine-prefix mapping, the comparison and the record-based sync decisions, ported to `App/Sources/Steam/SteamCloudCore.swift` and `SteamCloudSync.swift` with PocketGamesNoJ's stricter rules (docs/STEAM_CLOUD.md) | GPL-3.0-or-later with the DanPort Converter Exception |

Steam is a trademark of Valve Corporation. iPhone, iOS and Metal are trademarks of Apple Inc.
PocketGamesNoJ is not affiliated with Valve or Apple.

Modifications for PocketGames No J are maintained by Dan. Original third-party author and license notices remain unchanged.

The upstream port namespace is normalized to DanPort in this repository. Original author copyright notices and license permissions are retained. Original names in unmodified upstream legal documents are preserved for attribution.

## Additional libraries in the assembled app

The complete, offline license texts and component notices are bundled in
`App/Resources/Legal` and accessible in Settings → About → Open Source Licenses.
The bundle includes original copyright holders' names; Dan is credited for
maintaining PocketGames No J, without replacing those third-party notices.

| Component | License / attribution | Source used by the build |
|---|---|---|
| Blink (optional interpreter) | ISC; Copyright 2022 Justine Alexandra Roberts Tunney | https://github.com/jart/blink at `f006a4fc6f9b8de9272504fdff0dbbe5ce5dc580` |
| Zstandard educational decoder | BSD-3-Clause selected; Meta Platforms, Inc. and affiliates | Vendored `App/Sources/Steam/SwiftSteam/zstd_edu.c` and `.h`; full notice bundled |
| LLVM | Apache-2.0 with LLVM exceptions, including notices in its license text | https://github.com/llvm/llvm-project/releases/tag/llvmorg-15.0.7 |
| FreeType | FreeType Project License selected | https://github.com/freetype/freetype/tree/VER-2-13-3 |
| GMP 6.3.0 | LGPL-3.0-or-later selected; original authors listed in bundled AUTHORS | Pinned port's `build/gnutls-ios/src/gmp-6.3.0.tar.xz` |
| Nettle / Hogweed 3.10.1 | LGPL-3.0-or-later selected; original authors listed in bundled AUTHORS | Pinned port's `build/gnutls-ios/src/nettle-3.10.1.tar.gz` |
| GnuTLS 3.8.9 | LGPL-2.1-or-later for the library; bundled author notices retained | Pinned port's `build/gnutls-ios/src/gnutls-3.8.9.tar.xz`; bundled libtasn1/unistring retain their own notices |
| FFmpeg 7.1.1 libraries | LGPL-2.1-or-later configuration; GPL, nonfree and version3 components disabled | Pinned port's `build/ffmpeg/src/ffmpeg-7.1.1.tar.xz`; configuration in `build/ffmpeg/build.sh` |
| libxml2 / libxslt | MIT; Daniel Veillard and contributors, as reproduced in bundled notices | Bundled with the pinned Wine source |
| NVAPI headers | MIT; NVIDIA Corporation and affiliates | Pinned DXMT source; no NVIDIA driver binary is supplied |
| fmt | MIT; copyright holders as reproduced in bundled notice | Pinned runtime sources |
| Dock's MinGW-w64 and LLVM runtime | Per-component notices bundled in the app | Dock commit `e00078410845eb41d2618edd5e3ff0879a4c0735`; full runtime notices bundled |
| Apple Metal Shader Converter | Apple's proprietary agreement; headers under their separate bundled license | Converter agreement, header license and distribution notice reproduced in full; the GPL exception does not license Apple's code |
| Apple system libraries, including liblzma and zlib | Provided by the operating system under their respective terms | Dynamically linked SDK libraries; not redistributed as copies in this app |

Portions of this software are copyright © 2024 The FreeType Project
(www.freetype.org). All rights reserved.

### Verified Wine revision

Wine commit `257f271cfffed9f22f7987cac53bc00095d092fe` identifies itself as
**LGPL-2.1-or-later**, including its iOS fork modifications and separately
credited contributors. Its original LICENSE, AUTHORS and fork licensing notice
are reproduced in the legal bundle. Older port documentation describing a
GPL-converted Wine branch does not describe this pinned revision.

### Corresponding source and modifications

PocketGames source, the dependency pins, build instructions and local patches
are available at https://github.com/aghjkshdsj/PocketGames-No-J.
Each built app records its exact source commit in `Legal/build-info.json` and
links to that revision. Wine and DXMT pins are in `engine/wine/PIN` and
`engine/dxmt/PIN`; their source port is
https://api.github.com/repositories/1175417517 at
`65e6fe8f0da45b28b610c71fda9791e89d1060a6`.
The port includes the exact GMP, Nettle, GnuTLS and FFmpeg source archives and
their build scripts. The legal index records immutable upstream document URLs.

PocketGames modifications include interpreter integration, platform namespace
changes outside legal texts, Wine session/input/loader patches, DXMT resource
ownership patches and the two Dock patches in `engine/pedylib`. See those build
scripts and patches for the preferred form of the changes.

Valve's Steam client and game files, downloaded separately by users, are not
licensed by PocketGames' GPL. Access and use remain subject to Valve's and the
respective publishers' terms. No game license is granted by this notice.

Including these notices does not grant additional third-party rights or certify
App Store compatibility. Before store distribution, verify complete
corresponding-source delivery, applicable LGPL replacement/relinking rights,
Apple converter redistribution terms, and compatibility with the actual store
distribution terms. See `docs/APP_STORE_LICENSING.md`.
