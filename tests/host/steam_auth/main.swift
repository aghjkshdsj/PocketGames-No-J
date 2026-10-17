import Foundation

private enum Refusal: Error { case invalidCode, rateLimited }

@main
struct SteamAuthNetworkTests {
    static func main() async throws {
        let start = Date(timeIntervalSince1970: 1000)
        var clock = start
        var requests = 0
        var retries = 0
        let approved = Data("approved-token-response".utf8)
        let recovered: Data? = try await SteamAuthNetwork.recoverPoll(
            until: start.addingTimeInterval(300), now: { clock },
            pause: { _ in clock = clock.addingTimeInterval(45) },
            onRetry: { error, count in
                precondition(error.code == .networkConnectionLost && count == 1)
                retries += 1
            }
        ) {
            requests += 1
            if requests == 1 { throw URLError(.networkConnectionLost) }
            return approved
        }
        precondition(recovered == approved && requests == 2 && retries == 1)

        // Persistent connection loss is bounded by the original deadline.
        for code in [URLError.Code.networkConnectionLost, .notConnectedToInternet, .timedOut] {
            clock = start; requests = 0
            let result: Data? = try await SteamAuthNetwork.recoverPoll(
                until: start.addingTimeInterval(5), now: { clock },
                pause: { seconds in clock = clock.addingTimeInterval(seconds) }
            ) {
                requests += 1
                throw URLError(code)
            }
            precondition(result == nil && requests == 3 && clock == start.addingTimeInterval(5))
        }

        // Returning after expiry cannot create a fresh polling window.
        requests = 0
        let expired: Data? = try await SteamAuthNetwork.recoverPoll(until: start, now: { start }) {
            requests += 1
            return approved
        }
        precondition(expired == nil && requests == 0)

        // Refusals, rate limits and cancellation never become network retries.
        let failures: [Error] = [Refusal.invalidCode, Refusal.rateLimited,
                                URLError(.cancelled), URLError(.serverCertificateUntrusted), CancellationError()]
        for failure in failures {
            requests = 0
            do {
                let _: Data? = try await SteamAuthNetwork.recoverPoll(
                    until: start.addingTimeInterval(300), now: { start },
                    pause: { _ in fatalError("A permanent failure must not retry") }
                ) {
                    requests += 1
                    throw failure
                }
                fatalError("Expected original failure")
            } catch {
                precondition(requests == 1)
                precondition(String(describing: error) == String(describing: failure))
            }
        }

        // Cancelling during the backoff stops before another HTTP request.
        requests = 0
        do {
            let _: Data? = try await SteamAuthNetwork.recoverPoll(
                until: start.addingTimeInterval(300), now: { start },
                pause: { _ in throw CancellationError() }
            ) {
                requests += 1
                throw URLError(.networkConnectionLost)
            }
            fatalError("Expected cancellation")
        } catch is CancellationError {
            precondition(requests == 1)
        }
        precondition(SteamAuthNetwork.message(for: URLError(.networkConnectionLost)) !=
                     SteamAuthNetwork.message(for: URLError(.notConnectedToInternet)))
        print("Steam auth: recovery after a 45-second interruption, bounded retries, expiry, refusals and cancellation passed")
    }
}
