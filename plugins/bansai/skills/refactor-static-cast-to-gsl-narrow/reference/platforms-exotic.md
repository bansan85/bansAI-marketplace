# Integer types — legacy, exotic, mainframes, WebAssembly

Scope: historical hardware and ABIs (DOS/Win16, old 8/16-bit micros, RISC Unix
workstations, 36/48/60-bit mainframes, supercomputers), exotic platforms still
alive (IBM i, z/OS, AIX, Solaris SPARC, HP-UX, OpenVMS), special-pointer
architectures (CHERI), and virtual machines (WebAssembly, eBPF). GPU code
(OpenCL, CUDA, Metal) is in `platforms-pc.md`. DSPs (C28x, SHARC, DSP56k...) are in
`platforms-embedded.md`.

Only what decides whether an integer cast can lose a value is kept here.

## 0. Reading

- Sizes in bits unless stated. `≈` = typical value to confirm. On these
  platforms, **always check `sizeof` and `<limits.h>`**: compilers of one machine
  often disagree.
- For every integer type `T`, `signed T` and `unsigned T` have the same size.
  Only the range differs.
- Before C23 / C++20, the standard **allows** ones' complement, sign-magnitude
  and padding bits: `sizeof(T) * CHAR_BIT` is not the number of value bits
  (use `std::numeric_limits<T>::digits`).
- The standard guarantees only: `char` ≥ 8 bits, `short` ≥ 16, `int` ≥ 16,
  `long` ≥ 32, `long long` ≥ 64, `sizeof(char) == 1`,
  `short ≤ int ≤ long ≤ long long`.

## 1. Rare data models

| Model | int | long | long long | ptr | Platforms |
|---|---|---|---|---|---|
| IP16 / LP32 | 16 | 32 | 64 | 16 or 32 | DOS, Win16, 8086/80286, PDP-11, old 8/16-bit micros |
| LP32 (68k) | 16 or 32 | 32 | 64 | 32 | Mac 68k, Amiga, Atari ST, Palm OS (by compiler / options) |
| ILP32 | 32 | 32 | 64 | 32 | 32-bit Unix (SPARC V8, MIPS o32, PA-RISC 1.x, VAX), z/OS 31-bit |
| LP64 | 32 | 64 | 64 | 64 | Tru64/Alpha, HP-UX 64, Solaris/SPARC 64, AIX 64, IRIX n64, z/OS 64 |
| LLP64 | 32 | 32 | 64 | 64 | Windows 64, **IBM i with `DTAMDL(*LLP64)`** |
| **P128 (IBM i)** | 32 | 32 | 64 | **128** | IBM i / OS/400, default |
| ILP64 / SILP64 | **64** | 64 | 64 | 64 | UNICOS (Cray), old 64-bit Unix (rare) |
| 36 bits | 36 | 36 | 72 ≈ | 18 to 36 | PDP-10, UNIVAC 1100/2200, GE-600 / Honeywell 6000 (Multics) |
| 48 bits | 48 | 48 | 96 ≈ | 48 | Burroughs / Unisys MCP ≈ |
| 60 bits | 60 ≈ | 60 ≈ | — | 18 to 60 | CDC 6600 / Cyber ≈ |

## 2. Fundamental integers: rare values

- **`CHAR_BIT`**: 8 almost everywhere. PDP-10 / UNIVAC / Multics: **9** (4 `char`
  per 36-bit word), or 7 / 6 by convention. CDC 6600 / Cyber: 6 (10 per 60-bit
  word) or 12 ≈. IM6100: 12. Word-addressed machines (standard corner case): 64,
  all types 64 bits, `sizeof` = 1 everywhere.
- **Plain `char`**: signed on PDP-11, VAX, x86, 68k; unsigned on PowerPC, ARM
  Linux, s390; z/OS unsigned ≈.
- **`short`**: 16 almost everywhere. **Cray UNICOS**: stored on **64 bits** with
  32-bit semantics (padding), sometimes 32 (T3E / T90) ≈. 36-bit machines: 18
  or 36.
- **`int`**: 16 on 8086/80286 (DOS, Win16, OS/2 1.x), Z80, 6502, 6809, PDP-11,
  8085, 68HC11, TMS9900; 16 or 32 on 68k (MPW, Think C, Aztec, Lattice, Alcyon,
  Pure C: **check**); 32 on 68k Metrowerks, SAS/C, GCC (16 with `-mshort`),
  VAX, SPARC, MIPS, Alpha, PA-RISC, PowerPC, IA-64, s390; **64** on UNICOS; 36
  on PDP-10 / UNIVAC / Honeywell; 48 on Burroughs MCP ≈.
- **`long`**: 32 on 16-bit, ILP32, LLP64; 64 on LP64 and ILP64; 36 on 36-bit
  machines. Alpha NT (ILP32): 32; Tru64 / OSF1: 64.
- **`long long`**: absent in C89, MSC ≤ VC6 (`__int64`), Keil C51, old 8-bit
  compilers; 64 elsewhere; 72 ≈ on 36-bit machines.
- **`intmax_t`**: 64 in practice; 32 on compilers without `long long`.

## 3. 16-bit memory models: DOS / Win16

Compilers: MSC 5-7, Borland / Turbo C++, Watcom, Digital Mars, Zortech.

| Model | Code pointer | Data pointer | Code / data size |
|---|---|---|---|
| Tiny, Small | near (16) | near (16) | < 64 KB total / 64 KB each |
| Medium | far (32) | near (16) | > 64 KB / 64 KB |
| Compact | near (16) | far (32) | 64 KB / > 64 KB |
| Large | far (32) | far (32) | > 64 KB / > 64 KB (objects < 64 KB) |
| Huge | far (32) | **huge (32)** | > 64 KB / > 64 KB (objects > 64 KB) |

- `int` 16, `long` 32, `short` 16. `far` arithmetic and comparison use the
  offset only (64 KB).
- `size_t` is 16 bits (`unsigned int`) in models with objects < 64 KB; 32 bits
  in huge by compiler (**check**). `ptrdiff_t`: 16 (near), 16 or 32 (far, huge).
- Win16: `HANDLE` 16, `WORD` 16, `DWORD` 32, `LPARAM` 32, `WPARAM` 16, `int` 16.
- 32-bit DOS extenders (DJGPP, Watcom 32, Phar Lap, DOS/4GW): flat ILP32.

## 4. Old 8 and 16-bit micros

| Machine / compiler | char | short | int | long | ptr |
|---|---|---|---|---|---|
| Z80 (Aztec, HiTech C, SDCC) | 8 | 16 | 16 | 32 | 16 |
| 6502 (cc65, Aztec) | 8 | 16 | 16 | 32 | 16 |
| 6809 (CMOC, OS-9 C) | 8 | 16 | 16 | 32 | 16 |
| 8080 / 8085 | 8 | 16 | 16 | 32 | 16 |
| 68HC11 (GCC) | 8 | 16 | 16 (32 with inverted `-mshort` ≈) | 32 | 16 |
| PDP-11 (Unix V6 / V7) | 8 | 16 | 16 | 32 | 16 |
| TMS9900, Z8000 | 8 | 16 | 16 | 32 | 16 |
| 8086 small model | 8 | 16 | 16 | 32 | 16 |

cc65: plain `char` unsigned ≈, no 32-bit `int`.

## 5. RISC Unix and historical workstations

| Platform | Model | Notes |
|---|---|---|
| SPARC V8 (Solaris 32, SunOS 4) | ILP32 | `char` signed |
| SPARC V9 (Solaris 64, Linux 64) | LP64 | `v8plus`: 32-bit binary using 64-bit registers |
| MIPS o32 | ILP32 | `long long` 64 |
| MIPS n32 | ILP32 (64-bit CPU) | `long long` native 64 |
| MIPS n64 | LP64 | `long` 64 |
| Alpha (Tru64 / OSF/1, Linux) | LP64 | `int` 32 |
| Alpha NT | ILP32 | `long` 32 |
| PA-RISC HP-UX 10.x / 11.x 32-bit | ILP32 | |
| PA-RISC HP-UX 11.x 64 (`+DD64`) | LP64 | |
| Itanium HP-UX | ILP32 / LP64 | |
| Itanium Windows | LLP64 | |
| PowerPC AIX (XL C) | ILP32 (`-q32`) or LP64 (`-q64`) | `wchar_t` **16-bit unsigned** (`unsigned short`) by default ≈; 32-bit with GCC |
| PowerPC Darwin (macOS ≤ 10.5) | ILP32 / LP64 | |
| PowerPC Linux 32 / 64 | ILP32 / LP64 | `char` unsigned |
| IRIX (SGI) | o32 / n32 / n64 | |
| OpenVMS (VAX / Alpha / Itanium) | ILP32 default, LP64 optional (`/POINTER_SIZE=64`) | pointers 32 or 64 mixed (`#pragma pointer_size`) |

## 6. IBM mainframes and special pointers

### z/OS (XL C/C++, Metal C)

| | 32-bit (ILP32 + `long long`) | 64-bit (LP64) |
|---|---|---|
| `char` | 1 byte (EBCDIC, unsigned ≈) | same |
| `wchar_t` | **2 bytes** | **4 bytes** |
| `short` / `int` | 2 / 4 | 2 / 4 |
| `long` | 4 | **8** |
| `long long` | 8 | 8 |
| pointer / `size_t` / `ptrdiff_t` / `ssize_t` | 4 (31 address bits in AMODE 31) | 8 |
| `time_t` / `off_t` / `rlim_t` | 4 | 8 |

Big-endian. In AMODE 31, the high bit of a 32-bit pointer can be a flag in old
code ≈.

### IBM i (OS/400, ILE C/C++)

| | P128 (4-4-16, default) | LLP64 (4-4-8, teraspace) |
|---|---|---|
| `int` / `long` | 4 / 4 | 4 / 4 |
| pointer | **16 bytes** (tagged space pointer) | **8 bytes** (`__ptr64`) |

A 16-byte pointer has an out-of-band validity bit: it cannot be made by an
integer cast. `intptr_t` / `uintptr_t` **do not exist** in P128 (largest integer
is 64 bits). `STGMDL(*TERASPACE)` + `DTAMDL(*LLP64)` for 8-byte pointers.

### Windows CE / Mobile, Symbian, Palm OS

Windows CE (ARM, MIPS, SH, x86): ILP32, UTF-16 APIs, `wchar_t` 16 bits.
Palm OS (68k): `int` 16 bits (option `-mshort`), pointers 32, `long` 32.
Symbian / EPOC (ARM): ILP32, `wchar_t` 16 bits ≈.

## 7. Supercomputers and non-IBM mainframes

- **Cray (UNICOS, C90, T90, T3E)**: `int` = `long` = **64 bits**, pointer 64,
  `char` 8. `short`: 64 bits of storage with 32-bit semantics (padding) on UNICOS
  C, or 32 ≈. Word pointers: `char*` carries a byte offset in the high bits, so
  `int*` and `char*` differ in representation.
- **NEC SX**: `int` 32, `long` 64, pointer 64.
- **Convex C1/C2**: `int` 32, pointer 32.
- **CDC 6600 / 7600 / Cyber**: 60-bit word, `char` 6 bits ≈, ones' complement.
- **Burroughs / Unisys MCP (A-Series)**: 48-bit word, `char` 8 or 6 bits ≈.
- **Unisys 2200 (ClearPath Dorado)**: 36-bit word, `char` 9 bits, **ones'
  complement**, C compilers still exist.

## 8. 36-bit machines and non-binary representations

- PDP-10 / DECsystem-10/20, UNIVAC 1100/2200, GE-600 / Honeywell 6000 (Multics),
  IBM 7090: 36-bit word, addresses 12 to 18 bits (30 on some).
- `CHAR_BIT`: 9 (Multics / UNIVAC ASCII), 7, or 6 (FIELDATA / BCD); `sizeof(int)`
  is one word.
- **Ones' complement** (UNIVAC) or **sign-magnitude** (IBM 7090): `-0` exists,
  `INT_MIN == -INT_MAX`, `~0 != -1`.
- Byte pointers vs word pointers: `char*` wider than `int*`.
- Null pointer not all-zero bits (Prime 50, some Honeywell / Bull).
- Function pointers different from data pointers in size (Unisys 1100, Itanium).

## 9. Virtual machines

### WebAssembly

| | wasm32 | wasm64 (memory64) |
|---|---|---|
| Model | ILP32 | LP64 |
| `int` / `long` / `long long` | 32 / **32** / 64 | 32 / **64** / 64 |
| pointer / `size_t` / `ptrdiff_t` | **32** | **64** |
| `char` | signed | signed |
| `wchar_t` | 32 signed ≈ | 32 |

wasm32 and wasm64 objects cannot be linked together. Emscripten `MEMORY64=0|1|2`
(2 = wasm64 lowered to wasm32). `size_t` = `unsigned long` (32) since
Emscripten 1.38.10. Memory limited to 2 to 4 GB (wasm32). Function pointers are
table indices.

### eBPF

64-bit pointers and registers, `int` 32, `long` 64, 512-byte stack.

### NaCl (x86-64)

32-bit pointers on a 64-bit CPU.

## 10. CHERI / Morello

| Mode | Data pointer | `intptr_t` / `uintptr_t` | `size_t` | `ptraddr_t` / `vaddr_t` |
|---|---|---|---|---|
| **Pure-capability (purecap)** | **128 bits** (+ 1 out-of-band tag bit) | **128 bits** | 64 | 64 (address only) |
| **Hybrid** | 64; `__capability`: 128 | 64; `__intcap_t`: 128 | 64 | 64 |

In purecap, `sizeof(void*) == 16`, `long` stays 64 (LP64), and
`intptr_t != size_t` in width. A pointer round trip through a plain integer
destroys the tag.

## 11. 32-bit ABIs on 64-bit CPUs

| ABI | CPU | `long` | pointer | `long long` |
|---|---|---|---|---|
| x32 | x86-64 | 32 | 32 | 64 |
| arm64ilp32 (Linux) / arm64_32 (watchOS) | AArch64 | 32 | 32 | 64 |
| MIPS n32 | MIPS64 | 32 | 32 | 64 |
| SPARC v8plus | SPARC V9 | 32 | 32 | 64 |
| s390 31-bit | z/Architecture | 32 | 32 (31 used) | 64 |
| Win32 on Win64 (WoW64) | x86-64 | 32 | 32 | 64 |

## 12. Real values of the target

```cpp
#include <climits>
#include <limits>
static_assert(CHAR_BIT == 8, "8-bit char required");
static_assert(std::numeric_limits<int>::digits + 1 == sizeof(int) * CHAR_BIT,
              "int has padding bits or is not two's complement");
```

GCC / Clang: `gcc -dM -E - </dev/null`. z/OS: `c89 -Wc,"LIST"`. IBM i:
`CRTCMOD ... OUTPUT(*PRINT)`. 16-bit MSVC: `cl /Zs` plus `sizeof`.

## 13. What it means for a cast

- Assume no invariant of the fundamental types: check `CHAR_BIT`, `sizeof(int)`,
  `sizeof(void*)`.
- `long` ↔ `int` is equal width on ILP32, LLP64, 16-bit and IBM i models, and
  differs on LP64, ILP64, Cray and 36-bit machines.
- `int` is 16 bits on DOS, Win16, 8/16-bit micros and some 68k compilers; 64 bits
  on UNICOS; 36 or 48 bits on word machines.
- `size_t` is 16 bits in the small DOS models; 32 on wasm32 and z/OS 31-bit; 64
  elsewhere.
- IBM i P128 and CHERI purecap: pointer-to-integer casts do not exist or lose
  the tag, so `intptr_t` reasoning is invalid.
- On ones' complement or sign-magnitude machines, `-0` and `~0 != -1` change
  signed ↔ unsigned results.
