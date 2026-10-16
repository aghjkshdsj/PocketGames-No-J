# Privacy implementation and remaining review

The manifest covers the first-party uses identified below. It is not a completed
privacy declaration for every runtime, imported game or third-party service.
`NSPrivacyCollectedDataTypes` is intentionally absent pending that review; do
not interpret omission as a verified "Data Not Collected" App Store answer.

| API category / declared reasons | Observed use |
| --- | --- |
| UserDefaults / CA92.1 | App settings, controller preferences and the app's own Steam server/cache state. |
| FileTimestamp / C617.1, 3B52.1 | Metadata in the app container and folders granted through the document picker; import, download and save comparison. |
| DiskSpace / E174.1, 85F4.1 | DepotDownloader refuses insufficient-space downloads; GameDetail and Storage display available capacity. |
| SystemBootTime / 35F9.1 | Elapsed intervals for benchmarks, controller gestures and input timing. |

Review the linked Wine and graphics code separately, especially guest-facing
uptime, file metadata and filesystem capacity interfaces. A host API reason is
not blanket permission for arbitrary guest uses or transmission of restricted
device information. Verify allowed uses against Apple's current descriptions
before finalizing the submitted binary. No reason for fingerprinting is declared.

## Data flows to verify for App Store privacy answers

- Steam authentication: account name, Steam ID and authentication/Guard/QR
  exchanges with Valve. SteamTokenStore stores refresh/access tokens using
  `kSecAttrAccessibleWhenUnlockedThisDeviceOnly`. Sign out removes that entry.
- Library/content: owned-game requests, download requests, game IDs and artwork
  requests to Valve and its CDN providers. Network requests reveal an IP address.
- Steam Cloud: save file contents, paths, timestamps, sizes and account/file
  identifiers to Valve and its storage providers. The app's global Cloud toggle
  stops its synchronization; it does not govern a game's own network code.
- Diagnostics: local logs and explicit Share destinations. Examine exported logs
  for identifying data; no automatic project log upload was found. Reports a
  user sends to project support have different retention from local logs.
- Game traffic: guest programs and Valve's client can access online services.
  Review the actual guest-to-native boundary, service permissions and consent.

Likely privacy-label areas to evaluate include User ID, Other User Content and
Diagnostics. Determine linked-to-user status, purpose, collection/retention and
any applicable platform exception from actual processing. Neither optional Steam
use nor absence of a project backend proves that no data is collected by third
parties. Do not select advertising/tracking purposes without evidence.

The bundled policy describes current source behavior. Before publishing, confirm
the seller identity, confidential support channel, retention handling for support
requests and final list of service providers. Check the final generated privacy
report and App Store Connect answers against the policy and submitted artifact.

Sources: [Apple privacy manifests](https://developer.apple.com/documentation/bundleresources/privacy-manifest-files),
[required API reasons](https://developer.apple.com/documentation/bundleresources/app-privacy-configuration/nsprivacyaccessedapitypes/nsprivacyaccessedapitypereasons),
[Valve privacy](https://store.steampowered.com/privacy_agreement/).
