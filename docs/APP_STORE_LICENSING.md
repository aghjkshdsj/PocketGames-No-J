# Licensing preparation for an App Store release

Settings → About → Open Source Licenses displays the offline documents in
`App/Resources/Legal`. Their SHA-256 digests and immutable source URLs are in
`index.json`. `tools/prepare_licenses.py` refreshes project notices and records
the exact build revision. CI rejects missing, changed or stale legal resources
before IPA publication. Original upstream legal wording is retained even where
the product's branding has changed.

This is an attribution and license-distribution implementation, not a grant of
new permissions or a determination that Apple can distribute the combination.
The project remains GPL-3.0-or-later with its existing additional permission.
No copyright assignment or proprietary relicense is performed.

## Prepared follow-up materials

- The offline bundle includes the nested FreeType BDF/PCF, hashing, HarfBuzz
  bridge and bundled-zlib notices, plus the exact FFmpeg IJG notices and credit.
  These are preserved notices, not changes to the compiled libraries.
- `compliance/source-lock.json` records the pinned source inputs and converter
  provenance hashes. `tools/collect_source_kit.py` collects and verifies source
  snapshots without changing the app or adopting new license terms.
- `tools/audit_ipa_licenses.py` checks an existing IPA's notice hashes and
  retained IJG symbols, and can compare converter payload sections with the
  pristine pinned binary. Stripped/absent symbols do not prove code absence.
- `docs/LGPL_REBUILD.md` identifies the remaining full modified-library
  rebuild, relink and installation demonstration. Source collection alone
  does not complete that verification.
- `docs/APP_STORE_PERMISSION_DRAFT.md` contains unadopted wording scoped to
  Dan-controlled contributions. `docs/CONVERTER_REDISTRIBUTION_REVIEW.md`
  records the exact agreement question without replacing the converter.

Before App Store submission, resolve these remaining distribution questions:

- Have a qualified reviewer check GPL/LGPL rights against Apple's actual
  distribution terms and any applied DRM or additional restrictions. The
  converter exception permits specified library combinations; it does not
  automatically waive other GPL obligations or change Apple's own terms.
- Deliver the complete corresponding source for the actual binary, including
  all modifications, generated build inputs needed to rebuild, configuration,
  and required installation/relinking material. Public links and pinned source
  references help locate it but are not a substitute for checking completeness.
- Verify LGPL requirements for the statically linked GMP, Nettle, GnuTLS,
  FFmpeg, FreeType alternative terms if selected, and Wine/D3D9 components.
  Verify bundled subcomponents and fonts against the final shipped inventory.
- Confirm the Apple Metal Shader Converter version's redistribution agreement
  applies to the intended packaging and use; preserve its terms separately.
- Verify authorization and terms for Steam login, downloads, client files and
  cloud services. Neither these notices nor the app grants game distribution
  rights or permission to circumvent protection systems.
- Confirm which contributions Dan owns and which belong to other contributors.
  Git authorship and AI-generated attribution are evidence to investigate,
  not automatic proof of copyright ownership.

The pinned Wine revision's own LICENSE and fork notice confirm LGPL-2.1-or-later.
Historical GPL-branch commentary in the preserved port exception is not evidence
that this pinned Wine branch is GPL-only.

## Maintenance

When a dependency changes, collect its exact license/notice files from the new
source revision, retain their wording, update the index digests and source URLs,
and recheck the final binary inventory. Do not substitute generic license text
for an upstream copyright notice.

Run `python3 tools/prepare_licenses.py --check` and
`python3 tests/legal_bundle_test.py`. Packaging also runs
`python3 tools/prepare_licenses.py --app PATH_TO_APP` through the runtime check.
