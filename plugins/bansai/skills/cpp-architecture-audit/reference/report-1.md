# L1 — factual architecture analysis

Read when Step 3 starts; skipped with Steps 3–4 when L1 is reused (SKILL.md, Step 0). SKILL.md's rules apply, in particular rule 1 (factual), rule 2 (architecture, not implementation), rule 3 (sources read once) and rule 5 (evidence). Also read `${CLAUDE_SKILL_DIR}/reference/writing-style.md` and apply it: plain English, friendly tone, no detail lists. The orchestrator and each L1 writer subagent read this file.

Goal: let a good developer who does not know the project understand how it is built, in one pleasant read. Length: 2,000 to 6,000 words depending on the project, diagrams not counted.

## Step 3 — Cross-cutting synthesis

From `inventory.md`, `graph.md`, `batch-root.md` and the `batch-*.md` files only (rule 3), write `<work>/synthesis.md`: compact (about 1,500 words), the common source of the L1 writers (and of L2), one heading per item:
- mission and scope: as documented (root), otherwise deduced from the public API (F2) and marked "to validate";
- module map: for each module, targets and type, level, role (F1), subsystem;
- dependencies: build declarations compared with includes (share coming from interfaces, F3), gaps between declared visibility and usage, cycles, levels;
- architectural style: signals from the reference below found in the graph and the batches; for each style identified, the main modules, their targets and the links between them (the content of its diagram); a style without its signals is not named: "no dominant style";
- main flows (1 to 3): chain the batches' flow entries and exits (F24, F12) from trigger to result, step by step in plain words, with the rule or unit that helps to understand the algorithm; a missing link is "not observable";
- runtime view: executables, processes, and how they communicate (build, F11, F12);
- hardware view, embedded only: memory map, peripherals, interrupts, RTOS tasks, timing constraints (root, F27);
- cross-cutting concepts: the 3 to 6 that shape the whole project, with their observable facts; the others are left for L2;
- structuring decisions (build type, error model, concurrency model, genericity, ownership…), with their documented justification or "not documented": not in L1, used by L2;
- recurring patterns and communication mechanisms between modules;
- multiple responsibilities and duplications, consolidated at project level and described without labels (L2);
- GUI: each GUI and its main windows;
- L1 §6 is always written; L1 §3.5 (hardware) and §7 (GUI) shrink to a "not applicable" line when there is no embedded target or no GUI.

## Step 4 — Writing L1

Write `architecture-analysis.md` at its location (SKILL.md, "Deliverables") following the skeleton below. The orchestrator writes the title and §1 as part `0`, launches the writers (parts A to E, see "Writing in parts") in a single message, assembles the parts with `arch_facts.py assemble`, then reads the report once to remove repeated facts, fix links and check the required diagrams.

## Cross-cutting concepts — facts for §4.1

Keep only the concepts applicable to the project's nature. L1 §4.1 presents only the 3 to 6 main ones that are really used and explain the project as a whole (security and privacy go to §12); L2 assesses all of them from the facts below, detailed by the brief's facets; verdict criteria are in `report-2.md`.

| Concept | Facts (source) |
|---|---|
| SRP | responsibilities of each structuring class or module (F1) |
| OCP, LSP, ISP, YAGNI, KISS, Law of Demeter, DDD, API-first / Contract-first | F15 |
| DIP | direction of dependencies between levels (graph); dependency on abstractions or on concrete classes (F3, F14) |
| DRY | elements doing the same thing (F16) |
| Security by Design | trust boundaries, isolation of sensitive processing (F21) |
| Privacy by Design | only if personal data is identifiable: where it flows, where it is isolated (F21) |
| IoC / dependency injection | how dependencies are obtained, composition root (F14) |

## Rules for every section

- Open with 1 or 2 plain sentences (what the reader finds, or the main finding), then the structure, then the evidence.
- **One owner per fact** (table below). Another section links to it ("see §4.2") and does not repeat it. After writing, a fact found twice is kept in its owner only.
- Section not applicable: one line saying so.
- Tests are not mentioned outside §10.
- Diagrams: Mermaid, as required by the next table, placed inside the section they illustrate. Keep each diagram readable: about 15 nodes at most; above that, group modules into subsystems (`subgraph`) and show only the main modules, the rest in a one-line note.

| Topic | Owner section |
|---|---|
| Mission, nature, style, key findings (one line each, with a link) | §1 |
| Folder tree, build systems, external dependencies and their role | §2 |
| Modules, targets, levels, role of each | §3.1 |
| Architectural styles | §3.2 |
| Main flows | §3.3 |
| What runs (executables, processes, plugins) and how they talk | §3.4 |
| Fan-in, fan-out, interdependencies | §4.2 |
| What each module offers and hides | §4.3 |
| Circular dependencies | §5.3 |
| Pimpl, public / private headers | §5.1 (not repeated in §8) |
| Dependency injection, DDD, other principles | §4.1 (not repeated in §8 and §9) |
| Build options, packaging, scripts and CI of the build | §5.4 |
| Threads, tasks, asynchrony (GUI modules included) | §6.1 |
| Security and privacy | §12 (not in §4.1) |
| Tests, including their place in CI | §10 |

## Required diagrams

| Where | Diagram |
|---|---|
| §3.1 | Component flowchart of the modules, always: modules grouped by subsystem, arrows = dependencies |
| §3.2 | One diagram per architectural style identified: the main modules, the targets they hold, the links between them. No style identified: no diagram |
| §3.3 | One diagram per flow: sequence diagram, activity-style flowchart (`subgraph` lanes, like BPMN), or state diagram; the choice is yours, the aim is that the reader understands the algorithm at a glance |
| §4.2 | Interdependency graph of the modules, edges with their number of includes, levels from top to bottom |
| §5.3 | One diagram that gathers all the circular dependencies. No cycle: no diagram |
| §4.1 | Optional, when a concept is long to explain in text |
| §7.1 | Optional navigation diagram between windows |

## Skeleton

The `←` marks give the data source; they do not appear in the report. A part is written from its sources only (SKILL.md rule 3). The "§n" references in SKILL.md and in the other `reference/` files follow this numbering: changing it requires updating them.

```markdown
# Architecture analysis — [project]

Commit: `[sha]` (branch, clean | modified tree) or "unversioned repository" · Date: [YYYY-MM-DD] · Scope: [audited folder, exclusions]

## 1. Summary ← synthesis
- Mission and scope: what the project does and does not do (documented, or deduced and marked "to validate")
- Project nature and justification
- Architectural style(s) identified, or "no dominant style"
- 3 to 5 key findings (boundaries, direction of dependencies, communication), one sentence each, with a link to the section that owns it

## 2. Context and scope ← inventory, build, root, graph, F13
### Repository structure
[the "Repository tree" of the inventory as a `tree` drawing in a code block, 30 lines at most, a short `# comment` after the main folders; third-party and generated folders marked]
### Build systems
[one line per build system: name and version, where it starts, what it builds (number of targets, presets)]
### External dependencies
[table: dependency | pinned version or "not pinned" | role: the main features of the library the project uses, in a few words | modules that include it (and the wrapper, if one hides it)]
### What was read, and limits
[two paragraphs. First: what was read (interfaces, build files, the few `.cpp` files, summaries per batch, the script's census). Second: the limits (not observable, unresolved or ambiguous includes, files not read in full, targeted rereads, logical modules from a split target, excluded third-party code)]

## 3. Overview
### 3.1 Module map ← build, graph, batches
[table: module | target(s) and type | level | role in one line. Then the component flowchart]
### 3.2 Architectural style ← graph (levels), batches, signals from SKILL.md's reference
[per style identified: the signals seen and where (a short paragraph), then its diagram]
### 3.3 Main flows ← batches (F24, F12)
[1 to 3 flows, each: its goal in one sentence; what triggers it; the steps in order, one plain line each, saying which module does what; the rule or unit that helps to understand the algorithm, if any; the example that runs it, if any; its diagram. Written for a reader who discovers the project: the algorithm, not its implementation]
### 3.4 Runtime view ← build, batches (F11, F12)
[what runs: executables, loaded libraries and plugins, processes, and how they communicate. Threads inside a module: §6.1]
### 3.5 Hardware view ← root (linker script, RTOS configuration), batches (F27)
[embedded only, otherwise a single "not applicable" line. Tables, each row sourced `file:line`:
- memory map: region | address range | content (`.isr_vector`, `.text`, `.data`, `.bss`, heap, stack) | size — from the linker script;
- peripherals: peripheral | base address | key registers | role | driver | datasheet or reference manual section, if cited in the code;
- interrupts: vector | handler | priority | role | data shared with the main context or tasks | protection observed, or "none observed";
- RTOS tasks: task | priority | period or trigger | stack; synchronization objects and the tasks sharing them;
- timing constraints stated in code or comments]

## 4. Architecture principles
### 4.1 Cross-cutting concepts ← reference, batches
[Not a checklist. Only the 3 to 6 main concepts that are really used and that explain the project as a whole (how it is organized and built), taken from SKILL.md's table. Per concept: 2 to 4 sentences — what it looks like here, where it shows. No local detail. A diagram if the text gets long. Concepts that are absent or marginal are not mentioned]
### 4.2 Coupling and cohesion ← graph (fan-in, fan-out, internal includes, levels), batches
[short text, then the interdependency graph. Name the modules with the highest fan-in and fan-out, with their numbers. Cycles: §5.3]
### 4.3 Boundaries and internal APIs ← graph (effective interface), batches
[per module, or per group of similar modules: what it offers, what it hides, how the others reach it, in one or two sentences. No list of headers]
### 4.4 Error handling ← batches
[the project-wide model in one paragraph; a module is mentioned only where it differs]
### 4.5 Configuration and technical cross-cutting concerns ← batches
[logging, configuration, allocation, instrumentation: one short paragraph each, only those that exist]

## 5. C++ specifics
### 5.1 Interface / implementation separation ← batches
[public and private headers, Pimpl]
### 5.2 Namespaces ← batches
### 5.3 Circular dependencies ← graph
[one diagram that gathers all cycles (modules; files inside a module when there are few), then one sentence per cycle. No cycle: one line]
### 5.4 Build structure, packaging and installation ← inventory (targets, options), build, root, batches
[how targets are organized, install rules, exported package, distributed artifacts; build options, scripts and CI of the build, and the inconsistencies seen between them]

## 6. Application core (backend) ← batches
### 6.1 Concurrency and asynchrony
[a table: module | what it does with threads, tasks or asynchrony (one line; "none" counts). GUI modules included. No private variables]
### 6.2 Persistence and data formats

## 7. Presentation (GUI) ← batches
[without GUI: a single "not applicable" line]
### 7.1 Windows and navigation (F23)
[Each GUI (application or GUI module): its main windows and dialogs, and how the user moves between them. No screenshot: the audit never runs the application]
### 7.2 Presentation pattern
[MVC, MVP, MVVM, Model/View, ad hoc]
### 7.3 GUI / backend boundary and communication

## 8. Design patterns ← batches
[one paragraph: the patterns present, where and how, and what they show about how the architecture is implemented. Without Pimpl (§5.1) and dependency injection (§4.1)]

## 9. Design methodologies ← inventory, documentation, batches
[TDD, BDD, ATDD, DDD: for each, the traces found and why they show it, or "no trace". TDD cannot be known from code alone: say it only if the documentation claims it. DDD: link to §4.1 if it is covered there]

## 10. Tests (macro view) ← inventory, build, graph
[presence, location, framework, place in the build and in CI, modules included or not by the tests — without reading them]

## 11. Architecture documentation ← inventory, batches
[presence; content and match with the code, without judging whether it is up to date; share of public headers with API documentation comments (F22)]

## 12. Security and privacy (architecture only) ← batches
[trust boundaries, isolation of sensitive processing, personal data if any (F21)]
```

## Writing in parts (Step 4)

The orchestrator has a limited output size, so L1 is written in parts, in parallel, then assembled by the script. Each part is a file `<work>/r1-<id>.md` with no title: its first line is the first heading of its sections.

| Part | Sections | Main sources |
|---|---|---|
| `0` (the orchestrator) | title, commit line, §1 | `synthesis.md` |
| `A` | §2, §3.1, §3.2 | inventory, root, graph, batches (F1, F3, F4, F13), synthesis |
| `B` | §3.3, §3.4, §3.5 | batches (F11, F12, F24, F27), root, synthesis |
| `C` | §4, §5 | graph, batches (F3, F6, F7, F10, F12, F14 to F16, F18, F19), root, synthesis |
| `D` | §6, §7 | batches (F11, F23, F25), synthesis |
| `E` | §8 to §12 | inventory, graph, batches (F17, F21, F22), synthesis |

Prompt of a writer subagent (`Agent` tool, `subagent_type: "general-purpose"`, `model: "sonnet"`), all launched in one message:

> Read `${CLAUDE_SKILL_DIR}/reference/report-1.md` and `${CLAUDE_SKILL_DIR}/reference/writing-style.md` and apply them. Part: <id> — sections <list>. Sources: `<work>/synthesis.md`, `<work>/inventory.md`, `<work>/graph.md`, `<work>/batch-*.md`, `<work>/batch-root.md`. Language: English. Output: `<work>/r1-<id>.md`.

Each writer writes only its sections, links to the other sections by number, and replies `OK <file> — <n> words`. Assembly: `python "${CLAUDE_SKILL_DIR}/scripts/arch_facts.py" assemble --out "<report>" "<work>/r1-0.md" "<work>/r1-A.md" … "<work>/r1-E.md"`.

Then the orchestrator reads the report once and, with targeted edits: removes a fact stated twice (the owner keeps it), fixes the `§` links, checks that every required diagram is present and that no section lists headers or methods. Without subagents (small project), the orchestrator writes all the parts itself, with the same rules.
