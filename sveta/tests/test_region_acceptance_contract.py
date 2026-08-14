"""`01` §23 «Acceptance Criteria» ↔ `app/release/acceptance.py` — bazasiz.

**Nima uchun bu fayl kerak.** `01` §23 — mahsulotning yakuniy savoli
(«mintaqani ommaga ochsa bo'ladimi?») va u yettita belgilash katagi
bilan beriladi. Shu paytgacha ro'yxat faqat hujjatda edi: kodda
«acceptance» so'zi umuman uchramasdi.

66-run `03` §6 gate larini qulflagan, lekin u boshqa o'q: gate —
**loyiha fazasi** bo'yicha va hayotda bir marta yopiladi, §23 esa
**har mintaqa** uchun qaytadan yuriladi (`03` §6 G-8 shunga tayanadi).

Bu fayl to'rt narsani bog'laydi:

1. **Ro'yxatning tuzilishi** — yettita qator, tartibi va har birining
   **so'zma-so'z** matni hujjatdan parse qilinadi. `SPEC_TABLE`
   qo'lda ko'chirilmaydi (61-run sabog'i: qo'lda ko'chirilgan jadval
   o'z nusxasini o'lchaydi).
2. **Sonlar** — `≥50` va PG-S4 ning `100%` i hujjatdan olinadi.
3. **Vitrina reyestri xossa sifatida** — `shows_index` bayrog'i
   *ishonch* emas, **dalil** bilan tekshiriladi: javob modelining
   maydonlari, CSV ustunlari va `web/` fayllarining o'zi o'qiladi
   (69-run ning qoidasi: «xossa bayroq bilan qulflanmaydi»).
4. **Delegatsiya nusxa emasligi** — 6-qator `01` §22 ning birinchi
   qatori bilan bir xil talab; test uni `monitoring` ni **o'zgartirib**
   tekshiradi, ya'ni ikkinchi nusxa yozilsa fayl yiqiladi (57-run
   sabog'i).

**Ataylab tekshirilmaydi:** `note` va `why_missing` matnlari. Ular
keyingi o'quvchi uchun sabab, artefakt emas; ularni tenglik bilan
qulflash izohni tahrirlab bo'lmaydigan qilardi.
"""

from __future__ import annotations

import inspect
import re
from dataclasses import replace
from pathlib import Path

import pytest

from app.api.v1.heatmap import HeatCollection
from app.api.v1.map import MapCollection, OutageProperties
from app.api.v1.stats import StatsOut
from app.clustering import lookup, snapshot
from app.core import i18n
from app.obs import monitoring
from app.release import acceptance, gates
from app.stats import export, maturity

SVETA_ROOT = Path(__file__).resolve().parents[1]
#: `01_PRD_Samarkand.md` repo ildizida, `sveta/` ning yonida.
PRD_DOC = SVETA_ROOT.parent / "01_PRD_Samarkand.md"
WEB_DIR = SVETA_ROOT / "web"

ACCEPTANCE_SECTION = "## 23. Acceptance Criteria"
ACCEPTANCE_SECTION_END = "## 24. Product Roadmap"

#: §23 dagi belgilash kataklari soni. **Aynan**: ro'yxat yopiq.
SPEC_CRITERION_ROWS = 7


# --- Hujjatni o'qish ---


def _doc() -> str:
    return PRD_DOC.read_text(encoding="utf-8")


def _section(start: str, end: str) -> str:
    text = _doc()
    assert start in text, f"`{start}` topilmadi — hujjat qayta tuzilgan"
    tail = text.split(start, 1)[1]
    assert end in tail, f"`{end}` topilmadi — hujjat qayta tuzilgan"
    return tail.split(end, 1)[0]


def _checkboxes() -> list[str]:
    """§23 ning `- [ ] …` qatorlari, hujjatdagi tartibda."""
    rows = [
        line.strip()[len("- [ ]") :].strip()
        for line in _section(ACCEPTANCE_SECTION, ACCEPTANCE_SECTION_END).splitlines()
        if line.strip().startswith("- [ ]")
    ]
    assert rows, "§23 da belgilash katagi topilmadi"
    return rows


def _pg_s4_row() -> str:
    """`01` §3 «Product Goals» jadvalidagi PG-S4 qatori.

    Maqsad §3 da, mezon esa §23 da — ikkovi hujjatning ikki uchida
    yashaydi va aynan shuning uchun bog'lanmagan edi.
    """
    for line in _doc().splitlines():
        if line.strip().startswith("| PG-S4 "):
            return line
    raise AssertionError("`01` da PG-S4 qatori topilmadi")


# --- 1. Ro'yxatning tuzilishi ---


def test_section_has_exactly_seven_checkboxes() -> None:
    """Ro'yxat yopiq.

    Yangi qator qo'shilsa reyestr uni **jimgina** o'tkazib yuborardi:
    `evaluate()` faqat `CRITERIA` ni yuradi, ya'ni hisobot to'liq
    ko'rinib turib to'liq bo'lmasdi.
    """
    assert len(_checkboxes()) == SPEC_CRITERION_ROWS


def test_every_checkbox_is_a_criterion_verbatim_and_in_order() -> None:
    """Har qator reyestrda **so'zma-so'z** va **o'sha tartibda**.

    Tartib bu yerda ham ma'noli: hisobotni o'qiyotgan odam uni hujjat
    bilan yonma-yon qo'yadi, va qatorlar joy almashsa u tekshirishni
    to'xtatadi.
    """
    assert [c.phrase for c in acceptance.CRITERIA] == _checkboxes()


def test_registry_has_no_criterion_outside_the_document() -> None:
    """Reyestrda hujjatda yo'q qator bo'lmasligi kerak.

    Oldingi test uni qoplaydi (ro'yxatlar teng), lekin xato xabari
    boshqa: bu yerda «kod hujjatdan oldinga ketdi» deyiladi.
    """
    extra = sorted({c.phrase for c in acceptance.CRITERIA} - set(_checkboxes()))
    assert extra == [], f"hujjatda yo'q mezon: {extra}"


def test_criterion_codes_do_not_collide_with_gate_codes() -> None:
    """`03` §6 va `01` §23 — ikki xil o'q, kodlari aralashmasligi kerak.

    Ikkalasi ham «mezon» deb ataladi va ikkalasi ham `app/release/` da
    yashaydi. Bir xil kod ikki reyestrda uchrasa, hisobotni o'qigan
    odam gate mezonini mintaqa mezoni deb o'qishi mumkin edi.
    """
    collision = set(acceptance.CRITERION_BY_CODE) & set(gates.CRITERION_BY_CODE)
    assert collision == set(), f"kod ikkala reyestrda: {sorted(collision)}"


# --- 2. Sonlar hujjatdan ---


def test_control_sample_threshold_comes_from_the_document() -> None:
    """`≥50 точек` — son nasrda qolib ketmasligi kerak."""
    row = acceptance.CRITERION_BY_CODE["control_sample"].phrase
    found = re.search(r"≥\s*(\d+)\s+точек", row)
    assert found, f"§23 2-qatorida namuna hajmi topilmadi: {row!r}"
    assert acceptance.MIN_CONTROL_SAMPLE == int(found.group(1))


def test_showcase_target_comes_from_pg_s4() -> None:
    """PG-S4 ning maqsadi — `100% витрин с индексом покрытия`.

    Ulush aynan shu qatordan olinadi: `01` §23 ning 4-qatori «на всех
    витринах» deydi, lekin **o'lchovni** §4 beradi. Ikkovini
    ajratib qo'yish 4-qatorni «bor/yo'q» savoliga aylantirardi.
    """
    row = _pg_s4_row()
    assert "витрин" in row and "индексом покрытия" in row, row
    found = re.search(r"(\d+)%\s+витрин", row)
    assert found, f"PG-S4 qatorida ulush topilmadi: {row!r}"
    assert acceptance.REQUIRED_SHOWCASE_SHARE == int(found.group(1)) / 100


# --- 3. Bog'lanishlar haqiqiy simvolga yechiladi ---


def _resolve(target: str) -> object:
    module_name, _, attr_path = target.partition(":")
    module = __import__(module_name, fromlist=["_"])
    obj: object = module
    for part in attr_path.split("."):
        obj = getattr(obj, part)
    return obj


def test_every_bind_resolves_to_a_real_symbol() -> None:
    """`binds` — havola emas, **yechiladigan** simvol.

    Modulni qayta nomlash yoki simvolni o'chirish reyestrni jimgina
    yolg'onchi qilardi: qator «bajarilgan» bo'lib qolaverardi.
    """
    for criterion in acceptance.CRITERIA:
        for target in criterion.binds:
            assert _resolve(target) is not None, f"{criterion.code}: {target}"


def test_manual_criterion_binds_to_nothing() -> None:
    """`MANUAL` — dalil tizimdan tashqarida.

    Reyestrning o'z tekshiruvi (`_check_registry`) buni import paytida
    ushlaydi; bu yerda **holat** qulflanadi: nazorat namunasi bugun
    hech qayerda saqlanmaydi, va u saqlanadigan bo'lsa mezon
    `MANUAL` bo'lishdan to'xtaydi.
    """
    manual = [c for c in acceptance.CRITERIA if c.evidence is acceptance.Evidence.MANUAL]
    assert [c.code for c in manual] == ["control_sample"]
    assert manual[0].binds == ()


# --- 4. Vitrina reyestri — bayroq emas, dalil ---


def _heat_legend_block(html: str) -> str:
    """`#heat-legend` `<div>` ining ichi, ichma-ich `<div>` lar bilan.

    Birinchi `</div>` ni olish yetarli emas: blokning ichida
    `.ramp` va `.ramp-labels` bor, ya'ni sodda qidiruv qamrov
    qatorini blokdan tashqarida deb ko'rsatardi — va test aynan
    o'sha qator ichidami degan savolga javob beradi.
    """
    start = html.index('<div id="heat-legend"')
    depth = 0
    for match in re.finditer(r"<div\b|</div>", html[start:]):
        depth += 1 if match.group().startswith("<div") else -1
        if depth == 0:
            return html[start : start + match.end()]
    raise AssertionError("`#heat-legend` yopilmagan")


def test_api_showcases_really_carry_the_index_and_the_maturity_note() -> None:
    """`shows_index=True` javob modelining maydoni bilan isbotlanadi.

    Bayroqni tekshirish o'zini tekshirish bo'lardi: `CoverageOut`
    javobdan olib tashlansa reyestr baribir «bor» deb turardi.
    """
    models = {"stats_api": StatsOut, "heatmap_api": HeatCollection}
    for code, model in models.items():
        showcase = acceptance.SHOWCASE_BY_CODE[code]
        fields = set(model.model_fields)
        assert showcase.shows_index == ("coverage" in fields), code
        assert showcase.shows_maturity == ("maturity" in fields), code


def test_csv_export_really_carries_the_index_and_the_maturity_note() -> None:
    """CSV — jurnalist qo'liga tushadigan vitrina (`03` §R1.2)."""
    showcase = acceptance.SHOWCASE_BY_CODE["stats_export"]
    assert showcase.shows_index == ("coverage_index" in export.HEADER)
    # Chuqurlik pometasi ustun emas, izoh qatori: CSV ning boshida
    # `# <sarlavha>: <matn>` bo'lib chiqadi (`stats/export.py`).
    source = inspect.getsource(export)
    assert showcase.shows_maturity == ("region_maturity" in source)


def test_map_endpoint_carries_neither() -> None:
    """`GET /api/v1/map` — indekssiz, va bu **holat**, kamchilik emas.

    Javob `map_snapshot` dan o'qiladi (`05` §7.1), snapshot esa
    GeoJSON: unda hududning indeksi uchun joy yo'q. Test buni
    qulflaydi — indeks qo'shilgan kuni reyestr ham yangilanishi kerak.
    """
    showcase = acceptance.SHOWCASE_BY_CODE["map_api"]
    assert showcase.shows_index is False
    assert showcase.shows_maturity is False
    assert set(snapshot.empty_payload("samarkand")) == {"type", "region", "features"}
    # Ikkala qatlam ham: javobning o'zi (`05` §7.1 sxemasi) va har bir
    # hodisaning xossalari. Indeks ikkovidan birortasida ham yo'q.
    for fields in (set(MapCollection.model_fields), set(OutageProperties.model_fields)):
        assert "coverage" not in fields
        assert "maturity" not in fields


def test_public_page_hides_the_index_behind_the_density_toggle() -> None:
    """Sahifada indeks **bor**, lekin standart ko'rinishda ko'rinmaydi.

    Bu — running asosiy topilmasi va uni faqat fayllarni o'qib
    isbotlash mumkin: `#heat-coverage` `#heat-legend` blokining
    **ichida**, blok `hidden` atributi bilan boshlanadi va
    `heatOn` bayrog'i `false` dan boshlanadi. Ya'ni odam zichlik
    qatlamini qo'lda yoqmaguncha `01` PG-S4 bajarilmaydi.
    """
    showcase = acceptance.SHOWCASE_BY_CODE["web_default"]
    assert showcase.shows_index is False
    assert showcase.shows_maturity is False

    html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    block = _heat_legend_block(html)
    assert "hidden" in block.split(">", 1)[0], "`#heat-legend` yashirin emas"
    for anchor in ('id="heat-coverage"', 'id="heat-maturity"'):
        assert anchor in block, f"{anchor} endi `#heat-legend` ichida emas"

    js = (WEB_DIR / "app.js").read_text(encoding="utf-8")
    assert re.search(r"\bvar\s+heatOn\s*=\s*false\b", js), "`heatOn` endi `false` dan boshlanmaydi"
    # Ikkala qator ham **faqat** `refreshHeat` dan to'ldiriladi.
    for call in ("showCoverage(", "showMaturity("):
        assert js.count(call) == 2, f"{call} chaqiruvlari soni o'zgardi"


def test_index_share_is_below_the_target_and_the_criterion_is_unmet() -> None:
    """PG-S4 bugun bajarilmagan — hisobotda ham shunday ko'rinadi."""
    assert acceptance.index_share() < acceptance.REQUIRED_SHOWCASE_SHARE
    result = acceptance.evaluate()
    unmet = {item.criterion.code for item in result.unmet}
    assert "coverage_index_on_showcases" in unmet


def test_maturity_shares_the_same_gap_as_the_index() -> None:
    """§23 ning 4- va 7-qatori bitta sababdan yiqiladi.

    Ikkalasi ham `#heat-legend` ichida. Ulushlar ajralib ketsa — bu
    odam ko'rishi kerak bo'lgan hodisa: demak biri tuzatilgan,
    ikkinchisi unutilgan.
    """
    assert acceptance.maturity_share() == acceptance.index_share()
    unmet = {item.criterion.code for item in acceptance.evaluate().unmet}
    assert {"coverage_index_on_showcases", "young_region_disclaimer"} <= unmet


def test_every_showcase_without_the_index_says_why() -> None:
    missing = acceptance.showcases_without_index()
    assert {s.code for s in missing} == {"map_api", "web_default"}
    assert all(s.why_missing for s in missing)


# --- 5. Delegatsiya nusxa emas ---


def test_metrics_region_label_follows_monitoring(monkeypatch: pytest.MonkeyPatch) -> None:
    """6-qator `01` §22 ning birinchi qatoriga **bog'langan**, ko'chirilmagan.

    Test `monitoring` ning talabiga to'siq qo'yadi va shu bilan
    §23 ning qatori ham yiqilishini kutadi. Ikkinchi, mustaqil
    yozilgan tekshiruv bu testni o'tkazib yuborardi — va aynan shu
    57-run topgan siljish sinfi.
    """
    assert acceptance.metrics_labelled_region() is True

    held = monitoring.REQUIREMENT_BY_CODE["region_label"]
    obstacle = monitoring.Obstacle(
        code="test_only",
        unblocks=monitoring.Unblocks.SPEC,
        why="sun'iy to'siq",
    )
    monkeypatch.setitem(
        monitoring.REQUIREMENT_BY_CODE,
        "region_label",
        replace(held, obstacles=(obstacle,)),
    )
    assert acceptance.metrics_labelled_region() is False
    unmet = {item.criterion.code for item in acceptance.evaluate().unmet}
    assert "metrics_region_label" in unmet


def test_insufficient_data_verdict_is_bound_to_the_catalog() -> None:
    """5-qator uch qatlamda: verdikt, kalit, matn.

    Faqat `AreaVerdict` a'zosini tekshirish yetarli emas — verdikt
    bor-u kaliti yo'q bo'lsa foydalanuvchi bo'sh javob olardi.
    """
    assert acceptance.insufficient_data_verdict_present() is True
    key = lookup.MESSAGE_KEYS[lookup.AreaVerdict.NOT_ENOUGH_DATA]
    for lang in i18n.SUPPORTED_LANGUAGES:
        assert i18n.t(key, lang) != key, f"{lang}: matn yo'q"


def test_young_region_warning_key_exists_in_both_catalogs() -> None:
    for lang in i18n.SUPPORTED_LANGUAGES:
        assert i18n.t(maturity.WARNING_YOUNG, lang) != maturity.WARNING_YOUNG


def test_uz_catalog_is_complete() -> None:
    """3-qator: «непереведённых строк нет»."""
    assert acceptance.uz_catalog_complete() is True
    assert i18n.missing_keys("uz") == set()


def test_uz_criterion_really_reads_the_catalog(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ijobiy javob `return True` bo'lib qolmasligi kerak.

    Katalog bugun to'liq, ya'ni «to'liq» degan javob **har qanday**
    ishlanmadan chiqadi — shu jumladan hech narsa o'qimaydiganidan.
    Test bo'shliqni sun'iy yaratadi va mezon uni ko'rishini kutadi.
    """
    monkeypatch.setattr(acceptance.i18n, "missing_keys", lambda lang: {"app.disclaimer"})
    assert acceptance.uz_catalog_complete() is False
    unmet = {item.criterion.code for item in acceptance.evaluate().unmet}
    assert "uz_interface" in unmet


def test_verdict_criterion_really_reads_the_verdict(monkeypatch: pytest.MonkeyPatch) -> None:
    """5-qator uchun ham o'sha sabab: bugungi javob «ha».

    Kalit `MESSAGE_KEYS` dan olib tashlansa mezon yiqilishi kerak —
    aks holda u verdiktning **mavjudligini** emas, o'z qaytish
    qiymatini tekshirardi.
    """
    gone = lookup.AreaVerdict.NOT_ENOUGH_DATA
    without = {k: v for k, v in lookup.MESSAGE_KEYS.items() if k is not gone}
    monkeypatch.setattr(acceptance.lookup, "MESSAGE_KEYS", without)
    assert acceptance.insufficient_data_verdict_present() is False

    # Ikkinchi holat va u birinchisidan **farq qiladi**: kalit bor,
    # lekin u hech qaysi katalogda yo'q. `missing_keys` uni ko'rmaydi
    # (u faqat standart katalogdagi kalitni tarjimasi bilan
    # solishtiradi), ya'ni bu yo'lni faqat `all_keys` ushlaydi.
    dangling = dict(lookup.MESSAGE_KEYS) | {gone: "area.no_such_key"}
    monkeypatch.setattr(acceptance.lookup, "MESSAGE_KEYS", dangling)
    assert acceptance.insufficient_data_verdict_present() is False


# --- 6. Ikkita o'q: mintaqa va kod ---


def test_only_two_criteria_are_about_the_region() -> None:
    """Ro'yxatning asosiy xossasi: yettitadan **ikkitasi** mintaqa haqida.

    Qolgan beshtasi kodning tuzilishi haqida, ya'ni ikkinchi mintaqada
    tekinga bajariladi. Bu son o'zgarsa — modulning butun izohi
    qayta yozilishi kerak.
    """
    by_scope: dict[acceptance.Scope, list[str]] = {}
    for criterion in acceptance.CRITERIA:
        by_scope.setdefault(criterion.scope, []).append(criterion.code)
    assert by_scope[acceptance.Scope.REGION] == ["boundaries_loaded", "control_sample"]
    assert len(by_scope[acceptance.Scope.CODEBASE]) == 5


def test_today_every_met_criterion_is_a_restatement() -> None:
    """Bugungi holat: bajarilgan uchala qator ham `CODEBASE`.

    Ya'ni ikkinchi mintaqa uchun yurgizilgan ro'yxat **bittasini ham**
    yangi tekshirmaydi. Aynan shu G-8 tayanadigan joy, va aynan shu
    «3/7 yashil» degan xulosaning narxi.
    """
    result = acceptance.evaluate()
    assert result.met_count == result.restated_count
    assert all(item.status is not gates.CriterionStatus.MET for item in result.region_questions)


def test_region_questions_are_unmeasured_today() -> None:
    result = acceptance.evaluate()
    assert {item.criterion.code for item in result.unmeasured} == {
        "boundaries_loaded",
        "control_sample",
    }


def test_boundaries_criterion_names_its_human_blocker() -> None:
    """1-qatorni mahalla poligonlari ushlab turibdi (H-5).

    To'siq reyestrda turishi shart: usiz qator shunchaki
    «o'lchanmagan» bo'lib ko'rinardi va o'lchov yozish kifoya
    degan taassurot qolardi.
    """
    criterion = acceptance.CRITERION_BY_CODE["boundaries_loaded"]
    assert criterion.blocked_by
    assert any("mahalla" in reason.lower() for reason in criterion.blocked_by)


def test_region_is_not_accepted_today() -> None:
    assert acceptance.evaluate().is_accepted is False


# --- 7. Reyestrning o'z tekshiruvlari ---


def test_evaluate_rejects_unknown_codes() -> None:
    with pytest.raises(ValueError, match="notanish mezon kodi"):
        acceptance.evaluate({"control_samples": True})


def test_evaluate_rejects_structural_overrides() -> None:
    """`STRUCTURAL` qatorni tashqaridan «bajarildi» deb bo'lmaydi.

    Bu hisobotni soxtalashtirishning eng arzon yo'li bo'lardi:
    `evaluate({"coverage_index_on_showcases": True})` PG-S4 ni bir
    chaqiruv bilan yopardi.
    """
    with pytest.raises(ValueError, match="tashqaridan berilmaydi"):
        acceptance.evaluate({"coverage_index_on_showcases": True})


def test_runtime_criterion_can_be_answered_by_the_caller() -> None:
    result = acceptance.evaluate({"boundaries_loaded": True, "control_sample": False})
    statuses = {item.criterion.code: item.status for item in result.criteria}
    assert statuses["boundaries_loaded"] is gates.CriterionStatus.MET
    assert statuses["control_sample"] is gates.CriterionStatus.UNMET


def test_structural_criteria_and_checks_stay_in_sync() -> None:
    """Tekshiruvsiz qolgan `STRUCTURAL` qator import paytida yiqiladi.

    Aks holda `evaluate` uni jimgina `UNMEASURED` deb ko'rsatardi,
    ya'ni bugun javobi **bor** qator hisobotdan yo'qolardi.
    """
    structural = {
        c.code for c in acceptance.CRITERIA if c.evidence is acceptance.Evidence.STRUCTURAL
    }
    assert structural == set(acceptance.STRUCTURAL_CHECKS)


# --- 8. O'lchanmagan qatlamlar (159-run) ---------------------------------
#
# 70-run bu modulni «20 mutatsiya, 0 survivor» deb yopgan, lekin o'sha
# harness `returncode != 0` ni KILLED deb o'qirdi (`pytest` ning `rc=4`
# i yolg'on hisoblanardi; tuzatilgani 126-run). Qayta o'lchov: **64
# mutatsiya → 24 KILLED, 40 SURVIVOR**. Quyidagi bo'lim o'ttiz
# sakkiztasini qulflaydi; ikkitasi ekvivalent va `PROGRESS.md` da
# nomlangan.
#
# Survivorlarning uchta oilasi bor va uchalasi ham bitta sababdan:
# **bugungi ma'lumot ikkita shartni ajratmaydi**.
#
# 1. `shows_index` va `shows_maturity` beshala vitrinada bir xil, ya'ni
#    `index_share`, `maturity_share` va `showcases_without_index`
#    o'zaro almashtirilsa hech narsa o'zgarmasdi;
# 2. UZ va RU kataloglari ikkalasi ham to'liq, ya'ni `all(...)` ni
#    `any(...)` ga almashtirish ko'rinmasdi;
# 3. `_check_registry` ning **oltita** tarmog'i hech qachon otilmagan —
#    reyestr to'g'ri bo'lgani uchun. Qorovul otilmasa, u yo'q.


def _showcases(*flags: tuple[bool, bool]) -> tuple[acceptance.Showcase, ...]:
    """Sun'iy vitrina reyestri: har qator uchun `(indeks, chuqurlik)`.

    Haqiqiy reyestrda ikkala bayroq ham hamma qatorda teng, ya'ni u
    `index_share` ni `maturity_share` dan **ajratmaydi**. Bu fikstyura
    aynan shuning uchun bor.
    """
    return tuple(
        acceptance.Showcase(
            code=f"s{number}",
            spec="01 §23",
            where="app.release.acceptance:SPEC",
            shows_index=shows_index,
            shows_maturity=shows_maturity,
            why_missing="" if shows_index else "sinov fikstyurasi",
        )
        for number, (shows_index, shows_maturity) in enumerate(flags)
    )


#: Indeks to'liq (2/2), chuqurlik emas (1/2).
FULL_INDEX = ((True, True), (True, False))
#: Chuqurlik to'liq (2/2), indeks emas (1/2).
FULL_MATURITY = ((True, True), (False, True))


def _criterion(**overrides: object) -> acceptance.Criterion:
    base: dict[str, object] = {
        "code": "synthetic",
        "scope": acceptance.Scope.CODEBASE,
        "evidence": acceptance.Evidence.RUNTIME,
        "phrase": "sun'iy qator",
    }
    return acceptance.Criterion(**(base | overrides))  # type: ignore[arg-type]


def _result(
    code: str, status: gates.CriterionStatus, scope: acceptance.Scope
) -> acceptance.CriterionResult:
    return acceptance.CriterionResult(criterion=_criterion(code=code, scope=scope), status=status)


# 8.1. Lug'at: `StrEnum` qiymatlari va reyestrning manzili


def test_scope_and_evidence_values_are_locked() -> None:
    """Ikkala o'qning ham qiymatlari hech qayerda o'lchanmagan edi.

    `StrEnum` ning qiymati — modulning **lug'ati**: u `admin/registries`
    orqali vitrinaga chiqadi va hisobotni o'qigan odam aynan shu
    satrni ko'radi. A'zoni qayta nomlash `.name` ni o'zgartiradi va uni
    boshqa test ushlaydi; **qiymatni** o'zgartirish esa bugungacha
    jimgina o'tardi.
    """
    assert [(m.name, m.value) for m in acceptance.Scope] == [
        ("REGION", "region"),
        ("CODEBASE", "codebase"),
    ]
    assert [(m.name, m.value) for m in acceptance.Evidence] == [
        ("STRUCTURAL", "structural"),
        ("RUNTIME", "runtime"),
        ("MANUAL", "manual"),
    ]


def test_spec_names_the_section_these_tests_parse() -> None:
    """`SPEC` va testlar bitta bo'limga qarashi kerak.

    Ikkovi ajralib ketsa reyestr «§23 ni o'lchayapman» deb turib
    boshqa bo'limni nomlab qo'yardi — va aynan `registries.py`
    vitrinasida shu satr ko'rinadi.
    """
    number = ACCEPTANCE_SECTION.removeprefix("## ").split(".", 1)[0]
    assert acceptance.SPEC == f"01 §{number}"


# 8.2. Vitrinaning manzili — havola emas, tekshiriladigan joy

#: Vitrina `spec` ining hujjati.
SPEC_DOCS = {
    "01": "01_PRD_Samarkand.md",
    "03": "03_Development_Roadmap.md",
    "05": "05_Technical_Design.md",
}

#: Har vitrina indeks **qayerda** turishini (yoki qayerda yo'qligini)
#: nomlaydi. Manzil — reyestrning yagona tekshiriladigan qismi: uni
#: qo'shni simvolga siljitish `_resolve` uchun sezilmaydi (`StatsOut`
#: ham, `CoverageOut` ham mavjud), ya'ni faqat tenglik ushlaydi.
EXPECTED_WHERE = {
    "stats_api": "app.api.v1.stats:CoverageOut",
    "heatmap_api": "app.api.v1.heatmap:HeatCollection",
    "stats_export": "app.stats.export:HEADER",
    "map_api": "app.api.v1.map:MapCollection",
    "web_default": "web/index.html:#heat-coverage",
}


def test_every_showcase_spec_points_at_a_real_document_section() -> None:
    """`spec` — hujjatdagi sarlavha, dekoratsiya emas."""
    for showcase in acceptance.SHOWCASES:
        doc, _, section = showcase.spec.partition(" §")
        assert section, f"{showcase.code}: `{showcase.spec}` da bo'lim yo'q"
        text = (SVETA_ROOT.parent / SPEC_DOCS[doc]).read_text(encoding="utf-8")
        found = re.search(rf"^#+ {re.escape(section)}[ .—]", text, re.MULTILINE)
        assert found, f"{showcase.code}: `{showcase.spec}` bo'limi topilmadi"


def test_every_showcase_names_the_exact_symbol() -> None:
    assert {s.code: s.where for s in acceptance.SHOWCASES} == EXPECTED_WHERE


def test_every_showcase_address_resolves() -> None:
    """Manzil yechilishi ham kerak — jadval eskirmasin.

    Yuqoridagi tenglik jadvalning **o'zi** bilan siljib ketishi mumkin;
    bu test manzilni haqiqiy simvolga (yoki fayldagi selektorga)
    yechadi.
    """
    for showcase in acceptance.SHOWCASES:
        head, _, tail = showcase.where.partition(":")
        if head.startswith("app."):
            assert _resolve(showcase.where) is not None, showcase.code
        else:
            text = (SVETA_ROOT / head).read_text(encoding="utf-8")
            assert f'id="{tail.lstrip("#")}"' in text, showcase.code


def test_a_showcase_defaults_to_no_reason() -> None:
    """Standart `why_missing` **bo'sh**, «bo'shga o'xshagan» emas.

    Bitta probel qorovulni (`_check_registry`) va «sababini aytadimi»
    testini bir vaqtda so'ndirardi: ikkalasi ham rostlikni tekshiradi.
    """
    blank = acceptance.Showcase(
        code="x",
        spec="01 §23",
        where="app.release.acceptance:SPEC",
        shows_index=True,
        shows_maturity=True,
    )
    assert blank.why_missing == ""


# 8.3. Ulushlar o'z bayrog'ini o'qiydi


def test_index_share_reads_the_index_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(acceptance, "SHOWCASES", _showcases(*FULL_INDEX))
    assert acceptance.index_share() == 1.0
    assert acceptance.maturity_share() == 0.5


def test_maturity_share_reads_the_maturity_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(acceptance, "SHOWCASES", _showcases(*FULL_MATURITY))
    assert acceptance.maturity_share() == 1.0
    assert acceptance.index_share() == 0.5


def test_showcases_without_index_reads_the_index_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(acceptance, "SHOWCASES", _showcases((True, False), (False, True)))
    assert [s.code for s in acceptance.showcases_without_index()] == ["s1"]


# 8.4. i18n tekshiruvlari **har** katalogni talab qiladi


@pytest.mark.parametrize("broken", i18n.SUPPORTED_LANGUAGES)
def test_uz_criterion_fails_when_a_single_catalog_is_incomplete(
    monkeypatch: pytest.MonkeyPatch, broken: str
) -> None:
    """Bitta katalogning bo'shlig'i yetarli.

    Bugun ikkala katalog ham to'liq, ya'ni `all(...)` va `any(...)`
    bir xil javob beradi — shart tillar bo'yicha **ajratilmagan**.
    Parametr har tilni navbat bilan buzadi: shu bilan `any` ham,
    ro'yxatning qisqarishi ham ko'rinadi.
    """
    monkeypatch.setattr(
        acceptance.i18n,
        "missing_keys",
        lambda lang: {"app.disclaimer"} if lang == broken else set(),
    )
    assert acceptance.uz_catalog_complete() is False


@pytest.mark.parametrize("broken", i18n.SUPPORTED_LANGUAGES)
def test_verdict_criterion_fails_when_a_single_catalog_lacks_the_text(
    monkeypatch: pytest.MonkeyPatch, broken: str
) -> None:
    """5-qator uchun ham o'sha ajratma.

    Verdikt bor, kalit bor, lekin bitta tilda matn yo'q — foydalanuvchi
    o'sha tilda kalitning o'zini ko'radi.
    """
    key = lookup.MESSAGE_KEYS[lookup.AreaVerdict.NOT_ENOUGH_DATA]
    monkeypatch.setattr(
        acceptance.i18n,
        "missing_keys",
        lambda lang: {key} if lang == broken else set(),
    )
    assert acceptance.insufficient_data_verdict_present() is False


# 8.5. Chegara **aynan** maqsadda, va har mezon o'z ulushini o'qiydi


def test_disclaimer_is_active_exactly_at_the_target(monkeypatch: pytest.MonkeyPatch) -> None:
    """`>=` — `>` emas: 100% ning o'zi yetarli.

    Bugungi ulush (0.6) ikkala taqqoslash uchun ham `False`, ya'ni
    chegara **o'lchanmagan**. Fikstyura ulushni aynan maqsadga
    qo'yadi. Ikkinchi yarmi ulushni ajratadi: chuqurlik to'liq
    bo'lmasa mezon yopilmaydi, garchi indeks to'liq bo'lsa ham.
    """
    monkeypatch.setattr(acceptance, "SHOWCASES", _showcases(*FULL_MATURITY))
    assert acceptance.maturity_disclaimer_active() is True

    monkeypatch.setattr(acceptance, "SHOWCASES", _showcases(*FULL_INDEX))
    assert acceptance.maturity_disclaimer_active() is False


def test_disclaimer_needs_the_catalog_key_as_well(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ulush to'liq bo'lsa ham, matnsiz pometa «faol» emas."""
    monkeypatch.setattr(acceptance, "SHOWCASES", _showcases(*FULL_MATURITY))
    monkeypatch.setattr(acceptance.i18n, "all_keys", set)
    assert acceptance.maturity_disclaimer_active() is False


def test_index_criterion_is_met_exactly_at_the_target(monkeypatch: pytest.MonkeyPatch) -> None:
    """4-qatorning tekshiruvi uchun ham o'sha ikki qulf."""
    check = acceptance.STRUCTURAL_CHECKS["coverage_index_on_showcases"]

    monkeypatch.setattr(acceptance, "SHOWCASES", _showcases(*FULL_INDEX))
    assert check() is True

    monkeypatch.setattr(acceptance, "SHOWCASES", _showcases(*FULL_MATURITY))
    assert check() is False


# 8.6. `binds` — kortejning **har** elementi


#: `test_every_bind_resolves_to_a_real_symbol` mavjudlikni tekshiradi,
#: ya'ni kortejdan bitta element **jimgina** tushib qolardi. Bu jadval
#: dalilning to'liqligini qulflaydi.
EXPECTED_BINDS = {
    "boundaries_loaded": (
        "app.geo.queries:region_has_mahallas",
        "app.geo.quality:check_validity",
        "app.geo.quality:check_closed_rings",
        "app.geo.models:District.valid_from",
    ),
    "control_sample": (),
    "uz_interface": ("app.core.i18n:missing_keys",),
    "coverage_index_on_showcases": (
        "app.release.acceptance:SHOWCASES",
        "app.stats.coverage:CoverageIndex",
    ),
    "insufficient_data_verdict": (
        "app.clustering.lookup:AreaVerdict.NOT_ENOUGH_DATA",
        "app.clustering.lookup:MESSAGE_KEYS",
    ),
    "metrics_region_label": ("app.obs.monitoring:REQUIREMENT_BY_CODE",),
    "young_region_disclaimer": (
        "app.stats.maturity:WARNING_YOUNG",
        "app.release.acceptance:SHOWCASES",
    ),
}


def test_every_criterion_binds_exactly_what_the_registry_promises() -> None:
    assert {c.code: c.binds for c in acceptance.CRITERIA} == EXPECTED_BINDS


# 8.7. Qorovulning otilmagan tarmoqlari
#
# `_check_registry()` import paytida yuradi va reyestr to'g'ri, ya'ni
# **birorta ham** `raise` hech qachon bajarilmagan. Qorovulni
# kuchaytirish butun to'plamni collection error ga olib kelardi,
# shuning uchun u faqat zaiflashtiriladi — va zaiflashtirilganini
# faqat sun'iy buzilgan reyestr ko'radi.


def test_registry_guard_catches_a_duplicated_criterion_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    doubled = (*acceptance.CRITERIA, replace(acceptance.CRITERIA[-1], phrase="nusxa"))
    monkeypatch.setattr(acceptance, "CRITERIA", doubled)
    with pytest.raises(ValueError, match="mezon kodi takrorlangan"):
        acceptance._check_registry()


def test_registry_guard_catches_a_check_without_a_criterion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Yo'nalish muhim: **tekshiruv** ortiqcha bo'lgan holat.

    Teskari yo'nalishni (mezon ortiqcha) `!=` ni `>` ga almashtirgan
    mutant ham ushlaydi; faqat shu yo'nalish uni ajratadi.
    """
    monkeypatch.setattr(
        acceptance,
        "STRUCTURAL_CHECKS",
        dict(acceptance.STRUCTURAL_CHECKS) | {"ghost": lambda: True},
    )
    with pytest.raises(ValueError, match="STRUCTURAL mezonlar va tekshiruvlar mos emas"):
        acceptance._check_registry()


def test_registry_guard_catches_a_manual_criterion_that_binds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bound = replace(
        acceptance.CRITERION_BY_CODE["control_sample"],
        binds=("app.core.i18n:missing_keys",),
    )
    monkeypatch.setattr(
        acceptance,
        "CRITERIA",
        tuple(bound if c.code == "control_sample" else c for c in acceptance.CRITERIA),
    )
    with pytest.raises(ValueError, match="MANUAL mezon"):
        acceptance._check_registry()


def test_registry_guard_catches_a_duplicated_showcase_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    doubled = (*acceptance.SHOWCASES, replace(acceptance.SHOWCASES[0], spec="05 §7.1"))
    monkeypatch.setattr(acceptance, "SHOWCASES", doubled)
    with pytest.raises(ValueError, match="vitrina kodi takrorlangan"):
        acceptance._check_registry()


def test_registry_guard_catches_a_showcase_that_hides_the_index_in_silence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sababsiz indekssiz vitrina.

    Fikstyura `spec` ni **to'ldirilgan**, `shows_maturity` ni esa
    `True` qoldiradi: shu bilan qorovul aynan `shows_index` va
    `why_missing` juftligini o'qishi tekshiriladi.
    """
    silent = acceptance.Showcase(
        code="silent",
        spec="01 §23",
        where="app.release.acceptance:SPEC",
        shows_index=False,
        shows_maturity=True,
    )
    monkeypatch.setattr(acceptance, "SHOWCASES", (*acceptance.SHOWCASES, silent))
    with pytest.raises(ValueError, match="vitrina sababsiz indekssiz"):
        acceptance._check_registry()


# 8.8. Hisobotning shakli — bugungi ma'lumotdan ajratilgan
#
# `AcceptanceReport` — sof dataklass, ya'ni uni haqiqiy reyestrsiz ham
# qurish mumkin. Bugungi hisobda `met_count == restated_count` va
# `unmet` ichida `UNMEASURED` yo'q — ikkovi ham **tasodifan** shunday.


def test_unmet_holds_only_the_unmet_rows() -> None:
    report = acceptance.AcceptanceReport(
        criteria=(
            _result("a", gates.CriterionStatus.UNMET, acceptance.Scope.CODEBASE),
            _result("b", gates.CriterionStatus.UNMEASURED, acceptance.Scope.REGION),
            _result("c", gates.CriterionStatus.MET, acceptance.Scope.CODEBASE),
        )
    )
    assert [i.criterion.code for i in report.unmet] == ["a"]
    assert [i.criterion.code for i in report.unmeasured] == ["b"]
    assert [i.criterion.code for i in report.region_questions] == ["b"]


def test_restated_count_counts_only_the_met_codebase_rows() -> None:
    """Bugun `met_count == restated_count`, chunki bajarilgan uchala
    qator ham `CODEBASE`. Mintaqa qatori yopilgan kuni ikkovi ajraladi —
    va aynan o'sha kuni `restated_count` ma'noga ega bo'ladi.
    """
    report = acceptance.AcceptanceReport(
        criteria=(
            _result("region_met", gates.CriterionStatus.MET, acceptance.Scope.REGION),
            _result("codebase_met", gates.CriterionStatus.MET, acceptance.Scope.CODEBASE),
            _result("codebase_unmet", gates.CriterionStatus.UNMET, acceptance.Scope.CODEBASE),
        )
    )
    assert report.met_count == 2
    assert report.restated_count == 1
    assert report.is_accepted is False
