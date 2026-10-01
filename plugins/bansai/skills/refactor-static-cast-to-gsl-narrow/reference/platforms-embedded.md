# Integer types — embedded (microcontrollers and DSPs)

Scope: 8, 16 and 32-bit MCUs and DSPs, bare-metal or RTOS. PC, Android, iOS and
GPU: `platforms-pc.md`. Legacy and exotic hardware: `platforms-exotic.md`.

Only what decides whether an integer cast can lose a value is kept here.

## 0. Reading

- Sizes in **bits**. `sizeof` counts `char` units: 16-bit words on C28x, 32-bit
  words on SHARC. `≈` = typical value to confirm (section 7).
- For every integer type `T`, `signed T` and `unsigned T` have the same size.
  Only the range differs.
- `char`, `signed char`, `unsigned char` are three distinct types, `sizeof == 1`.
- Compiler options change sizes (`-mint8`, `-fshort-wchar`, memory models).
  A library built with other options is ABI-incompatible: reason with the
  options the user gave.

## 1. General rules

1. The CPU width does not give `int`: Cortex-M (32-bit) has a 32-bit `int`, AVR
   (8-bit) a 16-bit `int`, C28x (32-bit) a 16-bit `int`, SHARC (32-bit) a 32-bit
   `char`.
2. `CHAR_BIT` can be 16, 24 or 32 (DSPs). Then `uint8_t` and `int8_t` do not
   exist, and `unsigned char` is not 0..255.
3. Pointers are not uniform: near/far, several address spaces (Harvard), generic
   pointers wider than specific ones, function pointers different from data
   pointers.
4. `size_t`, `ptrdiff_t`, `intptr_t` may not have the pointer width (MSP430
   large, segmented models).
5. The `<stdint.h>` typedefs differ between toolchains (section 5).
6. Integral promotion uses the target `int`. With a 16-bit `int`, `uint16_t`
   promotes to `unsigned int` and arithmetic wraps at 16 bits; with a 32-bit
   `int`, `uint16_t` promotes to a signed `int`.

## 2. Widths by family (bits)

`ptr` = default data pointer. `—` = type absent.

| Family / toolchain | char | short | int | long | long long | ptr |
|---|---|---|---|---|---|---|
| AVR 8-bit (avr-gcc) | 8 | 16 | **16** (8 with `-mint8`) | 32 | 64 | 16 |
| PIC 8-bit (MPLAB XC8) | 8 | 16 | 16 | 32 | — (v1) / 32 ≈ (v2) | 8 to 24 by space |
| PIC24 / dsPIC (XC16, XC-DSC) | 8 | 16 | 16 | 32 | 64 | 16 |
| PIC32 MIPS (XC32) | 8 | 16 | 32 | 32 | 64 | 32 |
| 8051 Keil C51 | 8 (+ `bit`) | — ≈ | 16 | 32 | — | 8, 16 or **24 (generic)** |
| 8051 SDCC (mcs51) | 8 | 16 | 16 | 32 | 64 ≈ | 8 / 16 / 24 by qualifier |
| Z80 / Rabbit / eZ80 / SM83 (SDCC) | 8 | 16 | 16 | 32 | 64 ≈ | 16 (24 on eZ80 ADL ≈) |
| STM8 (SDCC, Cosmic, Raisonance, IAR) | 8 | 16 | 16 | 32 | 64 (SDCC) | 16 (24 in large model ≈) |
| HC08 / HCS08 / HC12 / HCS12 | 8 | 16 | 16 | 32 | — / 64 ≈ | 16 (24 paged) |
| MSP430 (TI cl430) | 8 | 16 | 16 | 32 | 64 | 16 (small), 20 stored on 32 (large) |
| RL78 (CC-RL) | 8 | 16 | 16 | 32 | 64 | near 16 / far 32 (20 used) |
| M16C / R8C / H8 / 78K / V850 / RX / RH850 / SH | ≈ 8 | ≈ 16 | 16 (M16C, H8); 32 (RX, V850, SH) | 32 | ≈ 64 | 16 / 32 by model |
| Infineon C166 / XC16x (Keil C166) | 8 | 16 | 16 | 32 | — | **16 or 32** (near / far / huge) |
| TI C2000 C28x (CCS cl2000) | **16** | 16 | 16 | 32 | 64 | **32** (22 used) |
| TI C54x / C55x ≈ | **16** | 16 | 16 | 32 | 40 (C54x) ≈ / 64 | 16 (23 in C55x large ≈) |
| TI C6000 (cl6x) | 8 | 16 | 32 | **40 (COFF)** / 32 (EABI) | 64 | 32 |
| ADI SHARC / SHARC+ | **32** | 32 | 32 | 32 | 64 | 32 |
| ADI Blackfin | 8 | 16 | 32 | 32 | 64 | 32 |
| NXP DSP56k ≈ | **24** ≈ | 24 ≈ | 24 ≈ | 48 ≈ | — | 24 ≈ |
| ARM Cortex-M / R / A 32-bit | 8 | 16 | 32 | 32 | 64 | 32 |
| AArch64 bare-metal | 8 | 16 | 32 | **64** | 64 | 64 |
| RISC-V RV32 (ilp32*) | 8 | 16 | 32 | 32 | 64 | 32 |
| RISC-V RV64 (lp64*) | 8 | 16 | 32 | 64 | 64 | 64 |
| Xtensa (ESP8266, ESP32) | 8 | 16 | 32 | 32 | 64 | 32 |
| ARC / Nios II / MicroBlaze / OpenRISC / LEON-SPARC V8 | 8 | 16 | 32 | 32 | 64 | 32 |
| PowerPC e200 / e500 (MPC5xxx, EABI) | 8 | 16 | 32 | 32 | 64 | 32 |
| TriCore / Hexagon / CEVA | 8 | 16 | 32 | 32 | 64 | 32 |

Notes:
- **AVR**: `size_t` and `ptrdiff_t` 16 bits. Pointers into `PROGMEM` above 64 KB
  need `__memx` / `__flash` (24-bit).
- **XC8**: `short long` / `__int24` = 24-bit integer. Pointers of 1, 2 or 3
  bytes by memory space.
- **Keil C51**: generic pointer 3 bytes (1 memory-type byte + 2 address bytes).
  No `long long`. **SDCC mcs51**: generic pointer 3 bytes, `__data` / `__idata` /
  `__pdata` 1 byte, `__xdata` / `__code` 2 bytes.
- **C28x**: `CHAR_BIT == 16`, `sizeof(int) == 1`, `sizeof(long) == 2`,
  `sizeof(long long) == 4`. `char` is 16 bits. `wchar_t` is `int` (16) in COFF,
  `long` (32) in EABI. `size_t` is `unsigned long` (32).
- **C6000**: `long` is 40 bits in COFF (register pairs), 32 in EABI.
- **SHARC**: `sizeof(int) == 1`, `sizeof(long long) == 2`. Word addressing, no
  addressable byte.
- **MSP430 (TI)**: large data model: 20-bit pointers stored on 32 bits,
  `size_t` / `ptrdiff_t` 32 bits. Small and restricted: 16 bits. `wchar_t` is
  `unsigned int` (16).
- **RL78**: far pointer 32 bits (20 used); a far pointer converted to an integer
  has its high byte at 0.
- **C166**: pointers 2 bytes (`near`, `sdata`, `bdata`) or 4 bytes (`far`, `huge`,
  `xhuge`, generic).

## 3. `char`

| Target | CHAR_BIT | plain `char` |
|---|---|---|
| AVR, PIC (XC8, XC16, XC32), 8051 Keil C51 | 8 | signed |
| MSP430 (TI) | 8 | **unsigned** (`--plain_char=signed` to change) |
| ARM 32/64 (GCC, armclang, IAR, TI ARM) | 8 | **unsigned** (AAPCS); Apple arm64: signed |
| RISC-V | 8 | **unsigned** |
| PowerPC EABI, Renesas CC-RL / CC-RX | 8 | unsigned ≈ (toolchain-dependent) |
| C28x (TI) | **16** | signed (COFF), unsigned (EABI) ≈: check `CHAR_MIN` |
| C54x / C55x | **16** | ≈ |
| DSP56k | **24** ≈ | ≈ |
| SHARC | **32** | ≈ |

- Force: `-fsigned-char` / `-funsigned-char` (GCC/Clang), `--plain_char=` (TI),
  `--char_is_signed` (IAR/Arm).
- `uint8_t` and `int8_t` exist only when `CHAR_BIT == 8`. With `CHAR_BIT > 8`,
  8-bit logic needs an explicit `& 0xFF`.
- `char8_t`, `char16_t`, `char32_t` have the representation of `unsigned char`,
  `uint_least16_t`, `uint_least32_t`. On C28x, `sizeof(char16_t) == 1`.

## 4. Pointers, `size_t`, `ptrdiff_t`

| Target | data pointer | function pointer | `size_t` | `ptrdiff_t` |
|---|---|---|---|---|
| AVR | 16 | 16 (word); 24 for extended progmem | 16 | 16 |
| PIC XC8 | 8 / 16 / 24 | 16 / 24 | 16 (or 8 ≈) | 16 |
| MSP430 small | 16 | 16 | 16 | 16 |
| MSP430 large | 20 (stored 32) | 20 (stored 32) | 32 | 32 |
| MSP430 restricted | 20 (stored 32) | 16 or 32 | **16** | **16** |
| 8051 Keil | 8 / 16 / 24 | 16 | 16 | 16 |
| RL78 near / far | 16 / 32 | 16 / 32 | 16 | 16 |
| C28x | 32 (22 used) | 32 | 32 (`unsigned long`) | 32 |
| C166 | 16 / 32 | 16 / 32 | 16 | 16 |
| ARM / RISC-V 32 / Xtensa / ARC | 32 | 32 | 32 | 32 |
| AArch64 / RV64 | 64 | 64 | 64 | 64 |
| SHARC | 32 (word address) | 32 | 32 | 32 |

Function pointers can differ from data pointers in size or representation
(Harvard: AVR, 8051, PIC, C28x).

## 5. Aliases (`<stdint.h>`) and their real type

| Toolchain | `uint8_t` | `uint16_t` | `uint32_t` | `uint64_t` | `size_t` | `intptr_t` | `ptrdiff_t` |
|---|---|---|---|---|---|---|---|
| avr-gcc / avr-libc | `unsigned char` | `unsigned int` | `unsigned long` | `unsigned long long` | `unsigned int` | `int` | `int` |
| arm-none-eabi-gcc (newlib / picolibc) | `unsigned char` | `unsigned short` | **`unsigned long`** | `unsigned long long` | **`unsigned int`** | `int` | `int` |
| riscv32-unknown-elf (newlib) ≈ | `unsigned char` | `unsigned short` | `unsigned int` | `unsigned long long` | `unsigned int` | `int` | `int` |
| ESP-IDF (newlib) ≈ | `unsigned char` | `unsigned short` | may be `unsigned long` | `unsigned long long` | `unsigned int` | `int` | `int` |
| TI C28x | n/a | `unsigned int` | `unsigned long` | `unsigned long long` | `unsigned long` | `long` | `long` |
| MSP430 (TI) | `unsigned char` | `unsigned int` | `unsigned long` | `unsigned long long` | `unsigned int` | `int` | `int` |

- `uint32_t` is `unsigned long` on AVR, MSP430, arm-none-eabi: `size_t`
  (`unsigned int`) and `uint32_t` are **distinct types** of the same width on
  arm-none-eabi.
- `int_fastN_t` / `int_leastN_t` come from the toolchain macros
  (`__INT_FAST16_TYPE__`...): do not assume, check (section 7). On `CHAR_BIT == 16`,
  `int_least8_t` is 16 bits and `int8_t` does not exist.
- `intmax_t` is 64 bits, 32 bits on toolchains without `long long` (Keil C51,
  XC8 v1).

## 6. Wide characters

`wchar_t`: AVR `int` (16, signed); MSP430 (TI) `unsigned int` (16); C28x `int`
(COFF) or `long` (EABI); TI ARM and old IAR: 16; arm-none-eabi: 32 (unsigned) ≈.
`-fshort-wchar` forces 16 bits unsigned.

## 7. Real values of the target

```bash
arm-none-eabi-gcc -mcpu=cortex-m4 -dM -E - </dev/null | grep -E '__(CHAR_BIT|CHAR_UNSIGNED|SIZEOF_(INT|LONG|LONG_LONG|POINTER|SIZE_T|WCHAR_T|SHORT)|SIZE_TYPE|PTRDIFF_TYPE|INTPTR_TYPE|INT(8|16|32|64)_TYPE|UINT32_TYPE|WCHAR_TYPE|SHRT_WIDTH|INT_WIDTH|LONG_WIDTH|INT_FAST(8|16|32|64)_TYPE|INT_LEAST(8|16|32|64)_TYPE)__'
avr-gcc -mmcu=atmega328p -dM -E - </dev/null | grep -E '__SIZEOF_|__INT'
```

## 8. What it means for a cast

- With a 16-bit `int` (AVR, MSP430, PIC, 8051, RL78, STM8, Z80, C28x): `int` ↔
  `uint16_t` is a sign change at equal width, `long` ↔ `uint32_t` too;
  `int` → `uint32_t` / `long` widens but a negative `int` still changes value.
- `long` is 32 bits on most targets here. Exceptions: 40 bits on C6000 COFF,
  48 bits on DSP56k ≈, 64 bits on AArch64 and RV64.
- `size_t` is 16 bits on AVR, MSP430 small and restricted, 8051, RL78, C166,
  but 32 bits on MSP430 large, C28x and 32-bit cores: `size_t` → `uint16_t` is
  a no-op on some and a narrowing on others.
- On C28x and SHARC, `sizeof` is in words: `sizeof(int) == 1`.
- With `CHAR_BIT == 16 / 24 / 32`, a cast to `unsigned char` does not give
  0..255.
- `char` signedness varies by toolchain: a cast from or to plain `char` is
  platform-dependent.
