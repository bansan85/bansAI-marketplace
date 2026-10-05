# Report 3 — project documentation

Read only if R3 is requested. SKILL.md's rules still apply, in particular rule 1 ("to validate"), rule 4 (complete without overwriting) and rule 7 (language). Goal: documentation true to the code, verifiable, useful to distinct audiences (management, newcomers, developers, integrators, maintainers). A page without real material is not created; a section without content is not written.

## Target tree

```
docs/
├── README.md          index: points each audience to its entry point
├── 01-architecture/   R1 (architecture-analysis.md), R2 if produced
├── 02-domain/         glossary.md
├── 03-guides/         getting-started.md, contributing.md, usage-tutorial.md, user-guide.md (GUI)
├── 04-api/            README.md, Doxyfile
└── 05-scenarios/      README.md, <family>/NN-<name>.md, gui/ (GUI journeys)
```

If a documentation tree already exists (`docs/`, `doc/`, `documentation/`), it is used and its numbering and naming conventions are kept: the layers are mapped onto its pages, and R1 and R2 go into its architecture folder (created as `01-architecture/` if it has none). Everything written in the tree takes the language of the existing documentation (SKILL.md rule 7).

## Layers per project nature

| Project nature | Layers |
|---|---|
| Small utility (1 to 3 modules) | 01, `03-guides/getting-started.md`. No 05 |
| Internal library | 01 · 03 (getting-started, contributing, tutorial) · 04 if a public surface exists · 05 if the internal flow deserves tracing |
| Public library or SDK | All layers; 05 by usage scenarios covering every feature; 02 if a domain exists |
| Service | 01 · 02 if a domain exists · 03 · 04 = endpoint or message reference · 05 = request path, one per endpoint or message type |
| GUI application | 01 (R1 §7) · 03 getting-started and user-guide · `05-scenarios/gui/`, one sheet per screen or user journey · 02 if a domain exists · no 04 unless a library part exposes an API |
| Embedded or firmware | 01 to 05 enriched with hardware: R1 §3.5, boot configuration in getting-started, 05 = hardware operations and interrupt sheets; 02 for protocol, sensor or register jargon |

A mixed project (library and GUI) takes the library layers plus `05-scenarios/gui/`. The project's nature decides whether layer 05 is produced, never how much it covers: once produced, it is exhaustive on the surface concerned.

Other adaptations:
- bindings (Python, C#, MATLAB…): every exposed language in the tutorial and the scenarios;
- no domain jargon (F26 empty): no layer 02;
- no stable public surface: 04 reduced to a pointer, no generation configuration;
- no CI: the CI section of `contributing.md` becomes "local checks";
- no example: the tutorial is built on a test exercising the public API, otherwise no tutorial.

### Layers question (Step 0)

`AskUserQuestion`, `multiSelect: true`. Question: "Documentation for a [nature] in [C | C++ | C and C++][, bindings: …] (evidence: [2 or 3 paths]; existing documentation: [tree or "none"], completed without being overwritten, in [language]). Which layers should be produced besides architecture (01)? To correct the nature or the language, answer through 'Other'." Options: "Domain glossary (02)", "Developer guides (03)", "API reference (04)", "Usage scenarios (05, order of magnitude N sheets)"; each option's description says whether the table above recommends it and why. N is estimated from the inventory (public interface files, examples, `.ui` files, interrupt handler files) and refined in Step 8. A correction from the user replaces the nature or language of Step 0.

## Guides facts (`batch-root.md`, "Guides" section)

Recorded by the orchestrator in Step 0 when R3 is requested; if the section is missing (extraction reused, or R3 chosen later), the orchestrator reads the same files at the start of Step 7 and adds it. Each fact with its source:
- prerequisites: compilers and minimum versions, CMake minimum version, toolchains, package manager, system packages;
- build: scripts (path, what they do), presets, manual commands; options from the inventory with their default and their effect (Grep of the option name in the build files);
- installation and additional packages;
- tests: how they are built and run, coverage tool;
- examples: how they are built and run;
- conventions: key formatting, lint and naming settings as configured (`.clang-format`, `.clang-tidy` checks, `.editorconfig`), pre-commit hooks;
- CI: stages → jobs → role → triggers (branches, tags, merge requests), artifacts, what blocks a merge;
- git workflow: documented branches and merge rules, commit conventions observed in `git log` (read-only);
- inconsistencies observed between README, scripts, build and CI: already recorded by Step 0 (SKILL.md), completed here with the branches named in CI that do not exist (`git branch -a`).

## Step 7 — Existing documentation and layers 02 to 04

### 7.1 Existing documentation

When a documentation tree exists:
1. map it: layers and pages present, their state (complete, draft, empty) and their intent (human notes, "validated by an expert", "to validate" mentions);
2. coverage diff: public surface and features (F2, graph effective interface) compared with what is documented → missing items;
3. add what is missing, in the existing style and language;
4. correct only verifiably false facts (line reference, signature, version, dead link), touching human prose as little as possible;
5. delete nothing human: what seems obsolete goes into the "to validate / seems obsolete" list (the documentation says X, the code says Y), never into a deletion;
6. keep existing cross-links and add the new ones.

Write `<work>/docs-plan.md`: existing pages and their state, layers kept, feature inventory, scenario catalog, "to validate / seems obsolete" list. It is updated until Step 9.

### 7.2 Writing layers 02 to 04

Sources: `inventory.md`, `graph.md`, `batch-*.md`, `batch-root.md`, R1 (rule 3). Page conventions and templates below.

## Step 8 — Scenarios and tutorial

1. **Feature inventory**: what the project lets a developer do, from the features (F2), the effective interface (graph), the examples (inventory) and the headers included by the tests (graph). An overload or variant with a distinct behavior is a distinct feature. GUI: each window, dialog or view (F23). Embedded: each peripheral driven and each interrupt (F27). Service: each endpoint or message type.
2. **Catalog**: one scenario per atomic task (granularity rules in `scenario-brief.md`), grouped into families of usage; global numbering NN so that sheets can refer to each other. Each entry: NN, sheet type (scenario, GUI journey, interrupt; a hardware operation is a scenario), title, entry function with `file:line`, feature variant, example to anchor it, features covered. Every feature is reachable from at least one scenario, directly or as a step of a broader one.
3. **Subagents**: all in a single message, `Agent` tool, `subagent_type: "general-purpose"`, `model: "sonnet"`; up to ~15 scenarios per subagent, a family kept whole when it fits; the tutorial is a separate job. Prompt reduced to:

   > Read `${CLAUDE_SKILL_DIR}/reference/scenario-brief.md` and apply it. Job: scenarios | tutorial. Language: <…>. Scenarios: <NN — sheet type — title — entry `file:line` — feature variant — example — features> | Example: <path>, exposed languages: <…>. Context: `<work>/graph.md`, `<work>/batch-<x>.md`, catalog `<work>/docs-plan.md`, R1: <path>, glossary: <path or "none">. Output: <folder or file>.

   Never copy the brief into the prompt. Each subagent returns a single line. Missing or truncated sheet: relaunch on the missing sheets only.
4. **Coverage diff**: cross the inventory with the sheets written and the "not traceable" lists returned. A feature not covered is added to an existing scenario as a step when possible (relaunch), otherwise it stays in the catalog marked "not covered — to complete", as does a stack that cannot be traced (generated code, binary). Never silence on a feature.
5. **`05-scenarios/README.md`**: the call stack legend (copy of the "Legend" block of `scenario-brief.md`); a link to the module map of R1 §3.1 (and its diagram, if any); the catalog, one table per family: # | Scenario | Function | Key chain, with the features not covered; if examples exist, an examples ↔ scenarios table; embedded: link to the interrupt table of R1 §3.5 and list of the interrupt sheets. GUI: `05-scenarios/gui/README.md` with the screen catalog (each screen reachable has its sheet, or "not covered — to complete") and a link to R1 §7.5 for navigation.

## Step 9 — Index

`docs/README.md`, completed if it exists (rule 4):
- table "You are… → Start with…": management → R1 §1, and the R2 summary table if R2 exists; newcomer → getting-started, glossary, tutorial; developer → scenarios, contributing; integrator → API reference, tutorial, R1 §5.5; maintainer → R2 if it exists, R1 §4, contributing;
- annotated `docs/` tree;
- "State of this documentation": project version, commit, branch, date, pages or sections marked "to validate", targeted rereads made after R1 was written (SKILL.md rule 3).

The "to validate / seems obsolete" list of `docs-plan.md` goes into the final message.

## Page conventions (all R3 pages)

- First line after the title: `> Layer N — <role of the page>.`
- Clickable relative links to the code, from the page's location, with a line anchor when useful: `[engine.h](../../include/core/engine.h#L42)`.
- Domain terms in bold, linked to the glossary on their first occurrence.
- One page = one audience and one level; a "Further reading" section links the neighboring pages (glossary ↔ scenarios ↔ R1 decisions).
- Tables for any parameter/value or decision/consequence list; diagrams per SKILL.md.
- A ⚠️ marks a pitfall observable in the code or configuration, with its source and a link to R1 or R2 when they cover it.

## Templates — layers 02 to 04

- **`02-domain/glossary.md`** — tables term → definition → source, grouped by theme (F26, README, documentation). Banner "⚠️ To validate by a [domain] expert" when definitions are deduced from code. The other pages link here.
- **`03-guides/getting-started.md`** — prerequisites; build (scripts first, then the manual way); table option → default → effect, from the real build files; installation and additional packages; tests; examples (build and run); embedded: hardware boot configuration (clocks, pins, option bytes or fuses, initialization sequence, from startup code, F27). Consolidates the instructions scattered across READMEs. Pitfalls ⚠️ linked to R1 or R2.
- **`03-guides/contributing.md`** — conventions (formatting, lint, naming) read in their configuration files; tests; coverage; CI pipeline: Mermaid of the stages and table stage → jobs → role, read in the real CI files; git workflow; ⚠️ observed inconsistencies (Guides facts). Without CI: "local checks".
- **`03-guides/user-guide.md`** (GUI only) — for end users, distinct from the developer guides: what the application lets them do, main windows and their actions, typical journeys linked to the GUI sheets; from F23 and the `.ui` / `.qml` files. Behavior deduced from code is marked "to validate".
- **`03-guides/usage-tutorial.md`** — written in Step 8 (tutorial job).
- **`04-api/README.md`** — tool: Doxygen (optionally Sphinx + Breathe); pdoc or Sphinx for Python bindings; prerequisites; generation command, run from the repository root; generated HTML not versioned (build artifact); proposed CI job as a snippet in the page (the CI file is not modified). Annotation state (F22, R1 §11): if few public headers are annotated, annotation is stated as a prerequisite rather than presenting the reference as ready. Service: endpoint or message reference instead of, or besides, Doxygen: endpoint or message | request | response | handler `file:line`, from the contracts or the handlers.
- **`04-api/Doxyfile`** — only if none exists (otherwise the existing one is documented). Paths relative to the repository root, from which the README command runs it: `INPUT` = public header folders (effective interface), `RECURSIVE = YES`, `FILE_PATTERNS` = the interface extensions, `EXCLUDE` = third-party and generated code, `OUTPUT_DIRECTORY` = a non-versioned build folder, `USE_MDFILE_AS_MAINPAGE` = root README if present, `GENERATE_LATEX = NO`, `EXTRACT_ALL` according to the annotation state.
