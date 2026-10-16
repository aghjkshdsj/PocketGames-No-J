# Exact converter distribution review

The implementation remains unchanged. No converter replacement or graphics
feature removal is proposed by this review.

The build pin identifies Metal Shader Converter **4.0 beta 2**. Hashes for the
installer, pristine iOS dylib and bundled agreement are recorded in
`compliance/source-lock.json`. The pinned source's extraction script checks
both the installer and the original iOS binary before copying the library;
it does not convert a macOS binary to iOS.

The preserved agreement is EA1844, dated May 31, 2023. Section 2.B permits
distribution of dynamic libraries for shader conversion, subject to the other
conditions. Section 2.D limits uses and hardware, and section 3 restricts copies
provided for evaluation and certain other purposes. The supplied text alone
does not determine whether additional terms accompanied this beta installer
or whether its particular delivery was evaluation-only.

The app's packaging adds a code signature, so its whole-file dylib hash can
change. `tools/audit_ipa_licenses.py --converter-original PATH` instead verifies
the original's pinned hash and compares all file-backed Mach-O sections with
the shipped library. This establishes payload provenance, not permission.

## Evidence still required

Obtain the exact hash-matching installer from an authorized Apple account and
retain its download record, accompanying license / package license resources,
release notes and any separately accepted beta terms. Record whether those
terms make the copy evaluation-only and how they interact with section 2.B.
Verify the granted use covers the app's on-device shader conversion.

If those materials do not establish the necessary rights, obtain Apple's
permission or separately evaluate a licensed replacement with game regression
testing. Do not replace the library merely to make the license checklist green.

The publicly documented availability of iOS converter libraries from version
3.1 supports the existence of an official iOS implementation. It does not
establish redistribution rights for this particular beta copy.

Sources: the exact bundled `Upstream-19-Apple-Metal-Shader-Converter.txt`,
the pinned source port at revision `65e6fe8f0da45b28b610c71fda9791e89d1060a6`,
and [Apple's converter documentation](https://developer.apple.com/metal/shader-converter/).
