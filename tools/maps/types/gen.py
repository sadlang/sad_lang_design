"""يولّد خارطة نظام الأنواع (.html و.md) من outline.txt.

صيغةُ السطر في outline.txt:
    ## رقم | عنوان المنطقة | ما تتناوله | h | s | l
    - الاسم :: وصفٌ قصير [→ #معرِّف] {#٣.١} {T} {fam: أ} {name: مؤقت — السبب} {eq: int · i64} {own: ٢.٥.١.١} {§ مفتاح: القسم}
  الاسم       ما بين `…` اسمُ النوع في الشفرة، وما سواه وصفٌ لعقدةٍ لا اسمَ شفرةٍ لها
  :: …        وصفٌ قصيرٌ محايد (اختياريّ)
  [→ ..]      «انظر»: #معرِّفُ موضوعٍ في هذه الخارطة. والورقةُ التي لا شيءَ فيها غيرُها «إحالة»
  [↗ ..]      «انظر أيضًا»: مثلُها، والعقدةُ موضوعٌ قائمٌ بنفسه
  {#..}       المعرِّفُ الثابت (يُعطى مرّةً ولا يتغيّر إن نُقلت العقدة)
  {T}         العقدةُ نوعُ بياناتٍ (أو صيغةُ نوع)، لا موضوعٌ أو مثال
  {fam: ..}   أسرةُ الملكيّة كما في تصنيف_انواع_البيانات.md: أ · ب١ · ب٢ · ج-أصل · ج-تابع · د · أجزاء · سمة · ؟
  {name: ..}  حالُ الاسم حيث تقولها المصادر: مؤقت · بلا · صيغة · مرشح، و«*» تسري إلى ما تحته، وبعد «—» السبب
  {eq: ..}    نظيرُه في لغاتٍ أخرى (تلميحٌ خافت)
  {own: ..}   معرِّفُ العقدة المقابلة في خارطة نظام الملكيّة
  {§ ..}      مرجعُ المصدر: مفتاحُ الوثيقة ثمّ القسم

التشغيل:
    PYTHONIOENCODING=utf-8 python tools/maps/types/gen.py                # يولّد ويتحقّق
    PYTHONIOENCODING=utf-8 python tools/maps/types/gen.py --assign-ids   # يعطي العقدَ الجديدة معرّفاتٍ ويكتبها في outline.txt
"""
import json, re, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
# The generator and its template live in tools/; the outline and the generated map live with the system.
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OUT = os.path.join(REPO, "مواصفة", "انظمة", "الانواع", "خارطة")
OUTLINE = os.path.join(OUT, "outline.txt")
OWN_OUTLINE = os.path.join(OUT, "..", "..", "الملكية", "خارطة", "outline.txt")
LIST_DOC = os.path.join(OUT, "..", "وثائق", "قائمة_الانواع.md")
TAX_DOC = os.path.join(OUT, "..", "..", "الملكية", "وثائق", "تصنيف_انواع_البيانات.md")
NBH = "‑"
AD = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
def ad(x): return str(x).translate(AD)

OWN_HTML = "../../الملكية/خارطة/خارطة_نظام_الملكية.html"
SRC_DOCS = {
    "types": {"n": "نظام الأنواع (ق‑٤)",     "f": "../وثائق/نظام_الانواع.md"},
    "list":  {"n": "قائمة الأنواع",          "f": "../وثائق/قائمة_الانواع.md"},
    "tax":   {"n": "تصنيف أنواع البيانات",   "f": "../../الملكية/وثائق/تصنيف_انواع_البيانات.md"},
    "dec":   {"n": "DECISIONS.md",           "f": "../../../../DECISIONS.md"},
}
# أسرُ الملكيّة: النصُّ القصير، والتعريف، وموضعُها في خارطة الملكيّة
FAM = {
    "أ":      {"t": "أ · بيانات",          "d": "قيمٌ لا هويّةَ لها إلّا محتواها",                       "own": "٢.١.١"},
    "ب١":     {"t": "ب١ · موردٌ مُعلَن",    "d": "ما لا يُنسَخ، يُعلنه كاتبُ النوع بـ«مورد بنية»",         "own": "٢.١.٢.١"},
    "ب٢":     {"t": "ب٢ · بالعدوى",        "d": "مركّبٌ لا يُنسَخ لأنّه يحمل موردًا أو أصلَ «مشترك»",       "own": "٢.١.٢.٢"},
    "ج-أصل":  {"t": "ج · مشترك (أصل)",     "d": "الأصلُ يملك الصندوق",                                  "own": "٢.١.٣.١"},
    "ج-تابع": {"t": "ج · مشترك (تابع)",    "d": "التابعُ يصل إلى الصندوق ولا يملكه",                     "own": "٢.١.٣.٢"},
    "د":      {"t": "د · مرجعٌ صريح",      "d": "مرجعٌ بعمرٍ مسمّى، لمطوّر النُّظُم",                      "own": "٢.١.٤"},
    "أجزاء":  {"t": "الأسرةُ من أجزائه",    "d": "أسرةُ المركّب تُحسب من أجزائه",                          "own": "٢.٢"},
    "سمة":    {"t": "الأسرةُ تُعلَن في السمة", "d": "النوعُ الفعليّ مجهولٌ وقتَ الترجمة، فالأسرةُ تُعلَن في السمة", "own": "٢.٥.٦.١"},
    "؟":      {"t": "الأسرةُ لم تُتناوَل",   "d": "لم يتناولها تصنيفُ الأنواع بعد",                        "own": None},
}
NAME = {   # حالُ الاسم: نصُّ الشارة على النوع، ونصُّها على الفرع الذي تسري منه
    "مؤقت":  {"t": "اسمٌ مؤقّت",           "g": "أسماؤها مؤقّتة",      "s": "مؤقّت"},
    "بلا":   {"t": "(بلا اسم بعد)",        "g": "(بلا أسماء بعد)",     "s": "(بلا اسم بعد)"},
    "صيغة":  {"t": "صيغتُه لم تُقرَّر",     "g": "صيغتُها لم تُقرَّر",   "s": "صيغتُه لم تُقرَّر"},
    "مرشح":  {"t": "مرشّحٌ للنقاش",        "g": "مرشّحةٌ للنقاش",      "s": "مرشّح"},
}
ERRORS, NOTES = [], []
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
        node = {"_depth": depth, "_line": lineno, "_raw": line, "see": [], "_also": False, "tid": None,
                "src": None, "T": False, "fam": None, "name": None, "eq": None, "own": None}
        for grp in re.findall(r"\[([^\]]+)\]", text):
            g = grp.strip()
            if g[0] in "→↗":
                node["_also"] = node["_also"] or g[0] == "↗"
                for s in g[1:].split():
                    if not s.startswith("#"): err(f"line {lineno}: see without #: {s}")
                    node["see"].append(s[1:])
            else:
                err(f"line {lineno}: unknown bracket group {g}")
        for grp in re.findall(r"\{([^}]+)\}", text):
            g = grp.strip()
            if g.startswith("#"):
                if node["tid"]: err(f"line {lineno}: two ids")
                node["tid"] = g[1:].strip()
            elif g.startswith("§"):
                k, _, sec = g[1:].strip().partition(":")
                k = k.strip()
                if k not in SRC_DOCS: err(f"line {lineno}: unknown source key {k}")
                node["src"] = {"k": k, "s": sec.strip()}
            elif g == "T":
                node["T"] = True
            elif g.startswith("fam:"):
                v = g[4:].strip()
                if v not in FAM: err(f"line {lineno}: unknown family {v}")
                node["fam"] = v
            elif g.startswith("name:"):
                v, _, why = g[5:].strip().partition("—")
                v = v.strip(); inh = v.endswith("*"); v = v.rstrip("*")
                if v not in NAME: err(f"line {lineno}: unknown name status {v}")
                node["name"] = {"k": v, "r": why.strip(), "inh": inh}
            elif g.startswith("eq:"):
                node["eq"] = g[3:].strip()
            elif g.startswith("own:"):
                node["own"] = g[4:].strip()
            else:
                err(f"line {lineno}: unknown brace group {g}")
        body = re.sub(r"\s*\[[^\]]+\]|\s*\{[^}]+\}", "", text).strip()
        label, _, desc = body.partition(" :: ")
        node["t"], node["d"] = label.strip(), desc.strip()
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

# ---------- ids: assign (optional) ----------
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
        raw = re.sub(r"\s*\{#[^}]+\}", "", n["_raw"])
        raw = re.sub(r"\[([→↗])([^\]]+)\]",
                     lambda m: "[" + m.group(1) + " " + " ".join("#" + slug_map.get(s[1:], s[1:]) for s in m.group(2).split()) + "]", raw)
        # المعرِّفُ بعد الاسم والوصف والإحالات، وقبل بقيّة المجموعات
        m = re.search(r"\s\{", raw)
        raw = raw + " {#" + n["tid"] + "}" if not m else raw[:m.start()] + " {#" + n["tid"] + "}" + raw[m.start():]
        out.append(raw)
    open(OUTLINE, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print("ids assigned:", len(NODES), "slugs replaced:", len(slug_map))

if "--assign-ids" in sys.argv:
    assign_ids()
    sys.exit(0)

# ---------- ownership map: ids and paths ----------
def parse_own():
    out, stack, area = {}, [], None
    for raw in open(OWN_OUTLINE, encoding="utf-8"):
        line = raw.rstrip("\n")
        if line.startswith("## "):
            n, t = [p.strip() for p in line[3:].split("|")][:2]
            area = {"n": ad(n), "t": t}; stack = []
            out[ad(n)] = {"w": ad(n), "p": f"{ad(n)} · {t}"}
            continue
        m = re.match(r"^( *)- (.*)$", line)
        if not m: continue
        depth = len(m.group(1)) // 2
        tid = re.search(r"\{#([^}]+)\}", m.group(2)).group(1)
        lab = re.sub(r"\s*\[[^\]]+\]|\s*\{[^}]+\}", "", m.group(2)).strip().replace("`", "").replace("-", NBH)
        stack = stack[:depth] + [lab]
        w = f"{area['n']} › " + (stack[-2] if depth else stack[-1])
        out[tid] = {"w": w, "p": f"{area['n']} · {area['t']} › " + " › ".join(stack)}
    return out
OWN = parse_own()

# ---------- validate ----------
TOPICS = {a["tid"]: a for a in areas}
for n in NODES:
    if not n["tid"]: err(f"line {n['_line']}: node without id: {n['t']} (run --assign-ids)")
    elif not TOPIC_RE.match(n["tid"]): err(f"line {n['_line']}: non-numeric id {n['tid']} (run --assign-ids)")
    elif n["tid"] in TOPICS: err(f"line {n['_line']}: duplicate id {n['tid']}")
    else: TOPICS[n["tid"]] = n
for n in NODES:
    for s in n["see"]:
        if s not in TOPICS: err(f"line {n['_line']}: «انظر» to unknown topic {s}")
        elif TOPICS[s] is n: err(f"line {n['_line']}: «انظر» to itself #{s}")
    if n["own"] and n["own"] not in OWN: err(f"line {n['_line']}: own id not in ownership map: {n['own']}")
for f in FAM.values():
    if f["own"] and f["own"] not in OWN: err(f"family own id not in ownership map: {f['own']}")

# حالُ الاسم يسري من الفرع إلى ما تحته من أنواع
def eff_name(n):
    if n["name"]: return n["name"]
    if not n["T"]: return None          # يسري إلى الأنواع وحدها، لا إلى الفئات والأمثلة
    p = n["_parent"]
    while "n" not in p:
        if p["name"] and p["name"]["inh"]: return dict(p["name"], inh=False, via=p["tid"])
        p = p["_parent"]
    return None
for n in NODES: n["_name"] = eff_name(n)

# خارطةٌ بلا أحكام: لا علامات قرار ولا رموزَ قرارات في الأسماء والأوصاف
BAD_MARK = re.compile(r"[✅📝⚠️⬜⏸🧵⛔]")
BAD_CODE = re.compile(r"(?:^|[\s(«])(?:[مأصعفقلسرن]" + NBH + r"[٠-٩أ-ي]|[سل][٠-٩]|LP-)")
for n in NODES:
    for what, s in (("label", n["t"]), ("desc", n["d"])):
        if BAD_MARK.search(s): err(f"line {n['_line']}: decision mark in {what}: {s}")
        if BAD_CODE.search(s): err(f"line {n['_line']}: decision code in {what}: {s}")
    if n["t"].count("`") % 2 or n["d"].count("`") % 2: err(f"line {n['_line']}: unbalanced backticks")

def codes(s): return re.findall(r"`([^`]+)`", s)
def type_key(n):
    """اسمُ النوع: أوّلُ مقطعٍ برمجيٍّ في اسم العقدة، إن وُجد."""
    c = codes(n["t"]); return c[0] if c else None
TYPES = [n for n in NODES if n["T"]]
seen = {}
for n in TYPES:
    k = type_key(n) or n["t"]
    if k in seen: err(f"line {n['_line']}: type {k} listed twice as {{T}} (line {seen[k]['_line']}); use [→ #..]")
    seen[k] = n

# كلُّ اسمٍ في قائمة_الانواع.md يظهر في الخارطة
LABEL_CODES = {c for n in NODES for c in codes(n["t"])}
ALL_CODES = LABEL_CODES | {c for n in NODES for c in codes(n["d"])}
IGNORE = {   # أسماءٌ في قائمة الأنواع ليست أنواعًا، أو نصّت القائمةُ على أنّها لا تُكتب
    "عدد": "الاسمُ الأوّل للعدد الصحيح، ثمّ صار `رقم`، ثمّ `رقمي`",
    "رقم": "الاسمُ السابق للعدد الصحيح (٢٠٢٦-١٠-٠٧)، صار `رقمي` (٢٠٢٦-١٠-١١)",
    "اي خطأ": "الكتابةُ القديمة لـ`اي_خطأ`",
    "عشري٨": "نصّت القائمةُ على أن لا `عشري٨`",
    "رقمي٦٤": "الاسمُ المجرّد هو عرضُ ٦٤، فلا يُكتب",
    "طبيعي٦٤": "الاسمُ المجرّد هو عرضُ ٦٤، فلا يُكتب",
    "عشري٦٤": "الاسمُ المجرّد هو عرضُ ٦٤، فلا يُكتب",
    "الخطأ": "اسمُ حقلٍ في `نتيجة`",
    "جا": "دالّةٌ رياضيّة", "جتا": "دالّةٌ رياضيّة", "اس": "دالّةٌ رياضيّة", "لو": "دالّةٌ رياضيّة",
    "جذر_تكعيبي": "دالّةٌ رياضيّة",
    "قرّب": "دالّةُ تقريبٍ مقترحة", "ارضية": "دالّةُ تقريبٍ مقترحة", "سقف": "دالّةُ تقريبٍ مقترحة",
    "مال": "مثالٌ لنوعٍ يعرّفه المطوّر", "صحيح(\"1\")": "مثالٌ من لغة ألف", "عشري(\"0.5\")": "مثالٌ من لغة ألف",
    "س.الى_رقمي٣٢()": "صيغةٌ مرفوضة", "الى": "اسمُ الطريقة العامّة `س.الى<ت>()`", "جا(١٫٠)": "تعبير", "٠٫٠ \\ ٠٫٠": "تعبير", "محدود؟": "دالّةٌ في المكتبة",
    '" ١٢ "': "نصٌّ يُحلَّل", '"-١٢"': "نصٌّ يُحلَّل", '"+١٢"': "نصٌّ يُحلَّل", '"1٢"': "نصٌّ يُحلَّل",
}
list_text = open(LIST_DOC, encoding="utf-8").read()
LIST_TOKENS = []
for x in re.findall(r"`([^`\n]+)`", list_text):
    if re.search(r"[؀-ۿ]", x) and x not in LIST_TOKENS: LIST_TOKENS.append(x)
def present(tok, pool):
    return tok in pool or any(c.startswith(tok + "<") for c in pool)
list_missing, list_desc_only = [], []
for tok in LIST_TOKENS:
    if tok in IGNORE: continue
    if present(tok, LABEL_CODES): continue
    if present(tok, ALL_CODES): list_desc_only.append(tok); continue
    list_missing.append(tok)
if list_missing: err(f"names in قائمة_الانواع.md missing from the map: {list_missing}")
# مواردُ المكتبة في تصنيف_انواع_البيانات.md §٤‑و
tax_text = open(TAX_DOC, encoding="utf-8").read()
sec = tax_text.split("### ٤‑و")[1].split("### ٤‑ز")[0]
TAX_RES = []
for row in sec.splitlines():
    if row.startswith("|") and not row.startswith("|---") and "الفئة" not in row:
        cell = row.split("|")[2]
        TAX_RES += [x for x in codes(cell) if re.search(r"[؀-ۿ]", x)]
tax_missing = [x for x in TAX_RES if x not in LABEL_CODES]
if tax_missing: err(f"resources in تصنيف_انواع_البيانات.md §٤‑و missing: {tax_missing}")

if ERRORS:
    print("\n".join("ERROR: " + e for e in ERRORS))
    sys.exit(1)

# ---------- stats ----------
TARGETS = {s for n in NODES for s in n["see"]}
def is_ref(n):
    """الإحالة: ورقةٌ كلُّ ما فيها «انظر»، وليست هي موضعَ موضوعٍ يُحال إليه."""
    return not n.get("c") and bool(n["see"]) and not n["_also"] and not n["T"] and n["tid"] not in TARGETS
def sub(n): return list(all_nodes(n))
def nk(n): return n["_name"]["k"] if n["_name"] else None
def tstats(ns):
    ts = [x for x in ns if x["T"]]
    return {"types": len(ts),
            "named": sum(1 for x in ts if nk(x) not in ("بلا", "صيغة")),
            "prov": sum(1 for x in ts if nk(x) == "مؤقت"),
            "unnamed": sum(1 for x in ts if nk(x) in ("بلا", "صيغة")),
            "cand": sum(1 for x in ts if nk(x) == "مرشح")}
stats = []
for a in areas:
    ns = sub(a)
    st = {"top": len(a["c"]), "groups": sum(1 for x in ns if x.get("c")), "leaves": sum(1 for x in ns if not x.get("c")),
          "refs": sum(1 for x in ns if is_ref(x)), "nodes": len(ns), **tstats(ns)}
    a["_st"] = st; stats.append(st)
TOT = {k: sum(s[k] for s in stats) for k in stats[0]}
print(f"areas {len(areas)} · nodes {TOT['nodes']} (top {TOT['top']} · branches {TOT['groups']} · leaves {TOT['leaves']}, refs {TOT['refs']}) · "
      f"types {TOT['types']} (named {TOT['named']} · provisional {TOT['prov']} · unnamed/form {TOT['unnamed']} · candidates {TOT['cand']})")
for a in areas:
    s = a["_st"]; print(f"  {a['n']:>2} {a['t']}: nodes {s['nodes']} types {s['types']} prov {s['prov']} unnamed {s['unnamed']} cand {s['cand']}")
print(f"قائمة_الانواع.md: {len(LIST_TOKENS)} names · ignored {len([t for t in LIST_TOKENS if t in IGNORE])} · "
      f"in descriptions only: {list_desc_only}")
print(f"تصنيف §٤‑و resources: {len(TAX_RES)} all present")

def plain(t): return t.replace("`", "")
def where(tid):
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
    for k in ("d", "fam", "eq", "own", "src"):
        if n[k]: o[k] = n[k]
    if n["T"]: o["T"] = 1
    if n["see"]: o["see"] = n["see"]
    if n["_also"]: o["also"] = 1
    if is_ref(n): o["r"] = 1
    if n["_name"]:
        nm = n["_name"]; o["nm"] = {"k": nm["k"], "r": nm["r"]}
        if nm["inh"]: o["nm"]["g"] = 1
        if nm.get("via"): o["nm"]["via"] = 1
    if n.get("c"): o["c"] = [export(k) for k in n["c"]]
    return o
DATA = [{"n": a["n"], "t": a["t"], "d": a["d"], "h": a["h"], "s": a["s"], "l": a["l"], "tid": a["tid"],
         "st": a["_st"], "c": [export(k) for k in a["c"]]} for a in areas]
WHERE = {tid: {"w": where(tid), "p": path(T) if "n" not in T else f"{ad(T['n'])} · {T['t']}"} for tid, T in TOPICS.items()}
OWN_USED = {n["own"] for n in NODES if n["own"]} | {f["own"] for f in FAM.values() if f["own"]}
tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
for key, val in {"DATA": DATA, "WHERE": WHERE, "SRC_DOCS": SRC_DOCS, "FAM": FAM, "NAME": NAME,
                 "OWN": {k: OWN[k] for k in sorted(OWN_USED)}, "OWN_HTML": OWN_HTML,
                 "TOT": dict(TOT, areas=len(areas))}.items():
    marker = f"/*__{key}__*/null"
    assert marker in tpl, marker
    tpl = tpl.replace(marker, json.dumps(val, ensure_ascii=False))
open(os.path.join(OUT, "خارطة_نظام_الانواع.html"), "w", encoding="utf-8", newline="\n").write(tpl)

# ---------- Markdown ----------
def mm(label):
    s = label.replace("`", "").replace("<", "‹").replace(">", "›")
    s = re.sub(r"[()\[\]{}\"]", "", s)
    s = s.replace("«", "").replace("»", "")
    return re.sub(r"\s+", " ", s).strip()

def mm_node(n, indent, out):
    lab = mm(n["t"])
    if nk(n) == "بلا": lab += " · بلا اسم بعد"
    out.append(" " * indent + lab)
    for k in n.get("c", []): mm_node(k, indent + 2, out)

def own_md(oid): return f"[الملكيّة {OWN[oid]['w']}]({OWN_HTML}#{oid})"
def li(n, depth, out):
    lab = n["t"]
    if nk(n) == "بلا": lab += " _(بلا اسم بعد)_"
    lab = f"**{lab}**" if n.get("c") else (f"_{lab}_" if is_ref(n) else lab)
    parts = [lab]
    if n["d"]: parts.append("— " + n["d"])
    tags = []
    if n["_name"] and nk(n) != "بلا":
        tags.append("‹" + (NAME[nk(n)]["g"] if n["_name"]["inh"] else NAME[nk(n)]["t"]) + "›")
    if n["fam"]: tags.append(f"‹{FAM[n['fam']]['t']}›")
    for s in n["see"]:
        tags.append(f"← {'انظر أيضًا' if n['_also'] else 'انظر'} {where(s)} ‹{s}›")
    if n["own"]: tags.append("← انظر " + own_md(n["own"]))
    if n["eq"]: tags.append(f"≈ <code dir=\"ltr\">{n['eq']}</code>")
    meta = n["tid"] + (f" · {src_text(n['src'])}" if n["src"] else "")
    out.append("  " * depth + "- " + " ".join(parts + tags) + f" <sub>{meta}</sub>")
    for k in n.get("c", []): li(k, depth + 1, out)

H = ad
md = []
md += [
    "# خارطةُ نظام الأنواع",
    "",
    "> **أنواعُ البيانات في لغة ص وأسماؤها:** كلُّ منطقةٍ وما تحتها من أنواعٍ وموضوعات، ولكلّ نوعٍ اسمُه كما في المصادر، ووصفٌ قصير،",
    "> وأسرةُ ملكيّته حيث نصّ عليها تصنيفُ الأنواع. **بنيةٌ لا أحكام:** الأسماءُ تسمّي النوعَ أو الموضوع، والحكمُ في الوثائق الحاكمة.",
    "> **التاريخ:** ٢٠٢٦-١٠-٠٧ · **النسخةُ التفاعليّة:** [خارطة_نظام_الانواع.html](خارطة_نظام_الانواع.html) (بحثٌ وطيٌّ وروابطُ عميقة) ·",
    "> **الخارطةُ الشقيقة:** [خارطة نظام الملكيّة](../../الملكية/خارطة/خارطة_نظام_الملكية.html) ([md](../../الملكية/خارطة/خارطة_نظام_الملكية.md)).",
    f"> **المصادر:** [نظام_الانواع.md]({SRC_DOCS['types']['f']}) (ق‑٤) · [قائمة_الانواع.md]({SRC_DOCS['list']['f']}) ·",
    f"> [تصنيف_انواع_البيانات.md]({SRC_DOCS['tax']['f']}) · [DECISIONS.md]({SRC_DOCS['dec']['f']}) (ق‑٤ وف‑١). الروابطُ نسبيّة: تعمل حين تُفتح الخارطةُ من مجلّدها في المستودع.",
    "",
    "## كيف تُقرأ",
    "",
    "- **`رقمي`** اسمُ النوع في الشفرة كما في المصادر. والعقدةُ التي لا اسمَ شفرةٍ لها موضوعٌ أو صيغة، و**_(بلا اسم بعد)_** نوعٌ ذكرته المصادرُ ولم تسمّه.",
    "- **‹اسمٌ مؤقّت›** حيث تقول المصادرُ إنّ الاسمَ مقترحٌ أو مؤقّتٌ أو لم يُحسَم، و**‹صيغتُه لم تُقرَّر›** حيث لم تُقرَّر صيغةُ كتابته، و**‹مرشّحٌ للنقاش›** لما لم تذكره وثيقةٌ قبل قائمة الأنواع. وعلى الفرع **‹أسماؤها مؤقّتة›** تسري إلى كلّ ما تحته.",
    "- **‹أ · بيانات›** وأمثالُها أسرةُ الملكيّة كما في تصنيف الأنواع: أ بيانات · ب١ موردٌ مُعلَن · ب٢ بالعدوى · ج مشترك (أصلٌ أو تابع) · د مرجعٌ صريح. و«الأسرةُ من أجزائه» للمركّب.",
    "- **«← انظر الملكيّة ٢ › الأوّليّة»** رابطٌ إلى العقدة المقابلة في خارطة نظام الملكيّة، و**«← انظر ٤ › `اختياري<ن>`»** إلى موضعٍ في هذه الخارطة.",
    "- **≈ `int · i64`** نظيرُ النوع في لغاتٍ أخرى، تلميحٌ لا تعريف.",
    "- **_الإحالة_** (بخطٍّ مائل) ورقةٌ لا شيءَ فيها إلّا «انظر»: النوعُ مذكورٌ هنا لصلته، وموضعُه الأصليّ واحد.",
    "- **<sub>٣.١</sub>** المعرِّفُ الثابت، يُعطى مرّةً ولا يتغيّر إن نُقلت العقدة. وفي النسخة التفاعليّة رابطٌ عميق: `#٣.١`، أو باسم النوع: `#رقمي٣٢`. ويليه مرجعُ المصدر حيث ذُكر.",
    "- **في المخطّطات** تُختصَر الأسماءُ وتُحذف منها الأقواسُ والعلامات التي تكسر صيغة Mermaid، والنصُّ الكامل في «الشجرة نصًّا».",
    "",
    f"**الأرقام:** {H(len(areas))} منطقة · {H(TOT['nodes'])} عقدة ({H(TOT['groups'])} فرعًا · {H(TOT['leaves'])} ورقة، منها {H(TOT['refs'])} إحالة) · "
    f"**{H(TOT['types'])} نوعًا**: {H(TOT['named'])} مسمًّى (منها {H(TOT['prov'])} باسمٍ مؤقّت و{H(TOT['cand'])} مرشّحًا للنقاش) و{H(TOT['unnamed'])} بلا اسمٍ أو صيغة بعد.",
    "", "---", "", "## ١ · نظرةٌ عامّة", "", "```mermaid", "mindmap", "  root((نظامُ الأنواع))"]
for a in areas:
    md.append(f"    {ad(a['n'])} · {mm(a['t'])}")
md += ["```", "",
       "| # | المنطقة | ما تتناوله | العقد | الأنواع | باسمٍ مؤقّت | بلا اسم بعد | مرشّحة |",
       "|---:|---|---|---:|---:|---:|---:|---:|"]
dash = lambda v: H(v) if v else "—"
for a in areas:
    s = a["_st"]
    md.append(f"| {ad(a['n'])} | **{a['t']}** | {a['d']} | {H(s['nodes'])} | {dash(s['types'])} | {dash(s['prov'])} | {dash(s['unnamed'])} | {dash(s['cand'])} |")
md += [f"| | **المجموع** | | **{H(TOT['nodes'])}** | **{H(TOT['types'])}** | **{H(TOT['prov'])}** | **{H(TOT['unnamed'])}** | **{H(TOT['cand'])}** |",
       "", "---", "", "## ٢ · المناطقُ مخطّطاتٍ", ""]

SPLIT_AT = 40
def size(ks): return sum(1 + len(sub(k)) for k in ks)
def diagrams(title, root_label, kids, out):
    """يقسم المخطّطَ الكبير: يُفرَد أكبرُ فرعٍ في مخطّطٍ وحده ما دام الباقي فوق الحدّ، ويُقسَم المُفرَدُ كذلك."""
    rest, alone = list(kids), []
    while size(rest) > SPLIT_AT and len(rest) > 1:
        big = max(rest, key=lambda k: len(sub(k)))
        rest.remove(big); alone.append(big)
    if title or alone:
        names = "» و«".join(plain(k["t"]) for k in alone)
        out += [(title or "#### المنطقةُ") + (f" دون «{names}»" if alone else ""), ""]
    out += ["```mermaid", "mindmap", f"  root(({root_label}))"]
    body = []
    for k in rest: mm_node(k, 4, body)
    out += body + ["```", ""]
    for k in alone:
        diagrams(f"#### {plain(k['t'])}", f"{root_label} › {mm(k['t'])}", k.get("c", []), out)
for a in areas:
    md += [f"### {ad(a['n'])} · {a['t']}", "", f"> {a['d']}.", ""]
    diagrams(None, ad(a["n"]), a["c"], md)
# العنوانُ الفارغ يترك سطرين فارغين: يُنظَّفان
md2 = []
for x in md:
    if x == "" and md2 and md2[-1] == "": continue
    md2.append(x)
md = md2
md += ["---", "", "## ٣ · الشجرةُ نصًّا", ""]
for a in areas:
    md += [f"### {ad(a['n'])} · {a['t']}", ""]
    out = []
    for k in a["c"]: li(k, 0, out)
    md += out + [""]
md += ["---", "", "## ٤ · فهرسُ الأنواع", "",
       "كلُّ عقدةٍ هي نوعُ بياناتٍ أو صيغةُ نوع، بترتيب الخارطة.", "",
       "| الاسم | الموضع | حالُ الاسم | الأسرة | المعرِّف |", "|---|---|---|---|---|"]
for n in TYPES:
    st = "بلا اسم بعد" if nk(n) == "بلا" else (NAME[nk(n)]["t"] if n["_name"] else "—")
    fam = FAM[n["fam"]]["t"] if n["fam"] else "—"
    nm = n["t"].replace("|", "\\|")
    md.append(f"| {nm} | {where(n['tid'])} | {st} | {fam} | {n['tid']} |")
md.append("")
open(os.path.join(OUT, "خارطة_نظام_الانواع.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md))
print("written")
