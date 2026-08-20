"""TZ §7 sozlamalar reyestri va §1 zonalari.

Bu fayl TZ ning ikkita **tuzilish** talabini qulflaydi va ikkalasi ham
jimgina buziladigan turdan:

* §7 — «отсутствие настройки при запуске = **ошибка запуска**, а не
  подстановка значения из кода». Ya'ni `06` §9 dagi bootstrap naqshi
  (baza bo'sh → koddagi son) bu yerda taqiqlangan. Buni test bilan
  ushlamasa, keyingi qo'l o'z-o'zidan `values.get(key, DEFAULT)` yozadi
  va porog jimgina koddan kelaveradi.
* §1 — to'rt daraja **bir vaqtda** saqlanadi. Bitta darajani unutish
  xato bermaydi: ustun `NULL` bo'lib qoladi va sanash so'rovi shunchaki
  kamroq qator ko'radi.
"""

from __future__ import annotations

import pytest

from app.core.tzconfig import (
    REQUIRED_KEYS,
    SETTINGS,
    SURVEY_WAVES_KEY,
    ConfigInvalidError,
    ConfigMissingError,
    Origin,
    Unit,
    origins,
    params_from_mapping,
    setting,
    starting_values,
)
from app.geo.h3_cells import cell_of
from app.geo.pipeline import TZ_LEVELS

# --------------------------------------------------------------------------
# 1. Reyestrning o'zi
# --------------------------------------------------------------------------


def test_every_setting_key_is_unique_and_namespaced() -> None:
    keys = [s.key for s in SETTINGS]

    assert len(keys) == len(set(keys))
    assert all(key.startswith("tz.") for key in keys), keys


def test_the_registry_covers_the_whole_spec_table() -> None:
    """§7 jadvalida 23 sozlama + to'lqinlar massivi.

    Son qo'lda yozilgan va bu ataylab: qator qo'shilsa yoki tushib
    qolsa, test aynan shu yerda yiqiladi va reyestr hujjat bilan
    solishtiriladi.

    28 — §7 jadvalining o'zidan **ko'p**: beshta kalit hujjat
    jadvalida yo'q, lekin TZ matnida son bo'lib uchraydi yoki uni
    ishlatadigan qoida sonsiz yozib bo'lmaydi, Т-1 esa ularni kodda
    literal qoldirishga yo'l qo'ymaydi
    (`tz.confirm.block_min_cells`, `tz.confirm.mahalla_min_blocks` —
    §2.1; `tz.restore.early_percentile` — §4/В-8;
    `tz.sensor.max_age_min`, `tz.sensor.min_state_min` — §11/7 ning
    datchik qabuli). Beshalasi ham `PROGRESS.md` ning «Ochiq
    savollar» ida 👤 belgisi bilan turadi.
    """
    assert len(SETTINGS) == 28
    assert len(REQUIRED_KEYS) == len(SETTINGS) + 1
    assert SURVEY_WAVES_KEY in REQUIRED_KEYS


def test_todays_values_are_all_invented() -> None:
    """👤 qarori (2026-08-19): Toshkent tarixi yo'q, ya'ni hech biri o'lchanmagan.

    Birinchi sozlama `computed` ga o'tganda bu test yiqiladi — va bu
    to'g'ri: o'shanda §7 ning pometalari qayta ko'rib chiqiladi.
    """
    marks = set(origins().values())

    assert marks == {Origin.INVENTED}


def test_shares_are_fractions_not_percents() -> None:
    """§7 da foiz bilan yozilgan, bazada ulush bilan yotadi.

    `40` va `0.40` ni adashtirish hech qanday xato bermaydi — porog
    yuz baravar oshadi va hech narsa tasdiqlanmaydi.
    """
    for spec in SETTINGS:
        if spec.unit is Unit.SHARE:
            assert 0.0 < spec.start <= 1.0, spec.key


def test_an_unknown_key_is_a_loud_error() -> None:
    with pytest.raises(ConfigMissingError, match="noma'lum kalit"):
        setting("tz.confirm.yoq")


# --------------------------------------------------------------------------
# 2. §7 ning asosiy talabi: yo'q kalit — xato
# --------------------------------------------------------------------------


def test_a_missing_key_raises_instead_of_falling_back() -> None:
    """Bitta kalitni olib tashlash yetarli — sukut qiymati qo'yilmaydi."""
    values = starting_values()
    del values["tz.confirm.house_users"]

    with pytest.raises(ConfigMissingError, match="tz.confirm.house_users"):
        params_from_mapping(values)


def test_the_error_names_every_missing_key_at_once() -> None:
    """Ishga tushirishda birma-bir emas, hammasi bir ko'rinishda."""
    with pytest.raises(ConfigMissingError) as exc:
        params_from_mapping({})

    message = str(exc.value)
    assert f"{len(REQUIRED_KEYS)} kalit yo'q" in message
    for key in REQUIRED_KEYS:
        assert key in message


def test_starting_values_are_complete_and_load() -> None:
    """§7 jadvali o'zi to'liq: seed qilingan mintaqa darhol ishlaydi."""
    params = params_from_mapping(starting_values())

    assert (params.house_users, params.block_users, params.mahalla_users) == (3, 5, 8)
    assert (params.house_window_min, params.block_window_min, params.mahalla_window_min) == (
        20,
        30,
        45,
    )
    assert params.survey_waves_min == (30, 60, 120, 240)
    assert params.quiet_from_hour == 23
    assert params.quiet_to_hour == 7


# --------------------------------------------------------------------------
# 3. Qiymatning o'zi tekshiriladi
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "bad"),
    [
        ("tz.scale.district_block_share", 40),  # foiz, ulush emas
        ("tz.scale.district_block_share", 0),  # nol ulush
        ("tz.confirm.house_users", 0),  # nol odam
        ("tz.confirm.house_users", -1),
        ("tz.notify.quiet_from_hour", 24),  # soat 0..23
        ("tz.confirm.house_users", "3"),  # satr
        ("tz.confirm.house_users", True),  # `bool` — `int` ning vorisi
    ],
)
def test_a_value_outside_its_unit_is_rejected(key, bad) -> None:
    values = starting_values()
    values[key] = bad

    with pytest.raises(ConfigInvalidError, match=key):
        params_from_mapping(values)


@pytest.mark.parametrize(
    "bad",
    [[], "30,60", [30, 30], [60, 30], [0, 30], [30, None]],
)
def test_survey_waves_must_be_a_growing_list_of_minutes(bad) -> None:
    """§4.1: to'lqinlar 30/60/120/240 — tartibi ma'noli, takrori xato."""
    values = starting_values()
    values[SURVEY_WAVES_KEY] = bad

    with pytest.raises(ConfigInvalidError, match=SURVEY_WAVES_KEY):
        params_from_mapping(values)


def test_hour_zero_is_a_valid_quiet_boundary() -> None:
    """`0` — yaroqli soat. `value <= 0` qorovuli uni to'smasligi kerak."""
    values = starting_values()
    values["tz.notify.quiet_to_hour"] = 0

    assert params_from_mapping(values).quiet_to_hour == 0


# --------------------------------------------------------------------------
# 4. §1 — to'rt daraja
# --------------------------------------------------------------------------


def test_the_grid_levels_match_the_spec_table() -> None:
    """§1 jadvali: r10 uy, r9 kvartal, r8 mahalla, r7 tuman, r11 manzil."""
    assert TZ_LEVELS == {
        "district": 7,
        "mahalla": 8,
        "block": 9,
        "house": 10,
        "address": 11,
    }


def test_levels_nest_from_the_same_point() -> None:
    """Bitta nuqta har darajada **boshqa** katak beradi.

    Agar rezolyutsiya uzatilmasa (`cell_of(lat, lon)` — sukut r9),
    to'rtala ustun bir xil qiymatga to'lardi va sanash uy darajasida
    kvartalni sanardi. Shuning uchun turlicha ekani o'lchanadi.
    """
    lat, lon = 39.6547, 66.9597
    cells = {name: cell_of(lat, lon, res) for name, res in TZ_LEVELS.items()}

    assert len(set(cells.values())) == len(TZ_LEVELS)


def test_a_nearby_point_shares_the_block_but_not_the_address() -> None:
    """~60 m siljish r11 ni almashtiradi, r9 ni odatda emas.

    §1.1 aynan shunga tayanadi: r11 «turli manzil» ning yaqinlashuvi.
    """
    lat, lon = 39.6547, 66.9597
    # ~60 m shimolga (1° kenglik ≈ 111 km).
    near_lat = lat + 0.00055

    assert cell_of(lat, lon, 11) != cell_of(near_lat, lon, 11)
    assert cell_of(lat, lon, 7) == cell_of(near_lat, lon, 7)
