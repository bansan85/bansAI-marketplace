---
name: optimize-skill
description: >-
  Audits and fully rewrites an existing Claude skill (SKILL.md and all its
  associated files: reference/, scripts/, assets/) to cut its token
  consumption, on two axes: authoring (the cost of reading the skill once
  triggered) and execution (the cost of applying it: subagents, tool calls,
  order of checks, avoidable re-reads, output format). Generic — applies to
  any skill, in any domain (git, code review, documentation, build,
  deployment...), not just git-related skills. Trigger for: "optimize this
  skill", "cut the tokens on this skill", "this skill is too long / too
  verbose", "token audit on [skill name]", "compress this SKILL.md",
  "slim down this skill", "this skill loads too much context", even without
  an explicit mention of the name "optimize-skill". Never sacrifices
  functional correctness or the skill's triggering to save tokens: when in
  doubt between cutting and keeping a phrase, it is kept.
---

# optimize-skill — Cutting the token cost of an existing skill

A skill costs tokens at two distinct moments: **on read** (as soon as it
triggers, its description then its body enter the context) and **on
execution** (the tool calls it drives once loaded). The two need different
levers — don't conflate them.

## Input

The target skill to optimize (path to its folder, or its name if
unambiguous in the project). If the user didn't specify which one and
several skills match, ask.

## Method

1. **Read the target skill in full**: `SKILL.md` and every file it
   references (`reference/`, `scripts/`, text `assets/`). Distinguish what
   is **always loaded** (frontmatter + body of `SKILL.md`, and any file the
   body says to read unconditionally) from what is only **loaded on
   demand** (reference files read conditionally) — only the first group
   weighs on every trigger, optimize it first.

2. **Short diagnosis** (max 3-5 lines per axis), shown before rewriting:
   - *Authoring axis*: duplicates found (same info in multiple places),
     unactionable justification sentences found.
   - *Execution axis*: subagent justified or not (rule below) and why,
     batchable tool calls found, possible cost-based reordering, avoidable
     re-reads.

3. **Fully rewrite** the target skill's file(s) — no partial patch — applying
   the two axes below.

4. **Numeric before/after summary** (line count and/or estimated tokens of
   `SKILL.md`, and of associated files if modified), shown in the chat.

Apply the rewritten files directly (Write/Edit) to the target skill. Don't
dump the full content in the chat — the diagnosis and the numeric summary
are enough. Leave the changes in the working tree; only commit if explicitly
asked.

## Authoring axis (read cost)

- **One fact, one place.** If a rule is repeated (e.g. stated in the
  frontmatter and restated in the body, or duplicated across two sections),
  keep the most useful phrasing and drop the other.
- **Cut unactionable justification.** A sentence like "it's important to do
  X because it's good practice" that doesn't change any concrete decision
  the model makes is noise — remove it, or reduce it to the instruction
  itself.
- **Always keep recognition triggers**, even when they read like "why".
  A phrasing such as "if you observe X, the likely cause is Y, so do Z" or
  "when the file contains pattern A, that's a sign of B" is not a
  justification — it's a decision rule that governs correct triggering or
  the correct branch of the skill. Never cut it out of overzealousness.
- **Condense the form**: short bullet lists, "when X → do Y" structure,
  rather than explanatory prose. Keep the minimum length that preserves
  meaning and functional completeness (edge cases, exact output formats,
  non-negotiable constraints) — a skill that becomes ambiguous and loses
  triggering accuracy costs more than one that's a bit longer but reliable.

## Execution axis (cost of applying it once loaded)

- **Subagent (Task/Agent) — decision rule**: delegate only if the
  exploration/search volume is far larger than the useful final output (e.g.
  broad grep across a repo, reading many files where only a synthesis
  matters), **or** if executing the query itself is likely to generate a lot
  of context (verbose command output, long logs, large intermediate reads)
  to return only a small amount of information — isolating that noise in a
  subagent keeps it out of the main context even when it isn't "exploration"
  in the search sense. Don't delegate if the action is direct, deterministic,
  and produces no intermediate noise to isolate.
  *Applied to this skill itself*: rewriting a skill needs its full content
  in context to produce a faithful rewrite — delegating the reading to a
  subagent saves nothing, since the useful output (the rewritten file) is as
  large as what was read. Only use a subagent for a targeted
  extraction/diagnosis phase on a very large target skill (several big
  reference files) that would produce a condensed diagnosis — never for the
  rewrite itself, which must stay with the agent that read the whole skill.
  - If a subagent is justified elsewhere in the audited skill, check whether
    the default model is actually needed: a lighter model fits a mechanical,
    low-judgment extraction/search task; keep a stronger model for a task
    that needs judgment or fine synthesis. Also spell out the query passed
    to the subagent: exactly what it must return, what to ignore, and the
    minimal output format expected (no detailed report if a short status
    suffices).
- **Batch tool calls** that are redundant or sequential and could be
  combined (several separate bash commands → one with pipe/`&&`, several
  independent reads → parallel calls).
- **Reorder by increasing cost**: put cheap checks before expensive ones to
  allow a fast short-circuit.
- **Spot avoidable re-reads**: re-reading a file already read, information
  already obtained earlier in the audited skill's flow.
- **Trim the required output format** to the strict minimum: only demand a
  detailed report if the skill actually needs one, a short status otherwise.

## Constraint

Never sacrifice the skill's functional correctness to save tokens. When in
doubt between cutting and keeping a phrase — especially a trigger
phrasing — always keep it.
