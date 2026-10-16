# FXI interpreter

FXI executes x86-64 instructions without generating host code. It uses identity-mapped guest
memory, cached decoded blocks, software x86 flags and SSE2 support. FXI32 provides the i386
variant. FXR keeps guest registers in host registers for higher throughput.

The app benchmarks FXI and FXR against native ARM64 kernels and reports checksum differences.
Linux CI also compares guest output with native output, including atomics, x87 and arithmetic.
Windows guests use the host interfaces in `App/Sources/Native/fxi_win_host.c` and
`fxi_wow_host.c`. See [execution details](INTERPRETERS.md).
