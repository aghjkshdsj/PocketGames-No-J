# Distribution evidence review — October 17, 2026

This is a record of evidence and unresolved conditions, not an adopted license
or an App Store clearance. Forty bundled notice documents have been checked
against build 15. Its modified-GnuTLS witness and thirty relink evidence files
also passed package verification. The owner confirmed manual Steam Cloud
download and upload in build 14, and reported build 15 looks good. These device
reports do not establish complete independent rebuilding or every LGPL right.

## Ownership and terms by component

| Component | Evidence | Work still needed before store distribution |
| --- | --- | --- |
| PocketGames app, interpreter and Dan-controlled port/fork/Dock modifications | Current GPL-3.0-or-later grants; owner says both earlier projects and credited aliases are his | Review imported files and contributions, including SwiftSteam and interpreter glue, against their original histories. Adopt a precisely scoped store permission only after that review. The existing draft is not active. |
| Wine at the locked revision | Original LGPL-2.1-or-later license and fork notice bundled | Complete preferred-source/build equivalence of the prebuilt guest farms, modified-library rebuild and authorized-device replacement instructions. Dan's permission cannot waive upstream requirements. |
| DXMT | MIT upstream plus GPL fork modifications; its D3D9/DXSO import is LGPL-2.1-or-later | Preserve the three grants separately. The fork notice identifies the D3D9 import and Wine/DXVK-derived areas; review these source notices during source equivalence checks. Do not label the complete graphics archive MIT-only or Dan-owned. |
| GMP/Nettle/GnuTLS | Exact source tarballs and versions locked; modified GnuTLS relink demonstrated | Independent reconstruction and usable application/link materials for the actual final binary; legitimate installation with the replacement, including the applicable LGPL 3 conditions. |
| FFmpeg | Pinned 7.1.1 source, LGPL configuration recipe and IJG notice | Retain actual final build configuration/logs and check final executable retention. A missing symbol does not prove a component is absent. |
| FreeType, LLVM, Blink, FEX, zstd, XML/XSLT and other imported components | Original notices preserved; pinned dependencies recorded in source lock and index | Reconcile with the final shipped inventory and retain copyright notices. Code authorship or a comment is not a substitute for provenance. |
| Apple shader converter 4.0 beta 2 | Exact installer, unsigned iOS payload and bundled agreement hashes locked | Obtain the exact authorized download's package terms and any separately accepted conditions. Check intended redistribution against them. The generic agreement and an unchanged binary alone do not settle the beta terms. |
| Valve client, sign-in, downloads, cloud services and games | Separate services/content; not licensed by the project's GPL | Review the actual integrated use, service authorization and content permissions. No permission is invented or requested on the owner's behalf. |

## Concrete evidence to obtain

1. Keep the release's immutable application source, all locked preferred source,
   modifications, generated configuration and reproducible build/relink material
   independently of expiring Actions artifacts. Rebuild the prebuilt guest DLLs
   from the matching sources rather than assuming their labels establish
   equivalence. Test the selected LGPL delivery route against the final binary.
2. On a Mac, supply the exact Apple installer acquired through an authorized
   account and run `tools/inspect_converter_installer.py INSTALLER --output
   NEW_EVIDENCE_DIRECTORY --download-record SOURCE_AND_DATE`. The tool verifies
   both pinned hashes and copies package agreement/metadata resources without
   copying the proprietary library into the evidence. Also retain applicable
   online terms or acceptance records. Do not include account secrets.
3. Review the actual Apple distribution arrangement and EULA against GPL/LGPL
   conditions. A custom EULA must preserve applicable library modification and
   debugging rights and satisfy Apple's minimum terms. The existing Apple-linking
   exception is not a general waiver of store restrictions. No proposed grant
   from Dan covers other authors, Apple or Valve.
4. Before signing, finalize the seller identity, privacy/support URLs and privacy
   answers against the actual data flows. The support email is
   officialpocketgame@gmail.com. Verify that mailbox privately; the app does not
   send a verification message or publish personal account information.

Do not remove required attribution or source-access information to prevent
copying. Packaging a library as a framework does not change its license or
establish replacement rights under the store's signing arrangement.

Primary references: [LGPL 2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html),
[LGPL 3](https://www.gnu.org/licenses/lgpl-3.0.html),
[Apple developer agreement and minimum EULA terms](https://developer.apple.com/support/terms/apple-developer-program-license-agreement/),
[Apple converter documentation](https://developer.apple.com/metal/shader-converter/).
