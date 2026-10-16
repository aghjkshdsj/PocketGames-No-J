// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation

/// Persistent user settings (UserDefaults).
final class Settings: ObservableObject {
    private let d = UserDefaults.standard

    @Published var showHUD: Bool { didSet { d.set(showHUD, forKey: "showHUD") } }
    @Published var frameCap: Int { didSet { d.set(frameCap, forKey: "frameCap") } }
    /// Interpreter, run the built-in x86-64 Linux programs with FXR instead of FXI (experimental).
    /// Windows programs use winFXR.
    @Published var useFXR: Bool { didSet { d.set(useFXR, forKey: "useFXR") } }
    /// The interpreter engine for the built-in x86-64 Linux programs.
    var linuxMode: RunMode { useFXR ? .fxr : .interpreter }
    /// Interpreter, start Windows games with no audio device (Wine's mmdevapi disabled), so the
    /// game's audio engine does not decode and mix in the interpreter. Read at launch.
    @Published var muteGameAudio: Bool { didSet { d.set(muteGameAudio, forKey: "muteGameAudio") } }
    /// Interpreter, run Windows games' x64 code with FXR (on by default since it can run every 64-bit
    /// game of a kept session, docs/FXR.md) instead of FXI. Read when a game starts.
    @Published var winFXR: Bool { didSet { d.set(winFXR, forKey: "winFXR") } }
    /// Interpreter, keep the Wine session when a game ends, so the next game starts without
    /// closing PocketGamesNoJ (experimental, docs/SESSION_REUSE.md). Read at launch (WineController).
    @Published var sessionReuse: Bool { didSet { d.set(sessionReuse, forKey: "sessionReuse") } }
    /// How Steam games start: "ask" (a choice at every Play), "dock" (Steam Dock: Valve's own
    /// Steam client signs in and starts the game, for games that need Steam running) or "direct"
    /// (the game's program starts on its own: faster, DRM-free games).
    @Published var steamLaunchMode: String { didSet { d.set(steamLaunchMode, forKey: "steamLaunchMode") } }
    /// Steam Cloud saves: synced before a Steam game starts and after it ends (SteamCloudSync).
    @Published var steamCloud: Bool { didSet { d.set(steamCloud, forKey: "steamCloud") } }
    /// How Windows games see the controller: "xinput", "dinput" (XInput plus a
    /// DirectInput joystick) or "hid" (player 1 as a HID gamepad). Read at launch.
    @Published var controllerAPI: String { didSet { d.set(controllerAPI, forKey: "controllerAPI") } }

    /// Games: the Metal performance HUD over the game (frame rate, GPU time). Per game in Game settings.
    @Published var gameHUD: Bool { didSet { d.set(gameHUD, forKey: "gameHUD") } }
    /// Games: the virtual monitor's height (540, 720, 900, 1080). Read when Wine starts.
    @Published var monitorHeight: Int { didSet { d.set(monitorHeight, forKey: "monitorHeight") } }
    /// The on-screen controller: "auto" (while no controller is connected), "always" or "off".
    @Published var touchPadMode: String { didSet { d.set(touchPadMode, forKey: "touchPadMode") } }
    /// A light tap felt when an on-screen button is pressed.
    @Published var touchPadHaptics: Bool { didSet { d.set(touchPadHaptics, forKey: "touchPadHaptics") } }
    /// Player 1 for games without their own choice: "xbox" or "playstation" (PadPrefs).
    @Published var padStyle: String { didSet { d.set(padStyle, forKey: "padStyle") } }

    /// The defaults of every setting (also read by GameDefaults without a Settings object).
    static func registerDefaults(_ d: UserDefaults) {
        // Defaults for interpreter execution and the game library.
        d.register(defaults: ["showHUD": true, "frameCap": 120,
                              "useFXR": false, "muteGameAudio": false, "winFXR": true, "sessionReuse": false,
                              "steamLaunchMode": "ask", "steamCloud": true, "controllerAPI": "xinput",
                              "gameHUD": false, "monitorHeight": 720, "touchPadMode": "auto", "touchPadHaptics": true])
    }

    init() {
        Settings.registerDefaults(d)
        showHUD = d.bool(forKey: "showHUD")
        frameCap = d.integer(forKey: "frameCap")
        useFXR = d.bool(forKey: "useFXR")
        muteGameAudio = d.bool(forKey: "muteGameAudio")
        winFXR = d.bool(forKey: "winFXR")
        sessionReuse = d.bool(forKey: "sessionReuse")
        steamLaunchMode = d.string(forKey: "steamLaunchMode") ?? "ask"
        steamCloud = d.bool(forKey: "steamCloud")
        controllerAPI = d.string(forKey: "controllerAPI") ?? "xinput"
        gameHUD = d.bool(forKey: "gameHUD")
        monitorHeight = d.integer(forKey: "monitorHeight")
        touchPadMode = d.string(forKey: "touchPadMode") ?? "auto"
        touchPadHaptics = d.bool(forKey: "touchPadHaptics")
        padStyle = PadPrefs.defaultStyle.rawValue
    }
}
