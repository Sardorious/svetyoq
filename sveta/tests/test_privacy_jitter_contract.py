"""`05` §3–§3.2 ↔ `app/geo/{pipeline,jitter,h3_cells}.py` + purge — bazasiz.

**Nima uchun bu fayl kerak.** 40–59 sessiyalar `06` ning butun hujjatini va
`05` ning §2, §4.4, §4.5, §5, §6.1, §7.2, §8, §9.3, §10 bo'limlarini kod
bilan bog'ladi. `05` §3 — **oxirgi** bog'lanmagan bo'lim, va u eng qimmati:
uning artefakti mahsulot xususiyati emas, **maxfiylik kafolati**. Buzilgani
test yiqilishi bilan emas, foydalanuvchining uyi xaritada ko'rinishi bilan
bilinadi — ya'ni hech qachon bilinmaydi.

`tests/test_geo_jitter.py` allaqachon bor, lekin u boshqa savolga javob
beradi: «kod o'zi bilan izchilmi» (bir xil kirish → bir xil chiqish, radius
konfiguratsiyadan oshmaydi). Hujjatdagi **qarorlar** esa u yerda qo'lda
ko'chirilgan: `60` soni, `blake2b` nomi, r9 — hammasi test kodida literal
sifatida yotadi. Hujjat o'zgarsa (`90 kun` → `30 kun`, r9 → r8, «doimiy» →
«tasodifiy») **hech narsa yiqilmaydi**.

Bo'lim beshta artefakt beradi va bugungacha hech biri o'lchanmagan:

1. **§3 quvuri** — olti qadamli blok. U `pipeline.py` ning modul
   docstringiga qo'lda ko'chirilgan, ya'ni ikkita nusxa mustaqil yashaydi.
2. **§3 dagi `9`** — `latlng_to_cell(lat, lon, 9)`. Kodda u uch joyda:
   `settings.h3_resolution`, `h3_cells.DEFAULT_RESOLUTION` va ustun nomi
   `reports.h3_r9`.
3. **§3.1 jadvalidagi ikkita rad etilgan usul.** Ular kodda umuman yo'q —
   rad etilgan variantdan kodda iz qolmaydi. Lekin ularning **sabablari**
   bajarilgan usulga qo'yilgan talab: «o'rtacha qiymat aniq uyni beradi» →
   bitta foydalanuvchining takroriy nuqtalari **bir xil** bo'lishi shart;
   «aniqlik yo'qoladi» → siljitish nolga teng bo'lmasligi shart. Ikkalasi
   ham hozir tekshirilmaydi.
4. **§3.1 tanlovi** — «katakcha markazi + doimiy siljitish», manba
   `hash(user_id, h3_cell)`. Markaz asos ekani hech qayerda o'lchanmagan.
5. **§3.2** — `90 kun`, «nolga tenglashtirish emas — `NULL`», «fon
   vazifasi», «`district_id` + `h3_r9` yetarli». To'rttala ham kodda bor,
   to'rttasi ham hujjatdan o'qilmaydi.

**Nimani ataylab tekshirmaydi.** `geom_exact` ning API javoblarida
yo'qligini — `tests/test_purge_exact_geom.py` va `test_openapi_contract.py`;
`jitter` ning xulq-atvor qirralarini — `tests/test_geo_jitter.py`. Bu yerda
faqat hujjat ↔ kod.

**Unicode ga bog'liqlik kamaytirilgan** (53-sessiyaning sabog'i): qatorlar
o'zbekcha so'z bo'yicha emas, backtickdagi tokenlar va sonlar bo'yicha
topiladi.
"""

from __future__ import annotations

import ast
import inspect
import math
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.dialects import postgresql

from app.core.config import settings
from app.geo import h3_cells
from app.geo import jitter as jitter_module
from app.geo import pipeline as pipeline_module
from app.geo.h3_cells import cell_center, cell_of, edge_length_m
from app.geo.jitter import offset_for, public_point
from app.jobs import purge_exact_geom as purge_job
from app.jobs.runner import JOBS, register_jobs
from app.reports.models import Report
from app.reports.queries import purge_exact_geom_stmt

SVETA_ROOT = Path(__file__).resolve().parents[1]
#: `05_Technical_Design.md` repo ildizida, `sveta/` ning yonida.
DESIGN_DOC = SVETA_ROOT.parent / "05_Technical_Design.md"
PIPELINE_SRC = SVETA_ROOT / "app" / "geo" / "pipeline.py"
JITTER_SRC = SVETA_ROOT / "app" / "geo" / "jitter.py"

#: Samarqand markazi atrofidagi nuqta — quvurning haqiqiy ish maydoni.
LAT, LON = 39.6547, 66.9597
USER = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER = uuid.UUID("22222222-2222-2222-2222-222222222222")

_METERS_PER_DEGREE_LAT = 111_320.0


# --------------------------------------------------------------------------
# Hujjatni o'qish
# --------------------------------------------------------------------------


def _doc() -> str:
    assert DESIGN_DOC.exists(), f"hujjat topilmadi: {DESIGN_DOC}"
    return DESIGN_DOC.read_text(encoding="utf-8")


def _section(start: str, end: str) -> str:
    text = _doc()
    assert start in text, f"`{start}` topilmadi — hujjat qayta tuzilgan"
    tail = text.split(start, 1)[1]
    assert end in tail, f"`{start}` dan keyin `{end}` topilmadi"
    return tail.split(end, 1)[0]


def _pipeline_block() -> str:
    """§3 ning sarlavhasi bilan §3.1 orasidagi yagona kodli bloki."""
    section = _section("## 3. Geo-quvur", "### 3.1")
    blocks = re.findall(r"```\n(.*?)```", section, flags=re.DOTALL)
    assert len(blocks) == 1, f"§3 da {len(blocks)} ta blok — hujjat qayta tuzilgan"
    return blocks[0]


def _s31() -> str:
    return _section("### 3.1", "### 3.2")


def _s32() -> str:
    return _section("### 3.2", "\n---")


def _table_rows(section: str) -> list[list[str]]:
    """Markdown jadvalining ma'noli qatorlari (sarlavha va ajratgich tashqarida)."""
    rows: list[list[str]] = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|-: "):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
    return rows[1:] if rows else []


def _norm(text: str) -> str:
    """Bo'shliqlar normallashtirilgan matn — nusxalarni solishtirish uchun."""
    return re.sub(r"\s+", " ", text).strip()


def _numbers(text: str) -> list[int]:
    return [int(n) for n in re.findall(r"\d+", text.replace("_", ""))]


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _calls(func) -> set[str]:
    """Funksiya tanasida chaqirilgan nomlar (`f(...)` va `mod.f(...)`)."""
    tree = ast.parse(inspect.getsource(func).lstrip())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                names.add(target.id)
            elif isinstance(target, ast.Attribute):
                names.add(target.attr)
    return names


# --------------------------------------------------------------------------
# §3 — geo-quvur
# --------------------------------------------------------------------------


def test_pipeline_block_is_copied_into_the_module_docstring() -> None:
    """`pipeline.py` docstringidagi nusxa hujjat bilan **so'zma-so'z** bir xil.

    Nusxa ataylab qilingan (modulni ochgan odam quvurni darhol ko'radi),
    lekin nusxa — drift manbai: hujjatga qadam qo'shilsa, docstring eski
    quvurni va'da qilib qolaverardi.
    """
    doc_block = _norm(_pipeline_block())
    module_doc = pipeline_module.__doc__ or ""
    assert doc_block in _norm(module_doc), (
        "`app/geo/pipeline.py` docstringidagi quvur `05` §3 dan farq qiladi"
    )


def test_pipeline_steps_are_all_called_by_resolve() -> None:
    """Blokdagi har bir qadamning kodda chaqiruvi bor.

    Qadam ↔ funksiya moslashuvi qo'lda yozilgan — lekin **chap tomoni**
    hujjatdan olinadi: blokdagi qator yo'qolsa yoki qayta nomlansa, test
    aynan shu yerda yiqiladi.
    """
    block = _pipeline_block()
    steps = {
        "validatsiya": "validate_point",
        "h3_r9": "cell_of",
        "district_id": "find_district_id",
        "mahalla_id": "find_mahalla_id",
        "geom_public": "public_point",
    }
    called = _calls(pipeline_module.resolve)
    for token, func_name in steps.items():
        assert token in block, f"`{token}` qadami `05` §3 blokida yo'q"
        assert func_name in called, f"`{token}` qadami `resolve()` da chaqirilmaydi"


def test_h3_resolution_literal_comes_from_the_document() -> None:
    """Blokdagi `latlng_to_cell(lat, lon, 9)` ning `9` i kodning uch joyida.

    Rezolyutsiyani o'zgartirish migratsiya talab qiladi (`reports.h3_r9`
    ustun nomi r9 ni qat'iy belgilaydi), shuning uchun uchala nusxa ham
    hujjatdagi son bilan solishtiriladi.
    """
    block = _pipeline_block()
    match = re.search(r"latlng_to_cell\([^)]*?(\d+)\s*\)", block)
    assert match, "§3 blokida `latlng_to_cell(..., N)` topilmadi"
    spec_res = int(match.group(1))

    assert h3_cells.DEFAULT_RESOLUTION == spec_res
    assert settings.h3_resolution == spec_res
    assert h3_cells.resolution() == spec_res
    # Ustun nomi ham o'sha sonni takrorlaydi.
    assert f"h3_r{spec_res}" in Report.__table__.columns


def test_district_lookup_keeps_both_conditions_from_the_document() -> None:
    """Blokdagi `WHERE valid_to IS NULL AND ST_Contains(geom, point)`.

    `valid_to IS NULL` tushib qolsa nuqta **yopilgan** chegaraga ham
    tushardi (`01` FR-S-803 versiyalanishi), va bu jimgina defekt:
    natijada `district_id` bo'sh emas, shunchaki noto'g'ri.
    """
    block = _pipeline_block()
    assert "valid_to IS NULL" in block
    assert "ST_Contains" in block

    source = inspect.getsource(pipeline_module.find_district_id)
    assert "valid_to.is_(None)" in source
    assert "ST_Contains" in source


def test_geom_public_is_produced_by_jitter_not_by_the_exact_point() -> None:
    """Blokdagi `geom_public = jitter(geom_exact)`.

    Ya'ni ommaviy koordinata **hosila**: `resolve()` uni `public_point` dan
    oladi va aniq nuqtani u yerga ko'chirmaydi.
    """
    assert "geom_public = jitter(geom_exact)" in _norm(_pipeline_block())

    tree = ast.parse(inspect.getsource(pipeline_module.resolve).lstrip())
    public_sources = {
        kw.arg: kw.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "GeoResolution"
        for kw in node.keywords
    }
    for field in ("public_lat", "public_lon"):
        assert field in public_sources, f"`GeoResolution({field}=...)` topilmadi"
        assigned = ast.unparse(public_sources[field])
        assert assigned not in {"lat", "lon"}, (
            f"`{field}` aniq koordinatadan olinmoqda — `05` §3 buzilishi"
        )

    resolution_pub = public_point(USER, LAT, LON)
    assert resolution_pub != (LAT, LON)


# --------------------------------------------------------------------------
# §3.1 — tanlangan usul
# --------------------------------------------------------------------------


def test_chosen_method_is_cell_centre_plus_offset() -> None:
    """Tanlov: «H3 r9 katakcha markazi + kichik siljitish».

    Ya'ni asos — **markaz**, aniq nuqta emas. Aks holda siljitish faqat
    shovqin bo'lardi va uyni ochib berardi.
    """
    assert "H3 r9" in _norm(_s31()), "§3.1 tanlovi r9 dan boshqa narsaga o'zgargan"

    cell = cell_of(LAT, LON)
    c_lat, c_lon = cell_center(cell)
    north_m, east_m = offset_for(USER, cell)
    pub_lat, pub_lon = public_point(USER, LAT, LON)

    d_lat_m = (pub_lat - c_lat) * _METERS_PER_DEGREE_LAT
    d_lon_m = (pub_lon - c_lon) * _METERS_PER_DEGREE_LAT * math.cos(math.radians(c_lat))
    assert abs(d_lat_m - north_m) < 0.5
    assert abs(d_lon_m - east_m) < 0.5


def test_offset_depends_only_on_user_and_cell() -> None:
    """Manba — `hash(user_id, h3_cell)`, boshqa hech narsa.

    Aniq koordinata kirsa, siljitish undan xabar topib qolardi va
    katakchaning butun ma'nosi yo'qolardi.
    """
    spec = _norm(_s31())
    assert "hash(user_id, h3_cell)" in spec, "§3.1 dagi siljitish manbai o'zgargan"

    cell = cell_of(LAT, LON)
    base = offset_for(USER, cell)
    assert offset_for(USER, cell) == base
    assert offset_for(OTHER, cell) != base
    assert offset_for(USER, cell_of(LAT + 0.05, LON + 0.05)) != base

    params = list(inspect.signature(jitter_module._unit_pair).parameters)
    assert params == ["user_key", "cell"], (
        "siljitish manbaiga uchinchi kirish qo'shilgan — `05` §3.1 buzilishi"
    )


def test_offset_is_deterministic_across_processes() -> None:
    """«**doimiy** (deterministik)» — ya'ni tasodifiylik manbai yo'q.

    Python ning o'rnatilgan `hash()` i satrlar uchun har protsessda
    tasodifiylanadi (`PYTHONHASHSEED`), ya'ni u hujjatning «har doim bir
    xil nuqta» va'dasini buzardi; `random` esa uni ochiqdan-ochiq buzadi.
    """
    spec = _norm(_s31())
    assert "deterministik" in spec

    tree = ast.parse(_source(JITTER_SRC))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "hash", (
                "`app/geo/jitter.py` o'rnatilgan `hash()` ni ishlatmoqda — "
                "u `PYTHONHASHSEED` bilan tasodifiylanadi"
            )
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names]
            module = getattr(node, "module", None) or ""
            assert "random" not in names and module != "random"
            assert "secrets" not in names and module != "secrets"
    assert "blake2b" in _source(JITTER_SRC)


def test_repeated_reports_of_one_user_do_not_average_out() -> None:
    """§3.1 jadvalining 1-qatori: «o'rtacha qiymat aniq uyni beradi».

    Aynan shu sabab bilan tasodifiy siljitish rad etilgan. Tanlangan usul
    unga immunitetli bo'lishi shart: bitta foydalanuvchining bitta
    katakchadagi **hamma** xabari bir xil nuqta beradi, ya'ni o'rtachalash
    yangi ma'lumot bermaydi (dispersiya — nol).
    """
    rows = _table_rows(_s31())
    assert rows, "§3.1 jadvali topilmadi"
    rejected = _norm(rows[0][0])
    assert "150" in rejected, "§3.1 ning rad etilgan 1-usuli o'zgargan"

    cell = cell_of(LAT, LON)
    points = set()
    for i in range(200):
        lat = LAT + (i % 20 - 10) * 0.00002
        lon = LON + (i // 20 - 5) * 0.00002
        if cell_of(lat, lon) != cell:
            continue
        points.add(public_point(USER, lat, lon))
    assert len(points) == 1, (
        f"bitta katakchada {len(points)} xil ommaviy nuqta — o'rtachalash hujumi ishlaydi"
    )


def test_offset_is_not_zero_so_points_do_not_collapse() -> None:
    """§3.1 jadvalining 2-qatori: sof markazga bog'lash aniqlikni yo'qotadi.

    Shuning uchun tanlov «markaz **+** siljitish»: siljitish nolga teng
    bo'lsa usul aynan rad etilgan ikkinchi variantga aylanardi va bitta
    katakchadagi hamma foydalanuvchi bitta piksel bo'lib qolardi.
    """
    rows = _table_rows(_s31())
    assert len(rows) == 2, f"§3.1 jadvalida {len(rows)} qator — hujjat qayta tuzilgan"
    assert "H3" in rows[1][0], "§3.1 ning rad etilgan 2-usuli o'zgargan"
    # Rad etilgan birinchi usulda kattalik bor (±150 m), ikkinchisida yo'q —
    # u umuman siljitmaydi. Aynan shu farq tanlovni ikkalasidan ajratadi.
    assert _numbers(rows[1][0]) in ([], [3]), f"2-usulga kattalik qo'shilgan: {rows[1][0]}"

    assert settings.jitter_max_m > 0
    cell = cell_of(LAT, LON)
    centre = cell_center(cell)
    distinct = {public_point(uuid.uuid5(uuid.NAMESPACE_DNS, str(i)), LAT, LON) for i in range(50)}
    assert len(distinct) == 50, "turli foydalanuvchilar bitta nuqtaga yig'ildi"
    assert centre not in distinct


def _spec_edge_m() -> int:
    """§3.1 dagi «≈ N m o'rtacha qirra»."""
    match = re.search(r"≈\s*(\d+)\s*m", _s31())
    assert match, "§3.1 da r9 qirra uzunligi topilmadi"
    return int(match.group(1))


def test_r9_edge_length_stays_in_the_documented_band() -> None:
    """«H3 r9 ≈ 174 m o'rtacha qirra» — kafolatning **asosi**.

    Son hujjatda muvozanatning asosi sifatida keltirilgan: «xarita uchun
    yetarli, uy uchun yetarli emas». Rezolyutsiya o'zgarsa u jimgina yolg'on
    bo'lib qolardi — r10 da katakcha 76 m ga tushadi va bir necha uyni
    qoplaydi, r8 da esa 531 m ga chiqib xaritani foydasiz qiladi.

    **Nima uchun tenglik emas, tasma.** `174` — H3 v3 ning jadvalidan; h3-py
    4.2 o'rtacha qirra hisobini tuzatdi va r9 endi ≈ 201 m. Ya'ni haqiqiy
    katakcha hujjat va'da qilganidan **kattaroq**, ya'ni maxfiylik
    kuchsizlanmagan — kafolat buzilmaydi. Shuning uchun shart bir tomonlama:
    haqiqiy qirra hujjatdagi sondan kichik bo'lmasin va uni ikki barobardan
    ortiq oshirmasin. Farqning o'zi `PROGRESS.md` ning «Ochiq savollar» ida
    (hujjatni agent o'zgartirmaydi).
    """
    spec_edge = _spec_edge_m()
    actual = edge_length_m(9)
    assert spec_edge <= actual < 2 * spec_edge, (
        f"hujjat {spec_edge} m deydi, h3 esa {actual:.1f} m"
    )


def test_the_band_actually_excludes_the_neighbouring_resolutions() -> None:
    """Yuqoridagi tasma vakuum emas: r8 ham, r10 ham unga sig'maydi.

    Tasma juda keng bo'lsa test yashil qolib, rezolyutsiya o'zgarishini
    o'tkazib yuborardi.
    """
    spec_edge = _spec_edge_m()
    for res in (8, 10):
        edge = edge_length_m(res)
        assert not (spec_edge <= edge < 2 * spec_edge), (
            f"r{res} ({edge:.1f} m) tasmaga sig'moqda — tasma juda keng"
        )


def test_offset_is_small_relative_to_the_cell() -> None:
    """«**kichik** siljitish» — katakcha bergan xiralikni bosib ketmaydi.

    Ikkala tomondan ham o'lchanadi: siljitish r9 qirrasidan ham, rad
    etilgan tasodifiy usulning ±150 m idan ham kichik. Aks holda «markaz +
    kichik siljitish» de-fakto o'sha rad etilgan usul bo'lardi.
    """
    rejected_m = max(_numbers(_table_rows(_s31())[0][0]))
    assert settings.jitter_max_m < rejected_m
    assert settings.jitter_max_m < edge_length_m(9)


# --------------------------------------------------------------------------
# §3.2 — aniq koordinatani saqlash
# --------------------------------------------------------------------------


def test_retention_days_come_from_the_document() -> None:
    """«**90 kundan keyin** o'chirish» — sozlamada ham, vazifada ham."""
    section = _norm(_s32())
    match = re.search(r"\*\*(\d+)\s+kun", section)
    assert match, "§3.2 da saqlash muddati topilmadi"
    spec_days = int(match.group(1))

    assert settings.exact_geom_retention_days == spec_days

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert purge_job.cutoff(now) == now - timedelta(days=spec_days)


def test_purge_nulls_the_column_instead_of_zeroing_it() -> None:
    """«nolga tenglashtirish emas — ustunni `NULL` qilish».

    Farq maxfiylik uchun hal qiluvchi: `POINT(0 0)` qator **bor** deb
    ko'rsatadi va `IS NOT NULL` filtri uni ikkinchi marta tozalamaydi, ya'ni
    tozalash o'z-o'zidan to'xtardi.
    """
    section = _norm(_s32())
    assert "NULL" in section

    compiled = str(
        purge_exact_geom_stmt(
            older_than=datetime(2026, 1, 1, tzinfo=timezone.utc), batch_size=10
        ).compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
    )
    assert re.search(r"SET\s+geom_exact\s*=\s*NULL", compiled), compiled
    assert "ST_MakePoint" not in compiled
    assert "geom_exact IS NOT NULL" in compiled


def test_purge_runs_as_a_background_job() -> None:
    """«fon vazifasi bilan» — ro'yxatda haqiqatan turibdi.

    Vazifa `register_jobs()` da qolib ketishi 56-sessiyada butun `jobs`
    konteynerini jim qoldirgan edi: kod bor, ishlamaydi.
    """
    assert "fon vazifasi" in _norm(_s32())
    register_jobs()
    assert "purge_exact_geom" in {job.name for job in JOBS}


def test_history_columns_survive_the_purge() -> None:
    """«Tarixiy statistika uchun `district_id` + `h3_r9` yetarli».

    Ya'ni tozalash **faqat** `geom_exact` ga tegadi. Ikkala ustun ham
    modelda bor va `UPDATE` ularni ko'rmaydi.
    """
    section = _s32()
    survivors = re.findall(r"`(\w+)`", section)
    assert "district_id" in survivors and "h3_r9" in survivors

    for column in ("district_id", "h3_r9"):
        assert column in Report.__table__.columns

    compiled = str(
        purge_exact_geom_stmt(
            older_than=datetime(2026, 1, 1, tzinfo=timezone.utc), batch_size=10
        ).compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
    )
    set_clause = compiled.split("SET", 1)[1].split("WHERE", 1)[0]
    for column in ("district_id", "h3_r9", "geom_public"):
        assert column not in set_clause, f"tozalash `{column}` ga ham tegmoqda"
