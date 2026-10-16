import Foundation

// File storage tests use a deterministic stand-in; the app supplies SHA-1.
enum SteamCloudTransfer {
    static func sha1(_ data: Data) -> Data { Data(data.reversed()) }
}
enum SteamLog { static func event(_ text: String) { print(text) } }

let fm = FileManager.default
let temporary = fm.temporaryDirectory.appendingPathComponent("pocketgames-backups-" + UUID().uuidString, isDirectory: true)
let backupRoot = temporary.appendingPathComponent("save-backups", isDirectory: true)
try fm.createDirectory(at: backupRoot, withIntermediateDirectories: true)
defer { try? fm.removeItem(at: temporary) }
let app = 2019300

func make(_ appID: Int, _ number: Int) throws -> SteamCloudBackup {
    let writer = SteamCloudBackups.Writer(appID: appID, reason: "test \(number)", root: backupRoot)
    try writer.add(Data("save \(number)".utf8), cloudPath: "%WinAppDataLocal%dokimon/save.sav", side: "device", time: 1)
    try writer.add(Data("world \(number)".utf8), cloudPath: "%WinAppDataLocal%dokimon/world_save.sav", side: "device", time: 1)
    try writer.finish()
    return SteamCloudBackups.list(appID, root: backupRoot).first { $0.folder == writer.folderName }!
}

let other = try make(480, 1)
var original: [SteamCloudBackup] = []
for n in 1...5 { original.append(try make(app, n)) }
precondition(SteamCloudBackups.list(app, root: backupRoot).count == 5)
precondition(SteamCloudBackups.list(app, root: backupRoot).allSatisfy { $0.files.count == 2 })

var interrupted: SteamCloudBackups.Writer? = .init(appID: app, reason: "incomplete", root: backupRoot)
try interrupted!.add(Data("partial".utf8), cloudPath: "%WinAppDataLocal%dokimon/save.sav", side: "device", time: 1)
precondition(SteamCloudBackups.list(app, root: backupRoot).count == 5, "pending backup must not evict completed sets")
interrupted = nil
let afterInterruption = try fm.contentsOfDirectory(atPath: SteamCloudBackups.folder(app, root: backupRoot).path)
precondition(afterInterruption.allSatisfy { !$0.hasPrefix(".pending-") })

let sixth = try make(app, 6)
let kept = SteamCloudBackups.list(app, root: backupRoot)
precondition(kept.count == 5 && kept.contains { $0.folder == sixth.folder })
precondition(!kept.contains { $0.folder == original[0].folder }, "oldest set must be removed")
precondition(SteamCloudBackups.list(480, root: backupRoot) == [other], "another game's backups must stay")

let currentSave = temporary.appendingPathComponent("current-save.sav")
try Data("current progress".utf8).write(to: currentSave)
try SteamCloudBackups.delete(app, sixth, root: backupRoot)
precondition(SteamCloudBackups.list(app, root: backupRoot).count == 4)
let preservedSave = try Data(contentsOf: currentSave)
precondition(preservedSave == Data("current progress".utf8))
precondition(SteamCloudBackups.list(480, root: backupRoot) == [other])
for number in 7...25 { _ = try make(app, number) }
let rapid = SteamCloudBackups.list(app, root: backupRoot)
precondition(Set(rapid.map(\.reason)) == Set((21...25).map { "test \($0)" }), "rapid backups must retain the five latest sets even when folder names are reused")
precondition(rapid.allSatisfy { $0.preciseCreated != nil })
do {
    try SteamCloudBackups.delete(app, sixth, root: backupRoot)
    fatalError("A stale selection must fail")
} catch SteamCloudBackupError.missingBackup {}

for name in ["..", ".", "../outside", "/outside", "a/b", "a\\b", "a:b", "bad\0name"] {
    do {
        _ = try SteamCloudBackups.checkedFolder(app, name: name, root: backupRoot)
        fatalError("Unsafe path accepted: \(name)")
    } catch SteamCloudBackupError.invalidPath {}
}
let outside = temporary.appendingPathComponent("outside", isDirectory: true)
try fm.createDirectory(at: outside, withIntermediateDirectories: true)
let sentinel = outside.appendingPathComponent("keep.sav")
try Data("keep".utf8).write(to: sentinel)
let linkedBackup = SteamCloudBackups.folder(app, root: backupRoot).appendingPathComponent("linked")
try fm.createSymbolicLink(at: linkedBackup, withDestinationURL: outside)
do {
    _ = try SteamCloudBackups.checkedFolder(app, name: "linked", root: backupRoot)
    fatalError("A linked backup must not be accepted")
} catch SteamCloudBackupError.invalidPath {}
let linkedGame = SteamCloudBackups.folder(999, root: backupRoot)
try fm.createSymbolicLink(at: linkedGame, withDestinationURL: SteamCloudBackups.folder(480, root: backupRoot))
do {
    _ = try SteamCloudBackups.checkedFolder(999, name: other.folder, root: backupRoot)
    fatalError("A linked game must not be accepted")
} catch SteamCloudBackupError.invalidPath {}
precondition(fm.fileExists(atPath: sentinel.path))
precondition(SteamCloudBackups.list(480, root: backupRoot) == [other])
print("Steam backup storage: five-set cap, completed publication, interrupted staging, deletion and path boundaries passed")
