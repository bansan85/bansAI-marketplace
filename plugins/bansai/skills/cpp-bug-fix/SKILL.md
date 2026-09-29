---
name: cpp-bug-fix
description: >-
  Automatically fixes the bugs listed in a report written by the cpp-bug-hunt
  skill (docs/bug-reports/*.md). Groups related findings, then processes one
  block at a time, most severe first, in a single Sonnet subagent per block:
  regression test that fails first, fuzzer case if a fuzzer exists, fix, full
  test run, formatting, git add and commit. Trigger for: "fix the bugs from the
  report", "cpp-bug-fix", "fix the bug report", "corrige les bugs du rapport".
  Requires the explicit path of the report in the request, and refuses to run
  without it. Modifies code and creates commits. Never pushes.
---

# cpp-bug-fix — fix a cpp-bug-hunt report, one block at a time

Input: the explicit path of a report produced by `cpp-bug-hunt` (see that skill's
`reference/report-format.md` for its layout). Output: one commit per block of
related bugs, each with a regression test.

## Rules

- **One subagent at a time.** Never launch two in parallel. Launch it in the
  foreground (`run_in_background: false`): the next step needs its result.
- **Subagent settings**: `subagent_type: general-purpose`, `model: sonnet`.
  Do not try to set an effort level.
- **The subagent commits by itself**, by invoking
  `/bansai:git-commit-already-added`, so its own context feeds the commit
  message. You never commit.
- **Language.** Talk to the user in the user's language. Everything that ends
  up in git MUST be in English: code, comments, test names, commit messages.
- Never push, never amend, never rewrite history.

## 1. Locate the report and check the repository

- Report: the path MUST be given explicitly in the user's request. If it is
  absent, stop at once: tell the user the skill cannot run without the path of
  the report, and give a usage example. Do not search `docs/bug-reports/`, do
  not guess, do not ask the user to pick one. If the path does not point to an
  existing file, stop the same way.
- Run `git status --porcelain`. If the tree is not clean, stop and tell the
  user: the subagent stages explicit paths, but a dirty tree makes "revert my
  own changes" unsafe.
- If the current branch is the repository's default branch, ask before going
  on.
- Read `CLAUDE.md` if present. Extract the build, test and format commands and
  the presence of a fuzzer. Pass only what the subagent will need.

## 2. Read the report

The report's labels may be in any language. Read it fully once. For each
finding keep: a stable id (its title), impact category, bug category,
locations, and a short summary (the reasoning, trigger scenario, suggested
fix). Also keep the report's header block (scope, date, commit, tooling,
context paragraph): it is the context passed to subagents.

Report line numbers are a snapshot of the commit named in the header. They go
stale after each fix.

## 3. Load the state file

State lives outside the worktree so it never dirties the tree and can never be
staged: `$(git rev-parse --git-path cpp-bug-fix)/<report-basename>.json`
(create the directory if needed). It maps each finding id to a status:
`fixed` (with commit hash), `already-fixed`, `not-reproducible` (with reason),
`abandoned` (with reason), or `commit-failed`.

On start, skip `fixed`, `already-fixed` and `not-reproducible` findings.
`abandoned` and `commit-failed` ones are offered again.

## 4. Group related findings

Put findings in the same block when fixing them separately would be wasteful
or unsafe:

- same root cause or same defective function or code path;
- same lines or same data structure, so the fixes would conflict or overlap;
- one fix changes the behavior the other one's test depends on;
- the trigger scenario of one is a variant of the other's.

Do not group findings merely because they share a file or an impact category.
Prefer small blocks: group only for a real dependency. A block of more than 4
findings is suspect.

Order blocks by their most severe finding (impact order of the report), then by
order of appearance.

## 5. Show the plan, ask what to process

Show the blocks in processing order, numbered. For each: the number, the
severity, and its findings (title, and the reason for the grouping if there is
more than one). Mark the ones the state file already resolved as skipped.

Then ask, in plain text (a list can exceed the option limit of a question
tool): process all blocks, or only some (by number)? Wait for the answer. In a
non-interactive session, process all.

## 6. Process each selected block, sequentially

For each block:

1. Do not read `reference/fixer-instructions.md` yourself. The subagent reads
   it.
2. Launch **one** subagent. Its prompt contains only: the repository root, the
   absolute path of `reference/fixer-instructions.md` in this skill's folder
   (with the instruction to read it first), the report header/context, the
   build/test/format/fuzzer facts from `CLAUDE.md`, and for each finding of the
   block: id, impact, category, locations, summary. Not the rest of the report.
3. When it returns, verify: `git status --porcelain` is empty and HEAD moved
   (if the status is `fixed`), or the tree is clean (any other status). If not,
   stop and tell the user. Do not clean up on your own.
4. Update the state file. Print one line: block number, status, commit hash.
5. Go to the next block. A `not-reproducible`, `abandoned` or `commit-failed`
   block never stops the run, unless step 3 found a dirty tree.

Later blocks run on top of earlier commits, so the code they inspect already
contains the earlier fixes.

## 7. Final summary

One table, one row per finding: block, title, status, commit hash. Then, for
each non-`fixed` row, the reason in one sentence, and what the user can do
(for example fix it manually, or relaunch the skill to retry an `abandoned`
block). Mention the fuzzer cases added and the findings that could not get one.
