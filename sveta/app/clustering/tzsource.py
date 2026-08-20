"""TZ §3 ning maxrajini bazadan oladi va `tzscale` ga uzatadi (`3-source`).

**Nima uchun bu modul bor.** `app/clustering/tzscale.py` §3 ning
arifmetikasini to'liq biladi, lekin bitta savolga javob bera olmaydi:
«qaysi kvartallarda bizning foydalanuvchimiz bor». Javob `reports`
jadvalida, tzscale esa **toza** modul — bazani ham, soatni ham
ko'rmaydi. 182-rundan beri o'sha bo'shliq `RULES` ning `3-source`
qatorida `built=False` bo'lib turgan edi, ya'ni §3 ni chaqiradigan
mahsulot kodi ham yo'q edi.

187-run bo'shliqning narxini o'lchadi: `from_zone_verdicts()` ning
`blocks_with_users` argumenti sukut bo'yicha bo'sh edi va argumentni
**yozmagan** chaqiruvchi jimgina boshqa maxrajga o'tardi — «bugun
xabar qilgan kvartallar». Sukut qiymati o'shanda olib tashlandi, lekin
javobni topadigan yo'l qo'shilmadi: chaqiruvchi endi majbur, ammo
qo'lidan kelmaydi. Bu modul aynan o'sha yo'l.

## Chegaradagi katak — bu modulning yagona qarori

`from_zone_verdicts()` `district_of` ni **`Mapping[str, str]`** deb
oladi, ya'ni bitta kvartal bitta tumanga tegishli. Baza esa bunga
kafolat bermaydi: r9 katagi (~349 m) tuman chegarasini kesib o'tishi
mumkin va o'sha kataklardagi xabarlar ikki xil `district_id` bilan
yozilgan bo'ladi (`district_id` yozish paytida biriktiriladi —
`app/reports/models.py`).

Bunday katakni **ikkala** tumanning maxrajiga qo'shish oson yo'l edi
va u ikkita narsani buzardi:

1. Bitta ko'chadagi uzilish ikkita tumanning sanoqchisini ko'tarardi
   — §3 ning birinchi jumlasi («сто сообщений с одной улицы не
   доказывают, что район без света») aynan buni taqiqlaydi.
2. Shahar darajasi tumanlarning **natijasini** sanaydi, ya'ni ikki
   marta sanalgan kvartal shaharga ham ikki marta ta'sir qilardi.

Shuning uchun katak bitta tumanga biriktiriladi: **foydalanuvchisi
ko'p bo'lgani yutadi**, tenglikda tumanning identifikatori bo'yicha
kichigi (Т-3 — bir xil ma'lumot bir xil javob bersin; bazadan kelgan
tartibga tayanish aynan shu qorovulni buzardi). Tanlanmagan tomon
yo'qolmaydi — u `straddling` da qoladi va reyestr vitrinasida
ko'rinadi.

## Tumani yo'q katak

`district_id` `NULL` bo'lishi mumkin (`05` §5.3 — nuqta birorta
tuman poligoniga tushmagan). Bunday katak **maxrajga ham, sanoqqa ham
kirmaydi**: uni «noma'lum tuman» chelagiga yig'ish ikkita har xil
tumanning kvartallarini bitta porogga qo'shardi. Lekin u jimgina
tashlanmaydi ham — `unassigned` da qaytadi, chunki bu defektning
ko'rsatkichi (`05` §5.3) va uning o'sishi §3 ning maxrajini
kamaytiradi.

Modul **statusga tegmaydi** (Т-5) va **soatga qaramaydi** (Т-4):
mavjudlik vaqtga bog'liq emas (`reports.queries.blocks_with_users`
izohi).
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.reports import queries as report_queries

# `SPEC` konstantasi bu yerda **ataylab yo'q**: u reyestr modulining
# belgisi (`tests/test_admin_registries.py` uni indeksdan qidiradi), bu
# esa ulash qatlami — §3 ning vitrinasi `tzscale.RULES` da qoladi.
# Boshqa ulash qatlamlari (`tzpanel`, `tzreceipts`, `tzintake`) ham
# shunday.


@dataclass(frozen=True)
class BlockRegistry:
    """§3 ning maxraji: kvartal → tuman xaritasi va uning nuqsonlari.

    `district_of` va `blocks` — `tzscale.from_zone_verdicts()` ning
    ikkita argumenti; qolgan ikkita maydon **javob emas, diagnostika**:
    ular bo'sh emasligini chaqiruvchi ko'rishi kerak, aks holda maxraj
    sababsiz kichrayadi.
    """

    #: Kvartal (r9) → tuman identifikatori (matn). Т-3: tartiblangan.
    district_of: dict[str, str]
    #: Foydalanuvchisi bor kvartallar — tumani aniqlangalari.
    blocks: tuple[str, ...]
    #: Tumani aniqlanmagan kvartallar (`05` §5.3 defekti).
    unassigned: tuple[str, ...]
    #: Ikki va undan ortiq tumanda uchragan kvartallar. Har biri bitta
    #: tumanga biriktirilgan, lekin fakt yo'qolmaydi.
    straddling: tuple[str, ...]

    @property
    def districts(self) -> tuple[str, ...]:
        """Foydalanuvchisi bor tumanlar — §3 ning shahar maxraji.

        Shahar darajasi tumanlarning natijasidan yig'iladi
        (`tzscale.city`), ya'ni bu ro'yxat `tzscale` ga to'g'ridan-to'g'ri
        uzatilmaydi. U vitrinada va tekshiruvda kerak: tumanlar soni
        maxrajning kattaligi haqidagi yagona ko'rsatkich.
        """
        return tuple(sorted(set(self.district_of.values())))


def resolve(rows: Iterable[report_queries.BlockUsersRow]) -> BlockRegistry:
    """So'rov natijasini `tzscale` ning kirishiga aylantiradi.

    Toza funksiya: bazaga ham, soatga ham murojaat qilmaydi — shuning
    uchun chegaradagi katakning qarori testda fikstyurasiz o'lchanadi.
    """
    best: dict[str, tuple[int, str]] = {}
    seen: dict[str, set[str]] = {}
    unassigned: set[str] = set()

    for row in rows:
        if row.district_id is None:
            unassigned.add(row.h3_r9)
            continue
        district = str(row.district_id)
        seen.setdefault(row.h3_r9, set()).add(district)
        current = best.get(row.h3_r9)
        # Ko'p foydalanuvchili tomon yutadi; tenglikda identifikatori
        # kichigi. Bazadan kelgan tartib bu yerda o'qilmaydi (Т-3):
        # `ORDER BY` bo'lsa ham unga tayanish qorovulni bo'sh qilardi.
        if current is None:
            best[row.h3_r9] = (row.users, district)
            continue
        users, chosen = current
        if row.users > users or (row.users == users and district < chosen):
            best[row.h3_r9] = (row.users, district)

    district_of = {cell: choice[1] for cell, choice in sorted(best.items())}
    return BlockRegistry(
        district_of=district_of,
        blocks=tuple(sorted(district_of)),
        unassigned=tuple(sorted(unassigned)),
        straddling=tuple(sorted(cell for cell, names in seen.items() if len(names) > 1)),
    )


async def load(session: AsyncSession, *, region_id: uuid.UUID) -> BlockRegistry:
    """§3 ning maxrajini mintaqa bo'yicha o'qiydi.

    Bitta so'rov: kvartallar bo'yicha aylanish N+1 berardi va
    `blocks_with_users` ning o'zi allaqachon tuman kesimida guruhlangan.
    """
    return resolve(await report_queries.blocks_with_users(session, region_id=region_id))
