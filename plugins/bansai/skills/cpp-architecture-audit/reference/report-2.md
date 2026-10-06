# L2 — prioritized issues and recommendations

Read when Step 5 starts, only if L2 is requested. SKILL.md's rules still apply; here judgment is allowed, provided it rests on the explicit criteria of this file. Also apply `writing-style.md`: plain English, friendly tone, no tests mentioned.

## Step 5 — Architectural direction

From the identified style (L1 §3.2) — or, without a dominant style, from the observed structure (levels, boundaries, flows) —, select from SKILL.md's styles reference up to 5 styles that would be an evolution, fewer if not that many are compatible with the project's nature. Criteria: structural principles shared with the existing design, realistic migration effort, fit with the project's nature. Never an incompatible style (e.g. Event Sourcing or microservices for a stateless library), nor one of the reference's last three styles without its signal. Rank them by decreasing relevance, each with the concrete signal that motivates it (e.g. "1. Hexagonal — `net/` already acts as an adapter for `core/`, limited migration effort").

Ask via `AskUserQuestion`:
- question: "[The current architecture is close to [style]. | The current architecture follows no dominant style.] In order of relevance: 1. [A] — [concrete signal + benefit]; 2. …; 5. … Do you want to steer the recommendations toward one of them, or strengthen the existing design without a paradigm change?";
- options: the first 3 styles and "Strengthen the existing design"; numbers 4 and 5 are chosen through "Other".

Wait for the answer. Chosen style: recommendations consistent with it. Otherwise: strengthening of the existing design, without a paradigm change.

## Step 6 — Writing L2

Write `architecture-prioritized-issues.md` at its location (SKILL.md, "Deliverables") following the skeleton at the end of this file, with the scales and criteria below.

Sources, exclusively: `inventory.md`, `graph.md`, `synthesis.md`, the `batch-*.md` files, L1 and the answer from Step 5 (SKILL.md rule 3 for any reread). L1 is deliberately short on some topics (binary boundary, ownership, polymorphism, variability, structuring decisions, each principle): L2 takes them from the batch facets and from `synthesis.md`. Each issue refers to the L1 section that covers it (same vocabulary), or, when L1 does not cover it, to the facet (F#) and the module of the summary; it does not copy it.

A defect is described only once, in "Issue details" (P#). The conformance, debt, design patterns, best practices and migration plan sections classify it and refer to its P#, without describing it again.

L2 remains an architecture audit: no bugs, no complexity metric, no local defect. The size of a class or module is mentioned only as a symptom of multiple responsibilities.

Length: 1,500 to 5,000 words depending on the project; an issue fits in 5 lines.

## Scales

Used throughout L2:
- **Priority**: 🔴 critical — compromises evolvability, maintainability or structural reliability; 🟠 important — significant impact, not blocking in the short term; 🟡 minor — desirable improvement, low current impact.
- **Effort**: low — one module, a few files; medium — several modules, without changing a public interface; high — public interfaces or build structure changed.
- **Verdict**: compliant; partially compliant (criterion violated locally); non-compliant (systemic violation); not assessable (facts not observable from the interfaces and summaries).

## Criteria — cross-cutting concepts

| Concept | Non-compliant if… |
|---|---|
| SRP | a class or module carries unrelated responsibilities |
| OCP | adding a variant requires modifying a central list or factory |
| LSP | a derived class refuses or restricts an operation of its base; often visible only in `.cpp` files, otherwise "not assessable" |
| ISP | clients depend on an interface of which they use only an identifiable group of methods |
| DIP | a high-level module depends directly on concrete infrastructure classes |
| DRY | the same logic or knowledge is duplicated across modules |
| KISS | a flow crosses layers or indirections without observable variation, boundary or decoupling |
| YAGNI | an abstraction or extension point has a single implementation, no other use found (Grep its name) and no documented need |
| Law of Demeter | a module manipulates, through an intermediary, types of a module it neither includes directly nor depends on in the build (hidden transitive coupling) |
| DDD | domain vocabulary inconsistent across modules, or module boundaries unrelated to subdomains (only if DDD is claimed or partially present) |
| API-first | exposed contracts are defined only by their implementation |
| Security by Design | sensitive data or processing not isolated behind an identifiable boundary, or secrets (keys, passwords, tokens) written in the sources |
| Privacy by Design | personal data scattered without an identifiable control point |
| IoC / DI | the business core instantiates its own infrastructure or goes through global state |

## Criteria — design patterns

A present pattern can be improved if it is bypassed (direct access that short-circuits the facade or interface), if the same problem is solved by different patterns depending on the module, or if it has neither observed variation nor need (KISS, YAGNI). Propose an absent pattern only if it resolves a non-compliance reported elsewhere in L2 and is compatible with the project's nature. Service Locator: propose with reservations (controversial pattern).

## Criteria — C++ best practices with architectural impact

Out of scope, because they belong to a code review: RAII, smart pointers, rule of 0/3/5, move semantics, const-correctness. In L2, list only the points not met:
- no circular dependency between headers or between modules (graph);
- build organized into separate targets, each declaring its dependencies and include paths, rather than a single configuration with global variables;
- library(ies) and executable(s) separated in the build;
- external dependencies managed by a package manager or identified submodules, rather than copied code or hard-coded system paths;
- external dependencies pinned to a version, consistently across manifests, submodules and CI (L1 §2);
- build options, scripts, build instructions and CI consistent with each other: no documented option missing from the build, no CI job on a missing branch or target (L1 §5.4, `batch-root.md`);
- shared library: symbols exported explicitly (export macro, hidden visibility by default); API/ABI versioned when the binaries are distributed (F5);
- ownership of objects that cross a module boundary is stated by the type or documented (F9);
- polymorphism chosen on purpose: no virtual hierarchy with a single implementation, no template machinery without a second use (F8);
- public headers free of third-party dependency types, unless those types are part of the documented contract;
- platform conditional compilation confined to an abstraction layer rather than spread across several modules (graph, F20);
- embedded: data shared between interrupts and the main context or tasks goes through an identified protection, and stated timing constraints rest on an observable mechanism (priorities, timing measurement) (L1 §3.5).

## Technical debt

A debt is a structural defect whose correction cost grows with time or with each new use (compound interest), unlike an isolated defect. L2 is the only place in the audit where it is qualified.

Handle each type individually; without evidence, write "no debt of this type identified":
- **design / architecture**: non-compliance with cross-cutting concepts other than SRP and DRY, cycles, gaps between declared dependencies and usage, unprotected sharing between interrupts and tasks (F15; L1 §3.5, §5.3, §5.4);
- **code**: SRP and DRY non-compliance (unrelated responsibilities, duplication across modules) (F1, F16; L1 §4.2);
- **documentation**: gap between architecture documentation and code; high fan-in modules without documentation (L1 §11);
- **build / tooling**: unmet best practices related to the build and dependencies (L1 §2, §5.4).

For each type present:
- **issues**: the P# concerned;
- **probable origin**, only if it can be deduced (TODO/FIXME cited by the graph, comment justifying a shortcut, growth visible in the history), never assumed;
- **deliberate or accidental**, if distinguishable on the same grounds;
- **interest**: how the cost worsens (e.g. each new copy-pasted flow increases the risk of divergence between the copies).

Every debt item is also an issue P#, hence present in the summary table, and in the migration plan if it calls for a structural change.

## Migration plan

Only if structural changes are recommended (🔴 or 🟠 issues, or target style chosen in Step 5): incremental refactoring steps, each deliverable and testable on its own, never a complete rewrite. If a target style was chosen, illustrate it with a diagram (SKILL.md's diagrams reference) in "Possible directions".

## Skeleton — `architecture-prioritized-issues.md`

```markdown
# Prioritized architecture issues — [project]

Commit: `[sha]` (branch, clean | modified tree) or "unversioned repository" · Date: [YYYY-MM-DD] · Scope: [audited folder, exclusions]

## Scales
[priority, effort and verdict, copied from the "Scales" section]

## Summary table
| # | Priority | Issue | Modules | Effort |
|---|---|---|---|---|
| [P1](#p1) | 🔴 | … | … | … |

## Cross-cutting concepts — conformance
[each concept of SKILL.md's table that applies to the project, compliant ones included, individually: verdict, criterion applied, evidence from the facets (F#) or L1 reference, P# if any]

## Structuring decisions — consequences
[each decision listed in `synthesis.md` (build type, error model, concurrency model, genericity, ownership…): its documented justification or "not documented", observed consequences on evolvability, build, performance or portability, benefits and costs, P# if any]

## Architectural technical debt
### Typology
### Prioritization matrix
| P# | Type | Interest | Priority | Effort |
|---|---|---|---|---|
### Trajectory if left untreated
[per module concerned: areas that will become blocking first, based on change frequency (graph, history) and fan-in; without history, say so]

## Issue details
### <a id="p1"></a>🔴 P1 — [short title]
- **Finding**: [L1 § reference, or F# and module]
- **Where**: [files, modules]
- **Architectural impact**: [evolvability, testability, coupling, regression risk…]
- **Recommendation**: [high-level direction illustrated by real files or classes, no patch]
- **Effort**: [low | medium | high]

[all issues, 🟡 included, by decreasing priority]

## Design patterns — possible improvements
[for each pattern in L1 §8: true to its intent or improvable (criteria), with its P# if any; absent patterns proposed only to resolve a non-compliance]

## C++ best practices — non-compliance
[only the unmet points: point, P#; if everything is met, one line]

## Alternative architectures considered
[Step 5 ranking reproduced identically, with signal and benefit; the user's choice]

## Possible directions
[changes that do not fix an issue: context (L1), benefit, trade-off and cost, open question if any]

## Progressive migration plan
[if structural changes are recommended; per step: deliverable and independently testable objective, P# addressed, prerequisites, files and modules, risk and mitigation]
```
