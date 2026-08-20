"""TZ §12 «Дополнительно» — §3 ning poroglari erishuvchanmi.

§12 ning asosiy yarmi 193-runda qurildi (`app/clustering/tzreach.py`):
u §2.1 ning **odam** poroglarini tarixda o'lchaydi. §12 ning oxirgi
jumlasi esa boshqa savol beradi va uni alohida ajratadi:

> «**Дополнительно:** сколько районов и кварталов в Самарканде и в
> скольких из них есть пользователи — от этого зависит §3.»

Bu modul aynan o'sha savolga javob beradi. Javob tarixga tayanmaydi —
u bugungi **reyestrlardan** hisoblanadi, ya'ni `tzreach` dan farqli
o'laroq Toshkent tarixi bo'lmasa ham bugun o'lchanadi.

## Nima uchun bu savol §3 uchun hayotiy

§3 ning ikkala qatorida ham ulushdan tashqari **eng kam son** bor
(«но не менее 3 кварталов», «но не менее 3 районов»). Ulush maxrajga
nisbatan o'sadi, eng kam son esa **mutlaq**. Ya'ni foydalanuvchisi bor
kvartallari uchtadan kam bo'lgan tuman §3 bo'yicha **hech qachon**
tasdiqlanmaydi — hamma kvartali tasdiqlansa ham. Bu aynan §3 ning o'zi
ogohlantirgan holat («иначе порог недостижим навсегда»), faqat u
ogohlantirishni maxraj tomonida yozgan va eng kam son tomonida
yozmagan.

## 🔴 Shaharning porogi tumanlarning **natijasidan** yig'iladi

Eng qimmat topilma shu va u ko'rinmas. `tzscale.city()` shaharning
maxrajiga foydalanuvchisi bor **har bir** tumanni qo'shadi, sanoqqa
esa faqat **tasdiqlangan** tumanni. Demak ikkita kvartali bor tuman:

* shaharning maxrajini **ko'taradi** (`has_users=True`),
* sanoqqa esa **hech qachon** kira olmaydi (`district_block_min`
  uni to'sadi).

Bunday tumanlar ko'p bo'lsa, shahar darajasi tumanlarning har biri
alohida erishuvchan ko'ringan holda ham erishilmas bo'lib qoladi.
Shuning uchun shaharning tepa chegarasi «foydalanuvchisi bor
tumanlar» emas, **o'zi erishuvchan** tumanlar soni; farqi
(`dead_weight`) — porogni ko'taradigan va uni hech qachon
to'ldirmaydigan tumanlar.

## 🔴 Ikkita maxraj bor va ular almashtirilmaydi

| Savol | Maxraj | Manbasi |
|---|---|---|
| §3 ning porogi | foydalanuvchisi bor zonalar | `reports` |
| §12 ning qamrovi | mavjud zonalar | `geo` reyestri |

Ularni almashtirish har ikki tomonga ham buzadi:

* qamrovni `blocks_with_users` dan hisoblash **har doim 100 %**
  beradi — maxraj sanoqning o'zidan olingan bo'lardi;
* §3 ning porogini `districts_total` dan hisoblash bo'sh tumanlarni
  maxrajga qo'shardi va §3 ning «считаем от 12» qoidasini bekor
  qilardi.

Shuning uchun geo reyestri bu yerda **faqat qamrovning** maxraji.
U §3 ning maxrajini hech qachon kichraytirmaydi: reyestrda yo'q,
lekin foydalanuvchisi bor tuman baribir §3 ning maxrajida qoladi va
`unknown_districts` da nomlanadi.

## 🔴 Ulush erishuvchanlikni hech qachon to'smaydi — eng kam son to'sadi

`share_need(n, share) <= n` har qanday `share <= 1` uchun, va
`tzconfig._check()` `Unit.SHARE` ni `(0, 1]` bilan qulflaydi. Ya'ni
«erishuvchanmi» degan savol tuzilmaviy ravishda `n >= minimum` ga
qisqaradi. Shunga qaramay `need` bu yerda **hisoblanadi**, taxmin
qilinmaydi: sozlama qorovuli bo'shatilsa (`share > 1`) javob jimgina
noto'g'ri bo'lib qolmasin.

Undan chiqadigan ikkinchi kuzatuv `minimum_decides` da: `0.40` va
uchta kvartal bilan ulush `n <= 5` bo'lgan **har qanday** tumanda
eng kam sondan past turadi (`n == 6..7` da ikkalasi teng, `n >= 8`
da ulush oshadi), ya'ni §3 ning ulushi kichik shaharda umuman
ishlamaydi va qarorni faqat mutlaq son qabul qiladi. §3 esa
«Абсолютное число в настройках не задавать, только долю и минимум»
deb yozgan — mutlaq son sozlamada emas, lekin u qaror qabul qiladi.

## Sanoq bu yerda qayta yozilmaydi

`need` `tzscale.share_need()` dan olinadi — §3 ni mahsulot qanday
hisoblasa, o'lchov ham shunday hisoblaydi. Formulani bu yerda
takrorlash oson edi va u §12 ni foydasiz qilardi: o'lchov mahsulot
qo'llaydigan qoidadan **boshqa** qoida haqida son berardi
(`tzreach` bilan bir xil sabab).

## Т-1 / Т-3 / Т-4

Modulda §7 ning soni yo'q — hammasi `TzParams` dan. Xulosa
(`looks_unreachable`) ham son bilan emas, ikkita **o'lchangan** sonni
solishtirish bilan. Soat umuman so'ralmaydi: mavjudlik vaqtga bog'liq
emas (`reports.queries.blocks_with_users` izohi).
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from app.clustering import tzsource
from app.clustering.tzscale import share_need
from app.core.tzconfig import TzParams
from app.geo import queries as geo_queries

# `SPEC` konstantasi ataylab **yo'q** — `tzreach` bilan bir xil sabab:
# `SPEC` li modul `app/admin/registries.py` indeksida qator bo'lishi
# shart, indeks esa hujjatning qatorlarini kod bilan solishtiradigan
# reyestrlarni ko'rsatadi. Bu modulda solishtiriladigan qator yo'q —
# u §3 ning bandlarini emas, **reyestrlarni** o'lchaydi, va javobi
# kodga emas, ma'lumotga bog'liq. §3 ning holati vitrinada allaqachon
# ko'rinadi (`tzscale.RULES`).


class Verdict(StrEnum):
    """O'lchovning holati."""

    #: O'lchash mumkin emas — sabab `Reason` da.
    UNKNOWN = "unknown"
    #: O'lchandi; sonlar `districts` va `city` da.
    MEASURED = "measured"


class Reason(StrEnum):
    """Nega o'lchanmadi. `MEASURED` da — `NONE`."""

    NONE = "none"
    #: Foydalanuvchisi bor kvartal umuman yo'q — §3 ning maxraji nol,
    #: ya'ni «erishuvchanmi» degan savol ma'nosiz. Bu **geo reyestri
    #: bo'shligidan boshqa** holat: chegaralar bo'lmasa ham
    #: foydalanuvchi bo'lishi mumkin.
    NO_BLOCKS_WITH_USERS = "no_blocks_with_users"


@dataclass(frozen=True)
class RegionFacts:
    """O'lchovning kirishi — ikkita reyestrning kesimi.

    Uchala xarita ham **matn kalitli**: `tzscale` tumanni matn bilan
    biladi (`ZoneFact.parent_id`), `tzsource` ham matn qaytaradi.
    `uuid` ga o'tish bog'liqlik yo'nalishini teskari qilardi.
    """

    #: `geo` reyestri: tuman → kodi. §12 ning «сколько районов» i va
    #: **faqat qamrovning** maxraji.
    districts: dict[str, str]
    #: `geo` geometriyasi: tuman → poligonni qoplaydigan r9 kataklar
    #: **taxminiy** soni. Taxminiy, chunki bazada `h3` kengaytmasi yo'q
    #: va son maydondan hisoblanadi (`geo.queries._geometry_facts`).
    #: Tumani yo'q qiymat — geometriya o'qilmagan.
    blocks_estimated: dict[str, int]
    #: `reports`: tuman → foydalanuvchisi bor kvartallar soni. §3 ning
    #: maxraji.
    blocks_with_users: dict[str, int]
    #: Tumani aniqlanmagan kvartallar (`05` §5.3). Ular hech qaysi
    #: tumanning porogiga qo'shilmaydi, ya'ni yo'qotilgan maxraj.
    blocks_unassigned: int
    #: Ikki tumanda uchragan va bittasiga biriktirilgan kvartallar.
    blocks_straddling: int


@dataclass(frozen=True)
class DistrictReach:
    """Bitta tumanning §3 bo'yicha tepa chegarasi."""

    district_id: str
    #: Reyestrdagi kodi; reyestrda yo'q tumanda bo'sh satr.
    code: str
    #: §3 ning maxraji — foydalanuvchisi bor kvartallar.
    blocks_with_users: int
    #: Reyestrdagi taxminiy umumiy kvartallar; noma'lum bo'lsa `None`.
    blocks_estimated: int | None
    #: §3 ning kerakli soni (`tzscale.share_need` + eng kam son).
    need: int
    #: Faqat ulushdan kelib chiqadigan qismi — `minimum_decides` uchun.
    #: `need` dan tiklab bo'lmaydi: `max()` ikkala argumentini ham
    #: yo'qotadi, ya'ni «qaysi biri qaror qabul qildi» degan savolga
    #: javob faqat shu maydonda qoladi.
    share_part: int
    #: Geo reyestrida bormi. `False` — foydalanuvchisi bor, lekin
    #: joriy chegara versiyasi yo'q tuman.
    known: bool

    @property
    def reachable(self) -> bool:
        """Porog **umuman** yig'ilishi mumkinmi.

        Tepa chegara — foydalanuvchisi bor kvartallarning hammasi
        tasdiqlangan holat: dalilsiz kvartal tasdiqlanmaydi
        (`tzscale.from_zone_verdicts` maxrajga faqat shularni
        qo'shadi).
        """
        return self.blocks_with_users >= self.need

    @property
    def minimum_decides(self) -> bool:
        """Qarorni ulush emas, mutlaq eng kam son qabul qiladimi.

        `True` — ulushdan kelib chiqadigan son eng kam sondan oshmaydi,
        ya'ni §3 ning `40 %` i bu tumanda hech narsa qo'shmaydi.
        """
        return self.need > 0 and self.need != self.share_part

    @property
    def coverage(self) -> float | None:
        """Qamrov: foydalanuvchisi bor kvartallarning ulushi.

        Maxraj **geo** dan (modul izohi, ikkinchi 🔴). Noma'lum yoki
        nol bo'lsa `None` — `0.0` qaytarish o'lchanmagan qamrovni
        «nol qamrov» deb ko'rsatardi.
        """
        if self.blocks_estimated is None or self.blocks_estimated <= 0:
            return None
        return self.blocks_with_users / self.blocks_estimated

    @property
    def over_capacity(self) -> bool:
        """Foydalanuvchisi bor kvartallar taxminiy umumiydan ko'pmi.

        Bu qamrov `100 %` dan katta degani emas, **taxmin noto'g'ri**
        degani: son maydondan hisoblanadi va poligon bilan xabarlar
        mos kelmasligi mumkin. Qiymat kesilmaydi — kesish nuqsonni
        yashirardi.
        """
        return self.blocks_estimated is not None and self.blocks_with_users > self.blocks_estimated


@dataclass(frozen=True)
class CityReach:
    """Shahar darajasining tepa chegarasi.

    Maxraj va sanoq **har xil to'plamdan** olinadi va bu §3 ning
    tuzilishi: `tzscale.city()` maxrajga foydalanuvchisi bor har bir
    tumanni qo'shadi, sanoqqa esa faqat tasdiqlanganini (modul izohi,
    birinchi 🔴).
    """

    #: `geo` reyestridagi joriy tumanlar — §12 ning «сколько районов» i.
    districts_total: int
    #: §3 ning maxraji — foydalanuvchisi bor tumanlar.
    districts_with_users: int
    #: Sanoqning tepa chegarasi — o'zi erishuvchan tumanlar.
    districts_reachable: int
    #: §3 ning kerakli soni.
    need: int
    #: Ulush bilan hisoblangan qismi — `minimum_decides` uchun.
    share_part: int

    @property
    def reachable(self) -> bool:
        """Shahar darajasi umuman yig'ilishi mumkinmi."""
        return self.districts_reachable >= self.need

    @property
    def minimum_decides(self) -> bool:
        """Qarorni mutlaq eng kam son qabul qiladimi."""
        return self.need > 0 and self.need != self.share_part

    @property
    def dead_weight(self) -> int:
        """Porogni ko'taradigan, lekin uni to'ldira olmaydigan tumanlar.

        Foydalanuvchisi bor, lekin o'zi hech qachon tasdiqlanmaydigan
        tumanlar. Bu son katta bo'lsa, shahar darajasi tumanlarning
        har biri alohida erishuvchan ko'ringan holda ham erishilmas.
        """
        return self.districts_with_users - self.districts_reachable

    @property
    def coverage(self) -> float | None:
        """Foydalanuvchisi bor tumanlarning ulushi. Maxraj — `geo`."""
        if self.districts_total <= 0:
            return None
        return self.districts_with_users / self.districts_total

    @property
    def over_capacity(self) -> bool:
        """Reyestrda yo'q tumanlarda foydalanuvchi bormi."""
        return self.districts_with_users > self.districts_total


@dataclass(frozen=True)
class Coverage:
    """§12 «Дополнительно» ning javobi."""

    verdict: Verdict
    reason: Reason
    #: Tuman kesimida — identifikatori bo'yicha tartiblangan (Т-3).
    #: `UNKNOWN` da ham to'ldiriladi: o'lchov bo'lmasa ham dalil
    #: ko'rinsin.
    districts: tuple[DistrictReach, ...]
    city: CityReach
    blocks_unassigned: int
    blocks_straddling: int

    def district(self, district_id: str) -> DistrictReach | None:
        """Bitta tumanning natijasi; yo'q bo'lsa `None`."""
        for item in self.districts:
            if item.district_id == district_id:
                return item
        return None

    @property
    def unreachable_districts(self) -> tuple[str, ...]:
        """Porogi hech qachon yig'ilmaydigan tumanlar, tartiblangan."""
        return tuple(item.district_id for item in self.districts if not item.reachable)

    @property
    def reachable_districts(self) -> tuple[str, ...]:
        """Porogi yig'ilishi mumkin bo'lgan tumanlar, tartiblangan."""
        return tuple(item.district_id for item in self.districts if item.reachable)

    @property
    def unknown_districts(self) -> tuple[str, ...]:
        """Foydalanuvchisi bor, lekin `geo` reyestrida yo'q tumanlar.

        Ular §3 ning maxrajidan **chiqarilmaydi** (modul izohi,
        ikkinchi 🔴), lekin nomlanadi: reyestrning nuqsoni qamrovni
        birdan katta qiladi va buni ko'rish kerak.
        """
        return tuple(item.district_id for item in self.districts if not item.known)

    @property
    def looks_unreachable(self) -> bool:
        """§12 ning xulosasi: tumanlarning ko'pchiligi erishilmasmi.

        Sonli chegara bilan emas, ikkita **o'lchangan** sonni
        solishtirish bilan (Т-1). Tenglikda `False`: teng bo'linish
        «ko'pchilik» emas.
        """
        return len(self.unreachable_districts) > len(self.reachable_districts)


def blocks_by_district(registry: tzsource.BlockRegistry) -> dict[str, int]:
    """`tzsource` ning kvartal→tuman xaritasidan tuman kesimi.

    Sanaladigan narsa — **kvartallar**, odamlar emas: §3 ning birinchi
    jumlasi («сто сообщений с одной улицы не доказывают, что район без
    света») aynan odamlarni sanashni taqiqlaydi, va `BlockUsersRow.users`
    ni qo'shish §12 ning javobini o'sha taqiqlangan tomonga burardi.

    `BlockRegistry` chegaradagi katakni allaqachon bitta tumanga
    biriktirgan, ya'ni bu yerda ikki marta sanash mumkin emas.
    """
    counts: dict[str, int] = {}
    for district in registry.district_of.values():
        counts[district] = counts.get(district, 0) + 1
    return dict(sorted(counts.items()))


def measure(facts: RegionFacts, *, params: TzParams) -> Coverage:
    """§12 «Дополнительно» ning javobi.

    Toza funksiya: bazaga ham, soatga ham murojaat qilmaydi.
    """
    districts: list[DistrictReach] = []
    # Maxraj — §3 niki: foydalanuvchisi bor tumanlar. Geo reyestrining
    # bo'sh tumanlari bu ro'yxatga **kirmaydi** (modul izohi, 2-🔴).
    for district_id in sorted(facts.blocks_with_users):
        blocks = facts.blocks_with_users[district_id]
        share_part = share_need(blocks, share=params.district_block_share)
        item = DistrictReach(
            district_id=district_id,
            code=facts.districts.get(district_id, ""),
            blocks_with_users=blocks,
            blocks_estimated=facts.blocks_estimated.get(district_id),
            need=max(share_part, params.district_block_min),
            share_part=share_part,
            known=district_id in facts.districts,
        )
        districts.append(item)

    with_users = len(districts)
    reachable = sum(1 for item in districts if item.reachable)
    city_share_part = share_need(with_users, share=params.city_district_share)
    city = CityReach(
        districts_total=len(facts.districts),
        districts_with_users=with_users,
        districts_reachable=reachable,
        need=max(city_share_part, params.city_district_min),
        share_part=city_share_part,
    )

    return Coverage(
        verdict=Verdict.MEASURED if with_users else Verdict.UNKNOWN,
        reason=Reason.NONE if with_users else Reason.NO_BLOCKS_WITH_USERS,
        districts=tuple(districts),
        city=city,
        blocks_unassigned=facts.blocks_unassigned,
        blocks_straddling=facts.blocks_straddling,
    )


def to_facts(
    registry: tzsource.BlockRegistry,
    *,
    districts: Iterable[geo_queries.DistrictRow],
    geometry: Iterable[geo_queries.TerritoryGeometryFacts],
) -> RegionFacts:
    """Ikkita reyestrni `measure()` ning kirishiga aylantiradi.

    Toza: bazani ko'rmaydi, shuning uchun ikki reyestrning mos
    kelmasligi testda fikstyurasiz o'lchanadi.
    """
    return RegionFacts(
        districts={str(row.id): row.code for row in districts},
        blocks_estimated={str(row.territory_id): row.covering_cells for row in geometry},
        blocks_with_users=blocks_by_district(registry),
        blocks_unassigned=len(registry.unassigned),
        blocks_straddling=len(registry.straddling),
    )


async def load(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    params: TzParams,
) -> Coverage:
    """Uchta so'rov: chegaralar reyestri, geometriya va kvartallar.

    `tzsource.load()` qayta ishlatiladi — §3 ning maxraji o'lchovda
    ham, mahsulotda ham **bir xil** so'rovdan kelishi shart, aks holda
    §12 boshqa maxraj haqida son berardi (`tzreach` ning birinchi
    sababi).
    """
    registry = await tzsource.load(session, region_id=region_id)
    rows = await geo_queries.current_districts(session, region_id)
    geometry = await geo_queries.district_geometry_facts(session, region_id)
    return measure(to_facts(registry, districts=rows, geometry=geometry), params=params)


def summary(coverage: Coverage) -> Mapping[str, object]:
    """Hisobot uchun tekis kesim (`tools/` skripti va tekshiruv).

    Odam o'qiydigan matn bu yerda yasalmaydi: modul i18n katalogini
    ko'rmaydi va §12 foydalanuvchiga chiqmaydi — u ishlab chiqishdan
    **oldingi** tekshiruv.
    """
    return {
        "verdict": coverage.verdict.value,
        "reason": coverage.reason.value,
        "districts_total": coverage.city.districts_total,
        "districts_with_users": coverage.city.districts_with_users,
        "districts_reachable": coverage.city.districts_reachable,
        "city_need": coverage.city.need,
        "city_reachable": coverage.city.reachable,
        "dead_weight": coverage.city.dead_weight,
        "blocks_with_users": sum(item.blocks_with_users for item in coverage.districts),
        "blocks_unassigned": coverage.blocks_unassigned,
        "blocks_straddling": coverage.blocks_straddling,
        "unreachable_districts": coverage.unreachable_districts,
        "unknown_districts": coverage.unknown_districts,
        "looks_unreachable": coverage.looks_unreachable,
    }
