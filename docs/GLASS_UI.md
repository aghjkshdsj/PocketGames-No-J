# App interface

The Home, Library and Downloads tabs share game artwork, search, settings and controller
navigation. `RootView.swift` hosts the shell. `GameLauncher.swift` handles custom games,
Steam launch choices and Cloud save conflicts; `GameSessionHost.swift` hosts running games.

Settings includes appearance, interpreter performance, controls, Steam, storage, logs and
About. About identifies the app as PocketGames No J by Dan. Performance compares the built-in
interpreters and signed Windows libraries with native CPU kernels and a Metal GPU stage.
