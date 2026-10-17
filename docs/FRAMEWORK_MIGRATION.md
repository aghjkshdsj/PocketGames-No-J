# Native framework validation candidate

The working baseline is build 15 at
`a1d582b34be06ae5867cb1230b8c30167b7208b9`. The owner confirmed that it looks
good after the build 14 cloud-folder correction. Preserve that IPA while testing
this branch. Main and the earlier preparation branch are not changed by this
candidate.

## Implemented migration

`build-ipa.yml` accepts `framework_layout=true` only with `lgpl_validation=true`.
It builds a real unsigned Xcode archive, converts its 293 native dynamic
libraries to frameworks, then produces a separate ad-hoc validation IPA without
publishing a release. This is not a signed App Store export.

The two Wine families have distinct framework names (`PGEC_*` and `PGA64_*`),
even where the Windows module name is identical. Test wrappers use `PGTest_*`;
the shader converter uses `PGShaderConverter`. The naming helper rejects unsafe
paths and the packager rejects collisions before moving any original binary.

Only native binaries move. The original PE data farms, interpreter modules,
prefix template, notices and user save paths keep their locations. Wine's
loader resolves the framework path for both its initial dyld load and each
additional process instance. The app's availability checks and built-in DLL
test also support the new layout. The graphics service selects the converter
framework when the inventory is present, without a development-path fallback.
Legacy packages continue to select their existing paths.

The packager updates each native library's install name and creates framework
metadata. Every file-backed Mach-O section must retain the same address, size
and SHA-256. The checker requires arm64 iOS-device binaries, unique bundle IDs,
matching executable names, a complete manifest and resolved non-system imports.
It rejects any leftover standalone native libraries. Frameworks are signed and
verified individually, followed by the outer application. The signed IPA must
pass the structural audit again. These checks do not validate Apple-issued
provisioning, private APIs generally, permission to distribute or game behavior.

Changing the Wine loader and converter lookup changes runtime inputs. Rebuild
all four runtime workflows for the candidate SHA. Keep the source-input equality
guard; do not reuse the earlier build's runtime binaries.

## Device gate before further adoption

Install the candidate using the same method as build 15. Check Forager start,
audio, controller input and sustained frame pacing. Check Dokimon With Steam,
its restored twelve-minute save, manual Download and Upload, and session reuse.
Run the built-in DLL test, 32-bit suite, 64-bit suite and D3D samples as supported.
Use fresh logs to identify architecture or converter loading failures. Do not
erase game saves, replace the working baseline or merge this migration based
only on compilation and a structural pass.

After paid membership is active, validate the real provisioning profile and
memory entitlements, build/export with distribution signing and test through
TestFlight. An ad-hoc signature does not demonstrate that entitlement approval
or App Store processing will succeed.

Reference: [Apple TN2435, embedded libraries and frameworks](https://developer.apple.com/library/archive/technotes/tn2435/_index.html).
