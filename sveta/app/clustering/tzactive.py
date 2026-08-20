"""TZ §2.3 ning maxrajini bazadan oladi va `tzcount` ga uzatadi (`2.3-source`).

**Nima uchun bu modul bor.** `app/clustering/tzcount.py` §2.3 ning
arifmetikasini to'liq biladi — `threshold()` porogni `max(faollar, 2)`
gacha tushiradi va `sparse` bayrog'ini ko'taradi — lekin bitta savolga
javob bera olmaydi: «zonada nechta faol foydalanuvchi bor». Javob
`reports` jadvalida, `tzcount` esa **toza** modul.

191-run bo'shliqni ochiq yozib qoldirgan edi: `tzwitness.load()` ning
`active_users` argumenti **sukut qiymatisiz**, ya'ni chaqiruvchi javob
berishga majbur, ammo javobni topadigan yo'l repoda umuman yo'q edi.
Bu modul aynan o'sha yo'l — 190-run ning `tzsource` i (§3 ning
maxraji) va 191-run ning `tzwitness` i (§1.1(3) ning uy katagi) bilan
bir xil shakl.

## Bo'sh xarita nima qiladi — va nima uchun bu xavfsiz tomon

`active_users` bo'sh bo'lsa §2.3 **umuman ishlamaydi**: `threshold()`
`None` ni «noma'lum» deb o'qiydi va §2.1 ning bazaviy porogini
qoldiradi. Ya'ni bugungi holat (maxrajsiz) kam odamli zonani hech
qachon tasdiqlamaydi — TZ ning «без этого правила частный сектор и
малые махалли не подтвердят ничего никогда» jumlasi so'zma-so'z
bajarilib turibdi. Nosozlik **jim**, chunki qolgan hamma zona
to'g'ri ishlaydi.

## Nima uchun sanoq Python da qilinmaydi

Xom qatorlarni (`user_id` + uchala katak) o'qib, darajalarni Python da
yig'ish oson yo'l edi va u jimgina noto'g'ri: bitta odam bitta
kvartalning ikkita uy katagidan xabar bergan bo'lsa, kvartal
darajasida u ikki marta sanalardi. `count(distinct …)` har daraja
uchun alohida bazaga aytiladi (`reports.queries.zone_users_stmt`), bu
modul esa faqat **rezolyutsiyani darajaga** o'giradi.

## Ikki marta kelgan zona

`GROUP BY` bir xil `(rezolyutsiya, katak)` ni ikki marta qaytarmaydi,
ya'ni bu holat bo'lmasligi kerak. Bo'lib qolsa **kattasi** olinadi,
kichigi emas: §2.3 uchun katta maxraj — qoidani **o'chiradigan**
tomon (porog §2.1 da qoladi), kichigi esa porogni tushiradi. Xato
qilinsa, qat'iyroq tomonga.

## Т-4 va Т-1

Modulda soat yo'q: mavjudlik ham, faollik ham vaqt bilan
cheklanmaydi (`zone_users` izohidagi ikkita sabab). §7 ning soni ham
yo'q — rezolyutsiyalar `tzcount.LEVEL_RESOLUTION` dan olinadi, ya'ni
daraja↔rezolyutsiya jadvali loyihada **bitta** joyda qoladi.

## Bu modul hali chaqirilmaydi

`clustering.service.evaluate()` statusni hamon `06` ning og'irlikli
hisobi bilan qaraydi. Ulash keyingi qadam va u bitta ochiq savolga
bog'liq: TZ **zonani** tasdiqlaydi (r10/r9/r8), `outages` esa
klaster — qaysi zonaning verdikti hodisani tasdiqlaydi degan javob
§2.1 da yo'q (`PROGRESS.md`, «Ochiq savollar»).
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.clustering.tzcount import LEVEL_RESOLUTION, Level
from app.reports import queries as report_queries

# `SPEC` konstantasi bu yerda **ataylab yo'q** — `tzsource` va
# `tzwitness` bilan bir xil sabab: bu ulash qatlami, §2 ning vitrinasi
# `tzstatus` da qoladi.

#: Rezolyutsiya → daraja. `LEVEL_RESOLUTION` ning teskarisi va u
#: **qo'lda takrorlanmaydi**: jadval ikki joyda yozilsa, r11 ni
#: darajaga aylantirib qo'yadigan kun kelardi.
RESOLUTION_LEVEL: dict[int, Level] = {
    resolution: level for level, resolution in LEVEL_RESOLUTION.items()
}


@dataclass(frozen=True)
class ActiveZones:
    """§2.3 ning maxraji: zona → faol foydalanuvchilar soni.

    `counts` — javob (`tzwitness.load(active_users=…)` ning kirishi);
    `unknown` **javob emas, diagnostika**: darajaga aylantirib
    bo'lmagan rezolyutsiyalar. Bugun bo'sh bo'lishi kerak, lekin
    so'rovga to'rtinchi daraja qo'shilsa u jimgina yo'qolmaydi.
    """

    counts: dict[tuple[Level, str], int]
    #: Tanilmagan rezolyutsiyalar, tartiblangan.
    unknown: tuple[int, ...]

    def of(self, level: Level, cell: str) -> int | None:
        """Zonadagi faollar soni; zona umuman uchramasa `None`.

        `None` — «noma'lum», `0` emas: `tzcount.threshold()` ikkovini
        **har xil** o'qiydi (noma'lumda §2.3 qo'llanmaydi, nolda
        porog pastki chekkacha tushadi).
        """
        return self.counts.get((level, cell))

    @property
    def zones(self) -> tuple[tuple[Level, str], ...]:
        """Maxraji ma'lum zonalar, tartiblangan (Т-3)."""
        return tuple(sorted(self.counts))


def to_counts(rows: Iterable[report_queries.ZoneUsersRow]) -> ActiveZones:
    """So'rov natijasini `tzcount` ning kirishiga aylantiradi.

    Toza funksiya: bazaga ham, soatga ham murojaat qilmaydi.
    """
    counts: dict[tuple[Level, str], int] = {}
    # Ro'yxat, to'plam emas: `set` ning yurish tartibi tasodifiy va
    # `sorted` ni undan olib tashlagan mutant kichik sonlarda **jimgina
    # o'tib ketardi. Takrorini `set` oxirida yechadi.
    unknown: list[int] = []

    for row in rows:
        level = RESOLUTION_LEVEL.get(row.resolution)
        if level is None:
            unknown.append(row.resolution)
            continue
        key = (level, row.cell)
        current = counts.get(key)
        # Modul izohidagi sabab: takror kelgan zonada kattasi yutadi.
        counts[key] = row.users if current is None else max(current, row.users)

    return ActiveZones(
        counts={key: counts[key] for key in sorted(counts)},
        unknown=tuple(sorted(set(unknown))),
    )


async def load(session: AsyncSession, *, region_id: uuid.UUID) -> ActiveZones:
    """Mintaqaning uchala darajasidagi maxrajni o'qiydi.

    Bitta so'rov: `zone_users` uchala guruhlashni `UNION ALL` bilan
    yig'adi. Zona kesimida alohida so'rov (N+1) ataylab qilinmaydi —
    §2.3 hodisadagi **har** zona uchun so'raladi va shaharda ular
    yuzlab bo'ladi.

    `region_id` hodisaning mintaqasi bo'lishi kerak: sanoq `outage_id`
    bo'yicha, maxraj esa mintaqa bo'yicha filtrlanadi, ya'ni boshqa
    mintaqa berilsa `active_users >= have` kafolati buziladi
    (`zone_users` izohi).
    """
    rows = await report_queries.zone_users(session, region_id=region_id)
    return to_counts(rows)
