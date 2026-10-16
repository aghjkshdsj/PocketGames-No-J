// SPDX-License-Identifier: GPL-3.0-or-later
import SwiftUI

@main
struct PocketGamesNoJApp: App {
    @StateObject private var settings = Settings()
    @StateObject private var engine = EngineController()
    @StateObject private var device = DeviceInfo()
    @StateObject private var wine = WineController()
    @StateObject private var logs = LogStore.shared
    @ObservedObject private var crashes = CrashReporter.shared
    @Environment(\.scenePhase) private var phase

    init() { dlog("PocketGames No J by Dan") }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(settings)
                .environmentObject(engine)
                .environmentObject(device)
                .environmentObject(wine)
                .environmentObject(logs)
                .onOpenURL { url in dlog("[app] opened by \(url.absoluteString)") }
                .sheet(item: $crashes.report) { CrashReportSheet(report: $0) }
                .onChange(of: phase) { _, newPhase in
                    if newPhase == .background { crashes.sceneActive(false) }
                    guard newPhase == .active else { return }
                    crashes.sceneActive(true)
                    device.refresh()
                    engine.start(settings: settings)
                }
                .onAppear {
                    crashes.sceneActive(true)
                    crashes.offerPreviousCrash()
                    ControllerBridge.shared.start()
                    GameInput.shared.start()
                    engine.start(settings: settings)
                }
        }
    }
}
