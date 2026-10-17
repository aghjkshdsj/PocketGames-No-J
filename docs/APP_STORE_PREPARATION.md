# App Store preparation — October 16, 2026

This branch is a preparation and regression-test candidate. Build 7 remains the
delivered gameplay baseline: the user reported Forager running at a stable
60 FPS on iPhone 15 Pro Max, iOS 27.0.1, installed with iLoader. That result does
not establish performance of this branch or other games.

Build 9 at `396493dbf31cc1f3f3625a8e64ba4950b1ac8832` subsequently passed the
complete IPA and modified-GnuTLS relink checks. The user confirmed Forager still
works with that candidate; the supplied device log includes successful 32-bit
window reservation and rendering with sampled frame gaps around 16.7 ms.
Steam testing remains pending. The supplied red controller artwork is now the
app icon for subsequent packages; it does not change the already-built IPA.

## Implemented here

- Settings → About → Privacy opens an offline policy describing local storage,
  optional Steam authentication/downloads, cloud saves, sharing and deletion.
  The policy also has a public repository URL once merged. Publishing identity
  and a suitable private support contact still need to be finalized.
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

## Remaining engineering gates

| Gate | Evidence still required |
| --- | --- |
| Native library packaging | Replace standalone PE wrapper dylibs and converter dylib with proper frameworks, retaining code identity, module lookup, resources and signing order; test both 32-bit and 64-bit paths. |
| Rendering regression | Install this candidate on the same phone, reproduce Forager startup, gameplay, audio and frame pacing; also run the built-in Direct3D samples. |
| Privacy | Finish required-API/data-flow review of linked runtimes and guest-facing APIs; finalize manifest collection declarations and App Store privacy answers, including Valve and CDN handling. |
| LGPL | Complete modified-library build, independent source reconstruction, necessary application materials and authorized-device installation/replacement tests; establish source equivalence of prebuilt guest DLLs. |
| Rights | Resolve GPL/store permission, exact converter beta terms and authorization for the integrated Steam services. See APP_STORE_LICENSING.md. |
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
