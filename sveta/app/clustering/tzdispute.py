"""TZ §2.2 — qarshi dalillar («у меня свет есть») va tasdiqni qaytarib olish.

`TZ_Podtverzhdenie_i_uvedomleniya.md` §11 navbatining **uchinchi** bandi:
«Свидетельства против, статус "Спорно" — без них подтверждение нечем
опровергнуть». Bu modul uning sanash yarmi; statusning o'zi — Т-5 ga
ko'ra `app/clustering/tzstatus.py` ning `decide()` sida, boshqa hech
qayerda.

## Nima uchun alohida modul, lekin sanash bir xil

§2.2 ning birinchi qatori: «Одновременно с подсчётом "нет света"
ведётся подсчёт "у меня свет есть" **в той же клетке**». Ya'ni qarshi
dalil ham §1.1 ning o'sha yaqinlashuvi bilan sanaladi — turli akkaunt,
turli manzil, ustma-ust tushmagan uy katagi. Shuning uchun bu yerda
o'z sanash sikli yozilmaydi: `tzcount.count_witnesses()` chaqiriladi.
Aks holda ТС-202 va ТС-203 ning simmetrik ko'rinishlari (bitta odam
uchta nuqtadan «menda svet bor» deydi) jimgina ishlab ketardi va
tasdiqlashni **to'sish** uni soxtalashtirishdan arzon bo'lardi.

Modul alohida, chunki §2.2 ning natijasi boshqa: bu porog emas,
**veto**. Ikkalasini bitta funksiyaga qo'shish `Evidence` ga `kind`
maydonini talab qilardi va o'sha maydon bo'yicha filtr bitta joyda
unutilishi bilan qarshi dalil tasdiqlovchiga aylanardi.

## 🔴 Uzilishni xabar qilgan odamning «menda svet bor» i qarshi dalil emas

TZ da bu ochiq yozilmagan, lekin ikkita bo'lim to'qnashadi: §2.2
(«qarshi dalil») va §4 ning В-4 tugmasi («Свет вернулся» — o'sha
odamning o'zidan). Shu zonada uzilishni **xabar qilgan** akkauntning
keyingi «menda svet bor» i — bu §4 ning **tiklanish** guvohligi, §2.2
ning qarshi dalili emas.

Sabab: aks holda haqiqiy uzilish tiklanganda avvalgi xabar
qilganlarning ikkitasi tugmani bosishi bilan hodisa «Спорно» ga
tushar va odamlarga «tasdiqlash qaytarib olindi» ketardi — «свет
вернулся» o'rniga. Xato «sizda avariya» qanchalik zararli bo'lsa,
haqiqiy avariyani «bahsli» deb e'lon qilish ham shunchalik zararli:
ikkalasi ham servisning o'z ma'lumotiga ishonchini yo'q qiladi.

Bu odamlar tashlanmaydi, **sanaladi** — `Rebuttals.from_reporters`
da: tiklanish quvuri (§11/4) aynan o'sha ro'yxatni oladi.

## 🔴 §2.3 qarshi dalil porogini pasaytirmaydi

§2.3 «порог = все активные пользователи зоны, но не менее 2» deydi va
u **tasdiqlash** porogi haqida. Qarshi dalil porogi (§7 —
«Порог свидетельств против» = 2) o'zgarmaydi: kam odamli zonada uni
pasaytirish bitta odamga butun kvartalni to'sish huquqini berardi, va
aynan kam odamli zonada bunday akkauntni ochish eng arzon.

## Т-4 va Т-1

Soat argumentda (`now`), §7 ning birorta soni bu faylda literal emas —
hammasi `TzParams` dan. Ikkalasi ham `tests/test_tz_dispute.py` da
`ast` bilan qulflangan.

Modul **toza**: bazaga, `settings` ga va vaqtga bog'liq emas.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from app.clustering.tzcount import (
    Drop,
    Evidence,
    Level,
    count_witnesses,
    window_min,
)
from app.core.tzconfig import TzParams

#: Hujjat bo'limi. Reyestrlar vitrinasi shuni o'qiydi.
SPEC = "TZ §2.2"


@dataclass(frozen=True)
class Obligation:
    """§2.2 ning bitta majburiyati va u qurilganmi.

    Ro'yxat kodda turadi, chunki uni `app.admin.registries` o'qiydi:
    §2.2 ning oxirgi qatori («всем, кому было отправлено уведомление,
    отправляется исправление») bugun **oxirigacha bajarilmagan**, va
    buni sessiya jurnalida emas, operator ko'radigan joyda aytish
    kerak.
    """

    code: str
    note: str
    built: bool


OBLIGATIONS: tuple[Obligation, ...] = (
    Obligation(
        code="veto",
        note="2+ qarshi guvoh tasdiqlashni beruvchi porogni bekor qiladi",
        built=True,
    ),
    Obligation(
        code="retract",
        note="Tasdiqlangan hodisada tasdiq qaytarib olinadi, status «Спорно»",
        built=True,
    ),
    Obligation(
        code="to_operator",
        note="Bahsli hodisa operatorga o'tadi (§8 ning qarori)",
        built=True,
    ),
    Obligation(
        code="correction_sent",
        note="§6.4 — tuzatish o'sha odamlarga, o'sha kanal bilan yuboriladi",
        # §11 navbatining 6-bandi: yuborish quvuri va Т-9 ning
        # oluvchilar ro'yxati o'sha yerda quriladi. Bugun `Card`
        # faqat **majburiyatni** e'lon qiladi (`corrects`).
        built=False,
    ),
)


@dataclass(frozen=True)
class Rebuttals:
    """§2.2 bo'yicha sanalgan qarshi dalillar.

    `Witnesses` dan alohida tur: nomlari bir xil bo'lsa, chaqiruvchi
    ikkalasini almashtirib yuborishi mumkin edi va tekshirgich buni
    ko'rmasdi.
    """

    #: §1.1 dan o'tgan qarshi guvohlar soni.
    people: int
    #: §2.2 ning porogi (`tz.confirm.against_users`).
    need: int
    #: Porog bajarildimi — ya'ni tasdiqlash **berilmaydi**.
    vetoed: bool
    #: Uzilishni o'zi xabar qilgan akkauntlar: ular §2.2 ga emas,
    #: §4 ning tiklanish hisobiga tushadi. Vaqt tartibida.
    from_reporters: tuple[str, ...]
    #: Sanoqqa kirgan akkauntlar, vaqt tartibida (Т-3 uchun determinizm).
    users: tuple[str, ...]
    #: Nega tashlangani — diagnostika. Т-8: foydalanuvchiga ko'rsatilmaydi.
    drops: dict[Drop, int] = field(default_factory=dict)

    @property
    def remaining(self) -> int:
        """Veto uchun yana nechta kerak. Kartada **ko'rsatilmaydi**.

        §5 hisoblagichni faqat tasdiqlash uchun ochadi. Qarshi
        dalilning hisoblagichini ko'rsatish to'suvchiga «yana bitta
        akkaunt kerak» deb aytish bo'lardi, va tasdiqlash
        hisoblagichidan farqli o'laroq bu razmenni TZ qilmagan.
        """
        return max(self.need - self.people, 0)


def against_threshold(params: TzParams) -> int:
    """§7 — «Порог свидетельств против». Daraja bo'yicha o'zgarmaydi.

    §2.1 poroglari darajaga qarab uchxil, §2.2 niki esa bitta: veto
    zonaning kattaligiga bog'liq emas, u dalilning o'ziga bog'liq.
    """
    return params.against_users


def count_rebuttals(
    level: Level,
    rebuttals: Iterable[Evidence],
    *,
    now: datetime,
    params: TzParams,
    reporters: Iterable[str],
) -> Rebuttals:
    """§2.2: «у меня свет есть» dalillarini shu katakda sanaydi.

    `reporters` — shu zonada uzilishni xabar qilgan akkauntlar
    (`Witnesses.users`). Ular sanoqdan chiqariladi va `from_reporters`
    ga yoziladi: modul docstringidagi birinchi 🔴 qaror.

    🔴 **Argumentning sukut qiymati yo'q** (188-run). U bo'sh
    `()` edi, ya'ni uni **yozmagan** chaqiruvchi 🔴 qarorni jimgina
    o'chirib qo'yardi: uzilishni o'zi xabar qilgan ikki kishi «свет
    вернулся» ni bosishi bilan `vetoed` rost bo'lib, haqiqiy uzilish
    «Спорно» ga tushar va §6.4 ning tuzatishi hammaga ketardi.
    Xuddi o'sha ikkita dalildan `reporters` bilan `vetoed=False`,
    `reporters` siz `vetoed=True` chiqadi — bir xil dalildan teskari
    verdikt, xatosiz va jurnalsiz. Modul javobni o'zi topa olmaydi
    (kim xabar qilgani — `tzcount` ning natijasi), shuning uchun
    chaqiruvchi javob berishga majbur: `tzscale.from_zone_verdicts`
    ning `blocks_with_users` i va `Outage.notifies` bilan bir xil
    sabab. Bo'sh ro'yxat halol javob, `()` ni ochiq yozish kerak.

    Oyna — o'sha darajaning §2.1 oynasi: «одновременно с подсчётом»
    ikkala hisob ham bir xil vaqt kesimida ketishini bildiradi.
    """
    known = frozenset(reporters)
    items = list(rebuttals)
    mine = tuple(
        item.user_id
        for item in sorted(items, key=lambda e: (e.at, e.user_id))
        if item.user_id in known
    )
    counted = count_witnesses(
        (item for item in items if item.user_id not in known),
        now=now,
        window_min=window_min(level, params),
    )
    need = against_threshold(params)
    return Rebuttals(
        people=counted.people,
        need=need,
        vetoed=counted.people >= need,
        from_reporters=mine,
        users=counted.users,
        drops=counted.drops,
    )
