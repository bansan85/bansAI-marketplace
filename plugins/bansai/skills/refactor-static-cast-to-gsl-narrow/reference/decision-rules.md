# Decision rules

How to decide, for each integer `static_cast` of the scope, whether it becomes
`gsl::narrow`. Applied in step 4 of the skill, with the platform facts derived
from the `platforms-*.md` files and the user's answers. A verdict holds only if
it holds on **every** selected target.

## 1. Find the casts

`grep -n 'static_cast<'` over the scope. Work file by file, keep notes minimal.
Discard at once, without reading context, the casts whose destination is
obviously not an integer (`bool`, enum, float, pointer, class). For the rest,
resolve the **source** and the **destination** type by reading the declarations
(variables, parameters, return types, aliases, `auto`). Determine the category
(see the skill). A cast in no category is out of scope and not counted.

## 2. Decide, in this order

For each cast of a category, the first rule that matches wins. `analysed` counts
every cast of a category that you examine; `converted` counts those turned into
`gsl::narrow`.

1. **Not provably an integer, or inside a macro body.** Source or destination is
   an enum (including `std::byte`), a floating-point type, a class with a
   conversion operator, or a type you cannot resolve (`auto`, a dependent
   template type): keep `static_cast`. Enums are only counted. Unresolved types
   and casts in `#define` bodies are kept and **listed** (`unresolved`). If the
   type is certainly an integer but its exact width or signedness depends on the
   platform, do not stop here: reason on the worst case.
2. **Constant source.** A literal, `constexpr` variable, `sizeof`, `alignof`,
   `offsetof`, `std::numeric_limits<>::max()`, `CHAR_BIT`, a macro expanding to
   one of those, any constant expression: keep `static_cast`, even if the value
   is out of range of the destination. Count only (`constant`).
3. **`noexcept` context.** The cast is inside the body (including constructor
   initializer lists) of any enclosing function, method, constructor or lambda
   declared `noexcept`, `noexcept(true)`, `noexcept(<expression>)` (unless the
   expression is the literal `false`) or `throw()`, or inside a destructor or a
   deallocation function (implicitly `noexcept`): keep `static_cast` and
   **list** it (`noexcept`). `gsl::narrow` throws, which would terminate the
   program there.
4. **Proven safe on every target.** See the proof rules below. Keep
   `static_cast`. Count only (`proven-safe`).
5. **Intentional truncation or reinterpretation.** The code obviously wants the
   wrap-around or the bit pattern, and `gsl::narrow` would throw on legitimate
   values: hash and checksum arithmetic, modular arithmetic, byte extraction
   without a mask, the `std::isalpha(static_cast<unsigned char>(c))` idiom,
   `static_cast<HRESULT>(0x8007...)`, `static_cast<DWORD>(flags)` of a signed
   flag word, bit-pattern conversions of registers. Keep `static_cast` and
   **list** it (`intentional`). The intent must be evident from the code (names,
   neighboring bit operations, comments). If it is not, go to rule 6.
6. **Everything else: convert.**

## Proof rules (rule 4)

Value bits: an N-bit unsigned type has N value bits, an N-bit signed type has
N-1. The range of the source must be included in the range of the destination
on every target.

- **Strict widening**: unsigned → unsigned or signed → signed with destination
  at least as wide; unsigned → signed with destination **strictly** wider.
  Widths of `int`, `long`, `size_t`, `wchar_t`, `DWORD`... come from the platform
  files: take the narrowest case across the selected targets. A width you cannot
  find there is unknown: convert. Fixed-width types (`std::int32_t`...) are known.
- **Alias of the same type**: after alias resolution the two types are the same.
  Two distinct types of the same width (`long` and `long long`) are safe only if
  their signedness is equal.
- **Bounded by the expression**: a mask (`x & 0xFF`), a modulo by a constant
  (`x % 10`), a right shift that leaves few bits (`u32 >> 24`), `std::min`,
  `std::clamp`, a bitwise `|`/`&` of operands that all fit, a function with a
  documented small range (`std::popcount`, `std::countl_zero`...).
- **Dominating check in the same flow** (not a caller's promise, not a comment,
  not `assert`, which disappears in release): `if (v <= max)`, `if (v >= 0)`,
  an early return or throw, `std::in_range<T>(v)`, a `static_assert`.
- **Non-negative by construction** for signed → unsigned: loop index counting up
  from 0, a size or count returned by the standard library, an unsigned
  expression, a pointer or iterator difference of a valid range
  `static_cast<std::size_t>(last - first)` where `first <= last` holds by
  construction.
- **Platform guard**: the cast sits in an `if constexpr`, `#if` or `requires`
  branch that compares `sizeof` or `numeric_limits` and thereby proves the
  range (for example `if constexpr (sizeof(wchar_t) == sizeof(char16_t))`, or
  `if (value < 0x10000)` before `static_cast<char16_t>(value)`).
- **Integral promotion**: operands narrower than `int` are promoted to `int` (or
  `unsigned int`). Use the `int` width of the selected targets: on a 16-bit
  `int`, `uint16_t + uint16_t` wraps at 16 bits.

Not a proof: "values are small in practice", test data, a name or a comment, a
check in another function, `assert`, a bound that holds on only some targets.
Any doubt: rule 6.

## 3. Convert

- `static_cast<T>(expr)` → `gsl::narrow<T>(expr)`, with `T` written exactly as
  in the original. Keep the surrounding code unchanged: no other refactoring,
  no cleanup, no style churn.
- Add `#include <gsl/narrow>` to each file where you now use `gsl::narrow` and
  that does not include it. Insert it where the project's include ordering puts
  it. Do not check that the library exists, it is assumed.
- Add no `try`/`catch`, change no signature, add no comment about the cast.
