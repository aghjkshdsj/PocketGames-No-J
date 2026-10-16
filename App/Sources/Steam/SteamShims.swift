// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation

/// The two the upstream port app types SwiftSteam (vendored from the upstream port, see
/// SwiftSteam/README.md) reaches outside its own folder.

/// the upstream port reads `env.NAME` switches from Documents/madeira.cfg. PocketGamesNoJ has
/// no such file yet; SwiftSteam then falls back to the process environment.
enum the upstream portConfig {
    static func get(_ key: String) -> String? { nil }
}

extension LogStore {
    /// SwiftSteam logs through `LogStore.shared.log(_:)`.
    func log(_ message: String) { LogStore.log(message) }
}
