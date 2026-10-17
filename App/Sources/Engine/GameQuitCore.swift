// SPDX-License-Identifier: GPL-3.0-or-later

/// Quit waits for Wine's actual end notification. A timeout offers Force quit; it never
/// terminates a game which may still be saving or asking the player to confirm its exit.
struct GameQuitFlow {
    enum Phase: Equatable { case idle, waiting, needsForce, forcing, forceFailed }
    private(set) var phase = Phase.idle
    private var generation = 0

    var pending: Bool { phase != .idle }
    var canQuit: Bool { phase == .idle || phase == .needsForce }
    var canForce: Bool { phase != .forcing }

    mutating func requestQuit() -> Int? {
        guard canQuit else { return nil }
        generation += 1
        phase = .waiting
        return generation
    }

    @discardableResult
    mutating func quitTimedOut(_ attempt: Int) -> Bool {
        guard attempt == generation, phase == .waiting else { return false }
        phase = .needsForce
        return true
    }

    mutating func requestForce() -> Int? {
        guard canForce else { return nil }
        generation += 1
        phase = .forcing
        return generation
    }

    @discardableResult
    mutating func forceTimedOut(_ attempt: Int) -> Bool {
        guard attempt == generation, phase == .forcing else { return false }
        phase = .forceFailed
        return true
    }

    /// Invalidates callbacks even when the next game has the same title.
    @discardableResult
    mutating func sessionEnded() -> Bool {
        let requested = pending
        generation += 1
        phase = .idle
        return requested
    }
}
