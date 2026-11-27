"""check_sources: site pages point to sources that exist, and the decision index matches DECISIONS.md.

[S1] A page's «مصدر» field (front matter, one line, once: مصدر: ["path#where", ...]) names
     files that exist, case-exact as on the Linux CI; the path is relative to the repository root.
[S2] Every «§N» (also §N‑M and §N‑letter) in the «where» part names a heading «N ·» in that file (outside code blocks), and
     every decision id (ق‑N, ف‑N, ك‑N) in it names a «## id ·» heading of DECISIONS.md.
     An ASCII hyphen (§٢-١, ق-٤) is reported as a wrong label, not skipped: headings use U+2011.
     The rest of «where» is free text and is not checked.
[S3] Every decision in the table of DECISIONS.md has a key in src/lib/decisions.mjs (itself or "id/…").
[S4] Every key of decisions.mjs whose base looks like a decision id is in that table.
[S5] Every page that owns a decision (a non-empty يملك, one-line or block list) declares a «مصدر».
     An empty «مصدر: []» is reported by S1.
[S6] Every family folder under reference/errors/ has a group with an Arabic label in src/lib/systems.mjs,
     so the sidebar never falls back to the folder name (site decision 23). And every group there has a folder.
Not checked yet: in decisions.mjs, only the first key of a line is read.
"""

from __future__ import annotations

import json
import re

from check_links import FENCE, blank, exists
from repo_files import ROOT, SITE_DIR, SITE_DOCS, finish, parser, walk

DECISIONS = ROOT / "DECISIONS.md"
INDEX = ROOT / SITE_DIR / "src" / "lib" / "decisions.mjs"

FRONT = re.compile(r"\A---\n(.*?)\n---", re.S)
FIELD = re.compile(r"^مصدر:\s*(.*)$", re.M)
# The hyphen is U+2011. An ASCII hyphen is matched too, so that it is reported rather than ignored.
DECISION_ID = re.compile(r"[قفك][‑-][٠-٩]+")
# A section label: §٢, §٢‑١٠, and a lettered subsection §١‑أ (a single letter after the hyphen).
SECTION = re.compile(r"§([٠-٩0-9]+(?:[‑-](?:[٠-٩0-9]+|[ء-ي](?![ء-ي])))?)")
# The owner key, as check-owners.mjs reads it (one-line list), or a YAML block list below it.
OWNS = re.compile(r"""^(["']?)يملك\1:[ \t]*(.*)$""", re.M)
# A row of the decision table: | **ق‑N** | ... |
TABLE_ROW = re.compile(r"^\| \*\*([قفك]‑[٠-٩]+)\*\* \|", re.M)
INDEX_KEY = re.compile(r"""^\s*(['"])([^'"]+)\1\s*:""", re.M)


def owns_decision(front: str) -> bool:
    """The page owns at least one decision: «يملك» with a non-empty value or block list."""
    m = OWNS.search(front)
    if not m:
        return False
    value = m.group(2).strip()
    if value:
        return value not in ("[]", "null", "~")
    # A block list: the next line is an indented «- item».
    following = front[m.end():].split("\n")[1:2]
    return bool(following) and re.match(r"^\s+-\s*\S", following[0]) is not None


def headings(path) -> str:
    # A «#» comment inside a code block is not a heading.
    text = FENCE.sub(blank, path.read_text(encoding="utf-8"))
    return "\n".join(l for l in text.split("\n") if l.startswith("#"))


def has_heading(heads: str, label: str) -> bool:
    return re.search(rf"^#+ {re.escape(label)} ·", heads, re.M) is not None


def check_pages(problems: list[str]) -> None:
    decision_heads = headings(DECISIONS)
    for relpath, p, _ in walk((".md", ".mdx")):
        if not relpath.startswith(SITE_DOCS + "/"):
            continue
        fm = FRONT.match(p.read_text(encoding="utf-8"))
        fields = FIELD.findall(fm.group(1)) if fm else []
        if not fields:
            if fm and owns_decision(fm.group(1)):
                problems.append(f"[S5] {relpath}: owns a decision (يملك) but declares no «مصدر»")
            continue
        if len(fields) > 1:
            problems.append(f"[S1] {relpath}: «مصدر» appears {len(fields)} times; write one list")
            continue
        try:
            entries = json.loads(fields[0])
            assert isinstance(entries, list) and all(isinstance(e, str) for e in entries)
        except (ValueError, AssertionError):
            problems.append(f"[S1] {relpath}: «مصدر» is not a one-line list of strings")
            continue
        if not entries:
            problems.append(f"[S1] {relpath}: «مصدر» is an empty list")
            continue
        for entry in entries:
            path, _, where = entry.partition("#")
            target = ROOT / path
            if not (exists(target) and target.is_file()):
                problems.append(f"[S1] {relpath}: source not found: {path}")
                continue
            heads = headings(target)
            for sec in SECTION.findall(where):
                if not has_heading(heads, sec):
                    problems.append(f"[S2] {relpath}: no heading «{sec} ·» in {path}")
            for did in DECISION_ID.findall(where):
                if not has_heading(decision_heads, did):
                    problems.append(f"[S2] {relpath}: no decision «{did}» in DECISIONS.md")


def check_index(problems: list[str]) -> None:
    table = TABLE_ROW.findall(DECISIONS.read_text(encoding="utf-8"))
    keys = [m.group(2) for m in INDEX_KEY.finditer(INDEX.read_text(encoding="utf-8"))]
    bases = {k.split("/", 1)[0] for k in keys}
    for did in table:
        if did not in bases:
            problems.append(f"[S3] DECISIONS.md: «{did}» has no key in decisions.mjs")
    for k in keys:
        base = k.split("/", 1)[0]
        if DECISION_ID.fullmatch(base) and base not in table:
            problems.append(f"[S4] decisions.mjs: «{k}» is not in the table of DECISIONS.md")


ERRORS_DIR = ROOT / SITE_DOCS / "reference" / "errors"
SYSTEMS = ROOT / SITE_DIR / "src" / "lib" / "systems.mjs"
# The errors group in systems.mjs: dir: 'errors', ..., groups: [{ dir: 'files', label: '...' }, ...]
ERRORS_GROUP = re.compile(r"dir:\s*'errors'.*?groups:\s*\[(.*?)\]", re.S)
GROUP = re.compile(r"\{\s*dir:\s*'([^']+)',\s*label:\s*'([^']+)'\s*\}")


def check_error_groups(problems: list[str]) -> None:
    folders = {p.name for p in ERRORS_DIR.iterdir() if p.is_dir()}
    match = ERRORS_GROUP.search(SYSTEMS.read_text(encoding="utf-8"))
    groups = dict(GROUP.findall(match.group(1))) if match else {}
    for folder in sorted(folders - set(groups)):
        problems.append(f"[S6] reference/errors/{folder}/ has no group in systems.mjs")
    for folder in sorted(set(groups) - folders):
        problems.append(f"[S6] systems.mjs: errors group '{folder}' has no folder")
    for folder, label in sorted(groups.items()):
        if not re.search(r"[ء-ي]", label):
            problems.append(f"[S6] systems.mjs: errors group '{folder}' has a non-Arabic label «{label}»")


def main() -> None:
    args = parser("Report site sources that do not resolve, and index/table mismatches.").parse_args()
    problems: list[str] = []
    check_pages(problems)
    check_index(problems)
    check_error_groups(problems)
    finish("check_sources", problems, args.strict)


if __name__ == "__main__":
    main()
