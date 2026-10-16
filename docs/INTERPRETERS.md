# Interpreter execution

FXI executes x86-64 instructions; FXI32 handles 32-bit guests through WoW64. FXR is an
experimental variant that keeps guest registers in host registers. Blink is an optional
benchmark comparison engine. CPU benchmarks compare checksums against native code.

Windows libraries are converted by `engine/pedylib/pe2dylib.py`, linked and signed on a Mac,
then bundled in `PE/wine` and `PE/wine-a64`. The CPU module names in the Wine ABI are fixed
upstream names: their implementations here dispatch into the interpreters.

Use Settings → Performance to choose the Windows interpreter, audio and session reuse.
32-bit compatibility, Steam client startup and game speed vary. Missing signed libraries
produce an error; there is no alternative executable-memory launch mode.
