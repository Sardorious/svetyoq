"""TZ §1.1 ning sanog'ini bazaga ulaydi: dalil qatorlari va uy kataklari.

**Nima uchun bu modul bor.** `app/clustering/tzcount.py` §1.1 ning
uchala shartini biladi, lekin uchinchisiga kerakli ma'lumotni o'zi
topa olmaydi: «ни один из аккаунтов не имеет домашней клетки,
совпадающей с другим на уровне r11». `Evidence.home_r11` — argument,
ya'ni javob **chaqiruvchida**; 190-run esa `blocks_with_users` ning
izohida buni ochiq yozdi: «foydalanuvchining uy katagi hech qayerda
saqlanmaydi».

Natijada bugungi holat quyidagicha edi: `count_witnesses()` ni bazadan
kelgan qatorlar bilan chaqirgan birinchi chaqiruvchi `home_r11` ni
`None` qoldirar, `seen_homes` bo'sh qolar va §1.1(3) **jimgina
o'chib** ketardi. Nosozlik ko'rinmasdi — sanoq ishlayotgandek
tuyulardi, faqat bitta kvartiradagi uchta akkaunt uchta guvoh bo'lib
sanalardi, ya'ni TZ ning yagona anti-sibil sharti bekor bo'lardi.

## Uy katagi qayerdan olinadi

Sxemadagi yagona **doimiy va foydalanuvchi o'zi ko'rsatgan** nuqta —
obuna (`subscriptions`). Xabarning nuqtasi bunga yaramaydi: u odam
**turgan** joyni bildiradi, `geom_exact` esa 90 kundan keyin o'chadi
(`05` §3.2) va u bilan birga r11 ham yo'qoladi — uy katagi sababsiz
o'zgarib turardi.

Bir nechta faol obunasi bor akkaunt uchun **eng eskisi** olinadi
(tenglikda katak identifikatori bo'yicha kichigi — Т-3; bazadan
kelgan tartibga tayanish qorovulni bo'sh qilardi). Bu tanlov teshik
qoldiradi va u yopilgan deb hisoblanmaydi: uchta obuna ochgan akkaunt
o'z uy katagini tanlashi mumkin. Teshikning kengligi `HomeRegistry.
ambiguous` da qaytadi — jimgina yo'qolmaydi. 👤 savol §1.1(3) ni
**to'plamlar** kesishmasi deb o'qish kerakmi (`PROGRESS.md`).

## Nima uchun `address_key` berilmaydi

§1.1(2) ning ikkinchi yarmi — «три разных **указанных пользователем**
адреса». Obunaning `label` i aynan shunday matn, lekin u kalit sifatida
ishlatilmaydi: matn erkin va ikki odam bir xil yozishi mumkin
(«Uy», «Дом»). Bir xil kalit `count_witnesses()` da **birinchisini
qoldirib, ikkinchisini tashlaydi**, ya'ni begona odam bir so'z yozib
haqiqiy guvohni sanoqdan chiqarardi. To'sish soxtalashtirishdan arzon
bo'lmasligi kerak (§1.1 ning ustma-ustlik qarori bilan bir xil sabab),
shuning uchun `address_key` `None` qoladi va §1.1(2) r11 katagi
bo'yicha o'lchanadi — TZ ning o'zi taklif qilgan birinchi variant.

Manzil kaliti normallashtirilgan (uy raqamigacha yechilgan) manzil
reyestri paydo bo'lganda beriladi; erkin matn bilan emas.

## Т-4 va Т-1

Modulda soat yo'q (`now` argument bilan keladi) va §7 ning soni yo'q:
`ADDRESS_RESOLUTION` ham, poroglar ham `tzcount`/`TzParams` dan.

## Bu modul hali chaqirilmaydi

`clustering.service.evaluate()` statusni hamon `06` ning og'irlikli
hisobi bilan qaraydi. Ulash keyingi qadam va u bitta ochiq savolga
bog'liq: TZ **zonani** tasdiqlaydi (r10/r9/r8), `outages` esa
klaster — qaysi zonaning verdikti hodisani tasdiqlaydi degan javob
§2.1 da yo'q (`PROGRESS.md`, «Ochiq savollar»).
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.clustering.tzcount import (
    ADDRESS_RESOLUTION,
    Evidence,
    Level,
    ZoneVerdict,
    evaluate_levels,
)
from app.core.tzconfig import TzParams
from app.geo import h3_cells
from app.notifications import subscriptions as subscription_queries
from app.reports import queries as report_queries

# `SPEC` konstantasi bu yerda **ataylab yo'q** — `tzsource` bilan bir xil
# sabab: bu ulash qatlami, §1 ning vitrinasi reyestr modullarida qoladi.


@dataclass(frozen=True)
class HomeRegistry:
    """§1.1(3) ning kirishi: akkaunt → uy katagi (r11).

    `home_of` — javob; `ambiguous` **javob emas, diagnostika**: bir
    nechta har xil katakda obunasi bor akkauntlar. Ular uchun tanlov
    qilingan, lekin tanlov qat'iy emas va buni chaqiruvchi ko'rishi
    kerak.
    """

    #: Akkaunt identifikatori (matn) → r11 katagi. Т-3: tartiblangan.
    home_of: dict[str, str]
    #: Bir nechta **har xil** r11 katagida obunasi bor akkauntlar.
    ambiguous: tuple[str, ...]

    @property
    def declared(self) -> tuple[str, ...]:
        """Uy katagi ma'lum akkauntlar.

        Sanoqda qatnashgan akkauntlarning nechtasi §1.1(3) tomonidan
        umuman tekshirilishi mumkinligi — shu ro'yxatning kattaligi.
        """
        return tuple(sorted(self.home_of))


def resolve_homes(points: Iterable[subscription_queries.DeclaredPoint]) -> HomeRegistry:
    """Obuna nuqtalarini uy kataklariga aylantiradi.

    Toza funksiya: bazaga ham, soatga ham murojaat qilmaydi.
    """
    chosen: dict[str, tuple[datetime, str]] = {}
    seen: dict[str, set[str]] = {}

    for point in points:
        user = str(point.user_id)
        cell = h3_cells.cell_of(point.lat, point.lon, ADDRESS_RESOLUTION)
        seen.setdefault(user, set()).add(cell)
        current = chosen.get(user)
        if current is None:
            chosen[user] = (point.created_at, cell)
            continue
        at, taken = current
        # Eng eski obuna yutadi; teng vaqtda katak identifikatori
        # bo'yicha kichigi. Bazadan kelgan tartib bu yerda o'qilmaydi
        # (Т-3), garchi `declared_points_stmt` da `ORDER BY` bo'lsa ham.
        if point.created_at < at or (point.created_at == at and cell < taken):
            chosen[user] = (point.created_at, cell)

    return HomeRegistry(
        home_of={user: value[1] for user, value in sorted(chosen.items())},
        ambiguous=tuple(sorted(user for user, cells in seen.items() if len(cells) > 1)),
    )


def to_evidence(
    rows: Iterable[report_queries.TzEvidenceRow], homes: HomeRegistry
) -> tuple[Evidence, ...]:
    """So'rov natijasini `tzcount` ning kirishiga aylantiradi.

    `address_key` berilmaydi — modul izohidagi sabab.
    """
    return tuple(
        Evidence(
            user_id=str(row.user_id),
            at=row.created_at,
            h3_r8=row.h3_r8,
            h3_r9=row.h3_r9,
            h3_r10=row.h3_r10,
            h3_r11=row.h3_r11,
            home_r11=homes.home_of.get(str(row.user_id)),
        )
        for row in rows
    )


@dataclass(frozen=True)
class Counting:
    """Bitta hodisaning uchala darajadagi sanog'i.

    `verdicts` — `tzcount.evaluate_levels()` ning javobi; `homes` —
    §1.1(3) qay darajada tekshirilganini ko'rsatadi.
    """

    verdicts: dict[tuple[Level, str], ZoneVerdict]
    homes: HomeRegistry
    #: O'qilgan dalil qatorlari (oyna qo'llanishidan **oldin**).
    rows: int

    def verdict(self, level: Level, cell: str) -> ZoneVerdict | None:
        """Zonaning verdikti; zona umuman bo'lmasa `None`."""
        return self.verdicts.get((level, cell))

    def reporters(self, level: Level, cell: str) -> tuple[str, ...]:
        """Zonada sanalgan akkauntlar — §2.2 ning kirishi.

        `tzdispute.count_rebuttals(reporters=…)` aynan shu ro'yxatni
        so'raydi: uzilishni o'zi xabar qilgan odamning «menda svet
        bor» i qarshi dalil emas. Ro'yxatsiz chaqiruv jimgina
        noto'g'ri ishlaydi, shuning uchun u zona verdiktidan
        (`ZoneVerdict.users`, 188-run) shu yerga olib chiqiladi.

        Zona yo'q bo'lsa **bo'sh** ro'yxat qaytadi va bu to'g'ri:
        hech kim xabar qilmagan zonada chiqarib tashlanadigan odam
        ham yo'q.
        """
        found = self.verdicts.get((level, cell))
        return () if found is None else found.users

    @property
    def reached(self) -> tuple[tuple[Level, str], ...]:
        """Uchala shartni bajargan zonalar, tartiblangan.

        §2.3 ishlagan zona bu yerda **bor**: «порог достигнут» va
        «подтверждение выдаётся» har xil narsa (`ZoneVerdict.
        confirmable` ikkinchisi). Ikkalasini bitta ro'yxatga yig'ish
        kam odamli zonaning statusini jimgina ko'tarardi.
        """
        return tuple(sorted(key for key, item in self.verdicts.items() if item.reached))


async def load(
    session: AsyncSession,
    outage_id: uuid.UUID,
    *,
    kind: str,
    now: datetime,
    params: TzParams,
    min_trust_score: int,
    account_created_before: datetime,
    active_users: Mapping[tuple[Level, str], int],
) -> Counting:
    """Hodisaning dalillarini o'qiydi va uchala darajani baholaydi.

    `active_users` — §2.3 ning maxraji (zonadagi faol foydalanuvchilar).
    Uning **sukut qiymati yo'q** va bu ataylab: bo'sh xarita §2.3 ni
    o'chiradi (porog hech qachon pasaymaydi), ya'ni kam odamli zona
    hech qachon porogga yetmaydi. Sukut qiymati bo'lganda chaqiruvchi
    buni sezmasdan tanlab qo'yardi — 187-run `blocks_with_users` da
    aynan shu naqshni topgan. Bo'sh xarita berish mumkin, lekin u
    **yozilgan** qaror bo'ladi.

    Ikkita so'rov: dalillar va obuna nuqtalari. Uchinchisi (§2.3 ning
    maxraji) chaqiruvchida, chunki u zonalar ro'yxatiga bog'liq va uni
    shu yerda yig'ish har zona uchun alohida so'rov (N+1) berardi.
    """
    rows = await report_queries.tz_evidence(
        session,
        outage_id,
        kind=kind,
        min_trust_score=min_trust_score,
        account_created_before=account_created_before,
    )
    points = await subscription_queries.declared_points(
        session, [row.user_id for row in rows]
    )
    homes = resolve_homes(points)
    verdicts = evaluate_levels(
        to_evidence(rows, homes),
        now=now,
        params=params,
        active_users=dict(active_users),
    )
    return Counting(verdicts=verdicts, homes=homes, rows=len(rows))
