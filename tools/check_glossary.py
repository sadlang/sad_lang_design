"""check_glossary: Arabic text uses the approved term, not a banned synonym (style guide, rules 12 and 27).

Matching follows the header of data/glossary.toml:
- a banned word or phrase matches whole, optionally after «ال» or the prefixes و ف ب ك ل;
- diacritics and tatweel are ignored, and alef-hamza forms are unified (as in K-1);
- text between «» (the owner's quoted words, within one paragraph) and records
  (مراجعات/) are skipped; a phrase may break across a line;
- only entries with status = "approved" are enforced.

It also checks text hygiene (rule 48): NFC, and no bidi-control or invisible characters.
"""

from __future__ import annotations

import re
import tomllib
import unicodedata

from repo_files import ROOT, finish, is_record, parser, walk

GLOSSARY = ROOT / "data" / "glossary.toml"
SCANNED = (".md", ".mdx", ".toml", ".txt", ".astro", ".mjs", ".ts", ".py")

ARABIC_LETTER = "\u0621-\u064a\u0671-\u06d3"
DIACRITICS = re.compile("[\u064b-\u065f\u0670\u0640]")
HAMZA_ALEF = str.maketrans({"\u0623": "\u0627", "\u0625": "\u0627", "\u0622": "\u0627", "\u0671": "\u0627"})
# A quotation never crosses a blank line, so a stray «» cannot hide whole paragraphs.
QUOTED = re.compile(r"«(?:[^»\n]|\n(?![ \t]*\n))*»")
# Bidi controls (LRM, RLM, ALM, embeddings, isolates) and invisible characters (ZWSP, word joiner, BOM).
HIDDEN = re.compile("[\u200b\u200e\u200f\u061c\u202a-\u202e\u2060\u2066-\u2069\ufeff]")


def normalize(s: str) -> str:
    return DIACRITICS.sub("", s).translate(HAMZA_ALEF)


def term_pattern(term: str) -> re.Pattern:
    term = normalize(term).strip()
    if term.startswith("ال"):
        rest = re.escape(term[2:]).replace(r"\ ", r"\s+")
        body = rf"(?:[وف]?[بك]?ال|[وف]?لل){rest}"
    else:
        # Outside the f-string: Python 3.11 (the CI version) forbids a backslash inside its braces.
        whole = re.escape(term).replace(r"\ ", r"\s+")
        body = rf"(?:[وف]?(?:[بك]?ال|لل|[بكل])?){whole}"
    return re.compile(rf"(?<![{ARABIC_LETTER}]){body}(?![{ARABIC_LETTER}])")


def load_banned() -> list[tuple[str, str, str, re.Pattern]]:
    data = tomllib.loads(GLOSSARY.read_text(encoding="utf-8"))
    out = []
    for tid, entry in data.get("term", {}).items():
        if entry.get("status") != "approved":
            continue
        for b in entry.get("banned", []):
            out.append((tid, entry["ar"], b, term_pattern(b)))
    return out


def blank(m: re.Match) -> str:
    return re.sub(r"[^\n]", " ", m.group())


def main() -> None:
    args = parser("Report banned synonyms and text-hygiene violations.").parse_args()
    banned = load_banned()
    problems = []
    for relpath, p, _ in walk(SCANNED):
        raw = p.read_text(encoding="utf-8", errors="replace")
        for n, line in enumerate(raw.split("\n"), 1):
            if HIDDEN.search(line):
                problems.append(f"{relpath}:{n}: bidi-control or invisible character (rule 48)")
            if unicodedata.normalize("NFC", line) != line:
                problems.append(f"{relpath}:{n}: text is not NFC (rule 48)")
        # The glossary lists the banned words themselves; records are cited, not governing.
        if p == GLOSSARY or is_record(relpath):
            continue
        # Line numbers count "\n" only, as editors do (splitlines also splits on U+2028 and others).
        text = normalize(QUOTED.sub(blank, raw))
        seen = set()
        for tid, ar, b, pat in banned:
            for m in pat.finditer(text):
                n = text.count("\n", 0, m.start()) + 1
                if (n, tid, b) not in seen:
                    seen.add((n, tid, b))
                    problems.append(f"{relpath}:{n}: «{b}» is banned; use «{ar}» (rule 27, term.{tid})")
    finish("check_glossary", problems, args.strict)


if __name__ == "__main__":
    main()
