"""`05` §7.2 endpoint jadvali ↔ OpenAPI yo'llari kontrakti — bazasiz.

**Nima uchun bu fayl kerak.** `05` §7.3 (nima chiqmaydi) o'nlab joyda
qulflangan: `geom_exact`, `tg_id`, `user_id`, uchta xabar to'sig'i, besh
daqiqagacha yaxlitlash — hammasi testda. §7.2 esa, ya'ni **qaysi
endpointlar umuman bo'lishi kerak**, hech qayerda tekshirilmaydi.
Jadvalga havola faqat ikkita docstringda bor
(`test_geo_api_db.py`, `test_stats_api_db.py`) va **ikkalasi ham
`requires_db`** — o'n to'qqiz rundan beri sandboxda umuman ishlamaydi.

Shundan to'rtta yo'nalish jim qoladi:

1. hujjatdagi endpoint **o'chsa yoki qayta nomlansa** — hech narsa
   yiqilmaydi, mahsulot va'dasi esa yo'qoladi;
2. hujjatga **oltinchi qator** qo'shilsa — u hech qachon yozilmasligi
   mumkin;
3. `settings.api_prefix` o'zgarsa — hujjatdagi `/api/v1` eskirib qoladi,
   lekin ikkalasini hech narsa bog'lamaydi (`API_PREFIX` sozlama bo'lib
   qolgani 44-sessiyaning ochiq savoli);
4. ommaviy sathga **hujjatda yo'q** endpoint qo'shilsa — hech kim uni
   oqlashga majbur emas.

Shuning uchun jadval hujjatdan o'qiladi (45-sessiyaning `_SPEC_ROW` va
47-sessiyaning `BEYOND_SPEC` naqshlari), ortiqchasi esa **ochiq ro'yxat**
bilan oqlanadi.

**Bu fayl javob maydonlariga tegmaydi** — `StatsOut`, `HeatCollection`,
`MahallaOut`, `DistrictOut` maydonlari va butun `§7.3` maxfiylik ro'yxati
`tests/test_openapi_contract.py` da allaqachon qulflangan. Bu yerda faqat
**sath**: qaysi yo'l bor, qaysi metod bilan va u kimga ochiq.

Hammasi bazasiz: `app.openapi()` bazaga tegmaydi, hujjat esa oddiy matn.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.core.config import settings

SVETA_ROOT = Path(__file__).resolve().parents[1]
#: `05_Technical_Design.md` repo ildizida, `sveta/` ning yonida.
DESIGN_DOC = SVETA_ROOT.parent / "05_Technical_Design.md"

#: `05` §7.2 jadvalining qatori: `| `GET /api/v1/map` | izoh |`.
#: Sarlavha (`| Endpoint | Izoh |`) va ajratgich (`|---|---|`) backtick siz,
#: ya'ni mos kelmaydi. Izoh ustuni **bo'sh bo'lishi mumkin** — `/health`
#: qatori aynan shunday, shuning uchun bu yerda «har qator o'zini
#: izohlaydi» degan tekshiruv yo'q (47-sessiyadagidan farqi shu).
_SPEC_ROW = re.compile(r"^\|\s*`([A-Z]+)\s+(/\S*)`\s*\|(.*)\|\s*$")

#: Jadval bo'shab qolmasligining pastki chegarasi. Bugun 5 ta; chegara
#: ataylab pastroq emas, aynan 5 — §7.2 «asosiy endpointlar» ro'yxati,
#: u epiclar bilan o'smaydi (o'sadigan hammasi `BEYOND_SPEC` ga tushadi).
SPEC_ROWS = 5

#: Ommaviy sathda bor, `05` §7.2 jadvalida **yo'q** yo'llar. Har biri sabab
#: bilan; sababsiz qo'shilgan endpoint testni yiqitadi.
BEYOND_SPEC: dict[str, str] = {
    "/map/config": (
        "statik frontend uchun sahifa sozlamalari (markaz, zum, tayl manbasi) — "
        "ma'lumot emas, ko'rinish; §7.2 ma'lumot endpointlarini sanaydi"
    ),
    "/map/i18n": (
        "veb-xarita matnlari bitta katalogdan kelishi uchun (UZ/RU) — "
        "qattiq kodlangan matn bloklovchi defekt"
    ),
    "/heatmap": "xabar zichligi H3 katakchalari bo'yicha, `05` §7.3 to'sig'i bilan",
    "/geo/mahallas": (
        "mahalla chegaralari spravochnigi — `01` §16 mahalla qamrovi shu "
        "ro'yxatga tayanadi"
    ),
    "/regions": (
        "faol mintaqalar ro'yxati — `region` parametrini tanlash mumkin "
        "bo'lishi uchun kirish nuqtasi"
    ),
    "/stats.csv": "`/stats` bilan bir xil ma'lumot, CSV eksporti (yuklab olish uchun)",
}

#: `05` §7.2 jadvalidan keyingi jumla: «`region_id` barcha geo-so'rovlarda
#: majburiy (PRD §16)». Ro'yxat **normallashtirilgan** yo'l bilan, prefikssiz.
#: `/outages/{}` bitta hodisani `id` bo'yicha oladi, `/health` esa geo emas —
#: shuning uchun ikkalasi bu ro'yxatda yo'q.
GEO_ENDPOINTS = frozenset({"/map", "/stats", "/geo/districts"})

#: So'rov mintaqani nomlaydigan parametr. `app/api/v1/map.py` izohi:
#: parametr **majburiy emas**, bo'sh qiymat `DEFAULT_REGION_CODE` ga
#: aylanadi, lekin so'rov baribir **bitta** mintaqa bo'yicha bajariladi.
#: Test aynan shu qarorni qulflaydi — parametrning **borligini**, uning
#: `required` bo'lishini emas.
REGION_PARAM = "region"

#: `05` §7.3 admin sathini umuman sanamaydi (u E8 ning ishi), shuning uchun
#: teskari yo'nalish faqat ommaviy tegi bo'lgan operatsiyalarni ko'radi.
ADMIN_TAG = "admin"

#: `_tail` uchun; alohida nom — kesim ifodasi sodda qolsin.
_PREFIX_LEN = len(settings.api_prefix)


def _section() -> str:
    """`05` §7.2 ning matni.

    Chegara — keyingi sarlavha, **darajasidan qat'i nazar**: §7.2 dan keyin
    `### 7.3` keladi va u `\\n## ` naqshiga tushmaydi (uchinchi belgi `#`,
    probel emas). Faqat `\\n## ` ga tayanish bo'limni §8 gacha cho'zib,
    §7.3 ni ham ichiga olardi.
    """
    assert DESIGN_DOC.exists(), f"`05_Technical_Design.md` topilmadi: {DESIGN_DOC}"
    text = DESIGN_DOC.read_text(encoding="utf-8")
    heading = "### 7.2 Asosiy endpointlar"
    assert heading in text, f"`05` da «{heading}» sarlavhasi yo'q"
    start = text.index(heading)
    after = start + len(heading)
    ends = [pos for pos in (text.find("\n### ", after), text.find("\n## ", after)) if pos != -1]
    if not ends:
        return text[start:]
    return text[start:min(ends)]


def _spec_endpoints() -> dict[str, str]:
    """`05` §7.2 jadvali: to'liq yo'l → HTTP metodi. Tartib saqlanadi."""
    result: dict[str, str] = {}
    for line in _section().splitlines():
        match = _SPEC_ROW.match(line)
        if not match:
            continue
        method, path = match.group(1), match.group(2)
        assert path not in result, f"`05` §7.2 da takrorlangan yo'l: {path}"
        result[path] = method
    return result


def _normalize(path: str) -> str:
    """`{id}` va `{outage_id}` — bitta yo'l.

    Hujjat parametrni `{id}` deb yozadi, kod esa `{outage_id}`. Nomni
    tenglashtirishga urinish hujjatni kodga moslashtirish bo'lardi;
    kontraktning ma'nosi esa **shakl** — nechta segment va qaysi biri
    o'zgaruvchi.
    """
    return re.sub(r"\{[^}]*\}", "{}", path)


def _tail(path: str) -> str:
    """Prefikssiz, normallashtirilgan ko'rinish.

    `BEYOND_SPEC` va `GEO_ENDPOINTS` aynan shu shaklda yozilgan: prefiks
    sozlama bo'lgani uchun uni ro'yxatlarga qattiq yozib qo'yish
    `API_PREFIX` o'zgarishi bilan ikkala ro'yxatni ham buzardi.
    """
    return _normalize(path)[_PREFIX_LEN:]


SPEC = _spec_endpoints()
SPEC_TAILS = {_tail(path): method for path, method in SPEC.items()}


@pytest.fixture(scope="module")
def schema(app):
    return app.openapi()


@pytest.fixture(scope="module")
def public_paths(schema) -> dict[str, dict]:
    """Ommaviy sath: `api_prefix` ostidagi, admin tegi yo'q yo'llar.

    **Prefiks bo'yicha filtr ataylab.** Telegram webhook i (`05` §6.3) token
    bo'lgan muhitda `create_app()` ga qo'shiladi va u API ning yo'li emas;
    prefikssiz `/` esa `include_in_schema=False`. Ikkalasini ham sath deb
    sanash testni muhitga bog'lab qo'yardi.
    """
    result: dict[str, dict] = {}
    for path, item in schema["paths"].items():
        if not path.startswith(settings.api_prefix):
            continue
        operations = {
            method: op
            for method, op in item.items()
            if isinstance(op, dict) and ADMIN_TAG not in op.get("tags", [])
        }
        if operations:
            result[_tail(path)] = operations
    return result


# --------------------------------------------------------------------------
# Parserning o'zi
# --------------------------------------------------------------------------


def test_the_endpoint_table_is_parsed_and_not_empty() -> None:
    """Parser jim buzilsa qolgan hamma test bo'sh to'plamda o'taverardi."""
    assert len(SPEC) == SPEC_ROWS, (
        f"`05` §7.2 da {len(SPEC)} ta endpoint topildi, kutilgani {SPEC_ROWS} ta: "
        f"{sorted(SPEC)} — jadval o'zgargan bo'lsa `SPEC_ROWS` ni yangilang"
    )


def test_the_table_stops_before_the_next_section() -> None:
    """Bo'lim chegarasi §7.3 ga o'tib ketmasin.

    §7.3 «Nima chiqmaydi» ro'yxati backtickli nomlar bilan to'la
    (`geom_exact`, `user_id`); chegara siljisa ular jadval qatori bo'lib
    o'qilmaydi, lekin bo'lim matni ikki barobar kattalashadi va keyingi
    tekshiruvlarning ma'nosi yo'qoladi.
    """
    section = _section()
    assert "Nima chiqmaydi" not in section
    assert "`region_id` barcha geo-so'rovlarda majburiy" in section, (
        "§7.2 ning geo qoidasi jumlasi yo'qolgan — `GEO_ENDPOINTS` tayanchsiz qoldi"
    )


# --------------------------------------------------------------------------
# Hujjat → sath
# --------------------------------------------------------------------------


def test_documented_paths_use_the_configured_prefix() -> None:
    """Hujjatdagi `/api/v1` va `settings.api_prefix` — bitta qiymat.

    `API_PREFIX` sozlama bo'lib qolgan (44-sessiyaning ochiq savoli), ya'ni
    uni `.env` dan o'zgartirish mumkin. O'zgartirilsa `05` §7.2 dagi beshta
    qator bir zumda yolg'onga aylanadi va buni hech narsa aytmasdi.
    """
    wrong = [path for path in SPEC if not path.startswith(settings.api_prefix + "/")]
    assert wrong == [], (
        f"`05` §7.2 dagi yo'llar `{settings.api_prefix}` bilan boshlanmaydi: {wrong}"
    )


@pytest.mark.parametrize("tail", sorted(SPEC_TAILS))
def test_documented_endpoint_exists(tail: str, public_paths: dict[str, dict]) -> None:
    """Har bir hujjatdagi qatorning bazasiz tayanchi.

    Ikkita holatni ham bir xil yiqitadi: yo'l umuman yo'qolgan yoki unga
    `admin` tegi qo'yilgan (`public_paths` admin tegini filtrlaydi) —
    ikkinchisi §7.2 ning ma'nosini, ya'ni «ommaviy» so'zini bekor qiladi.
    """
    assert tail in public_paths, (
        f"`05` §7.2 da `{settings.api_prefix}{tail}` bor, ommaviy sathda yo'q — "
        f"o'chgan, qayta nomlangan yoki `admin` tegini olgan "
        f"(mavjudlari: {sorted(public_paths)})"
    )


@pytest.mark.parametrize("tail", sorted(SPEC_TAILS))
def test_documented_endpoint_answers_the_documented_method(
    tail: str, public_paths: dict[str, dict]
) -> None:
    """Yo'lning borligi yetmaydi — metod ham hujjatdagidek bo'lsin."""
    method = SPEC_TAILS[tail].lower()
    # `.get` — yo'lning o'zi yo'qligi haqida `test_documented_endpoint_exists`
    # gapiradi; bu yerda `KeyError` xabarni faqat chalkashtirardi.
    available = sorted(public_paths.get(tail, {}))
    assert method in available, (
        f"`05` §7.2: {SPEC_TAILS[tail]} {settings.api_prefix}{tail}, "
        f"OpenAPI da esa faqat {available}"
    )


# `X-Admin-Token` ning ommaviy endpointda paydo bo'lishi bu yerda
# tekshirilmaydi — `tests/test_openapi_contract.py` dagi
# `test_public_operations_do_not_require_a_token` buni **butun sxema**
# bo'yicha allaqachon qiladi (43 va 45-sessiyaning saboqi: avval mavjud
# testni qidir, keyin yoz).


# --------------------------------------------------------------------------
# Sath → hujjat (teskari yo'nalish — aynan shu jim edi)
# --------------------------------------------------------------------------


def test_public_surface_has_nothing_undocumented_and_unexplained(
    public_paths: dict[str, dict],
) -> None:
    """Hujjatda yo'q ommaviy yo'l faqat `BEYOND_SPEC` da sabab bilan yashaydi."""
    extra = set(public_paths) - set(SPEC_TAILS)
    assert extra == set(BEYOND_SPEC), (
        "ommaviy sath va hujjat farqi kutilganidan boshqa. "
        f"Ortiqcha va sababsiz: {sorted(extra - set(BEYOND_SPEC))}; "
        f"`BEYOND_SPEC` da bor, sathda yo'q: {sorted(set(BEYOND_SPEC) - extra)}"
    )


def test_every_justification_says_something() -> None:
    """Bo'sh sabab — oqlashning ko'rinishi, mazmuni emas."""
    silent = [path for path, why in BEYOND_SPEC.items() if len(why.strip()) < 20]
    assert silent == [], f"`BEYOND_SPEC` da mazmunsiz sabab: {silent}"


# --------------------------------------------------------------------------
# §7.2 ning jumlasi: mintaqa
# --------------------------------------------------------------------------


def test_geo_endpoints_are_a_subset_of_the_documented_ones() -> None:
    """`GEO_ENDPOINTS` jadval bilan birga o'zgarsin.

    Yo'l qayta nomlansa ro'yxat jimgina eskirib qolardi va keyingi test
    bo'sh to'plamda o'taverardi.
    """
    assert GEO_ENDPOINTS <= set(SPEC_TAILS), sorted(GEO_ENDPOINTS - set(SPEC_TAILS))


@pytest.mark.parametrize("tail", sorted(GEO_ENDPOINTS))
def test_geo_endpoint_names_exactly_one_region(tail: str, public_paths: dict[str, dict]) -> None:
    """«`region_id` barcha geo-so'rovlarda majburiy» (`05` §7.2, PRD §16).

    Kod bu qoidani `region` so'rov parametri bilan bajaradi: u majburiy
    emas, bo'sh qiymat `DEFAULT_REGION_CODE` ga aylanadi — ya'ni javob
    **har doim aynan bitta** mintaqa bo'yicha quriladi
    (`app/api/v1/map.py` izohi). Parametr yo'qolsa yoki qayta nomlansa
    so'rov mintaqani umuman tanlay olmasdi va bu qaror jimgina bekor
    bo'lardi.
    """
    operations = public_paths.get(tail, {})
    assert operations, f"`{settings.api_prefix}{tail}` ommaviy sathda yo'q"
    for method, op in operations.items():
        names = {param["name"] for param in (op.get("parameters") or [])}
        assert REGION_PARAM in names, (
            f"{method.upper()} {settings.api_prefix}{tail}: `{REGION_PARAM}` "
            f"parametri yo'q (bor: {sorted(names)})"
        )
