# Steam sign-in connection-loss recovery

The build 9 device report recorded three `url--1005` sign-in failures (two
password attempts and one QR attempt), each after app-inactive messages. A
subsequent password attempt succeeded and retrieved 226 owned Windows games.
The log contains no expired-session result. It does not prove which request
failed or why the connection was interrupted. Switching apps for Steam Guard
is consistent with this sequence; reproducing it on-device is still required.

Previously, one lost status-poll connection ended the entire sign-in and removed
the Guard/QR prompt. The UI incorrectly grouped a lost connection with an
offline device as "No internet connection."

`SteamAuthAPI.poll` now retries temporary connection-loss, offline and timeout
errors while retaining the same serialized client/request identifiers and the
original deadline. Password sessions keep their five-minute deadline; QR uses
a ten-minute wall-clock deadline, including interruption time. Cancellation,
expired/refused sessions, rate limits, certificate failures and decoding errors
are not retried. Password/session-creation and Guard-code submission requests
are not automatically replayed. A failed Guard-code submission keeps its prompt
available for the user's next attempt.

The retry log identifies only the polling stage and numeric error, never request
bodies, account names, passwords or tokens. The lost-connection message now says
that the connection was interrupted rather than asserting the device is offline.

Host tests simulate return after a 45-second interruption, continuing loss until
the original deadline, expiry, permanent refusals and cancellation. On-device
acceptance still requires switching to Steam for approval for at least 30–60
seconds, returning to complete sign-in, cancellation/start-over, a genuinely
offline attempt and library retrieval. Downloads, launching with Steam and cloud
saves require their own tests; library retrieval alone does not establish those.

Apple reference: [URLError.networkConnectionLost](https://developer.apple.com/documentation/foundation/urlerror/networkconnectionlost).
