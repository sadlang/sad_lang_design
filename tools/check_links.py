"""check_links: every relative link in .md/.mdx resolves to an existing file or site page.

Repository files: the link is resolved against the linking file's directory
(percent-encoding decoded, #anchor and ?query dropped).
Site pages (under the site's src/content/docs): links are routes. A page a/b/c.mdx
is served at /a/b/c/, so ../x/ from it means /a/b/x/; the route must map to
x.md(x) or x/index.md(x). Anchors are not checked yet. A site link starting with / is
broken: the site is served under the repository name (site decision 24), so it must be relative.
Inline links, images and reference definitions are checked, outside code; names must
match case exactly, as on the Linux CI. Not checked: HTML href/src and MDX imports.

--baseline FILE ignores the broken links recorded in FILE (one "file -> target" per line),
so a move can be checked for links it broke, apart from those already broken.
"""

from __future__ import annotations

import functools
import os
import posixpath
import re
import sys
from pathlib import Path
from urllib.parse import unquote

from repo_files import ROOT, SITE_DOCS, finish, parser, walk

# Inline link or image: [text](target), [text](<target>), with an optional "t", 't' or (t) title.
# The text may hold one level of brackets: [a [b] c](x).
LINK = re.compile(
    r"!?\[(?:[^\[\]\n]|\[[^\[\]\n]*\])*\]\(\s*(<[^>\n]+>|[^)\s]+)"
    r"(?:\s+(?:\"[^\"\n]*\"|'[^'\n]*'|\([^)\n]*\)))?\s*\)"
)
# Reference definition: [label]: target  (not a footnote [^1]: ...).
REF_DEF = re.compile(r"^[ ]{0,3}\[(?!\^)[^\]\n]+\]:[ \t]*(<[^>\n]+>|\S+)", re.M)
# Fenced code: may be indented (inside a list), longer than three marks, or unclosed until the end.
FENCE = re.compile(r"^[ \t]*(?P<f>`{3,}|~{3,})[^\n]*\n.*?(?:^[ \t]*(?P=f)[`~]*[ \t]*$|\Z)", re.S | re.M)
INLINE_CODE = re.compile(r"`[^`\n]+`")
EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", re.I)


def blank(m: re.Match) -> str:
    return re.sub(r"[^\n]", " ", m.group())


@functools.lru_cache(maxsize=None)
def _names(directory: str) -> frozenset[str]:
    try:
        return frozenset(os.listdir(directory))
    except OSError:
        return frozenset()


def exists(path: Path) -> bool:
    """Case-exact existence: Windows and macOS ignore case, the Linux CI does not."""
    full = os.path.normpath(path)
    try:
        parts = Path(full).relative_to(ROOT).parts
    except ValueError:
        return os.path.exists(full)
    cur = str(ROOT)
    for part in parts:
        if part not in _names(cur):
            return False
        cur = os.path.join(cur, part)
    return True


def site_route_exists(route: str) -> bool:
    route = route.strip("/")
    docs = ROOT / SITE_DOCS
    candidates = [docs / f"{route}.md", docs / f"{route}.mdx", docs / route / "index.md", docs / route / "index.mdx"]
    if not route:
        candidates = [docs / "index.md", docs / "index.mdx"]
    return any(exists(c) and c.is_file() for c in candidates)


def page_route(relpath: str) -> str:
    inner = relpath[len(SITE_DOCS) + 1 :]
    inner = re.sub(r"\.mdx?$", "", inner)
    if inner == "index" or inner.endswith("/index"):
        inner = inner[: -len("index")]
    else:
        inner += "/"
    return "/" + inner


def resolve(relpath: str, target: str) -> bool:
    target = target.strip("<>")
    path = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not path:
        return True
    if relpath.startswith(SITE_DOCS + "/"):
        if Path(path).suffix in ("", ".html") or path.endswith("/"):
            if path.startswith("/"):
                return False  # يخرج من عنوان الموقع على GitHub Pages (قرارات الموقع، القرار ٢٤)
            return site_route_exists(posixpath.normpath(posixpath.join(page_route(relpath), path)))
    if path.startswith("/"):
        return exists(ROOT / path.lstrip("/"))
    return exists(ROOT / posixpath.dirname(relpath) / path)


def broken_links() -> list[tuple[str, int, str]]:
    out = []
    for relpath, p, _ in walk((".md", ".mdx")):
        text = p.read_text(encoding="utf-8")
        text = FENCE.sub(blank, text)
        text = INLINE_CODE.sub(blank, text)
        matches = sorted([*LINK.finditer(text), *REF_DEF.finditer(text)], key=lambda m: m.start())
        for m in matches:
            target = m.group(1)
            if EXTERNAL.match(target.strip("<>")):
                continue
            if not resolve(relpath, target):
                line = text.count("\n", 0, m.start()) + 1
                out.append((relpath, line, target))
    return out


def main() -> None:
    ap = parser("Report relative links that do not resolve.")
    ap.add_argument("--baseline", type=Path, help="ignore broken links already listed here")
    ap.add_argument("--write-baseline", type=Path, help="write current broken links here and exit 0")
    args = ap.parse_args()

    found = broken_links()
    keys = [f"{f} -> {t}" for f, _, t in found]
    if args.write_baseline:
        args.write_baseline.parent.mkdir(parents=True, exist_ok=True)
        with open(args.write_baseline, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("".join(k + "\n" for k in sorted(set(keys))))
    known = set()
    if args.baseline:
        if not args.baseline.is_file():
            # A mistyped path must not silently disable the baseline.
            sys.exit(f"check_links: baseline file not found: {args.baseline}")
        known = set(args.baseline.read_text(encoding="utf-8").splitlines()) - {""}
        # Not a problem: a fixed link should also be removed from the baseline.
        for k in sorted(known - set(keys)):
            print(f"note: baseline entry no longer broken: {k}")
    problems = [
        f"{f}:{line}: broken link -> {t}"
        for (f, line, t), k in zip(found, keys)
        if k not in known
    ]
    finish("check_links", problems, args.strict and not args.write_baseline)


if __name__ == "__main__":
    main()
