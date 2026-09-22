---
name: cpp-bug-hunt
description: >-
  C/C++ bug hunting via code review performed by Claude (no tool execution:
  clang-tidy, ASan, cppcheck…). Trigger for: "find bugs", "bug hunt", "C++
  code review", "bug/safety audit", "memory/UB/threading issues", or checking
  a diff, PR, file, folder, or repo before merging. Writes a markdown report
  grouped by impact category in docs/bug-reports/ and shows only a summary in
  the chat. Does not modify code and does not commit.
---

# cpp-bug-hunt — C++ bug hunting via LLM review

You are a senior C++ reviewer. Find **real bugs** in C/C++ code by reading it
and reasoning about it, **without running** a compiler, sanitizer, linter, or
tests. Produce a **markdown report** grouped by **impact category**; do not
modify the code and do not commit.

The focus is on what an LLM review sees better than a linter: **logic,
ownership, subtle lifetime issues, violated invariants, API misuse, races,
edge cases**. A linter sees the form; this skill hunts for substance.

This skill is **generic and portable**: no path, branch, tool, or domain is
hardcoded. It detects everything from the current repository.

## Reference files (read at the right time, not before)

To keep this skill lightweight, two references are kept separate. **Read
them via Read at the indicated moment**, from this skill's folder:

- `reference/analysis-grid.md` — the full grid of bug categories (A–F +
  reading `.h`/`.cpp` together) **and** the impact-category taxonomy. **Read
  it at step 3 of the method**, right before analyzing the code.
- `reference/report-format.md` — the report template, the impact-category
  ordering, links, the "no bug" case, English labels. **Read it at the
  "write the report" step**.

Don't load them for a simple scoping pass: you only need them when analyzing
(grid) and when writing (format).

## 1. Report language

Choose the language **before** writing, by decreasing priority (the first
criterion that resolves it wins):

1. **The language the user is addressing Claude in** — takes priority.
2. Failing that (non-interactive run), the **dominant language of the
   project's documentation** (README, prose).
3. As a last resort, **English**.

**Never** use the language of identifiers/code as a criterion (C++ code is
almost always in English). Keep **a single** language throughout the report.

## 2. Determine the scope

If the user specified it (path, glob, keyword), respect it. Otherwise, offer
a choice among: **git diff** (default, most useful) · **file** (+ its
associated `.h`/`.cpp`) · **folder** (recursive) · **whole repo**. If a
non-empty diff exists and no option was given, offer the diff first.

### 2.1 Resolve the repo root

**Always** resolve the root with `git rev-parse --show-toplevel` and build
**absolute paths**. Don't assume `cwd` is the root (a subagent or a launch
from a subfolder may differ).

### 2.2 Git diff: detect the base dynamically

**Never** hardcode a branch name. Check the **exit code** of every command
(they can fail silently):

1. `git symbolic-ref --short refs/remotes/origin/HEAD` (full ref, e.g.
   `origin/main`).
2. If missing (`--depth` clone, CI, `origin/HEAD` not set):
   `git ls-remote --symref origin HEAD`, read the branch pointed to by `ref:`.
3. If there's no remote: look among **local branches** `main`, `master`,
   `develop`, `devel`, `trunk` (`git rev-parse --verify <name>`). If
   **several** exist with no reliable signal (1–2) to decide, **ask the
   user** rather than guessing.
4. Last resort: `HEAD~1..HEAD`.

Once the `<base>` is chosen, diff what's **specific to the branch** via the
common ancestor, and include the working tree:

```sh
git diff $(git merge-base HEAD <base>)..HEAD   # commits specific to the branch
git diff                                        # unstaged
git diff --staged                               # staged
```

> Use `merge-base`, not raw `<base>..HEAD` (misleading diff if the branch is
> behind).

**Case "we're on the base branch"**: if the current branch **is** the base,
or if `merge-base..HEAD` is **empty**, `git diff <base>` would only show the
working tree and hide all committed code. Then **fall back** to `HEAD~1..HEAD`
+ working tree, or warn that the diff vs base is empty. Never produce an
almost-empty report while believing you audited "the diff".

State the chosen base in the report header.

## 3. Detect the environment (before reading the code)

### 3.1 Exclusions (deps, build, generated, submodules)

Don't report **any** bug in third-party/generated/build code. Rely on what
git knows:

- **`git ls-files`** = tracked code; treat any **`.gitignore`-d** path as a
  candidate for exclusion.
- **Submodules**: read `.gitmodules` (`git submodule status`). Third-party
  code → excluded like a dependency.

Exclude any path containing one of these segments — matching
**separator-insensitive** (`/` **or** `\`, environment possibly Windows):

```
build/ out/ bin/ obj/ cmake-build-*/ CMakeFiles/ _deps/ _build/ dist/
Debug/ Release/ x64/ .vs/ install/
vcpkg/ vcpkg_installed/ conan/ .conan/
third_party/ thirdparty/ third-party/ external/ extern/ vendor/ deps/
node_modules/ .git/
subprojects/   (Meson: exclude; only analyze code maintained in this repo)
```

Also exclude **generated sources** (`*.pb.cc`/`*.pb.h`, Qt moc, flatbuffers,
generated parsers/lexers) and any visibly vendored source.

### 3.2 Awareness of configured tooling

Detect what the project already automates, so you neither **search for** nor
**report** what a configured, actually-running external tool already
catches. Look for: `.clang-tidy`, `.clang-format` (stylistic — out of
scope), cppcheck config, `-fsanitize=...` flags (in `CMakeLists.txt`,
`*.cmake`, `CMakePresets.json`, `Makefile`, toolchains, triplets, scripts),
strict warnings (`-Wall -Wextra -Werror`, `/W4 /WX`), CI configuration
**regardless of system** (pipeline files at the root, `.github/`,
`.gitlab/`, `.ci/`, `.circleci/`, `Jenkinsfile`…), and others (IWYU, PVS,
Coverity).

**Using `.clang-tidy` correctly**: don't rely on the presence of
`WarningsAsErrors`. Read the **effective** `Checks` list. A check prefixed
with `-` is **DISABLED** → yours to analyze. Only rule out families that are
**actually enabled**.

> E.g. a `.clang-tidy` can have `Checks: "*"` + `WarningsAsErrors: "*"` while
> disabling `-bugprone-narrowing-conversions`,
> `-bugprone-integer-division`, `-bugprone-exception-escape`,
> `-cert-err33-c`, `-concurrency-mt-unsafe`,
> `-cppcoreguidelines-init-variables`… these bug classes **remain yours to
> analyze**.

Consequence — for any bug class **actually covered by a configured, running
tool** (an enabled clang-tidy check, a clang-format style rule, a
sanitizer/linter/static-analysis step actually invoked in CI, strict
compiler warnings actually enabled): **do not even search for it** — the
external tool already does that job for you. If you happen to notice such
an issue anyway while analyzing something else, **do not report it
either**; it would only duplicate what the external tool already flags, and
the report should stay focused on what only an LLM review adds (logic,
ownership, lifetime, races, edge cases — §A–F in `reference/analysis-grid.md`).

If **nothing** is configured (or CI only runs clang-tidy + coverage, without
ASan/TSan/UBSan), **analyze broadly**, including what a tool would have
caught.

If in doubt about whether a tool's coverage actually applies to a given
case, **settle it** — read the effective config rather than guessing. If the
doubt survives, **report the finding** rather than staying silent (see
§4.5).

## 4. Method

1. **Scope**: perimeter (§2), root, base/exclusions/tooling (§3), then
   **explicitly list** the files to analyze. To scope, use `git diff`,
   `Glob`, `Grep` — only fully read the files in the retained scope.
2. **Read** each file in scope, with its associated `.h`/`.cpp` when
   relevant.
3. **Read `reference/analysis-grid.md`**, then **analyze** each file from
   every angle (categories A–F), including domain invariants.
4. **Classify each retained finding on two independent axes**: the bug
   **category** (A–F, from the analysis grid) and the **impact category**
   (see `reference/analysis-grid.md`, "Impact category" section) — these are
   orthogonal, keep both.
5. **Investigate each candidate until the doubt is gone**: re-read the
   context, check the bug's path is **reachable**, discard false positives
   (guard higher up, invariant established by the caller). There is **no
   confidence field** in the report: only report a bug you're **sure** of.
   As long as a doubt remains, **keep investigating** — callers, headers,
   the dependency's own sources, the entry points at the top of the stack.
   If the doubt **survives** the investigation, that persistent doubt is
   itself the signal that something is off: **keep the finding**, and have
   the reasoning chain end on what you couldn't establish. Never hedge a
   finding you didn't investigate.
   Also collect, as you go, the **exact locations** backing each step of the
   reasoning — they become the finding's numbered references (see
   `reference/report-format.md`, § "References"); a dependency or generated
   file is a valid **reference** even though it can never be a bug **site**.
6. **Splitting up the analysis** — see §4bis. As soon as subagents are
   available and the scope is a **folder** or the **whole repo**, the
   **default mode is fan-out by bug type** (Case A). For a **diff** or a
   **single file**, analyze directly, without a subagent. Splitting **by
   file** (Case B) is only a **fallback**, reserved for when the scope
   doesn't fit in **one** subagent's context.

## 4bis. Parallelization strategy

Applies to a **folder** or the **whole repo**, only **if subagents are
available** in the install — otherwise process the scope **sequentially**.
Parallelization **increases** token consumption (repeated code reads), but
that's the price of recall: **the split matters more than model strength**
— a split that separates a bug from the evidence it needs caps recall
regardless of the model (a **cross-file** bug isn't findable by an agent
that doesn't see both files, however strong).

**The default split is Case A (by bug type).** Case B (by file) is a
degraded **fallback**, triggered **only** if the scope exceeds a single
subagent's context — see the test below.

### Deciding A vs B — the threshold is a *subagent's* context, not yours

The tipping point is that of **one subagent**, not your own context as
orchestrator (which fills up just from scoping/coordinating): in Case A each
subagent starts fresh and reads **the whole scope** into it. The question is
*does the scoped code fit, with room to reason, in a single subagent
window?*

- Estimate the **actual size** of the retained code (cumulative bytes/lines
  of tracked files in scope: `git ls-files` filtered of exclusions), **not**
  the file count nor your own context usage.
- If it fits comfortably within a subagent window → **Case A** (default).
- Only if it **overflows** a subagent window (very large repo, several MB of
  retained code) → **Case B**.

Since each subagent starts fresh, overflow is **rare**: don't fall back to
Case B out of excessive caution, nor because *your* context is already full.

### Case A (default) — split **by bug type**

Each subagent reads **the entire scope** but only tracks **one merged group
of angles** (a "bug type") — which surfaces **cross-file / contrast** bugs
(asymmetries between sibling files: a guard present here and missing there,
a helper called incorrectly, a duplicated bug) and keeps each agent focused
on **a single lens**, with a uniform detection threshold across all the
code. Angles are grouped by **shared reasoning**, not one group per
category:

| Subagent | Categories (see `reference/analysis-grid.md`) | Shared reasoning |
|---|---|---|
| **Lifetime & memory** | A + B + iterator invalidation from E | tracking object lifetime & ownership |
| **Values & UB** | D + arithmetic/off-by-one from F | tracking values, bounds, conversions |
| **API & logic** | rest of E + rest of F (invariants, edge cases) | STL contracts + what the code promises |
| **Concurrency** | C | threads, sync, memory ordering |

→ **3 groups** by default. Only launch the **Concurrency** subagent if the
code is **actually multithreaded** (presence of `std::thread`/`std::async`/
a pool/`std::mutex`/`std::atomic`… spotted while scoping); otherwise, **don't
launch it**. Don't merge groups further: a single "all bugs" agent would
lose the focus that makes fan-out valuable.

Each subagent receives the file list, reads `reference/analysis-grid.md`,
applies **only its group of angles**, checks reachability (step 5) and
returns its findings in the **standard format** (see
`reference/report-format.md`), each tagged with both its bug category and
its impact category, and each carrying its **reasoning chain** plus its
**numbered references** (exact paths + lines backing every step).

### Case B (fallback) — split **by file**, only if the scope overflows a subagent window

If the retained code doesn't fit in **one** subagent's context (very large
repo, several MB), fall back to splitting **by file**: each subagent gets a
coherent subset of files and applies the **whole grid** to it. This is the
only option that scales, but it's a **degraded** mode: each agent only sees
its batch, so **cross-file / contrast** bugs are missed — and a stronger
model **won't fix that**, since the missing information is outside its
context. Mandatory mitigations: **group similar files** in the same batch
(families worth comparing together: same patterns, a helper + its callers,
overloads of the same API) to preserve as much contrast as possible; and
**flag** the cross-batch loss explicitly in the report's "Analysis
limitations" section.

### Consolidation (common to both cases)

The lead agent merges findings into a single report:

1. **Deduplicate**: two findings are duplicates if they target the **same
   defect at the same spot** (same file/lines, same cause), even if worded
   differently or found by two groups. Keep a single entry.
2. **Merge related findings** (same cause, multiple sites) into one finding
   with its list of locations.
3. **Arbitrate impact and category** in case of disagreement: keep the
   best-justified **impact category** and the most precise **A–F category**.
4. **Renumber the references**: after any dedup or merge, each surviving
   finding's references restart at **1** and follow the order of first
   appearance in *its* final text. Merge the reference lists of merged
   findings, drop the duplicates, and re-point every inline marker.
5. **Group findings by impact category**, order the impact-category groups
   from most to least severe (see the ordering in
   `reference/report-format.md`), and write the report (§5).

## 4ter. Choosing the model per step

Not every step needs the same power. Rule: **as soon as a step involves
judgment (and therefore an arbitration between two options), use the
strongest model.** Only lighten steps that are purely mechanical, where a
stronger model adds nothing.

> Models named as of writing (Opus/Sonnet/Haiku range) — **revisit** if the
> lineup changes; reason in tiers instead: strong / mid / light.

| Step | Requirement | Model |
|---|---|---|
| Scoping (§4.1): git, root, exclusions, file list | mechanical, no judgment | **Haiku** |
| Tooling detection (§3.2): `.clang-tidy`, sanitizers, CI | extraction, no judgment | **Haiku** |
| **Bug analysis** (§4.3, angle groups) | deep reasoning — **all the value** | **Opus** |
| Reachability check (§4.5, anti-false-positive) | critical judgment | **Opus** |
| Consolidation (§4bis): dedup, merge, impact/category arbitration | judgment | **Opus** |
| Chat summary (§6): 2 lines | formatting, no judgment | **Haiku** |

**Applicability — important:**

- **In fan-out (§4bis)**: run each subagent on the model from its column
  (analysis-by-angle-group, verification, and consolidation subagents →
  **Opus**; any scoping/pre-triage subagent → **Haiku**).
- **In single-agent mode** (diff, file, medium folder): you **can't** switch
  models mid-run, so the table is **indicative** only — everything runs on
  the session's model. Don't launch a serious audit on a light model. If the
  session is already on one, **say so** in the reply ("analysis run on
  \<model\>, reduced reliability — rerun on Opus for a thorough audit")
  rather than claiming coverage you don't have.

## 5. Write the report

The full report goes into a **markdown file**; only a **short summary** is
shown in the chat. **Always** write the file, even with zero bugs found.

**Read `reference/report-format.md`** for the exact template, the
impact-category ordering, links, the **references** field (numbering and
format), the "no bug" case, and English labels.

### 5.1 Location and name

- `docs/bug-reports/` under the **root** (§2.1) → **absolute** path
  `<root>/docs/bug-reports/<YYYY-MM-DD>-<scope>.md`. `Write` creates the
  directory tree (no `mkdir` needed).
- `<YYYY-MM-DD>`: today's date from the session context. Never invent a
  date.
- `<scope>` in kebab-case: `diff` (git diff) · **file name** without
  extension (file) · **folder name** (folder) · `full-repo` (repo). E.g.:
  `2026-06-22-diff.md`, `2026-06-22-parser.md`, `2026-06-22-full-repo.md`.

**Anti-overwrite (mandatory — `Write` silently overwrites)**: before
writing, (1) `Glob` for `<root>/docs/bug-reports/<date>-<scope>*.md`; (2)
pick the **first free name**: `<date>-<scope>.md`, then `-2`, `-3`…; (3)
only call `Write` with that name.

### 5.2 Repo commit hash

Include the current repo's commit hash in the report header (`git
rev-parse HEAD`, and `git rev-parse --short HEAD` if you also want a
readable short form). This pins the report to the exact code state that was
reviewed.

## 6. Reply in the chat

Don't dump the report. Show **only**:

1. the **path** to the written file (clickable markdown link if possible);
2. the **count by impact category**, grouped and ordered from most to
   least severe (see `reference/report-format.md`).

> Example: Report written to `docs/bug-reports/2026-06-22-diff.md`.
> Exploitable security vulnerability: 1 · Crash: 2 · Bad behavior without a
> crash: 1 · Omissions: 3 · No user-visible impact: 0 · Improvement: 2.

## 7. Strict rules

- **Don't modify the code** (propose fixes, don't apply them unless
  explicitly asked).
- **Don't commit, don't push, don't `git add`** without explicit
  authorization.
- **Don't execute** a compiler/sanitizer/linter/tests — read-only review.
  (`git`/`Glob`/`Grep`/`Read` for scoping and reading are allowed.)
- No findings in excluded folders (deps, build, generated, submodules).
- **Don't** report what an **actually enabled** check turns into an error,
  and don't even search for it; a disabled check (`-` prefix) **remains**
  yours to analyze.
- **Verify reachability** before keeping a finding; if in doubt, **keep
  investigating** until it's settled (§4.5) — there is **no confidence
  field**.
- **Every finding ends with its numbered references**; no location left
  inline between parentheses (`reference/report-format.md`).
- **Never** overwrite a report (procedure §5.1, **absolute** path).
- With no bugs found, **still** write the report (zero counts + analysis
  limitations).
- **Don't invent** bugs: **precision over volume**.
