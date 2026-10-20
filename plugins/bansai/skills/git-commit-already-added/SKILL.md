---
name: git-commit-already-added
description: Draft a commit message from content that is already staged (git add) and create or amend the commit. Matches the repository's existing commit style (language, conventional-commit prefix usage, casing, punctuation, title length) inferred from git log. Use when the user asks to commit what is already staged/added, to write or generate a commit message for the current index, or to amend, squash or fixup the staged content into the previous commit, without asking for anything further to be staged. Do not use when files still have to be selected and staged.
---

# Git commit from already-staged changes

Write the message from **the git index only**. Never stage more, never
unstage, never use unstaged changes as input. Two exceptions: an amend
summarizes what the amended commit will hold (step 3), and step 2
reformats staged lines.

## Gates

Each gate needs evidence in a tool result of this run. "I remember it"
and "I wrote this change in this conversation" are not evidence.

1. **Diff read** (step 3): every hunk was read, or is covered by the
   large-diff rule.
2. **Concept ledger** (step 3): the concepts are listed, N is fixed,
   before any text is drafted.
3. **Lint** (step 6): `scripts/check_message.py` prints `OK` on the file
   that is committed. Never count characters or lines by eye.
4. **Report** (step 8): the reply contains the full commit text.

## 1. State

Run `git status && git diff --cached --stat`.

- An operation in progress (unmerged paths, rebase, cherry-pick,
  revert, merge): stop and name it. Git prepared its own message.
- Empty stat, no amend: say nothing is staged and stop. Never `git add`.
- Empty stat, amend: continue; it is a pure reword.

## 2. Format the staged lines

Skip if nothing is staged. Say nothing of it before step 8.

Scope: only the lines the commit changes (`git diff --cached -U0`;
amend: the newly staged lines only). A new file is fully changed.
Never reformat untouched lines or touch deleted files.

Formatter per file: CLAUDE.md (project, then user level) if it names
one; else `clang-format` for C/C++ when `.clang-format` is at the git
root; `gersemi` for CMake when `.gersemirc` is there; else look in
`.editorconfig`, pre-commit and tool configs, CI scripts. None found or
tool missing: leave the file. Whatever CLAUDE.md did not state is noted
for step 9.

Work on the index content (`git show :<path>`): use the tool's line
ranges (`clang-format --lines=a:b --assume-filename=<path>`), or format
a copy and keep only the hunks that overlap changed lines. Write it back
with `git hash-object -w --stdin` and `git update-index --cacheinfo`.
Write the working tree too only if it was identical to the index.
Record files and tool for step 8.

## 3. Read the change, list the concepts

Normal commit: `git diff --cached`. Amend: refuse a merge commit
(`git rev-parse --verify -q HEAD^2` succeeds); then diff against the
parent, `git diff --cached -M HEAD^`, or against the empty tree
`4b825dc642cb6eb9a060e54bf8d69288fbee4904` when `HEAD^` does not
exist. Read the old message too (`git log -1 --format=%B`): keep what
still applies. An amend yields one tree, not two stacked patches.

The reading is mandatory even when the change is fresh in the context.
The conversation may feed only the context paragraph.

Large diff (truncated output, or over about 1500 lines): read the stat,
then `git diff --cached -- <paths>` per folder until every file is
read. Tests, fixtures, generated, lock and binary files may be read
through the stat and the names they add. All else: hunk by hunk.

**Concept ledger.** A concept is the minimal set of changes answering
one intention, what an atomic commit would hold. Group by intention,
never by file. A refactoring and the adaptation of its callers is one
concept; two unrelated fixes are two. Write one line per concept: the
observable effect, and the files that serve it. Merge entries where one
is only the plumbing, adaptation or test of the other. Keep apart those
that each give a caller or user something observable, even when one
builds on the other. Tests that go with a change are not a concept.

The count N fixes the shape:

- N = 1: no `(X/N)`. Body: optional context paragraph, plus ONE concept
  paragraph (a bug fix: bug paragraph, then fix paragraph).
- N ≥ 2: optional unnumbered context paragraph, then exactly N concept
  paragraphs, each starting `(X/N)`.

If the facts do not fit paragraphs of 5 lines after cutting what the
code already says, the commit is too big: say so in the reply and point
to the `git-add-commits` skill.

## 4. Style

Each item stated in CLAUDE.md (project, then user level) is
authoritative. Infer the rest from the history, and note it for step 9:
`git rev-parse --verify -q HEAD && git log -n 10 --no-merges --format="%B---END---"`.
A non-zero exit means an initial commit: use Conventional Commits and
the user's language. Skip the call when CLAUDE.md states all five.

- **Prefix**: use a Conventional Commits type only if the history uses
  it consistently; then use it fully (scope if the history has scopes,
  see step 5).
- **Language**: that of the history; else the user's, not this file's.
- **Casing, final period**: as in the history.
- **Title length**: at most 50 characters, prefix, scope and period
  included; as short as the meaning allows.
- **Attribution trailer**: add the session's own trailer (for instance
  `Co-Authored-By:`) only if some commit of those 10 already carries the
  same key. Compare the key alone, case-insensitively, ignoring the
  identity; scan whole bodies, squash sub-messages included. Otherwise
  leave it out.

The history decides only these five items. Paragraph length, count and
numbering never follow it: a long paragraph in the log is no model.

## 5. Draft

Read [reference/examples.md](reference/examples.md) first (skip for a
title-only commit). Only these rules decide content and structure;
generic commit habits do not.

- **Reader**: a competent engineer who does not know this codebase.
  Plain words as a smart 16-year-old would follow, with a senior
  engineer's precision. No unexplained internal jargon.
- **Title**: opens with an action verb in the history's form
  (imperative in English, infinitive in French). A normative keyword
  (MUST, SHOULD, MAY…) carries its RFC 2119 meaning.
- **Sources**: concept paragraphs draw on the staged diff alone. Other
  files only through `git show :<path>`. Nothing outside the repository
  unless indispensable.
- **Context paragraph**: only if it adds what neither the title nor the
  concept paragraphs say. 100% factual: each claim is something the
  user said or the diff shows. Never infer a reason, constraint,
  workflow or cause. Cut the unfounded claim, not the paragraph.
- **Concept paragraphs**: say what changed in effect, for the software
  or for what a caller or user can now expect. The code shows how; say
  what it cannot. For a fix: what goes wrong and why it matters.
- **Stay on the code**: never how a bug was found (review, fuzzing,
  crash report) or any process. Never a rejected alternative.
- **Names**: no function, member or class names unless the commit is
  incomprehensible without them. Never a private member: describe its
  role.
- **No filler**: if the title says it all, write no body.
- **Bug fix**: bug paragraph, then fix paragraph, which describes the
  mechanism. Drop it if it only restates the bug with the condition
  inverted, and cut any clause that only negates the bug. Use the
  standard defect name (out-of-bounds read, use-after-free, double free,
  integer overflow, type confusion, divide by zero, race condition…)
  when accurate, in the title too.
- **Conventional Commits** (when step 4 chose it):
  `<type>(<scope>)!: <subject>`, scope from the history's own values.
  A backward-incompatible change takes `!` and a `BREAKING CHANGE:`
  footer saying what breaks and what callers must do. Issue trailers
  follow the history's form, only if the user or diff supplies the
  reference; never invent one or take it from the branch name.
- **Trailers**: one block at the very end after one blank line, one per
  entry. `BREAKING CHANGE:` is always required for a breaking change.
  It alone wraps at 72, continuation lines indented by two spaces. Every
  other trailer stays on one line. Lines written by git or a hook
  (`Change-Id:`, Gerrit's `Reviewed-on:`, `(cherry picked from…)`) are
  kept byte for byte; on an amend carry the old block over unchanged.
  The block is not a paragraph and is never numbered.

## 6. Write and lint

Write the draft with the Write tool to a UTF-8 file in the session
scratchpad. Run:

`python -I "${CLAUDE_SKILL_DIR}/scripts/check_message.py" <file> --concepts N`

Add `--title-max <n>` when step 4 states a limit under 50. The script
checks the title, the 72-character lines, the 5-line paragraphs, the
paragraph count for N, the numbering and the trailer block. On `FAIL`,
fix the file and run it again. Never change N to pass: a different N
means going back to the ledger.

The script does not read words. Then check by hand: Names, Stay on the
code, Bug fix, RFC 2119, the facts of the context paragraph.

## 7. Commit

Commit exactly the index. No `git add` (step 2 already re-staged), no
approval round (step 8 shows the result). On an amend, first note
`git rev-parse --short HEAD`.

`git commit -F <file>` or `git commit --amend -F <file>`. Never `-m`.
If the message goes through the shell, quote the here-document delimiter
(`<<'MSG'`, or PowerShell `@'…'@`); never an unquoted `<<EOF`. Delete
the file once the commit exists.

If git refuses (GPG signature, hook, lock), stop and report its error.
Never pass `--no-gpg-sign`, `-c commit.gpgsign=false` or `--no-verify`
on your own: only when the user asks in so many words. Keep the file and
give its full path.

## 8. Report

Run `git --no-pager log -1 --format="%h%n%B"` (a hook may have rewritten
the message). The reply MUST contain that full text, title, body and
trailers, and the hash; on an amend, also the old hash. Add one line on
the step 2 reformatting (files, tool; and if an unstaged edit kept a
working-tree file unchanged, say so) when it changed anything. Nothing
else: no word on unstaged or untracked files, on what the commit
leaves out, or on an omitted trailer. A refused commit (step 7) is the
one exception.

## 9. Record missing conventions

Only if step 2 or 4 had to search or infer what CLAUDE.md did not state
(formatter per file type, prefix, language, casing and punctuation,
title length, trailer): ask once, listing it, whether to add it to the
project-root CLAUDE.md. On yes, write it there without staging it.
