# Commit message style

Rules for drafting the title and body. The repository style detected in
step 3 of `SKILL.md` (type prefix, scope, language, casing, punctuation)
is applied on top of these rules and wins wherever the two differ.

## What a concept is

A **concept** is the minimal, coherent set of changes that answers one
single change intention — what an atomic commit would contain on its
own. Two different bug fixes landing in the same commit are two
concepts. A config file edit and an unrelated one-line code change are
two concepts. Refactoring a function and adapting all its callers is
one concept.

## Structure

- **Reading level**: understandable by a smart 16-year-old, but keep
  the technical precision of a software engineer with 10 years of
  experience. The reader is a competent engineer who does **not**
  know this codebase's architecture — don't lean on internal jargon
  without making it clear from context.
- **50/72 rule**: title ≤ 50 characters (hard ceiling, prefix, scope
  and trailing period included — aim well below it), blank line, body
  lines wrapped at ≤ 72 characters, blank line between paragraphs.
- **Action-verb subject**: the title opens with a verb naming what the
  commit does, in the form the repository's history uses. In English
  that is the imperative ("Add", "Fix", "Remove", not "Added",
  "Fixes", "Adding"); in French it is normally the infinitive
  ("Ajouter", "Corriger", "Supprimer"). Match the history.
- **RFC 2119**: the title must comply with RFC 2119 — if it uses a
  normative keyword (MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT,
  SHOULD, SHOULD NOT, RECOMMENDED, MAY, OPTIONAL), that keyword
  carries exactly the meaning RFC 2119 gives it, never a casual
  synonym.
- **What it may draw on**: the concept paragraphs may draw on the
  staged diff and nothing else. Only the context paragraph may also
  draw on the current conversation. When reading other files of the
  repository is unavoidable, read them from the index
  (`git show :<path>`) so unstaged edits cannot leak into the message.
  Reference anything outside the repository only if it is truly
  indispensable to understand the diff.
- **Context paragraph (optional)**: if useful, one leading paragraph
  stating the context — the problem, motivation, or reason the change
  was needed. Include it only if it adds information the concept
  paragraph(s) don't already convey; if it would just restate the
  concept, drop it and start directly with the concept paragraph(s).
- **Concept paragraph(s)**: one paragraph per concept stating what the
  commit actually changes — the solution itself, not just the problem
  it addresses. Describe the finality, not the diff: state what goes
  wrong and why it matters, or what changed in effect — to the
  software's behaviour, or to what a caller or user can now expect —
  not how the code does it. The reader can already see the code; the
  body's job is to say what the code cannot say about itself. Stay
  factual and tied to what the diff actually does.
- **Stay on the code**: never mention how a bug was found (code
  review, fuzzing, a specific crash report, ...) or anything else
  about the process behind the commit, and never list alternatives
  that were rejected.
- **Names**: do not name functions, member variables or classes unless
  understanding the commit is impossible without that name. Prefer a
  plain description of the role or behaviour instead. Never name a
  private member variable: describe its role.
- **Paragraph length**: at most 5 lines per paragraph, and always the
  shortest wording that carries the information — 5 is the ceiling,
  not the budget to spend. If a paragraph runs past 5 lines, check
  whether it is really covering several concepts; if it is, split it
  into one paragraph per concept. Length alone is not proof of several
  concepts.
- **Paragraph count**: the optional context paragraph, plus one concept
  paragraph per concept — except bug fixes, whose concept part is the
  bug/fix pair described below.
- **Numbering**: only when there is more than one concept paragraph,
  prefix each concept paragraph with `(X/N)` at the very start of the
  paragraph (e.g. `(1/2) Add …`) so the reader can see how many
  independent concepts the commit bundles. The context paragraph, when
  present, is never numbered, and a single concept paragraph is never
  numbered either.
- **No filler body**: if the title already says everything needed,
  don't add a body paragraph just to have one.
- **Bug fixes**: first paragraph describes the bug, second paragraph
  describes the fix. Skip the second paragraph if it would just
  restate the first one with the faulty condition inverted. When the
  defect has a standard vulnerability-class name, use it (out-of-bounds
  read/write, use-after-free, double free, integer overflow, type
  confusion, divide by zero, race condition, etc.) — but only when it
  accurately describes the flaw. Use it in the title as well as in the
  bug paragraph, e.g. `fix: close use-after-free in NO_CACHE read
  buffer`. The 50-character ceiling still applies.

## Conventional Commits

Only when step 3 established that the repository uses the convention:

- `<type>(<scope>)!: <subject>` — include the `(scope)` when the
  history uses scopes, and pick the scope from the values the history
  already uses rather than inventing one.
- Add `!` after the type/scope when the change is backward-incompatible,
  **and** end the message with a `BREAKING CHANGE: <what breaks and
  what callers must do>` footer. The `!` alone is not enough.
- Reproduce the issue-trailer form the history uses (`Closes #123`,
  `Refs: ABC-123`, `Fixes: …`) when the user or the diff supplies the
  reference. Never invent an issue number and never guess one from the
  branch name.

## Trailer block (footer)

Any trailer — `BREAKING CHANGE:`, `Closes #123`, `Refs:`,
`Signed-off-by:`, `Co-Authored-By:`, `Change-Id:`, `Reviewed-by:`,
`Reviewed-on:`, `Tested-by:`, and the session's attribution footer —
goes in a single block at the very end of the message, after one blank
line, one trailer per entry.

**A trailer wraps only when its value is free prose.** In practice that
means `BREAKING CHANGE:` and nothing else: its text varies in length, so
it obeys the 72-character limit like the rest of the message — wrap it
and indent each continuation line by two spaces, so the footer still
reads as a single entry.

Every other trailer holds one atomic value — an identity, a URL, a
hash, an issue id — with no natural break point, so it stays on one
line however long it gets. Splitting `Reviewed-on:` or `Co-Authored-By:`
across two lines destroys the grep or the parser that reads it.

Lines that git or a hook wrote itself are reproduced byte for byte:
`Change-Id:`, Gerrit's `Reviewed-on:` / `Tested-by:` / `Reviewed-by:`,
and `(cherry picked from commit 765ae13)`. Never re-flow, re-indent,
re-order or drop them — when amending, carry the previous message's
trailer block over unchanged.

The trailer block is not a paragraph: it is never numbered, never
counted in `N`, and not subject to the paragraph-length rule.

## Examples

### Good — context paragraph plus a single concept paragraph

```
Fix stale cache after a config reload

Reloading the configuration rebuilt the resolver but left the
previous entries in the lookup cache, so requests kept being
routed with the old rules until the process restarted.

Invalidate the lookup cache as part of the reload, so a reload
takes effect on the next request instead of the next restart.

Co-Authored-By: Someone <someone@example.com>
```

### Good — two unrelated concepts, numbered

```
feat(auth): refresh tokens and bump CI image

(1/2) Sessions no longer end abruptly after an hour: the client
now refreshes its token in the background before expiry, and
falls back to a normal re-login if the refresh is rejected.

(2/2) The CI image moves to Node 22, which the refresh timer
needs for its use of AbortSignal.timeout.
```

### Good — bug fix, bug paragraph then fix paragraph

```
Fix cache never filled by const getters

The accessors are declared const and were meant to memoize their
result on first call, but the cache member is not mutable, so a
const member function cannot assign to it. Every accessor ended
up recomputing its value on each call.

Declare the cache member mutable, so the const accessors can
fill it on first use. Logical constness is preserved: the value
an accessor returns is unchanged, only the first call is slow.
```

### Good — title only, no body

```
Fix a missing plural in a comment
```

### Good — breaking change under Conventional Commits

```
fix(api)!: correct retreive_config spelling

The public entry point was exported misspelled as
retreive_config. It is now retrieve_config, with the same
signature and the same behaviour; the old name is gone rather
than kept as an alias.

BREAKING CHANGE: retreive_config() no longer exists. Call
  retrieve_config() instead — the arguments and the return type
  are unchanged, so migrating is a rename.
```

### Bad — restates the diff as code, and pads the body for no reason

```
Update auth.ts

Changed the isValid function to also check expiresAt and added a
new refreshToken function that calls the /refresh endpoint and
sets this.token. Also removed an unused import.
```

### Bad — invents information the diff does not contain

```
fix(cache): invalidate entries on reload

The problem was found during a code review. It is probably the
cause of the latency spikes reported last month, and lookups
should now be about twice as fast.

We first considered dropping the cache entirely, then adding a
TTL, before settling on explicit invalidation.

Closes #482
```

Not one of those statements comes from the diff: where the bug was
found is process narration, the latency cause and the speed-up were
never measured, the rejected alternatives are explicitly banned, and
nobody supplied issue 482.

## Final self-check

Before returning the message, re-check it and fix it if any of these
fails:

1. The title is a single line of at most 50 characters, prefix and
   scope included, and opens with an action verb.
2. A blank line follows the title.
3. Every line is at most 72 characters, except a trailer whose value
   is one atomic token (identity, URL, hash, id), which stays on a
   single line. Among trailers, only `BREAKING CHANGE:` wraps.
4. No paragraph exceeds 5 lines.
5. `(X/N)` appears at the start of every concept paragraph if and only
   if there is more than one.
6. The output contains the message only — no preamble, no code fences,
   no explanation.
7. The body says nothing about how the change was found or made, and
   names no function, member variable or class that a plain
   description of its role could replace.
