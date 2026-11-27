"""gen_style_guide: the site page of the style guide, generated from its source in حوكمة/.

The source حوكمة/دليل_الاسلوب.md is read as Markdown in the repository; its sections are wrapped in
<قسم حالة="..."> tags, which the site renders as status badges. This tool writes the site page:
front matter, the component import, a line saying the page is generated, then the source body
without its title and its opening note (the one blockquote right after the title; a later
blockquote is body and is kept). The note must be followed by a blank line; otherwise the tool
exits, naming the line.

Write the page:                      python tools/gen_style_guide.py
Check that the page is up to date:  python tools/gen_style_guide.py --check (exit 1 if not).
Paths are resolved from the repository root, so it runs from any directory.
"""

from __future__ import annotations

import argparse
import sys

from repo_files import ROOT, SITE_DOCS

SOURCE = "حوكمة/دليل_الاسلوب.md"
PAGE = f"{SITE_DOCS}/compiler/reference/standards/style-guide.mdx"
FRONT = """---
title: دليل الأسلوب
description: دليلُ أسلوب Rust لشفرة المترجم.
sidebar:
  order: 2
مصدر: ["{source}"]
---
import {{ قسم }} from '~/components';

{{/* مولَّد من {source} بـtools/gen_style_guide.py. لا يُعدَّل باليد: عدِّل المصدر ثمّ شغّل المولّد. */}}

"""


def render(source: str) -> str:
    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if not lines[0].startswith("# "):
        sys.exit(f"gen_style_guide: {SOURCE} must start with its title («# …»)")
    i = 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    note = i
    while i < len(lines) and lines[i].startswith(">"):  # the opening note: one blockquote
        i += 1
    if i > note and i < len(lines) and lines[i].strip():
        # Markdown reads this line as part of the note (lazy continuation), and the note is dropped.
        sys.exit(f"gen_style_guide: {SOURCE}: leave a blank line after the opening note (line {i + 1})")
    while i < len(lines) and not lines[i].strip():
        i += 1
    body = "\n".join(lines[i:]).rstrip("\n") + "\n"
    return FRONT.format(source=SOURCE) + body


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate the style guide's site page from its source.")
    ap.add_argument("--check", action="store_true", help="fail if the page differs from its source")
    args = ap.parse_args()
    # utf-8-sig: a BOM at the start of the source must not hide its title.
    out = render((ROOT / SOURCE).read_text(encoding="utf-8-sig"))
    page = ROOT / PAGE
    if args.check:
        # Bytes, not text: read_text's newline translation would let a CRLF page pass, and decoding
        # would crash on a page that is not UTF-8 (or, with errors="replace", could make it pass).
        current = page.read_bytes() if page.exists() else b""
        if current != out.encode("utf-8"):
            sys.exit(f"gen_style_guide: {PAGE} is out of date; run python tools/gen_style_guide.py")
        print("[gen_style_guide] page is up to date")
        return
    with open(page, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)
    print(f"[gen_style_guide] wrote {PAGE}")


if __name__ == "__main__":
    main()
