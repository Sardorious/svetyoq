"""Spetsifikatsiya reyestrlari indeksi va uning vitrinasi — bazasiz.

Indeks o'zi hech narsani o'lchamaydi: har bir son o'n uchta boshqa
modulning sof funksiyasidan keladi va ularning har biri o'z kontrakt
testi bilan qulflangan. Ya'ni bu yerda takrorlash mumkin bo'lgan
narsalar tekshirilmaydi — faqat **indeksning o'z** da'volari, va ular
uch sinfdan.

1. **Ro'yxatning to'liqligi.** Indeksning yagona ma'nosi — «hammasi shu
   yerda». Agar keyingi run o'n to'rtinchi reyestrni yozsa va uni bu
   yerga qo'shishni unutsa, vitrina jimgina qisqaradi va hech narsa
   qizarmaydi: uni ko'radigan odam ro'yxatni to'liq deb o'qiydi.
   Shuning uchun `app/` **skanerlanadi**: `SPEC` konstantasi bo'lgan
   har bir modul indeksda bo'lishi shart.

2. **Sonlarning ma'nosi.** `flagged` — qatorlar kichik to'plami,
   `undeclared` — hujjatda umuman yo'q narsalar. Ularni qo'shib
   yuborish yoki bir-birining o'rniga ishlatish hisobotni boridan
   yaxshiroq ham, yomonroq ham ko'rsatishi mumkin, va ikkala yo'nalish
   ham jim.

3. **Muhitga bog'liqlik.** To'rtta reyestr hujjat matnisiz umuman
   qurilmaydi, va matn Docker obrazida yo'q. Bu holat testda
   **tripwire** bilan yozilgan (69-sessiyaning naqshi): tuzatilgan
   kuni test qizaradi va hujjat ham, izoh ham yangilanishi kerak
   bo'ladi.
"""

from __future__ import annotations

import ast
import importlib
import json
import re
from pathlib import Path

import pytest

import app as app_pkg
from app.admin import registries as reg
from app.admin.roles import Permission, Role, has_permission
from app.core import i18n
from app.core.config import settings

APP_ROOT = Path(app_pkg.__file__).resolve().parent
SVETA_ROOT = APP_ROOT.parent
#: ⚠️ Yo'l `05` §7.2 da yo'q va bo'lishi ham shart emas (admin sathi u
#: yerda sanalmaydi). `PROGRESS.md` 74–79 runlarda uni
#: `/admin/monitoring` deb rejalashtirgan edi; 80-run yozib bo'lgach
#: odam nomni **`/admin/registries`** ga o'zgartirdi — `01` §22 ning
#: o'zi «Logging & Monitoring» deb ataladi va indeksda `monitoring`
#: degan alohida qator bor, ya'ni eski nom ikkita boshqa narsani bitta
#: so'z bilan atardi.
PATH = f"{settings.api_prefix}/admin/registries"

TOKEN_ADMIN = "a" * 40
TOKEN_MOD = "m" * 40
TOKEN_VIEWER = "v" * 40
TOKENS = f"nilufar:admin:{TOKEN_ADMIN},aziz:moderator:{TOKEN_MOD},bek:viewer:{TOKEN_VIEWER}"

#: Reyestr modulini belgilaydigan konstanta. `risks.py` ikkita bo'limni
#: qamraydi va shuning uchun `SPEC` o'rniga ikkita nom ishlatadi.
SPEC_NAMES = ("SPEC", "SPEC_RISKS")

#: Skaner bo'shab qolmasligining pastki chegarasi. Bugun 12 ta modulda
#: `SPEC` bor (+`gates`, uning bunday konstantasi yo'q).
MIN_SCANNED = 10


@pytest.fixture(autouse=True)
def tokens(monkeypatch):
    monkeypatch.setattr(settings, "admin_tokens", TOKENS)


@pytest.fixture(scope="module")
def doc() -> str:
    text = reg.read_doc()
    assert text is not None, f"repoda `{reg.DOC_NAME}` topilmadi: {reg.DOC_ROOT}"
    return text


@pytest.fixture(scope="module")
def report(doc):
    return reg.evaluate(doc)


# --------------------------------------------------------------------------
# 1. Ro'yxatning to'liqligi
# --------------------------------------------------------------------------


def _modules_with_spec() -> dict[str, str]:
    """`app/` dagi `{modul nomi: SPEC qiymati}`.

    `ast` bilan, import qilmasdan: skaner import yon ta'siriga bog'liq
    bo'lmasligi kerak. Qiymat faqat oddiy satr bo'lganda olinadi —
    `risks.py` ning ikkita konstantasidan birinchisi (`SPEC_RISKS`)
    yetarli, chunki indeks qatori baribir bitta.
    """
    found: dict[str, str] = {}
    for path in sorted(APP_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            if not isinstance(target, ast.Name) or target.id not in SPEC_NAMES:
                continue
            if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, str):
                continue
            module = ".".join(path.relative_to(APP_ROOT.parent).with_suffix("").parts)
            found.setdefault(module, node.value.value)
    return found


def test_the_scanner_finds_the_registry_modules() -> None:
    """Skaner jim buzilsa qolgan tekshiruv bo'sh to'plamda o'taverardi."""
    scanned = _modules_with_spec()
    assert len(scanned) >= MIN_SCANNED, scanned


def test_every_module_with_a_spec_constant_is_in_the_index() -> None:
    """Indeksdan tushib qolgan reyestr — jimgina qisqargan ro'yxat.

    Bu — faylning asosiy da'vosi. `SPEC` konstantasi 66–79 runlarning
    umumiy odati bo'ldi: bo'lim kodga ko'chirilganda uning nomeri
    modulning tepasida yoziladi. Shu odat shu yerda **shartga**
    aylanadi.
    """
    indexed = {entry.module for entry in reg.REGISTRIES}
    missing = sorted(set(_modules_with_spec()) - indexed)
    assert not missing, f"indeksda yo'q reyestrlar: {missing}"


def test_every_indexed_module_exists_and_is_importable() -> None:
    """`module` — havola, izoh emas."""
    for entry in reg.REGISTRIES:
        importlib.import_module(entry.module)


def test_spec_labels_are_read_from_the_registries_not_copied() -> None:
    """Bo'lim nomeri modulning **o'z** konstantasidan olinadi.

    Qo'lda ko'chirilgan nomer 61-sessiyaning tuzog'i: fayl o'z
    nusxasini o'lchaydi va manba o'zgarganda hech narsa qizarmaydi.
    """
    scanned = _modules_with_spec()
    for entry in reg.REGISTRIES:
        source = scanned.get(entry.module)
        if source is None:  # `gates` — `SPEC` konstantasi yo'q
            continue
        assert entry.spec.startswith(source), (entry.code, entry.spec, source)


def test_the_two_section_registry_names_both_sections() -> None:
    """`risks` ikkita bo'limni qamraydi va ikkalasi ham ko'rinadi."""
    entry = reg.REGISTRY_BY_CODE["risks"]
    assert "§26" in entry.spec and "§27" in entry.spec


def test_gates_is_named_but_not_measured() -> None:
    """Yagona `LIVE` qator: indeks uni hisoblamaydi, faqat yo'l ko'rsatadi.

    Uni «hisoblanmagani uchun» ro'yxatdan chiqarib tashlash indeksni
    yolg'onga aylantirardi — reyestr **bor**, va u eng ko'p o'qiladigan
    reyestrlardan biri.
    """
    entry = reg.REGISTRY_BY_CODE["gates"]
    assert entry.serving is reg.Serving.LIVE
    assert entry.probe is None
    assert entry.endpoint == "/admin/gates"


def test_only_two_registries_have_their_own_endpoint(report) -> None:
    """Indeksning sababi: qolgan hammasi faqat shu yerda ko'rinadi."""
    surfaced = [e.code for e in reg.REGISTRIES if e.surfaced]
    assert surfaced == ["measures", "gates"]
    assert len(report.unsurfaced) == len(reg.REGISTRIES) - 2


def test_registry_endpoints_exist_in_the_api(app) -> None:
    """`endpoint` — ishlaydigan yo'l, matn emas."""
    paths = set(app.openapi()["paths"])
    for entry in reg.REGISTRIES:
        if entry.endpoint:
            assert f"{settings.api_prefix}{entry.endpoint}" in paths, entry.code


# --------------------------------------------------------------------------
# 2. Sonlarning ma'nosi
# --------------------------------------------------------------------------


def test_flagged_never_exceeds_total(report) -> None:
    """`flagged` — qatorlarning kichik to'plami.

    Uchta sababdan belgilangan bitta qatorni uch marta sanash eng
    oson xato: hisobot boridan yomonroq ko'rinadi va uni tekshirgan
    odam yo'q qatorni qidiradi.
    """
    for item in report.findings:
        if item.probe:
            assert item.probe.flagged <= item.probe.total, item.registry.code


def test_probe_rejects_impossible_counts() -> None:
    """Invariantni `Probe` ning o'zi ushlaydi, test emas."""
    with pytest.raises(ValueError):
        reg.Probe(verdict=reg.Verdict.ACCURATE, total=1, flagged=2, undeclared=0)


def test_undeclared_is_not_folded_into_flagged(report) -> None:
    """Ikkita son ikkita boshqa da'vo.

    `flagged` — «yozilgani noto'g'ri», `undeclared` — «yozilmagani
    bor». Ular bir joyda bo'lsa, indeks e'lon qilinmagan narsalarni
    hujjatning xatosi deb ko'rsatardi va teskarisi. Bugun ikkalasi ham
    nol emas, ya'ni farq o'lchanadi.
    """
    assert report.undeclared_total > 0
    assert any(item.probe and item.probe.flagged for item in report.findings)


def test_counts_cover_every_registry(report) -> None:
    """Hisob yig'indisi ro'yxat uzunligiga teng — hech kim tushib qolmaydi."""
    assert sum(report.counts.values()) == len(reg.REGISTRIES)


def test_unavailable_is_not_a_verdict(report) -> None:
    """`unavailable` hukm emas: u boshqa o'qning qiymati.

    `counts` da ikkalasi yonma-yon turadi va aynan shu yerda ular
    aralashib ketishi mumkin edi.
    """
    assert "unavailable" not in {str(v) for v in reg.Verdict}
    assert set(report.counts) == {str(v) for v in reg.Verdict} | {"unavailable"}


def test_coverage_registries_are_unscored(report) -> None:
    """Qamrov hisobotlari hujjatning rostligi haqida gapirmaydi.

    `measures`, `monitoring`, `dashboards` va `acceptance` «nechtasi
    o'lchanadi» degan savolga javob beradi; `acceptance` esa ustiga
    **mintaqa** haqida. Ularni `INACCURATE` deb belgilash hujjatga u
    aytmagan gapni yuklardi.
    """
    unscored = {
        item.registry.code
        for item in report.findings
        if item.probe and item.probe.verdict is reg.Verdict.UNSCORED
    }
    assert unscored == {"measures", "monitoring", "dashboards", "acceptance"}


def test_verdicts_are_taken_from_the_registries(report) -> None:
    """Hukm indeksda qayta hisoblanmaydi — u reyestrning o'z javobi.

    Uchta mustaqil manba tekshiriladi (`accurate`, `trustworthy`,
    `faithful`): uchalasi ham boshqa nom bilan atalgan va shuning
    uchun ular indeksda oson chalkashib ketishi mumkin edi.
    """
    from app.admin import security as security_mod
    from app.release import dependencies as dependencies_mod

    expected = {
        "dependencies": dependencies_mod.evaluate().accurate,
        "security": security_mod.evaluate().trustworthy,
    }
    for item in report.findings:
        if item.registry.code in expected and item.probe:
            accurate = item.probe.verdict is reg.Verdict.ACCURATE
            assert accurate == expected[item.registry.code], item.registry.code


# --------------------------------------------------------------------------
# 3. Muhitga bog'liqlik
# --------------------------------------------------------------------------


def test_doc_bound_registries_disappear_without_the_document() -> None:
    """Matnsiz to'rtta reyestr umuman qurilmaydi — va bu prodda shunday."""
    blind = reg.evaluate(None)
    unavailable = {item.registry.code for item in blind.unavailable}
    doc_bound = {e.code for e in reg.REGISTRIES if e.serving is reg.Serving.DOC_BOUND}
    assert doc_bound <= unavailable
    for item in blind.unavailable:
        if item.registry.serving is reg.Serving.DOC_BOUND:
            assert item.reason is reg.Reason.DOC_MISSING


def test_self_contained_registries_survive_without_the_document() -> None:
    """Sof reyestrlar matnga bog'liq emas — aks holda ajratishning ma'nosi yo'q."""
    blind = reg.evaluate(None)
    for item in blind.findings:
        if item.registry.serving is reg.Serving.SELF_CONTAINED:
            assert item.available, item.registry.code


def test_the_index_admits_when_it_is_incomplete() -> None:
    """`complete` — hisobotning javobi, dalil emas."""
    assert reg.evaluate(None).complete is False
    assert reg.evaluate(None).doc_present is False


def test_missing_document_is_a_state_not_a_failure(tmp_path) -> None:
    """`read_doc` xato ko'tarmaydi: hujjatning yo'qligi nosozlik emas."""
    assert reg.read_doc(tmp_path) is None


def test_the_image_does_not_ship_the_spec_document() -> None:
    """Hujjat Docker obraziga kirmaydi — **qaror**, kamchilik emas.

    `Dockerfile` `app`, `tools`, `tests` va `alembic` ni ko'chiradi;
    `01_PRD_Samarkand.md` esa build kontekstidan **tashqarida**
    (kontekst — `sveta/`, hujjat undan bir daraja yuqorida). Ya'ni
    to'rtta `DOC_BOUND` reyestr serverda ko'rinmaydi.

    80-run buni topdi va o'sha kuni odam javob berdi: **hujjatlar
    obrazga qo'shilmaydi.** Shundan keyin bu test tripwire emas,
    **kontrakt**: u qarorni ushlab turadi.

    Yiqilishning ikkala tomoni ham bir xil darajada muhim. Hujjat
    `COPY` ga qo'shilsa — qaror jimgina bekor qilingan bo'ladi.
    Build konteksti repo ildiziga ko'chirilsa (`..` bilan `COPY`) —
    hujjat obrazga **tasodifan** tushishi mumkin, va o'sha kuni
    `Serving.DOC_BOUND` ning butun ma'nosi qayta o'qilishi kerak.
    """
    dockerfile = (SVETA_ROOT / "Dockerfile").read_text(encoding="utf-8")
    copied = re.findall(r"^COPY\s+(\S+)", dockerfile, re.MULTILINE)
    assert reg.DOC_NAME not in dockerfile
    assert ".." not in " ".join(copied), "build konteksti kengaydi — tripwire ni qayta o'qing"


# --------------------------------------------------------------------------
# Vitrina
# --------------------------------------------------------------------------


def test_reading_the_index_needs_its_own_permission() -> None:
    assert has_permission(Role.ADMIN, Permission.REGISTRIES_READ)
    assert not has_permission(Role.MODERATOR, Permission.REGISTRIES_READ)
    assert not has_permission(Role.VIEWER, Permission.REGISTRIES_READ)


@pytest.mark.parametrize("token", [TOKEN_MOD, TOKEN_VIEWER])
async def test_index_is_forbidden_without_the_permission(client, token) -> None:
    response = await client.get(PATH, headers={"X-Admin-Token": token})
    assert response.status_code == 403


async def test_index_is_not_public(client) -> None:
    assert (await client.get(PATH)).status_code == 403


async def test_index_lists_every_registry(client) -> None:
    response = await client.get(PATH, headers={"X-Admin-Token": TOKEN_ADMIN})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == len(reg.REGISTRIES)
    assert [row["code"] for row in body["registries"]] == [e.code for e in reg.REGISTRIES]


async def test_index_reaches_no_database(client) -> None:
    """Vitrina bazasiz javob beradi.

    `conftest` bazasiz muhitda ham `client` beradi; agar endpoint
    sessiya so'raganda edi, bu test aynan shu yerda yiqilardi va
    `requires_db` ga ko'chirilishi kerak bo'lardi. Da'vo shakli
    `/admin/measures` bilan bir xil.
    """
    response = await client.get(PATH, headers={"X-Admin-Token": TOKEN_ADMIN})
    assert response.status_code == 200


async def test_live_registry_is_returned_without_numbers(client) -> None:
    response = await client.get(PATH, headers={"X-Admin-Token": TOKEN_ADMIN})
    row = next(r for r in response.json()["registries"] if r["code"] == "gates")
    assert row["verdict"] is None
    assert row["total"] is None and row["flagged"] is None
    assert row["reason"], "hisoblanmagan qator sababsiz qolmaydi"
    assert row["endpoint"] == "/admin/gates"


async def test_measured_rows_carry_no_reason(client) -> None:
    """Sabab faqat qurilmagan qatorda bo'ladi — aks holda u shovqin."""
    response = await client.get(PATH, headers={"X-Admin-Token": TOKEN_ADMIN})
    for row in response.json()["registries"]:
        if row["verdict"] is not None:
            assert row["reason"] == "", row["code"]


async def test_labels_are_translated(client) -> None:
    """Hisobotni odam o'qiydi, interfeys emas (`/admin/gates` bilan bir xil)."""
    uz = await client.get(
        PATH, headers={"X-Admin-Token": TOKEN_ADMIN, "Accept-Language": "uz"}
    )
    ru = await client.get(
        PATH, headers={"X-Admin-Token": TOKEN_ADMIN, "Accept-Language": "ru"}
    )
    uz_labels = {r["code"]: r["label"] for r in uz.json()["registries"]}
    ru_labels = {r["code"]: r["label"] for r in ru.json()["registries"]}
    assert uz_labels != ru_labels
    for code, label in uz_labels.items():
        assert not label.startswith(reg.KEY_PREFIX), f"{code}: tarjima topilmadi"
        assert not ru_labels[code].startswith(reg.KEY_PREFIX), code


def test_every_registry_key_is_in_both_catalogues() -> None:
    """Kalit ikkala tilda ham bo'lishi shart (`04` §6).

    `test_i18n_key_contract.py` buni oila darajasida qulflaydi; bu
    yerda esa **ro'yxatning o'zi** o'lchanadi: yangi reyestr
    qo'shilganda uning kaliti bilan birga qo'shilganini shu test
    darhol ko'rsatadi.
    """
    locales = APP_ROOT / "core" / "i18n" / "locales"
    for lang in ("uz", "ru"):
        catalogue = json.loads((locales / f"{lang}.json").read_text(encoding="utf-8"))
        for key in reg.REGISTRY_KEYS + reg.REASON_KEYS:
            assert key in catalogue, (lang, key)
            assert i18n.t(key, lang) != key


def test_every_reason_has_a_key() -> None:
    """Sabab kodi qo'shilib, kaliti unutilishi — jim yo'nalish."""
    assert len(reg.REASON_KEYS) == len(list(reg.Reason))


def test_the_index_is_not_in_the_public_surface(app) -> None:
    """`05` §7.2 ommaviy endpointlarni sanaydi; indeks admin sathida.

    Da'vo `test_api_surface_contract.py` ning `ADMIN_TAG` filtri bilan
    bir xil, lekin bu yerda u aynan shu yo'l uchun yoziladi: teg
    tushib qolsa indeks jimgina ommaviy sathga chiqardi va u yerda
    hech qanday `BEYOND_SPEC` izohi bo'lmasdi.
    """
    operations = app.openapi()["paths"][PATH]
    assert "admin" in operations["get"]["tags"]
