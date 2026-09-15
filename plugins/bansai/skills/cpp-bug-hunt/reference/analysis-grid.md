# C++ bug analysis grid

Reference loaded by the `cpp-bug-hunt` skill at analysis time.
Review the code from each of these angles. Not every category applies to
every codebase — skip the ones that aren't relevant. For each category:
*what to look for* + *warning signs* worth a closer look.

## A. Memory
- **Use-after-free / use-after-return**: pointer or reference to a local
  returned or stored beyond its scope; returning the address of a local.
- **Use-after-move**: object read/reused after `std::move` (beyond a
  reassignment).
- **Double free**, `delete` vs `delete[]`, `free` on a `new`, mixing
  allocator/deallocator.
- **Out-of-bounds access**: unchecked `operator[]`, pointer arithmetic,
  `memcpy`/`memmove`/`memset` with the wrong size, off-by-one (`<=` instead
  of `<`).
- **Leaks**: `new`/`malloc` not freed on every path (including
  exception/early return); `shared_ptr` cycles.
- **Reading uninitialized memory**: uninitialized variable or member not set
  by the constructor, `reserve` confused with `resize`.
- **Null pointer dereference**; null `this`.
- **Signals**: `&local` escaping, `.data()`/`.c_str()` kept around, `.get()`
  of a smart pointer stored elsewhere, `auto&` bound to a temporary, `[&]`
  capture in a deferred callback.

## B. Lifetime & ownership
- **Dangling pointers/references/iterators**; `string_view`/`span`/reference
  to a **destroyed temporary** (e.g. `std::string_view sv =
  function_returning_string();`).
- **Invalidation** after modifying a container: `push_back`/`insert` that
  reallocates, `erase`.
- **Capture by reference** in a lambda, thread, `std::function`, or callback
  that **outlives** the scope of its target.
- **Smart pointer misuse**: `shared_ptr` cycles, raw `new` mixed with smart
  pointers, two `shared_ptr`s built from the same raw pointer, shallow-copied
  `unique_ptr`, double ownership.
- **Missing RAII**: a resource with no destructor, manual `lock()` without
  `lock_guard`/`scoped_lock`/`unique_lock`.
- **Inconsistent rule of 0/3/5**: a class managing a resource without
  correct copy/move → shallow copy, double free, invalid state after move.
- **Member initialization order** (determined by declaration order),
  destruction order, static lifetime.
- **Signals**: an owning raw pointer member, `delete this`, `release()`
  without the owner picking it up, a `static`/singleton holding a reference
  to something transient.

## C. Concurrency (if the code is multithreaded)
- **Data race**: shared state read/written by multiple threads without
  synchronization (no mutex, no `atomic`).
- A variable meant to be `atomic`/mutex-protected that isn't, or protected by
  a different mutex depending on the access site.
- **Deadlock**: inconsistent lock ordering, reentrant lock on a non-recursive
  mutex, lock held during a blocking call/callback.
- **Condition variables without a predicate** (missed wakeups / spurious
  wakeups).
- **Atomics** with too weak a memory order; wrong visibility assumptions.
- Non-thread-safe lazy init, broken double-checked locking, misused
  `std::call_once`; a shared modifiable local `static`.
- `volatile` wrongly used as a synchronization tool.
- **Signals**: shared mutable members, `std::thread`/`std::async`/pool,
  asynchronous callbacks.

## D. Undefined behavior (UB)
- **Signed integer overflow**; negative shift or shift `<<`/`>>` ≥ type
  width; division/modulo by zero.
- **Reading an uninitialized variable**; reading an inactive union member.
- **Potential `nullptr` dereference** (unchecked return of
  `find`/`dynamic_cast`/allocator).
- **Signed/unsigned comparison**, narrowing conversion that changes the
  value, silent truncation (`size_t` → `int`).
- **Strict aliasing**: dubious `reinterpret_cast`, misaligned dereference;
  `const_cast` followed by writing to a truly `const` object.
- **Unspecified evaluation order** exploited by mistake (multiple side
  effects on the same object within one expression).
- **ODR**; mismanaged `static`/`inline`.
- `printf`/format string with a specifier that doesn't match the type.
- **Signals**: chained casts, arithmetic mixing signed/unsigned, `int` used
  for sizes, bitwise shifts on signed integers.

## E. STL & standard API
- **Invalidated iterator/reference** reused (modifying a container while
  iterating); malformed ranges.
- **Ignored return value** that carries an error or a result
  (`[[nodiscard]]`, error code, untested `std::optional`/`expected`).
- **Container/algorithm misuse**: `operator[]` that **inserts** on
  `map`/`unordered_map` instead of `at`/`find`; `erase` without the
  erase-remove idiom; a comparator violating strict weak ordering;
  inconsistent hashing; wrong assumptions about order or uniqueness.
- **Exceptions**: leak on an exception path, violated `noexcept` (an
  exception escaping → `std::terminate`), a destructor that can throw, an
  exception caught **by value** (slicing).
- **Object slicing** (copying a derived object into a base by value).
- **Unintended expensive copies**; a `std::move` that doesn't move; a
  moved-from object reused.
- **Signals**: `.find()`'s return value not compared to `.end()`,
  `front()`/`back()`/`top()` on a possibly empty container, `.at()` vs `[]`
  poorly chosen.

## F. Logic & invariants
- **Inverted condition**, `=` instead of `==`, `&`/`|` instead of `&&`/`||`,
  off-by-one, wrong `<`/`<=` choice, operator precedence.
- **`switch`**: `case` without `break` (unintentional fallthrough), missing
  `default`, uncovered enum value.
- **Unhandled edge cases**: empty input, zero-size container, negative
  value, `NaN`/`inf`, capacity overflow, max index.
- **Ignored error codes / return values**; swallowed exceptions.
- **Violated domain invariant** — reason about **what the code promises**,
  not just memory safety. State the invariant **generically**, based on what
  you observe in **this** project: consistency of dimensions/sizes between
  related structures, indices within a valid range, a function's
  pre/postconditions, unit/scale consistency for any quantity the module
  manipulates, expected monotonicity or ordering, a respected state-machine
  invariant, consistency between related fields of a struct. Spot these
  invariants in comments, asserts, and names, then check they hold on
  **every** path.
- **Leaked non-memory resources** (files, sockets, handles, locks) on error
  paths.
- **Dead code / unreachable branch** hiding intent; an always-true/false
  condition.
- **Signals**: `// TODO`/`// FIXME`/`// HACK`, asymmetry between two
  branches that should be symmetric, repeated magic constants, copy-paste
  with a variable left unrenamed.

## Reading `.h` and `.cpp` together

A bug is often visible at the **declaration/definition junction**. For a
symbol in scope:

- read the **header** (`.h`/`.hpp`/`.hh`) for the **contract**: signatures,
  default values, `noexcept`/`const`/`[[nodiscard]]`, pre/postconditions in
  comments, documented ownership, and **member declaration order** (which
  determines initialization order — a classic bug source);
- read the **source** (`.cpp`/`.cc`/`.cxx`) for the actual **implementation**,
  and check it **honors the header's contract** (e.g. a `noexcept` function
  that can actually throw, an unguaranteed postcondition);
- spot **divergences**: a default value contradicted elsewhere, a shadowed
  overload, a subtly different signature between the declaration and
  definition of a template.

For a header alone, reason about the contracts and likely usage. For a
class, check that constructor, destructor, copy, and move are **mutually
consistent**.

## Impact category

In addition to the bug **category** above (A–F), classify each finding into
an **impact category** from the list below. This is a **second, orthogonal
axis** — a finding always has both a category (A–F: what kind of defect it
is) and an impact category (what happens as a result).

This list is a reasoning aid, not a **closed grid**: the examples given for
each category are **illustrative, not exhaustive**. A bug whose impact
matches a category belongs there even if it resembles none of the listed
examples. Never force a bug into the closest category if none actually
fits.

- **Omissions** — missing or incomplete handling of an error case or edge
  case. E.g.: unchecked `malloc`/`new` return value, `switch` without
  `default`, uncaught exception, ignored system-call return code, an
  unhandled edge case.
- **Bad behavior without a crash** — the program keeps running but produces
  an incorrect result or gets stuck. E.g.: a badly bounded loop, a silent
  overflow, a race condition, a conditional deadlock, an inconsistent state
  after an exception, comparing floats with strict equality.
- **Crash** — the program stops abruptly. E.g.: double free,
  use-after-free, null dereference, out-of-bounds access, stack overflow, an
  invariant assertion violated in release builds.
- **Bug without user-visible impact** — a real defect with no observable
  consequence for the end user. E.g.: a memory leak on a rare path, an
  unclosed handle, a mutex left unlocked right before the process exits,
  dead computation, an incorrect log line, a resource leak on a debug-only
  path.
- **Exploitable security vulnerability** — an attacker can turn the defect
  to their advantage, often without causing a crash. E.g.: a buffer overflow
  on attacker-controlled input, a format string bug, an injection, an
  exploitable use-after-free, an out-of-bounds read exposing memory, an
  authentication bypass.
- **Improvement** — not strictly a bug, but an optimization or quality
  opportunity. E.g.: an unnecessary copy, repeated allocation in a hot loop,
  a suboptimal algorithm, an overly broad lock, duplicated logic.

### Ordering impact categories by severity

When grouping a report by impact category (see `reference/report-format.md`),
order the groups from **most to least severe**:

1. **Exploitable security vulnerability** — worst regardless of whether it
   crashes, since an attacker actively controls the outcome.
2. **Crash** — certain, visible disruption of service.
3. **Bad behavior without a crash** — silently wrong results or a stuck
   program; often harder to detect than a crash, and just as damaging to
   correctness.
4. **Omissions** — a real gap in error/edge-case handling, but one that
   hasn't (yet) been shown to misbehave or crash.
5. **Bug without user-visible impact** — a genuine defect with no
   demonstrated consequence for the user.
6. **Improvement** — not a bug; lowest priority in a bug report.
