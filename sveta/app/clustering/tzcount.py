"""TZ §1.1, §2.1, §2.3 — odam sanash va poroglar.

`TZ_Podtverzhdenie_i_uvedomleniya.md` §11 navbatining **ikkinchi** bandi:
«Подсчёт, пороги, статусы, карточка со счётчиком — основа». Bu modul
uning sanash yarmi; statuslar va karta — `app/clustering/tzstatus.py`.

## Nima uchun `06` ning formulasi emas

TZ ning kirish qismi og'irlikli modelni ochiq rad etadi: «Ни один из
этих коэффициентов не был измерен — все подобраны вручную». 👤 qarori
(2026-08-19) bo'yicha ziddiyatda TZ haq, ya'ni `app/clustering/
confirmation.py` ning `W ≥ N_req` i bu yerda **ishlatilmaydi**. Sanash
modeli ko'rsatiladigan bo'lgani uchun tanlangan: «подтвердили 3 из 3»
ni odamga aytish mumkin, «uverennost 0.73» ni — yo'q.

## §1.1 ning halol chegarasi

TZ ning o'zi tan oladi: «Правило "3 человека с разных адресов" точно
выполнить **невозможно**» — GPS ning shahardagi xatosi 20–50 m, r11
katagi esa ~50 m. Shuning uchun bu yerda amalga oshiriladigan narsa
qoida emas, **yaqinlashuv** va u uchta shartning birgalikda
bajarilishi:

1. uchta turli akkaunt;
2. uchta turli r11 katagi **yoki** uchta turli ko'rsatilgan manzil;
3. akkauntlarning uy katagi r11 darajasida ustma-ust tushmaydi.

Uchinchi shart bir kvartiradagi uchta akkauntni kesadi, lekin bitta
podezddagi uchta jirovchini **kesmaydi** — bu yopilmagan teshik va
uni yopilgan deb hisoblash mumkin emas (TZ §1.1 ning oxirgi qatori).

**Ustma-ustlik qanday hal qilinadi.** Ikki akkauntning uy katagi bir
xil bo'lsa, ikkalasi ham **tashlanmaydi** — bittasi qoldiriladi. Aks
holda hujumchi haqiqiy fuqaroning uy katagi bilan bitta akkaunt
ochib, uni sanoqdan **chiqarib** yuborishi mumkin edi: tasdiqlashni
to'sish tasdiqlashni soxtalashtirishdan arzon bo'lardi. Qaysi biri
qoladi — vaqt bo'yicha birinchisi; teng vaqtda `user_id` bo'yicha,
ya'ni natija T-3 talab qilganidek takrorlanadi.

## Т-4: soat argumentda

Modulda `datetime.now()` yo'q va bo'lmaydi — `now` har funksiyaga
argument bilan keladi (Т-4). Shu sabab tarixni boshqa sozlamalar
bilan qayta hisoblash (Т-3) shu modulni chaqirishning o'zidan iborat.

## Т-1: bu faylda §7 ning soni yo'q

Barcha poroglar, oynalar va ulushlar `TzParams` dan keladi.
Funksiyalar ichida `0` va `1` dan boshqa son literali yo'q va buni
`tests/test_tz_counting.py` `ast` bilan tekshiradi (ТС-220).

Modul **toza**: bazaga, `settings` ga va vaqtga bog'liq emas.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from app.core.tzconfig import TzParams


class Level(StrEnum):
    """TZ §1 ning tasdiqlash darajalari.

    §1 jadvalida to'rtta qator bor, lekin tuman (r7) — **masshtab**
    o'lchovi (§3), tasdiqlash darajasi emas. Shuning uchun bu yerda
    uchta: uy, kvartal, mahalla.
    """

    #: r10, ~132 m — tasdiqlashning bazaviy birligi.
    HOUSE = "house"
    #: r9, ~349 m — tiklanish birligi (§4, V-1) va ikkinchi daraja.
    BLOCK = "block"
    #: r8, ~923 m — guruhlash.
    MAHALLA = "mahalla"


#: TZ §1 jadvali: daraja → H3 rezolyutsiyasi. Bu **zona geometriyasi**,
#: §7 sozlamasi emas: to'r doimiy va sozlanmaydi (§1 — «Круги вокруг
#: сообщений не используются»).
LEVEL_RESOLUTION: dict[Level, int] = {
    Level.HOUSE: 10,
    Level.BLOCK: 9,
    Level.MAHALLA: 8,
}

#: §1.1(2) — «turli manzil» ning yaqinlashuvi. Zona emas: r11 hech
#: qachon tasdiqlash darajasi bo'lmaydi, u faqat ajratish uchun.
ADDRESS_RESOLUTION = 11


class Shortfall(StrEnum):
    """Nima yetishmayapti. Karta shu sababni ko'rsatadi (§5)."""

    #: Hech narsa — daraja tasdiqlangan.
    NONE = "none"
    #: Odam yetmaydi (§2.1 ning birinchi ustuni).
    PEOPLE = "people"
    #: Odam yetarli, lekin r10 kataklari yoyilmagan (§2.1, kvartal).
    SPREAD = "spread"
    #: Odam yetarli, lekin kvartallar yetarli tasdiqlanmagan (§2.1, mahalla).
    BLOCKS = "blocks"


class Drop(StrEnum):
    """Xabar nega sanoqqa kirmadi. Faqat kuzatuv uchun — foydalanuvchiga
    ko'rsatilmaydi (Т-8: himoya ishlaganini bildirmaymiz)."""

    #: Oynadan tashqarida (§2.1 — sirpanuvchi oyna).
    OUT_OF_WINDOW = "out_of_window"
    #: Shu akkauntning shu zonadagi ikkinchi xabari (§1.1(1)).
    SAME_USER = "same_user"
    #: Uy katagi allaqachon sanalgan akkauntniki (§1.1(3)).
    SAME_HOME = "same_home"
    #: Manzili allaqachon sanalgan (§1.1(2)).
    SAME_ADDRESS = "same_address"
    #: Na r11 katagi, na ko'rsatilgan manzil — §1.1(2) ni tekshirib
    #: bo'lmaydi. `geom_exact` 90 kundan keyin o'chadi (`05` §3.2),
    #: ya'ni eski qatorlar shu yerga tushadi.
    NO_ADDRESS = "no_address"


@dataclass(frozen=True)
class Evidence:
    """Sanash uchun bitta xabarning kerakli minimumi.

    `kind` yo'q: «menda svet bor» dalillari (§2.2) **alohida** ro'yxat
    bo'lib keladi va alohida sanaladi — bir funksiyada ikkita ma'noni
    aralashtirish §2.2 ning «подтверждение отзывается» tarmog'ini
    ko'rinmas qilardi.
    """

    user_id: str
    at: datetime
    #: TZ §1 ning to'rt darajasi. `None` — qator eski, aniq nuqtasi
    #: o'chirilgan (`0012` migratsiyasi izohi).
    h3_r8: str | None = None
    h3_r9: str | None = None
    h3_r10: str | None = None
    h3_r11: str | None = None
    #: §1.1(2) ning ikkinchi yarmi — foydalanuvchi **o'zi ko'rsatgan**
    #: manzil. Bor bo'lsa r11 katagidan ustun turadi.
    address_key: str | None = None
    #: §1.1(3) — akkauntning uy katagi (r11). Noma'lum bo'lsa `None`
    #: va bunday akkaunt hech kim bilan ustma-ust tushmaydi.
    home_r11: str | None = None


@dataclass(frozen=True)
class Witnesses:
    """§1.1 bo'yicha sanalgan guvohlar."""

    #: Sanoqqa kirgan odamlar soni — karta shuni ko'rsatadi.
    people: int
    #: Oynaga tushgan **barcha** xabarlar. §5 ning «число подтвердивших
    #: и точек» iborasidagi ikkinchi son: xaritada ko'rinadigan nuqtalar
    #: sanoqdan ko'p bo'lishi mumkin (bir odamning ikkinchi xabari ham
    #: nuqta qoldiradi, lekin guvoh qo'shmaydi).
    in_window: int
    #: Sanoqqa kirganlarning turli r10 kataklari (§2.1, kvartal sharti).
    cells_r10: int
    #: Sanoqqa kirgan akkauntlar, vaqt tartibida. Т-3 uchun determinizm.
    users: tuple[str, ...]
    #: Nega tashlangani — sabab kesimida. Diagnostika, foydalanuvchiga emas.
    drops: dict[Drop, int]


def _address_key(item: Evidence) -> str | None:
    """§1.1(2): ko'rsatilgan manzil, bo'lmasa r11 katagi."""
    if item.address_key is not None:
        return item.address_key
    return item.h3_r11


def _sorted(evidence: Iterable[Evidence]) -> list[Evidence]:
    """Determinizm (Т-3): vaqt, keyin `user_id`, keyin manzil."""
    return sorted(evidence, key=lambda e: (e.at, e.user_id, _address_key(e) or ""))


def count_witnesses(
    evidence: Iterable[Evidence],
    *,
    now: datetime,
    window_min: int,
) -> Witnesses:
    """§1.1 + §2.1 ning oynasi: nechta guvoh sanaladi.

    Oyna **sirpanuvchi** va yopiq: `now - window <= at <= now`. Kelajak
    vaqtli xabar ham tashlanadi — soat argumentda bo'lgani uchun (Т-4)
    bunday qator qayta hisoblashda uchraydi.
    """
    lower = now - timedelta(minutes=window_min)
    drops: dict[Drop, int] = {}

    def drop(reason: Drop) -> None:
        drops[reason] = drops.get(reason, 0) + 1

    seen_users: set[str] = set()
    seen_homes: set[str] = set()
    seen_addresses: set[str] = set()
    kept: list[Evidence] = []
    in_window = 0

    for item in _sorted(evidence):
        if item.at < lower or item.at > now:
            drop(Drop.OUT_OF_WINDOW)
            continue
        in_window += 1
        if item.user_id in seen_users:
            drop(Drop.SAME_USER)
            continue
        address = _address_key(item)
        if address is None:
            drop(Drop.NO_ADDRESS)
            continue
        if item.home_r11 is not None and item.home_r11 in seen_homes:
            drop(Drop.SAME_HOME)
            continue
        if address in seen_addresses:
            drop(Drop.SAME_ADDRESS)
            continue
        seen_users.add(item.user_id)
        if item.home_r11 is not None:
            seen_homes.add(item.home_r11)
        seen_addresses.add(address)
        kept.append(item)

    cells = {item.h3_r10 for item in kept if item.h3_r10 is not None}
    return Witnesses(
        people=len(kept),
        in_window=in_window,
        cells_r10=len(cells),
        users=tuple(item.user_id for item in kept),
        drops=drops,
    )


def window_min(level: Level, params: TzParams) -> int:
    """§2.1 ning oxirgi ustuni — darajaning sirpanuvchi oynasi."""
    return {
        Level.HOUSE: params.house_window_min,
        Level.BLOCK: params.block_window_min,
        Level.MAHALLA: params.mahalla_window_min,
    }[level]


def base_threshold(level: Level, params: TzParams) -> int:
    """§2.1 ning «Нужно человек» ustuni — kam odamlilikni hisobga olmasdan."""
    return {
        Level.HOUSE: params.house_users,
        Level.BLOCK: params.block_users,
        Level.MAHALLA: params.mahalla_users,
    }[level]


@dataclass(frozen=True)
class Threshold:
    """Zonaga qo'llanadigan haqiqiy porog (§2.1 + §2.3)."""

    need: int
    #: §2.3 ishladimi. Ishlagan bo'lsa status «Вероятно» dan
    #: yuqoriga ko'tarilmaydi va bildirishnoma yuborilmaydi.
    sparse: bool


def threshold(level: Level, params: TzParams, *, active_users: int | None = None) -> Threshold:
    """§2.3 — kam odamli zona.

    «Порог = все активные пользователи зоны, но не менее 2.» Ya'ni
    zonada bazaviy porogdan kam odam bo'lsa, porog o'sha odamlar
    soniga tushadi, lekin pastki chekdan pastga emas. Bu qoidasiz
    xususiy sektor va kichik mahallalar **hech qachon** hech narsani
    tasdiqlamaydi.

    `active_users=None` — zonadagi faollar soni noma'lum. U holda
    §2.3 qo'llanmaydi: noma'lumlikni «kam odam» deb o'qish porogni
    jimgina pasaytirardi.
    """
    base = base_threshold(level, params)
    if active_users is None or active_users >= base:
        return Threshold(need=base, sparse=False)
    return Threshold(need=max(active_users, params.sparse_floor_users), sparse=True)


@dataclass(frozen=True)
class ZoneVerdict:
    """Bitta zonaning bitta darajadagi holati."""

    level: Level
    #: Sanalgan guvohlar (karta shu sonni ko'rsatadi).
    have: int
    #: Kerakli son — §2.3 dan keyin.
    need: int
    #: Oynadagi barcha xabarlar — §5 ning «точек» soni.
    points: int
    #: Turli r10 kataklari (kvartal sharti uchun).
    cells_r10: int
    #: Ushbu mahalladagi tasdiqlangan kvartallar (mahalla sharti uchun).
    confirmed_blocks: int
    #: Sanoqqa kirgan akkauntlar, vaqt tartibida (`Witnesses.users`).
    #: Kartada **ko'rsatilmaydi** — bu §2.2 ning kirishi: qarshi
    #: dalilni sanaydigan `tzdispute.count_rebuttals()` uzilishni
    #: xabar qilganlarni chiqarib tashlashi kerak, va 188-rungacha
    #: chaqiruvchi shu ro'yxatni zona verdiktidan **ololmasdi** —
    #: u faqat `count_witnesses()` ning javobida bor edi. Ya'ni
    #: normal yo'ldan (`evaluate_levels`) kelgan chaqiruvchi uchun
    #: `reporters` ni to'g'ri berish imkonsiz edi va §2.2 ning
    #: 🔴 qarori jimgina o'chib qolardi.
    users: tuple[str, ...]
    #: Uchala shart ham bajarildimi.
    reached: bool
    #: §2.3 ishladimi.
    sparse: bool
    shortfall: Shortfall
    drops: dict[Drop, int]

    @property
    def remaining(self) -> int:
        """Karta uchun: «yana nechta kutilmoqda» (§5)."""
        return max(self.need - self.have, 0)

    @property
    def confirmable(self) -> bool:
        """Zona umuman «Подтверждено» ga chiqa oladimi.

        §2.3: kam odamli zonada status «Вероятно» dan yuqoriga
        ko'tarilmaydi — porog bajarilgan bo'lsa ham.
        """
        return self.reached and not self.sparse


def evaluate_zone(
    level: Level,
    evidence: Iterable[Evidence],
    *,
    now: datetime,
    params: TzParams,
    active_users: int | None = None,
    confirmed_blocks: int = 0,
) -> ZoneVerdict:
    """§2.1 ning bitta qatorini bitta zonaga qo'llash.

    `confirmed_blocks` — faqat mahalla darajasida ma'noga ega: §2.1
    «и подтверждены минимум 3 квартала». Uni chaqiruvchi hisoblaydi,
    chunki u kvartal darajasidagi **boshqa** zonalarning natijasi
    (`evaluate_levels` shuni qiladi).

    Darajalar §2.1 ning oxirgi qatoriga ko'ra **mustaqil**: uy
    tasdiqlanishi uchun kvartal tasdiqlanishi shart emas.
    """
    limit = threshold(level, params, active_users=active_users)
    counted = count_witnesses(evidence, now=now, window_min=window_min(level, params))

    enough_people = counted.people >= limit.need
    enough_spread = level is not Level.BLOCK or counted.cells_r10 >= params.block_min_cells
    enough_blocks = level is not Level.MAHALLA or confirmed_blocks >= params.mahalla_min_blocks

    if not enough_people:
        shortfall = Shortfall.PEOPLE
    elif not enough_spread:
        shortfall = Shortfall.SPREAD
    elif not enough_blocks:
        shortfall = Shortfall.BLOCKS
    else:
        shortfall = Shortfall.NONE

    return ZoneVerdict(
        level=level,
        have=counted.people,
        need=limit.need,
        points=counted.in_window,
        cells_r10=counted.cells_r10,
        confirmed_blocks=confirmed_blocks,
        users=counted.users,
        reached=shortfall is Shortfall.NONE,
        sparse=limit.sparse,
        shortfall=shortfall,
        drops=counted.drops,
    )


def cell_of(item: Evidence, level: Level) -> str | None:
    """Xabarning shu darajadagi katagi."""
    return {
        Level.HOUSE: item.h3_r10,
        Level.BLOCK: item.h3_r9,
        Level.MAHALLA: item.h3_r8,
    }[level]


def evaluate_levels(
    evidence: Iterable[Evidence],
    *,
    now: datetime,
    params: TzParams,
    active_users: dict[tuple[Level, str], int] | None = None,
) -> dict[tuple[Level, str], ZoneVerdict]:
    """Uchala darajani bir vaqtda baholaydi (§2.1: «независимо и одновременно»).

    Kalit — `(daraja, katak)`. Mahalla darajasi kvartallarning
    natijasidan foydalanadi, shuning uchun tartib qat'iy: uy →
    kvartal → mahalla.
    """
    items = list(evidence)
    active = active_users or {}
    result: dict[tuple[Level, str], ZoneVerdict] = {}

    for level in (Level.HOUSE, Level.BLOCK, Level.MAHALLA):
        cells: dict[str, list[Evidence]] = {}
        for item in items:
            cell = cell_of(item, level)
            if cell is not None:
                cells.setdefault(cell, []).append(item)
        for cell, group in sorted(cells.items()):
            blocks = 0
            if level is Level.MAHALLA:
                blocks = _confirmed_blocks_in(result, group)
            result[(level, cell)] = evaluate_zone(
                level,
                group,
                now=now,
                params=params,
                active_users=active.get((level, cell)),
                confirmed_blocks=blocks,
            )
    return result


def _confirmed_blocks_in(
    result: dict[tuple[Level, str], ZoneVerdict],
    group: list[Evidence],
) -> int:
    """Shu mahalladagi tasdiqlangan kvartallar soni.

    «Tasdiqlangan» — `confirmable`, ya'ni §2.3 ishlagan kvartal
    sanalmaydi: kam odamli kvartal mahallani ko'tarib yuborishi
    mumkin emas.
    """
    blocks = {item.h3_r9 for item in group if item.h3_r9 is not None}
    return sum(
        1
        for block in blocks
        if (Level.BLOCK, block) in result and result[(Level.BLOCK, block)].confirmable
    )
