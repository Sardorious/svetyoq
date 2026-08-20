"""TZ §6.3 ning qolgan uch turi va §6.4 — §11 navbatining 6-bandi.

## Nima uchun bitta modulda

§11 jadvalining 6-qatori: «Остальные уведомления + **исправления**.
Исправления делать в одном заходе с уведомлениями, не позже.» Ya'ni
hujjatning o'zi tuzatishni alohida bandga chiqarishni **taqiqlaydi**:
uzilish bildirishnomasi tuzatishsiz yuborilsa, sервис mish-mishning
o'rniga emas, uning yana bitta manbaiga aylanadi (§6.4).

Shuning uchun bu yerda uchtasi birga: uzilish, rejali ishlar va
tuzatish. Ular bir xil quvurdan o'tadi va bir xil qabul qiluvchilar
jurnalini (Т-9) ishlatadi.

## Nima uchun `tzrestored` dan import qilinadi

`app/notifications/tzrestored.py` ning docstring i buni oldindan
yozib qo'ygan: «§11/6 da uzilish bildirishnomasi va tuzatish o'sha
bo'g'inlarni qayta ishlatadi». §6.3 «Свет вернулся» ni birinchi
qilishni tezlik uchun emas, **xato narxi** uchun buyurgan edi: eng
arzon xabarda sinalgan quvur (obuna, tinch soatlar, limitlar, Т-7
ning kaliti, ertalabki svodka) endi eng qimmat xabarga beriladi.
Nusxa ko'chirish o'sha qarorni ikkiga bo'lardi: tinch soat oynasi
ikki joyda tuzatilishi kerak bo'lgan payt — birinchisi unutiladi.

Import yo'nalishi shu sababdan «tiklanish → uzilish», ya'ni tarixiy:
umumiy bo'g'inlar birinchi qurilgan modulda qoldi.

## §6.2 ning beshtasi: qaysi tur qaysisini o'tadi

| Tekshiruv | Uzilish | Rejali ishlar | Tuzatish |
|---|---|---|---|
| 1. Obuna | ✔ | ✔ | ✖ |
| 2. O'zi xabar bergan | ✔ | ✖ | ✖ |
| 3. Oprosga javob bergan | ✔ | ✖ | ✖ |
| 4. Tinch soatlar | ✔ | ✔ | ✖ |
| 5. Limitlar | ✔ (ikkalasi) | ✔ (sutkalik) | ✖ |

🔴 **Uzilish — beshtasi ham.** §6.2 ning 2- va 3-tekshiruvi so'zma-so'z
«про **отключение** не шлём» deydi, ya'ni ular aynan shu tur uchun
yozilgan. `tzrestored` da ular ataylab o'tkazib yuborilgan edi; bu
yerda ular ishlaydi va ТС-217 ning ikkinchi yarmini beradi.

🔴 **Rejali ishlar 2- va 3-tekshiruvni o'tkazib yuboradi.** Bugun
uzilish haqida xabar bergan odam ertaga rejalashtirilgan ishlarni
bilmaydi — bu boshqa hodisa haqidagi boshqa xabar. Soatlik limit ham
qo'llanmaydi: §6.2/5 ning birinchi yarmi «не более 1 уведомления
**об отключении** на адрес в час» deb turini ataylab nomlaydi.
Sutkalik yarmi esa odam haqida va turini ajratmaydi — u qo'llanadi.

🔴 **Tuzatish hech qaysisini o'tmaydi.** §6.4: «Это не опция.» Xabar
allaqachon ketgan; obunani bekor qilgan, limitini to'ldirgan yoki
uxlab yotgan odam ham noto'g'ri «sizda avariya» ni **olgan**. Uni
tinch soatlargacha ushlab turish — odamni butun tun yolg'on xabar
bilan qoldirish, ya'ni §6.4 ning maqsadini teskarisiga aylantirish.
Shuning uchun tuzatishda `Outcome.HOLD` umuman yo'q. 👤 Bu qaror
`PROGRESS.md` ning «Ochiq savollar» ida odam tasdig'iga qo'yilgan.

## «Подтверждено и выше» — status emas, o'tmish fakti

§6.2 ning oxiri: «Уведомления отправляются **только** на статус
"Подтверждено" и выше. На "Ожидает" и "Вероятно" — никогда.»

Bu modul `app.clustering` ni import qilmaydi (`05` §1 va Т-5), ya'ni
statusni o'zi bilolmaydi. Shuning uchun `Outage.notifies` — **kirish
maydoni** va uning sukut qiymati yo'q: chaqiruvchi `tzstatus.notifies()`
ni chaqirib, javobini bermaguncha `Outage` umuman yasalmaydi. Unutish
mumkin bo'lgan joy shu bilan yopiladi.

## Т-9 — qabul qiluvchilar jurnali

«Список получателей каждого уведомления хранится (для §6.4).»
`Receipt` — o'sha jurnalning bitta qatori, `record()` uni `SEND`
bo'lgan yetkazishlardan yasaydi, `correct()` esa **faqat o'sha
jurnaldan** tuzatish yuboradi. Manzil nomi (`label`) ham saqlanadi:
tuzatish yuborilayotganda odam manzilni o'chirgan bo'lishi mumkin,
§6.4 esa xabarni baribir talab qiladi.

Modul **toza**: bazaga, tarmoqqa va soatga bog'liq emas (Т-4 — `now`
argument bilan keladi), matn faqat i18n kalitlari sifatida chiqadi,
§7 ning birorta soni kodda son bo'lib yozilmagan (Т-1).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo
from enum import StrEnum

from app.core.tzconfig import TzParams
from app.notifications.tzrestored import (
    KEY_SEPARATOR,
    UNSUBSCRIBE_KEY,
    Address,
    Check,
    Delivery,
    Ledger,
    Outcome,
    Reason,
    delivery_key,
    in_quiet_hours,
    next_local_midnight,
    next_morning,
)

#: Hujjat bo'limi. Reyestrlar vitrinasi (`app.admin.registries`) shuni o'qiydi.
SPEC = "TZ §6.3 + §6.4"

#: §6.3: «Плановые работы — всем, **за 12 часов**». Bu son §7 ning
#: sozlamalar jadvalida **yo'q**, ya'ni Т-1 unga tegishli emas; u §6.3
#: matnining o'zidan olingan va shu yerda nom bilan turadi. 👤 Uni
#: sozlamaga chiqarish kerakmi — «Ochiq savollar» da.
PLANNED_LEAD = timedelta(hours=12)

#: Soatlik limit qayta tiklanadigan qadam (§6.2/5). Vaqtning o'lchovi,
#: §7 sozlamasi emas.
ONE_HOUR = timedelta(hours=1)


class Kind(StrEnum):
    """§6.3 jadvalining to'rt turi. Qiymatlar `tzrestored.NOTICES`
    ning `code` lari bilan **bir xil** — buni test qulflaydi."""

    OUTAGE = "outage"
    RESTORED = "restored"
    PLANNED = "planned"
    CORRECTION = "correction"


@dataclass(frozen=True)
class Channel:
    """Bu modul yasaydigan bitta bildirishnoma va uning **kirishi**.

    Ro'yxat kodda turadi, chunki uni `app.admin.registries` o'qiydi.
    `NOTICES` xabar **yasaladimi** ni aytadi; bu yerda esa ikkinchi
    savol: xabarni yasash uchun kerak bo'lgan ma'lumot qayerdan
    keladi. Ikkalasi bir xil emas, va farqni yashirish reyestrni
    yolg'onga aylantirardi.
    """

    kind: Kind
    #: Kirish ma'lumotini beradigan qatlam.
    source: str
    #: O'sha qatlam bugun bormi.
    wired: bool


CHANNELS: tuple[Channel, ...] = (
    Channel(
        kind=Kind.OUTAGE,
        source="tzstatus.notifies() + tzcount — hisob va status bor",
        wired=True,
    ),
    Channel(
        kind=Kind.PLANNED,
        # §8: «отметить плановые работы, внести официальный источник».
        # §11/7 (178-run) e'lonning **shaklini** qurdi —
        # `app.reports.tzsensor.Signal.PLANNED` — lekin operator uni
        # kiritadigan joy (jadval va panel shakli) hali yo'q, ya'ni
        # kanal baribir ulanmagan. Shakl bor, kirish yo'q.
        source="§8 operatori kiritadigan e'lon (shakli: tzsensor.Signal.PLANNED)",
        wired=False,
    ),
    Channel(
        kind=Kind.CORRECTION,
        # Т-9: «Список получателей каждого уведомления хранится».
        # 180-run: jadval (`tz_receipts`, `0014`) va uni o'qiydigan
        # qatlam (`app.notifications.tzreceipts`) paydo bo'ldi, ya'ni
        # tuzatishning kirishi endi haqiqatan bor.
        source="Т-9 ning qabul qiluvchilar jadvali (tz_receipts)",
        wired=True,
    ),
)


#: §6.2/2 va §6.2/3 — «про **отключение** не шлём». Faqat uzilish uchun.
OUTAGE_ONLY_CHECKS: frozenset[Check] = frozenset(
    {Check.SELF_REPORTED, Check.SURVEY_ANSWERED}
)

#: Har bir tur uchun haqiqatda qo'llanadigan tekshiruvlar, §6.2 tartibida.
APPLIED: Mapping[Kind, tuple[Check, ...]] = {
    Kind.OUTAGE: (
        Check.SUBSCRIBED,
        Check.SELF_REPORTED,
        Check.SURVEY_ANSWERED,
        Check.QUIET_HOURS,
        Check.LIMITS,
    ),
    Kind.PLANNED: (Check.SUBSCRIBED, Check.QUIET_HOURS, Check.LIMITS),
    #: §6.4: «Это не опция» — hech bir tekshiruv to'smaydi.
    Kind.CORRECTION: (),
}

#: §6.3 va §6.4 ning matnlari. Kalitlar **so'zma-so'z** yoziladi,
#: yig'ib yasalmaydi: yasalgan kalitni katalog skaneri ko'rmaydi va
#: o'lik tarjima jimgina paydo bo'lardi.
OUTAGE_KEY = "tz.notify.outage"
PLANNED_KEY = "tz.notify.planned"
#: §6.4: «что отменено и почему» — sabab turiga qarab ikki matn.
CORRECTION_RETRACTED_KEY = "tz.notify.correction_retracted"
CORRECTION_OPERATOR_KEY = "tz.notify.correction_operator"


class Cause(StrEnum):
    """Tuzatishning sababi — §6.4 ning «почему» si.

    Ikkitasi bor, chunki manba ikkita: aholining qarshi guvohliklari
    (§2.2, ТС-205) va operatorning qarori (§8). Uchinchi «umumiy»
    matn yozib bo'lmaydi: §6.4 sababni talab qiladi, «xabar noto'g'ri
    edi» esa sabab emas.
    """

    #: §2.2 — «свидетельства против», tasdiqlash qaytarib olindi.
    RETRACTED = "retracted"
    #: §8 — operator bekor qildi.
    OPERATOR = "operator"


CAUSE_KEYS: Mapping[Cause, str] = {
    Cause.RETRACTED: CORRECTION_RETRACTED_KEY,
    Cause.OPERATOR: CORRECTION_OPERATOR_KEY,
}


@dataclass(frozen=True)
class Outage:
    """§6.3 ning 1-qatori uchun kirish — **o'tmish fakti**.

    `confirmed_by` — «число подтвердивших» o'sha lahzada. Bildirishnoma
    ketayotganda hisob o'zgargan bo'lishi mumkin, matn esa voqea sodir
    bo'lgan paytdagi sonni aytishi kerak.

    `notifies` ning sukut qiymati **yo'q**: §6.2 ning oxirgi qoidasini
    (`Подтверждено` va undan yuqori) chaqiruvchi ochiq aytishi shart.
    """

    incident_id: str
    cell: str
    started_at: datetime
    confirmed_by: int
    notifies: bool


@dataclass(frozen=True)
class PlannedWork:
    """§6.3 ning 3-qatori: «адрес, дата, время, источник».

    `source` — §8 ning «внести официальный источник» i: operator
    kiritgan manba nomi. U matnga **chiqadi**, chunki rejali ishlar
    aholi hisobidan emas, tashqi e'londan keladi va odam uni
    tekshira olishi kerak.
    """

    incident_id: str
    cell: str
    starts_at: datetime
    source: str


@dataclass(frozen=True)
class Correction:
    """§6.4 — «что отменено и почему».

    `against` — §2.2 ning qarshi guvohlari soni; `Cause.OPERATOR` da
    o'qilmaydi va nol qoladi.
    """

    incident_id: str
    cell: str
    cause: Cause
    against: int = 0


@dataclass(frozen=True)
class Receipt:
    """Т-9: yuborilgan bitta xabarning bitta qabul qiluvchisi.

    `label` ham saqlanadi: tuzatish yuborilayotganda odam manzilni
    o'chirgan yoki nomini o'zgartirgan bo'lishi mumkin, §6.4 esa
    xabarni **o'sha** odamga, o'sha xabarning tili va manzil nomi
    bilan talab qiladi.
    """

    kind: Kind
    incident_id: str
    cell: str
    user_id: str
    address_id: str
    label: str
    lang: str
    sent_at: datetime

    @property
    def key(self) -> str:
        """Т-7 ning kaliti — jurnalni `Ledger.sent_keys` ga aylantirish uchun.

        🔴 **Turi kalitga kiradi** — `RESTORED` dan tashqari. Dastlab bu
        xossa uchlikni tursiz qaytarardi va o'sha holda jurnaldan
        qurilgan `Ledger` uzilish xabarini **hech qachon** to'smasdi:
        `plan_outage()` `outage_key(..., Kind.OUTAGE)` ni qidiradi,
        jurnal esa tursiz kalit berardi, ya'ni Т-7 aynan eng qimmat
        ikkita xabar uchun ishlamasdi va bir xil «sizda avariya»
        qayta-qayta ketaverardi. Nosozlik ko'rinmasdi: ikkala tomon
        ham o'zicha to'g'ri edi.

        `RESTORED` istisno, chunki uning kalitini `tzrestored` yasaydi
        va u modul turlar haqida umuman bilmaydi (`Kind` shu yerda
        e'lon qilingan, quyi modulda emas). Istisno shu yerda — bitta
        joyda — turadi, ikkala tomonda takrorlanmaydi.
        """
        base = delivery_key(self.incident_id, self.cell, self.address_id)
        if self.kind is Kind.RESTORED:
            return base
        return KEY_SEPARATOR.join((base, self.kind.value))


def next_hour(moment: datetime, *, tz: tzinfo) -> datetime:
    """§6.2/5 ning birinchi yarmi qayta tiklanadigan lahza.

    Mahalliy kalendarda — tinch soatlar va sutkalik limit bilan bir
    xil soatda: uch xil vaqt o'qi bo'lgan xizmatni tekshirib
    bo'lmaydi.
    """
    local = moment.astimezone(tz)
    return local.replace(minute=0, second=0, microsecond=0) + ONE_HOUR


def outage_key(incident_id: str, cell: str, address_id: str, kind: Kind) -> str:
    """Т-7 ning kaliti, turi bilan.

    Turi kalitga kiradi, chunki bitta hodisa bo'yicha bir manzilga
    ketadigan xabarlar bir nechta: uzilish, tiklanish va tuzatish.
    Ularni bitta kalitga qo'shish tuzatishni «allaqachon yuborilgan»
    deb tashlab yuborardi — ya'ni §6.4 ni jimgina buzardi.
    """
    return KEY_SEPARATOR.join((delivery_key(incident_id, cell, address_id), kind.value))


def render_outage(
    outage: Outage, address: Address, *, tz: tzinfo
) -> tuple[str, dict[str, object]]:
    """§6.3: «адрес, время начала, число подтвердивших»."""
    local = outage.started_at.astimezone(tz)
    return OUTAGE_KEY, {
        "address": address.label,
        "time": f"{local.hour:02d}:{local.minute:02d}",
        "count": outage.confirmed_by,
    }


def render_planned(
    work: PlannedWork, address: Address, *, tz: tzinfo
) -> tuple[str, dict[str, object]]:
    """§6.3: «адрес, дата, время, источник»."""
    local = work.starts_at.astimezone(tz)
    return PLANNED_KEY, {
        "address": address.label,
        "date": f"{local.day:02d}.{local.month:02d}",
        "time": f"{local.hour:02d}:{local.minute:02d}",
        "source": work.source,
    }


def render_correction(
    correction: Correction, receipt: Receipt
) -> tuple[str, dict[str, object]]:
    """§6.4: «что отменено и почему».

    Manzil nomi jurnaldan olinadi, joriy obunadan emas — xabar aynan
    o'sha manzil haqida ketgan edi.
    """
    if correction.cause is Cause.RETRACTED:
        return CAUSE_KEYS[Cause.RETRACTED], {
            "address": receipt.label,
            "against": correction.against,
        }
    return CAUSE_KEYS[Cause.OPERATOR], {"address": receipt.label}


def _decide_outage(
    address: Address,
    *,
    now: datetime,
    tz: tzinfo,
    params: TzParams,
    ledger: Ledger,
    key: str,
) -> tuple[Outcome, Reason, datetime | None, Check | None]:
    """§6.2 ning beshtasi, hujjatdagi tartibda.

    Т-7 ning kaliti eng birinchi tekshiriladi va u **tekshiruv emas**:
    beshtasi «kimga yuborish kerak» ni hal qiladi, kalit esa «bu xabar
    allaqachon ketganmi» ni.
    """
    if key in ledger.sent_keys:
        return Outcome.DROP, Reason.ALREADY_SENT, None, None
    if not address.confirmed:
        return Outcome.DROP, Reason.NOT_SUBSCRIBED, None, Check.SUBSCRIBED
    if address.reported:
        return Outcome.DROP, Reason.SELF_REPORTED, None, Check.SELF_REPORTED
    if address.answered_no:
        return Outcome.DROP, Reason.SURVEY_ANSWERED, None, Check.SURVEY_ANSWERED
    if not address.quiet_exempt and in_quiet_hours(now, tz=tz, params=params):
        return (
            Outcome.HOLD,
            Reason.QUIET_HOURS,
            next_morning(now, tz=tz, params=params),
            Check.QUIET_HOURS,
        )
    if ledger.sent_hour.get(address.address_id, 0) >= params.notify_per_address_hour:
        return Outcome.HOLD, Reason.HOURLY_LIMIT, next_hour(now, tz=tz), Check.LIMITS
    if ledger.sent_today.get(address.user_id, 0) >= params.notify_per_user_day:
        return (
            Outcome.HOLD,
            Reason.DAILY_LIMIT,
            next_local_midnight(now, tz=tz),
            Check.LIMITS,
        )
    return Outcome.SEND, Reason.NONE, now, None


def _decide_planned(
    address: Address,
    *,
    now: datetime,
    tz: tzinfo,
    params: TzParams,
    ledger: Ledger,
    key: str,
) -> tuple[Outcome, Reason, datetime | None, Check | None]:
    """Rejali ishlar: obuna → tinch soatlar → sutkalik limit.

    2- va 3-tekshiruv, hamda soatlik limit ataylab yo'q — sababi
    modul docstringida.
    """
    if key in ledger.sent_keys:
        return Outcome.DROP, Reason.ALREADY_SENT, None, None
    if not address.confirmed:
        return Outcome.DROP, Reason.NOT_SUBSCRIBED, None, Check.SUBSCRIBED
    if not address.quiet_exempt and in_quiet_hours(now, tz=tz, params=params):
        return (
            Outcome.HOLD,
            Reason.QUIET_HOURS,
            next_morning(now, tz=tz, params=params),
            Check.QUIET_HOURS,
        )
    if ledger.sent_today.get(address.user_id, 0) >= params.notify_per_user_day:
        return (
            Outcome.HOLD,
            Reason.DAILY_LIMIT,
            next_local_midnight(now, tz=tz),
            Check.LIMITS,
        )
    return Outcome.SEND, Reason.NONE, now, None


def plan_outage(
    outage: Outage,
    addresses: Iterable[Address],
    *,
    now: datetime,
    tz: tzinfo,
    params: TzParams,
    ledger: Ledger | None = None,
) -> tuple[Delivery, ...]:
    """Uzilish → har bir manzil uchun qaror.

    `notifies=False` bo'lsa ro'yxat **bo'sh**: §6.2 «На "Ожидает" и
    "Вероятно" — **никогда**» deydi, ya'ni bu `DROP` bilan sabab yozish
    emas, umuman yetkazish yasamaslik. Sabab yozilsa, keyingi qatlam
    uni «keyinroq yuborsak bo'ladi» deb o'qishi mumkin edi.

    Faqat shu kvartalning manzillari qaraladi; tartib — manzil
    identifikatori bo'yicha (Т-3).
    """
    if not outage.notifies:
        return ()
    book = ledger if ledger is not None else Ledger()
    result: list[Delivery] = []
    for address in sorted(addresses, key=lambda item: item.address_id):
        if address.cell != outage.cell:
            continue
        key = outage_key(outage.incident_id, outage.cell, address.address_id, Kind.OUTAGE)
        outcome, reason, send_at, failed = _decide_outage(
            address, now=now, tz=tz, params=params, ledger=book, key=key
        )
        text_key, text_args = render_outage(outage, address, tz=tz)
        result.append(
            Delivery(
                key=key,
                user_id=address.user_id,
                address_id=address.address_id,
                incident_id=outage.incident_id,
                cell=outage.cell,
                lang=address.lang,
                outcome=outcome,
                reason=reason,
                send_at=send_at,
                text_key=text_key,
                text_args=text_args,
                failed=failed,
            )
        )
    return tuple(result)


def planned_due(work: PlannedWork, *, now: datetime) -> bool:
    """§6.3: «за 12 часов».

    Erta yuborilgan e'lon unutiladi, kech yuborilgani foydasiz.
    Chegara **ikki tomonlama**: `now` ishlar boshlanishidan 12 soat
    oldin yoki undan keyin bo'lsa — vaqti keldi; undan oldin — hali
    emas.
    """
    return work.starts_at - PLANNED_LEAD <= now


def plan_planned(
    work: PlannedWork,
    addresses: Iterable[Address],
    *,
    now: datetime,
    tz: tzinfo,
    params: TzParams,
    ledger: Ledger | None = None,
) -> tuple[Delivery, ...]:
    """Rejali ishlar → qarorlar. Vaqti kelmagan bo'lsa — bo'sh ro'yxat.

    Boshlanib bo'lgan ishlar haqida ham yuborilmaydi: e'lon
    ogohlantirish, hisobot emas.
    """
    if not planned_due(work, now=now) or work.starts_at <= now:
        return ()
    book = ledger if ledger is not None else Ledger()
    result: list[Delivery] = []
    for address in sorted(addresses, key=lambda item: item.address_id):
        if address.cell != work.cell:
            continue
        key = outage_key(work.incident_id, work.cell, address.address_id, Kind.PLANNED)
        outcome, reason, send_at, failed = _decide_planned(
            address, now=now, tz=tz, params=params, ledger=book, key=key
        )
        text_key, text_args = render_planned(work, address, tz=tz)
        result.append(
            Delivery(
                key=key,
                user_id=address.user_id,
                address_id=address.address_id,
                incident_id=work.incident_id,
                cell=work.cell,
                lang=address.lang,
                outcome=outcome,
                reason=reason,
                send_at=send_at,
                text_key=text_key,
                text_args=text_args,
                failed=failed,
            )
        )
    return tuple(result)


def record(
    deliveries: Iterable[Delivery],
    addresses: Iterable[Address],
    *,
    kind: Kind,
    now: datetime,
) -> tuple[Receipt, ...]:
    """Т-9: `SEND` bo'lganlardan jurnal qatorlarini yasaydi.

    Faqat `SEND`: ushlab qolingan xabar hali ketmagan, ya'ni uni
    tuzatish kerak emas — uni **bekor qilish** kerak (`cancel()`).

    Manzil nomi joriy obunalar ro'yxatidan olinadi va jurnalga
    **ko'chiriladi**: keyinchalik obuna o'chsa ham §6.4 ning matni
    yasaladi.
    """
    labels = {address.address_id: address.label for address in addresses}
    return tuple(
        Receipt(
            kind=kind,
            incident_id=item.incident_id,
            cell=item.cell,
            user_id=item.user_id,
            address_id=item.address_id,
            label=labels.get(item.address_id, item.address_id),
            lang=item.lang,
            sent_at=now,
        )
        for item in deliveries
        if item.outcome is Outcome.SEND
    )


def cancel(
    deliveries: Iterable[Delivery], incident_id: str
) -> tuple[Delivery, ...]:
    """Tasdiqlash qaytarib olinganda — hali ketmagan xabarlarni olib tashlash.

    §6.4 tuzatishni **yuborilgan** xabarlar uchun talab qiladi. Ushlab
    qolinganlari esa umuman yuborilmasligi kerak: ertalab kelgan
    «sizda avariya» ni darhol «u bekor qilindi» bilan quvish odamni
    ikki marta bezovta qilish va ishonchni yana bir marta kamaytirish
    bo'lardi.
    """
    return tuple(
        item
        for item in deliveries
        if not (item.incident_id == incident_id and item.outcome is Outcome.HOLD)
    )


def correct(
    correction: Correction,
    receipts: Iterable[Receipt],
    *,
    now: datetime,
) -> tuple[Delivery, ...]:
    """§6.4: «тем же людям, тем же каналом» — majburiy tuzatish.

    Manba — **faqat** Т-9 ning jurnali: kimga uzilish haqida xabar
    ketgan bo'lsa, o'shanga tuzatish ketadi. Joriy obunalar ro'yxati
    o'qilmaydi.

    Hech bir tekshiruv qo'llanmaydi va `HOLD` yo'q: yakun har doim
    `SEND`. Sabab modul docstringida.

    Tartib — manzil identifikatori bo'yicha (Т-3).
    """
    rows = [
        item
        for item in receipts
        if item.kind is Kind.OUTAGE
        and item.incident_id == correction.incident_id
        and item.cell == correction.cell
    ]
    result: list[Delivery] = []
    for receipt in sorted(rows, key=lambda item: item.address_id):
        text_key, text_args = render_correction(correction, receipt)
        result.append(
            Delivery(
                key=outage_key(
                    receipt.incident_id, receipt.cell, receipt.address_id, Kind.CORRECTION
                ),
                user_id=receipt.user_id,
                address_id=receipt.address_id,
                incident_id=receipt.incident_id,
                cell=receipt.cell,
                lang=receipt.lang,
                outcome=Outcome.SEND,
                reason=Reason.CORRECTION,
                send_at=now,
                text_key=text_key,
                text_args=text_args,
                failed=None,
            )
        )
    return tuple(result)


def record_correction(
    deliveries: Iterable[Delivery],
    receipts: Iterable[Receipt],
    *,
    now: datetime,
) -> tuple[Receipt, ...]:
    """Т-9: tuzatishning o'zi ham jurnalga tushadi.

    `record()` manzil nomini **joriy obunalar** ro'yxatidan oladi;
    tuzatishda esa bunday ro'yxat umuman o'qilmaydi (§6.4 — «тем же
    людям»), ya'ni nom va til birinchi xabarning jurnal qatoridan
    ko'chiriladi. Shu sababdan bu alohida funksiya: `record()` ga
    `Address` stub lari yasab uzatish o'sha qarorni yashirardi.

    Nima uchun tuzatish ham yoziladi: usiz «tuzatish yuborilganmi»
    savoliga javob faqat protsess xotirasida bo'lardi va qayta ishga
    tushirilgan navbat butun kvartalga ikkinchi marta «biz xato
    qildik» yuborardi. Т-7 ning kaliti (turi bilan) shu qatorda
    saqlanadi va aynan shuni to'sadi.
    """
    known = {item.address_id: item for item in receipts if item.kind is Kind.OUTAGE}
    result: list[Receipt] = []
    for item in deliveries:
        if item.outcome is not Outcome.SEND:
            continue
        origin = known.get(item.address_id)
        result.append(
            Receipt(
                kind=Kind.CORRECTION,
                incident_id=item.incident_id,
                cell=item.cell,
                user_id=item.user_id,
                address_id=item.address_id,
                label=origin.label if origin is not None else item.address_id,
                lang=item.lang,
                sent_at=now,
            )
        )
    return tuple(result)


def keys_of(deliveries: Iterable[Delivery]) -> tuple[str, ...]:
    """Xabarga chiqadigan i18n kalitlari — §6.1 ning otpiskasi bilan.

    `Delivery.keys` bitta yetkazish uchun; bu — ro'yxat uchun. Faqat
    `SEND`: to'silgan yetkazishning matni odamgacha yetmaydi, ya'ni
    uni kalitlar ro'yxatiga qo'shish «bu matn ko'rsatildi» degan
    yolg'on da'vo bo'lardi. Takrorlar olib tashlanmaydi: har xabar
    o'z otpiska qatorini oladi.
    """
    result: list[str] = []
    for item in deliveries:
        if item.outcome is not Outcome.SEND:
            continue
        result += [item.text_key, UNSUBSCRIBE_KEY]
    return tuple(result)
