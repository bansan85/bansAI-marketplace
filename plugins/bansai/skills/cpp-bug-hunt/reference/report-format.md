# Bug report format

Reference loaded by the `cpp-bug-hunt` skill when writing the report.
Write in the **chosen language** (see SKILL.md §1), grouped by **impact
category**, categories ordered from most to least severe (see below). Adapt
every label (headings, impact-category names, field names) to that language.

## Writing style

Write every finding so it's **understandable by a sharp 16-year-old**,
while keeping the **technical precision of a software engineer with 10
years of experience**. The reader is a competent engineer who does **not**
know this codebase's architecture — don't lean on internal jargon without
making it clear from context (name a subsystem or convention the first time
it's used, in plain words).

**Naming budget** — this applies to **every prose field** of a finding
(title, Reasoning, Trigger scenario, Consequence, Suggested fix): each one
cites **at most 2–3** variable/function/identifier names. Past that,
describe the role in plain words ("the source buffer", "the release
callback", "the lock held by the caller") instead of stacking identifiers —
the snippet already carries the exact names, the prose carries the
reasoning, and the **References** field carries the precise locations. The
References field itself is **exempt** from this budget: it's a list of
pointers, not prose.

## Template

````markdown
# C++ Bug Review — <scope>

- **Date**: <YYYY-MM-DD>
- **Repo commit**: <sha from `git rev-parse HEAD`>
- **Scope**: <precise description: diff range, file, folder, repo>
- **Comparison base** (if diff): <detected ref/range>
- **Quality tooling detected**: <clang-tidy (active/disabled checks) /
  cppcheck / sanitizers / strict warnings / none> — and what is therefore
  deliberately skipped, or, conversely, analyzed broadly.
- **Files covered**: <list>
- **Count by impact**: <impact category 1> n · <impact category 2> n · …
  (ordered from most to least severe)

## Findings

### <Impact category 1 — most severe>

#### <short title>

**Impact**: <impact category>
**Category**: <Memory / Ownership / Concurrency / UB / STL / Logic>

**Location(s)**:
- `<path-relative-to-root>:<line>`
  ```cpp
  39  ...
  40  ...
  41  ...
  42  <flagged line>
  43  ...
  44  ...
  45  ...
  ```
  (one bullet + snippet per location if there are several; if there's only
  one, drop the bullet and show a single snippet right under the path)

**Reasoning**: the **chain of reasoning** that led you to call this a bug,
written as a **bullet list** — one step per bullet, in the order you
established them, each carrying its reference marker `[n]` where it rests
on the code. Don't re-explain in detail how the code works: the chain has
to be enough to understand it. End on the step that makes the defect
inescapable.

**Trigger scenario**: the sequence of events or input that provokes the
defect (state, call sequence).

**Consequence**: crash, corruption, wrong result, leak…

**Suggested fix**: the recommended correction (text or short snippet),
without applying it.

**References**:
1. [<path>:<line(s)>](../../<path>#L<line>) — <what this spot shows, one
   short clause>
2. …
````

(then the next finding in this same impact category, then one section per
impact category that has findings, in severity order)

````markdown
## Analysis limitations
What couldn't be verified: missing context, unseen callers, excluded
generated/third-party code, tooling whose exact coverage is uncertain…
````

## References

Every finding ends with a **References** field. It replaces the habit of
dropping locations inline between parentheses: **anything you would have
put in parentheses to back a claim becomes a numbered reference.**

**What counts as a reference**

- A pointer to code you cite in the prose — "lines 68-73", "line 118", "the
  constructor", "the contract documented in the header".
- A file, class, or function you name to support a step in the reasoning
  chain — "`stream.cpp`, the append function has no `try`/`catch`",
  "verified in `VET-008/consumer.cpp` and `VET-021/consumer.cpp`".
- A third-party or dependency source you relied on — an installed header, a
  vendored library's source, a generated file. Those are **excluded from
  reporting** as bug sites (see SKILL.md §3.1) but are perfectly valid as
  **evidence**, and must be referenced like any other.

**Numbering**

- Numbering restarts at **1 for each finding** and increments in **order of
  first appearance** in that finding's text.
- Inline, a reference is **just its number in brackets**: `[1]`, `[2]`. No
  parenthesized path, no line number left in the prose — the number carries
  it.
- The same location cited twice within one finding reuses **the same
  number**.
- Markers are allowed in any prose field of the finding (Reasoning, Trigger
  scenario, Consequence, Suggested fix); the numbering is shared across all
  of them.

**The References list**

- A numbered list at the very end of the finding, in numeric order.
- Each entry is a **complete, clickable link including the line numbers**,
  followed by a short clause saying what that spot shows.
- Use a line **range** when the evidence is a block: `src/foo.cpp:68-73` →
  `[src/foo.cpp:68-73](../../src/foo.cpp#L68-L73)`.
- A reference with **no** line number is only allowed when the evidence is a
  whole file's absence of something ("no handler anywhere in this file");
  otherwise always pin the lines.

**Example** — the prose stays readable, the evidence stays checkable:

```markdown
**Reasoning**:
- The library's root exception class does **not** derive from
  `std::exception`: the installed header declares it with no base class
  [1], so a catch on the standard base type never catches it.
- The constructor knows this — it wraps one call and retranslates the
  exception into `std::runtime_error` [2] — but it is the **only** one of
  the class's five entry points into that library to do so [3].
- The dependency doesn't cover the gap either: it converts only on the
  read path [4], and its append function has no handler at all [5].
- At the top of the stack, each entry point catches the standard base type
  only [6] — so nothing catches this exception, anywhere.

**References**:
1. [vcpkg_installed/x64-windows/include/H5Exception.h:28](../../vcpkg_installed/x64-windows/include/H5Exception.h#L28)
   — root exception class declared with no base class
2. [src/urx_writer.cpp:68-73](../../src/urx_writer.cpp#L68-L73) — the only
   retranslation into `std::runtime_error`
3. [src/urx_writer.cpp:59](../../src/urx_writer.cpp#L59),
   [src/urx_writer.cpp:118](../../src/urx_writer.cpp#L118) — unguarded
   entry points
4. [external/urx/reader_impl.inl:212](../../external/urx/reader_impl.inl#L212)
   — read path converts, write path doesn't
5. [external/urx/stream.cpp:84-97](../../external/urx/stream.cpp#L84-L97)
   — append function, no handler
6. [tests/VET-008-urx-writing/consumer.cpp:41](../../tests/VET-008-urx-writing/consumer.cpp#L41)
   — top-level handler catches the standard base type only
```

## Location links

The path cited is **relative to the repo root**. Since the report lives in
`docs/bug-reports/`, a clickable markdown link must go **up** two levels
(`../../<path>`) to resolve correctly, e.g.
`[src/foo.cpp:42](../../src/foo.cpp#L42)`. The `#L<line>` anchor is only
honored by some forges and stays indicative; the plain `path:line` pair is
what matters.

## Impact categories

Definitions, examples, and severity ordering: `reference/analysis-grid.md`,
"Impact category" section. Group findings under those six headings (§
"Findings" above) in that same order, **only including headings that have
at least one finding**.

## Categories (A–F)

Bug category (Memory, Ownership, Concurrency, UB, STL, Logic —
`reference/analysis-grid.md`) is a separate field from impact. Report both,
each on its own dedicated line, as in the template.

## Certainty — there is no confidence field

A finding is in the report or it isn't; **never** add a confidence or "to
confirm" field. See SKILL.md step 5 for the investigation procedure
(keep investigating until the doubt is resolved or, if it persists, becomes
the finding's closing point). Never hedge a finding you didn't investigate.

## No bugs found

Write the file **anyway**: the header with its zero counts, the
"Analysis limitations" section, and an explicit statement that no findings
were made. A documented absence of bugs is still useful information.

## Writing in a language other than English

Translate every label — impact-category names (e.g. "Exploitable security
vulnerability" → "Faille de sécurité exploitable" in French), bug-category
names, field names (`Reasoning` → "Cheminement", `References` →
"Références", `Trigger scenario` → "Scénario déclencheur"…) and every
section heading — into the chosen language, while keeping the same six
impact categories in the same order, the same fields, and the same meaning.
Reference **numbering and links stay as they are**; only the trailing clause
of each reference entry is translated.
