"""Metodologiya bo'limi — `03` §R1.2 «metodologiya bilan bog'lanish». Bazasiz.

`03` §R1.2 ning tarkibida to'rtta qator bor. Uchtasi o'lchanadi (uchala
kesim, Coverage Index, CSV), to'rtinchisi — metodologiya — 15-rundan beri
yozilmagan holda «✅» ko'rinardi. Bu fayl uni birinchi marta o'lchaydi.

**Nima aynan o'lchanadi.** Metodologiyaning butun ma'nosi shundaki, u
vitrinaning **haqiqiy** qiymatlarini ochadi. Ya'ni ikkita jim buzilish
mumkin va ikkalasi ham hech qanday xato bermaydi:

1. **Bo'lim kodning qiymatlaridan ajralib ketadi.** `region_config` da
   `confirm.coef` 0.5 dan 0.7 ga o'zgaradi, metodologiya esa 0.5 ni
   ko'rsatishda davom etadi — o'quvchi uchun bu oddiy xatodan yomonroq,
   chunki u **ochiqlik** niqobi ostida keladi. Shuning uchun quyidagi
   testlar qiymatlarni `Params` ning o'zidan qayta o'qiydi, faylga
   ikkinchi nusxa yozib qo'ymaydi.
2. **Versiya o'zgarishni o'tkazib yuboradi yoki uni o'ylab topadi.**
   Birinchisi `01` §347 dagi «уведомление о смене методологии» ni
   ishlamas qiladi, ikkinchisi esa har tarjima tuzatilganda soxta
   bildirishnoma berardi.

Endpointning o'zi (`GET /api/v1/stats/methodology`) `requires_db`, chunki
u mintaqani bazadan qidiradi; sathi esa
`tests/test_api_surface_contract.py` da bazasiz qulflangan. Bu yerda
javob **modellari** darajasida tekshiriladi: `methodology_out` toza
funksiya.
"""

from __future__ import annotations

import pytest

from app.api.v1 import stats as stats_api
from app.clustering import params as cluster_params
from app.core.config import settings
from app.core.i18n import SUPPORTED_LANGUAGES, t
from app.reports import sources as report_sources
from app.stats import aggregate, coverage, duration, methodology
from app.stats import service as stats_service
from tests.conftest import default_methodology

LIMITS = methodology.PublicLimits(
    h3_resolution=9,
    min_reports=3,
    time_rounding_min=5,
    coverage_window_days=30,
    target_penetration=0.02,
    autoclose_after_min=120,
)


def build(params: cluster_params.Params | None = None) -> methodology.Methodology:
    return methodology.build(params or cluster_params.DEFAULT_PARAMS, LIMITS)


def values_of(method: methodology.Methodology) -> dict[str, str]:
    """Barcha bo'limlarning qiymatlari — bitta `{kod: qiymat}` jadvali."""
    return {value.code: value.value for section in method.sections for value in section.values}


# --------------------------------------------------------------------------
# Bo'limning tuzilishi
# --------------------------------------------------------------------------


def test_every_declared_section_is_built() -> None:
    """`SECTION_ORDER` — ro'yxat emas, **va'da**.

    Bo'lim ro'yxatga qo'shilib, quruvchisi yozilmasa `build` yiqiladi;
    teskarisi ham bo'lmasligi kerak — qurilgan, lekin ko'rsatilmaydigan
    bo'lim javobga umuman tushmasdi.
    """
    assert tuple(s.code for s in build().sections) == methodology.SECTION_ORDER


def test_section_order_is_what_actually_governs_the_output(monkeypatch) -> None:
    """Tartibni `SECTION_ORDER` belgilaydi, quruvchilar jadvali emas.

    Bugun ikkalasi bir xil, ya'ni farq **ko'rinmaydi**: `dict` qo'shilish
    tartibini saqlaydi. Ertaga quruvchilar joy almashsa, `SECTION_ORDER`
    esa o'sha qolsa — javob jimgina boshqa tartibda chiqardi va yagona
    manba qaysiligi noaniq bo'lib qolardi. Shuning uchun ro'yxat
    o'zgartiriladi va javob unga ergashishi tekshiriladi.
    """
    reversed_order = tuple(reversed(methodology.SECTION_ORDER))
    monkeypatch.setattr(methodology, "SECTION_ORDER", reversed_order)
    assert tuple(s.code for s in build().sections) == reversed_order


def test_a_built_but_unlisted_section_is_an_error(monkeypatch) -> None:
    """Ro'yxatga tushmagan bo'lim javobga umuman kirmasdi.

    `builders[code]` faqat teskari xatoni ushlaydi: ro'yxatda bor,
    quruvchisi yo'q. Bu yo'nalish esa jim — bo'lim yozilgan, tarjima
    qilingan va hech qachon ko'rsatilmagan bo'lardi.
    """
    monkeypatch.setattr(methodology, "SECTION_ORDER", methodology.SECTION_ORDER[:-1])
    with pytest.raises(ValueError, match="ko'rsatilmaydi"):
        build()


def test_sections_keep_the_declared_order() -> None:
    """Tartib ma'noli: manba → hodisa → vitrina → cheklov.

    Bu ko'rinish qarori, shuning uchun u versiyaga **ta'sir qilmaydi**
    (`test_display_order_does_not_change_the_version`), lekin javobda
    barqaror bo'lishi kerak: `dict` ustidan yurish tartibi o'zgarsa
    bo'limlar har so'rovda joy almashardi.
    """
    order = methodology.SECTION_ORDER
    assert order[0] == "sources", "avval xabar qayerdan kelishi"
    assert order[-1] == "privacy", "oxirida nima chiqmasligi"


def test_no_section_is_empty() -> None:
    """Hech narsa ochmaydigan sarlavha — ochiqlikning ko'rinishi."""
    for section in build().sections:
        assert section.values, section.code


def test_an_empty_section_is_an_error_not_a_silent_skip(monkeypatch) -> None:
    """Bo'sh bo'lim jimgina tushib qolmasin.

    Bu holat nazariy emas: `SOURCES` bo'shab qolsa (masalan registrni
    bazadan o'qishga o'tkazilsa va u to'ldirilmasa) metodologiya
    «manbalar» sarlavhasini ko'rsatib, ostida hech narsa yozmasdi.
    """
    empty = methodology.MethodologySection(
        code="sources", spec=methodology.SECTION_SPEC["sources"], values=()
    )
    monkeypatch.setattr(methodology, "_sources_section", lambda: empty)
    with pytest.raises(ValueError, match="bo'sh"):
        methodology.build(cluster_params.DEFAULT_PARAMS, LIMITS)


def test_every_section_names_its_source_document() -> None:
    """`spec` — o'quvchi uchun birlamchi manbaga ko'rsatkich."""
    for section in build().sections:
        assert section.spec == methodology.SECTION_SPEC[section.code]
        assert section.spec.strip(), section.code


def test_values_are_sorted_by_code() -> None:
    """Saralash barqarorlik uchun, ko'rinish uchun emas."""
    for section in build().sections:
        codes = [value.code for value in section.values]
        assert codes == sorted(codes), section.code


# --------------------------------------------------------------------------
# Qiymatlar jonli manbadan keladimi
# --------------------------------------------------------------------------


def test_confirmation_values_come_from_the_live_params() -> None:
    """`06` §4 — chegara `region_config` dan, koddagi nusxadan emas.

    Bu testning butun ma'nosi shu: parametr o'zgartirilib, bo'lim eski
    sonni ko'rsatishda davom etsa — metodologiya yolg'on gapiradi.
    """
    tuned = cluster_params.from_mapping({"confirm.coef": 0.9, "confirm.ceil": 12})
    values = values_of(build(tuned))
    assert values["confirm.coef"] == "0.9"
    assert values["confirm.ceil"] == "12"


def test_scale_and_guard_values_come_from_the_live_params() -> None:
    """`06` §5 — masshtab narvoni ham, qamrov to'sig'i ham."""
    tuned = cluster_params.from_mapping(
        {"scale.cell_ratio_district": 0.44, "guard.min_active_mahalla": 7}
    )
    values = values_of(build(tuned))
    assert values["scale.cell_ratio_district"] == "0.44"
    assert values["guard.min_active_mahalla"] == "7"


def test_source_weights_come_from_the_registry() -> None:
    """`06` §2 — og'irliklar `SOURCES` dan, qayta yozilgan ro'yxatdan emas."""
    values = values_of(build())
    for source in report_sources.SOURCES:
        assert values[f"source.{source.code}"] == methodology._fmt(source.weight)


def test_the_user_factor_band_is_disclosed_with_the_weights() -> None:
    """`06` §2.1 — og'irlik yakuniy son emas, u `user_factor` ga ko'paytiriladi.

    Faqat manba og'irliklarini ko'rsatish yarim ochiqlik bo'lardi:
    o'quvchi «moderator = 3.0» ni ko'rib, haqiqatda xabar 1.2 dan 4.8
    gacha vazn olishini bilmasdi. Uchala son ham `sources` modulidan
    o'qiladi — bu yerda qayta yozilsa, ular ajralib ketishi mumkin
    bo'lgan yagona joy aynan shu bo'lardi.
    """
    values = values_of(build())
    assert values["user_factor.divisor"] == methodology._fmt(report_sources.TRUST_DIVISOR)
    assert values["user_factor.min"] == methodology._fmt(report_sources.USER_FACTOR_MIN)
    assert values["user_factor.max"] == methodology._fmt(report_sources.USER_FACTOR_MAX)
    # Uchtasi ham har xil: teng bo'lsa ularni joy almashtirib qo'ygan
    # xatolik yuqoridagi uchala qatordan ham o'tib ketardi.
    trio = {values["user_factor.divisor"], values["user_factor.min"], values["user_factor.max"]}
    assert len(trio) == 3


def test_authoritative_sources_stay_in_the_list_with_their_zero() -> None:
    """Nol og'irlik «ishlatilmaydi» degani emas (`06` §2.2).

    Rasmiy manba og'irlikli hisobdan tashqarida, lekin hodisani darhol
    tasdiqlaydi. Ro'yxatdan tushib qolsa o'quvchi rasmiy e'lon umuman
    hisobga olinmaydi deb o'ylardi.
    """
    values = values_of(build())
    authoritative = [s for s in report_sources.SOURCES if s.is_authoritative]
    assert authoritative, "registrda rasmiy manba qolmadi — test tayanchsiz"
    for source in authoritative:
        assert values[f"source.{source.code}"] == "0"


def test_coverage_bands_come_from_the_coverage_module() -> None:
    """`medium` so'zi nimani anglatishini o'quvchi javobdan bilsin."""
    values = values_of(build())
    for threshold, band in coverage.BAND_THRESHOLDS:
        assert values[f"coverage.band.{band}"] == str(threshold)


def test_duration_ladder_and_method_are_disclosed() -> None:
    """`01` §4 — «P90» so'zi bitta ma'noni anglatishi uchun usul ham chiqadi."""
    values = values_of(build())
    for index, edge in enumerate(duration.BAND_EDGES):
        assert values[f"duration.edge_{index}"] == str(edge)
    assert values["duration.percentile_method"] == "percentile_cont"
    assert values["duration.min_sample"] == str(duration.MIN_SAMPLE)


def test_reconciliation_threshold_comes_from_aggregate() -> None:
    """`03` §R1.2 chiqish mezoni — ≤5%."""
    values = values_of(build())
    assert values["stats.max_unassigned_ratio"] == methodology._fmt(aggregate.MAX_UNASSIGNED_RATIO)


def test_privacy_limits_come_from_the_caller() -> None:
    """`05` §3.1, §7.3 — nima chiqmaydi."""
    values = values_of(build())
    assert values["geo.h3_resolution"] == str(LIMITS.h3_resolution)
    assert values["public.min_reports"] == str(LIMITS.min_reports)
    assert values["public.time_rounding_min"] == str(LIMITS.time_rounding_min)


def test_the_module_holds_no_second_copy_of_a_number() -> None:
    """Modul qiymatni o'zi o'ylab topmasin.

    Bu yagona **strukturaviy** tekshiruv: metodologiyaning butun qiymati
    qiymatlar boshqa joydan kelishida, ya'ni faylda raqamli literal
    paydo bo'lishi — aynan o'sha ikkinchi nusxaning boshlanishi.
    Ruxsat etilgani: `VERSION_BYTES` (daydjest uzunligi, metodologiya
    emas) va `_fmt` ning ichidagi yo'q — u raqam ishlatmaydi.
    """
    import ast
    import pathlib

    source = pathlib.Path(methodology.__file__).read_text(encoding="utf-8")
    numbers = [
        node.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    ]
    assert numbers == [methodology.VERSION_BYTES], (
        f"`methodology.py` da kutilmagan raqamli literal: {numbers} — "
        "qiymat manbadan o'qilishi kerak, bu yerda qayta yozilmasligi"
    )


# --------------------------------------------------------------------------
# Kanonik shakl
# --------------------------------------------------------------------------


def test_integral_floats_lose_their_point() -> None:
    """`3` va `3.0` — bitta parametr qiymati.

    `from_mapping` hamma narsani `float` orqali o'tkazadi, ya'ni bu
    holat nazariy emas: nuqta saqlanib qolsa bir xil konfiguratsiya
    ikki xil versiya berardi.
    """
    assert methodology._fmt(3.0) == "3"
    assert methodology._fmt(3) == "3"
    assert methodology._fmt(0.5) == "0.5"


def test_the_same_config_written_two_ways_gives_one_version() -> None:
    """Yuqoridagi qoidaning versiyaga tegishli natijasi."""
    a = build(cluster_params.from_mapping({"confirm.floor": 4}))
    b = build(cluster_params.from_mapping({"confirm.floor": 4.0}))
    assert a.version == b.version


# --------------------------------------------------------------------------
# Versiya
# --------------------------------------------------------------------------


def test_version_is_stable_for_the_same_values() -> None:
    assert build().version == build().version


def test_version_is_deterministic_across_processes() -> None:
    """`blake2b`, `hash()` emas (`CLAUDE.md` §2).

    Qiymat qotirilgan: `hash()` ga qaytilsa yoki `digest_size`
    o'zgarsa, ikkita `sveta-api` konteyneri bir xil konfiguratsiyada
    turli versiya ko'rsatardi va `01` §347 bildirishnomasi shovqinga
    aylanardi. Test aynan shu regressiyani ushlaydi, uzunlikni emas.
    """
    section = methodology.MethodologySection(
        code="demo",
        spec="06 §4",
        values=(methodology.MethodologyValue(code="a", value="1"),),
    )
    assert methodology.version((section,)) == "596fc5d715f89de0"


def test_version_changes_when_a_parameter_changes() -> None:
    """`01` §347 — metodologiya o'zgarganini odam ko'rishi kerak."""
    tuned = cluster_params.from_mapping({"confirm.coef": 0.9})
    assert build(tuned).version != build().version


def test_version_changes_when_a_deploy_level_limit_changes() -> None:
    """`region_config` dan tashqaridagi qiymat ham metodologiyaning qismi."""
    other = methodology.build(
        cluster_params.DEFAULT_PARAMS,
        methodology.PublicLimits(
            h3_resolution=LIMITS.h3_resolution,
            min_reports=LIMITS.min_reports + 1,
            time_rounding_min=LIMITS.time_rounding_min,
            coverage_window_days=LIMITS.coverage_window_days,
            target_penetration=LIMITS.target_penetration,
            autoclose_after_min=LIMITS.autoclose_after_min,
        ),
    )
    assert other.version != build().version


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_version_ignores_the_translation(lang: str) -> None:
    """Tarjimadagi vergul — metodologiya o'zgargani emas.

    Aks holda har matn tuzatilganda soxta «metodologiya o'zgardi»
    bildirishnomasi ketardi va odam ularga ishonishni to'xtatardi.

    Tekshiruv to'g'ridan-to'g'ri: daydjest olinadigan matnda katalogdan
    kelgan **birorta** satr bo'lmasligi kerak. Tarjimani vaqtincha
    o'zgartirib solishtirish ham mumkin edi, lekin u faqat bugungi
    ulanishni o'lchardi; bu esa qoidani o'lchaydi.
    """
    canonical = methodology._canonical(build().sections)
    for key in (methodology.TITLE_KEY, *methodology.SECTION_KEYS):
        assert t(key, lang) not in canonical, key


def test_display_order_does_not_change_the_version() -> None:
    """Ko'rsatish tartibi metodologiya emas."""
    sections = build().sections
    assert methodology.version(sections) == methodology.version(tuple(reversed(sections)))


def test_version_notices_a_moved_source_reference() -> None:
    """Qiymat o'sha qolib, uning bandi ko'chgan bo'lsa — bu ham o'zgarish."""
    base = methodology.MethodologySection(
        code="demo",
        spec="06 §4",
        values=(methodology.MethodologyValue(code="a", value="1"),),
    )
    moved = methodology.MethodologySection(
        code="demo",
        spec="06 §5",
        values=base.values,
    )
    assert methodology.version((base,)) != methodology.version((moved,))


def test_version_is_a_short_readable_label() -> None:
    """Uni odam ko'z bilan solishtiradi, ya'ni 64 bayt ortiqcha."""
    version = build().version
    assert len(version) == methodology.VERSION_BYTES * 2
    assert version == version.lower()
    assert all(char in "0123456789abcdef" for char in version)


# --------------------------------------------------------------------------
# i18n
# --------------------------------------------------------------------------


def test_section_keys_cover_every_section_in_both_parts() -> None:
    """`SECTION_KEYS` — `KEY_TABLES` ning tayanchi.

    U `SECTION_ORDER` dan chiqadi, ya'ni yangi bo'lim qo'shilishi bilan
    kalitlar ro'yxati o'zi kengayadi va tarjimasi darhol talab qilinadi.
    """
    for section in build().sections:
        assert section.title_key in methodology.SECTION_KEYS
        assert section.body_key in methodology.SECTION_KEYS
    assert len(methodology.SECTION_KEYS) == 2 * len(methodology.SECTION_ORDER)


def test_the_title_key_agrees_with_the_prefix() -> None:
    """`TITLE_KEY` literal, shuning uchun mosligi shu yerda qulflanadi."""
    assert methodology.TITLE_KEY == f"{methodology.KEY_PREFIX}.title"


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_every_key_is_translated_in_every_language(lang: str) -> None:
    """`t()` topa olmagan kalitni **o'zini** qaytaradi (`04` §6)."""
    keys = (methodology.TITLE_KEY, *methodology.SECTION_KEYS)
    for key in keys:
        text = t(key, lang)
        assert text != key, f"{lang}: `{key}` tarjima qilinmagan"
        assert text.strip()


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_body_text_explains_rather_than_labels(lang: str) -> None:
    """Izoh sarlavhaning takrori bo'lib qolmasin.

    Bir so'zli «izoh» metodologiyani ochmaydi, lekin barcha yuqoridagi
    testlardan o'tardi: kalit bor, tarjima bor, javobda ko'rinadi.
    """
    for section in build().sections:
        body = t(section.body_key, lang)
        assert len(body) >= 80, f"{lang}: `{section.body_key}` juda qisqa"
        assert body != t(section.title_key, lang)


# --------------------------------------------------------------------------
# Vitrina bilan bog'lanish (`03` §R1.2 ning aynan o'zi)
# --------------------------------------------------------------------------


def test_the_showcase_link_carries_the_version() -> None:
    """Vitrinadagi raqam usulga bog'lanadi.

    Havolaning o'zi yetmaydi: saqlangan yoki eksport qilingan kesim
    keyinchalik o'qilganda, havola **bugungi** qiymatlarni ko'rsatadi.
    Versiya esa o'sha kesim bilan birga qoladi.
    """
    method = build()
    ref = stats_api.methodology_ref(method, region="samarkand")
    assert ref.version == method.version


def test_the_showcase_link_points_at_the_real_endpoint() -> None:
    """Havola qo'lda yozilgan `/api/v1` emas, `settings.api_prefix` dan."""
    ref = stats_api.methodology_ref(build(), region="samarkand")
    assert ref.url.startswith(settings.api_prefix + stats_api.METHODOLOGY_PATH)
    assert "region=samarkand" in ref.url


def test_the_link_names_the_region_it_was_built_for() -> None:
    """Metodologiya mintaqa kesimida (`06` §9), ya'ni havola ham."""
    ref = stats_api.methodology_ref(build(), region="bukhara")
    assert "region=bukhara" in ref.url


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_the_response_model_renders_text_from_the_catalog(lang: str) -> None:
    """`methodology_out` — matn faqat katalogdan, qattiq kodlangan emas."""
    method = build()
    out = stats_api.methodology_out(method, region="samarkand", lang=lang)
    assert out.version == method.version
    assert out.title == t(methodology.TITLE_KEY, lang)
    assert [s.code for s in out.sections] == list(methodology.SECTION_ORDER)
    for section_out, section in zip(out.sections, method.sections, strict=True):
        assert section_out.title == t(section.title_key, lang)
        assert section_out.body == t(section.body_key, lang)
        assert section_out.spec == section.spec
        assert [v.code for v in section_out.values] == [v.code for v in section.values]


def test_public_limits_name_the_settings_they_claim_to() -> None:
    """`settings` → `PublicLimits` — har maydon o'z sozlamasidan.

    Bu jadval kichik va zerikarli, aynan shuning uchun xato bo'lishi
    oson: `min_reports` ga `public_time_rounding_min` yozilsa
    metodologiya «uchta xabar» o'rniga «besh daqiqa» ni ochardi va
    hamma test yashil qolardi — ikkalasi ham son.
    """
    limits = stats_service.public_limits()
    assert limits.h3_resolution == settings.h3_resolution
    assert limits.min_reports == settings.public_min_reports
    assert limits.time_rounding_min == settings.public_time_rounding_min
    assert limits.coverage_window_days == settings.coverage_window_days
    assert limits.target_penetration == settings.stats_target_penetration
    assert limits.autoclose_after_min == settings.cluster_autoclose_after_min


def test_the_fixture_uses_the_same_limits_as_the_service() -> None:
    """`conftest.default_methodology` mahsulotdan ajralib ketmasin."""
    expected = methodology.build(cluster_params.DEFAULT_PARAMS, stats_service.public_limits())
    assert default_methodology().version == expected.version


def test_every_public_limit_reaches_the_disclosure() -> None:
    """`PublicLimits` ning **har** maydoni bo'limlarda ko'rinadi.

    Bitta maydonni tushirib qoldirish jim buzilish: bo'lim to'liq
    ko'rinadi, versiya ham hisoblanadi — faqat o'sha qiymat o'zgarganda
    versiya qimirlamaydi va o'quvchi undan bexabar qoladi. Tekshiruv
    **maydon bo'yicha** yuriladi, qo'lda yozilgan ro'yxat bo'yicha
    emas: yangi maydon qo'shilgan zahoti u ham talab qilinadi.
    """
    import dataclasses

    base = build().version
    for field in dataclasses.fields(LIMITS):
        current = getattr(LIMITS, field.name)
        moved = dataclasses.replace(LIMITS, **{field.name: current + type(current)(1)})
        version = methodology.build(cluster_params.DEFAULT_PARAMS, moved).version
        assert version != base, f"`PublicLimits.{field.name}` metodologiyaga umuman tushmaydi"


def test_every_tunable_parameter_reaches_the_disclosure() -> None:
    """`06` §9 jadvalining **har** kaliti bo'limlarda ko'rinadi.

    Sozlanadigan, lekin ochilmaydigan parametr — metodologiyaning eng
    yomon holati: E11 uni haqiqiy ma'lumotda o'zgartiradi, vitrina esa
    o'zgargan raqamlarni eski usul bilan hisoblangandek ko'rsatadi.
    """
    base = build().version
    for key, value in cluster_params.DEFAULTS.items():
        tuned = cluster_params.from_mapping({key: value + 1})
        assert build(tuned).version != base, f"`{key}` metodologiyada ochilmaydi"
