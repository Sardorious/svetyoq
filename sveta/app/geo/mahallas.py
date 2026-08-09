"""Mahallalar spravochnigining xulosasi — toza modul (`01` §16, FR-S-802).

`01` §16 API deltasi bitta qator beradi: «`GET /geo/mahallas` — новый
эндпоинт: справочник махаллей с полигонами и **версией**». Poligonlar
so'rov qatlamining ishi, versiya va uning atrofidagi qarorlar — shu
modulniki. Modul bazasiz va konfiguratsiyasiz: kirish — qatorlarning
neytral kesimi, chiqish — javobning `registry` bloki.

**Nima uchun bu `app.stats.boundaries` ning nusxasi emas.** Ikkalasi ham
«spravochnik versiyasi» savoliga javob beradi, lekin `mahallas` jadvali
`districts` dan uchta muhim joyda farq qiladi (`05` §2.1) va farqlarning
har biri shu yerdagi qarorni o'zgartiradi:

1. **`code` ustuni yo'q.** Ya'ni bir mahallaning ikki versiyasini
   bog'laydigan barqaror kalit yo'q. Yagona amaliy o'rinbosar —
   `(district_id, name_uz)` juftligi; shuning uchun `mahallas` soni
   aynan shu juftliklar bo'yicha sanaladi va bu javobda ochiq yozilgan.
2. **`license` va `source_ref` ustunlari yo'q.** `districts` javobi
   `licenses`/`attribution` beradi (OSM ODbL atributsiz qayta
   tarqatishni taqiqlaydi), bu yerda esa berish uchun ma'lumot yo'q.
   Bo'sh ro'yxat «litsenziya cheklovi yo'q» degan yolg'onni aytardi,
   shuning uchun javobda `sources` va **doimiy dislaymer** bor.
3. **Jadval E17 gacha bo'sh** (`05` §2.1 izohi). Ya'ni «bo'sh javob» —
   kutilgan holat, xato emas. Lekin uni **jimgina** qaytarish FR-S-802
   degradatsiyasini ko'rinmas qilardi: mijoz bo'sh ro'yxatni «bu yerda
   mahalla yo'q» deb o'qirdi, aslida esa «spravochnik hali
   to'ldirilmagan». Shuning uchun bo'shlikning **ikki xil sababi**
   ajratilgan va har biri o'z ogohlantirishiga ega.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

#: Mintaqada mahalla qatori **umuman** yo'q — spravochnik to'ldirilmagan
#: (E17). FR-S-802: «при отсутствии полигона привязка выполняется только
#: к району без ошибки» — ya'ni bu xato emas, **degradatsiya**, va u
#: ko'rinishi kerak.
WARNING_MISSING = "geo.warning.mahallas_missing"

#: Spravochnik bo'sh emas, lekin **so'ralgan paytda** amal qilgan qator
#: yo'q. `WARNING_MISSING` dan ataylab ajratilgan: birinchisi «hech
#: qachon bo'lmagan», ikkinchisi «o'sha sanada hali (yoki endi) yo'q».
#: Bitta ogohlantirish ikkalasini qoplaganida `?at=` bilan o'tmishga
#: qaragan mijoz spravochnikni umuman yo'q deb o'ylardi.
WARNING_EMPTY_SLICE = "geo.warning.mahallas_empty_slice"

#: `mahallas` da `license` ustuni yo'q (`05` §2.1) — shuning uchun javob
#: `districts` dagidek `licenses`/`attribution` bera olmaydi. Dislaymer
#: **doimiy**: u ma'lumotga emas, sxemaga bog'liq va o'zgarmaydi.
DISCLAIMER_SOURCE = "geo.disclaimer.mahalla_source"


@dataclass(frozen=True)
class MahallaFact:
    """Bitta mahalla versiyasining neytral kesimi.

    So'rov qatoridan (`geo.queries.MahallaRow`) ataylab kichikroq:
    geometriya ham, identifikator ham bu yerda kerak emas — versiya
    haqidagi savol poligonning o'ziga bog'liq emas (`app.stats.boundaries`
    dagi bilan bir xil sabab).
    """

    #: Mahallaning tumani. `district_id`, `district_code` emas: kod
    #: versiyalanadi (`districts` da bir kod bir necha qator), `id` esa
    #: aynan bitta chegara versiyasini bildiradi.
    district_id: str
    name_uz: str
    valid_from: datetime
    valid_to: datetime | None
    source: str

    @property
    def identity(self) -> tuple[str, str]:
        """Versiyalar bo'ylab barqaror kalit — `code` ustuni o'rniga.

        `05` §2.1 da `mahallas.code` yo'q. Nom o'zgarishi mumkin, lekin
        chegara versiyalanganda odatda geometriya o'zgaradi, nom emas —
        ya'ni juftlik amalda bitta mahallani ushlab turadi. Aniq emasligi
        javobda yashirilmaydi: `mahallas` soni «taxminiy» emas, balki
        **aynan shu qoida bo'yicha** hisoblangani hujjatda yozilgan.
        """
        return (self.district_id, self.name_uz)


@dataclass(frozen=True)
class MahallaRegistry:
    """Javobning `registry` bloki (`01` §16 «с полигонами и версией»)."""

    #: Mintaqada mahalla qatori bormi — **har qanday davrda**. Bo'sh
    #: kesim (`count == 0`) bilan aralashtirmang: bittasi spravochnikning
    #: o'zi haqida, ikkinchisi so'ralgan sana haqida.
    available: bool
    #: Qaytarilgan kesimning **eng so'nggi** `valid_from` sanasi (ISO,
    #: kun aniqligida). `05` §2.1 da alohida versiya raqami yo'q va uni
    #: shu yerda o'ylab topish chetlashish bo'lardi (`app.stats.boundaries`
    #: dagi bilan bir xil qaror). Bo'sh kesimda `None`.
    version: str | None
    #: Kesimdagi qatorlar soni.
    versions: int
    #: Turli mahallalar soni — `(district_id, name_uz)` juftligi bo'yicha.
    #: `versions` dan kichik bo'lishi mumkin emas; teng bo'lmasa, demak
    #: kesimda bitta mahallaning bir nechta versiyasi bor.
    mahallas: int
    #: Kesim nechta tumanga tegishli.
    districts: int
    sources: tuple[str, ...]
    warnings: tuple[str, ...]


def _iso_day(moment: datetime) -> str:
    return moment.date().isoformat()


def summarize(facts: list[MahallaFact], *, available: bool) -> MahallaRegistry:
    """Qatorlardan javobning `registry` blokini yig'adi.

    `available` **bazadan alohida** keladi va bu ataylab: uni
    `bool(facts)` dan chiqarib bo'lmaydi. `?at=` bilan spravochnik
    to'ldirilishidan oldingi sanani so'ragan mijoz bo'sh kesim oladi,
    holbuki spravochnik mavjud — bu ikki holat bir xil ogohlantirishga
    tushib qolsa, javob **noto'g'ri** bo'lardi.

    Bo'sh emas kesimda ogohlantirish yo'q: hamma narsa joyida.
    """
    if not facts:
        return MahallaRegistry(
            available=available,
            version=None,
            versions=0,
            mahallas=0,
            districts=0,
            sources=(),
            warnings=(WARNING_EMPTY_SLICE if available else WARNING_MISSING,),
        )

    return MahallaRegistry(
        available=True,
        version=_iso_day(max(f.valid_from for f in facts)),
        versions=len(facts),
        mahallas=len({f.identity for f in facts}),
        districts=len({f.district_id for f in facts}),
        sources=tuple(sorted({f.source for f in facts})),
        warnings=(),
    )
