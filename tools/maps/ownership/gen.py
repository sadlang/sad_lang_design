"""يولّد خارطة نظام الملكيّة (.html و.md) من outline.txt.

صيغةُ السطر في outline.txt:
    ## رقم | عنوان المنطقة | ما تتناوله | h | s | l
    - الاسم [ت-١ ت-٢] [→ خ-٨ #٢.٤.٣] {#٣.١.١} {§ مفتاح: القسم}
  [..]     أرقامُ حالات القائمة التي موضعُها الأصليّ هنا
  [→ ..]   «انظر»: رقمُ حالة، أو #معرِّفُ موضوع. والورقةُ التي لا شيءَ فيها غيرُها «إحالة»
  [↗ ..]   «انظر أيضًا»: مثلُها، والعقدةُ موضوعٌ قائمٌ بنفسه لا إحالة
  {#..}    معرِّفُ الموضوع الثابت (يُعطى مرّةً ولا يتغيّر إن نُقلت العقدة)
  {§ ..}   مرجعُ المصدر: مفتاحُ الوثيقة ثمّ القسم
  {¶ ..}   نصٌّ يُعرض عند الضغط: ق١ … ق٤ (القواعد) أو ث١ … ث٤ (الثوابت)، يُستخرج من نظام_الملكية.md عند التوليد

التشغيل:
    PYTHONIOENCODING=utf-8 python tools/maps/ownership/gen.py                # يولّد ويتحقّق
    PYTHONIOENCODING=utf-8 python tools/maps/ownership/gen.py --assign-ids   # يعطي العقدَ الجديدة معرّفاتٍ ويكتبها في outline.txt
"""
import json, re, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
# The generator and its template live in tools/; the outline and the generated map live with the system.
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OUT = os.path.join(REPO, "مواصفة", "انظمة", "الملكية", "خارطة")
OUTLINE = os.path.join(OUT, "outline.txt")
NBH = "‑"
AD = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
def ad(x): return str(x).translate(AD)

SRC_DOCS = {
    "own":   {"n": "نظام الملكيّة",        "f": "../وثائق/نظام_الملكية.md"},
    "tax":   {"n": "تصنيف أنواع البيانات", "f": "../وثائق/تصنيف_انواع_البيانات.md"},
    "sum":   {"n": "ملخّص نظام الذاكرة",   "f": "../وثائق/ملخص_نظام_الذاكرة.md"},
    "road":  {"n": "خارطة الطريق",         "f": "../خطة/خارطة_طريق_نظام_الملكية.md"},
    "list":  {"n": "قائمة تدفّق القيم",     "f": "../وثائق/قائمة_حالات_تدفق_القيم.md"},
    "dec":   {"n": "DECISIONS.md",         "f": "../../../../DECISIONS.md"},
    "types": {"n": "نظام الأنواع",         "f": "../../الانواع/وثائق/نظام_الانواع.md"},
}
ERRORS = []
def err(msg): ERRORS.append(msg)

# ---------- parse ----------
TOPIC_RE = re.compile(r"^[٠-٩]+(?:\.[٠-٩]+)*$")
def parse():
    areas, stack, lines = [], [], []
    for lineno, raw in enumerate(open(OUTLINE, encoding="utf-8"), 1):
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        if line.startswith("## "):
            n, t, d, h, s, l = [p.strip() for p in line[3:].split("|")]
            area = {"n": int(n), "t": t, "d": d, "h": int(h), "s": int(s), "l": int(l), "c": [],
                    "tid": ad(n), "_line": lineno, "_raw": line}
            areas.append(area)
            stack = [(-1, area)]
            lines.append(("area", area))
            continue
        m = re.match(r"^( *)- (.*)$", line)
        if not m:
            sys.exit(f"bad line {lineno}: {line}")
        depth = len(m.group(1)) // 2
        text = m.group(2)
        ids, see, tid, src, also, xkey = [], [], None, None, False, None
        for grp in re.findall(r"\[([^\]]+)\]", text):
            g = grp.strip()
            if g.startswith("→"):
                see += g[1:].split()
            elif g.startswith("↗"):
                see += g[1:].split(); also = True
            else:
                ids += g.split()
        for grp in re.findall(r"\{([^}]+)\}", text):
            g = grp.strip()
            if g.startswith("#"):
                if tid: err(f"line {lineno}: two ids")
                tid = g[1:].strip()
            elif g.startswith("¶"):
                xkey = g[1:].strip()
            elif g.startswith("§"):
                k, _, sec = g[1:].strip().partition(":")
                k = k.strip()
                if k not in SRC_DOCS: err(f"line {lineno}: unknown source key {k}")
                src = {"k": k, "s": sec.strip()}
            else:
                err(f"line {lineno}: unknown brace group {g}")
        raw_label = re.sub(r"\s*\[[^\]]+\]|\s*\{[^}]+\}", "", text).strip()
        node = {"t": raw_label.replace("-", NBH), "_raw_label": raw_label, "_depth": depth, "_line": lineno}
        node["ids"] = [i.replace("-", NBH) for i in ids]
        node["see"] = [(i[1:] if i.startswith("#") else i.replace("-", NBH)) for i in see]
        node["_see_raw"] = see
        node["_also"] = also
        node["tid"] = tid
        node["src"] = src
        node["x"] = xkey
        while stack and stack[-1][0] >= depth:
            stack.pop()
        parent = stack[-1][1]
        node["_parent"] = parent
        node["_area"] = stack[0][1]
        parent.setdefault("c", []).append(node)
        stack.append((depth, node))
        lines.append(("node", node))
    return areas, lines

areas, lines = parse()

def all_nodes(n):
    for k in n.get("c", []):
        yield k
        yield from all_nodes(k)
NODES = [x for a in areas for x in all_nodes(a)]

# ---------- topic ids: assign (optional) ----------
def assign_ids():
    used = {a["tid"] for a in areas} | {n["tid"] for n in NODES if n["tid"] and TOPIC_RE.match(n["tid"])}
    slug_map = {}
    def visit(parent):
        prefix = parent["tid"] + "."
        nums = [int(k["tid"][len(prefix):].translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")))
                for k in parent.get("c", []) if k["tid"] and TOPIC_RE.match(k["tid"])
                and k["tid"].startswith(prefix) and "." not in k["tid"][len(prefix):]]
        nxt = max(nums, default=0) + 1
        for k in parent.get("c", []):
            if not (k["tid"] and TOPIC_RE.match(k["tid"])):
                while prefix + ad(nxt) in used: nxt += 1
                new = prefix + ad(nxt); used.add(new); nxt += 1
                if k["tid"]: slug_map[k["tid"]] = new
                k["tid"] = new
            visit(k)
    for a in areas: visit(a)
    out = []
    for kind, n in lines:
        if kind == "area":
            out.append(n["_raw"]); continue
        parts = [n["_raw_label"]]
        if n["ids"]: parts.append("[" + " ".join(i.replace(NBH, "-") for i in n["ids"]) + "]")
        if n["_see_raw"]:
            parts.append(("[↗ " if n["_also"] else "[→ ") + " ".join(("#" + slug_map.get(s[1:], s[1:])) if s.startswith("#") else s
                                          for s in n["_see_raw"]) + "]")
        parts.append("{#" + n["tid"] + "}")
        if n["src"]: parts.append("{§ " + n["src"]["k"] + ": " + n["src"]["s"] + "}")
        if n.get("x"): parts.append("{¶ " + n["x"] + "}")
        out.append("  " * n["_depth"] + "- " + " ".join(parts))
    open(OUTLINE, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print("ids assigned:", len(NODES), "slugs replaced:", len(slug_map))

if "--assign-ids" in sys.argv:
    assign_ids()
    sys.exit(0)

# ---------- validate ----------
TOPICS = {a["tid"]: a for a in areas}
for n in NODES:
    if not n["tid"]: err(f"line {n['_line']}: node without id: {n['t']} (run --assign-ids)")
    elif not TOPIC_RE.match(n["tid"]): err(f"line {n['_line']}: non-numeric id {n['tid']} (run --assign-ids)")
    elif n["tid"] in TOPICS: err(f"line {n['_line']}: duplicate id {n['tid']}")
    else: TOPICS[n["tid"]] = n

def seq(prefix, n): return [f"{prefix}{NBH}{ad(i)}" for i in range(1, n + 1)]
H_LETTERS = ["أ", "ب", "ج", "د", "هـ", "و", "ز", "ح", "ط", "ي", "ك", "ل", "م", "ن", "س", "ع", "ف", "ص", "ق"]
SECTIONS = [
    {"t": "١ · التهيئةُ والإسناد", "ids": seq("ت", 27)},
    {"t": "٢ · النداء", "ids": seq("ن", 30)},
    {"t": "٣ · التخزين", "ids": seq("خ", 27)},
    {"t": "٤ · الإرجاع", "ids": seq("ر", 25)},
    {"t": "٥ · الخروجُ من النطاق والتحرير", "ids": [f"ح{NBH}{x}" for x in H_LETTERS]},
]
expected = [i for s in SECTIONS for i in s["ids"]]
assert len(expected) == 128, len(expected)
CASE_RE = re.compile(r"^[تنخرح]" + NBH + r"\S+$")

placed = {}
for n in NODES:
    for i in n["ids"]:
        if i in placed: err(f"DUPLICATE case {i}: line {placed[i]['_line']} and {n['_line']}")
        placed[i] = n
missing = [i for i in expected if i not in placed]
extra = [i for i in placed if i not in expected]
if missing: err(f"missing cases: {missing}")
if extra: err(f"unknown cases: {extra}")
for n in NODES:
    for s in n["see"]:
        if CASE_RE.match(s):
            if s not in placed: err(f"line {n['_line']}: «انظر» to unplaced case {s}")
            elif placed[s] is n: err(f"line {n['_line']}: «انظر» to itself {s}")
        elif s not in TOPICS: err(f"line {n['_line']}: «انظر» to unknown topic {s}")
        elif TOPICS[s] is n: err(f"line {n['_line']}: «انظر» to itself #{s}")
# خارطةٌ بلا أحكام: لا علامات قرار ولا رموزَ قرارات في الأسماء
BAD_MARK = re.compile(r"[✅📝⚠️⬜⏸🧵]")
BAD_CODE = re.compile(r"(?:^|[\s(«])(?:[مأصعفقلس]" + NBH + r"[٠-٩أ-ي]|[سل][٠-٩])")
for n in NODES:
    if BAD_MARK.search(n["t"]): err(f"line {n['_line']}: decision mark in label: {n['t']}")
    if BAD_CODE.search(n["t"]): err(f"line {n['_line']}: decision code in label: {n['t']}")

# ---------- نصوصُ القواعد والثوابت (من نظام_الملكية.md) ----------
OWN_DOC = os.path.join(OUT, "..", "وثائق", "نظام_الملكية.md")
def md_inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
def paras(lines):
    out, cur = [], []
    for l in lines:
        if l.strip(): cur.append(l.strip())
        elif cur: out.append(" ".join(cur)); cur = []
    if cur: out.append(" ".join(cur))
    return out
def extract_texts():
    L = open(OWN_DOC, encoding="utf-8").read().split("\n")
    T = {}
    # القواعد: الاقتباسُ الذي يبدأ بـ«أربعُ قواعد»
    i = next(k for k, l in enumerate(L) if l.startswith("> **أربعُ قواعد"))
    block = []
    for l in L[i + 1:]:
        if not l.startswith(">"): break
        block.append(l[1:].lstrip(" "))
    cur = None
    for l in block:
        m = re.match(r"^\*\*([١-٤])\. (.+?)\*\*", l)
        if m:
            cur = "ق" + m.group(1)
            T[cur] = {"t": m.group(2).strip().rstrip(":.،"), "lines": [l], "s": "القرار · القاعدة " + m.group(1)}
        elif cur: T[cur]["lines"].append(l)
    # الثوابت: قسمُ «أربعةُ ثوابت»
    i = next(k for k, l in enumerate(L) if l.startswith("### أربعةُ ثوابت"))
    cur = None
    for l in L[i + 1:]:
        if l.startswith("### "): break
        m = re.match(r"^- \*\*(ث[١-٤]) · ([^*]+)", l)
        if m:
            cur = m.group(1)
            T[cur] = {"t": re.split(r"[:.]", m.group(2))[0].strip(), "lines": [l[2:]], "s": "أربعةُ ثوابت · " + cur}
        elif cur and l.startswith("  "): T[cur]["lines"].append(l)
        elif cur and not l.strip(): cur = None
    for k, v in T.items():
        if k.startswith("ث"):
            m = re.search(r"ث[١-٤] · (.+?)\*\*", " ".join(x.strip() for x in v["lines"]))
            if m: v["t"] = re.split(r"[:.]", m.group(1))[0].strip()
    return {k: {"t": v["t"], "s": v["s"], "md": paras(v["lines"]),
                "h": "".join(f"<p>{md_inline(p)}</p>" for p in paras(v["lines"]))} for k, v in T.items()}
TEXTS = extract_texts()
for k in ["ق١", "ق٢", "ق٣", "ق٤", "ث١", "ث٢", "ث٣", "ث٤"]:
    if k not in TEXTS: err(f"text {k} not found in نظام_الملكية.md")
for n in NODES:
    if n.get("x"):
        if n["x"] not in TEXTS: err(f"line {n['_line']}: unknown text key {n['x']}")
        elif "tid" in TEXTS[n["x"]]: err(f"line {n['_line']}: text {n['x']} linked twice")
        else: TEXTS[n["x"]]["tid"] = n["tid"]
for k in TEXTS:
    if "tid" not in TEXTS[k]: err(f"text {k} has no node in outline (add {{¶ {k}}})")

if ERRORS:
    print("\n".join("ERROR: " + e for e in ERRORS))
    sys.exit(1)

# ---------- stats ----------
TARGETS = {s for n in NODES for s in n["see"] if not CASE_RE.match(s)}
def is_ref(n):
    """الإحالة: ورقةٌ بلا حالات، كلُّ ما فيها «انظر»، وليست هي موضعَ موضوعٍ يُحال إليه."""
    return not n.get("c") and not n["ids"] and bool(n["see"]) and not n["_also"] and n["tid"] not in TARGETS
def sub(n): return list(all_nodes(n))
stats = []
for a in areas:
    ns = sub(a)
    st = {"top": len(a["c"]), "groups": sum(1 for x in ns if x.get("c")),
          "leaves": sum(1 for x in ns if not x.get("c")), "refs": sum(1 for x in ns if is_ref(x)),
          "ids": sum(len(x["ids"]) for x in ns), "nodes": len(ns)}
    a["_st"] = st; stats.append(st)
TOT = {k: sum(s[k] for s in stats) for k in stats[0]}
print(f"areas {len(areas)} · top {TOT['top']} · branches {TOT['groups']} · leaves {TOT['leaves']} "
      f"(refs {TOT['refs']}) · nodes {TOT['nodes']} · cases {len(placed)}/{len(expected)}")
for a in areas:
    s = a["_st"]; print(f"  {a['n']:>2} {a['t']}: top {s['top']} branches {s['groups']} leaves {s['leaves']} refs {s['refs']} ids {s['ids']}")

def plain(t): return t.replace("`", "")
def where(tid):
    """موضعُ موضوعٍ مختصرًا: رقمُ المنطقة › اسمُ الفرع الذي فيه (أو اسمُه إن كان في المستوى الأوّل)."""
    T = TOPICS[tid]
    if "n" in T: return ad(T["n"])
    P = T["_parent"]
    return f"{ad(T['_area']['n'])} › {plain(T['t'] if 'n' in P else P['t'])}"
def path(n):
    out = []
    while "n" not in n:
        out.append(plain(n["t"])); n = n["_parent"]
    return f"{ad(n['n'])} · {n['t']} › " + " › ".join(reversed(out))
def src_text(src): return f"{SRC_DOCS[src['k']]['n']} › {src['s']}" if src else ""

# ---------- HTML ----------
def export(n):
    o = {"t": n["t"], "tid": n["tid"]}
    if n["ids"]: o["ids"] = n["ids"]
    if n["see"]: o["see"] = n["see"]
    if is_ref(n): o["r"] = 1
    if n["src"]: o["src"] = n["src"]
    if n.get("x"): o["x"] = n["x"]
    if n.get("c"): o["c"] = [export(k) for k in n["c"]]
    return o
DATA = [{"n": a["n"], "t": a["t"], "d": a["d"], "h": a["h"], "s": a["s"], "l": a["l"], "tid": a["tid"],
         "c": [export(k) for k in a["c"]]} for a in areas]
WHERE = {tid: {"w": where(tid), "p": path(T) if "n" not in T else f"{ad(T['n'])} · {T['t']}"}
         for tid, T in TOPICS.items()}
tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
TEXTS_JS = {k: {"t": v["t"], "s": v["s"], "h": v["h"], "tid": v["tid"]} for k, v in TEXTS.items()}
for key, val in {"DATA": DATA, "SECTIONS": SECTIONS, "WHERE": WHERE, "SRC_DOCS": SRC_DOCS, "TEXTS": TEXTS_JS,
                 "TOT": dict(TOT, areas=len(areas), cases=len(placed))}.items():
    marker = f"/*__{key}__*/null"
    assert marker in tpl, marker
    tpl = tpl.replace(marker, json.dumps(val, ensure_ascii=False))
open(os.path.join(OUT, "خارطة_نظام_الملكية.html"), "w", encoding="utf-8", newline="\n").write(tpl)

# ---------- Markdown ----------
def mm(label):
    s = label.replace("`", "").replace("<", "‹").replace(">", "›")
    s = re.sub(r"[()\[\]{}\"]", "", s)
    s = s.replace("«", "").replace("»", "")
    return re.sub(r"\s+", " ", s).strip()

def mm_node(n, indent, out):
    lab = mm(n["t"])
    if n["ids"]: lab += " · " + " ".join(n["ids"])
    out.append(" " * indent + lab)
    for k in n.get("c", []): mm_node(k, indent + 2, out)

def see_md(s, ref):
    w = "انظر" if ref else "انظر أيضًا"
    return f"← {w} `{s}`" if CASE_RE.match(s) else f"← {w} {where(s)} ‹{s}›"

def li(n, depth, out):
    lab = n["t"]
    lab = f"**{lab}**" if n.get("c") else (f"_{lab}_" if is_ref(n) else lab)
    tags = "".join(f" `{i}`" for i in n["ids"])
    tags += "".join(" " + see_md(s, is_ref(n)) for s in n["see"])
    meta = n["tid"] + (f" · {src_text(n['src'])}" if n["src"] else "")
    if n.get("x"): tags += f" · ¶ نصُّه في §٥ ({n['x']})"
    out.append("  " * depth + "- " + lab + tags + f" <sub>{meta}</sub>")
    for k in n.get("c", []): li(k, depth + 1, out)

H = lambda x: ad(x)
md = []
md += [
    "# خارطةُ نظام الملكيّة",
    "",
    "> **بنيةُ نظام الملكيّة والذاكرة في لغة ص:** كلُّ منطقةٍ وما تحتها من فروعٍ وحالات. **بنيةٌ لا أحكام:** الأسماءُ تسمّي",
    "> الموضوعَ أو الحالة، والحكمُ في الوثائق الحاكمة. وأسماءُ الآليّات (قفلُ القرّاء والكاتب، فحصُ الجيل، النقلُ عند التسليم…) ترد أسماءً لا أحكامًا.",
    "> **التاريخ:** ٢٠٢٦-١٠-٠٧ · **النسخةُ التفاعليّة:** [خارطة_نظام_الملكية.html](خارطة_نظام_الملكية.html) (بحثٌ وطيٌّ وروابطُ عميقة).",
    "> **المصادر:** [قائمة_حالات_تدفق_القيم.md](../وثائق/قائمة_حالات_تدفق_القيم.md) · [نظام_الملكية.md](../وثائق/نظام_الملكية.md) ·",
    "> [تصنيف_انواع_البيانات.md](../وثائق/تصنيف_انواع_البيانات.md) · [ملخص_نظام_الذاكرة.md](../وثائق/ملخص_نظام_الذاكرة.md) · [خارطة_طريق_نظام_الملكية.md](../خطة/خارطة_طريق_نظام_الملكية.md) ·",
    "> [DECISIONS.md](../../../../DECISIONS.md) · [نظام_الانواع.md](../../الانواع/وثائق/نظام_الانواع.md). الروابطُ نسبيّة: تعمل حين تُفتح الخارطةُ من مجلّدها في المستودع.",
    "",
    "## كيف تُقرأ",
    "",
    "- **فرع** عقدةٌ تحتها شيء (بخطٍّ عريض)، و**ورقة** عقدةٌ لا شيءَ تحتها. و**الموضوعُ الرئيس** عقدةٌ في المستوى الأوّل من منطقتها، فرعًا كان أو ورقة.",
    f"- **`ت{NBH}١`** وأمثالُه رقمُ الحالة في [قائمة تدفّق القيم](../وثائق/قائمة_حالات_تدفق_القيم.md): ت التهيئة · ن النداء · خ التخزين · ر الإرجاع · ح الخروج.",
    f"- **«← انظر `خ{NBH}١٧`»** الحالةُ موضعُها الأصليّ في مكانٍ آخر، وتُذكر هنا لصلتها.",
    "- **«← انظر ٩ › المهامُّ غيرُ المتزامنة ‹٩.٥.٦›»** الموضوعُ موضعُه الأصليّ هناك: رقمُ المنطقة › الفرعُ الذي فيه، ثمّ معرِّفُه.",
    "- **_الإحالة_** (بخطٍّ مائل) ورقةٌ لا شيءَ فيها إلّا «انظر»: الموضوعُ نفسُه مذكورٌ هنا لصلته، وموضعُه الأصليّ واحد.",
    "- **«← انظر أيضًا …»** على موضوعٍ قائمٍ بنفسه: موضوعٌ قريبٌ منه في مكانٍ آخر.",
    "- **<sub>٢.٤.٣</sub>** معرِّفُ الموضوع: **ثابت**، يُعطى مرّةً ولا يتغيّر إن نُقلت العقدة، فقد لا يطابق موضعَها الحاليّ. وفي النسخة التفاعليّة رابطٌ عميق: `#٢.٤.٣` أو `#ن-16`. ويليه مرجعُ المصدر حيث ذُكر.",
    f"- **كلُّ حالةٍ من الـ{ad(len(expected))} في موضعٍ أصليٍّ واحد** من الخارطة، والجدولُ في آخر الملفّ يدلّ عليه.",
    "- **في المخطّطات** تُختصَر الأسماءُ وتُحذف منها الأقواسُ والعلامات التي تكسر صيغة Mermaid، والنصُّ الكامل في «الشجرة نصًّا».",
    "",
    "### رموزٌ أخرى في المصادر",
    "",
    "الوثائقُ التي تقود إليها الخارطةُ تستعمل حروفَ الحالات نفسَها لأشياءَ أخرى. هذا الجدولُ للتمييز وحده، لا حكمَ فيه.",
    "",
    "| تراه في المصادر | معناه هناك | لا يُخلط بـ |",
    "|---|---|---|",
    f"| `قت{NBH}١` … `قت{NBH}١٤` | قواعدُ التهيئة في قائمة تدفّق القيم. كانت تُكتب `ر{NBH}` حتى ٢٠٢٦-١٠-٠٧، فإن صادفتَ «ر‑٧ التهيئةُ الشرطيّة» أو «موردٌ ثابت (ر‑١٢)» في نصٍّ أقدم فهي قاعدةٌ لا حالة | حالاتُ الإرجاع `ر{NBH}١` … `ر{NBH}٢٥` |",
    f"| `ن٥` (بلا شَرطة) · `ن{NBH}١` … `ن{NBH}٣` في تدقيق ق‑٣ | `ن٥` المستقبِلُ المستهلَك في مراجعة ص‑٣، و`ن{NBH}١` … `ن{NBH}٣` أسئلةُ التدقيق | حالاتُ النداء `ن{NBH}١` … `ن{NBH}٣٠` |",
    f"| `ح{NBH}١` … `ح{NBH}٣` · `ح١` … `ح٥` | أسئلةُ تدقيق · وعلاقاتُ العمر في الحالة المشتركة (المنطقة ١٠ › علاقاتُ العمر) | حالاتُ الخروج `ح{NBH}أ` … `ح{NBH}ق` (بالحروف) |",
    f"| `م{NBH}أ` … `م{NBH}ز` · `م{NBH}١` … `م{NBH}٩` | بنودُ قاعدة `مشترك` · وأسئلةُ تدقيق | — |",
    f"| `ب١` · `ب٢` · `ب١` … `ب١٣` | قسما الأسرة ب (موردٌ مُعلَن · مركّبٌ بالعدوى) · وبذورُ ق‑٤ في نظام الأنواع | كلٌّ منهما بالآخر |",
    "",
]
md.append(f"**الأرقام:** {H(len(areas))} منطقة · {H(TOT['top'])} موضوعًا رئيسًا · {H(TOT['groups'])} فرعًا · "
          f"{H(TOT['leaves'])} ورقة (منها {H(TOT['refs'])} إحالة) · {H(len(placed))} حالةً من القائمة.")
md += ["", "---", "", "## ١ · نظرةٌ عامّة", "", "```mermaid", "mindmap", "  root((نظامُ الملكيّة))"]
for a in areas:
    md.append(f"    {ad(a['n'])} · {mm(a['t'])}")
md += ["```", "",
       "| # | المنطقة | ما تتناوله | الموضوعاتُ الرئيسة | الفروع | الأوراق | حالاتُ القائمة |",
       "|---:|---|---|---:|---:|---:|---:|"]
for a in areas:
    s = a["_st"]
    md.append(f"| {ad(a['n'])} | **{a['t']}** | {a['d']} | {ad(s['top'])} | {ad(s['groups'])} | {ad(s['leaves'])} | {ad(s['ids']) if s['ids'] else '—'} |")
md += [f"| | **المجموع** | | **{H(TOT['top'])}** | **{H(TOT['groups'])}** | **{H(TOT['leaves'])}** | **{H(len(placed))}** |",
       "", "---", "", "## ٢ · المناطقُ مخطّطاتٍ", ""]

SPLIT_AT = 70
def diagrams(a):
    """يقسم المنطقةَ الكبيرة: يُفرَد أكبرُ موضوعٍ رئيس في مخطّطٍ وحده ما دام الباقي فوق الحدّ."""
    rest, alone = list(a["c"]), []
    size = lambda ks: sum(1 + len(sub(k)) for k in ks)
    while size(rest) > SPLIT_AT and len(rest) > 1:
        big = max(rest, key=lambda k: len(sub(k)))
        rest.remove(big); alone.append(big)
    return rest, alone
for a in areas:
    md += [f"### {ad(a['n'])} · {a['t']}", "", f"> {a['d']}.", ""]
    rest, alone = diagrams(a)
    letters = iter("أبجده")
    if alone:
        names = "» و«".join(plain(k["t"]) for k in alone)
        md += [f"#### {ad(a['n'])}{NBH}{next(letters)} · المنطقةُ دون «{names}»", ""]
    md += ["```mermaid", "mindmap", f"  root(({ad(a['n'])} · {mm(a['t'])}))"]
    out = []
    for k in rest: mm_node(k, 4, out)
    md += out + ["```", ""]
    for k in alone:
        md += [f"#### {ad(a['n'])}{NBH}{next(letters)} · {plain(k['t'])}", "",
               "```mermaid", "mindmap", f"  root(({ad(a['n'])} › {mm(k['t'])}))"]
        out = []
        for kk in k.get("c", []): mm_node(kk, 4, out)
        md += out + ["```", ""]
md += ["---", "", "## ٣ · الشجرةُ نصًّا", ""]
for a in areas:
    md += [f"### {ad(a['n'])} · {a['t']}", ""]
    out = []
    for k in a["c"]: li(k, 0, out)
    md += out + [""]
md += ["---", "", "## ٤ · أين تقع كلُّ حالةٍ من القائمة", "",
       "| قسمُ القائمة | الحالة ← المنطقة · الموضوعُ الرئيس |", "|---|---|"]
for sec in SECTIONS:
    cells = []
    for i in sec["ids"]:
        n = placed[i]
        top = n
        while "n" not in top["_parent"]: top = top["_parent"]
        cells.append(f"`{i}` ← {ad(n['_area']['n'])} · {plain(top['t'])}")
    md.append(f"| **{sec['t']}** ({ad(len(sec['ids']))}) | " + " · ".join(cells) + " |")
md += ["", "---", "", "## ٥ · نصوصُ القواعد والثوابت", "",
       "> منقولةٌ كما هي من [نظام_الملكية.md](../وثائق/نظام_الملكية.md) عند كلّ توليد. وفي النسخة التفاعليّة يفتحها الضغطُ على القاعدة أو الثابت.", ""]
for k, v in TEXTS.items():
    md += [f"### {k} · {v['t']}", "", f"<sub>{v['s']} · موضعُه في الخارطة ‹{v['tid']}›</sub>", ""]
    for para in v["md"]: md += [para, ""]
md.append("")
open(os.path.join(OUT, "خارطة_نظام_الملكية.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md))
print("written")
