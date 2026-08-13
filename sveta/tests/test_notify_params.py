"""Obuna radiusi mintaqa parametri sifatida (`01` §19).

Bazasiz: `from_mapping` toza funksiya, `region_config` dan o'qilgan
lug'atni qabul qiladi.
"""

from __future__ import annotations

import logging

import pytest

from app.core.config import settings
from app.notifications import params as np
from app.notifications import subscriptions as subs

MIN = subs.MIN_RADIUS_M


_WARNINGS = {"notify.config_clamped", "notify.config_invalid"}


def _clamp_warnings(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.msg in _WARNINGS]


def test_empty_config_keeps_global_defaults() -> None:
    """Sozlanmagan mintaqa bugungi xatti-harakatni aynan saqlaydi."""
    p = np.from_mapping({}, min_radius_m=MIN)
    assert p.default_radius_m == settings.subscription_default_radius_m
    assert p.max_radius_m == settings.subscription_max_radius_m


def test_none_is_same_as_empty() -> None:
    assert np.from_mapping(None, min_radius_m=MIN) == np.from_mapping({}, min_radius_m=MIN)


def test_region_value_wins() -> None:
    """`01` §19: mintaqa o'z radiusini beradi va u global qiymatdan ustun."""
    p = np.from_mapping(
        {np.KEY_DEFAULT_RADIUS: 300, np.KEY_MAX_RADIUS: 1500}, min_radius_m=MIN
    )
    assert (p.default_radius_m, p.max_radius_m) == (300, 1500)


def test_only_one_key_configured() -> None:
    """Yarim sozlangan mintaqa ham yaroqli: qolgani boshlang'ich qiymatdan."""
    p = np.from_mapping({np.KEY_DEFAULT_RADIUS: 250}, min_radius_m=MIN)
    assert p.default_radius_m == 250
    assert p.max_radius_m == settings.subscription_max_radius_m


@pytest.mark.parametrize("raw", ["abc", None, [], {"a": 1}, ""])
def test_invalid_value_falls_back(raw: object) -> None:
    """`jsonb` ga har narsa yozilishi mumkin — obuna oqimi to'xtamaydi."""
    p = np.from_mapping({np.KEY_DEFAULT_RADIUS: raw}, min_radius_m=MIN)
    assert p.default_radius_m == settings.subscription_default_radius_m


def test_string_number_is_accepted() -> None:
    """`jsonb` da son satr sifatida ham yozilishi mumkin."""
    p = np.from_mapping({np.KEY_DEFAULT_RADIUS: "400"}, min_radius_m=MIN)
    assert p.default_radius_m == 400


@pytest.mark.parametrize(("raw", "expected"), [("500.0", 500), (450.7, 450), ("300.9", 300)])
def test_fractional_value_is_read_through_float(raw: object, expected: int) -> None:
    """`int(float(...))` — `int(...)` emas (130-run, mutatsiya M1).

    `region_config.value` — `jsonb`: `region_admin` seed i **float** yozadi
    (`seed_values()` → `float(...)`), ya'ni qiymat bazadan `500.0` yoki
    `"500.0"` bo'lib qaytishi mumkin. `int("500.0")` `ValueError` beradi va
    mintaqa jimgina global qiymatga tushardi — sozlangan mintaqa
    «sozlanmagan» ko'rinardi.
    """
    p = np.from_mapping({np.KEY_DEFAULT_RADIUS: raw}, min_radius_m=MIN)
    assert p.default_radius_m == expected


def test_default_below_floor_is_clamped() -> None:
    """Jitter chegarasidan past standart radius mintaqada ham ruxsat etilmaydi."""
    p = np.from_mapping({np.KEY_DEFAULT_RADIUS: 10}, min_radius_m=MIN)
    assert p.default_radius_m == MIN


def test_max_below_floor_is_clamped() -> None:
    """`max < min` — konfiguratsiya xatosi; oraliq bo'sh qolmaydi."""
    p = np.from_mapping({np.KEY_MAX_RADIUS: 5}, min_radius_m=MIN)
    assert p.max_radius_m == MIN
    assert p.default_radius_m == MIN


def test_default_above_max_is_clamped() -> None:
    """Standart hech qachon yuqori chegaradan oshmaydi."""
    p = np.from_mapping(
        {np.KEY_DEFAULT_RADIUS: 5000, np.KEY_MAX_RADIUS: 1000}, min_radius_m=MIN
    )
    assert p.default_radius_m == 1000


def test_invalid_value_is_not_swallowed_silently(caplog: pytest.LogCaptureFixture) -> None:
    """Zaxiraga tushish **ko'rinadi** (130-run, mutatsiya M9).

    Modulning o'z va'dasi: «konfiguratsiyadagi bitta xato butun obuna
    oqimini to'xtatmasligi kerak, lekin u **jim** ham qolmaydi». Jim
    zaxira — sozlagan odam uchun eng yomon holat: mintaqa radiusi
    yozilgan, kod esa global qiymat bilan ishlaydi va hech bir jurnalda
    sabab yo'q.
    """
    with caplog.at_level(logging.WARNING):
        np.from_mapping({np.KEY_DEFAULT_RADIUS: "abc"}, min_radius_m=MIN)
    invalid = [r for r in caplog.records if r.msg == "notify.config_invalid"]
    assert len(invalid) == 1
    assert invalid[0].key == np.KEY_DEFAULT_RADIUS
    assert invalid[0].fallback == settings.subscription_default_radius_m


def test_clamp_warning_fires_only_when_something_was_clamped(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Ogohlantirish qisilgan qiymat haqida (130-run, mutatsiyalar M3, M12).

    Ikkala yo'nalish ham o'lchanadi: yaroqli konfiguratsiya jurnalda
    umuman ko'rinmaydi (`max == min` chegara holati ham — u qisish emas),
    qisilgan qiymat esa **aynan bir marta** ko'rinadi. Teskari shart
    (`clamped == default_m`) har normal mintaqa uchun soxta signal
    berardi va jurnal bo'yicha kalibrlash ma'nosiz bo'lardi.
    """
    with caplog.at_level(logging.WARNING):
        np.from_mapping(
            {np.KEY_DEFAULT_RADIUS: 400, np.KEY_MAX_RADIUS: 1000}, min_radius_m=MIN
        )
    assert _clamp_warnings(caplog) == []

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        np.from_mapping(
            {np.KEY_DEFAULT_RADIUS: MIN, np.KEY_MAX_RADIUS: MIN}, min_radius_m=MIN
        )
    assert _clamp_warnings(caplog) == []

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        np.from_mapping({np.KEY_DEFAULT_RADIUS: 10}, min_radius_m=MIN)
    clamped = _clamp_warnings(caplog)
    assert len(clamped) == 1
    assert clamped[0].key == np.KEY_DEFAULT_RADIUS


def test_seed_values_are_disjoint_from_confirm_defaults() -> None:
    """`06` §9 jadvali begona kalit bilan aralashmaydi."""
    from app.clustering.params import DEFAULTS

    assert set(np.seed_values()) & set(DEFAULTS) == set()


def test_seed_values_cover_every_key_read() -> None:
    """`region_admin` seed qiladigan kalitlar — kod o'qiydiganlarning aynan o'zi.

    Ular ajralib ketsa mintaqa «sozlangan» ko'rinadi, lekin kod baribir
    global qiymatga tushardi — 28-sessiyadagi `default_language` bilan
    bir xil holat.
    """
    assert set(np.seed_values()) == {np.KEY_DEFAULT_RADIUS, np.KEY_MAX_RADIUS}


def test_seed_values_carry_the_matching_number() -> None:
    """Kalit to'g'ri, qiymat ham to'g'ri (130-run, mutatsiya M8).

    Ikkala qiymat almashtirilsa kalitlar to'plami o'zgarmaydi — 12 test
    ham yashil qolardi. Amalda `region_admin` yangi mintaqaga standart
    sifatida **yuqori chegarani** (bugun 3000 m) yozib qo'yardi: har bir
    yangi obunachi butun shahar bo'yicha bildirishnoma olardi va buni
    hech kim so'ramagan bo'lardi.
    """
    seeded = np.seed_values()
    assert seeded[np.KEY_DEFAULT_RADIUS] == float(settings.subscription_default_radius_m)
    assert seeded[np.KEY_MAX_RADIUS] == float(settings.subscription_max_radius_m)
    assert seeded[np.KEY_DEFAULT_RADIUS] <= seeded[np.KEY_MAX_RADIUS]


def test_region_admin_seed_includes_notify_keys() -> None:
    from tools.region_admin import seed_defaults

    assert set(np.seed_values()) <= set(seed_defaults())


def test_the_floor_is_an_absolute_value_above_the_jitter() -> None:
    """`MIN_RADIUS_M` — prozada yozilgan, kodda o'lchanmagan kafolat.

    Bu fayl chegarani `MIN = subs.MIN_RADIUS_M` orqali **o'zidan** o'qiydi
    (124-run refleksivligi), `app/` da esa unga murojaat qiladigan yagona
    boshqa joy — `channels.RULE_CLAUSES` ning `why` **matni**
    («`MIN_RADIUS_M` jitterdan katta»), ya'ni uni hech kim qayta
    sanamaydi (126-run: proza katalog emas — uning `evidence` i
    `find_matching` ga ishora qiladi, konstantaga emas). Chegarani 50 ga
    tushirish bugun jimgina o'tardi va obuna doirasi hodisa markazining
    o'z siljishidan kichik bo'lib qolardi (`05` §3.1, `jitter_max_m`):
    o'z uyidagi uzilish haqida obunachi jitterning yo'nalishiga qarab
    xabar olardi yoki olmasdi — deterministik, lekin tushuntirib
    bo'lmaydigan xatti-harakat.
    """
    assert subs.MIN_RADIUS_M == 200
    assert subs.MIN_RADIUS_M > settings.jitter_max_m


def test_params_from_config_passes_the_module_floor() -> None:
    """`params_from_config` ni chaqiradigan test umuman yo'q edi.

    Funksiyaning yagona vazifasi — pastki chegarani ulash, va `add()` ning
    `params` berilmagan **har** chaqiruvi shu yerdan o'tadi. `min_radius_m`
    ni `0` ga almashtirish ham, `values` ni butunlay tashlab yuborish ham
    jimgina o'tardi: birinchisi mintaqaning ma'nosiz kichik radiusini
    qabul qilardi, ikkinchisi esa **sozlangan** mintaqani sozlanmagan
    qilib ko'rsatardi. Uchala tarmoq ham o'lchanadi — qisish, mintaqaning
    o'z qiymati va `None` ↔ bo'sh lug'atning tengligi.
    """
    assert subs.params_from_config({np.KEY_DEFAULT_RADIUS: 10}).default_radius_m == MIN
    configured = subs.params_from_config(
        {np.KEY_DEFAULT_RADIUS: 640, np.KEY_MAX_RADIUS: 1500}
    )
    assert (configured.default_radius_m, configured.max_radius_m) == (640, 1500)
    assert subs.params_from_config() == subs.params_from_config({})


def test_the_floor_itself_is_accepted() -> None:
    """Chegaraning o'zi — `<` va `<=` ni ajratadigan yagona nuqta.

    Mavjud tasdiqlar `MIN - 1` (rad etiladi) va 300/800 (qabul qilinadi)
    bilan turadi, ya'ni `value <= MIN_RADIUS_M` mutanti omon qolardi.
    Narxi bir metr emas: yuqori chegarasi polga qisilgan mintaqada
    (`test_max_below_floor_is_clamped`) **standart radiusning o'zi** MIN
    ga teng bo'ladi va o'sha mintaqada radiussiz **har** `add()` chaqiruvi
    `SubscriptionRadiusError` bilan yiqilardi — obuna umuman ochilmasdi,
    sababi esa foydalanuvchiga «radius oraliqdan tashqarida» deb
    ko'rinardi. Ikkinchi tasdiq yuqori chegarani ham ushlaydi
    (`value >= params.max_radius_m` mutanti shu qatorda o'ladi).
    """
    p = np.NotifyParams(default_radius_m=300, max_radius_m=800)
    assert subs._validated_radius(MIN, p) == MIN

    degenerate = np.from_mapping({np.KEY_MAX_RADIUS: 5}, min_radius_m=MIN)
    assert (degenerate.default_radius_m, degenerate.max_radius_m) == (MIN, MIN)
    assert subs._validated_radius(None, degenerate) == MIN


def test_zero_is_a_value_not_a_missing_argument() -> None:
    """`radius_m is not None` — `if radius_m` emas.

    `0` — ikkala o'qishni ajratadigan yagona kirish. Bugun u chegaradan
    past va rad etiladi; truthiness mutanti uni «berilmagan» deb o'qib,
    mintaqaning standart radiusini **jimgina** ochib qo'yardi: botda `0`
    yozgan odam xatolik o'rniga 300 metrlik obuna olardi va buni
    so'ramagan bo'lardi.
    """
    p = np.NotifyParams(default_radius_m=300, max_radius_m=800)
    with pytest.raises(subs.SubscriptionRadiusError):
        subs._validated_radius(0, p)


def test_validated_radius_uses_region_max() -> None:
    """Mintaqa chegarasidan oshgan so'rov rad etiladi, global emas."""
    p = np.NotifyParams(default_radius_m=300, max_radius_m=800)
    assert subs._validated_radius(None, p) == 300
    assert subs._validated_radius(800, p) == 800
    with pytest.raises(subs.SubscriptionRadiusError):
        subs._validated_radius(801, p)
    with pytest.raises(subs.SubscriptionRadiusError):
        subs._validated_radius(MIN - 1, p)


def test_radius_error_reports_region_bounds() -> None:
    """Xato matni mintaqaning chegarasini beradi, boshqa shaharnikini emas."""
    p = np.NotifyParams(default_radius_m=300, max_radius_m=800)
    with pytest.raises(subs.SubscriptionRadiusError) as exc:
        subs._validated_radius(5000, p)
    assert exc.value.context["max_m"] == 800
    # `min_m` ham javob tanasiga chiqadi (`errors.to_dict`) va i18n matni
    # oraliqni **faqat** shundan oladi — `min_m=value` mutanti
    # foydalanuvchiga «5000 dan 800 gacha» deb ko'rsatardi.
    assert exc.value.context["min_m"] == MIN
