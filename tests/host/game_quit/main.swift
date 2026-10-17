// SPDX-License-Identifier: GPL-3.0-or-later
// No UIKit: exercise exit confirmation waits and stale callbacks across repeated games.
func expect(_ value: @autoclosure () -> Bool, _ message: String) {
    precondition(value(), message)
}

var quit = GameQuitFlow()
expect(!quit.pending, "a new game must not inherit a quit request")
let first = quit.requestQuit()!
expect(quit.pending, "wait for the real Wine completion before returning to the library")
expect(quit.requestQuit() == nil, "repeated Quit must not send another Alt+F4 or escalate")
expect(quit.quitTimedOut(first), "a slow quit should offer help")
expect(quit.phase == .needsForce, "timeout must wait for an explicit force confirmation")
expect(!quit.quitTimedOut(first), "a repeated timeout must do nothing")
let retryQuit = quit.requestQuit()!
expect(quit.phase == .waiting, "a player who cancelled the game's exit dialog can ask it to quit again")
expect(!quit.quitTimedOut(first), "the first graceful watchdog must not affect a retry")
expect(quit.quitTimedOut(retryQuit), "a retry still offers explicit Force quit if it hangs")
expect(quit.sessionEnded(), "a requested normal exit should return to the library")
expect(!quit.pending, "completion must allow the next launch")

let second = quit.requestQuit()!
expect(!quit.quitTimedOut(first), "an earlier game's timeout must not affect a new game")
let force = quit.requestForce()!
expect(!quit.quitTimedOut(second), "graceful timeout must not overwrite force progress")
expect(quit.requestForce() == nil, "only one force operation may be in flight")
expect(quit.forceTimedOut(force), "a stuck force action must permit retry")
let retry = quit.requestForce()!
expect(!quit.forceTimedOut(force), "an old force watchdog must not affect a retry")
expect(quit.sessionEnded(), "force completion should return to the library")

let third = quit.requestQuit()!
expect(!quit.forceTimedOut(retry), "force watchdog must not affect a later game of the same name")
expect(quit.phase == .waiting, "the later game is waiting for its own normal exit")
expect(quit.quitTimedOut(third), "the later game's own watchdog still works")
quit.sessionEnded()
expect(!quit.sessionEnded(), "a natural exit or startup failure without a request need not navigate")

let directForce = quit.requestForce()!
expect(quit.phase == .forcing, "a hung launch can be force-quit without Alt+F4 first")
expect(quit.sessionEnded(), "a direct force request is an explicit stop")
expect(!quit.forceTimedOut(directForce), "completion invalidates all force callbacks")
print("Game quit flow tests passed")
