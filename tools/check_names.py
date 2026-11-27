"""check_names: file and folder names follow حوكمة/اصطلاحات_المستودع.md (section «التسمية»).

Rules (the id in brackets is printed with each violation):
  [N1] no spaces in names.
  [N2] no hamza on alef (أ إ آ) in Arabic names, as in K-1; except «خطأ» and the fixed name «اقرأني.md».
  [N3] digits in names are Western (0-9), and every number outside the date has two digits:
       01_ 02_ ... at the start or in the middle of a name.
  [N4] a record (in a system's مراجعات/) is named <topic>_<author>_<YYYY-MM-DD>.md; a record of
       several files is a folder named <topic>_<YYYY-MM-DD>/, and the names inside it are free
       of this pattern (N1-N3 still apply to them).
       (the author is omitted for a council).
  [N5] a dated record (a file, or a folder of several files) lives in a
       system's مراجعات/, nowhere else.
  [N6] names under data/ and tools/ are ASCII snake_case.
  [N7] site page paths (src/content/docs) are ASCII kebab-case, translated not transliterated.
  [N8] a content folder with more than two files, or with any subfolder, has an اقرأني.md,
       or an ancestor's اقرأني.md names it by its path from there (`<folder>/`, `<sub>/<folder>/`).
Names imposed by tools (README.md, DECISIONS.md, AGENTS.md, CLAUDE.md, LICENSE, NOTICE,
CONTRIBUTING.md, dot-files) are exempt. Inside .github/ and the site folder only N5 applies
(and N7 under src/content/docs); inside data/ and tools/ only N6.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from repo_files import ROOT, SITE_DIR, SITE_DOCS, finish, is_record, parser, walk

TOOL_NAMES = {"README.md", "DECISIONS.md", "AGENTS.md", "CLAUDE.md", "LICENSE", "NOTICE", "CONTRIBUTING.md"}
INDEX = "اقرأني.md"
HAMZA_EXEMPT_WORDS = ("خطأ",)
HAMZA_ALEF = re.compile("[أإآ]")
EASTERN_DIGITS = re.compile("[٠-٩۰-۹]")
# [0-9], not \d: in Python \d also matches Eastern digits, which [N3] reports on its own.
NUMBER = re.compile(r"[0-9]+")
DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
DATED = re.compile(r"_[0-9]{4}-[0-9]{2}-[0-9]{2}\.\w+$")
RECORD_NAME = re.compile(r"^[^\s]+_[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$")
RECORD_FOLDER = re.compile(r"^[^\s]+_[0-9]{4}-[0-9]{2}-[0-9]{2}$")
SNAKE = re.compile(r"^[a-z0-9_]+(\.[a-z0-9]+)*$")
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# Site slugs transliterated from Arabic; decision 6 of the reorganization: translate them.
TRANSLITERATED = {"raqmi": "integer", "tabii": "natural", "ashri": "decimal"}
# Folders whose content is not ours to name, or is named by a tool.
FOREIGN = (".github/", f"{SITE_DIR}/")


def in_record_folder(relpath: str) -> bool:
    """Inside a dated record folder (a record of several files). Callers also check is_record()."""
    parts = relpath.split("/")[:-1]
    return any(RECORD_FOLDER.match(p) for p in parts)


def is_record_root(relpath: str) -> bool:
    """A system's مراجعات/: a records folder whose parent holds no records.

    A folder named مراجعات inside another مراجعات/ is not a root, so it is
    a record folder and must be dated like one.
    """
    parent = relpath.rpartition("/")[0]
    return not parent or not is_record(parent + "/")


def is_content(relpath: str) -> bool:
    return not relpath.startswith(FOREIGN + ("data/", "tools/")) and not relpath.startswith(".")


def check_name(relpath: str, name: str, is_dir: bool) -> list[str]:
    out = []
    if name in TOOL_NAMES or name.startswith("."):
        return out
    if relpath.startswith(SITE_DOCS + "/"):
        stem = name if is_dir else name.split(".", 1)[0]
        if not KEBAB.match(stem) and stem != "404":
            out.append(f"[N7] {relpath}: site path is not ASCII kebab-case")
        if stem in TRANSLITERATED:
            out.append(f"[N7] {relpath}: transliterated slug; translate to «{TRANSLITERATED[stem]}»")
        return out
    if relpath.startswith(("data/", "tools/")):
        if not SNAKE.match(name):
            out.append(f"[N6] {relpath}: not ASCII snake_case")
        return out
    if relpath.startswith(FOREIGN):
        if not is_dir and DATED.search(name) and name.endswith(".md"):
            out.append(f"[N5] {relpath}: dated record outside مراجعات/")
        if is_dir and RECORD_FOLDER.match(name):
            out.append(f"[N5] {relpath}: dated record folder outside مراجعات/")
        return out
    if " " in name:
        out.append(f"[N1] {relpath}: name contains a space")
    if name != INDEX:
        stripped = name
        for w in HAMZA_EXEMPT_WORDS:
            stripped = stripped.replace(w, "")
        if HAMZA_ALEF.search(stripped):
            out.append(f"[N2] {relpath}: hamza on alef in name")
    if EASTERN_DIGITS.search(name):
        out.append(f"[N3] {relpath}: Eastern Arabic digits in name; use 0-9")
    if any(len(n) != 2 for n in NUMBER.findall(DATE.sub("", name))):
        out.append(f"[N3] {relpath}: a number in the name must have two digits (01_)")
    if is_dir and is_record(relpath + "/") and not is_record_root(relpath) and not in_record_folder(relpath) and not RECORD_FOLDER.match(name):
        out.append(f"[N4] {relpath}: record folder not named <topic>_<YYYY-MM-DD>")
    if is_dir and RECORD_FOLDER.match(name) and not is_record(relpath + "/"):
        out.append(f"[N5] {relpath}: dated record folder outside مراجعات/")
    if not is_dir:
        if is_record(relpath) and name != INDEX and not in_record_folder(relpath) and not RECORD_NAME.match(name):
            out.append(f"[N4] {relpath}: record not named <topic>_<author>_<YYYY-MM-DD>.md")
        if DATED.search(name) and name.endswith(".md") and not is_record(relpath):
            out.append(f"[N5] {relpath}: dated record outside مراجعات/")
    return out


def indexed(folder: Path) -> bool:
    """The folder has its own index, or an ancestor's index names it by its path from there.

    From the parent that path is `<folder>/`; from a grandparent `<sub>/<folder>/`, and so on.
    It must start a word: `قواعد التهيئة/` does not name `التهيئة/`, nor `x/وثائق/` name `وثائق/`.
    """
    if (folder / INDEX).exists():
        return True
    for parent in folder.parents:
        if parent == ROOT or ROOT not in parent.parents:
            return False
        idx = parent / INDEX
        if idx.exists():
            path = folder.relative_to(parent).as_posix() + "/"
            if re.search(rf"(?<![\w/]){re.escape(path)}", idx.read_text(encoding="utf-8")):
                return True
    return False


def main() -> None:
    ap = parser("Report names that break the repository conventions.")
    ap.add_argument("--baseline", type=Path, help="ignore violations already listed here (one per line)")
    ap.add_argument("--write-baseline", type=Path, help="write current violations here and exit 0")
    args = ap.parse_args()
    problems = []
    for relpath, p, is_dir in walk(include_dirs=True):
        problems += check_name(relpath, p.name, is_dir)
        if is_dir and is_content(relpath + "/"):
            entries = [e for e in p.iterdir() if not e.name.startswith(".")]
            files = [e for e in entries if e.is_file()]
            if (len(files) > 2 or len(files) < len(entries)) and not indexed(p):
                problems.append(f"[N8] {relpath}/: more than two files or a subfolder, and no {INDEX}")
    if args.write_baseline:
        args.write_baseline.parent.mkdir(parents=True, exist_ok=True)
        with open(args.write_baseline, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("".join(p + "\n" for p in sorted(problems)))
        finish("check_names", problems, False)
    if args.baseline:
        if not args.baseline.is_file():
            sys.exit(f"check_names: baseline file not found: {args.baseline}")
        known = set(args.baseline.read_text(encoding="utf-8").splitlines()) - {""}
        # Not a problem: a fixed name should also be removed from the baseline.
        for k in sorted(known - set(problems)):
            print(f"note: baseline entry fixed: {k}")
        problems = [p for p in problems if p not in known]
    finish("check_names", problems, args.strict)


if __name__ == "__main__":
    main()
