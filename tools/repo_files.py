"""Shared helpers for the repository checks in tools/.

Walks the repository and yields files, skipping generated and third-party trees.
All checks run in report mode by default (print, exit 0); --strict makes them fail.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Windows consoles and pipes default to a legacy code page; force UTF-8 for Arabic output
# before anything is printed (Linux CI is UTF-8 already).
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent

SITE_DIR = "موقع_اللغة"
SITE_DOCS = f"{SITE_DIR}/src/content/docs"

# Directories never scanned: generated output, dependencies, and vendored agent skills.
SKIP_DIRS = {".git", "node_modules", "dist", ".astro", "__pycache__"}
SKIP_PREFIXES = (".github/skills/",)

# Records: immutable dated logs. They are cited, never governing.
RECORD_DIRS: tuple[str, ...] = ()
RECORD_SEGMENT = "/مراجعات/"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def is_record(relpath: str) -> bool:
    # The index of a records folder is kept up to date by hand: it is not a record.
    if relpath.rsplit("/", 1)[-1] == "اقرأني.md":
        return False
    return relpath.startswith(RECORD_DIRS) or RECORD_SEGMENT in f"/{relpath}"


def walk(suffixes: tuple[str, ...] | None = None, include_dirs: bool = False):
    """Yield (relpath, Path, is_dir) for every repository entry not skipped."""
    for dirpath, dirnames, filenames in os.walk(ROOT):
        base = Path(dirpath)
        kept = []
        for d in sorted(dirnames):
            r = rel(base / d) + "/"
            if d in SKIP_DIRS or r.startswith(SKIP_PREFIXES):
                continue
            kept.append(d)
            if include_dirs:
                yield r.rstrip("/"), base / d, True
        dirnames[:] = kept
        for f in sorted(filenames):
            p = base / f
            r = rel(p)
            if r.startswith(SKIP_PREFIXES):
                continue
            if suffixes is None or p.suffix in suffixes:
                yield r, p, False


def parser(description: str) -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--strict", action="store_true", help="exit 1 when any violation is found")
    return ap


def finish(name: str, problems: list[str], strict: bool) -> None:
    for p in problems:
        print(p)
    mode = "strict" if strict else "report"
    print(f"[{name}] {len(problems)} problem(s) ({mode} mode)")
    sys.exit(1 if strict and problems else 0)
