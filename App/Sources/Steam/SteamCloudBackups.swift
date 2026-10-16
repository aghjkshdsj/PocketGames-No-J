// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation

// MARK: - Backups

/// One backup folder: Documents/save-backups/<App ID>/<time>/, with the saved files under
/// device/ (this device's copies a download or a restore replaced) and cloud/ (the cloud's copies
/// an upload replaced; Steam keeps none), and backup.json, which Restore reads. The Files app
/// shows the folder (On My iPhone › PocketGamesNoJ › save-backups).
struct SteamCloudBackup: Codable, Identifiable, Equatable, Sendable {
    struct File: Codable, Equatable, Sendable {
        /// The cloud path (%Root%...), which says where the file goes back.
        var cloudPath: String
        /// Where the copy is, relative to the backup folder.
        var stored: String
        /// "device" or "cloud".
        var side: String
        var size: UInt64
        var sha: String
        /// The file's own modification time (Unix seconds).
        var time: UInt64
    }
    var appID: Int
    var created: Date
    var reason: String
    var files: [File]
    /// The folder's name (its time), not stored.
    var folder = ""

    var id: String { folder }
    private enum CodingKeys: String, CodingKey { case appID, created, reason, files }
}

enum SteamCloudBackupError: LocalizedError {
    case invalidPath, missingBackup
    var errorDescription: String? {
        switch self {
        case .invalidPath: return "The backup location is invalid. No backup was deleted."
        case .missingBackup: return "That backup is no longer available."
        }
    }
}

enum SteamCloudBackups {
    static var root: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("save-backups", isDirectory: true)
    }
    static func folder(_ appID: Int, root: URL = SteamCloudBackups.root) -> URL {
        root.appendingPathComponent(String(appID), isDirectory: true)
    }

    /// Deletion and publication stay inside one game's backup directory, even
    /// if Files has been used to replace a directory with a symbolic link.
    static func checkedFolder(_ appID: Int, name: String, root: URL = SteamCloudBackups.root) throws -> URL {
        guard appID > 0, UInt64(appID) <= UInt64(UInt32.max), !name.isEmpty,
              name != ".", name != "..", !name.contains("/"), !name.contains("\\"),
              !name.contains(":"), !name.contains("\0") else { throw SteamCloudBackupError.invalidPath }
        let game = folder(appID, root: root).standardizedFileURL
        let target = game.appendingPathComponent(name, isDirectory: true).standardizedFileURL
        for path in [game, target] {
            if (try? path.resourceValues(forKeys: [.isSymbolicLinkKey]))?.isSymbolicLink == true {
                throw SteamCloudBackupError.invalidPath
            }
        }
        guard game.resolvingSymlinksInPath().deletingLastPathComponent().path == root.resolvingSymlinksInPath().standardizedFileURL.path,
              target.resolvingSymlinksInPath().deletingLastPathComponent().path == game.resolvingSymlinksInPath().path else {
            throw SteamCloudBackupError.invalidPath
        }
        return target
    }

    /// Collects the files of one backup; the folder and its manifest are written as files arrive.
    final class Writer {
        let appID: Int
        let reason: String
        private(set) var files: [SteamCloudBackup.File] = []
        private var url: URL?
        private var created = Date()
        private let backupRoot: URL
        private var finished = false

        init(appID: Int, reason: String, root: URL = SteamCloudBackups.root) {
            self.appID = appID; self.reason = reason; self.backupRoot = root
        }

        var isEmpty: Bool { files.isEmpty }
        var folderName: String? { url?.lastPathComponent }

        deinit {
            if !finished, let url, url.lastPathComponent.hasPrefix(".pending-"),
               let checked = try? SteamCloudBackups.checkedFolder(appID, name: url.lastPathComponent, root: backupRoot) {
                try? FileManager.default.removeItem(at: checked)
            }
        }

        private func ensureFolder() throws -> URL {
            if let url { return try SteamCloudBackups.checkedFolder(appID, name: url.lastPathComponent, root: backupRoot) }
            created = Date()
            let made = try SteamCloudBackups.checkedFolder(appID, name: ".pending-" + UUID().uuidString, root: backupRoot)
            try FileManager.default.createDirectory(at: made, withIntermediateDirectories: true)
            url = made
            return made
        }

        /// Copies `data` (one side's copy of the save at `cloudPath`) into the backup and writes the
        /// manifest. Throws when it cannot: the caller then changes nothing.
        func add(_ data: Data, cloudPath: String, side: String, time: UInt64) throws {
            guard !finished, side == "device" || side == "cloud" else { throw SteamCloudBackupError.invalidPath }
            let folder = try ensureFolder()
            let (rootName, rest) = SteamCloudPaths.split(cloudPath)
            var parts = [side, rootName ?? "remote"]
            parts += rest.replacingOccurrences(of: "\\", with: "/").split(separator: "/").map(String.init)
                .filter { $0 != "." && $0 != ".." && !$0.isEmpty }
            let stored = parts.joined(separator: "/")
            let target = folder.appendingPathComponent(stored)
            try FileManager.default.createDirectory(at: target.deletingLastPathComponent(), withIntermediateDirectories: true)
            try data.write(to: target, options: .atomic)
            if time > 0 {
                try? FileManager.default.setAttributes([.modificationDate: Date(timeIntervalSince1970: TimeInterval(time))], ofItemAtPath: target.path)
            }
            files.append(.init(cloudPath: cloudPath, stored: stored, side: side, size: UInt64(data.count),
                               sha: SteamCloudRecord.hex(SteamCloudTransfer.sha1(data)), time: time))
            let manifest = SteamCloudBackup(appID: appID, created: created, reason: reason, files: files)
            let encoder = JSONEncoder()
            encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
            encoder.dateEncodingStrategy = .iso8601
            try encoder.encode(manifest).write(to: folder.appendingPathComponent("backup.json"), options: .atomic)
        }

        /// Publish only a fully written set, then keep the newest five. A failed
        /// or interrupted staging backup never evicts a completed backup.
        func finish() throws {
            guard !finished, let pending = url else { return }
            _ = try SteamCloudBackups.checkedFolder(appID, name: pending.lastPathComponent, root: backupRoot)
            let format = DateFormatter()
            format.locale = Locale(identifier: "en_US_POSIX")
            format.dateFormat = "yyyy-MM-dd HH-mm-ss"
            let stem = format.string(from: created)
            var name = stem, suffix = 2
            var destination = try SteamCloudBackups.checkedFolder(appID, name: name, root: backupRoot)
            while FileManager.default.fileExists(atPath: destination.path) {
                name = stem + " (\(suffix))"; suffix += 1
                destination = try SteamCloudBackups.checkedFolder(appID, name: name, root: backupRoot)
            }
            try FileManager.default.moveItem(at: pending, to: destination)
            url = destination
            finished = true
            try SteamCloudBackups.prune(appID, keeping: name, root: backupRoot)
        }
    }

    /// The game's backups, newest first.
    static func list(_ appID: Int, root: URL = SteamCloudBackups.root) -> [SteamCloudBackup] {
        let base = folder(appID, root: root)
        let names = (try? FileManager.default.contentsOfDirectory(atPath: base.path)) ?? []
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        var out: [SteamCloudBackup] = []
        for name in names where !name.hasPrefix(".") {
            guard let directory = try? checkedFolder(appID, name: name, root: root) else { continue }
            let manifest = directory.appendingPathComponent("backup.json")
            guard let data = try? Data(contentsOf: manifest), data.count < 8 << 20,
                  var backup = try? decoder.decode(SteamCloudBackup.self, from: data), backup.appID == appID else { continue }
            backup.folder = name
            out.append(backup)
        }
        return out.sorted { $0.created == $1.created ? $0.folder > $1.folder : $0.created > $1.created }
    }

    static func delete(_ appID: Int, _ backup: SteamCloudBackup, root: URL = SteamCloudBackups.root) throws {
        let target = try checkedFolder(appID, name: backup.folder, root: root)
        guard backup.appID == appID, list(appID, root: root).contains(where: { $0.folder == backup.folder }) else {
            throw SteamCloudBackupError.missingBackup
        }
        try FileManager.default.removeItem(at: target)
    }

    /// Remove the oldest completed sets once the sixth has been published.
    static func prune(_ appID: Int, keeping: String? = nil, root: URL = SteamCloudBackups.root) throws {
        let all = list(appID, root: root)
        let drop = SteamCloudBackupRetention.expired(all.map { ($0.folder, $0.created) }, keeping: keeping)
        for name in drop {
            guard let backup = all.first(where: { $0.folder == name }) else { continue }
            try delete(appID, backup, root: root)
        }
        if !drop.isEmpty { SteamLog.event("[steam-cloud] app=\(appID) backups pruned=\(drop.count) kept=\(all.count - drop.count)") }
    }
}

