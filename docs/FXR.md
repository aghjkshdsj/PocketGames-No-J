# FXR

FXR is an experimental FXI variant that keeps guest registers in host ARM registers.
The core is in `engine/fxr`, with `fxr_bridge.c` for Linux guests and `fxr_win_shim.c` for
Windows guests. The app can select FXR for built-in programs and 64-bit Windows games.
32-bit guests use FXI32. Compatibility mode selects FXI instead.

Faulting instruction state is recorded for Windows exception dispatch. A different thread
reading a running thread's state sees its last call into Windows. A kept Wine session uses
the interpreter chosen by its first 64-bit game. Restart the app to change that choice.

CI checks output against native guests, and device benchmarks compare checksums and timings
with native ARM64. Performance depends on the game and device.
