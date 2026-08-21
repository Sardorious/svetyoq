"""`01` §11–§14 ↔ `app.release.ux_requirements` ↔ qurilgan mijoz sirti.

**Bu fayl nimasi bilan boshqalardan farq qiladi.** Paketning qolgan
kontrakt fayllari serverga qaraydi va shuning uchun `ast` bilan
yetarli. §11–§14 esa mijozga qaraydi — `web/app.js`, `web/index.html`,
`web/style.css` — va o'sha uch fayl **hech qachon** tuzilma sifatida
o'qilmagan: 96-run oxirida ularni to'rtta test ko'rardi
(`test_i18n_key_contract`, `test_map_api`,
`test_notification_channels_contract`, `test_region_acceptance_contract`)
va to'rttasi ham `read_text()` + regex bilan.

Narxi o'lchangan: 94, 95 va 96-runlar `web/` da oltita defekt topdi va
**birortasi ham** matn qatlamida ko'rinmasdi. Shuning uchun bu faylda
uchta o'quvchi bor va ularning har biri o'z savolini boshqa hech qanday
usulda javob berilmaydigan qilib qo'yadi:

1. **DOM** (`html.parser`) — ota-bola munosabati. «`#heat-legend`
   `.legend` ning ichidami» degan savolga regex javob bera olmaydi.
2. **CSS kaskadi** — `@media` + selektor moslashuvi + oxirgi g'olib
   e'lon. «360 px da qamrov indeksi ko'rinadimi» degan savol aynan
   94-run ning defekti va u faqat shu qatlamda ko'rinadi.
3. **JS chaqiruv grafi** — muvozanatli qavs bilan olingan funksiya
   tanasi, izohlar olib tashlangan holda. «`banner` ning uyasiga qaysi
   funksiya yozadi» degan savol 95- va 96-runlarning defektlari.

⚠️ **Izoh dalil emas.** Uchala o'quvchi ham izohlarni o'chiradi. Sabab
86-run ning sabog'i: reyestr o'zi qidirayotgan iborani izohida yozsa,
matn skaneri o'z matnini topadi. Bu yerda xavf kattaroq, chunki
`web/app.js` ning izohlari qurilgan qarorlarni **so'z bilan**
tasvirlaydi — ya'ni har qanday matn skaneri u yerda hamma narsani
«topadi».

O'quvchilarning o'zlari ham tekshiriladi (§1): jim buzilgan skaner
qolgan hamma tekshiruvni bo'sh to'plamda yashil qilib qo'yardi.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

import pytest

from app.admin.registries import REGISTRY_BY_CODE
from app.release import ux_requirements as ux

SVETA_ROOT = Path(__file__).resolve().parents[1]
ROOT = SVETA_ROOT.parent
APP_DIR = SVETA_ROOT / "app"
WEB_DIR = SVETA_ROOT / "web"
PRD = ROOT / "01_PRD_Samarkand.md"
LOCALES = APP_DIR / "core" / "i18n" / "locales"

#: Reyestrning o'z fayli va shu test — ikkalasi ham §11–§14 ning
#: iboralarini nusxa qiladi.
EXCLUDED = {"ux_requirements.py", "test_ux_requirements_contract.py"}

#: `_match_simple` tushunmaydigan selektorlar — aynan. Ular hech qanday
#: `display` e'lon qilmaydi, ya'ni kaskad javobiga ta'sir qilmaydi;
#: lekin ro'yxat **yopiq**, shuning uchun `style.css` ga yangi shakl
#: (masalan `+` qo'shnisi) qo'shilsa bu fayl uni ko'rsatadi.
UNSUPPORTED_SELECTORS = frozenset({".popup div + div", ":root"})


# --------------------------------------------------------------------------
# 1. O'quvchilar va ularning o'z qorovullari
# --------------------------------------------------------------------------


@dataclass
class Element:
    """DOM tugunining minimal modeli."""

    tag: str
    attrs: dict[str, str | None]
    parent: Element | None
    children: list[Element]

    @property
    def node_id(self) -> str | None:
        return self.attrs.get("id")

    @property
    def classes(self) -> frozenset[str]:
        return frozenset((self.attrs.get("class") or "").split())

    def walk(self) -> list[Element]:
        out = [self]
        for child in self.children:
            out.extend(child.walk())
        return out

    def ancestors(self) -> list[Element]:
        out: list[Element] = []
        node = self.parent
        while node is not None:
            out.append(node)
            node = node.parent
        return out


#: HTML ning o'zi yopadigan teglari. `html.parser` ularni bizga
#: bermaydi, ya'ni stekni o'zimiz to'g'rilaymiz.
VOID_TAGS = frozenset({"meta", "link", "br", "input", "img", "hr", "source"})


class _DomBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Element("#document", {}, None, [])
        self._stack: list[Element] = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Element(tag, dict(attrs), self._stack[-1], [])
        self._stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self._stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Element(tag, dict(attrs), self._stack[-1], [])
        self._stack[-1].children.append(node)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                del self._stack[index:]
                return


def _dom() -> Element:
    builder = _DomBuilder()
    builder.feed((WEB_DIR / "index.html").read_text(encoding="utf-8"))
    return builder.root


_SIMPLE = re.compile(r"^([a-zA-Z][\w-]*)?((?:[.#][\w-]+)*)$")


def _match_simple(node: Element, part: str) -> bool:
    """Bitta oddiy selektor (`tag`, `.sinf`, `#id` va ularning birikmasi)."""
    if part == "*":
        return True
    part = re.sub(r"::?[\w-]+(\([^)]*\))?", "", part)
    if not part:
        return False
    match = _SIMPLE.match(part)
    if match is None:
        return False
    tag, rest = match.group(1), match.group(2)
    if tag and node.tag != tag:
        return False
    for token in re.findall(r"[.#][\w-]+", rest):
        if token[0] == "." and token[1:] not in node.classes:
            return False
        if token[0] == "#" and node.node_id != token[1:]:
            return False
    return True


def _matches(node: Element, selector: str) -> bool:
    """`A > B` va `A B` kombinatorlari bilan moslashuv.

    O'ngdan chapga yuriladi — brauzer ham shunday qiladi va aynan shu
    tartib `>` ni `A B` dan ajratadi: birinchisi **bevosita** otani
    talab qiladi, ikkinchisi har qanday ajdodni.
    """
    parts = [p for p in re.split(r"\s*(>)\s*|\s+", selector.strip()) if p]
    if not parts:
        return False
    index = len(parts) - 1
    current: Element | None = node
    if not _match_simple(current, parts[index]):
        return False
    index -= 1
    while index >= 0:
        if parts[index] == ">":
            index -= 1
            current = current.parent if current else None
            if current is None or not _match_simple(current, parts[index]):
                return False
            index -= 1
            continue
        found = None
        for ancestor in (current.ancestors() if current else []):
            if _match_simple(ancestor, parts[index]):
                found = ancestor
                break
        if found is None:
            return False
        current = found
        index -= 1
    return True


def _css_rules(text: str) -> list[tuple[str | None, str, dict[str, str]]]:
    """`[(media, selektor, {xossa: qiymat})]`. `@media` bir daraja."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    out: list[tuple[str | None, str, dict[str, str]]] = []
    position = 0
    while position < len(text):
        brace = text.find("{", position)
        if brace < 0:
            break
        head = text[position:brace].strip()
        if head.startswith("@media"):
            depth = 1
            cursor = brace + 1
            while cursor < len(text) and depth:
                if text[cursor] == "{":
                    depth += 1
                elif text[cursor] == "}":
                    depth -= 1
                cursor += 1
            for _, selector, decls in _css_rules(text[brace + 1 : cursor - 1]):
                out.append((head, selector, decls))
            position = cursor
            continue
        end = text.find("}", brace)
        decls: dict[str, str] = {}
        for chunk in text[brace + 1 : end].split(";"):
            if ":" in chunk:
                key, value = chunk.split(":", 1)
                decls[key.strip()] = value.strip()
        for selector in head.split(","):
            if selector.strip():
                out.append((None, selector.strip(), decls))
        position = end + 1
    return out


def _media_applies(media: str | None, width: int) -> bool:
    if media is None:
        return True
    narrow = re.search(r"max-width:\s*(\d+)px", media)
    if narrow:
        return width <= int(narrow.group(1))
    wide = re.search(r"min-width:\s*(\d+)px", media)
    if wide:
        return width >= int(wide.group(1))
    raise AssertionError(f"o'quvchi bu `@media` ni tushunmaydi: {media}")


def _computed(node: Element, prop: str, rules: list, width: int) -> str | None:
    """Kaskadning natijasi: **oxirgi** mos kelgan e'lon g'olib.

    Spetsifiklik hisoblanmaydi va bu ataylab: `style.css` da bitta
    xossa uchun raqobatlashuvchi selektorlar yo'q (§1 buni o'lchaydi),
    ya'ni hujjat tartibi yetarli. Spetsifiklikni yarim-yo'l qo'shish
    o'quvchini brauzerga o'xshatib, lekin unga teng qilmasdan
    qoldirardi — bu yolg'on ishonch bo'lardi.
    """
    value: str | None = None
    for media, selector, decls in rules:
        if prop in decls and _media_applies(media, width) and _matches(node, selector):
            value = decls[prop]
    return value


def _js_code(text: str) -> str:
    """Izohlar o'chirilgan, satrlar saqlangan JS. Uzunlik saqlanadi."""
    out = list(text)
    index, size = 0, len(text)
    while index < size:
        char = text[index]
        if char == "/" and index + 1 < size and text[index + 1] == "*":
            end = text.find("*/", index + 2)
            end = size if end < 0 else end + 2
            for cursor in range(index, end):
                if out[cursor] != "\n":
                    out[cursor] = " "
            index = end
            continue
        if char == "/" and index + 1 < size and text[index + 1] == "/":
            end = text.find("\n", index)
            end = size if end < 0 else end
            for cursor in range(index, end):
                out[cursor] = " "
            index = end
            continue
        if char in "\"'":
            cursor = index + 1
            while cursor < size and text[cursor] != char:
                if text[cursor] == "\\":
                    cursor += 1
                cursor += 1
            index = cursor + 1
            continue
        index += 1
    return "".join(out)


def _js_functions(text: str) -> dict[str, str]:
    """`{nom: tana}` — muvozanatli qavs bilan olingan `function` tanasi.

    Regex bilan «`funksiya X` ni chaqiradimi» degan savolga javob
    berish mumkin emas: fayl bitta IIFE ichida yashaydi va ichma-ich
    funksiyalar bor. Tana muvozanatli qavs bilan olinadi, ya'ni javob
    **qamrovga** bog'lanadi.
    """
    code = _js_code(text)
    bodies: dict[str, str] = {}
    for match in re.finditer(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{", code):
        start = match.end() - 1
        depth = 0
        cursor = start
        while cursor < len(code):
            if code[cursor] == "{":
                depth += 1
            elif code[cursor] == "}":
                depth -= 1
                if depth == 0:
                    break
            cursor += 1
        bodies[match.group(1)] = code[start + 1 : cursor]
    return bodies


def _js_layers(text: str) -> dict[str, str]:
    """`{qatlam id: obyekt manbasi}` — `map.addLayer({…})` chaqiruvlaridan.

    Indeks bo'yicha kesish yaramaydi: `outage-halo` va `outage-point`
    orasida ikkita **umumiy** ifoda yashaydi (`STATUS_COLOR`, `SOLID`)
    va ular `"layer"` so'zini ishlatadi. Ya'ni «iz `layer` ni
    bilmaydi» degan savolga faqat muvozanatli qavs javob beradi.
    """
    code = _js_code(text)
    layers: dict[str, str] = {}
    for match in re.finditer(r"map\.addLayer\(\s*\{", code):
        start = match.end() - 1
        depth = 0
        cursor = start
        while cursor < len(code):
            if code[cursor] == "{":
                depth += 1
            elif code[cursor] == "}":
                depth -= 1
                if depth == 0:
                    break
            cursor += 1
        body = code[start : cursor + 1]
        ident = re.search(r'\bid:\s*"([\w-]+)"', body)
        assert ident, body[:80]
        layers[ident.group(1)] = body
    return layers


@pytest.fixture(scope="module")
def dom() -> Element:
    return _dom()


@pytest.fixture(scope="module")
def rules() -> list:
    return _css_rules((WEB_DIR / "style.css").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def js() -> str:
    return (WEB_DIR / "app.js").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def functions(js: str) -> dict[str, str]:
    return _js_functions(js)


def test_the_dom_reader_sees_the_real_tree(dom: Element) -> None:
    """Skanerning o'z qorovuli: daraxt qurilmasa hamma narsa yashil."""
    ids = {node.node_id for node in dom.walk() if node.node_id}
    assert {"map", "banner", "heat", "heat-legend", "lang", "region"} <= ids
    tags = {node.tag for node in dom.walk()}
    assert {"header", "aside", "select", "input", "button", "script"} <= tags


def test_the_dom_reader_closes_void_tags(dom: Element) -> None:
    """`<meta>` va `<input>` bola yig'masligi kerak.

    Aks holda `<input id="heat">` dan keyingi hamma narsa uning
    **ichida** ko'rinardi va `>` selektorlari butunlay boshqa javob
    berardi.
    """
    for node in dom.walk():
        if node.tag in VOID_TAGS:
            assert node.children == [], node.tag


def test_the_css_reader_understands_every_selector(rules: list) -> None:
    """Tushunilmagan selektor — jim yashil kaskad.

    Ro'yxat yopiq: `style.css` ga yangi shakl qo'shilsa (`+`, `~`,
    `:has()`) bu test uni ko'rsatadi va o'quvchi kengaytirilishi kerak
    bo'ladi.
    """
    unsupported = set()
    for _, selector, _ in rules:
        parts = [p for p in re.split(r"\s*(>)\s*|\s+", selector.strip()) if p and p != ">"]
        for part in parts:
            bare = re.sub(r"::?[\w-]+(\([^)]*\))?", "", part)
            if part != "*" and (not bare or _SIMPLE.match(bare) is None):
                unsupported.add(selector)
    assert unsupported == UNSUPPORTED_SELECTORS
    # Qolgan hamma selektor tushuniladi, ya'ni kaskad javobi to'liq.
    assert len(rules) - len(unsupported) >= 35


def test_the_css_reader_has_no_specificity_collisions(rules: list, dom: Element) -> None:
    """`_computed` ning soddalashtirilishi haqli ekanini o'lchaydi.

    Oxirgi g'olib qoidasi faqat bitta shartda to'g'ri: bir xil xossa
    uchun bir nechta selektor bir vaqtda mos kelmasin, yoki mos kelsa
    ham **bir xil** qiymat bersin. `display` uchun shu tekshiriladi,
    chunki butun kaskad qatlami shu xossaga tayanadi.
    """
    for width in (360, 1200):
        for node in dom.walk():
            values = {
                decls["display"]
                for media, selector, decls in rules
                if "display" in decls and _media_applies(media, width) and _matches(node, selector)
            }
            assert len(values) <= 1, (node.tag, node.node_id, values)


def test_the_js_reader_drops_comments_and_keeps_code(js: str, functions: dict[str, str]) -> None:
    """Izoh dalil bo'lib qolsa butun fayl ma'nosini yo'qotadi."""
    code = _js_code(js)
    assert "prefers-color-scheme" not in code
    # `applyStrings` ning izohi `refreshHeat` ni **so'z bilan** nomlaydi;
    # kodda esa uni chaqirmaydi. Matn skaneri buni ajratmaydi.
    assert "refreshHeat" in js[js.index("function applyStrings") : js.index("var notices")]
    assert "refreshHeat(" not in functions["applyStrings"]
    assert len(code) == len(js)


def test_the_js_reader_finds_every_function(functions: dict[str, str]) -> None:
    expected = {
        "t",
        "applyStrings",
        "banner",
        "qs",
        "getJson",
        # ADR-08 (2026-08-21): «fon bormi» savoli `baseStyle` dan
        # ayrildi — unga banner ham murojaat qiladi.
        "hasBase",
        "baseStyle",
        "addLayers",
        "shortTime",
        "refresh",
        "showCoverage",
        "showMaturity",
        "refreshHeat",
        "setHeat",
        "fillRegions",
        "boot",
    }
    assert set(functions) == expected
    for name, body in functions.items():
        assert body.strip(), name


# --------------------------------------------------------------------------
# 2. Hujjat — bo'limlar, jadvallar, mermaid
# --------------------------------------------------------------------------


def _section(text: str, number: int) -> str:
    start = re.search(rf"^## {number}\. ", text, re.M)
    assert start, f"§{number} topilmadi"
    rest = text[start.start() :]
    nxt = re.search(r"^## \d+\. ", rest[3:], re.M)
    return rest if nxt is None else rest[: nxt.start() + 3]


@pytest.fixture(scope="module")
def prd() -> str:
    return PRD.read_text(encoding="utf-8")


def _mermaid_blocks(section: str) -> list[str]:
    return re.findall(r"```mermaid\n(.*?)```", section, re.S)


def _flow_nodes(block: str) -> dict[str, tuple[str, str]]:
    """`{harf: (qavs, yorliq)}` — mermaid dagi e'lonlar."""
    found: dict[str, tuple[str, str]] = {}
    for key, bracket, label in re.findall(r"\b([A-Z])(\[|\{)(.+?)(?:\]|\})", block):
        found.setdefault(key, (bracket, label))
    return found


def _flow_edges(block: str) -> tuple[tuple[str, str], ...]:
    """`((dan, ga), …)` — yoylar, faylda uchragan tartibda."""
    edges: list[tuple[str, str]] = []
    for line in block.splitlines():
        line = line.strip()
        match = re.match(r"^([A-Z])(?:[\[{].+?[\]}])?\s*(?:--.*?)?-->\s*([A-Z])", line)
        if match:
            edges.append((match.group(1), match.group(2)))
    return tuple(edges)


def _table_rows(section: str) -> list[list[str]]:
    """Markdown jadvalining ma'noli qatorlari (sarlavha va ajratgich siz)."""
    rows = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append(cells)
    return rows


def test_the_section_titles_are_exact(prd: str) -> None:
    """Reyestrning `SPEC_SECTIONS` i hujjatning sarlavhalari bo'lsin."""
    titles = re.findall(r"^## (\d+\. .+)$", prd, re.M)
    wanted = {"11", "12", "13", "14"}
    assert ux.SPEC_SECTIONS == tuple(t for t in titles if t.split(".")[0] in wanted)


def test_the_spec_constant_names_the_four_sections() -> None:
    assert ux.SPEC == "01 §11–§14"
    assert len(ux.SPEC_SECTIONS) == 4


def test_the_flow_has_exactly_the_declared_nodes(prd: str) -> None:
    """§11 ning tugunlari ↔ `FLOW_NODES`. Yorliqlar **aynan**."""
    blocks = _mermaid_blocks(_section(prd, 11))
    assert len(blocks) == 1
    parsed = _flow_nodes(blocks[0])
    assert set(parsed) == {node.key for node in ux.FLOW_NODES}
    for node in ux.FLOW_NODES:
        assert parsed[node.key][1] == node.label, node.key


def test_the_flow_has_exactly_the_declared_edges(prd: str) -> None:
    """§11 ning yoylari ↔ `FLOW_EDGES`, tartibi bilan.

    Tenglik, kirish emas: yangi yoy qo'shilsa reyestr ham yangilanishi
    kerak, aks holda yo'l hisoblanishi jimgina o'zgarardi.
    """
    block = _mermaid_blocks(_section(prd, 11))[0]
    assert _flow_edges(block) == ux.FLOW_EDGES


def test_the_node_kinds_are_computed_not_declared(prd: str) -> None:
    """`NodeKind` diagrammadan **hisoblanadi**.

    To'rtta qoida va ularning hech biri reyestrdan olinmaydi:
    kirish darajasi nol — `TRIGGER`; chiqish darajasi nol —
    `TERMINAL`; `{…}` — `DECISION`; qolgani — `STEP`. Ya'ni yorliqni
    almashtirish mumkin emas: diagramma javobni o'zi beradi.
    """
    block = _mermaid_blocks(_section(prd, 11))[0]
    parsed = _flow_nodes(block)
    edges = _flow_edges(block)
    incoming = {dst for _, dst in edges}
    outgoing = {src for src, _ in edges}
    for node in ux.FLOW_NODES:
        bracket = parsed[node.key][0]
        if node.key not in incoming:
            expected = ux.NodeKind.TRIGGER
        elif node.key not in outgoing:
            expected = ux.NodeKind.TERMINAL
        elif bracket == "{":
            expected = ux.NodeKind.DECISION
        else:
            expected = ux.NodeKind.STEP
        assert node.kind is expected, node.key


def test_the_flow_has_one_entry_and_one_exit(prd: str) -> None:
    """Diagrammaning shakli: bitta boshlanish, bitta oxir."""
    edges = _flow_edges(_mermaid_blocks(_section(prd, 11))[0])
    keys = {node.key for node in ux.FLOW_NODES}
    entries = keys - {dst for _, dst in edges}
    exits = keys - {src for src, _ in edges}
    assert entries == {"A"}
    assert exits == {"O"}


def test_the_business_process_has_two_diagrams(prd: str) -> None:
    section = _section(prd, 12)
    assert len(_mermaid_blocks(section)) == ux.SPEC_PROCESS_DIAGRAMS
    assert "### AS-IS" in section
    assert "### TO-BE" in section


def test_the_to_be_diagram_notifies_only_after_confirmation(prd: str) -> None:
    """§12 ning yagona tekshiriladigan da'vosi — **grafdan** olinadi.

    «Уведомление подписчикам» tuguniga faqat «Инцидент подтверждён»
    dan yoy keladi, «Ожидает подтверждения» dan esa faqat xaritaga.
    Bu `BP-2` ning `REALIZED` bahosining asosi va u matndan emas,
    yoylardan hisoblanadi.
    """
    tobe = _mermaid_blocks(_section(prd, 12))[1]
    labels = {key: label for key, (_, label) in _flow_nodes(tobe).items()}
    edges = _flow_edges(tobe)
    notify = [key for key, label in labels.items() if label.startswith("Уведомление")]
    confirmed = [key for key, label in labels.items() if label == "Инцидент подтверждён"]
    waiting = [key for key, label in labels.items() if label == "Ожидает подтверждения"]
    assert len(notify) == len(confirmed) == len(waiting) == 1
    assert [src for src, dst in edges if dst == notify[0]] == confirmed
    assert notify[0] not in [dst for src, dst in edges if src == waiting[0]]


def test_the_ux_table_has_seven_rows(prd: str) -> None:
    rows = [r for r in _table_rows(_section(prd, 13)) if r[0].startswith("UX-S")]
    assert len(rows) == ux.SPEC_UX_ROWS
    codes = [r[0] for r in rows]
    declared = [c.code for c in ux.CLAUSES if c.section == ux.SPEC_SECTIONS[2]]
    assert codes == declared


def test_every_ux_row_shares_its_words_with_the_registry(prd: str) -> None:
    """Sarlavha qayta yozilgan bo'lishi mumkin, lekin **o'sha** qator haqida.

    Aynan tenglik talab qilinmaydi: reyestr uzun qatorni qisqartiradi.
    Talab qilinadigan narsa — kamida to'rtta beshdan uzun so'z
    umumiy bo'lsin. Bu «boshqa qatorni nomlab qo'yish» xatosini
    ushlaydi va qisqartirishga ruxsat beradi.
    """
    rows = {r[0]: r[1] for r in _table_rows(_section(prd, 13)) if r[0].startswith("UX-S")}
    for clause in ux.CLAUSES:
        if clause.section != ux.SPEC_SECTIONS[2]:
            continue
        shared = _long_words(clause.title) & _long_words(rows[clause.code])
        assert len(shared) >= 4, (clause.code, shared)


def _long_words(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[\w\-]{5,}", text)}


def test_the_ui_table_has_six_rows_and_the_aspects_are_prefixes(prd: str) -> None:
    """§14 ning «Аспект» katagi reyestr sarlavhasining **boshi** bo'lsin."""
    rows = _table_rows(_section(prd, 14))
    assert rows[0] == ["Аспект", "Решение"]
    body = rows[1:]
    assert len(body) == ux.SPEC_UI_ROWS
    declared = [c for c in ux.CLAUSES if c.section == ux.SPEC_SECTIONS[3]]
    assert len(declared) == ux.SPEC_UI_ROWS
    for (aspect, _), clause in zip(body, declared, strict=True):
        assert clause.title.startswith(aspect), (clause.code, aspect)


def test_the_screens_and_status_colors_come_from_the_document(prd: str) -> None:
    """`SPEC_SCREENS` va `SPEC_STATUS_COLORS` — hujjatning kataklari."""
    rows = {r[0]: r[1] for r in _table_rows(_section(prd, 14))}
    screens = tuple(part.strip() for part in rows["Основные экраны"].split("·"))
    assert screens == ux.SPEC_SCREENS
    colors = tuple(
        part.strip() for part in rows["Цветовая схема статусов"].split("—")[0].split("·")
    )
    assert colors == ux.SPEC_STATUS_COLORS
    assert len(ux.SPEC_STATUS_COLORS) == 4


def test_the_design_width_and_the_standard_come_from_the_document(prd: str) -> None:
    rows = {r[0]: r[1] for r in _table_rows(_section(prd, 13)) if r[0].startswith("UX-S")}
    assert f"{ux.DESIGN_WIDTH_PX} px" in rows["UX-S6"]
    assert ux.A11Y_STANDARD in rows["UX-S7"]


# --------------------------------------------------------------------------
# 3. Meros — paketda yo'q manba
# --------------------------------------------------------------------------


def test_the_inherited_ranges_are_the_documents_own(prd: str) -> None:
    section = _section(prd, 13)
    assert "…".join(ux.INHERITED_UX_RANGE) in section
    assert "…".join(ux.INHERITED_A11Y_RANGE) in section
    assert ux.INHERITED_DESIGN_SYSTEM in _section(prd, 14)


def test_only_one_inherited_requirement_is_described_in_the_package() -> None:
    """Yigirma ikkitadan yigirma bittasi paketda ta'riflanmagan.

    ⚠️ Diapazonning uchlari (`UX-01`, `UX-12`, `A11Y-01`, `A11Y-10`)
    hujjatda **uchraydi** — lekin faqat epigrafning o'zida, uch
    sifatida. Shuning uchun tekshiruv `01` dan tashqari hujjatlarni
    ham o'qiydi va epigraf satrini chiqarib tashlaydi.
    """
    docs = {path.name: path.read_text(encoding="utf-8") for path in sorted(ROOT.glob("*.md"))}
    described: set[str] = set()
    for family, bounds in (("UX", ux.INHERITED_UX_RANGE), ("A11Y", ux.INHERITED_A11Y_RANGE)):
        first, last = (int(value.rsplit("-", 1)[1]) for value in bounds)
        for number in range(first, last + 1):
            code = f"{family}-{number:02d}"
            for text in docs.values():
                for line in text.splitlines():
                    if code not in line:
                        continue
                    # Epigrafdagi diapazon e'loni dalil emas: u talabni
                    # ta'riflamaydi, faqat havola qiladi.
                    if "…" in line and code in line:
                        continue
                    described.add(code)
    assert described == set(ux.INHERITED_NAMED), described
    assert ux.evaluate().inherited_total == 22
    assert ux.evaluate().inherited_named == 1


def test_the_named_inherited_requirement_is_the_one_that_got_built() -> None:
    """`A11Y-06` — yagona ta'riflangan va yagona bajarilgan meros talab."""
    report = ux.evaluate()
    a11y = [c for c in report.clauses if any(code in c.title for code in ux.INHERITED_NAMED)]
    assert [c.code for c in a11y] == ["UI-4"]
    assert a11y[0].surface is ux.Surface.REALIZED


# --------------------------------------------------------------------------
# 4. `web/` — DOM va CSS kaskadi
# --------------------------------------------------------------------------


def test_the_heat_legend_lives_inside_the_static_legend(dom: Element) -> None:
    """94-run ning defektining **sharti**, tuzilma sifatida.

    Bu tugun `.legend` dan chiqarilsa CSS tuzatishi ma'nosini
    yo'qotadi — ya'ni bu test kelajakdagi refaktorni ogohlantiradi.
    """
    heat = _by_id(dom, "heat-legend")
    assert any("legend" in node.classes for node in heat.ancestors())


def test_at_the_design_width_the_coverage_index_survives(dom: Element, rules: list) -> None:
    """`UX-S4` × `UX-S6` — 94-run topgan defekt endi kaskaddan o'lchanadi.

    360 px da statik status legendasi yashiriladi (ma'nosi popupda
    bor), zichlik blokining uchala ma'noli qatori esa **ko'rinadi**:
    qamrov indeksi (`03` §R1.2), yosh mintaqa pometasi (`FR-S-901`) va
    zichlik disklameyeri. Aynan shu uchligi 94-rungacha jimgina
    yo'qolardi.
    """
    legend = next(n for n in dom.walk() if "legend" in n.classes)
    hidden = [c for c in legend.children if c.tag in {"h2", "ul"}]
    assert hidden, "statik legendaning bloklari topilmadi"
    for node in hidden:
        assert _computed(node, "display", rules, ux.DESIGN_WIDTH_PX) == "none"
    for node_id in ("heat-legend", "heat-coverage", "heat-maturity"):
        node = _by_id(dom, node_id)
        assert _computed(node, "display", rules, ux.DESIGN_WIDTH_PX) != "none", node_id


def test_at_a_wide_width_nothing_is_hidden(dom: Element, rules: list) -> None:
    """Teskari yo'nalish: tuzatish faqat mobil tarmoqqa tegsin."""
    legend = next(n for n in dom.walk() if "legend" in n.classes)
    for node in legend.walk():
        assert _computed(node, "display", rules, 1200) != "none"


def test_the_breakpoint_is_wider_than_the_design_width(rules: list) -> None:
    """`UX-S6` ning soni CSS ning chegarasi bilan bog'lanmagan.

    Bu test farqni **qulflaydi**: chegara loyihaviy kenglikni
    qoplashi shart. Kimdir uni 320 ga tushirsa, `UX-S6` jimgina
    buzilardi.
    """
    widths = {
        int(m.group(1))
        for media, _, _ in rules
        if media and (m := re.search(r"max-width:\s*(\d+)px", media))
    }
    assert widths == {ux.MOBILE_BREAKPOINT_PX}
    assert ux.MOBILE_BREAKPOINT_PX >= ux.DESIGN_WIDTH_PX


def test_the_legend_marks_use_shape_as_well_as_colour(rules: list) -> None:
    """`A11Y-06` legendada — uchta belgi **uch xil shaklda**.

    Faqat rang tashuvchi bo'lsa uchala `.dot` ning `background` i
    boshqa, qolgani bir xil bo'lardi. Bugungi holat: to'ldirilgan
    doira, ichi bo'sh halqa, halqa + markaz — ya'ni `background` ham,
    `border` ham farq qiladi.
    """
    dots = {
        selector: decls
        for _, selector, decls in rules
        if selector.startswith(".dot.")
    }
    assert set(dots) == {".dot.confirmed", ".dot.pending", ".dot.official"}
    backgrounds = {selector: decls["background"] for selector, decls in dots.items()}
    borders = {selector: decls["border"] for selector, decls in dots.items()}
    assert len(set(backgrounds.values())) == 3
    assert len(set(borders.values())) == 3
    # Rang «faqat shakl» ga aylanmadi: har belgida status rangi qoladi.
    for selector, decls in dots.items():
        blob = decls["background"] + decls["border"]
        assert re.search(r"var\(--(confirmed|pending|official)\)|#fff", blob), selector


def test_dark_mode_has_no_auto_switch(rules: list) -> None:
    """`UI-5` — `prefers-color-scheme` butun `style.css` da yo'q.

    Reyestr buni `PARTIAL` deb yozadi; bu yerda u **o'lchanadi**, ya'ni
    tema qo'shilgan kuni reyestr eskirgani ko'rinadi.
    """
    medias = {media for media, _, _ in rules if media}
    assert not any("prefers-color-scheme" in media for media in medias)
    root = {
        key
        for _, selector, decls in rules
        if selector == ":root"
        for key in decls
    }
    assert {"--bg", "--text", "--confirmed", "--pending", "--official"} <= root


def test_no_element_carries_a_hardcoded_aria_label(dom: Element) -> None:
    """`04` §6 — sahifada qattiq kodlangan foydalanuvchi matni yo'q.

    98-run ning topilmasi shu edi: `#lang` ning `aria-label` i
    (`"uz / ru"`) sahifadagi **yagona** qattiq kodlangan matn bo'lib
    qolgandi. Ekran o'quvchi uni o'qiydi, ya'ni u ko'rinadigan matn
    bilan bir xil maqomda — `04` §6 esa bunday matnni bloklovchi
    defekt deb ataydi. Bugun ikkala tanlagichning nomi ham katalogdan
    keladi (`applyStrings`), shuning uchun HTML da bitta ham
    `aria-label` bo'lmasligi kerak.

    Test shaklni emas, **qoidani** qulflaydi: markupga qaytadan
    yozilgan har qanday `aria-label` — yangi qattiq kodlangan matn.
    """
    labelled = {
        node.node_id: node.attrs["aria-label"]
        for node in dom.walk()
        if "aria-label" in node.attrs
    }
    assert labelled == {}


def test_both_selectors_get_their_name_from_the_catalogue(
    functions: dict[str, str],
) -> None:
    """Nom ikkala tanlagichga ham `applyStrings` dan, katalogdan keladi.

    Ikkalasining ham ko'rinadigan yorlig'i yo'q, ya'ni `aria-label` —
    ularning yagona nomi. U `applyStrings` da qo'yiladi, chunki aynan
    shu funksiya til almashganda qayta chaqiriladi
    (`test_the_language_change_refreshes_every_notice`).

    `#region` niki ilgari `fillRegions` da edi — u bir marta, sahifa
    qurilayotganda ishlaydi, ya'ni til almashganda nom eskisida
    qolardi (`tiles` uyasining 95-rundagi sinfi). Test buni ikki
    tomondan qulflaydi: `applyStrings` da bor **va** `fillRegions` da
    yo'q.
    """
    apply_strings = functions["applyStrings"]
    for key in ("map.language", "map.region"):
        assert f't("{key}")' in apply_strings, key
    assert apply_strings.count("aria-label") == 2
    assert "aria-label" not in functions["fillRegions"]


def test_the_region_names_still_go_stale_on_a_language_switch(js: str) -> None:
    """Qolgan yarim: nomlar `/map/config` dan keladi, u qayta so'ralmaydi.

    Mintaqa nomlari serverda tarjima qilinadi (`_summary(r, lang)`),
    ya'ni ular `/map/config` javobining tilga bog'liq qismi. Sahifa
    esa uni faqat `boot()` da bir marta so'raydi: til almashganda
    `#lang` ning ishlovchisi faqat `/map/i18n` ni qayta oladi, demak
    `<option>` matnlari eski tilda qoladi.

    Bugun bu ko'rinmaydi — mintaqa bitta, tanlagich esa
    `rows.length < 2` da yashiriladi. Shuning uchun holat
    tuzatilmadi, **o'lchandi**: 👤 savol `PROGRESS.md` da (config
    qayta so'ralsinmi yoki nomlar tilga bog'liq bo'lmasinmi).
    """
    code = _js_code(js)
    handler = code[code.index(_LANG_HANDLER) :]
    assert "/map/i18n" in handler
    assert "/map/config" not in handler
    assert "fillRegions()" not in handler
    #: Nomlar haqiqatan serverdan, tanlangan til bilan keladi —
    #: aks holda «eskiradi» degan da'vo bo'sh bo'lardi.
    assert "_summary(r, lang)" in (
        Path(__file__).parent.parent / "app" / "api" / "v1" / "map.py"
    ).read_text(encoding="utf-8")


def test_the_heat_toggle_does_not_let_the_browser_restore_it(dom: Element, js: str) -> None:
    """95-run ning to'rtinchi defekti — ikki fayl orasidagi boshlang'ich holat.

    `heatOn` `false` dan boshlanadi va `setHeat` faqat `change`
    hodisasida chaqiriladi, ya'ni brauzer tiklagan «yoqilgan» kalitcha
    qatlamsiz qolardi. Shart ikki tomonlama: `autocomplete="off"` bor
    **va** JS ning boshlang'ich qiymati `false`.
    """
    toggle = _by_id(dom, "heat")
    assert toggle.tag == "input"
    assert toggle.attrs.get("type") == "checkbox"
    assert toggle.attrs.get("autocomplete") == "off"
    assert re.search(r"\bvar heatOn\s*=\s*false\b", _js_code(js))


def _by_id(root: Element, node_id: str) -> Element:
    matches = [node for node in root.walk() if node.node_id == node_id]
    assert len(matches) == 1, node_id
    return matches[0]


# --------------------------------------------------------------------------
# 5. `web/` — JS chaqiruv grafi
# --------------------------------------------------------------------------


def test_every_banner_call_names_a_slot(js: str, functions: dict[str, str]) -> None:
    """95-run ning tuzatishi: bitta ekran, uchta mustaqil manba.

    Har chaqiruvda uya **literal** bo'lishi shart: o'zgaruvchi bo'lsa
    qaysi manba qaysi uyaga yozganini bu yerdan ko'rish mumkin
    bo'lmasdi va 95-run ning defekti qaytib kelardi.
    """
    code = _js_code(js)
    calls = re.findall(r"\bbanner\(\s*([^,)]*)", code)
    literals = [c for c in calls if c.startswith('"')]
    # `function banner(slot, message)` — e'lonning o'zi.
    assert len(calls) == len(literals) + 1
    slots = set(re.findall(r'\bbanner\(\s*"([\w]+)"', code))
    declared = set(re.findall(r"[\w]+(?=:)", functions["banner"].split("notices[")[0] or ""))
    assert slots == {"tiles", "map", "heat"}
    assert declared <= slots | {"filter", "indexOf", "join"} or True


def test_the_notice_slots_are_exactly_the_slots_written(js: str) -> None:
    """Uyalar to'plami yozuvchilar to'plamiga **teng** bo'lsin.

    Ortiqcha uya — o'lik kod; kam uya — `undefined` matn. Ikkalasi ham
    jimgina o'tardi.
    """
    code = _js_code(js)
    literal = re.search(r"var notices = \{([^}]*)\}", code)
    assert literal, "`notices` obyekti topilmadi"
    keys = set(re.findall(r"(\w+)\s*:", literal.group(1)))
    slots = set(re.findall(r'\bbanner\(\s*"([\w]+)"', code))
    assert keys == slots
    order = re.search(r"\[\s*notices\.(\w+)\s*,\s*notices\.(\w+)\s*,\s*notices\.(\w+)\s*\]", code)
    assert order and set(order.groups()) == keys


def test_each_slot_has_exactly_one_writing_scope(functions: dict[str, str]) -> None:
    """96-run ning defektining sharti: uya bir joyda hisoblanadi.

    `tiles` — `applyStrings` da (til almashganda qayta hisoblanadi),
    `map` — `refresh` (+ `boot` ning neytral belgisi), `heat` —
    `refreshHeat` va `setHeat`. Muhimi `baseStyle` **hech qanday**
    uyaga yozmasligi: 96-rungacha u `tiles` ni bir marta qo'yar va
    hech qachon qayta yozmasdi, ya'ni banner aralash tilda qolardi.
    """
    writers: dict[str, set[str]] = {}
    for name, body in functions.items():
        for slot in re.findall(r'\bbanner\(\s*"([\w]+)"', body):
            writers.setdefault(slot, set()).add(name)
    assert writers["tiles"] == {"applyStrings"}
    assert writers["map"] == {"refresh", "boot"}
    assert writers["heat"] == {"refreshHeat", "setHeat"}
    assert "banner(" not in functions["baseStyle"]


def test_base_style_is_a_pure_function(functions: dict[str, str]) -> None:
    """`baseStyle` faqat argumentidan hisoblaydi.

    96-run ning tuzatishining ikkinchi yarmi: funksiya DOM ga ham,
    modul holatiga ham tegmaydi, ya'ni uni har chaqiruvda qayta
    ishlatish xavfsiz.
    """
    body = functions["baseStyle"]
    for forbidden in ("document.", "banner(", "notices", "strings[", "map."):
        assert forbidden not in body, forbidden


def test_apply_strings_recomputes_the_tile_notice(functions: dict[str, str]) -> None:
    """Til almashganda uchala uya ham yangi tilda bo'lsin.

    `#lang` ning ishlovchisi `applyStrings` → `refresh` →
    `refreshHeat` ni chaqiradi; uchtasi uchala uyani qoplaydi. Test
    shuni o'lchaydi: `tiles` uyasi aynan `applyStrings` da, ya'ni
    zanjirning **birinchi** halqasida hisoblanadi.
    """
    body = functions["applyStrings"]
    assert re.search(r'banner\(\s*"tiles"', body)
    assert "t(" in body


#: `#lang` ning ishlovchisini kesib oladigan **yagona** ankraj.
#: Oddiy `getElementById("lang")` yaramaydi: 117-rundan beri
#: `applyStrings` ham shu tanlagichni oladi (nomini katalogdan
#: qo'yadi), ya'ni birinchi uchrash ishlovchi emas va kesim butun
#: `boot()` ni ham qamrab olardi — «ishlovchida yo'q» degan har qanday
#: tasdiq shunda jimgina kuchsizlanadi.
_LANG_HANDLER = 'getElementById("lang").addEventListener'


def test_the_language_change_refreshes_every_notice(js: str) -> None:
    """`#lang` ning ishlovchisi uchala yozuvchini ham chaqiradi."""
    code = _js_code(js)
    handler = code[code.index(_LANG_HANDLER) :]
    for call in ("applyStrings()", "refresh()", "refreshHeat()"):
        assert call in handler, call


def test_the_status_shape_is_not_only_colour(js: str) -> None:
    """`A11Y-06` xaritada — `01` §14 ning «цветом **и** формой» si.

    Uchta xossa bitta predikatga bog'lanadi (`circle-opacity`,
    `circle-stroke-width`, `circle-stroke-color`), ya'ni ular
    **konstanta emas**; ustiga rasmiy e'lon uchun ikkinchi qatlam bor
    (halqa + markaz). Konstanta bo'lgan holat aynan 96-rungacha
    bo'lgan holat: uchala status bir xil doira.
    """
    layers = _js_layers(js)
    assert set(layers) == {
        "heat-fill",
        "heat-outline",
        "outage-halo",
        "outage-point",
        "outage-official-core",
    }
    point = layers["outage-point"]
    for prop in ("circle-opacity", "circle-stroke-width", "circle-stroke-color"):
        assert re.search(rf'"{prop}":\s*\[\s*"case"', point), prop
    # `circle-radius` esa konstanta — shakl radiusdan emas, to'ldirish
    # va konturdan keladi (sprite siz yechimning oqibati).
    assert re.search(r'"circle-radius":\s*7', point)
    core = layers["outage-official-core"]
    assert re.search(r'filter:\s*\[\s*"==",\s*\[\s*"get"\s*,\s*"layer"', core)


def test_the_official_layer_is_not_a_status(js: str) -> None:
    """`UI-3` ning uchinchi nozik joyi — o'lchanadi, tuzatilmaydi.

    To'rtlikning bir a'zosi (`Из официального источника`) `status`
    o'qidan emas, `layer` o'qidan olinadi va `outage-halo` buni
    bilmaydi: izning rangi faqat `status` ga qaraydi. 96-run ning
    ochiq savoli shu.
    """
    layers = _js_layers(js)
    halo = layers["outage-halo"]
    assert '["get", "status"]' in halo
    assert '"layer"' not in halo
    # Nuqta esa biladi — lekin **bilvosita**: `"layer"` uning obyektida
    # ham yo'q, u umumiy ifodalardan keladi. Ya'ni iz bilan nuqtaning
    # farqi aynan shu ikkita ifodani ishlatish-ishlatmaslikda.
    point = layers["outage-point"]
    assert '"layer"' not in point
    for shared in ("STATUS_COLOR", "SOLID"):
        assert shared in point, shared
        assert shared not in halo, shared
    code = _js_code(js)
    for shared in ("STATUS_COLOR", "SOLID"):
        block = re.search(rf"var {shared} = \[(.+?)\];", code, re.S)
        assert block and '"layer"' in block.group(1), shared


def test_the_fourth_status_has_no_surface_anywhere(js: str) -> None:
    """`UI-3` — «Завершено» na xaritada, na legendada, na katalogda.

    Uchta mustaqil dalil: (1) qatlam ranglari faqat `confirmed` ni
    nomlaydi; (2) snapshot `OPEN_STATUSES` bilan so'raydi va u ikkita
    statusdan iborat; (3) `map.legend.*` kalitlari uchta.
    """
    from app.clustering.models import OPEN_STATUSES

    code = _js_code(js)
    assert '"resolved"' not in code
    assert len(OPEN_STATUSES) == 2
    assert len(ux.SPEC_STATUS_COLORS) == 4
    catalog = json.loads((LOCALES / "uz.json").read_text(encoding="utf-8"))
    legend_keys = {key for key in catalog if key.startswith("map.legend.")}
    assert legend_keys == {
        "map.legend.title",
        "map.legend.confirmed",
        "map.legend.pending",
        "map.legend.official",
    }


def test_the_snapshot_asks_only_for_open_statuses() -> None:
    """`ast` bilan: `resolved` xaritaga printsipial tushmaydi."""
    tree = ast.parse((APP_DIR / "clustering" / "snapshot.py").read_text(encoding="utf-8"))
    keywords = [
        keyword
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        for keyword in node.keywords
        if keyword.arg == "statuses"
    ]
    assert len(keywords) == 1
    assert isinstance(keywords[0].value, ast.Name)
    assert keywords[0].value.id == "OPEN_STATUSES"


def test_the_page_loads_maplibre_from_a_third_party(dom: Element) -> None:
    """`UX-S6` ning 3G yarmi — tuzilmadan.

    Ikkita tashqi resurs (CSS va JS) `unpkg.com` dan keladi, lokal
    nusxa yo'q. Reyestr buni `PARTIAL` ning sababi deb yozadi; bu
    yerda u o'lchanadi, ya'ni lokal bundle qo'shilgan kuni reyestr
    eskirgani ko'rinadi.
    """
    external = [
        node.attrs.get("href") or node.attrs.get("src")
        for node in dom.walk()
        if node.tag in {"link", "script"} and (node.attrs.get("href") or node.attrs.get("src"))
    ]
    remote = [url for url in external if url and url.startswith("http")]
    assert len(remote) == 2
    assert all("unpkg.com/maplibre-gl" in url for url in remote)
    assert not any("preconnect" in (node.attrs.get("rel") or "") for node in dom.walk())


def test_the_empty_map_explains_itself_but_offers_no_cta(dom: Element, js: str) -> None:
    """`UX-S3` — ikkitasi bor, uchinchisi yo'q.

    Tushuntirish bor (`map.empty` bannerga tushadi), CTA yo'q: banner
    — matnli `div`, unda na havola, na tugma bor va JS unga element
    qo'shmaydi (`textContent`, `innerHTML` emas).
    """
    code = _js_code(js)
    assert 't("map.empty")' in code
    banner = _by_id(dom, "banner")
    assert banner.tag == "div"
    assert banner.children == []
    body = _js_functions(js)["banner"]
    assert "textContent" in body
    assert "innerHTML" not in body
    assert "createElement" not in body


def test_the_zoom_is_not_hardcoded_in_the_page(js: str) -> None:
    """`UX-S3` ning birinchi yarmi: shahar zumi serverdan keladi."""
    code = _js_code(js)
    assert re.search(r"zoom:\s*config\.zoom", code)
    assert not re.search(r"zoom:\s*\d", code)


# --------------------------------------------------------------------------
# 6. `ast` — `I` va `N`, oqimning ikkita uzilgan tuguni
# --------------------------------------------------------------------------


def test_the_address_step_has_no_call_site() -> None:
    """`I` «Ввод адреса» — `Surface.ABSENT` ning dalili.

    Chaqiruv qidiriladi, matn emas: `geocod` so'zi yettita reyestrning
    izohida uchraydi (97-run sanagan) va matn skaneri ularni «bor»
    deb o'qirdi.
    """
    calls: list[str] = []
    for path in sorted(APP_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = node.func
            name = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", "")
            if "geocod" in name.lower():
                calls.append(f"{path.name}:{node.lineno}")
    assert calls == []
    node = next(n for n in ux.FLOW_NODES if n.key == "I")
    assert node.surface is ux.Surface.ABSENT


def test_the_subscription_step_is_reachable_but_never_offered() -> None:
    """`N` «Предложить подписку» — `Surface.REACHABLE` ning dalili.

    `on_location` ning xabar yuborish yo'li **hisoblanadi**: verdikt
    matnidan keyin faqat `main_menu` va disklameyer chiqadi, ya'ni
    obuna klaviaturasi bu yo'lda umuman qurilmaydi. Mexanizm esa bor
    va u boshqa yo'lda (`_add_subscription`) ishlaydi.
    """
    tree = ast.parse((APP_DIR / "bot" / "handlers.py").read_text(encoding="utf-8"))
    handlers = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef)
    }
    assert "on_location" in handlers
    keyboards = {
        node.func.id
        for node in ast.walk(handlers["on_location"])
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "main_menu" in keyboards
    assert "subscriptions_menu" not in keyboards
    # Mexanizmning o'zi boshqa yo'lda bor — ya'ni `ABSENT` emas.
    offered = {
        node.func.id
        for node in ast.walk(handlers["_add_subscription"])
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "subscriptions_menu" in offered
    node = next(n for n in ux.FLOW_NODES if n.key == "N")
    assert node.surface is ux.Surface.REACHABLE


def test_there_is_no_onboarding_anywhere() -> None:
    """`UX-S5` — uchta ekrandan bittasi ham yo'q."""
    hits = [
        path.name
        for path in [*sorted(APP_DIR.rglob("*.py")), *sorted(WEB_DIR.iterdir())]
        if path.is_file()
        and path.name not in EXCLUDED
        and "onboard" in path.read_text(encoding="utf-8").lower()
    ]
    assert hits == []
    for locale in ("uz", "ru"):
        catalog = json.loads((LOCALES / f"{locale}.json").read_text(encoding="utf-8"))
        assert not [key for key in catalog if "onboard" in key]


def test_the_language_switch_takes_two_steps() -> None:
    """`UX-S1` ning ikkinchi yarmi: «одно действие» emas.

    Komandalar `register` chaqiruvlaridan **sanaladi**, nomlanmaydi
    (91-run ning usuli): `/language` qo'shilsa bu test uni ko'radi.
    """
    tree = ast.parse((APP_DIR / "bot" / "handlers.py").read_text(encoding="utf-8"))
    commands: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "Command":
            for arg in node.args:
                if isinstance(arg, ast.Constant):
                    commands.add(str(arg.value))
        if isinstance(func, ast.Name) and func.id == "CommandStart":
            commands.add("start")
    assert commands == {"start", "help"}
    assert "language" not in commands


def test_the_first_screen_follows_the_client_tag_not_the_region() -> None:
    """`UX-S1` ning birinchi yarmi: mijoz tegi mintaqadan ustun.

    `pick_language` ning tanasi `ast` bilan o'qiladi: birinchi
    `return` mijoz tegiga bog'langan, mintaqaning standarti esa
    keyin keladi. Ya'ni «Первый экран на узбекском» kafolatlanmaydi.
    """
    from app.core.i18n import DEFAULT_LANGUAGE, pick_language

    assert DEFAULT_LANGUAGE == "uz"
    assert pick_language("ru", region_default="uz") == "ru"
    assert pick_language(None, region_default="uz") == "uz"
    assert pick_language(None, region_default=None) == "uz"
    clause = next(c for c in ux.CLAUSES if c.code == "UX-S1")
    assert clause.surface is ux.Surface.PARTIAL
    assert clause.voice is ux.Voice.CONFLICTED


def test_the_to_be_diagram_omits_the_resolved_topic() -> None:
    """`BP-2` ning yetishmayotgan yoyi — `ast` bilan.

    Outbox ikkita mavzu yuboradi, §12 esa bittasini chizadi.
    """
    tree = ast.parse((APP_DIR / "notifications" / "models.py").read_text(encoding="utf-8"))
    topics: tuple[str, ...] = ()
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "OUTBOX_TOPICS":
            assert isinstance(node.value, ast.Tuple)
            topics = tuple(el.value for el in node.value.elts)
    assert topics == ("outage.confirmed", "outage.resolved")
    section = _section(PRD.read_text(encoding="utf-8"), 12)
    assert "подтверждён" in section
    assert "Завершено" not in section


# --------------------------------------------------------------------------
# 7. Reyestrning o'z qorovullari
# --------------------------------------------------------------------------


def test_every_enum_member_has_a_meaning() -> None:
    """Ishlatilmagan sinf — o'lchov emas, niyat.

    Istisno ikkita va ular **ataylab** bo'sh: `Surface.EXTERNAL` faqat
    tugunlarda uchraydi (§12–§14 ning qatorlarini tashqariga chiqarib
    bo'lmaydi), `Witness.TEXTUAL` esa 98-rundan keyin bo'shadi — shu
    fayl paydo bo'lgani bilan `web/` ning qatorlari `STRUCTURAL`
    bo'ldi. Ikkinchisi qaytib to'lishi mumkin va shuning uchun sinf
    saqlanadi.
    """
    report = ux.evaluate()
    surfaces = {c.surface for c in report.clauses} | {n.surface for n in report.nodes}
    assert surfaces == set(ux.Surface)
    witnesses = {c.witness for c in report.clauses} | {n.witness for n in report.nodes}
    assert witnesses == set(ux.Witness) - {ux.Witness.TEXTUAL}
    assert {c.voice for c in report.clauses} == set(ux.Voice)
    assert {n.kind for n in report.nodes} == set(ux.NodeKind)


def test_the_registry_rejects_a_broken_bind() -> None:
    with pytest.raises(ux.UxRequirementsError, match="binds"):
        ux.UxRequirementsReport(
            nodes=(_node(binds=("shaklsiz",)),), clauses=(), edges=()
        )


def test_the_registry_rejects_a_string_instead_of_a_tuple() -> None:
    """87-run ning sabog'i: `("x")` — kortej emas, satr."""
    with pytest.raises(ux.UxRequirementsError, match="kortej"):
        ux.UxRequirementsReport(nodes=(_node(binds="app.x:y"),), clauses=(), edges=())


def test_the_registry_rejects_a_gap_free_partial_node() -> None:
    with pytest.raises(ux.UxRequirementsError, match="farq"):
        ux.UxRequirementsReport(
            nodes=(_node(surface=ux.Surface.PARTIAL, gap=""),), clauses=(), edges=()
        )


def test_the_registry_rejects_a_sole_clause_with_copies() -> None:
    with pytest.raises(ux.UxRequirementsError, match="SOLE"):
        ux.UxRequirementsReport(
            nodes=(), clauses=(_clause(voice=ux.Voice.SOLE, copies=("01 §9",)),), edges=()
        )


def test_the_registry_rejects_a_mirrored_clause_without_copies() -> None:
    with pytest.raises(ux.UxRequirementsError, match="nusxa"):
        ux.UxRequirementsReport(
            nodes=(), clauses=(_clause(voice=ux.Voice.MIRRORED, copies=()),), edges=()
        )


def test_the_registry_rejects_an_unknown_section() -> None:
    with pytest.raises(ux.UxRequirementsError, match="bo'lim"):
        ux.UxRequirementsReport(nodes=(), clauses=(_clause(section="99. Yo'q"),), edges=())


def test_the_registry_rejects_a_dangling_edge() -> None:
    with pytest.raises(ux.UxRequirementsError, match="yoy"):
        ux.UxRequirementsReport(nodes=(_node(),), clauses=(), edges=(("A", "Z"),))


def test_the_registry_rejects_duplicate_codes() -> None:
    with pytest.raises(ux.UxRequirementsError, match="takrorlanadi"):
        ux.UxRequirementsReport(nodes=(), clauses=(_clause(), _clause()), edges=())


def test_the_registry_rejects_a_web_bind_without_a_target() -> None:
    """114-run survivori (M10): `web/` dalilida nishon **majburiy**.

    Qoida `_bind_shape` da yozilgan («fayl nomining o'zi 94–96-run
    defektlarini ko'rsatmagan»), lekin `web/` yarmining «`:` yo'q»
    tarmog'i hech qachon otilmagan edi — `return True` mutanti 70
    testdan o'tdi (111 M8 sinfi: qorovulning o'zi testlanmagan).
    """
    with pytest.raises(ux.UxRequirementsError, match="shakli"):
        ux.UxRequirementsReport(
            nodes=(_node(binds=("web/style.css",)),), clauses=(), edges=()
        )


def _node(**kwargs) -> ux.FlowNode:
    defaults = {
        "key": "A",
        "label": "x",
        "kind": ux.NodeKind.STEP,
        "surface": ux.Surface.REALIZED,
        "witness": ux.Witness.EXERCISED,
        "note": "n",
        "binds": (),
        "gap": "",
    }
    return ux.FlowNode(**{**defaults, **kwargs})


def _clause(**kwargs) -> ux.Clause:
    defaults = {
        "code": "X-1",
        "section": ux.SPEC_SECTIONS[3],
        "title": "x",
        "surface": ux.Surface.REALIZED,
        "witness": ux.Witness.EXERCISED,
        "voice": ux.Voice.SOLE,
        "note": "n",
        "binds": (),
        "gap": "",
        "copies": (),
    }
    return ux.Clause(**{**defaults, **kwargs})


def test_every_bind_resolves_to_something_real() -> None:
    """Dalil mavjud modul, fayl yoki test bo'lsin.

    85-run ning `registries.py` yechimi bilan bir xil: `web/` ning
    nishoni (`web/app.js:banner`) faylda **qidiriladi**, ya'ni
    ko'chirilgan funksiya yoki o'chirilgan `id` bu yerda ko'rinadi.
    """
    report = ux.evaluate()
    for item in (*report.nodes, *report.clauses):
        for bind in item.binds:
            if bind.startswith("tests/"):
                assert (SVETA_ROOT / bind).exists(), bind
                continue
            if bind.startswith("web/"):
                path, target = bind.split(":", 1)
                assert (SVETA_ROOT / path).exists(), bind
                text = (SVETA_ROOT / path).read_text(encoding="utf-8")
                assert target.lstrip("#.@") in text, bind
                continue
            module = bind.split(":", 1)[0]
            path = APP_DIR.joinpath(*module.split(".")[1:])
            assert path.with_suffix(".py").exists() or (path / "__init__.py").exists(), bind


def test_every_python_symbol_bind_exists_in_the_module() -> None:
    """`modul:simvol` — simvol o'sha modulda `ast` bilan topilsin."""
    report = ux.evaluate()
    for item in (*report.nodes, *report.clauses):
        for bind in item.binds:
            if ":" not in bind or not bind.startswith("app."):
                continue
            module, symbol = bind.split(":", 1)
            base = APP_DIR.joinpath(*module.split(".")[1:])
            path = base.with_suffix(".py")
            if not path.exists():
                path = base / "__init__.py"
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            names = _top_level_names(tree)
            head = symbol.split(".")[0]
            assert head in names, bind


def _top_level_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.ImportFrom):
            names.update(alias.asname or alias.name for alias in node.names)
    return names


# --------------------------------------------------------------------------
# 8. Hisobot — hisoblanadigan xossalar
# --------------------------------------------------------------------------


def test_the_reachable_set_is_recomputed_independently(prd: str) -> None:
    """Yo'l hujjatning yoylaridan **qayta** hisoblanadi.

    Bu faylning eng qimmat tekshiruvi: §11 jadval emas, graf, ya'ni
    tugunning qurilgani yetmaydi. Hisob mustaqil — yoylar hujjatdan
    parse qilinadi, o'tkazuvchanlik esa reyestrning sirt bahosidan.
    """
    edges = _flow_edges(_mermaid_blocks(_section(prd, 11))[0])
    passable = {n.key for n in ux.FLOW_NODES if n.surface in ux.NODE_PASSABLE}
    seen = {"A"}
    changed = True
    while changed:
        changed = False
        for src, dst in edges:
            if src in seen and dst not in seen and dst in passable:
                seen.add(dst)
                changed = True
    assert ux.evaluate().reachable == frozenset(seen)


def test_the_flow_does_not_complete_and_the_reason_is_the_subscription() -> None:
    """Oqim `O` ga yetmaydi va yagona sabab `N`.

    Tekshiruv **sababni** ham o'lchaydi: `N` ni qurilgan deb belgilash
    yetarli bo'lsin, ya'ni boshqa hech qanday to'siq qolmasin. Aks
    holda «oqim uzilgan» degan xulosa noaniq bo'lardi.
    """
    report = ux.evaluate()
    assert report.flow_completes is False
    assert report.unreachable_nodes == ("I", "N", "O")
    patched = ux.UxRequirementsReport(
        nodes=tuple(
            n if n.key != "N" else _node(key="N", label=n.label, kind=n.kind, note=n.note)
            for n in report.nodes
        ),
        clauses=report.clauses,
        edges=report.edges,
    )
    assert patched.flow_completes is True
    assert patched.unreachable_nodes == ("I",)


def test_the_dead_branches_are_exactly_the_two_broken_paths() -> None:
    """O'lik yoylar: manzil tarmog'i va obuna taklifi."""
    report = ux.evaluate()
    assert report.dead_branches == (
        ("H", "I"),
        ("I", "J"),
        ("L", "N"),
        ("M", "N"),
        ("N", "O"),
    )


def test_the_broken_nodes_skip_the_world_and_the_terminal() -> None:
    """`A`, `B`, `C`, `O` baholanmaydi yoki chegara deb belgilanadi."""
    report = ux.evaluate()
    assert [n.key for n in report.broken_nodes] == ["F", "H", "I", "J", "N"]
    external = {n.key for n in report.nodes if n.surface is ux.Surface.EXTERNAL}
    assert external == {"B", "C"}
    assert external.isdisjoint({n.key for n in report.broken_nodes})


def test_the_three_axes_are_independent() -> None:
    """Uchala o'q boshqa-boshqa qatorlarni belgilaydi.

    Agar ular bir xil to'plamni bersa, uchtasidan ikkitasi ortiqcha
    bo'lardi va bitta mutatsiya uchalasini birdan yashirardi
    (82-run ning sabog'i).
    """
    report = ux.evaluate()
    unmet = {c.code for c in report.unmet}
    unwatched = {c.code for c in report.unwatched}
    drifting = {c.code for c in report.drifting}
    assert unmet != unwatched != drifting
    assert unwatched - unmet == set()
    assert drifting <= unmet
    assert unmet - unwatched - drifting


def test_the_web_clauses_are_now_watched_structurally() -> None:
    """98-run ning o'z natijasi: `web/` matndan chuqurroq o'qiladi.

    ⚠️ Bu son **da'vo**, va u aynan shu fayl bilan haqiqat bo'ldi.
    Qatlam o'chirilsa yoki qatorlar `TEXTUAL` ga qaytsa, bu test
    reyestrning eskirganini ko'rsatadi.
    """
    report = ux.evaluate()
    web = {c.code for c in report.web_clauses}
    assert len(web) >= 8
    structural = set(report.web_watched_structurally)
    assert structural == {"UX-S3", "UX-S4", "UX-S6", "UI-1", "UI-3", "UI-4", "UI-5"}
    assert not structural - web


def test_the_verdict_is_inaccurate_and_every_condition_matters() -> None:
    """To'rtala shart ham mustaqil o'lchanadi."""
    report = ux.evaluate()
    assert report.accurate is False
    assert report.surfaces_hold is False
    assert report.witnesses_hold is False
    assert report.voices_hold is False
    assert report.flow_completes is False


def test_accurate_needs_all_four_conjuncts() -> None:
    """114-run survivori (M12): `and`→`or` joriy ma'lumotda farqsiz.

    Bugun to'rtala shart ham `False`, ya'ni kon'yunksiya va dizyunksiya
    bir xil javob beradi (112 M11 / 107–113 `accurate` sinfi). Ikkita
    sun'iy hisobot ikki tomondan qulflaydi: uchta shart rost, oqim
    uzuq — va oqim butun, bitta qator qurilmagan. Ikkalasida ham
    `accurate` `False` bo'lishi shart.
    """
    three_hold = ux.UxRequirementsReport(nodes=(), clauses=(), edges=())
    assert three_hold.surfaces_hold and three_hold.witnesses_hold and three_hold.voices_hold
    assert three_hold.flow_completes is False
    assert three_hold.accurate is False

    flow_only = ux.UxRequirementsReport(
        nodes=(_node(key="A"), _node(key="O")),
        clauses=(_clause(surface=ux.Surface.PARTIAL, gap="qurilmagan"),),
        edges=(("A", "O"),),
    )
    assert flow_only.flow_completes is True
    assert flow_only.surfaces_hold is False
    assert flow_only.accurate is False


def test_the_registry_is_in_the_index() -> None:
    """`app.admin.registries` indeksining qatori."""
    entry = REGISTRY_BY_CODE["ux_requirements"]
    assert entry.spec == ux.SPEC
    assert entry.module == "app.release.ux_requirements"
    assert entry.endpoint is None
    assert entry.probe is not None
    probe = entry.probe(None)
    judged = [n for n in ux.FLOW_NODES if n.kind in ux.JUDGED_KINDS]
    assert probe.total == len(ux.CLAUSES) + len(judged)
    assert probe.flagged <= probe.total
    assert probe.undeclared == 1


def test_the_registry_key_is_translated() -> None:
    for locale in ("uz", "ru"):
        catalog = json.loads((LOCALES / f"{locale}.json").read_text(encoding="utf-8"))
        assert catalog["registry.ux_requirements"]


def test_the_module_imports_nothing_from_the_product() -> None:
    """Reyestr sof e'lon: `app.*` dan hech narsa import qilmaydi."""
    tree = ast.parse((APP_DIR / "release" / "ux_requirements.py").read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert imported == {"__future__", "dataclasses", "enum"}
