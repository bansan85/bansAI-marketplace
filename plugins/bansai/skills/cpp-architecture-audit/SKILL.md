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
- **R1** `architecture-analysis.md` — factual, always produced;
- **R2** `architecture-prioritized-issues.md` — judgments and recommendations, only on explicit request;
- **R3** project documentation — `docs/` tree: domain glossary, developer guides, API reference setup, usage scenarios with call stacks, index; only on explicit request. With R3, R1 and R2 are written in its layer 01: the architecture folder of the existing documentation tree, otherwise `docs/01-architecture/`;
- `.architecture-audit/` (written `<work>`) — inventory, graph and summaries, reusable for a later R2 or R3.

Vocabulary: *orchestrator* = the agent running this skill; *module* = build unit (library, executable, plugin…) or, failing that, a coherent folder; *batch* = modules given to the same subagent; *interface files* = headers and C++20 module interfaces (`.h .hh .hpp .hxx .inl .ipp .tpp .ixx .cppm`…); *feature* = a usage the project offers (an overload or variant with a distinct behavior is a separate feature); *scenario* = R3 sheet tracing one atomic developer task down to its call stack.

## Rules

1. **R1 and R3 are factual.** Allowed: describing what exists, including that a class or module carries several distinct responsibilities, or that two elements do the same thing. Forbidden in R1, R3 and intermediate summaries: any label or judgment whose criterion is not defined in this skill ("god class", "catch-all module", "tight coupling", "central", "complex", "good separation", "clean", "debt"…), any improvement idea, any criticism of a choice. Quantify instead of qualifying: "included by 7 of 9 modules", not "widely used". What is deduced without certainty (domain meaning, intent, mission) is marked "to validate", never presented as a fact. The how-to content of R3 (build and generation commands, CI job snippet for the API reference) is not an improvement idea. Judgments, technical debt and recommendations exist only in R2, based on the criteria in `reference/report-2.md`.
2. **Architecture, not implementation.** Read interface and build files first; open a `.cpp` only when an interface is not enough to establish a responsibility, a relationship or a flow. No line-by-line analysis, no complexity metric. Only exceptions, for R3: checking the facts cited by existing documentation (Step 7), and tracing call stacks for scenarios and the tutorial (Step 8).
3. **Sources are read once.** Facts are extracted once (Step 2), per module and never per topic, then serve R1, R2 and R3. No file is read in depth by two agents, except when an incomplete batch is relaunched (Step 2) and by R3 scenario subagents (Step 8). The orchestrator does not reread sources, except to settle a precise point that no summary establishes, preferably with a targeted Grep; it then says so in R1's limitations, or, once R1 is written, in the "State of this documentation" section of the R3 index. It writes R1, R2 and the R3 pages itself, except scenario sheets and the tutorial (Step 8).
4. **Read-only.** Allowed: Read, Glob, Grep, read-only git, `scripts/arch_facts.py` (a census of files and directives, not an analyzer). Forbidden: building, tests, linters, static analyzers (clang-tidy, cppcheck, IWYU…), even if configured in the repository. Only the deliverables above are written. In existing documentation, complete without overwriting: never delete or rewrite human content, correct only verifiably false facts (line reference, signature, version, dead link); what seems obsolete is reported, not removed. Never commit.
5. **Evidence.** Every finding and every recommendation cites real files or symbols (`file:line` when useful). What cannot be observed is stated as "not observable". No pattern, style or methodology is asserted without concrete traces. In R3, every `file:line`, signature, version or constant comes from a summary or from a file the writer opened, never from memory; this applies in particular to register addresses, interrupt priorities and memory ranges.
6. **Third-party code.** Submodules, packages and code copied from a third party are external: only the API they expose to the project is described.
7. **Language.** Reports, documentation and questions in the language of the user's request; without one (non-interactive run), the dominant language of the existing documentation, otherwise English; with R3, everything written in the documentation tree, R1 and R2 included, takes the language of the existing documentation if there is one. One language per deliverable; the language of identifiers is never a criterion. Identifiers, paths, excerpts and diagrams in the project's language.

## Workflow

0. Scoping: arguments, inventory, reuse, build, nature, partition, questions, root artifacts.
1. Mechanical facts (script).
2. Factual extraction per batch (parallel subagents).
3. Cross-cutting synthesis.
4. Writing R1.
5–6. If R2 is requested: architectural direction, then R2, following `${CLAUDE_SKILL_DIR}/reference/report-2.md`.
7–9. If R3 is requested: existing documentation and layers 02 to 04, scenarios and tutorial, index, following `${CLAUDE_SKILL_DIR}/reference/project-docs.md`.

The script runs with the Bash tool (`python`, else `python3` or `py -3`). Without Python: targeted Glob and Grep on the same elements, stated in R1's limitations.

## Step 0 — Scoping (no subagent)

1. **Arguments**: "$ARGUMENTS". They may contain a path to audit (default: repository root) and the scope: `factual` (R1), `full` (R1 + R2), `docs` (R1 + R3) or `all` (R1 + R2 + R3), in any language (`factuel`, `complet`, `doc`, `tout`…). Empty or not substituted: follow the user's request.
2. **Inventory**: `python "${CLAUDE_SKILL_DIR}/scripts/arch_facts.py" inventory --root "<audited folder>" --out "<work>/inventory.md"`, then read it: commit and tree state, C/C++ files and interface volume per folder, build files of any system, targets extracted from CMake, MSBuild and qmake builds, CMake options, dependency management, candidate third-party code, generated code, contracts (`.proto`, `.ui`, `.qml`…), tests, examples, documentation, CI, conventions and tooling, scripts, embedded markers.
3. **Reuse**: `<work>` is reusable if its `meta.md` and the files it lists are present, it carries the same commit as the inventory, the tree was clean then and still is, the `batch-*.md` files carry the facets of the current brief (F1 to F27), and the request does not change the scope (folder, exclusions). In that case, skip items 4, 6 and 8 and Steps 1–2; if R1, at its location for the requested scope, carries the same commit too, reuse it and skip Steps 3–4. Otherwise, the extraction is redone and replaces the previous one.
4. **Build**: the "Build targets" section of the inventory gives the targets, their type and their declared dependencies, with their visibility when the build system distinguishes it. These declarations are the reference for module boundaries. Read the root build files; open the others only when the extraction is missing (another build system) or incomplete (names in variables, targets created by functions or macros), and only to delimit modules: their details belong to the batches (F4).
5. **Project nature and language**, justified by findings with their paths:
   - nature: library, service, GUI application, command-line tool, plugin, embedded or firmware, driver or hardware acquisition, real-time, or a combination (target types, `main()`, server or sockets, GUI framework, hardware target);
   - embedded signals: linker script, startup code, `SystemInit`, register or CMSIS headers, RTOS configuration (FreeRTOS, Zephyr, CMSIS-RTOS…), cross toolchain (`arm-none-eabi`…), interrupt handlers (`*_Handler`, `*_IRQHandler`), widespread `volatile` or memory-mapped access, no host OS;
   - language: C, C++ or both (extensions, `LANGUAGES` in CMake, `class` / `namespace` / `template` versus `struct` and free functions), and bindings to other languages.
6. **Partition**:
   - module = build unit, with all its files wherever they are (`include/…` as well as `src/…`). A target that holds most of the project, or more than ~250 KB of interfaces, is split, if it has subfolders, into logical modules per subfolder (`app/net`, `app/ui`…); R1 states that these boundaries are folders, not targets;
   - write `<work>/partition.txt`, one line per module: `name: path, path`. Test folders form the `tests` module, which the graph handles separately; example folders form the `examples` module. Third-party code is left out;
   - tests are assigned to no batch: their coverage stays at macro level (inventory, build, graph);
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

Write `<work>/meta.md`: the inventory's "Git" line, date, audited folder, exclusions, batches and their modules, facets extracted (F1 to F27).

## Step 3 — Cross-cutting synthesis

From `inventory.md`, `graph.md` and the `batch-*.md` files only (rule 3):
- mission and scope: as documented (root), otherwise deduced from the public API (F2) and marked "to validate";
- module map: for each module, target and type, level, role (F1);
- dependencies: build declarations compared with includes (share coming from interfaces, F3), gaps between declared visibility and usage, cycles, levels; external dependencies with their pinned version (root);
- architectural style: signals from the reference below found in the graph and the batches; a style without its signals is not named: "no dominant style";
- main flows (1 to 3): chain the batches' flow entries and exits (F24, F12) from trigger to result, with the invariants stated on the way; a missing link is "not observable";
- runtime view: executables, processes, threads or tasks, and how they communicate (build, F11, F12);
- hardware view, embedded only: memory map, peripherals, interrupts, RTOS tasks, timing constraints (root, F27);
- cross-cutting concepts applicable to the project's nature, with their observable facts; the others are omitted without mention;
- structuring decisions: choices visible across the summaries (build type, error model, concurrency model, genericity, ownership…), with their documented justification or "not documented";
- recurring patterns and communication mechanisms between modules;
- multiple responsibilities and duplications, consolidated at project level and described without labels;
- R1 §6 (application core) is always written; R1 §3.5 (hardware) and §7 (GUI) shrink to a "not applicable" line when there is no embedded target or no GUI.

## Step 4 — Writing R1

Write `architecture-analysis.md` (in layer 01 of the documentation tree if R3 is requested) following the skeleton below:
- per subsection: finding → observed structure → evidence (files, symbols) taken from the summaries;
- section not applicable: one line saying so;
- 1,500 to 5,000 words depending on project size; short lists; a finding is written once, other sections refer to it.

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

Keep only the concepts applicable to the project's nature. For each, R1 reports the facts listed below, detailed by the brief's facets; verdict criteria are in `reference/report-2.md`.

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

Goal: understand how the architecture is implemented. Identify patterns from the structure (headers, hierarchies, compositions, factories, registrations, names), without analyzing implementations line by line. Describe only the patterns actually present, where and how, in a written paragraph.

- Creational: Singleton, Factory Method, Abstract Factory, Builder, Prototype, Object Pool
- Structural: Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy, Pimpl
- Behavioral: Observer (including signals/slots), Strategy, Command, State, Template Method, Chain of Responsibility, Mediator, Visitor, Iterator, Memento, Null Object
- C++-specific: CRTP, policy-based design, type erasure, NVI, self-registering factories
- Concurrency: Active Object, Reactor / Proactor, thread pool, producer-consumer
- System: Repository, Unit of Work, dependency injection, Service Locator, Publish/Subscribe, pipeline
- GUI: MVC, MVP, MVVM, Presentation Model, Qt Model/View
- Embedded and real-time: HAL, BSP, ring buffer, double buffering, state machine (transition table or hierarchical), deferred interrupt processing

## Diagrams

Mermaid by default (rendered natively on GitLab and GitHub); PlantUML only on request. A diagram is inserted in the section it illustrates, never in an appendix, and only if it resolves an ambiguity the text handles poorly:
- more than ~5 interconnected modules → component flowchart;
- class hierarchy central to a pattern → classDiagram;
- temporal flow between modules → sequenceDiagram;
- cycle or coupling to show → graph with highlighting (`classDef`, `linkStyle`);
- layers or concentric circles → flowchart with one `subgraph` per layer.

No diagram if the structure fits in 2–3 sentences, if it would copy a list, or if it requires extrapolating unobserved elements.

Syntax: labels containing `::`, `<`, `>`, `(`, `)` or spaces go in quotes (`A["core::Engine"]`); templates written `Foo~T~` in a classDiagram; node identifiers without special characters; avoid accented characters in labels when the wording allows it (rendering compatibility).

## Skeleton — R1 (`architecture-analysis.md`)

The `←` marks give the data source; they do not appear in the report. Section titles are translated into the report's language. The "§n" references in `reference/` follow this numbering: changing it requires updating them.

```markdown
# Architecture analysis — [project]

Commit: `[sha]` (branch, clean | modified tree) or "unversioned repository" · Date: [YYYY-MM-DD] · Scope: [audited folder, exclusions]

## 1. Summary
- Mission and scope: what the project does and does not do (documented, or deduced and marked "to validate") ← root, F2
- Project nature and justification
- Identified architectural style(s), or absence of a dominant style
- 3 to 5 structuring findings (boundaries, direction of dependencies, communication mechanisms)

## 2. Context and scope ← inventory, build, root
- Repository structure, build system(s), structuring frameworks and libraries
- External dependencies: [table: dependency | pinned version or "not pinned" | role | modules including it] ← root, graph, F13
- What was read (interfaces, build, occasional `.cpp`) and limitations: not observable, unresolved or ambiguous includes, files not read in full, targeted rereads, logical modules from a split target, excluded third-party code

## 3. Overview
### 3.1 Module map ← build, graph, batches
[table: module | target and type | level | one-line role | main public headers; component flowchart beyond ~5 modules]
### 3.2 Architectural style ← graph (levels), batches, signals from the reference
### 3.3 Main flows ← batches (F24, F12)
[1 to 3 flows: trigger, the steps as a user of the project sees them, modules crossed in order, mechanism at each hop, the example that runs it if any; a sub-flow for each subtle step (numeric conversion, bounds, units, rounding, preconditions): its stated invariants and the edge cases as handled in the code, with their source]
### 3.4 Runtime view ← build, batches (F11, F12)
[executables and loaded libraries, processes, threads or tasks, inter-process communication]
### 3.5 Hardware view ← root (linker script, RTOS configuration), batches (F27)
[embedded only, otherwise a single "not applicable" line. Tables, each row sourced `file:line`:
- memory map: region | address range | content (`.isr_vector`, `.text`, `.data`, `.bss`, heap, stack) | size — from the linker script;
- peripherals: peripheral | base address | key registers | role | driver | datasheet or reference manual section, if cited in the code;
- interrupts: vector | handler | priority | role | data shared with the main context or tasks | protection observed, or "none observed";
- RTOS tasks: task | priority | period or trigger | stack; synchronization objects (mutexes, semaphores, queues) and the tasks sharing them;
- timing constraints stated in code or comments: budgets, deadlines, WCET assumptions]

## 4. Architecture principles
### 4.1 Cross-cutting concepts ← reference, batches
### 4.2 Coupling and cohesion ← graph (fan-in, fan-out, internal includes, levels), batches
### 4.3 Boundaries and internal APIs ← graph (effective interface), batches
### 4.4 Error handling ← batches
### 4.5 Configuration and technical cross-cutting concerns (logging, allocation, instrumentation) ← batches
### 4.6 Structuring decisions ← root, batches, sections above
[table: decision | documented justification and its source, or "not documented" | R1 § describing it; consequences and risks belong to R2]

## 5. C++ specifics
### 5.1 Interface / implementation separation (Pimpl, public and private headers) ← batches
### 5.2 Namespaces ← batches
### 5.3 Circular dependencies ← graph
### 5.4 Build structure, packaging and installation (install rules, exported CMake package, components, distributed artifacts); build options, scripts and CI integration, and inconsistencies observed between them ← inventory (targets, options), build, root, batches
### 5.5 Binary boundary: library type, symbol export, API/ABI versioning, interop with other languages ← build, batches
### 5.6 Polymorphism and genericity: static (templates, CRTP, concepts) or dynamic (virtual), type erasure, header-only ← batches
### 5.7 Ownership and lifetime at API boundaries ← batches
### 5.8 Variability and portability: conditional compilation, OS or hardware abstraction ← graph, batches

## 6. Application core (backend) ← batches
[always present: core of a library, logic of a service, or backend serving the GUI]
### 6.1 Exposed API (to clients or to the GUI): per module, main public headers → major functions, overloads and variants with a distinct behavior, semi-public functions (`detail::`, internal headers) used by other modules (F2)
### 6.2 Business / infrastructure relationship (external dependencies called directly or through a wrapper)
### 6.3 Concurrency and asynchrony
### 6.4 Persistence and data formats

## 7. Presentation (GUI) ← batches
[without GUI: a single "not applicable" line]
### 7.1 GUI / backend boundary
### 7.2 Presentation pattern (MVC, MVP, MVVM, Model/View, ad hoc)
### 7.3 GUI threading and processing
### 7.4 GUI ↔ backend communication
### 7.5 Windows, navigation and UI state: main windows, dialogs and views, navigation between them, global UI state (F23)

## 8. Design patterns ← batches
[paragraph: patterns present, where, how, and what they show about how the architecture is implemented]

## 9. Design methodologies ← inventory, documentation, batches
[TDD, BDD, ATDD, DDD (see §4.1): for each, traces found and why they attest it, or "no trace". TDD cannot be determined from code alone: assert it only if the project's documentation claims it]

## 10. Tests (macro view) ← inventory, build, graph
[presence, location, framework, integration into build and CI, modules included or not by the tests — without reading the tests]

## 11. Architecture documentation ← inventory, batches
[presence; content and correspondence with the code, without judging whether it is up to date; share of public headers carrying API documentation comments (F22)]

## 12. Architecture-related security ← batches
[structural aspects only]
```
