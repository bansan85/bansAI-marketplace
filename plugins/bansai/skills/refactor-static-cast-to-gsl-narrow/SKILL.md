---
name: refactor-static-cast-to-gsl-narrow
description: >-
  Replaces every integer static_cast that can lose a value (narrowing, signed to
  unsigned, unsigned to signed) with gsl::narrow, over a whole C++ project or a
  given path. Keeps static_cast when it can prove the cast is always safe
  (constants, sizeof, masks, dominating range checks, strict widening, ...), in
  noexcept code, and for enums. Starts by asking which platform families must be
  supported (PC, embedded, exotic), because integer widths depend on them. Ends
  with formatting, build, tests and one commit, and a report: converted /
  analysed per cast category, and the explicit list of conversions that had to
  be reverted. Trigger for: "replace static_cast with gsl::narrow", "make
  narrowing casts safe", "refactor-static-cast-to-gsl-narrow", "remplace les
  static_cast par gsl::narrow", "sécurise les casts d'entiers". Optional path
  argument; without it, the whole project. Modifies code and creates a commit.
  Never pushes.
---

# refactor-static-cast-to-gsl-narrow — safe integer casts

Input: an optional path (file, folder or glob) restricting the scope. Without
it, the whole project. Output: one commit and a report.

Principle: an integer `static_cast` that can change the value becomes
`gsl::narrow<T>(x)`, unless it can be **proven** safe on **every** target
platform. Any doubt: convert.

## Rules

- **Language.** Talk to the user in the user's language. Everything that ends
  up in git MUST be in English: code, comments, commit message.
- Never push, never amend, never rewrite history.
- The GSL is assumed available. Do not check for the library. The header is
  always `<gsl/narrow>`, added to any file where `gsl::narrow` is used and that
  does not include it yet.
- Integers only. Enums (including `std::byte`) stay `static_cast`, always.
- Never modify a test to make it pass.

## Cast categories

The categories catalog each conversion in the report. A cast belongs to the
**first** category that applies on at least one selected target (categories are
disjoint). "Integer" = built-in integer types and their aliases
(`std::size_t`, `std::uint32_t`, `DWORD`, project typedefs), `wchar_t`,
`char8_t`, `char16_t`, `char32_t`. Plain `char` counts as signed (worst case).

| # | Category | Source → destination |
|---|---|---|
| 1 | `narrowing` | destination narrower than the source (fewer bits), whatever the signedness |
| 2 | `signed-to-unsigned` | signed → unsigned, destination as wide or wider |
| 3 | `unsigned-to-signed` | unsigned → signed, destination as wide or wider |

`narrowing` is the main category and comes first: `int64_t` → `uint32_t` is
`narrowing`, not `signed-to-unsigned`. A cast is narrower if the destination
has fewer bits than the source on at least one selected target (for example
`size_t` → `uint32_t` on a 64-bit target).

Out of scope, never counted: same signedness and destination as wide or wider
on every target; `bool`; enums; floating point; pointers; class types.

## 1. Ask for the target platforms (first, before anything else)

Integer widths depend on the platform, so the verdict of every cast does too.
If the user's request does not give this information, ask. Never guess. In a
non-interactive session without it, stop and say why.

The questions come in **two successive rounds**. The details depend on the
families chosen, so they can only be asked after the user has answered the
first round. Never put a family question and a detail question in the same
call to the question tool.

1. **Round 1: the families, and nothing else.** One multiple-choice question
   (with the question tool if available), skipped if the request already names
   the families:
   - **PC**: desktop, server, Android, iOS, and GPU code (OpenCL, CUDA/HIP/SYCL,
     Metal).
   - **Embedded**: microcontrollers and DSPs, bare-metal or RTOS.
   - **Exotic**: legacy or exotic hardware (DOS/Win16, mainframes, non-x86/ARM
     servers, WebAssembly, eBPF, CHERI...).

   Wait for the answer.
2. **Round 2: the details of the selected families only**, in a new call. Ask
   nothing about a family that was not selected, and offer no option that
   belongs to another family (no Windows / Linux choice when only Embedded is
   selected). Skip what the request already says. The lists are examples: ask
   what changes a verdict.
   - PC: 32-bit builds supported (x86, ARM32)? Which OS (Windows is LLP64,
     Linux/macOS/Android/iOS are LP64)? GPU code in scope? Size-changing
     options (`-fshort-wchar`, `-D_FILE_OFFSET_BITS=64`, `-D_TIME_BITS=64`)?
   - Embedded: word size (8/16/32 bits)? Family (AVR, PIC, STM8, 8051, MSP430,
     RL78, C2000, Cortex-M, RISC-V, Xtensa...)? Toolchain and version? ABI
     options (`-mint8`, memory model near/far/large...)? Is the code shared with
     a PC build?
   - Exotic: which exact platform, ABI or data model, compiler?

   If a detail answer opens a further question that only it makes relevant
   (for example the toolchain once the word size is known), ask it in a third
   call.
3. "Don't know" means the broader set: take the worst case of the family.

The cast verdict holds only if it holds on **all** selected targets.

Then read the reference file of each selected family, in this skill's
`reference/` folder: PC → `platforms-pc.md`, Embedded → `platforms-embedded.md`,
Exotic → `platforms-exotic.md`. From them and from the user's answers, derive the
width, range and signedness of every integer type on every selected target.

## 2. Check the repository

- Run `git status --porcelain`. If the tree is not clean, stop and tell the
  user.
- If the current branch is the repository's default branch, ask before going on.
- Read `CLAUDE.md` if present. Extract the build, test and format commands.

## 3. Inventory

Scope = tracked C++ files under the given path (or the whole repository):
`git ls-files -- <path> '*.cpp' '*.cc' '*.cxx' '*.c++' '*.hpp' '*.hh' '*.hxx'
'*.h' '*.inl' '*.ipp' '*.tpp' '*.ixx' '*.cppm'`. Drop vendored and generated
code: `third_party`, `thirdparty`, `3rdparty`, `external`, `extern`, `vendor`,
`deps`, build output folders, files named `*.pb.*`, `*_generated.*`, `moc_*`,
`ui_*`, `qrc_*`, and files whose header says generated / do not edit. A path
given by the user is never dropped.

Count the files and the `static_cast<` occurrences. Print one line: scope,
files, occurrences. If there are no occurrences, stop.

## 4. Analyse and convert

Read `reference/decision-rules.md` and apply it to every `static_cast` of the
scope. Keep, for the report:

- per category: `analysed` (every cast of the category that you examined) and
  `converted`;
- the number of casts kept, by reason;
- the lists described in step 8, with `file:line`, the cast, its category and
  the reason.

## 5. Format

Format only the files you modified, in place, with the tools and pinned
versions the project uses: `clang-format -i <files>` for C/C++ sources. Use the
project's own launcher if `CLAUDE.md` names one. Do not run a script that
formats the whole repository.

## 6. Verify, and revert what fails

- Build every configuration your change can affect: at least the main one. If
  you touched code under a feature gate or a platform guard, build the matching
  reduced or other-platform configuration when the tooling is available. Note
  the ones you could not build.
- Run the project's whole test suite.
- A conversion that breaks the build (deduction, ambiguity, `constexpr` context,
  missing header, ...): put **that cast** back to `static_cast`, rebuild.
  Record it as `reverted-build` with its category, `file:line`, the cast, and
  the compiler error in one line.
- A test that now fails because `gsl::narrow` throws, or because a value
  changed: put **that cast** back to `static_cast`, rerun. Record it as
  `reverted-test` with its category, `file:line`, the cast, and the name of the
  failing test. The value change must be reviewed by a human.
- A reverted cast is no longer counted in `converted`.
- Give up after 3 failed attempts to get a green build and test run: revert all
  your changes (`git restore --staged --worktree` on the files you modified),
  check `git status --porcelain` is empty, and tell the user what you learned.
  Skip steps 7 and 8's table, keep its lists.

## 7. Commit

- If nothing was converted, there is nothing to commit; say so.
- `git add` explicit paths: exactly the files you modified. Never `-A`, `.` or
  `-u`.
- Invoke the skill `bansai:git-commit-already-added` with the Skill tool. The
  message MUST be in English and describe the refactoring (for example "replace
  integer static_cast with gsl::narrow").
- If a hook or a check rejects the commit, fix the cause once (for example a
  formatting fix, then re-stage your files) and commit again. If it still
  fails, leave the changes staged and tell the user.
- Never push. Never amend a previous commit.
- Check `git status --porcelain` is empty afterwards.

## 8. Final report

Nothing to resume on a later run: converted casts are no longer `static_cast`.

1. One table, one row per category (`narrowing`, `signed-to-unsigned`,
   `unsigned-to-signed`): `converted / analysed`, for example `42 / 118`. A
   total row. The commit hash.
2. Casts kept, counted by reason: `enum`, `constant`, `proven-safe`, `noexcept`,
   `intentional`, `unresolved`.
3. Lists, each entry `file:line`, the cast, its category, and the reason. They
   are the part the user must act on:
   - **Reverted casts** (`reverted-build`, `reverted-test`): ALWAYS present as
     its own section, first, with the build error or the failing test. Write
     "none" if there are none.
   - `noexcept`: with the name of the enclosing function.
   - `intentional` truncations or reinterpretations.
   - `unresolved`: source type not resolved, not an integer, or cast inside a
     macro.
4. The configurations that could not be built.

Casts kept as `enum`, `constant` or `proven-safe` are only counted, not listed.
