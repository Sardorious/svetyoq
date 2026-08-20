"""TZ §7 — sozlamalar reyestri (`TZ_Podtverzhdenie_i_uvedomleniya.md`).

**Nima uchun bu modul bor.** TZ §7 ning birinchi qatori shart qo'yadi:
«Все числа ниже — **в таблице настроек, не в коде**. Отсутствие настройки
при запуске = ошибка запуска, а не подстановка значения из кода.» Ya'ni
`06` §9 dagi «bootstrap qiymati» naqshi (baza bo'sh bo'lsa koddagi son
ishlatiladi) bu yerda **taqiqlangan**: kalit yo'q bo'lsa jimgina davom
etish o'rniga xato ko'tariladi.

Shundan modulning ikkiga bo'linishi kelib chiqadi:

* `SETTINGS` — kalitlarning **reyestri**: nomi, birligi, kelib chiqishi
  va §7 jadvalidagi **boshlang'ich qiymati**. Bu qiymat runtime da
  ishlatilmaydi — u faqat `region_config` ni birinchi marta to'ldirish
  uchun (`0012` migratsiyasi va `tools/seed_tz_config.py`).
* `params_from_mapping()` — bazadan o'qilgan lug'atni tipli
  `TzParams` ga aylantiradi va **har bir** kalitning borligini talab
  qiladi. Yo'q kalit — `ConfigMissingError`.

## Kelib chiqish belgisi — qiymat bilan birga chop etiladi

§7 ning oxirgi qatori har sozlamaga `ПРИДУМАНО` / `ЭКСПЕРТ` /
`ПОСЧИТАНО` pometasini talab qiladi va uni **qiymat bilan birga**
ko'rsatishni buyuradi. Bugun o'n ikkalasi ham `ПРИДУМАНО` va bu
tasodif emas: 👤 qarori (2026-08-19) bo'yicha Toshkent tarixi
ishlatilmaydi, ya'ni TZ §12 ning oldindan tekshiruvi o'tkazilmaydi va
sonlar Samarqandning **o'z** ma'lumotidan keyin o'lchanadi. Pometa —
shu holatning mahsulot ichidagi yagona ko'rinadigan izi: u
`GET /api/v1/admin/config` va vitrinada qiymat yonida turadi.

Modul **toza**: bazaga ham, `settings` ga ham bog'liq emas.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

#: Hujjat bo'limi. Reyestrlar vitrinasi (`app.admin.registries`) shuni o'qiydi.
SPEC = "TZ §7"


class Origin(StrEnum):
    """Qiymat qayerdan kelgan (§7 ning oxirgi qatori).

    Tartib **kuchsizdan kuchliga**: `INVENTED` — hech narsaga
    asoslanmagan, `COMPUTED` — ma'lumotdan hisoblangan.
    """

    #: `ПРИДУМАНО` — qo'lda tanlangan, o'lchanmagan.
    INVENTED = "invented"
    #: `ЭКСПЕРТ` — soha odamining bahosi, lekin o'lchov emas.
    EXPERT = "expert"
    #: `ПОСЧИТАНО` — haqiqiy ma'lumotdan hisoblangan.
    COMPUTED = "computed"


class Unit(StrEnum):
    """Qiymatning birligi — vitrinada ko'rsatiladi va testda tekshiriladi."""

    PEOPLE = "people"
    MINUTES = "minutes"
    HOURS = "hours"
    #: `0.0`…`1.0` oralig'idagi ulush. §7 da foiz bilan yozilgan.
    SHARE = "share"
    COUNT = "count"
    #: Mahalliy vaqtdagi soat (`0`…`23`).
    HOUR_OF_DAY = "hour_of_day"


class ConfigMissingError(RuntimeError):
    """§7: kalit yo'q — bu ishga tushirish xatosi, sukut qiymati emas."""


class ConfigInvalidError(RuntimeError):
    """Kalit bor, lekin qiymati o'z birligiga to'g'ri kelmaydi."""


@dataclass(frozen=True)
class Setting:
    """§7 jadvalining bitta qatori."""

    key: str
    #: §7 ning «Стартовое значение» ustuni. Runtime da **ishlatilmaydi**.
    start: float
    unit: Unit
    origin: Origin
    #: Qatorning qisqa mazmuni — vitrinada va jurnalda ko'rinadi.
    note: str


# --------------------------------------------------------------------------
# Reyestr — §7 jadvali, hujjatdagi tartibda
# --------------------------------------------------------------------------

SETTINGS: tuple[Setting, ...] = (
    Setting(
        key="tz.confirm.house_users",
        start=3,
        unit=Unit.PEOPLE,
        origin=Origin.INVENTED,
        note="Uy (r10) darajasida kerakli odam soni (§2.1)",
    ),
    Setting(
        key="tz.confirm.block_users",
        start=5,
        unit=Unit.PEOPLE,
        origin=Origin.INVENTED,
        note="Kvartal (r9) darajasida kerakli odam soni (§2.1)",
    ),
    Setting(
        key="tz.confirm.mahalla_users",
        start=8,
        unit=Unit.PEOPLE,
        origin=Origin.INVENTED,
        note="Mahalla (r8) darajasida kerakli odam soni (§2.1)",
    ),
    Setting(
        key="tz.confirm.house_window_min",
        start=20,
        unit=Unit.MINUTES,
        origin=Origin.INVENTED,
        note="Uy darajasidagi sirpanuvchi oyna (§2.1)",
    ),
    Setting(
        key="tz.confirm.block_window_min",
        start=30,
        unit=Unit.MINUTES,
        origin=Origin.INVENTED,
        note="Kvartal darajasidagi sirpanuvchi oyna (§2.1)",
    ),
    Setting(
        key="tz.confirm.mahalla_window_min",
        start=45,
        unit=Unit.MINUTES,
        origin=Origin.INVENTED,
        note="Mahalla darajasidagi sirpanuvchi oyna (§2.1)",
    ),
    Setting(
        key="tz.confirm.against_users",
        start=2,
        unit=Unit.PEOPLE,
        origin=Origin.INVENTED,
        note="«Menda svet bor» — tasdiqlashni to'xtatuvchi qarshi dalil (§2.2)",
    ),
    Setting(
        key="tz.confirm.sparse_floor_users",
        start=2,
        unit=Unit.PEOPLE,
        origin=Origin.INVENTED,
        note="Kam odamli zonada porogning pastki cheki (§2.3)",
    ),
    Setting(
        key="tz.confirm.block_min_cells",
        start=3,
        unit=Unit.COUNT,
        origin=Origin.INVENTED,
        note="Kvartal uchun turli r10 kataklarining eng kam soni (§2.1)",
    ),
    Setting(
        key="tz.confirm.mahalla_min_blocks",
        start=3,
        unit=Unit.COUNT,
        origin=Origin.INVENTED,
        note="Mahalla uchun tasdiqlangan kvartallarning eng kam soni (§2.1)",
    ),
    Setting(
        key="tz.scale.district_block_share",
        start=0.40,
        unit=Unit.SHARE,
        origin=Origin.INVENTED,
        note="Tuman uchun tasdiqlangan kvartallar ulushi (§3)",
    ),
    Setting(
        key="tz.scale.district_block_min",
        start=3,
        unit=Unit.COUNT,
        origin=Origin.INVENTED,
        note="Tuman uchun kvartallarning eng kam soni (§3)",
    ),
    Setting(
        key="tz.scale.city_district_share",
        start=0.50,
        unit=Unit.SHARE,
        origin=Origin.INVENTED,
        note="Shahar uchun tasdiqlangan tumanlar ulushi (§3)",
    ),
    Setting(
        key="tz.scale.city_district_min",
        start=3,
        unit=Unit.COUNT,
        origin=Origin.INVENTED,
        note="Shahar uchun tumanlarning eng kam soni (§3)",
    ),
    Setting(
        key="tz.restore.users",
        start=2,
        unit=Unit.PEOPLE,
        origin=Origin.INVENTED,
        note="Kvartalni yopish uchun turli manzildagi odam soni (§4, V-2)",
    ),
    Setting(
        key="tz.restore.answered_share",
        start=0.40,
        unit=Unit.SHARE,
        origin=Origin.INVENTED,
        note="So'rovga javob berganlarning kerakli ulushi (§4, V-2/V-6)",
    ),
    Setting(
        key="tz.restore.share_decay_per_hour",
        start=0.05,
        unit=Unit.SHARE,
        origin=Origin.INVENTED,
        note="Har soat davomiylik uchun ulushning pasayishi (§4, V-5)",
    ),
    Setting(
        key="tz.restore.share_floor",
        start=0.15,
        unit=Unit.SHARE,
        origin=Origin.INVENTED,
        note="Pasaygan ulushning pastki cheki (§4, V-5)",
    ),
    Setting(
        key="tz.restore.early_percentile",
        start=0.05,
        unit=Unit.SHARE,
        origin=Origin.INVENTED,
        # §7 jadvalida bu qator YO'Q: «5%» faqat В-8 ning matnida
        # uchraydi. Uni kodda literal qoldirish Т-1 ga zid, shuning
        # uchun sozlamaga chiqarildi. 👤 §7 ga hujjat sifatida
        # qo'shilsinmi — `PROGRESS.md` ning «Ochiq savollar» ida.
        note="V-8: erta tiklanish xabarining persentili (§4, V-8)",
    ),
    Setting(
        key="tz.stale_after_h",
        start=3,
        unit=Unit.HOURS,
        origin=Origin.INVENTED,
        note="Jimlikdan keyin «Ma'lumot eskirgan» statusi (§4.2)",
    ),
    Setting(
        key="tz.survey.share",
        start=0.25,
        unit=Unit.SHARE,
        origin=Origin.INVENTED,
        note="So'rov yuboriladigan xabar bergan odamlar ulushi (§4.1)",
    ),
    Setting(
        key="tz.notify.quiet_from_hour",
        start=23,
        unit=Unit.HOUR_OF_DAY,
        origin=Origin.INVENTED,
        note="Tinch soatlarning boshlanishi (§6.2, 4-tekshiruv)",
    ),
    Setting(
        key="tz.notify.quiet_to_hour",
        start=7,
        unit=Unit.HOUR_OF_DAY,
        origin=Origin.INVENTED,
        note="Tinch soatlarning tugashi (§6.2, 4-tekshiruv)",
    ),
    Setting(
        key="tz.notify.per_address_hour",
        start=1,
        unit=Unit.COUNT,
        origin=Origin.INVENTED,
        note="Bir manzilga soatiga uzilish bildirishnomasi (§6.2, 5-tekshiruv)",
    ),
    Setting(
        key="tz.notify.per_user_day",
        start=5,
        unit=Unit.COUNT,
        origin=Origin.INVENTED,
        note="Bir odamga sutkasiga bildirishnoma (§6.2, 5-tekshiruv)",
    ),
    Setting(
        key="tz.notify.max_addresses",
        start=3,
        unit=Unit.COUNT,
        origin=Origin.INVENTED,
        note="Bir odamdagi manzillar soni: uy, ish, ota-ona (§6.1)",
    ),
    Setting(
        key="tz.sensor.max_age_min",
        start=30,
        unit=Unit.MINUTES,
        origin=Origin.INVENTED,
        # §7 jadvalida bu qator YO'Q: §11/7 («Приём датчиков») umuman
        # son bermaydi. Lekin datchik xabarining yoshi tekshirilmasa,
        # uzilib qolgan aloqa tiklangandan keyin kelgan ikki soatlik
        # navbat В-7 bo'yicha kvartalni **bugungi** vaqt bilan yopardi.
        # Kodda literal qoldirish Т-1 ga zid → sozlamaga chiqarildi.
        # 👤 §7 ga hujjat sifatida qo'shilsinmi — «Ochiq savollar».
        note="Datchik xabarining eng katta yoshi (§11/7)",
    ),
    Setting(
        key="tz.sensor.min_state_min",
        start=5,
        unit=Unit.MINUTES,
        origin=Origin.INVENTED,
        # O'sha sabab: buzuq datchik holatni daqiqada o'n marta
        # almashtiradi va har almashinuv В-7 bo'yicha kvartalni yopib
        # qayta ochardi. Bu son «raqqosa» ni to'sadi.
        note="Ikki holat o'zgarishi orasidagi eng kichik oraliq (§11/7)",
    ),
)

#: §4.1 — so'rov to'lqinlari. Jadval emas, ro'yxat: `region_config` da
#: bitta kalit ostida massiv bo'lib yotadi, shuning uchun `SETTINGS` ga
#: kirmaydi, lekin **baribir bazadan** o'qiladi.
SURVEY_WAVES_KEY = "tz.survey.waves_min"
SURVEY_WAVES_START: tuple[int, ...] = (30, 60, 120, 240)

#: Barcha kalitlar — o'qish tartibida. `params_from_mapping` shuni talab qiladi.
REQUIRED_KEYS: tuple[str, ...] = tuple(s.key for s in SETTINGS) + (SURVEY_WAVES_KEY,)

_BY_KEY: dict[str, Setting] = {s.key: s for s in SETTINGS}


def setting(key: str) -> Setting:
    """Reyestr qatori. Noma'lum kalit — `KeyError` emas, ochiq xato."""
    try:
        return _BY_KEY[key]
    except KeyError as exc:
        raise ConfigMissingError(f"{SPEC}: noma'lum kalit `{key}`") from exc


def starting_values() -> dict[str, Any]:
    """`region_config` ni birinchi marta to'ldirish uchun qiymatlar.

    Runtime da **ishlatilmaydi** — faqat migratsiya va seed asbobi
    chaqiradi. Shu ajratish §7 ning «koddan sukut qiymati qo'yilmaydi»
    talabini bajaradi: kod bu funksiyani so'rov yo'lida chaqirmaydi.
    """
    values: dict[str, Any] = {s.key: s.start for s in SETTINGS}
    values[SURVEY_WAVES_KEY] = list(SURVEY_WAVES_START)
    return values


def origins() -> dict[str, Origin]:
    """Kalit → kelib chiqish belgisi. Qiymat bilan birga chop etiladi."""
    result: dict[str, Origin] = {s.key: s.origin for s in SETTINGS}
    result[SURVEY_WAVES_KEY] = Origin.INVENTED
    return result


@dataclass(frozen=True)
class TzParams:
    """§7 ning bazadan o'qilgan, tipi tekshirilgan ko'rinishi."""

    house_users: int
    block_users: int
    mahalla_users: int
    house_window_min: int
    block_window_min: int
    mahalla_window_min: int
    against_users: int
    sparse_floor_users: int
    block_min_cells: int
    mahalla_min_blocks: int
    district_block_share: float
    district_block_min: int
    city_district_share: float
    city_district_min: int
    restore_users: int
    restore_answered_share: float
    restore_share_decay_per_hour: float
    restore_share_floor: float
    restore_early_percentile: float
    stale_after_h: int
    survey_share: float
    survey_waves_min: tuple[int, ...]
    quiet_from_hour: int
    quiet_to_hour: int
    notify_per_address_hour: int
    notify_per_user_day: int
    notify_max_addresses: int
    #: §11/7 — datchiklar qabuli. §7 jadvalida yo'q, sabab `SETTINGS` da.
    sensor_max_age_min: int
    sensor_min_state_min: int


def _check(key: str, raw: Any) -> float:
    """Qiymat o'z birligiga mos keladimi. Mos kelmasa — ochiq xato."""
    spec = setting(key)
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise ConfigInvalidError(f"{key}: son kutilgan edi, `{raw!r}` keldi")
    value = float(raw)
    if spec.unit is Unit.SHARE and not 0.0 < value <= 1.0:
        raise ConfigInvalidError(f"{key}: ulush `(0, 1]` oralig'ida bo'lishi kerak, {value}")
    if spec.unit is Unit.HOUR_OF_DAY and not 0 <= value <= 23:
        raise ConfigInvalidError(f"{key}: soat `0..23` bo'lishi kerak, {value}")
    if spec.unit is not Unit.HOUR_OF_DAY and spec.unit is not Unit.SHARE and value <= 0:
        raise ConfigInvalidError(f"{key}: musbat bo'lishi kerak, {value}")
    return value


def _waves(raw: Any) -> tuple[int, ...]:
    """§4.1 to'lqinlari: bo'sh bo'lmagan, o'suvchi, musbat butun sonlar."""
    if not isinstance(raw, (list, tuple)) or not raw:
        raise ConfigInvalidError(f"{SURVEY_WAVES_KEY}: bo'sh bo'lmagan ro'yxat kutilgan edi")
    waves: list[int] = []
    for item in raw:
        if isinstance(item, bool) or not isinstance(item, (int, float)) or item <= 0:
            raise ConfigInvalidError(f"{SURVEY_WAVES_KEY}: musbat son emas — `{item!r}`")
        waves.append(int(item))
    if waves != sorted(set(waves)):
        raise ConfigInvalidError(f"{SURVEY_WAVES_KEY}: to'lqinlar o'suvchi va takrorsiz bo'lsin")
    return tuple(waves)


def params_from_mapping(values: Mapping[str, Any]) -> TzParams:
    """`region_config` dagi lug'at → `TzParams`.

    §7: **yo'q kalit — xato**. Bu funksiya sukut qiymati qo'ymaydi va
    aynan shuning uchun `SETTINGS[*].start` ni o'qimaydi.
    """
    missing = [key for key in REQUIRED_KEYS if key not in values]
    if missing:
        raise ConfigMissingError(
            f"{SPEC}: `region_config` da {len(missing)} kalit yo'q: " + ", ".join(sorted(missing))
        )
    return TzParams(
        house_users=int(_check("tz.confirm.house_users", values["tz.confirm.house_users"])),
        block_users=int(_check("tz.confirm.block_users", values["tz.confirm.block_users"])),
        mahalla_users=int(_check("tz.confirm.mahalla_users", values["tz.confirm.mahalla_users"])),
        house_window_min=int(
            _check("tz.confirm.house_window_min", values["tz.confirm.house_window_min"])
        ),
        block_window_min=int(
            _check("tz.confirm.block_window_min", values["tz.confirm.block_window_min"])
        ),
        mahalla_window_min=int(
            _check("tz.confirm.mahalla_window_min", values["tz.confirm.mahalla_window_min"])
        ),
        against_users=int(_check("tz.confirm.against_users", values["tz.confirm.against_users"])),
        sparse_floor_users=int(
            _check("tz.confirm.sparse_floor_users", values["tz.confirm.sparse_floor_users"])
        ),
        block_min_cells=int(
            _check("tz.confirm.block_min_cells", values["tz.confirm.block_min_cells"])
        ),
        mahalla_min_blocks=int(
            _check("tz.confirm.mahalla_min_blocks", values["tz.confirm.mahalla_min_blocks"])
        ),
        district_block_share=_check(
            "tz.scale.district_block_share", values["tz.scale.district_block_share"]
        ),
        district_block_min=int(
            _check("tz.scale.district_block_min", values["tz.scale.district_block_min"])
        ),
        city_district_share=_check(
            "tz.scale.city_district_share", values["tz.scale.city_district_share"]
        ),
        city_district_min=int(
            _check("tz.scale.city_district_min", values["tz.scale.city_district_min"])
        ),
        restore_users=int(_check("tz.restore.users", values["tz.restore.users"])),
        restore_answered_share=_check(
            "tz.restore.answered_share", values["tz.restore.answered_share"]
        ),
        restore_share_decay_per_hour=_check(
            "tz.restore.share_decay_per_hour", values["tz.restore.share_decay_per_hour"]
        ),
        restore_share_floor=_check("tz.restore.share_floor", values["tz.restore.share_floor"]),
        restore_early_percentile=_check(
            "tz.restore.early_percentile", values["tz.restore.early_percentile"]
        ),
        stale_after_h=int(_check("tz.stale_after_h", values["tz.stale_after_h"])),
        survey_share=_check("tz.survey.share", values["tz.survey.share"]),
        survey_waves_min=_waves(values[SURVEY_WAVES_KEY]),
        quiet_from_hour=int(
            _check("tz.notify.quiet_from_hour", values["tz.notify.quiet_from_hour"])
        ),
        quiet_to_hour=int(_check("tz.notify.quiet_to_hour", values["tz.notify.quiet_to_hour"])),
        notify_per_address_hour=int(
            _check("tz.notify.per_address_hour", values["tz.notify.per_address_hour"])
        ),
        notify_per_user_day=int(_check("tz.notify.per_user_day", values["tz.notify.per_user_day"])),
        notify_max_addresses=int(
            _check("tz.notify.max_addresses", values["tz.notify.max_addresses"])
        ),
        sensor_max_age_min=int(
            _check("tz.sensor.max_age_min", values["tz.sensor.max_age_min"])
        ),
        sensor_min_state_min=int(
            _check("tz.sensor.min_state_min", values["tz.sensor.min_state_min"])
        ),
    )
