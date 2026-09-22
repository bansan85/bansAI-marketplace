---
name: git-add-commits
description: Stage pending working-tree changes and commit them, splitting the work into several atomic commits when it covers more than one unrelated concept (e.g. a CI script tweak and two unrelated new functions land together). Use when the user says something like "git add / git commit", asks to commit the current changes, or to commit what this conversation just changed. Scopes the commit to files this conversation modified or created, if any; otherwise to every pending change in the working tree — an explicit scope named by the user always wins over both. Anything already staged before this skill runs is, by design, committed first and untouched as one single commit of its own. Delegates the actual commit-message drafting to git-commit-already-added for every commit it creates — this skill only decides what goes in the index. Do not use when the user has already staged exactly the content they want committed and only needs a message: use git-commit-already-added directly for that.
---

# Git add + commit

Turn pending changes into one or more commits, each atomic with respect to
the feature or fix it contains. This skill decides **what to stage and in
how many commits**; it never drafts commit messages itself — steps 3 and 6
hand every message to **git-commit-already-added**.

Two rules govern every git command below, and every command you add:

- **Never run an interactive git command.** There is no terminal here.
  `git add -p` prints the hunk, reads EOF, stages *nothing*, and still
  exits 0 — a silent no-op you cannot detect from its exit code. Step 6
  gives the non-interactive way to stage part of a file.
- **Always list paths with
  `git -c core.quotePath=false status --porcelain -uall`.** Without
  `core.quotePath=false` a non-ASCII path comes back C-escaped
  (`"accentu\303\251.txt"`), and passing that back to `git add` fails with
  `fatal: pathspec ... did not match any files`. Without `-uall` a new
  directory collapses to a single `dir/` entry, hiding every file inside
  it from the scope check in step 4. Porcelain paths are relative to the
  repository root; plain `git status -s` paths are not.

## 1. Check the repository state

Run these together in one call — none depends on another's output:

```
git rev-parse -q --verify HEAD
ls "$(git rev-parse --git-dir)"
git symbolic-ref -q HEAD
git -c core.quotePath=false status --porcelain -uall
```

- **HEAD**: record it as the starting point for the final report. Failing
  is fine on an unborn branch (no commit yet) — note it and carry on.
- **`ls` on the git dir**: if it contains `MERGE_HEAD`, `CHERRY_PICK_HEAD`,
  `REVERT_HEAD`, `rebase-merge/`, `rebase-apply/`, `sequencer/` or
  `BISECT_LOG`, an operation is in progress — stop and tell the user which
  one, without staging or committing anything. Test these state files, not
  English prose from `git status`: that output is translated, so a
  localized git would defeat a prose-based check silently.
- **`symbolic-ref`**: failing means a detached HEAD, where new commits
  would not belong to any branch — stop.
- **The porcelain listing**: stop if it shows an unmerged path (`UU`,
  `AA`, `DD`, or any code containing `U`). Otherwise hold onto it — step 4
  reuses it verbatim whenever step 3 commits nothing.

## 2. Take the user's explicit instructions first

What the user actually asked for overrides the defaults in step 4 and the
splitting decision in step 5. Read their request before inferring
anything:

- **An explicit scope wins.** "commit everything", "commit all pending
  changes", "commit only `src/parser.c`", or a list of paths replaces the
  session scope of step 4 entirely — do not narrow it back down to the
  files this conversation happened to touch.
- **An explicit commit count wins.** "make it one commit" or "split it in
  two" overrides the partition of step 5. When the user asks for a single
  commit but the changes cover several concepts, commit them together
  anyway and say so in the report; `git-commit-already-added` will give
  each concept its own numbered paragraph.
- **What the user cannot override is step 3.** Pre-staged content is
  committed on its own, always. If they object, they can unstage it and
  re-run.
- If the request is ambiguous between two readings that would produce
  materially different commits, ask before staging — not after.

## 3. Commit whatever is already staged, first and untouched

Run `git diff --cached --stat` before anything else, and before running
any `git add` yourself. If it is non-empty, that content was staged
deliberately (by the user or an earlier step) and is a **closed set**:
invoke the **git-commit-already-added** skill on it right away, exactly as
it stands. Do not add paths to it, do not unstage anything from it, and do
not fold any of it into the groups of step 5.

Two consequences to accept and, when they matter, to mention in the final
report:

- That commit comes first, so the dependency ordering of step 5 cannot
  apply to it. If it depends on changes that are still unstaged, the
  intermediate tree may not build.
- If the index holds only part of a file, that commit holds only part of
  that file.

Tell the user this commit is being created from content they staged
themselves, before you continue.

## 4. Determine the scope of the remaining changes

Unless step 2 established an explicit scope, which replaces this one:

- Look back over this conversation for files you **created, edited,
  deleted, renamed or moved** (`Edit`, `Write`, `NotebookEdit`, or a
  Bash/PowerShell command that wrote to, removed or moved a file).
  Deletions and renames count exactly like edits — `git add -- <path>`
  stages a deletion correctly. Normalize the paths to repo-relative,
  forward-slash form so they compare cleanly against git's output.
- If that list is non-empty, the scope is those files only.
- If it is empty — the conversation made no file changes, e.g. a pure
  discussion or a read-only investigation — the scope is every pending
  change in the working tree.
- If step 3 committed anything, re-run
  `git -c core.quotePath=false status --porcelain -uall` — committing
  changed the tracked state. Otherwise reuse step 1's listing as-is.
  Enumerate unstaged modifications, untracked files, deletions and
  renames from it, and intersect that with the scope above.
- A file you changed that does not appear in that listing is ignored by
  `.gitignore`. Do not try to force it in: name it to the user instead,
  so a silently dropped file never looks like a committed one.
- If the intersection is empty, there is nothing more to commit. Say so —
  and if step 3 created a commit, still go to step 7 and report it. Stop
  only after that. Do not silently widen the scope to "everything" as a
  fallback: an empty session-scope is a valid outcome, not a signal to
  ignore it.

## 5. Partition the in-scope changes into atomic groups

One group per **concept**: the minimal, coherent set of changes that
answers one single change intention — what an atomic commit would contain
on its own. Two different bug fixes are two concepts; a config edit and an
unrelated one-line code change are two concepts; refactoring a function
and adapting all its callers is one concept. (Mirrors the definition in
`../git-commit-already-added/references/message-style.md`; duplicated
here so this skill works standalone.)

- Decide groupings from the actual diff content (`git diff` for tracked
  paths, file contents for untracked ones), not from file names or
  directories alone. Two unrelated new functions added to the same file
  are two concepts; a CI script tweak and an application-code change are
  normally two concepts even if the user made them in the same sitting.
- Only split when the concepts are genuinely independent. When in doubt,
  keep changes together rather than splitting speculatively.
- A file in scope may also carry hunks that have nothing to do with this
  conversation — edits the user made themselves before it started. Judge
  hunks, not files: put those in a group of their own rather than letting
  them ride along in a group they do not belong to.
- Order the groups so a commit never depends on something introduced by a
  later one (e.g. a helper before its caller).
- Before creating the first commit, state the planned breakdown in one
  line per group, so the user can redirect a bad split before it becomes
  history.

## 6. Stage and commit each group, one at a time

For each group, in the order decided above:

1. **Stage exactly that group.** For whole-file changes, `git add --
   <path>` per path — the `--` keeps a path starting with `:` or `-` from
   being read as a pathspec. Never `git add -A` or `git add .`.

   For a file that must be split across two groups, build a patch and
   apply it to the index only. Never `git add -p`, and never `git add
   -N`: an intent-to-add entry survives the commit *without being
   committed*, so the file silently vanishes from the result.

   ```
   # tracked file
   git diff -- <path> > <scratchpad>/group.patch
   # untracked file (exits 1 when there is a difference — that is normal)
   git diff --no-index -- /dev/null <path> > <scratchpad>/group.patch
   ```

   Edit the patch down to the hunks of this group, then:

   ```
   git apply --cached --recount <scratchpad>/group.patch
   ```

   - `--recount` is **required**: a hand-edited hunk no longer matches its
     `@@ -a,b +c,d @@` counts, and git aborts with `corrupt patch`.
   - To leave out an **added** line, delete its `+` line.
   - To leave out a **removed** line, turn its `-` into a leading space so
     it becomes context. Deleting the `-` line instead makes the whole
     patch fail to apply.
   - Leave the `index <old>..<new>` line alone; git recomputes it.
   - Delete the patch file once applied.

2. **Verify and scan in one read**: run `git diff --cached` in full — not
   `--stat`, which shows file names and line counts and therefore cannot
   confirm which *hunks* landed. Check that the staged content is exactly
   the intended group, nothing more and nothing less, and at the same time
   look for anything resembling a secret or a credential, even in a file
   whose name looks innocuous. Warn the user and stop before committing if
   something looks off.

3. **Commit it**: invoke the **git-commit-already-added** skill to draft
   the message and create the commit for what is now staged. Do not draft
   the message yourself — that skill owns wording, style and language.

4. **Re-read the state** with
   `git -c core.quotePath=false status --porcelain -uall` before moving
   on. If the commit failed (a rejecting `pre-commit` hook, a signing
   error), stop, report which groups are already committed, and leave the
   rest alone. If files just committed show up modified again, a hook
   reformatted them: tell the user, and do not let those changes drift
   into the next group.

Repeat until every group from step 5 has its own commit.

## 7. Report back

List every commit this skill created, in order, each with its short hash
and title, using the starting point captured in step 1:

```
git --no-pager log --oneline <start>..HEAD
```

If the branch was unborn at step 1, use `git --no-pager log --oneline`
instead. Do not count commits by hand with `-n <count>`: a hook may have
added or rewritten one. Mark which commit came from the pre-staged block
of step 3, so the user can see the atomic breakdown — and its one imposed
boundary — at a glance.
