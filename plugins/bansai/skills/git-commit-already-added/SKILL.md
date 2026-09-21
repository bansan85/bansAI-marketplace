---
name: git-commit-already-added
description: Draft a commit message from content that is already staged (git add) and create or amend the commit. Matches the repository's existing commit style (language, conventional-commit prefix usage, casing, punctuation, title length) inferred from git log. Use when the user asks to commit what is already staged/added, to write or generate a commit message for the current index, or to amend, squash or fixup the staged content into the previous commit, without asking for anything further to be staged. Do not use when files still have to be selected and staged.
---

# Git commit from already-staged changes

Write a commit message using **only what is already in the git index**
(`git add` has already been run). Never stage additional files, never
unstage anything, and never look at unstaged working-tree changes as
input for the message.

Exception: if the user asks to **amend** the previous commit, the
content to summarize is what the amended commit will contain once the
index is folded into it — see step 2.

## 1. Check the repository state

Run `git status`. If it reports an operation in progress — unmerged
paths, "You are currently rebasing", "You are currently cherry-picking",
"You are currently reverting", "you are still merging" — stop and tell
the user which operation is in progress. Do not draft a message and do
not commit: git has already prepared its own message for those cases,
and amending a commit that is being replayed would rewrite it.

Then run `git diff --cached --stat`. If it is empty and the user is not
amending, tell the user nothing is staged and stop — do not run
`git add` on their behalf. If it is empty and the user *is* amending,
continue: this is a pure reword of the previous commit's message.

## 2. Read the staged change as one block

For a normal commit, run `git diff --cached` and read it as a single
unit of work.

When amending, do not read two diffs: an amend produces one tree, not
two stacked patches, so read the exact content the amended commit will
hold.

- First check that the previous commit is not a merge commit:
  `git rev-parse --verify -q HEAD^2`. If it succeeds, HEAD is a merge
  commit — refuse to amend it, tell the user, and stop.
- Then find the parent to diff against: `git rev-parse --verify -q HEAD^`.
  - If it succeeds, run `git diff --cached -M HEAD^`.
  - If it fails, HEAD is the root commit (`HEAD^` and `HEAD~1` would
    abort with `fatal: ambiguous argument`). Diff against the empty
    tree instead:
    `git diff --cached -M 4b825dc642cb6eb9a060e54bf8d69288fbee4904`.
- Read the previous message with `git log -1 --format=%B`, so you can
  keep what still applies and deliberately replace what does not.

Only split the change into several independent concepts if they are
genuinely unrelated (see the definition of a concept in
`references/message-style.md`). If there are several independent
concepts, describe each one in its own paragraph, and try to name all
of them in the title if it still fits in 50 characters; otherwise pick
the umbrella framing that covers all of them.

## 3. Infer the repository's commit style

Check whether history exists at all: `git rev-parse --verify -q HEAD`.
If it exits non-zero this is the initial commit — `git log` would abort
with `fatal: your current branch ... does not have any commits yet`
(exit 128), not return empty output. In that case skip the inference,
use Conventional Commits, and write in the user's language.

Otherwise run `git log -n 10 --no-merges --pretty=format:"%s"` and
deduce. Merge commits are excluded: their message is generated
automatically by git, not written by the user, so it carries no
signal about the user's style.

- **Type prefix**: only use a Conventional Commits type (`fix:`,
  `feat:`, `chore:`, …) in the title if recent history already uses
  that convention consistently. Don't introduce it if the history
  doesn't have it. When the convention is in use, it applies in full:
  carry a `(scope)` if the history uses scopes, and mark a
  backward-incompatible change with `!` after the type/scope plus a
  `BREAKING CHANGE:` footer — see `references/message-style.md`.
- **Language**: write the message in the same language as the commit
  history. If there is no history (first commit) or the signal is
  unclear, use the language the user is speaking in the current
  conversation instead — not the language of this skill file.
- **Casing and punctuation**: match whether titles start with a
  capital or lowercase letter, and whether they end with a period.
- **Title length**: 50 characters is a hard ceiling, not a target.
  Keep the title as short as it can be while still naming the change,
  even if past titles in this repo ran longer. The type prefix, the
  scope and any trailing period all count towards the 50.
- **Trailer block**: this only concerns trailers you would add on your
  own initiative, chiefly this session's required attribution footer —
  insert one only if that same trailer already appears in the history
  checked above (e.g. a prior `Co-Authored-By:` line); if the
  repository has never used it, leave it out. This does not apply to
  `BREAKING CHANGE:`, which is mandatory whenever the change is
  backward-incompatible under Conventional Commits, regardless of
  history, nor to a trailer the user or the diff explicitly supplies
  (e.g. `Closes #123`). See the "Trailer block (footer)" section of
  `references/message-style.md`.

## 4. Draft the message

Read `references/message-style.md` and follow it to produce the title
and body — message text only, no extra commentary. Apply on top of it
the style detected in step 3 (type prefix and scope, language, casing,
punctuation, title length).

## 5. Create the commit

Commit exactly the staged content — do not run `git add` first. Commit
directly: do not ask the user to approve the draft beforehand, the
final message is shown back in step 6.

When amending, first capture the current hash so it can be reported
later: `git rev-parse --short HEAD`.

Never pass the message with `-m`. Write it to a temporary UTF-8 file in
the session scratchpad with the Write tool and pass that file to git:

- new commit: `git commit -F <file>`
- amend: `git commit --amend -F <file>`

This is the only form that behaves identically on Windows and Linux,
preserves multi-line formatting exactly, and cannot mangle accented
characters. Delete the temporary file afterwards.

If you pass the message through the shell instead, the here-document
delimiter **must** be quoted, otherwise the shell expands `$VAR` and
executes backticks found in the message before git ever sees it:

- bash / Git Bash: `git commit -F - <<'MSG'` … then `MSG` at column 0
- PowerShell: a single-quoted here-string piped in — `@'` … then `'@`
  at column 0, followed by `| git commit -F -`

Never use an unquoted `<<EOF`.

Append this session's required commit attribution footer, as part of
the trailer block described in `references/message-style.md`, only if
step 3 found that the repository's history already carries that same
trailer. Otherwise leave it out.

## 6. Report back

Show the user the message exactly as git stored it — a `commit-msg`
hook may have rewritten it — with
`git --no-pager log -1 --format=%B`, followed by the commit hash
(`git rev-parse --short HEAD`). When amending, report both the
pre-amend hash captured in step 5 and the new one.
