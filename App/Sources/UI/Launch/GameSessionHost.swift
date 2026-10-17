// SPDX-License-Identifier: GPL-3.0-or-later
import SwiftUI

/// The running game's full-screen view and its menu (Resume, Controller, Touch mouse, the
/// on-screen controller, Hide game, Quit game / Force quit, Quit and close PocketGamesNoJ). On the root
/// view, so a game started anywhere shows here, and a hidden game comes back from any screen.
struct GameSessionHost: ViewModifier {
    @EnvironmentObject private var wine: WineController
    @ObservedObject private var session = GameSession.shared
    @ObservedObject private var pad = TouchPadOverlay.shared

    @State private var showGameMenu = false
    @State private var showControllerMenu = false
    @State private var showTouchMenu = false
    @State private var showPadMenu = false
    @State private var openingSubmenu = false   // the game menu closes before a submenu opens
    @State private var quit = GameQuitFlow()
    @State private var showQuitConfirmation = false
    @State private var showForceConfirmation = false
    @State private var showCloseConfirmation = false

    func body(content: Content) -> some View {
        content
            .fullScreenCover(isPresented: $session.shown) { gameSurface }
            .onChange(of: wine.state) { _, state in
                // The session ended (the game's own Quit, a crash, or a start that failed): close the
                // surface and its menus and go back to the app, where the status shows (and a crash
                // report after it). A launcher that starts its game and exits is not an end: 32-bit
                // sessions wait for the game.
                switch state {
                case .finished, .failed:
                    dlog("[ui] session ended: game view closed")
                    showGameMenu = false; showControllerMenu = false; showTouchMenu = false; showPadMenu = false
                    showQuitConfirmation = false; showForceConfirmation = false; showCloseConfirmation = false
                    openingSubmenu = false
                    GameHostView.shared.isHidden = true
                    session.shown = false
                    session.title = ""
                    session.gameID = ""
                    GameHostView.shared.setStatus(nil)   // Quit game's "Closing…"
                    GameInput.shared.releaseAll("game ended")
                    TouchPadOverlay.shared.sessionEnded()
                    if quit.sessionEnded() { UIState.shared.show(.library) }
                default: break
                }
            }
    }

    /// Full-screen surface for a Windows program's Direct3D window, edge to edge.
    /// The menu button is drawn by GameHostView (the Metal host is above every
    /// SwiftUI view); while the menu is open the host is hidden so it shows.
    private var gameSurface: some View {
        GameSurfaceView()
            .ignoresSafeArea()
            .background(Color.black)
            .statusBarHidden()
            .persistentSystemOverlays(.hidden)
            .padScope("game")   // the app behind takes no focus while the game is up
            .onAppear {
                GameHostView.onMenu = {
                    guard session.shown, wine.isPlaying else { return }
                    dlog("[ui] game menu opening (surface shown \(session.shown), menu already open \(showGameMenu))")
                    // The menu is opened when something is wrong (a game that hangs while starting
                    // or quitting, build 162): where every thread of the 32-bit programs is, each time.
                    if wine.sessionKept, case .running = wine.state { mid_wow_thread_report("game menu opened") }
                    GameHostView.shared.isHidden = true
                    showGameMenu = true
                }
                TouchPadOverlay.shared.sessionShown(gameKey: session.gameID, mode: wine.sessionOverrides?.touchPad)
            }
            .glassDialog(session.title, isPresented: $showGameMenu, message: gameMenuMessage) {
                var b: [DialogButton] = [
                    DialogButton(title: "Resume"),
                ]
                if wine.sessionKept {
                    if quit.canQuit {
                        b.append(DialogButton(title: "Quit game (keep app open)") {
                            submenu { showQuitConfirmation = true }
                        })
                    }
                    if quit.canForce {
                        b.append(DialogButton(title: "Force quit game…", role: .destructive) {
                            submenu { showForceConfirmation = true }
                        })
                    }
                }
                b += [
                    DialogButton(title: "Controller: \(wine.padKeyboard ? "keyboard and mouse" : wine.padStyle.title)…") {
                        submenu { showControllerMenu = true }
                    },
                    DialogButton(title: "Touch mouse: \(Self.touchNames[GameInput.shared.touchMode] ?? "Off")…") {
                        submenu { showTouchMenu = true }
                    },
                    DialogButton(title: "On-screen controller: \(pad.visible ? "shown" : "hidden")…") {
                        submenu { showPadMenu = true }
                    },
                    DialogButton(title: "Hide game (keeps running)") { session.shown = false },
                ]
                b.append(DialogButton(title: "Quit game and close PocketGames No J…", role: .destructive) {
                    submenu { showCloseConfirmation = true }
                })
                return b
            }
            .glassDialog("Quit \(session.title)?", isPresented: $showQuitConfirmation,
                         message: "Save your progress first. This asks the game to close and keeps PocketGames open. If the game asks you to confirm, answer in the game. The library appears after the game exits.") {
                [DialogButton(title: "Quit game", role: .destructive) { requestQuit() }, .cancel()]
            }
            .glassDialog("Force quit \(session.title)?", isPresented: $showForceConfirmation,
                         message: "Ends the game's processes immediately. Unsaved progress will be lost. PocketGames stays open; Steam Cloud checks the saves already on disk after the game ends.") {
                [DialogButton(title: "Force quit game", role: .destructive) { forceQuit() }, .cancel()]
            }
            .glassDialog("Close PocketGames No J?", isPresented: $showCloseConfirmation,
                         message: "Stops the game and closes the app. Unsaved progress will be lost and Steam Cloud may not finish syncing.") {
                [DialogButton(title: "Close app", role: .destructive) { CrashReporter.shared.quitApp() }, .cancel()]
            }
            .glassDialog("Controller", isPresented: $showControllerMenu, message: Self.controllerMessage(wine)) {
                PadStyle.allCases.map { s in
                    DialogButton(title: (s == wine.padStyle && !wine.padKeyboard ? "✓ " : "") + s.title) {
                        if wine.padKeyboard { wine.setPadKeyboard(false) }
                        wine.setPadStyle(s)
                    }
                } + [
                    DialogButton(title: (wine.padKeyboard ? "✓ " : "") + "Controller as keyboard and mouse") { wine.setPadKeyboard(!wine.padKeyboard) },
                    .cancel(),
                ]
            }
            .glassDialog("Touch mouse", isPresented: $showTouchMenu,
                         message: "Off: touching the game does nothing, so holding the phone never clicks. A three-finger tap opens the game menu in every mode (with a controller: the Home button, or View + Menu held together). On-screen controller buttons keep working in every mode. The choice is remembered for this game.") {
                GameInput.TouchMode.allCases.map { mode in
                    DialogButton(title: (mode == GameInput.shared.touchMode ? "✓ " : "") + (Self.touchNames[mode] ?? mode.rawValue)) {
                        GameInput.shared.setTouchMode(mode)
                    }
                } + [.cancel()]
            }
            .glassDialog("On-screen controller", isPresented: $showPadMenu,
                         message: "Automatic shows it while no controller is connected and hides it when one connects. The choice is remembered for this game.") {
                TouchPadMode.allCases.map { mode in
                    DialogButton(title: (mode == pad.mode ? "✓ " : "") + Self.padNames[mode]!) { pad.setMode(mode, remember: true) }
                } + [
                    DialogButton(title: "Edit layout…") {
                        // The editor is full screen over the hidden game view.
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.35) { pad.editing = true }
                    },
                    .cancel(),
                ]
            }
            .fullScreenCover(isPresented: $pad.editing) {
                TouchLayoutEditor(gameKey: session.gameID.isEmpty ? nil : session.gameID, title: session.title)
            }
            .onChange(of: showGameMenu) { _, open in
                dlog("[ui] game menu \(open ? "shown" : "closed")")
                if !open, session.shown, !openingSubmenu, !pad.editing { GameHostView.shared.isHidden = false }
            }
            .onChange(of: showControllerMenu) { _, open in closedSubmenu(open) }
            .onChange(of: showTouchMenu) { _, open in closedSubmenu(open) }
            .onChange(of: showQuitConfirmation) { _, open in closedSubmenu(open) }
            .onChange(of: showForceConfirmation) { _, open in closedSubmenu(open) }
            .onChange(of: showCloseConfirmation) { _, open in closedSubmenu(open) }
            .onChange(of: showPadMenu) { _, open in
                if open { openingSubmenu = false }
                if !open, session.shown, !pad.editing {
                    // "Edit layout…" opens the editor right after this closes: stay hidden for it.
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                        if session.shown, !pad.editing, !showGameMenu { GameHostView.shared.isHidden = false }
                    }
                }
            }
            .onChange(of: pad.editing) { _, editing in
                if !editing, session.shown {
                    pad.reloadLayout()
                    GameHostView.shared.isHidden = false
                }
            }
    }

    private var gameMenuMessage: String {
        if wine.sessionKept {
            switch quit.phase {
            case .waiting, .needsForce:
                return "Waiting for \(session.title) to close. Resume to answer any in-game confirmation, or choose Force quit if it is stuck. PocketGames stays open."
            case .forcing:
                return "Ending \(session.title)'s processes. The library appears when Wine reports that the game has ended."
            case .forceFailed:
                return "\(session.title) has not ended. You can retry Force quit, or close the app if it remains stuck."
            case .idle:
                return "Quit game closes the game and returns to the library so you can play another. Save first and confirm in the game if it asks. Hide game keeps it running."
            }
        }
        return "The game is starting. Quit game becomes available when its Wine session is ready."
    }

    private func submenu(_ open: @escaping () -> Void) {
        openingSubmenu = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.35) {
            guard openingSubmenu, session.shown, wine.isPlaying else { return }
            open()
        }
    }

    private func closedSubmenu(_ open: Bool) {
        if open { openingSubmenu = false }
        if !open, session.shown { GameHostView.shared.isHidden = false }
    }

    /// Ask the game to save/confirm and exit. Only Wine's completion opens the library and
    /// triggers the existing Steam Cloud end-of-game sync; the timeout never kills the game.
    private func requestQuit() {
        guard wine.sessionKept, wine.isPlaying, let attempt = quit.requestQuit() else { return }
        dlog("[ui] quit requested: Alt+F4 to \(session.title)")
        mid_post_key(0x12, 1); mid_post_key(0x73, 1)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.08) { mid_post_key(0x73, 0); mid_post_key(0x12, 0) }
        GameHostView.shared.setStatus("Closing \(session.title)… confirm in the game if it asks")
        DispatchQueue.main.asyncAfter(deadline: .now() + 10) {
            guard wine.isPlaying, quit.quitTimedOut(attempt) else { return }
            dlog("[ui] game still running after Quit game; waiting for the player")
            mid_wow_thread_report("Quit game: still running")
            GameHostView.shared.setStatus("Still running: confirm in the game, or open the menu for Force quit")
        }
    }

    /// The confirmed force action ends programs through the existing wineserver path; it
    /// keeps system processes and waits for the native cleanup before offering another launch.
    private func forceQuit() {
        guard wine.isPlaying, quit.canForce else { return }
        dlog("[ui] force quit requested for \(session.title)")
        guard wine.forceQuit() else {
            GameHostView.shared.setStatus("Force quit was not accepted. Open the game menu to retry.")
            return
        }
        guard let attempt = quit.requestForce() else { return }
        GameHostView.shared.setStatus("Ending \(session.title)…")
        DispatchQueue.main.asyncAfter(deadline: .now() + 8) {
            guard wine.isPlaying, quit.forceTimedOut(attempt) else { return }
            mid_wow_thread_report("Force quit: still running")
            GameHostView.shared.setStatus("Game has not ended. Open the menu to retry Force quit or close the app.")
        }
    }

    /// What a switch does to the running game.
    static func controllerMessage(_ wine: WineController) -> String {
        var m = "Xbox and PlayStation switch at once: your controller's buttons, the on-screen controller and what the game reads. Games that only read Xbox controllers (XInput) keep working either way. A game with PlayStation support shows PlayStation buttons when it finds the DualSense, which most games look for when they start: if it does not change now, it will the next time this game starts (PocketGames No J stays open)."
        if !wine.playStationAvailable {
            m += " This Wine session started without the DualSense (an older Wine build): it reaches games after PocketGames No J restarts."
        }
        m += " Keyboard and mouse: the controller presses keys and moves the mouse, for games without controller support. Remembered for this game; Settings › Controls has the default."
        return m
    }
    static let touchNames: [GameInput.TouchMode: String] = [
        .off: "Off", .trackpad: "Trackpad with cursor", .direct: "Tap where you click",
    ]
    static let padNames: [TouchPadMode: String] = [
        .auto: "Automatic (hidden with a controller)", .always: "Always shown", .off: "Off",
    ]
}

/// "Return to <game>": a game hidden with the game menu's Hide game is still running. Shown at the
/// top of every page while that is so.
struct ReturnToGameBar: View {
    @EnvironmentObject private var wine: WineController
    @ObservedObject private var session = GameSession.shared

    var body: some View {
        if wine.isPlaying, !session.shown, !session.title.isEmpty {
            Button {
                dlog("[ui] return to \(session.title)")
                session.shown = true
            } label: {
                HStack(spacing: 10) {
                    Image(systemName: "play.fill")
                    Text("Return to \(session.title)").lineLimit(1)
                    Spacer(minLength: 0)
                    Text("Running").font(.caption.weight(.semibold)).foregroundStyle(Glass.text.opacity(0.7))
                }
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(Glass.text)
                .padding(.horizontal, 18).frame(height: 44)
                .glassCapsule(highlighted: true)
            }
            .buttonStyle(.plain)
            .accessibilityHint("Shows the running game")
            .padFocus("shell.return", radius: 22, preferred: true) { session.shown = true }
        }
    }
}
