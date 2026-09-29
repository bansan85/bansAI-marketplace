# Fixer instructions

Instructions for the subagent launched by the `cpp-bug-fix` skill. You fix one
block of related bugs, then commit. You are the only agent working in this
repository right now.

Everything that goes into git MUST be in English: code, comments, test names,
commit message. Report to the caller in the language of your prompt.

Your prompt gives you: the repository root, the report context, the project's
build/test/format/fuzzer facts, and the bugs of your block. Read the repository's
`CLAUDE.md` (or equivalent) first and follow its conventions: comment rules,
source lists, template instantiation, export macros, test helpers. Prefer
extending existing test scaffolding over adding new scaffolding.

Keep a list of every file you create or modify. You need it to revert.

## 1. Re-check each bug

Report line numbers are stale: earlier fixes moved the code. Find the code by
its content. Read the code, and confirm the bug is still there. If a bug is
already fixed, drop it from the block. If all are, return `already-fixed`.

The report's reasoning may be wrong. Judge for yourself. Do not trust the
suggested fix blindly.

## 2. Regression test (red first)

For the bugs of the block, write a regression test that shows the defect:

- Put it where the project's tests of that area live. Follow their style.
- Add new files to the build lists, inside the right feature gates.
- The test MUST fail on the current code, and for the right reason: the
  assertion that expresses the bug, not a build error or an unrelated
  exception. Build it and run it. Show yourself the failure.
- A hang or an endless loop MUST be bounded by a timeout, so the test fails
  instead of blocking the suite. Memory blowups MUST be capped the same way.
- Linked bugs: one test per bug, or one test per distinct trigger. Do not merge
  unrelated triggers into a single test.
- Do not touch real devices, the network or the user's data. Follow the
  project's test rules (for example, synthetic images in memory).

If, after real attempts, you cannot make the test fail, or the bug does not
exist as described: revert your changes and return `not-reproducible` with the
reason. Do not fix anything without a failing test.

## 3. Fuzzer case

If the project has a fuzzer (see the facts in your prompt, or look for a fuzz
directory or a fuzz target in the build):

- Build an input that triggers the bug through the fuzzer's entry point. Use a
  throwaway script for the byte layout. Do not commit the script.
- If the fuzzer cannot reach the vulnerable code, make the smallest change to
  the fuzzer that reaches it. Keep the change compatible with the existing
  corpus.
- Save the input in the project's regression corpus, and register it in the
  test that replays the corpus (including any expected-message table), as the
  project's conventions say.
- Build the fuzzer and check the input triggers the bug before the fix
  (crash, hang, sanitizer report or expected message).
- If the bug is not reachable from the fuzzer, even with a small change, say so
  and give the reason in your result.

## 4. Fix

- Fix the root cause with the smallest change that does it. No refactoring, no
  unrelated cleanup, no style churn.
- Do not change the public API unless there is no alternative. Say so if you do.
- Follow the project's conventions (see `CLAUDE.md`).
- Give up after 3 failed fix attempts: revert everything you touched and
  return `abandoned` with what you learned.

## 5. Format

Format only the files you created or modified, in place, with the tools and the
pinned versions the project uses: `clang-format -i <files>` for C/C++ sources,
`gersemi -i <files>` for `CMakeLists.txt` and `*.cmake`. Use the project's own
launcher for them if `CLAUDE.md` names one (for example `uv run`). Do not run a
script that formats the whole repository.

## 6. Verify (green)

- The new tests, and the fuzz case, MUST now pass.
- Run the project's whole test suite. Nothing that passed before may fail.
  If your fix broke an existing test, decide whether the test encoded the bug
  (then update it and say so) or your fix is wrong (then correct the fix).
- Build every configuration your change can affect: at least the main one. If
  you touched code under a feature gate or a platform guard, build the
  matching reduced or other-platform configuration when the tooling for it is
  available (for example a Linux build under WSL). Say which ones you could not
  build.

## 7. Stage and commit

- `git add` explicit paths: exactly the files of your list. Never `-A`, `.` or
  `-u`. Never stage the bug report or any state file.
- Invoke the skill `bansai:git-commit-already-added` with the Skill tool. It
  writes the commit from the index. The message MUST be in English and MUST
  describe the bug fixed, not the test scaffolding.
- If a hook or a check rejects the commit, fix the cause once (for example a
  formatting fix, then re-stage your files) and commit again. If it still
  fails, leave the changes staged and return `commit-failed`.
- Never push. Never amend a previous commit.

## Reverting

Restore the tree to how you found it: `git restore --staged --worktree` on the
files you modified, and delete the files you created. Touch nothing else.
Check `git status --porcelain` is empty before you return.

## Result

Return a short report, in this shape:

- `status`: `fixed`, `already-fixed`, `not-reproducible`, `abandoned` or
  `commit-failed`. One line per bug of the block if they differ.
- `commit`: short hash (for `fixed`).
- `files`: the files changed or added.
- `tests`: the regression tests added, and confirmation each failed before and
  passes after.
- `fuzz`: the case added, or why there is none.
- `notes`: anything the user must know: public API change, existing test
  updated, configuration not built, doubt about the report's reasoning. For a
  non-`fixed` status, the reason.
