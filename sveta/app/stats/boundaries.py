"""Chegaralar spravochnigining versiyasi — toza modul (`01` FR-S-803, P0).

FR-S-803 ikkita talabdan iborat va ular **alohida** narsalar:

1. «историческая статистика пересчитывается по границам, действовавшим
   на момент инцидента» — bu `app.stats.service` ning ishi (davr bo'yicha
   tuman kesimi, `geo.queries.districts_for_period`);
2. «в ответе указана версия справочника» — bu shu modul.

Nima uchun ikkinchisi kerak. OQ-01: ma'muriy qayta tashkil etish tarixni
nolga tushirmasligi kerak. Lekin chegara o'zgargandan keyin ikki davrning
raqamlari **bir xil nomlar ostida** turgani bilan bir xil hududni
anglatmaydi. Javobda versiya bo'lmasa, buni o'quvchi bilmaydi va ikki
davrni to'g'ridan-to'g'ri taqqoslab qo'yadi — `01` §26 dagi «noto'g'ri
xulosa» xavfi aynan shu.

Modul toza: bazasiz, konfiguratsiyasiz, `datetime` ustidagi arifmetikadan
boshqa hech narsa qilmaydi.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

#: Davr chegara o'zgarishini kesib o'tsa chiqadigan ogohlantirish.
#: Alohida kalit, `stats.warning.unassigned` emas: u «hodisa tumansiz
#: qoldi» degani, bu esa «tumanlarning o'zi boshqacha edi».
WARNING_CHANGED = "stats.warning.boundaries_changed"


@dataclass(frozen=True)
class BoundaryFact:
    """Bitta chegara versiyasining neytral kesimi.

    `geo.queries.DistrictVersionRow` dan ataylab kichikroq: bu yerda
    geometriya ham, identifikator ham yo'q — versiya haqidagi savol
    poligonning o'ziga bog'liq emas.
    """

    code: str
    valid_from: datetime
    valid_to: datetime | None
    source: str
    license: str


@dataclass(frozen=True)
class BoundarySet:
    """Davr uchun spravochnik versiyasi (javobning majburiy qismi)."""

    #: Davrda amal qilgan **eng so'nggi** kesimning sanasi (ISO, kun
    #: aniqligida). Versiya raqami emas, sana: `05` §2.1 da chegaralar
    #: `valid_from` bilan versiyalanadi, alohida raqam yo'q va uni shu
    #: yerda o'ylab topish spetsifikatsiyadan chetlashish bo'lardi.
    version: str | None
    #: Davrda amal qilgan tuman versiyalari soni. Tumanlar sonidan
    #: **katta** bo'lishi mumkin — aynan shu holat o'zgarish belgisi.
    versions: int
    districts: int
    sources: tuple[str, ...]
    licenses: tuple[str, ...]
    #: Davr ichida chegara o'zgardimi. `True` bo'lsa davrning boshi va
    #: oxiri turli hududlarni anglatadi va ularni taqqoslab bo'lmaydi.
    changed_in_period: bool


def _iso_day(moment: datetime) -> str:
    return moment.date().isoformat()


def summarize(facts: list[BoundaryFact], *, start: datetime, end: datetime) -> BoundarySet:
    """Chegara versiyalaridan javobdagi `boundaries` blokini yig'adi.

    `changed_in_period` ikki xil yo'l bilan rost bo'ladi va ikkalasi ham
    kerak:

    - versiya davr **ichida** ochilgan (`valid_from > start`) — yangi
      chegara kuchga kirdi;
    - versiya davr **ichida** yopilgan (`valid_to < end`) — eski chegara
      kuchdan qoldi.

    Bittasi yetarli emas: tuman bo'linsa birinchisi rost, tumanlar
    birlashsa esa faqat ikkinchisi.

    Bo'sh ro'yxat — mintaqada chegara umuman yo'q (import qilinmagan).
    `version = None` shuni ochiq aytadi; bu yerda `start` sanasini
    qaytarish «spravochnik bor» degan yolg'on bo'lardi.
    """
    if not facts:
        return BoundarySet(
            version=None,
            versions=0,
            districts=0,
            sources=(),
            licenses=(),
            changed_in_period=False,
        )

    opened = any(f.valid_from > start for f in facts)
    closed = any(f.valid_to is not None and f.valid_to < end for f in facts)
    return BoundarySet(
        version=_iso_day(max(f.valid_from for f in facts)),
        versions=len(facts),
        districts=len({f.code for f in facts}),
        sources=tuple(sorted({f.source for f in facts})),
        licenses=tuple(sorted({f.license for f in facts})),
        changed_in_period=opened or closed,
    )
