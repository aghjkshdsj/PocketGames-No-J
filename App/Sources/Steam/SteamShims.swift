// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation

/// SwiftSteam's optional configuration shim. Missing values fall back to the process environment.
enum SteamConfig {
    static func get(_ key: String) -> String? { nil }
}

extension LogStore {
    /// SwiftSteam logs through `LogStore.shared.log(_:)`.
    func log(_ message: String) { LogStore.log(message) }
}
