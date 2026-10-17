# App Store preparation — October 17, 2026

This branch is a preparation and regression-test candidate. Build 15 at
`a1d582b34be06ae5867cb1230b8c30167b7208b9` is the latest delivered baseline;
the owner reports everything looks good. Earlier tests confirmed Forager at
60 FPS and Dokimon With Steam, manual cloud download and manual cloud upload
on iPhone 15 Pro Max with iLoader. Automatic post-game upload was not separately
confirmed. Keep the working IPA while testing the framework migration described
in `FRAMEWORK_MIGRATION.md`. These results do not prove a changed native-library
layout works or that every game is supported.

## Implemented here

- Settings → About → Privacy opens an offline policy describing local storage,
  optional Steam authentication/downloads, cloud saves, sharing and deletion.
  The contact is officialpocketgame@gmail.com; optional GitHub privacy/support
  buttons are removed while required legal/source access remains. Publishing
  identity, public support/privacy URLs and mailbox delivery still need review.
- The app bundles a privacy manifest with the observed required API reasons.
  `PRIVACY_REVIEW.md` records the evidence and remaining data-flow review. It
  deliberately does not assert a completed "Data Not Collected" label.
- GameSurface no longer invokes `setDisplaySyncEnabled:`. Apple's documented
  property has macOS/Mac Catalyst availability, not iOS. The candidate requires
  on-device rendering and frame-pacing comparison with build 7.
- `audit_app_store.py` records structural blockers in each full IPA build. Its
  optional `--require-structural-pass` fails on those blockers. Normal sideload
  builds retain their existing packaging while the framework migration is tested.
- The optional `lgpl_validation` build input rebuilds the pinned GMP/Nettle/
  GnuTLS stack, introduces a diagnostic witness in GnuTLS session creation,
  relinks the app and requires that witness in the application executable.
  It uploads a separate IPA and rebuild evidence without publishing a release.
- The optional `framework_layout` validation builds an unsigned Xcode archive,
  migrates native libraries with loader/signing checks and requires a structural
  pass before and after signing. Four fresh runtime builds are required for
  the loader changes. On-device validation remains a separate gate.

## Remaining engineering gates

| Gate | Evidence still required |
| --- | --- |
| Native library packaging | Verify the opt-in framework candidate's archive, section preservation, code signing, module lookup and both 32-bit and 64-bit runtime paths. |
| Rendering regression | Install this candidate on the same phone, reproduce Forager startup, gameplay, audio and frame pacing; also run the built-in Direct3D samples. |
| Privacy | Finish required-API/data-flow review of linked runtimes and guest-facing APIs; finalize manifest collection declarations and App Store privacy answers, including Valve and CDN handling. |
| LGPL | Complete modified-library build, independent source reconstruction, necessary application materials and authorized-device installation/replacement tests; establish source equivalence of prebuilt guest DLLs. |
| Rights | Resolve GPL/store permission, exact converter beta terms and authorization for the integrated Steam services. See DISTRIBUTION_RIGHTS_REVIEW.md and APP_STORE_LICENSING.md. |
| Emulator review | Prepare content inventory/deep links, age controls and consent/service explanations appropriate to the actual features; resolve native API exposure with Apple before submission. |
| Distribution | Create a real archive/export configuration and validate the paid provisioning profile with both memory entitlements; test through TestFlight. The current ad-hoc IPA is a sideload artifact. |

Framework migration must cover the loader's source as well as file placement.
`peWineDir`, availability checks, Wine's `virtual_ios.c`, `pe_dylib.c` and the
converter lookup currently depend on legacy paths. Merely renaming a dylib or
adding a `.framework` directory does not demonstrate correct packaging. A change
to engine runtime inputs requires rebuilding the four runtime workflows; the
existing source-input equality guard must remain in force.

## Enrollment and submission materials

Engineering checks can proceed before enrollment. The owner will need an active
Apple Developer Program membership for TestFlight and App Store distribution.
The account determines the publishing identity; do not place signing credentials
in source files, issues or chat. Provide a private distribution certificate/API
key only through the selected secure signing system when that setup is ready.

Prepare the final app name/subtitle, accurate compatibility description, support
and privacy URLs, age/content answers, encryption/export answers, real-device
screenshots and reviewer instructions. Use project-built demonstration programs
or games with explicit distribution permission; do not bundle Forager as a demo.
Settings → About → Test programs provides built-in programs, but Steam features
also need a reviewable account or appropriate demo access without sharing the
owner's personal Steam credentials.

Primary references: [enrollment](https://developer.apple.com/programs/enroll/),
[submission](https://developer.apple.com/app-store/submitting/),
[App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/),
[iOS dynamic library packaging](https://developer.apple.com/library/archive/technotes/tn2435/_index.html),
[displaySyncEnabled](https://developer.apple.com/documentation/quartzcore/cametallayer/displaysyncenabled).

Passing compilation, a structural scan or the LGPL witness test does not mean
the app is approved or that distribution rights have been established.
