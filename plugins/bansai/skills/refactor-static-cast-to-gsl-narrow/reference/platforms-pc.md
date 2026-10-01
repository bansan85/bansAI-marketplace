# Integer types — PC (32/64-bit), mobile and GPU

Scope: x86 / x86-64 (Windows, Linux, macOS, BSD), ARM32 / AArch64 / RISC-V /
PowerPC / s390x / LoongArch / MIPS under a full OS, Android, iOS, and GPU code
(OpenCL, CUDA/HIP/SYCL, Metal). Microcontrollers and DSPs: `platforms-embedded.md`.
Legacy and exotic hardware, WebAssembly: `platforms-exotic.md`.

Only what decides whether an integer cast can lose a value is kept here.

## 0. Reading

- Sizes in bits unless stated. `≈` = typical value to confirm (section 10).
- For every integer type `T`, `signed T` and `unsigned T` have the same size.
  Only the range differs. Two's complement everywhere here.
- `char`, `signed char`, `unsigned char` are three distinct types, 8 bits.
- Options change sizes: `-m32` / `-m64` / `-mx32`, `-fshort-wchar`,
  `-fsigned-char` / `-funsigned-char`, `/J` (MSVC: `char` unsigned),
  `-D_FILE_OFFSET_BITS=64`, `-D_TIME_BITS=64`, `/Zc:wchar_t-`.

## 1. Data models

| ABI / platform | int | long | long long | pointer | Model |
|---|---|---|---|---|---|
| i386 System V, Win32, Windows ARM32, ARM32 (Linux EABI, Android armeabi-v7a, iOS armv7), RISC-V RV32, PowerPC 32, MIPS o32 | 32 | 32 | 64 | 32 | ILP32 |
| MIPS n32, x32 ABI, arm64ilp32 (Linux), arm64_32 (watchOS), s390 31-bit | 32 | 32 | 64 | 32 | ILP32 on a 64-bit CPU |
| x86-64 System V (Linux, BSD, macOS, Solaris, Android x86_64), AArch64 (Linux, Android, macOS, iOS, BSD), RISC-V RV64, PowerPC64, s390x, LoongArch64, MIPS n64, SPARC64 | 32 | **64** | 64 | 64 | LP64 |
| **x86-64 Windows (MSVC, clang-cl, MinGW-w64), Windows ARM64** | 32 | **32** | 64 | 64 | **LLP64** |

- `long`: 32 bits on Windows 64 and ILP32, 64 bits on Linux/macOS/BSD/Android 64.
- `int` is 32 bits everywhere here, `short` 16, `long long` 64, `char` 8.
- Register width is not `int` width.

## 2. `char` signedness (plain `char`)

| Platform | `char` |
|---|---|
| x86, x86-64, MIPS, SPARC, Windows ARM64 | signed |
| AArch64 / ARM32 Linux, Android, BSD | **unsigned** |
| AArch64 macOS / iOS (Apple) | signed |
| PowerPC Linux, s390x Linux, RISC-V Linux | **unsigned** |

Test: `__CHAR_UNSIGNED__`, `CHAR_MIN == 0`. Treat plain `char` as signed for the
worst case, and as unknown signedness when both families are targeted.

## 3. Aliases and their real type

Same width does not mean same type: `long` and `long long` are distinct types.
A cast between two aliases of the same underlying type changes nothing.

| typedef | Linux x86-64 (glibc) | macOS (x86-64, arm64) | Win64 (MSVC/MinGW) | Linux i386 | Win32 (MSVC) |
|---|---|---|---|---|---|
| `int32_t` / `uint32_t` | `int` / `unsigned int` | same | same | same | same |
| `int64_t` | **`long`** | **`long long`** | `long long` | `long long` | `long long` |
| `uint64_t` | **`unsigned long`** | **`unsigned long long`** | `unsigned long long` | `unsigned long long` | `unsigned long long` |
| `size_t` | `unsigned long` | `unsigned long` | **`unsigned long long`** | `unsigned int` | `unsigned int` |
| `ptrdiff_t`, `intptr_t` | `long` | `long` | `long long` | `int` | `int` |
| `uintptr_t` | `unsigned long` | `unsigned long` | `unsigned long long` | `unsigned int` | `unsigned int` |
| `intmax_t` / `uintmax_t` | `long` / `unsigned long` | same | `long long` / `unsigned long long` | `long long` | `long long` |
| `ssize_t` | `long` | `long` | absent in MSVC (`SSIZE_T` = `LONG_PTR`) | `int` | absent |
| `time_t` | `long` | `long` | `__int64` | `long` (32 bits) | `__int64` |
| `off_t` | `long` | `long long` | **`long` (32 bits)** | `long` (32 bits, or `long long` with LFS) | `long` (32 bits) |
| `clock_t` | `long` | `unsigned long` | `long` (32 bits) | `long` | `long` |
| `wchar_t` | `int` (32) | `int` (32) | `unsigned short` (16) | `int` (32) | `unsigned short` (16) |

`int_fastN_t` / `uint_fastN_t` depend on the libc, not on the CPU:

| libc / platform | fast8 | fast16 | fast32 | fast64 |
|---|---|---|---|---|
| glibc x86-64 / AArch64 | `signed char` | **`long` (64)** | **`long` (64)** | `long` |
| glibc 32-bit | `signed char` | `int` (32) | `int` (32) | `long long` |
| musl | `signed char` | `int` (32) | `int` (32) | 64 |
| MSVC (UCRT), MinGW-w64 ≈ | `signed char` | **`short` (16)** | `int` (32) | `long long` |
| macOS / iOS | `int8_t` | **`int16_t` (16)** | `int32_t` | `int64_t` |
| FreeBSD ≈ | `int` | `int` | `int` | `int64_t` |
| Android Bionic ≈ | `int8_t` | 64 on LP64, 32 on 32-bit | same | 64 |

`int_leastN_t` has exactly N bits. `intmax_t` is 64 bits.

## 4. Pointer-width types

`size_t`, `ptrdiff_t`, `intptr_t`, `uintptr_t` follow the **ABI** address width,
not the CPU: 32 bits on ILP32 (including x32, arm64ilp32, arm64_32, MIPS n32),
64 bits on LP64 and LLP64.

- On x32 / arm64ilp32 / arm64_32: 64-bit CPU, but `size_t`, `long` and pointers
  are 32 bits; `long long`, `intmax_t` stay 64 bits.
- `PTRDIFF_MAX` can be below `SIZE_MAX / 2`: on GCC/Clang an object is at most
  `PTRDIFF_MAX` bytes.
- Never assume `sizeof(size_t) == sizeof(long)`.

## 5. Wide characters

| Platform | `wchar_t` |
|---|---|
| Windows (MSVC, clang-cl, MinGW-w64, Cygwin) | **16 bits unsigned** (UTF-16) |
| Linux x86 / x86-64 / PowerPC / RISC-V / MIPS / s390; macOS / iOS; FreeBSD / OpenBSD / NetBSD | 32 bits **signed** (`int`) |
| Linux ARM32 / AArch64 | 32 bits **unsigned** |
| Android (Bionic) | 32 bits, signedness follows the architecture (ARM unsigned, x86 signed ≈) |
| `-fshort-wchar` | 16 bits unsigned |

`wint_t`: MSVC `unsigned short` (16); glibc and musl `unsigned int` (32);
macOS / BSD `int` (32). `char8_t`, `char16_t`, `char32_t`: 8, 16, 32 bits
unsigned-representation (same as `unsigned char`, `uint_least16_t`,
`uint_least32_t`). A 16-bit `wchar_t` cannot hold a full Unicode code point.

## 6. System types

| Type | Width |
|---|---|
| `time_t` | Linux/Android 32-bit: **32** (unless glibc ≥ 2.34 with `-D_TIME_BITS=64`, which needs `-D_FILE_OFFSET_BITS=64`); musl ≥ 1.2: 64; 64-bit Linux/macOS/Android: 64; MSVC: 64 (32 with `_USE_32BIT_TIME_T`); FreeBSD ≥ 12, OpenBSD ≥ 5.5, NetBSD ≥ 6: 64 |
| `clock_t` | `long`: 64 on LP64, 32 on ILP32 and Windows |
| `off_t` | Linux/Android 32-bit: 32 unless `-D_FILE_OFFSET_BITS=64`; LP64, macOS, FreeBSD: 64; **MSVC/MinGW: 32** |
| `ino_t`, `blkcnt_t`, `fsblkcnt_t`, `fpos_t`, `rlim_t` | 32 or 64 depending on `_FILE_OFFSET_BITS` and the ABI |
| `pid_t`, `uid_t`, `gid_t`, `mode_t` | 32 |
| `socklen_t` | `unsigned int` (Linux, macOS), `int` (Winsock) |
| `SOCKET` | `int` (POSIX); **`UINT_PTR`** on Windows (32 on Win32, 64 on Win64) |
| `pthread_t` | `unsigned long` (Linux, 8 on LP64, 4 on ILP32), pointer (macOS, BSD) |
| `sig_atomic_t` | `int` (32) |

## 7. Windows API types

- **Fixed**: `BYTE` 8, `WORD` 16, `DWORD` 32, `LONG` 32, `ULONG` 32, `INT` 32,
  `UINT` 32, `BOOL` 32 (`int`), `BOOLEAN` 8, `HRESULT` 32, `DWORD32` / `INT32` 32,
  `DWORD64` / `INT64` 64, `LONGLONG` 64, `ULONGLONG` 64, `WCHAR` 16.
- **Pointer-width** (32 on Win32, 64 on Win64): handles and pointers (`HANDLE`,
  `HWND`, `LPVOID`...), `INT_PTR`, `UINT_PTR`, `LONG_PTR`, `ULONG_PTR`,
  `DWORD_PTR`, `SIZE_T`, `SSIZE_T`, `WPARAM`, `LPARAM`, `LRESULT`.
- **Build-dependent**: `TCHAR` = `char` (MBCS) or 16-bit `wchar_t` (`UNICODE`).
- `long`, `LONG`, `DWORD` are 32 bits on Windows 64, while `long` is 64 bits on
  Linux 64.

## 8. Mobile

### Android (Linux kernel + Bionic)

| ABI | Model | `char` | `wchar_t` | `size_t` | `time_t` | `off_t` |
|---|---|---|---|---|---|---|
| arm64-v8a | LP64 | unsigned | 32 unsigned ≈ | 64 | 64 | 64 |
| x86_64 | LP64 | signed | 32 signed ≈ | 64 | 64 | 64 |
| riscv64 | LP64 | unsigned | 32 ≈ | 64 | 64 | 64 |
| armeabi-v7a | ILP32 | unsigned | 32 ≈ | 32 | **32** | **32** unless `_FILE_OFFSET_BITS=64` (API ≥ 21) |
| x86 | ILP32 | signed | 32 ≈ | 32 | **32** | 32 unless `_FILE_OFFSET_BITS=64` |

JNI: `jint` 32, `jlong` **64** (not `long` on ILP32), `jshort` 16, `jbyte` 8
**signed**, `jboolean` 8 **unsigned**, `jchar` 16 **unsigned**, `jsize` = `jint`.

### iOS / macOS (Darwin)

iOS / macOS arm64 and macOS x86-64: LP64, `char` signed, `wchar_t` 32 signed.
watchOS arm64_32: ILP32 on a 64-bit CPU. iOS armv7: ILP32. `int64_t` =
`long long`, `size_t` = `unsigned long`, `off_t` 64, `time_t` = `long` (64).

## 9. GPU

- **OpenCL C**: `char` 8, `short` 16, `int` 32, **`long` 64 always**. `size_t`,
  `ptrdiff_t`, `intptr_t`, `uintptr_t` are 32 or 64 bits according to
  `CL_DEVICE_ADDRESS_BITS` of the **device**, not the host. `long long` is
  absent. The host `long` (32 bits on Windows) is not the OpenCL `long`: use
  `cl_int`, `cl_long`, `cl_ulong`.
- **CUDA / HIP / SYCL**: host code follows the host ABI (Windows `long` 32,
  Linux `long` 64); device code follows the host ABI for `long` and `size_t`.
  `char` is signed on NVIDIA devices (follows the host compiler).
- **Metal (MSL)**: `short` 16, `int` 32, `long` / `ulong` 64, pointers 64 bits.

## 10. Real values of the target

```bash
gcc -dM -E - </dev/null | grep -E '__(CHAR_UNSIGNED|SIZEOF_(INT|LONG|LONG_LONG|POINTER|SIZE_T|WCHAR_T)|SIZE_TYPE|PTRDIFF_TYPE|INT64_TYPE|UINT64_TYPE|WCHAR_TYPE|LP64|ILP32)__'
```

MSVC: `_WIN64`, `_M_X64`, `_M_ARM64`, `_M_IX86`, `_NATIVE_WCHAR_T_DEFINED`.

## 11. What it means for a cast

- `size_t`, `ptrdiff_t`, `intptr_t` → 32-bit or `int`: narrowing as soon as one
  selected target is 64-bit.
- `long` → `int` narrows on LP64; `long` and `int` have equal widths on
  Windows and ILP32. `unsigned long` → `unsigned int`, same.
- `int64_t` → `long` is a no-op on Linux LP64 and a narrowing on ILP32 and
  Windows. `uint32_t` → `long` is value-preserving on LP64 only.
- `DWORD`, `UINT`, `ULONG` are always 32 bits; `DWORD_PTR`, `ULONG_PTR`,
  `SIZE_T`, `WPARAM` follow the pointer width.
- `wchar_t` → `char16_t`: no-op on Windows, narrowing where `wchar_t` is 32 bits.
- `time_t` and `off_t` can be 32 bits: casts to or from 64-bit types are not
  free on 32-bit Linux/Android and, for `off_t`, on MSVC/MinGW.
- `char` signedness changes the category of any cast from or to plain `char`.
