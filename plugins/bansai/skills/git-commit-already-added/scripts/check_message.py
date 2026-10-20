#!/usr/bin/env python3
"""Check a drafted commit message against the structural limits of the skill.

Usage: check_message.py <message-file> --concepts N [--title-max 50]
                        [--line-max 72] [--max-paragraph-lines 5]

N is the number of concepts the draft was written for (the concept ledger of
step 2). The script counts characters, lines and paragraphs; it does not judge
wording. Exit code 0: every limit holds. Exit code 1: violations, one per line.
"""

import argparse
import re
import sys

# A trailer line: "Key: value", "Closes #123", or a git-written marker.
TRAILER = re.compile(
    r"^(?:[A-Za-z][A-Za-z0-9-]*: \S.*"
    r"|BREAKING[ -]CHANGE: \S.*"
    r"|[A-Za-z][A-Za-z0-9-]* #\d+.*"
    r"|\(cherry picked from commit [0-9a-f]+\))$"
)
NUMBERED = re.compile(r"^\((\d+)/(\d+)\) \S")


def split_paragraphs(lines):
    """Return [(first_line_number, [lines])] for each blank-separated block."""
    paragraphs = []
    current = []
    start = 0
    for number, line in enumerate(lines, start=1):
        if line.strip() == "":
            if current:
                paragraphs.append((start, current))
                current = []
            continue
        if not current:
            start = number
        current.append(line)
    if current:
        paragraphs.append((start, current))
    return paragraphs


def is_trailer_block(block):
    """A block is a trailer block when every line is a trailer or indented
    continuation of one, and the first line is a trailer."""
    if not TRAILER.match(block[0]):
        return False
    return all(TRAILER.match(line) or line.startswith("  ") for line in block)


def check(text, concepts, title_max, line_max, max_lines):
    errors = []
    if not text.endswith("\n"):
        errors.append("the file does not end with a newline")
    lines = text.rstrip("\n").split("\n")

    title = lines[0]
    if len(title) > title_max:
        errors.append(f"line 1: title is {len(title)} characters, max {title_max}")
    if title.strip() == "":
        errors.append("line 1: the title is empty")
    if len(lines) > 1 and lines[1].strip() != "":
        errors.append("line 2: must be blank, between the title and the body")

    for number, line in enumerate(lines, start=1):
        if line != line.rstrip():
            errors.append(f"line {number}: trailing whitespace")
        # A trailer value is atomic and may exceed the limit.
        if number > 1 and len(line) > line_max and not (
            TRAILER.match(line) and not line.startswith("BREAKING")
        ):
            errors.append(f"line {number}: {len(line)} characters, max {line_max}")

    body = split_paragraphs(lines[1:])
    body = [(start + 1, block) for start, block in body]
    trailers = None
    if body and is_trailer_block(body[-1][1]):
        trailers = body.pop()
    if trailers is None and body:
        start, block = body[-1]
        if len(block) > 1 and TRAILER.match(block[-1]):
            errors.append(
                f"line {start + len(block) - 1}: a trailer glued to prose;"
                " trailers go in their own block after a blank line"
            )

    for start, block in body:
        if is_trailer_block(block):
            errors.append(
                f"line {start}: trailers must share one block at the very end"
            )
            continue
        if len(block) > max_lines:
            errors.append(
                f"line {start}: paragraph of {len(block)} lines, max {max_lines}"
                " (shorten it, or it covers several concepts)"
            )

    numbered = [(s, b) for s, b in body if NUMBERED.match(b[0])]
    plain = [(s, b) for s, b in body if not NUMBERED.match(b[0])]

    if concepts <= 1:
        for start, _ in numbered:
            errors.append(
                f"line {start}: numbered paragraph, but only {concepts} concept"
                " declared (numbering is for more than one concept)"
            )
        # Context + concept, or context + bug + fix.
        if len(body) > 3:
            errors.append(
                f"{len(body)} body paragraphs for one concept, max 3"
                " (context, then concept or bug and fix)"
            )
    else:
        if len(numbered) != concepts:
            errors.append(
                f"{concepts} concepts declared, {len(numbered)} numbered paragraphs"
            )
        for index, (start, block) in enumerate(numbered, start=1):
            x, n = (int(g) for g in NUMBERED.match(block[0]).groups())
            if x != index or n != concepts:
                errors.append(
                    f"line {start}: reads ({x}/{n}), expected ({index}/{concepts})"
                )
        if len(plain) > 1:
            errors.append(
                f"{len(plain)} unnumbered paragraphs: only one context paragraph"
                " is allowed, and every concept paragraph must be numbered"
            )
        if plain and numbered and plain[0][0] > numbered[0][0]:
            errors.append("the unnumbered context paragraph must come first")
    return errors, len(body)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("message")
    parser.add_argument("--concepts", type=int, required=True)
    parser.add_argument("--title-max", type=int, default=50)
    parser.add_argument("--line-max", type=int, default=72)
    parser.add_argument("--max-paragraph-lines", type=int, default=5)
    args = parser.parse_args()

    with open(args.message, encoding="utf-8", newline="") as handle:
        text = handle.read().replace("\r\n", "\n")
    errors, paragraphs = check(
        text,
        args.concepts,
        min(args.title_max, 50),
        min(args.line_max, 72),
        min(args.max_paragraph_lines, 5),
    )
    if errors:
        for error in errors:
            print("FAIL:", error)
        sys.exit(1)
    print(f"OK: {paragraphs} body paragraphs, {args.concepts} concept(s)")


if __name__ == "__main__":
    main()
