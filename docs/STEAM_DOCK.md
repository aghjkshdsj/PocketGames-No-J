# Steam client host

With Steam starts a game through Valve's own Windows Steam client using `dockhost.exe`.
Without Steam starts its executable directly, suitable for games that do not require Steam.
The choice can be remembered per game. Steam Cloud sync runs before and after play.

The first client setup downloads pinned files from Valve and checks sizes and SHA-256 hashes.
Sign-in uses the account's refresh token in a one-use handoff. Startup can take several minutes
through the interpreter. The host prefers Valve's UDP/TCP transport and receives cached server
addresses from the native app. A failed setup reports an error rather than starting an unknown
client build. See `SteamDock.swift`, `SteamRuntime.swift` and `DockCMCache.swift`.

The host's original license and author notices are shipped with it; see THIRD-PARTY-NOTICES.md.
