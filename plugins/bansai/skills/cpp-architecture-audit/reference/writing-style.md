# Writing style — all deliverables (R1, R2, R3)

Who reads: a good software developer, about 10 years of experience, who does not know this project. In a few weeks they will be an expert; today they need a map, not the details. The documents must be pleasant to read.

## Language

- English, at the level of a 16-year-old reader: short sentences (about 20 words at most, one idea each), active voice, common words ("use", not "utilize"), no idioms, no irony.
- Technical level of a senior engineer: standard terms (mutex, CRTP, translation unit…) stay as they are, and are not explained. What is specific to the project (its domain words, its own names) is explained at first use in a few words, or linked to the glossary if there is one.
- Exception: when the pages complete an existing documentation tree written in another language, keep that language (SKILL.md rule 7) with the same plain style.

## Tone

- Friendly, direct, calm. Not formal, not stiff: "The core never talks to the screen directly", not "It may be observed that the core does not interact with the presentation layer".
- A short and accurate analogy is welcome when it makes a concept easier to grasp. No jokes, no marketing words, no judgment words (SKILL.md rule 1).

## Shape

- Open each section with 1 or 2 sentences: what the reader finds here, or the main finding. Details come after.
- Prefer a small diagram or a short table to a long list. A list has at most 7 items; a paragraph at most 5 sentences.
- Say each fact once, in the section that owns it; elsewhere, link to it.

## Architecture, not implementation

- Name a file, class or function only when the reader needs it to find their way: at most 3 per statement. Never list all the headers, `.cpp` files or methods of a module, and never mention private members.
- For details, point to the places that already hold them: Doxygen, README, CLAUDE.md, `vcpkg.json`, comments in the code.
- Explain what the structure is for (what problem it solves for the project), not how each line works.

## Tests

- Tests may be read to understand the architecture and how the API is used. They are not mentioned in any deliverable, except in R1 §10 (Tests, macro view). The only other exception: the commands that build and run the checks, in the developer guides.
