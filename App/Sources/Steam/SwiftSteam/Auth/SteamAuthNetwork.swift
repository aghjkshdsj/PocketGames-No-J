// SPDX-License-Identifier: GPL-3.0-or-later
import Foundation

/// Retry only the existing session's status poll. Do not replay password/session
/// creation or Steam Guard code submissions whose server-side result is unknown.
enum SteamAuthNetwork {
    private static let recoverableCodes: Set<URLError.Code> = [
        .networkConnectionLost, .notConnectedToInternet, .timedOut
    ]

    static func recoverPoll<Value>(
        until deadline: Date,
        now: () -> Date = { Date() },
        pause: (TimeInterval) async throws -> Void = { seconds in
            try await Task.sleep(nanoseconds: UInt64(seconds * 1_000_000_000))
        },
        onRetry: (URLError, Int) -> Void = { _, _ in },
        operation: () async throws -> Value
    ) async throws -> Value? {
        var retries = 0
        while now() < deadline {
            try Task.checkCancellation()
            do {
                let value = try await operation()
                try Task.checkCancellation()
                return value
            } catch {
                try Task.checkCancellation()
                guard let url = error as? URLError,
                      recoverableCodes.contains(url.code) else {
                    throw error
                }
                let remaining = deadline.timeIntervalSince(now())
                guard remaining > 0 else { return nil }
                retries += 1
                onRetry(url, retries)
                // A foreground return resumes this task and retries the same
                // poll without discarding Steam's client/request identifiers.
                try await pause(min(2, remaining))
            }
        }
        try Task.checkCancellation()
        return nil
    }

    static func message(for error: URLError) -> String {
        switch error.code {
        case .notConnectedToInternet:
            return "No internet connection. Connect and try again."
        case .networkConnectionLost:
            return "The connection to Steam was interrupted. Try again."
        case .timedOut:
            return "Steam did not respond in time. Try again."
        default:
            return "A network error occurred (\(error.code.rawValue)). Try again."
        }
    }
}
