# SwiftSteam (vendored)

Native Steam client in Swift: sign-in (password + Steam Guard, QR), the CM
connection, owned library, product info, depot downloader and content decoders.

Copied unchanged from [DanPort](https://api.github.com/repositories/1175417517)
`app/DanPort/SwiftSteam/` at commit `65e6fe8f0da45b28b610c71fda9791e89d1060a6`
(the commit pinned in `engine/wine/PIN` and `engine/dxmt/PIN`). Licence:
GPL-3.0-or-later with the DanPort Converter Exception, as in each file's header.

`../SteamInstall.swift` and `../SteamKeyValues.swift` (install paths, VDF
parser) come unchanged from the same commit's `app/DanPort/`; SwiftSteam uses
them. PocketGames No J supplies the two app types it uses (`SteamConfig`, `LogStore.log`)
in `../SteamShims.swift`. Keep local changes out of this folder so it can be
refreshed from a newer DanPort commit.

The one PocketGamesNoJ change (keep it when refreshing): `Core/SteamSession.swift` adds
`callServiceMethodResult`, which returns the response header's EResult with the body
(`callServiceMethod` now calls it). Steam Cloud saves (`../SteamCloudSync.swift`) must tell
a refused request from an empty answer.
