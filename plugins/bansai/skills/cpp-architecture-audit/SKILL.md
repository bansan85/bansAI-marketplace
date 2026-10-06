---
name: cpp-architecture-audit
description: "C++ software architecture audit and project documentation (library, service, GUI application, embedded), any build system: reconstructs modules, dependencies, responsibilities, patterns and architectural style from interfaces and build files. Factual report; on explicit request, prioritized issues and recommendations, and project documentation (domain glossary, developer guides, API reference setup, usage scenarios with call stacks). Not a code review, bug hunt or lint. Use for an audit, review or assessment of a C++ project's architecture or design, a map of modules and dependencies, a SOLID/DRY/KISS/DDD or design-pattern evaluation, the architectural style (layered, hexagonal, event-driven…), or to generate or complete a C++ project's documentation. E.g. 'architecture audit', 'what are the architecture problems', 'document this repo', « audit d'architecture », « revue de conception », « génère la doc », « complète la doc existante », even without the word 'skill'."
argument-hint: "[path] [factual|full|docs|all]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(py* *arch_facts.py*)
  - Write(**/.architecture-audit/**)
  - Write(**/architecture-analysis*.md)
  - Edit(**/architecture-analysis*.md)
  - Write(**/architecture-prioritized-issues*.md)
  - Write(**/docs/**)
  - Edit(**/docs/**)
  - Write(**/doc/**)
  - Edit(**/doc/**)
  - Write(**/documentation/**)
  - Edit(**/documentation/**)
  - Bash(git log*)
  - Bash(git branch*)
---

# C++ software architecture audit

Describe, then on request assess and document, the overall design of a C++ project: modules, dependencies, responsibilities, communication between components, patterns, architectural style; on request, the documentation that lets each audience use and maintain it.

Deliverables, written in the audited folder unless another location is requested:
- **R1** `architecture-analysis.md` — factual, always produced (format and writing procedure: `${CLAUDE_SKILL_DIR}/reference/report-1.md`);
- **R2** `architecture-prioritized-issues.md` — judgments and recommendations, only on explicit request;
- **R3** project documentation — `docs/` tree: domain glossary, developer guides, API reference setup, usage scenarios with call stacks, index; only on explicit request. With R3, R1 and R2 are written in its layer 01: the architecture folder of the existing documentation tree, otherwise `docs/01-architecture/`;
- `.architecture-audit/` (written `<work>`) — inventory, graph, summaries, synthesis and R1 parts, reusable for a later R2 or R3.

Vocabulary: *orchestrator* = the agent running this skill; *module* = build unit (library, executable, plugin…) or, failing that, a coherent folder; several targets of the same folder and role may form one module; *subsystem* = group of related modules, used to keep diagrams readable; *batch* = modules given to the same extraction subagent; *writer* = subagent that writes a part of R1; *interface files* = headers and C++20 module interfaces (`.h .hh .hpp .hxx .inl .ipp .tpp .ixx .cppm`…); *feature* = a usage the project offers (an overload or variant with a distinct behavior is a separate feature); *scenario* = R3 sheet tracing one atomic developer task down to its call stack.

## Rules

1. **R1 and R3 are factual.** Allowed: describing what exists, including that a class or module carries several distinct responsibilities, or that two elements do the same thing. Forbidden in R1, R3 and intermediate summaries: any label or judgment whose criterion is not defined in this skill ("god class", "catch-all module", "tight coupling", "central", "complex", "good separation", "clean", "debt"…), any improvement idea, any criticism of a choice. Quantify instead of qualifying: "included by 7 of 9 modules", not "widely used". What is deduced without certainty (domain meaning, intent, mission) is marked "to validate", never presented as a fact. The how-to content of R3 (build and generation commands, CI job snippet for the API reference) is not an improvement idea. Judgments, technical debt and recommendations exist only in R2, based on the criteria in `reference/report-2.md`.
2. **Architecture, not implementation.** Read interface and build files first; open a `.cpp` only when an interface is not enough to establish a responsibility, a relationship or a flow. No line-by-line analysis, no complexity metric. Tests and examples may be read to understand the architecture and the use of the API, but are never cited outside R1 §10 (`reference/writing-style.md`). Only exceptions, for R3: checking the facts cited by existing documentation (Step 7), and tracing call stacks for scenarios and the tutorial (Step 8).
3. **Sources are read once.** Facts are extracted once (Step 2), per module and never per topic, then serve R1, R2 and R3. No file is read in depth by two agents, except when an incomplete batch is relaunched (Step 2) and by R3 scenario subagents (Step 8). The orchestrator does not reread sources, except to settle a precise point that no summary establishes, preferably with a targeted Grep; it then says so in R1's limitations, or, once R1 is written, in the "State of this documentation" section of the R3 index. It writes R1's title and §1, R2 and the R3 pages itself; the other R1 sections are written by writer subagents, and R3's scenario sheets and tutorial by scenario subagents (Steps 4 and 8).
4. **Read-only.** Allowed: Read, Glob, Grep, read-only git, `scripts/arch_facts.py` (a census of files and directives, not an analyzer). Forbidden: building, tests, linters, static analyzers (clang-tidy, cppcheck, IWYU…), even if configured in the repository. Only the deliverables above are written. In existing documentation, complete without overwriting: never delete or rewrite human content, correct only verifiably false facts (line reference, signature, version, dead link); what seems obsolete is reported, not removed. Never commit.
5. **Evidence.** Every finding and every recommendation cites real files or symbols (`file:line` when useful). What cannot be observed is stated as "not observable". No pattern, style or methodology is asserted without concrete traces. In R3, every `file:line`, signature, version or constant comes from a summary or from a file the writer opened, never from memory; this applies in particular to register addresses, interrupt priorities and memory ranges.
6. **Third-party code.** Submodules, packages and code copied from a third party are external: only the API they expose to the project is described.
7. **Language.** All deliverables (R1, R2, R3, `<work>` files) are written in plain English: level of a 16-year-old reader, technical level of a senior developer (`reference/writing-style.md`). Exception: pages that complete an existing documentation tree written in another language keep that language. Questions and the final message are in the language of the user's request. Identifiers, paths, excerpts and diagrams stay in the project's language; the language of identifiers is never a criterion.
8. **Writing style.** Every deliverable follows `reference/writing-style.md`: friendly and direct, reader who does not know the project, architecture and not implementation (no lists of headers, `.cpp` files or methods), a fact stated once in the section that owns it. Every writer subagent is told to read it.

## Workflow

0. Scoping: arguments, inventory, reuse, build, nature, partition, questions, root artifacts.
1. Mechanical facts (script).
2. Factual extraction per batch (parallel subagents).
3. Cross-cutting synthesis (`synthesis.md`).
4. Writing R1 (parts in parallel, then assembly).
5–6. If R2 is requested: architectural direction, then R2, following `${CLAUDE_SKILL_DIR}/reference/report-2.md`.
7–9. If R3 is requested: existing documentation and layers 02 to 04, scenarios and tutorial, index, following `${CLAUDE_SKILL_DIR}/reference/project-docs.md`.

The script runs with the Bash tool (`python`, else `python3` or `py -3`). Without Python: targeted Glob and Grep on the same elements, stated in R1's limitations.

## Step 0 — Scoping (no subagent)

1. **Arguments**: "$ARGUMENTS". They may contain a path to audit (default: repository root) and the scope: `factual` (R1), `full` (R1 + R2), `docs` (R1 + R3) or `all` (R1 + R2 + R3), in any language (`factuel`, `complet`, `doc`, `tout`…). Empty or not substituted: follow the user's request.
2. **Inventory**: `python "${CLAUDE_SKILL_DIR}/scripts/arch_facts.py" inventory --root "<audited folder>" --out "<work>/inventory.md"`, then read it: commit and tree state, repository tree, C/C++ files and interface volume per folder, build files of any system, targets extracted from CMake, MSBuild and qmake builds, CMake options, dependency management, candidate third-party code, generated code, contracts (`.proto`, `.ui`, `.qml`…), tests, examples, documentation, CI, conventions and tooling, scripts, embedded markers.
3. **Reuse**: `<work>` is reusable if its `meta.md` and the files it lists are present, it carries the same commit as the inventory, the tree was clean then and still is, the `batch-*.md` files carry the facets of the current brief (F1 to F27) and `meta.md` its version ("Brief: 2"), and the request does not change the scope (folder, exclusions). In that case, skip items 4, 6 and 8 and Steps 1–2; if R1, at its location for the requested scope, carries the same commit too, reuse it and skip Steps 3–4. Otherwise, the extraction is redone and replaces the previous one.
4. **Build**: the "Build targets" section of the inventory gives the targets, their type and their declared dependencies, with their visibility when the build system distinguishes it. These declarations are the reference for module boundaries. Read the root build files; open the others only when the extraction is missing (another build system) or incomplete (names in variables, targets created by functions or macros), and only to delimit modules: their details belong to the batches (F4).
5. **Project nature and language**, justified by findings with their paths:
   - nature: library, service, GUI application, command-line tool, plugin, embedded or firmware, driver or hardware acquisition, real-time, or a combination (target types, `main()`, server or sockets, GUI framework, hardware target);
   - embedded signals: linker script, startup code, `SystemInit`, register or CMSIS headers, RTOS configuration (FreeRTOS, Zephyr, CMSIS-RTOS…), cross toolchain (`arm-none-eabi`…), interrupt handlers (`*_Handler`, `*_IRQHandler`), widespread `volatile` or memory-mapped access, no host OS;
   - language: C, C++ or both (extensions, `LANGUAGES` in CMake, `class` / `namespace` / `template` versus `struct` and free functions), and bindings to other languages.
6. **Partition**:
   - module = build unit, with all its files wherever they are (`include/…` as well as `src/…`); targets of the same folder and role that belong together may form one module. A target that holds most of the project, or more than ~250 KB of interfaces, is split, if it has subfolders, into logical modules per subfolder (`app/net`, `app/ui`…); R1 states that these boundaries are folders, not targets;
   - write `<work>/partition.txt`, one line per module: `name: path, path`. Test folders form the `tests` module, which the graph handles separately; example folders form the `examples` module. Third-party code is left out;
   - tests are assigned to no batch: their coverage stays at macro level (inventory, build, graph); the batch subagents may read the tests that include their modules' headers (graph) to understand usage;
   - batches, from the interface volume in the inventory: up to ~80 KB in total, no subagent; beyond that, group related modules into batches of ~80 to 250 KB, usually no more than ~15; a larger module is a batch on its own.
7. **Questions** — a single `AskUserQuestion` call (at most 4 questions, 2 to 4 options each; as text if the tool is missing):
   - scope, if not already given: "Do you want only the factual analysis of the existing architecture, also the identification of improvement points and recommendations, also the project documentation, or everything?" — options "Factual analysis (report 1)", "Analysis and recommendations (reports 1 and 2)", "Analysis and project documentation (report 1 and docs)", "Everything (reports 1, 2 and docs)";
   - a report to be written whose name already exists: "Replace", "Write alongside with the suffix -YYYY-MM-DD" (R3 pages are never replaced: rule 4);
   - more than 8 batches or more than ~1,000 C/C++ files: present the batches (modules, volume) — options "Approve the partition (recommended)", "Production code only" (no examples, tools or benchmarks);
   - R3 layers, if R3 is requested: read `${CLAUDE_SKILL_DIR}/reference/project-docs.md` and ask its layers question. If R3 is chosen in this call, read it and ask that question in a second call right after.

   R2 and R3 are never produced without an explicit answer.
8. **Root artifacts** (root build, dependency manifests, README, docs, ADRs, CI): read by the orchestrator, which records its findings in `<work>/batch-root.md`, with evidence: root build; project version (`project(VERSION)`, manifest, latest tag); project nature; external dependencies with their pinned version (manifest, override, baseline, submodule commit) or "not pinned"; mission and scope (what the project does and does not do) as documented; design decisions and their justification as documented; documentation; CI; inconsistencies observed between README, build options, scripts and CI (documented option missing from the build, CI job on a missing branch or target); for an embedded project, the memory regions of the linker script and the RTOS configuration; if R3 is requested, the "Guides" facts listed in `reference/project-docs.md`. A dedicated batch if they are large.

## Step 1 — Mechanical facts (no subagent)

`python "${CLAUDE_SKILL_DIR}/scripts/arch_facts.py" graph --root "<audited folder>" --partition "<work>/partition.txt" --exclude <third-party code, one option per folder> --out "<work>/graph.md"`, then read `graph.md`. It gives, without interpretation:
- modules and the volume of their interfaces;
- module → module dependencies from `#include` (`<…>` and `"…"` forms, resolved against the repository's files, except a `<…>` naming a standard or system header) and C++20 `import`, with the number of includes coming from interface files and one `file:line` example per edge;
- levels (0 = depends on no other internal module), fan-in, fan-out and internal includes per module, cycles between modules and between files;
- effective interface of each module: headers included from other modules (full list above ~250 KB of interfaces);
- includes from the `tests` module, kept out of the computations above, and modules that no test includes;
- external dependencies and the modules that include them; unresolved or ambiguous includes, to be cited as limitations of the method;
- conditional compilation per module, excluding include guards and `__cplusplus` switches; TODO, FIXME, HACK, XXX markers;
- 12-month git history: commits per module, most modified files, co-changes between modules.

## Step 2 — Factual extraction (parallel subagents)

Launch all batches in a single message: `Agent` tool, `subagent_type: "general-purpose"`, `model: "sonnet"`, with a prompt reduced to:

> Read `${CLAUDE_SKILL_DIR}/reference/extraction-brief.md` and apply it. Batch: <name>. Modules and paths: <…>. Graph: `<work>/graph.md`. Output: `<work>/batch-<name>.md`.

Never copy the brief into the prompt. Each subagent writes its summary and returns a single line. Wait for all batches, then read the `batch-*.md` files. Missing, truncated or incomplete summary: relaunch a subagent on that batch's missing facets only. Without subagents (small project), the orchestrator applies the brief itself.

Write `<work>/meta.md`: the inventory's "Git" line, date, audited folder, exclusions, batches and their modules, facets extracted (F1 to F27), "Brief: 2".

## Step 3 — Cross-cutting synthesis

From `inventory.md`, `graph.md`, `batch-root.md` and the `batch-*.md` files only (rule 3), write `<work>/synthesis.md`: compact (about 1,500 words), the common source of the R1 writers (and of R2), one heading per item:
- mission and scope: as documented (root), otherwise deduced from the public API (F2) and marked "to validate";
- module map: for each module, targets and type, level, role (F1), subsystem;
- dependencies: build declarations compared with includes (share coming from interfaces, F3), gaps between declared visibility and usage, cycles, levels;
- architectural style: signals from the reference below found in the graph and the batches; for each style identified, the main modules, their targets and the links between them (the content of its diagram); a style without its signals is not named: "no dominant style";
- main flows (1 to 3): chain the batches' flow entries and exits (F24, F12) from trigger to result, step by step in plain words, with the rule or unit that helps to understand the algorithm; a missing link is "not observable";
- runtime view: executables, processes, and how they communicate (build, F11, F12);
- hardware view, embedded only: memory map, peripherals, interrupts, RTOS tasks, timing constraints (root, F27);
- cross-cutting concepts: the 3 to 6 that shape the whole project, with their observable facts; the others are left for R2;
- structuring decisions (build type, error model, concurrency model, genericity, ownership…), with their documented justification or "not documented": not in R1, used by R2;
- recurring patterns and communication mechanisms between modules;
- multiple responsibilities and duplications, consolidated at project level and described without labels (R2);
- GUI: each GUI and its main windows;
- R1 §6 is always written; R1 §3.5 (hardware) and §7 (GUI) shrink to a "not applicable" line when there is no embedded target or no GUI.

## Step 4 — Writing R1

Follow `${CLAUDE_SKILL_DIR}/reference/report-1.md` (skeleton, one owner per fact, required diagrams, parts, prompt of the writers, assembly). Summary: the orchestrator writes the title and §1 as part `0`, launches the writers (parts A to E) in a single message, assembles the parts with `arch_facts.py assemble`, then reads the report once to remove repeated facts, fix links and check the required diagrams. The report goes to `architecture-analysis.md` (to layer 01 of the documentation tree if R3 is requested).

If R2 is requested: read `${CLAUDE_SKILL_DIR}/reference/report-2.md` and apply Steps 5 and 6. If R3 is requested: read `${CLAUDE_SKILL_DIR}/reference/project-docs.md` and apply Steps 7 to 9. Otherwise: final message.

## Final message

In the chat, only: paths of the written files; project nature and identified style (one line each); if R2: number of issues per priority and titles of the 🔴 ones; if R3: documentation tree written (layers, pages created and completed), corrections made to existing pages, number of scenarios and of features marked "not covered", then the full "to validate / seems obsolete" list (the documentation says X, the code says Y), for human decision; extraction reused or redone; `.architecture-audit/` reusable for a later R2 or R3 on the same commit, otherwise to delete or to ignore in git. Never the content of the reports or pages.

## Reference — architectural styles

To name the observed style (R1 §3.2) and choose alternatives (R2). A style is named only if its signals are observed; "no dominant style" is a valid result: never force a name. The last three are named or proposed only when their signal is present.

| Style | Observable signals |
|---|---|
| Monolith; modular monolith | a single deliverable; modular: separate modules that communicate only through their APIs |
| Layered (N-tier) | graph levels matching roles (presentation, business, data access…), dependencies only toward lower levels |
| Hexagonal (Ports & Adapters); onion; Clean Architecture | core without dependency on infrastructure; interfaces defined by the core and implemented by adapters that depend on it |
| Microkernel / plugins | minimal core, plugin interface, dynamic loading or extension registry |
| Pipe-and-filter / processing pipeline | stages with a common interface, chained, each passing its data to the next |
| Event-driven (EDA); Publish/Subscribe; Broker | bus, dispatcher or broker; emitters and receivers that do not know each other |
| Actor model; Reactor / Proactor | actors with a message queue; event loop dispatching I/O to handlers |
| Entity-Component-System / data-oriented design | entities reduced to identifiers, data components, systems processing arrays of components |
| Blackboard | shared structure read and enriched by independent modules |
| Client-server; peer-to-peer | processes with distinct roles linked by a protocol; symmetric peers |
| CQRS; Event Sourcing | separate read and write models; state rebuilt from an event log |
| Super-loop; interrupt-driven | main loop calling the processing steps in turn; processing triggered by interrupt routines |
| Real-time tasks (RTOS); cyclic executive | prioritized tasks communicating through queues or semaphores; scheduling by a table of fixed time slots |
| SOA; microservices | separately deployed services already present in the repository |
| Serverless / FaaS | cloud deployment configuration present |
| Space-based | documented need for extreme scalability |

## Reference — cross-cutting concepts

Keep only the concepts applicable to the project's nature. R1 §4.1 presents only the 3 to 6 main ones that are really used and explain the project as a whole (security and privacy go to §12); R2 assesses all of them from the facts below, detailed by the brief's facets; verdict criteria are in `reference/report-2.md`.

| Concept | Facts (source) |
|---|---|
| SRP | responsibilities of each structuring class or module (F1) |
| OCP, LSP, ISP, YAGNI, KISS, Law of Demeter, DDD, API-first / Contract-first | F15 |
| DIP | direction of dependencies between levels (graph); dependency on abstractions or on concrete classes (F3, F14) |
| DRY | elements doing the same thing (F16) |
| Security by Design | trust boundaries, isolation of sensitive processing (F21) |
| Privacy by Design | only if personal data is identifiable: where it flows, where it is isolated (F21) |
| IoC / dependency injection | how dependencies are obtained, composition root (F14) |

## Reference — design patterns

Goal: understand how the architecture is implemented. Identify patterns from the structure (headers, hierarchies, compositions, factories, registrations, names), without analyzing implementations line by line. Describe only the patterns actually present, where and how, in a written paragraph; Pimpl (R1 §5.1) and dependency injection (R1 §4.1) are left to their sections.

- Creational: Singleton, Factory Method, Abstract Factory, Builder, Prototype, Object Pool
- Structural: Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy, Pimpl
- Behavioral: Observer (including signals/slots), Strategy, Command, State, Template Method, Chain of Responsibility, Mediator, Visitor, Iterator, Memento, Null Object
- C++-specific: CRTP, policy-based design, type erasure, NVI, self-registering factories
- Concurrency: Active Object, Reactor / Proactor, thread pool, producer-consumer
- System: Repository, Unit of Work, dependency injection, Service Locator, Publish/Subscribe, pipeline
- GUI: MVC, MVP, MVVM, Presentation Model, Qt Model/View
- Embedded and real-time: HAL, BSP, ring buffer, double buffering, state machine (transition table or hierarchical), deferred interrupt processing

## Diagrams

Mermaid by default (rendered natively on GitLab and GitHub); PlantUML only on request. R1's required diagrams are listed in `reference/report-1.md`. Elsewhere (R2, R3), and for R1's optional ones, a diagram is used only if it resolves an ambiguity the text handles poorly:
- interconnected modules → component flowchart;
- class hierarchy central to a pattern → classDiagram;
- temporal flow between modules or actors → sequenceDiagram;
- process or algorithm → activity-style flowchart (BPMN-like, with one `subgraph` lane per actor or module) or stateDiagram-v2;
- cycle or coupling to show → graph with highlighting (`classDef`, `linkStyle`);
- layers or concentric circles → flowchart with one `subgraph` per layer.

A diagram is inserted in the section it illustrates, never in an appendix. No diagram if the structure fits in 2–3 sentences, if it would copy a list, or if it requires extrapolating unobserved elements. Keep it readable: about 15 nodes at most, grouping modules into subsystems above that.

Syntax: labels containing `::`, `<`, `>`, `(`, `)` or spaces go in quotes (`A["core::Engine"]`); templates written `Foo~T~` in a classDiagram; node identifiers without special characters; avoid accented characters in labels when the wording allows it (rendering compatibility).
