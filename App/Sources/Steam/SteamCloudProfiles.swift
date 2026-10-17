// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation

/// A per-game selection of an existing Windows profile. Downloading a cloud
/// copy must not make its directory look like evidence that the game uses it.
/// No prefix registry, profile directory or save is modified by selection.
enum SteamCloudProfiles {
    /// Only the game/profile pair confirmed on-device. Explicit user choices
    /// take precedence; other games keep their existing automatic behavior.
    static func defaultName(appID: Int) -> String? {
        appID == 2019300 ? "mythic" : nil
    }

    /// Detect pre-existing progress without reading save contents. Unknown
    /// rules are treated conservatively until a manual transfer is confirmed.
    static func hasLocalSaveFiles(paths: SteamCloudPaths, rules: [SteamCloudSaveRule]) -> Bool {
        guard !rules.isEmpty else { return true }
        return !SteamCloudAudit.run(listing: SteamCloudListing(), rules: rules, paths: paths,
                                    sha1: { _ in nil }).entries.isEmpty
    }

    static func names(drive: URL) -> [String] {
        let users = drive.appendingPathComponent("users", isDirectory: true)
        guard (try? users.resourceValues(forKeys: [.isSymbolicLinkKey]))?.isSymbolicLink != true,
              let entries = try? FileManager.default.contentsOfDirectory(at: users,
                includingPropertiesForKeys: [.isDirectoryKey, .isSymbolicLinkKey]) else { return [] }
        return entries.compactMap { url -> String? in
            let name = url.lastPathComponent
            guard !name.hasPrefix("."), name.caseInsensitiveCompare("Public") != .orderedSame,
                  let values = try? url.resourceValues(forKeys: [.isDirectoryKey, .isSymbolicLinkKey]),
                  values.isDirectory == true, values.isSymbolicLink != true,
                  url.resolvingSymlinksInPath().deletingLastPathComponent().path == users.resolvingSymlinksInPath().path else { return nil }
            return name
        }.sorted { $0.localizedStandardCompare($1) == .orderedAscending }
    }

    static func folder(named name: String, drive: URL) -> URL? {
        guard !name.isEmpty, !name.contains("/"), !name.contains("\\"),
              !name.contains(":"), !name.contains("\0"), name != ".", name != ".." else { return nil }
        let matches = names(drive: drive).filter { $0.caseInsensitiveCompare(name) == .orderedSame }
        guard matches.count == 1 else { return nil }
        return drive.appendingPathComponent("users", isDirectory: true).appendingPathComponent(matches[0], isDirectory: true)
    }
}
