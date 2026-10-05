# Extraction brief — one batch of the C++ architecture audit

You extract the architecture facts of a batch of modules. Your summary will be the only source on this batch for a factual report, possibly a recommendations report and project documentation: nobody will reread these files after you. Be complete and precise. Write in English.

## Rules

- **Reading**: read the batch's interface files (headers, C++20 module interfaces) and its build files in full. Open a `.cpp` only when an interface is not enough to establish a responsibility, a relationship or a flow. Do not read tests.
- **Large module** (more than ~250 KB of interfaces, "Interface KB" column of the graph): read in full the headers of its effective interface, which the graph then lists completely; for the others, locate declarations with Grep (`class`, `struct`, `enum`, `using`, `template`) and open only those a facet requires.
- **Scope**: open no file outside the batch. For a dependency outside the batch, note the path or symbol.
- **Graph**: `graph.md` already gives the dependencies between modules (with the share of includes coming from interface files), cycles, effective interface, external dependencies, conditional compilation and TODOs. Do not recount them: explain them (what is used, by whom, for what).
- **Read-only**: Read, Glob, Grep. No build, tests, linter or analyzer.
- **Factual**: describe what exists. You may say that a class carries several distinct responsibilities, or that two elements do the same thing. Forbidden: labels and judgments ("god class", "catch-all", "tight coupling", "central", "complex", "good", "bad", "clean", "debt", "to improve"…), suggestions, criticism. Quantify instead of qualifying.
- **Evidence**: `file:line` for each finding; no code block longer than 5 lines.
- **Size**: at most ~1,200 words per module and ~3,500 per batch; a small module fits in a few lines. F26 and F27 as compact tables. If the batch cap forces cuts, shorten the least included modules first, never the evidence. Facet not applicable: "—". Information not found in the batch: "not observable".
- **Output**: write the summary to the given file, in the format below, then reply only `OK <file> — <n> modules, <n> files read`.

## Format

```markdown
# Batch <name>

Interface files not read in full: <list, or "none">

## Module <name> — <paths>
- **F1 Role and responsibilities**: role of the module; classes or headers carrying several distinct responsibilities, with the list of these responsibilities (→ R1 §1, §3.1, §4.1 SRP)
- **F2 Public API and features**: main exposed classes and functions, and to whom; features: each distinct usage the module offers, an overload or variant with a distinct behavior counting separately, with the examples and tests that include its headers (graph); semi-public functions (`detail::`, internal headers) used by other modules (→ §1, §3.1, §4.3, §6.1, R3 scenarios)
- **F3 Internal dependencies**: for each graph edge leaving the module, what is used, and whether it is in the interface or only in the implementation (→ §4.2, §4.3)
- **F4 Build**: target(s) and type (static, shared or header-only library, executable, plugin); declared dependencies and their visibility if the build system distinguishes it; gaps between declared dependencies and observed usage (→ §3.1, §5.4)
- **F5 Binary boundary**: export macros, symbol visibility, API/ABI versioning (inline namespaces, version numbers), third-party types exposed in public headers; C API (`extern "C"`) and bindings to other languages (pybind11, SWIG, C++/CLI, MEX, JNI…) (→ §5.5)
- **F6 Interface / implementation**: Pimpl, public or private headers (`detail/`, `internal/`, `_p.h`) (→ §5.1)
- **F7 Namespaces** (→ §5.2)
- **F8 Polymorphism and genericity**: inheritance and `virtual`, templates, CRTP, concepts, type erasure, header-only (→ §5.6)
- **F9 Ownership at API boundaries**: how objects cross boundaries (value, reference, `unique_ptr`, `shared_ptr`, raw pointer, handle) and who owns them (→ §5.7)
- **F10 Error handling**: exceptions, return codes, `std::expected` / `optional`, assertions, mix; examples (→ §4.4)
- **F11 Concurrency**: threads, RTOS tasks and their priorities, interrupt routines, pools, queues, futures, coroutines, locks, atomics, documented thread affinity (→ §3.4, §6.3, §7.3)
- **F12 Communication with other modules**: direct calls, callbacks, observer, signals/slots, events, message queues, shared memory or files, singletons and global state; between processes: sockets, IPC, RPC (→ §3.3, §3.4, §4.3, §7.4)
- **F13 External dependencies** (graph section): called directly by business code or through a dedicated wrapper, which one (→ §2, §6.2)
- **F14 Obtaining dependencies**: injection (constructor, parameter, template), factory, service locator, singleton or global, direct instantiation; where the object graph is assembled (composition root: `main`, factory, container) (→ §4.1 IoC)
- **F15 Cross-cutting concepts**: extension mechanisms and central lists to modify to add a variant (OCP); derived classes that refuse or restrict an operation of their base (LSP); interfaces grouping methods meant for different clients (ISP); abstractions and number of observed implementations (YAGNI); layers and indirections crossed by the main flows (KISS); types of another module obtained through an intermediary, stating whether that module is included directly (Demeter); domain vocabulary (F26), entities, value objects, aggregates, repositories (DDD); contracts separate from the implementation, IDL (API-first) (→ §4.1)
- **F16 Duplications**: elements doing the same thing as another one, within the batch or, judging by names and signatures, outside it (→ §4.1 DRY, §4.2)
- **F17 Patterns**: patterns present, where (`file:line`), and their role in implementing the architecture (→ §8)
- **F18 Configuration**: externalized (files, environment variables, parameters) or hard-coded (→ §4.5)
- **F19 Technical cross-cutting concerns**: logging and tracing, specific allocation (allocators, pools), instrumentation (→ §4.5)
- **F20 Variability**: what the conditional compilation reported by the graph controls (platforms, options); OS or hardware abstraction layer (→ §5.8)
- **F21 Security and sensitive data**: trust boundaries, secrets or configuration mixed with business code, personal data (→ §12, §4.1)
- **F22 Documentation**: Doxygen, design comments, module README; number of public headers whose declarations carry API documentation comments, out of the total (→ §11, R3 API reference)
- **F23 GUI** (if the module belongs to it): GUI / backend boundary, presentation pattern, GUI threading; main windows, dialogs and views, navigation between them, global UI state, user actions (menus, toolbars, shortcuts) and the handlers they trigger (→ §7, R3 GUI journeys and user guide)
- **F24 Flows through the module**: entry points (who calls it, through which API or event), processing, exits (toward which modules or resources, through which mechanism); invariants stated in code or comments on the way (bounds, units, rounding, preconditions) (→ §3.3)
- **F25 Persistence and formats**: storage (files, database, non-volatile memory), serialization formats, format versioning (→ §6.4)
- **F26 Domain vocabulary**: domain terms and acronyms (business, protocol, sensor, register jargon; not C++ vocabulary): term | definition given in a comment or document, with `file:line`, or "no definition found" (→ R3 glossary, §4.1 DDD)
- **F27 Hardware** (embedded only): peripherals driven (base address, key registers, role, `file:line` of the register definition, datasheet or reference manual section if cited in the code); interrupt handlers (vector, configured priority, flags read and cleared, data shared with the main context or tasks and its protection: critical section, interrupt masking, `volatile`, atomic, queue, or "none observed"); RTOS tasks (priority, period or trigger, stack size) and synchronization objects; boot sequence (clocks, pins, option bytes or fuses, initialization order in startup code, `SystemInit`, early `main`); timing budgets, deadlines or WCET assumptions stated in code or comments. Addresses, priorities and sizes are read, never assumed (→ §3.5, R3 getting-started and scenarios)
```
