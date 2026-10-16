# Corresponding-source and replacement-library preparation

The collector assembles a **source preparation kit**, not a declaration of LGPL
compliance. Its manifest explicitly records that the modified-library app relink
test and equivalence of prebuilt guest DLLs remain unverified. Do not relabel
those fields as passed because collection succeeded.

## Collect and verify

Use Python 3.11 or later, Git, network access and sufficient disk space for the
source archives, including Wine and LLVM. From this repository run:

```sh
python3 tools/collect_source_kit.py --revision FULL_APP_COMMIT_SHA \
  --output /path/to/new-source-kit --cache /path/to/source-cache
python3 tools/collect_source_kit.py --verify --output /path/to/new-source-kit
```

The application archive is produced by `git archive` from the requested commit.
The lock records the source port, Wine, DXMT, Dock, Blink, FreeType and LLVM
commits. The port archive includes the exact FFmpeg, GMP, Nettle and GnuTLS
source tarballs, checked against their recorded SHA-256 digests. Original
copyright notices and upstream source names are preserved.

The source port is filtered to omit prebuilt objects, guest executables and
Apple's proprietary converter; every omitted path is recorded. This filtering
does not waive a corresponding-source obligation. The source code and recipes
for a prebuilt component must still be established and tested. Xcode, Apple
SDKs and authorized converter acquisition are separate prerequisites.

The kit captures source snapshots rather than Git working repositories. The
current build scripts use Git reset/checkout and network fetches. A verified
offline reconstruction/staging procedure is still needed; simply extracting
the snapshots and running every workflow command will not reconstruct that
metadata. Local cache files are trusted inputs; the kit records their digests
and the immutable retrieval URLs for review and independent comparison.

## Required macOS rebuild demonstration

### Automated first replacement test

Dispatch `build-ipa.yml` on the candidate app revision with `lgpl_validation`
set to true. Supply `runtime_revision` only when its inputs pass the existing
runtime-equality guard. The workflow first validates the normal runtime inputs,
then rebuilds the exact locked GMP, Nettle and GnuTLS sources on macOS for iOS.
The one-line GnuTLS diagnostic changes no cryptographic settings or results.
`tools/lgpl_relink_validation.py` requires the marker in both the replacement
archive and the complete linked application, and records original/replacement
hashes, the source patch, build configuration, application source and link
materials. The `lgpl-relink-validation` artifact also contains build logs.

The validation IPA has a distinct filename and does not create a GitHub release.
Download its evidence before the CI retention period expires. This is a build/
relink demonstration for one library, not proof of runtime execution, usable
independent reconstruction of all dependencies, or full LGPL compliance. Install
it with legitimate tester credentials and record game/Steam tests separately.

### Full release demonstration still required

1. Use a clean Apple-silicon macOS environment and record Xcode, SDK, deployment
   target, clang, Python, CMake, Ninja, Bison/Flex, MinGW and LLVM versions.
2. Reconstruct the source layout specified by `engine/wine/PIN`,
   `engine/dxmt/PIN`, `engine/blink/PIN` and the lock. Apply this app's namespace
   normalization and all patches in the recorded build order. Keep original
   archives beside the modified working trees. Do not substitute newer sources.
3. Rebuild the Wine Unix side, i386 Wine farm, DXMT Unix side and DXMT PE farms
   using the corresponding workflows. Account separately for the port's
   prebuilt ARM64EC/aarch64 DLLs and D3D12 implementation. Verify that the exact
   preferred source, generation steps and tools for those files are available.
4. Introduce a harmless, documented change to one LGPL library, such as an
   identifiable version-string marker in FFmpeg's libavutil. Keep the changed
   source and patch. Rebuild with the same configuration, including the
   `--disable-gpl`, `--disable-nonfree` and `--disable-version3` FFmpeg choices.
5. Rebuild and link the complete application with that replacement archive.
   Preserve configure arguments, generated configuration headers, logs, static
   libraries, linker command, link file lists, generated sources and application
   objects needed by the selected LGPL route. Confirm the replacement marker
   reaches the final app, rather than merely the standalone library archive.
6. Sign the modified app using the tester's own legitimately available Apple
   development credentials/profile and install it on an authorized device.
   Record profile/entitlement limitations. No publisher private key is part of
   the kit. Verify normal launch and relevant game/Steam regressions with the
   modified library. Record device, OS, source SHA and artifact hashes.
7. Package the necessary application material, corresponding source,
   modifications, configuration and tested instructions alongside the actual
   release, or implement another applicable LGPL delivery route. Verify
   recipients can reproduce the demonstrated replacement without relying on
   expired CI caches or inaccessible developer-only files.

Full usable application source may satisfy the applicable application-material
route; object files are not automatically an additional requirement in every
case. A shared-library filename alone does not demonstrate replaceability under
iOS code signing. LGPL 2.1 and LGPL 3 conditions differ; GMP and Nettle use the
LGPL 3 selection. Assess any conditional installation-information requirement
against the actual distribution arrangement.

The App Store EULA must preserve the upstream modification and debugging rights
required by the selected route. The draft permission for Dan-controlled code
does not waive library obligations.

References: [LGPL 2.1 section 6](https://choosealicense.com/licenses/lgpl-2.1/),
[LGPL 3 section 4](https://choosealicense.com/licenses/lgpl-3.0/).
