"""Metodologiya bo'limi — vitrinaning raqamlari qanday hisoblanganini ochadi.

**Nima uchun bu modul bor.** `03` §R1.2 ning tarkibida to'rtinchi qator
turibdi: «**Metodologiya bo'limi bilan bog'lanish**». Qolgan uchtasi
yozilgan (uchala kesim, Coverage Index, CSV), bu esa yo'q edi. `01` §Mission
uni mahsulotning ta'rifiga kiritadi — «оставаясь независимым и прозрачным
**в методологии**» — va `01` §5 jurnalist uchun qiymatni aynan shunday
ta'riflaydi: «Статистика **с раскрытой методологией** и индексом покрытия».

Ochilmagan metodologiya bilan Coverage Index ning o'zi ham yarim ishlaydi.
Indeks «bu hudud qamralganmi» deydi, lekin «tasdiqlangan» so'zi nimani
anglatishini aytmaydi: uchta xabarmi yoki sakkiztami, moderator xabari
oddiy foydalanuvchinikidan necha barobar og'irmi, «P90» qaysi usul bilan
hisoblanganmi. Bu sonlar `region_config` da yashaydi va E11 da **sozlanadi**,
ya'ni ular vaqt o'tishi bilan **o'zgaradi** — qo'lda yozilgan «Metodologiya»
sahifasi birinchi sozlashdayoq yolg'onga aylanardi.

Shuning uchun bu yerda matn yo'q. Bo'lim **jonli qiymatlardan** yig'iladi:
`Params` — bazadagi `region_config` dan, qolgani — kodning o'z
konstantalaridan (`sources.SOURCES`, `coverage.BAND_THRESHOLDS`,
`duration.BAND_EDGES`, `aggregate.MAX_UNASSIGNED_RATIO`). Hech bir son bu
faylda qayta yozilmagan; qayta yozilsa ikkita nusxa ajralib ketardi va
metodologiya aynan shu nuqtada yolg'on gapira boshlardi.

## Versiya

`version()` — barcha qiymatlar ustidan deterministik daydjest. U ikkita
savolga javob beradi:

1. **Vitrinaning raqami qaysi metodologiya bilan hisoblangan?** Javobdagi
   `version` sonlarni usulga bog'laydi, ya'ni saqlangan yoki eksport
   qilingan kesim keyinchalik ham o'qilishi mumkin.
2. **Metodologiya o'zgardimi?** `01` §347 chegara versiyasi almashganda
   «уведомление о смене методологии» ni talab qiladi. Odam qiymatlarni
   solishtirib o'tirmaydi — versiya o'zgardimi, shuni ko'radi.

Daydjest **qiymatlar** ustidan olinadi, tarjima matni ustidan emas: UZ
matnidagi vergul tuzatilgani metodologiya o'zgargani emas, va u
bildirishnoma yuborishga sabab bo'lmasligi kerak. Teskarisi ham qat'iy:
bitta parametr o'zgarsa versiya **albatta** o'zgaradi.

`blake2b`, `hash()` emas — `CLAUDE.md` §2: Python ning o'rnatilgan `hash()`
i har protsessda tasodifiylanadi, ya'ni ikkita `sveta-api` konteyneri bir
xil konfiguratsiyada turli versiya ko'rsatardi.

Modul **toza**: bazaga ham, `settings` ga ham murojaat qilmaydi — qiymatlar
chaqiruvchidan keladi (`coverage.py` bilan bir xil qoida).
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import blake2b

from app.clustering.params import Params
from app.reports import sources as report_sources
from app.stats import aggregate, coverage, duration

#: Bo'lim kodi → i18n kaliti prefiksi. Sarlavha `<prefiks>.title`, izoh
#: `<prefiks>.body`. Kalitlar `SECTION_KEYS` da **ochiq** sanaladi, chunki
#: f-satrdan yig'ilgan kalit statik tahlil uchun ko'rinmas bo'lardi
#: (`tests/test_i18n_key_contract.py` ning `KEY_FAMILIES` bo'limi).
KEY_PREFIX = "stats.methodology"

#: Metodologiya bo'limining o'z sarlavhasi (endpoint va CSV izohi uchun).
#:
#: **Literal, `f"{KEY_PREFIX}.title"` emas.** Bu yagona kalit jadvaldan
#: emas, to'g'ridan-to'g'ri chaqiriladi, ya'ni uni `KEY_TABLES` ga
#: qo'shish joyi yo'q; f-satr shaklida esa
#: `tests/test_i18n_key_contract.py` ning skaneri uni ko'rmasdi va
#: katalogdagi qator «o'lik» deb hisoblanardi. Prefiks bilan mosligini
#: o'sha faylning o'zi tekshiradi.
TITLE_KEY = "stats.methodology.title"

#: Daydjestning uzunligi baytda; o'n olti belgilik hex beradi. Bu sir emas,
#: **yorliq**: uni odam ikki kesimni solishtirish uchun ko'z bilan o'qiydi,
#: shuning uchun to'liq 64 bayt ortiqcha.
VERSION_BYTES = 8

#: Bo'limlar **ko'rsatiladigan** tartibda. Tartib ma'noli: avval xabar
#: qayerdan keladi (`sources`), keyin u qanday hodisaga aylanadi
#: (`confirmation`, `scale`), keyin vitrinaning o'zi (`coverage`,
#: `duration`, `reconciliation`), oxirida nima **chiqmaydi** (`privacy`).
SECTION_ORDER: tuple[str, ...] = (
    "sources",
    "confirmation",
    "scale",
    "coverage",
    "duration",
    "reconciliation",
    "privacy",
)

#: Har bir bo'lim qaysi hujjat bandidan kelib chiqqan. Bu satr javobda
#: ko'rinadi: metodologiyani o'qigan odam birlamchi manbani topa olsin.
SECTION_SPEC: dict[str, str] = {
    "sources": "06 §2",
    "confirmation": "06 §4",
    "scale": "06 §5",
    "coverage": "03 §R1.2",
    "duration": "01 §4",
    "reconciliation": "03 §R1.2",
    "privacy": "05 §3.1, §7.3",
}

#: Katalogdan so'raladigan barcha kalitlar, **literal** ro'yxat sifatida.
#: `tests/test_i18n_key_contract.py` teskari yo'nalishda aynan shu ro'yxatni
#: o'qiydi (`KEY_TABLES` naqshi).
SECTION_KEYS: tuple[str, ...] = tuple(
    f"{KEY_PREFIX}.{code}.{part}" for code in SECTION_ORDER for part in ("title", "body")
)


@dataclass(frozen=True)
class MethodologyValue:
    """Ochib beriladigan bitta qiymat: `confirm.coef = 0.5`.

    `code` — parametrning **haqiqiy** nomi (`region_config` kaliti yoki
    kod konstantasi), tarjima qilinadigan yorliq emas. Sabab amaliy: bu
    sonni sozlaydigan odam va uni o'qiydigan jurnalist bitta nomni
    ko'rishi kerak, aks holda «`confirm.coef` ni 0.6 qildik» degan gap
    vitrinadagi «Koeffitsient» qatoriga bog'lanmasdi.
    """

    code: str
    value: str


@dataclass(frozen=True)
class MethodologySection:
    """Metodologiyaning bitta bo'limi."""

    code: str
    spec: str
    values: tuple[MethodologyValue, ...]

    @property
    def title_key(self) -> str:
        return f"{KEY_PREFIX}.{self.code}.title"

    @property
    def body_key(self) -> str:
        return f"{KEY_PREFIX}.{self.code}.body"


@dataclass(frozen=True)
class Methodology:
    """To'liq bo'lim + uning versiyasi."""

    sections: tuple[MethodologySection, ...]
    version: str


@dataclass(frozen=True)
class PublicLimits:
    """`settings` dan keladigan qiymatlar — modul toza qolishi uchun.

    Ular `Params` dan **ajratilgan** va sabab bor: `Params` mintaqa
    kesimida bazada yashaydi va E11 da sozlanadi, bulari esa deploy
    darajasidagi sozlamalar. Bitta `dict` ga qo'shib yuborish
    «bu sonni kim o'zgartiradi» degan farqni yo'qotardi.
    """

    h3_resolution: int
    min_reports: int
    time_rounding_min: int
    coverage_window_days: int
    target_penetration: float
    autoclose_after_min: int


def _fmt(value: float | int | str) -> str:
    """Qiymatning kanonik matni.

    Butun songa teng `float` nuqtasiz yoziladi: `region_config` dagi
    `3` va `3.0` — **bitta** parametr qiymati, va ular turli versiya
    berishi metodologiya o'zgargandek ko'rinardi (`from_mapping` hamma
    narsani `float` orqali o'tkazadi, ya'ni bu holat nazariy emas).
    """
    if isinstance(value, str):
        return value
    number = float(value)
    return str(int(number)) if number.is_integer() else repr(number)


def _values(items: dict[str, float | int | str]) -> tuple[MethodologyValue, ...]:
    """`{kod: qiymat}` → qiymatlar, **kod bo'yicha saralangan**.

    Saralash ko'rinish uchun emas, barqarorlik uchun: chaqiruvchidagi
    qatorlar joy almashsa versiya o'zgarmasligi kerak — kodning
    tartibi metodologiya emas.
    """
    return tuple(MethodologyValue(code=code, value=_fmt(items[code])) for code in sorted(items))


def _sources_section() -> MethodologySection:
    """`06` §2 — xabar manbalari va ularning og'irliklari.

    Rasmiy manbalar (`weight = 0`) ham ro'yxatda qoladi: ularning noli
    «hisobga olinmaydi» degani emas, `06` §2.2 bo'yicha «og'irlikli
    hisobdan **tashqarida**, hodisani darhol tasdiqlaydi». Ro'yxatdan
    tushib qolsa o'quvchi rasmiy e'lon umuman ishlatilmaydi deb o'ylardi.
    """
    items: dict[str, float | int | str] = {
        f"source.{source.code}": source.weight for source in report_sources.SOURCES
    }
    items["user_factor.divisor"] = report_sources.TRUST_DIVISOR
    items["user_factor.min"] = report_sources.USER_FACTOR_MIN
    items["user_factor.max"] = report_sources.USER_FACTOR_MAX
    return MethodologySection(
        code="sources",
        spec=SECTION_SPEC["sources"],
        values=_values(items),
    )


def _confirmation_section(params: Params) -> MethodologySection:
    """`06` §4 — moslashuvchan tasdiqlash chegarasi.

    `spread.min_distance_m` ham shu yerda: u chegarani emas, **kim
    sanaladi** ni belgilaydi (`06` §2.3 mustaqillik). Ikkalasi birga
    o'qilishi kerak — «uchta foydalanuvchi» degan gapning ma'nosi
    ular bir-biridan qancha uzoq turishiga bog'liq.
    """
    confirm = params.confirm
    return MethodologySection(
        code="confirmation",
        spec=SECTION_SPEC["confirmation"],
        values=_values(
            {
                "confirm.min_users": confirm.min_users,
                "confirm.coef": confirm.coef,
                "confirm.floor": confirm.floor,
                "confirm.ceil": confirm.ceil,
                "spread.min_distance_m": params.spread_min_distance_m,
            }
        ),
    )


def _scale_section(params: Params) -> MethodologySection:
    """`06` §5 — masshtab narvoni va uning qamrov to'sig'i."""
    scale, guard = params.scale, params.guard
    return MethodologySection(
        code="scale",
        spec=SECTION_SPEC["scale"],
        values=_values(
            {
                "scale.coef": scale.coef,
                "scale.mahalla_floor": scale.mahalla_floor,
                "scale.mahalla_ceil": scale.mahalla_ceil,
                "scale.district_floor": scale.district_floor,
                "scale.district_ceil": scale.district_ceil,
                "scale.cell_ratio_mahalla": scale.cell_ratio_mahalla,
                "scale.cell_ratio_district": scale.cell_ratio_district,
                "guard.min_active_district": guard.min_active_district,
                "guard.min_active_mahalla": guard.min_active_mahalla,
                "avg_household_size": params.avg_household_size,
            }
        ),
    )


def _coverage_section(limits: PublicLimits) -> MethodologySection:
    """`03` §R1.2 — Coverage Index: pog'ona chegaralari va oynasi.

    Pog'ona chegaralari `coverage.BAND_THRESHOLDS` dan o'qiladi, ya'ni
    ular kodda siljisa metodologiya ham siljiydi. Aynan shu qator
    jurnalistga «medium» so'zi nimani anglatishini aytadi.
    """
    items: dict[str, float | int | str] = {
        f"coverage.band.{band}": threshold for threshold, band in coverage.BAND_THRESHOLDS
    }
    items["coverage.window_days"] = limits.coverage_window_days
    items["coverage.target_penetration"] = limits.target_penetration
    return MethodologySection(
        code="coverage",
        spec=SECTION_SPEC["coverage"],
        values=_values(items),
    )


def _duration_section(limits: PublicLimits) -> MethodologySection:
    """`01` §4 — davomiylik kesimi: usul, narvon va namunaning quyi chegarasi."""
    items: dict[str, float | int | str] = {
        f"duration.edge_{index}": edge for index, edge in enumerate(duration.BAND_EDGES)
    }
    # Usulning **nomi** ham qiymat: «P90» so'zi bir necha xil hisoblanadi
    # va qaysi biri ekanini aytmaslik sonni taqqoslab bo'lmas qilardi.
    items["duration.percentile_method"] = "percentile_cont"
    items["duration.min_sample"] = duration.MIN_SAMPLE
    items["duration.max_ongoing_ratio"] = duration.MAX_ONGOING_RATIO
    items["duration.max_timeout_ratio"] = duration.MAX_TIMEOUT_RATIO
    items["duration.autoclose_after_min"] = limits.autoclose_after_min
    return MethodologySection(
        code="duration",
        spec=SECTION_SPEC["duration"],
        values=_values(items),
    )


def _reconciliation_section() -> MethodologySection:
    """`03` §R1.2 chiqish mezoni — yig'indi va umumiy natija farqi."""
    return MethodologySection(
        code="reconciliation",
        spec=SECTION_SPEC["reconciliation"],
        values=_values({"stats.max_unassigned_ratio": aggregate.MAX_UNASSIGNED_RATIO}),
    )


def _privacy_section(limits: PublicLimits) -> MethodologySection:
    """`05` §3.1 va §7.3 — nima chiqmaydi.

    Metodologiyaning bu qismi hisoblash usuli emas, **cheklov**: uchta
    xabardan kam hodisa agregatga kirmaydi, vaqt yaxlitlanadi,
    koordinata H3 katakchasiga tushadi. O'quvchi «nima uchun bu yerda
    nol turibdi» degan savolga javobni shu yerdan topadi.
    """
    return MethodologySection(
        code="privacy",
        spec=SECTION_SPEC["privacy"],
        values=_values(
            {
                "geo.h3_resolution": limits.h3_resolution,
                "public.min_reports": limits.min_reports,
                "public.time_rounding_min": limits.time_rounding_min,
            }
        ),
    )


def _canonical(sections: tuple[MethodologySection, ...]) -> str:
    """Versiya hisoblanadigan matn.

    Bo'limlar **kod bo'yicha** saralanadi, `SECTION_ORDER` bo'yicha emas:
    ko'rsatish tartibini o'zgartirish metodologiyani o'zgartirmaydi.
    `spec` ham kiradi — qiymat o'sha qolib, uning manbasi boshqa bandga
    ko'chgan bo'lsa, bu ham o'zgarish.
    """
    lines = []
    for section in sorted(sections, key=lambda s: s.code):
        for value in section.values:
            lines.append(f"{section.code}|{section.spec}|{value.code}={value.value}")
    return "\n".join(lines)


def version(sections: tuple[MethodologySection, ...]) -> str:
    """Qiymatlar ustidan deterministik yorliq (`blake2b`, `hash()` emas)."""
    digest = blake2b(_canonical(sections).encode("utf-8"), digest_size=VERSION_BYTES)
    return digest.hexdigest()


def build(params: Params, limits: PublicLimits) -> Methodology:
    """Jonli qiymatlardan to'liq metodologiya bo'limi.

    Bo'sh bo'lim — xato, o'tkazib yuboriladigan holat emas: hech narsa
    ochmaydigan sarlavha ochiqlikning ko'rinishini beradi, mazmunini
    emas, va u jimgina paydo bo'lishi mumkin (masalan `SOURCES` bo'shab
    qolsa).
    """
    builders = {
        "sources": _sources_section(),
        "confirmation": _confirmation_section(params),
        "scale": _scale_section(params),
        "coverage": _coverage_section(limits),
        "duration": _duration_section(limits),
        "reconciliation": _reconciliation_section(),
        "privacy": _privacy_section(limits),
    }
    # Qurilgan, lekin `SECTION_ORDER` da yo'q bo'lim javobga **umuman**
    # tushmasdi va buni hech narsa aytmasdi — `builders[code]` faqat
    # teskari xatoni (ro'yxatda bor, quruvchisi yo'q) ushlaydi.
    unlisted = [code for code in builders if code not in SECTION_ORDER]
    if unlisted:
        raise ValueError(f"metodologiya bo'limi ko'rsatilmaydi: {unlisted}")
    sections = tuple(builders[code] for code in SECTION_ORDER)
    empty = [section.code for section in sections if not section.values]
    if empty:
        raise ValueError(f"metodologiya bo'limi bo'sh: {empty}")
    return Methodology(sections=sections, version=version(sections))
