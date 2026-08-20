"""TZ §6.3 — «Свет вернулся» bildirishnomasi (§11 navbatining 5-bandi).

## Nima uchun aynan shu bildirishnoma birinchi

§6.3 ning o'zi aytadi: «Приоритет разработки: **"Свет вернулся"
делается первым.** Оно полезнее всех и почти безвредно при ошибке.
Ошибочное "свет дали" — мелкая неприятность. Ошибочное "у вас авария"
— удар по доверию к сервису.» Ya'ni navbatning bu bandi tezlik uchun
emas, **xato narxi** uchun tanlangan: quvurning hamma bo'g'ini (obuna,
tekshiruvlar, tinch soatlar, limitlar, qabul qiluvchilar ro'yxati) shu
eng arzon bildirishnomada sinaladi, keyin §11/6 da uzilish
bildirishnomasi va tuzatish o'sha bo'g'inlarni qayta ishlatadi.

## Modul chegarasi: `app.notifications` `app.clustering` ni bilmaydi

`05` §1 va `app/notifications/events.py` ning qarori shu yerda ham
saqlanadi: bu modul `tzrestore` ni ham, `tzstatus` ni ham import
qilmaydi. Kirish — `Closure`, ya'ni **o'tmish fakti**: kvartal qachon
va qancha davomiylik bilan yopilgani. Bildirishnoma yuborilayotgan
paytda hodisa yana o'zgargan bo'lishi mumkin, matn esa voqea sodir
bo'lgan paytdagi holatni aytishi kerak.

Shu sababdan Т-5 ham buzilmaydi: bu yerda status **tanlanmaydi** va
`TzStatus` umuman import qilinmaydi. «Podtverjdeno va undan yuqori»
filtri `tzstatus.notifies()` da qoladi.

🔴 **Lekin filtrning javobi kirish maydoni bo'lishi kerak** (184-run).
178-rundan beri bu yerda «bu modul chaqirilgan bo'lsa, demak status
allaqachon tanlangan» deb yozilgan edi — ya'ni yuborish huquqi
chaqiruvchining **yodida** turardi va hech qayerda o'lchanmasdi.
ТС-212 aynan o'sha bo'shliqni ko'rsatadi: uch soat jimlikdan keyin
hodisa «Данные устарели» bo'ladi (§5: «уведомления — **нет**»), lekin
kvartallarning bir qismi allaqachon yopilgan bo'lishi mumkin —
`Restoration.any_closed` shu holatning sharti. Yopilgan kvartallar
ro'yxatidan to'g'ridan-to'g'ri `Closure` yasagan chaqiruvchi jimgina
«svet qaytdi» yuborardi va modulning birorta testi buni ko'rmasdi.
Shuning uchun `Closure.notifies` — **sukut qiymatisiz** maydon
(`tzoutage.Outage.notifies` bilan bir xil naql), `plan()` esa
`False` da bo'sh ro'yxat qaytaradi.

## §6.2 ning beshta tekshiruvidan qaysilari qo'llanadi

Jadvalning o'zi ikkitasini **ataylab** chetlab o'tadi:

* 2-tekshiruv — «Сам сообщил об этой аварии? Да — про отключение
  **не** шлём... Про возврат света — шлём.»
* 3-tekshiruv — «Ответил на опрос "света нет"? Да — про **отключение**
  не шлём.»

Ikkalasi ham uzilish haqidagi xabarni to'sadi, tiklanish haqidagisini
emas: xabar bergan odam aynan svet qaytganini bilmaydi va §6.3 ning
«Кому ценно» ustuni «Свет вернулся» uchun «**всем**» deydi. Shuning
uchun `Address.reported` va `Address.answered_no` maydonlari bu yerda
**bor**, lekin qarorga ta'sir qilmaydi — va buni alohida test qulflaydi
(ТС-217). Maydonlarni olib tashlash mumkin emas edi: §11/6 da o'sha
ro'yxat uzilish bildirishnomasiga beriladi va u yerda ikkala maydon ham
to'sadi.

Qolgan uchtasi qo'llanadi va §6.2 ning **tartibida**: obuna → tinch
soatlar → limitlar.

## Uchta qaror sabab bilan

🔴 **Bir martalik geolokatsiya obuna emas** (§6.1). Shuning uchun
`Address.confirmed` sukut bo'yicha `False` va tasdiqlanmagan manzil
`DROP` oladi, `HOLD` emas: bu vaqtinchalik to'siq emas, roziligi yo'q
odam. ТС-214 aynan shuni o'lchaydi.

🔴 **Tinch soat va limit — `HOLD`, `DROP` emas.** §6.2 ikkalasi uchun
ham «копим до утра» va «придержать» deydi, «не отправляем» emas. Farq
«Свет вернулся» da ayniqsa muhim: kechasi tashlab yuborilgan xabar
ertalab hech qachon kelmaydi va odam svet qaytganini umuman bilmaydi.
`send_at` shuning uchun **hisoblanadi**, `None` qoldirilmaydi: tinch
soat uchun — ertalabki chegara, sutkalik limit uchun — mahalliy
yarim tun, ya'ni hisoblagich nolga tushadigan lahza. Ikkalasi ham bir
xil mahalliy kalendardan chiqadi.

🔴 **Soatlik limit bu yerda qo'llanmaydi.** §6.2 ning 5-tekshiruvi:
«не более 1 уведомления **об отключении** на адрес в час и 5 в сутки
на человека». Birinchi yarmi uzilish bildirishnomasi haqida — u §11/6
da qo'llanadi; ikkinchi yarmi odam haqida va turini ajratmaydi, ya'ni
tiklanish xabari sutkalik hisobga **kiradi**. Ikkalasini ham bu yerda
qo'llash svet qaytganini aytmaslikning eng oson yo'li bo'lardi:
uzilish xabari o'sha manzilga o'sha soatda allaqachon ketgan bo'ladi.

## Т-7 va Т-9

Т-7 — «Повторная отправка того же сообщения не создаёт второго
свидетельства». Bildirishnoma tomonida buning ko'rinishi:
`(hodisa, kvartal, manzil)` uchligi — **kalit**, va `Ledger.sent_keys`
da bo'lgan kalit qayta yuborilmaydi. Kvartal ikkinchi marta yopilsa
(masalan qayta hisoblashda), odam ikkinchi «svet qaytdi» ni olmaydi.

Т-9 — «Список получателей каждого уведомления хранится (для §6.4)».
`recipients()` o'sha ro'yxatni **yasaydi**; jurnal qatorining shakli
(`Receipt`) va tuzatishni yasaydigan `correct()` §11/6 da —
`app/notifications/tzoutage.py`. Jurnalni saqlaydigan jadval hali
yo'q va bu keyingi qadam.

Modul **toza**: bazaga, tarmoqqa va soatga bog'liq emas (Т-4 — `now`
argument bilan keladi), matn faqat i18n kalitlari sifatida chiqadi
(`04` §6), §7 ning birorta soni kodda son bo'lib yozilmagan (Т-1).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta, tzinfo
from enum import StrEnum

from app.core.tzconfig import TzParams

#: Hujjat bo'limi. Reyestrlar vitrinasi (`app.admin.registries`) shuni o'qiydi.
SPEC = "TZ §6.3"

#: Kalitning bo'laklarini ajratuvchi. Manzil va hodisa identifikatorlari
#: UUID yoki `tg_id`, ya'ni bu belgi ularda uchramaydi.
KEY_SEPARATOR = "|"

#: Mahalliy sutkaning uzunligi — `send_at` ni ertangi kunga surish uchun.
#: Vaqtning o'lchovi, §7 sozlamasi emas.
ONE_DAY = timedelta(days=1)


@dataclass(frozen=True)
class Notice:
    """§6.3 jadvalining bitta qatori va u qurilganmi.

    Ro'yxat kodda turadi, chunki uni `app.admin.registries` o'qiydi:
    to'rtta bildirishnomadan qaysi biri **haqiqatda yuboriladi** —
    operator ko'radigan joyda yozilishi kerak, sessiya jurnalida emas.
    """

    code: str
    note: str
    built: bool


NOTICES: tuple[Notice, ...] = (
    Notice(
        code="outage",
        note="Uzilish: manzil, boshlanish vaqti, tasdiqlaganlar soni",
        # §11/6 — `app/notifications/tzoutage.py`, §6.2 ning beshtasi ham.
        built=True,
    ),
    Notice(
        code="restored",
        note="Svet qaytdi: manzil, vaqt, davomiylik",
        built=True,
    ),
    Notice(
        code="planned",
        note="Rejali ishlar: manzil, sana, vaqt, manba — 12 soat oldin",
        # §11/6 — `tzoutage.plan_planned()`; manbani §8 bo'yicha
        # operator kiritadi, e'lonni kiritish qatlami hali yo'q.
        built=True,
    ),
    Notice(
        code="correction",
        note="Tuzatish: nima bekor qilindi va nega (§6.4, majburiy)",
        # §11/6 — `tzoutage.correct()`, manbasi Т-9 ning jurnali.
        built=True,
    ),
)


class Check(StrEnum):
    """§6.2 ning beshta tekshiruvi, hujjatdagi tartibda."""

    #: 1. Bu manzilga obuna bo'lganmi (§6.1 — geolokatsiya obuna emas).
    SUBSCRIBED = "subscribed"
    #: 2. O'zi shu uzilish haqida xabar berganmi.
    SELF_REPORTED = "self_reported"
    #: 3. Oprosga «svet yo'q» deb javob berganmi.
    SURVEY_ANSWERED = "survey_answered"
    #: 4. Tinch soatlar (23:00–07:00).
    QUIET_HOURS = "quiet_hours"
    #: 5. Limitlar (manzilga soatiga, odamga sutkasiga).
    LIMITS = "limits"


CHECKS: tuple[Check, ...] = (
    Check.SUBSCRIBED,
    Check.SELF_REPORTED,
    Check.SURVEY_ANSWERED,
    Check.QUIET_HOURS,
    Check.LIMITS,
)

#: §6.3 jadvalining o'z qarori: bu ikki tekshiruv **faqat uzilish**
#: bildirishnomasini to'sadi. «Свет вернулся» ularni o'tkazib yuboradi.
SKIPPED_FOR_RESTORED: frozenset[Check] = frozenset({Check.SELF_REPORTED, Check.SURVEY_ANSWERED})

#: «Свет вернулся» uchun haqiqatda qo'llanadigan tekshiruvlar, tartibda.
APPLIED_FOR_RESTORED: tuple[Check, ...] = tuple(
    check for check in CHECKS if check not in SKIPPED_FOR_RESTORED
)


class Outcome(StrEnum):
    """Bitta manzil uchun yakun."""

    #: Hozir yuboriladi.
    SEND = "send"
    #: Keyinroq yuboriladi — `send_at` da. Xabar **yo'qolmaydi**.
    HOLD = "hold"
    #: Umuman yuborilmaydi.
    DROP = "drop"


class Reason(StrEnum):
    """Yakunning sababi. Jurnalga va admin paneliga; matnga emas."""

    NONE = "none"
    #: §6.1: manzil bor, lekin obuna tasdiqlanmagan.
    NOT_SUBSCRIBED = "not_subscribed"
    #: Т-7: shu uchlik uchun xabar allaqachon ketgan.
    ALREADY_SENT = "already_sent"
    #: §6.2/4: tinch soatlar, ertalabgacha to'planadi.
    QUIET_HOURS = "quiet_hours"
    #: §6.2/5: sutkalik limit to'ldi.
    DAILY_LIMIT = "daily_limit"
    #: §6.2/2: o'zi shu uzilish haqida xabar bergan. Faqat uzilish
    #: bildirishnomasini to'sadi (`tzoutage`), tiklanishnikini emas.
    SELF_REPORTED = "self_reported"
    #: §6.2/3: oprosga «svet yo'q» deb javob bergan. Faqat uzilish.
    SURVEY_ANSWERED = "survey_answered"
    #: §6.2/5 ning birinchi yarmi: manzilga soatiga bitta uzilish
    #: xabari. Turini ataylab nomlaydi, shuning uchun faqat `tzoutage`.
    HOURLY_LIMIT = "hourly_limit"
    #: §6.4: majburiy tuzatish. Tekshiruvdan o'tgani emas — hech bir
    #: tekshiruv qo'llanmagani.
    CORRECTION = "correction"


#: §6.3 — «Свет вернулся» matni. Kalitlar **so'zma-so'z** yoziladi,
#: `f"tz.notify.{...}"` emas: yig'ib yasalgan kalitni katalog skaneri
#: ko'rmaydi va o'lik tarjima jimgina paydo bo'lardi.
RESTORED_KEY = "tz.notify.restored"
#: Davomiylik aniq bo'lmaganda (§4.2 ning ikkita soni). Aniqlikni
#: bo'rttirish §4.2 ning butun ma'nosini yo'qotardi.
RESTORED_APPROX_KEY = "tz.notify.restored_approx"
#: §6.2/4: ertalab **bitta svodka** yuboriladi.
DIGEST_KEY = "tz.notify.digest"
#: §6.1: «Отписка — в один шаг из любого уведомления».
UNSUBSCRIBE_KEY = "tz.notify.unsubscribe"


@dataclass(frozen=True)
class Address:
    """Odamning bitta obuna manzili (§6.1: uy, ish, ota-onalar).

    `reported` va `answered_no` — §6.2 ning 2- va 3-tekshiruvi uchun.
    «Свет вернулся» ularga qaramaydi (jadvalning o'z qarori), lekin
    ular shu yerda turadi: §11/6 ning uzilish bildirishnomasi aynan
    shu ro'yxatni oladi.
    """

    user_id: str
    address_id: str
    #: Kvartal (r9) — §4 ning tiklanish birligi.
    cell: str
    #: Foydalanuvchi bergan nom: «Uy», «Ish». Matnga shu chiqadi.
    label: str
    lang: str
    #: §6.1: geolokatsiya yuborish rozilik emas. Sukut — obuna yo'q.
    confirmed: bool = False
    #: §6.2/4: «Пользователь может включить исключение».
    quiet_exempt: bool = False
    #: §6.2/2 — «Свет вернулся» uchun ahamiyatsiz, ataylab.
    reported: bool = False
    #: §6.2/3 — «Свет вернулся» uchun ahamiyatsiz, ataylab.
    answered_no: bool = False


@dataclass(frozen=True)
class Closure:
    """Yopilgan kvartal — **o'tmish fakti**, hodisaning joriy holati emas.

    `hours`/`minutes` — aniq davomiylik; `low_hours`/`high_hours` —
    §4.2 ning ikkita soni. `exact=False` bo'lganda matn diapazonni
    ko'rsatadi va «aniq emas» deb belgilanadi.
    """

    incident_id: str
    cell: str
    closed_at: datetime
    hours: int
    minutes: int
    #: §6.2 ning yuborish huquqi — §5 jadvalining oxirgi ustuni.
    #: Sukut qiymati **ataylab yo'q**: `tzoutage.Outage.notifies` bilan
    #: bir xil qaror. Chaqiruvchi javobni ochiq bermaguncha `Closure`
    #: yasalmaydi, ya'ni «bu modul chaqirilgan bo'lsa status allaqachon
    #: tanlangan» degan taxmin **kirish maydoniga** aylandi va
    #: o'lchanadigan bo'ldi (ТС-212).
    notifies: bool
    exact: bool = True
    low_hours: int = 0
    high_hours: int = 0


@dataclass(frozen=True)
class Ledger:
    """Allaqachon yuborilganlar — Т-7 va §6.2/5 uchun.

    Ikkalasi ham **kirish**, ya'ni bu modul bazaga qaramaydi:
    `sent_keys` — Т-7 ning uchligi, `sent_today` — odam bo'yicha
    mahalliy sutkadagi bildirishnomalar soni.
    """

    sent_keys: frozenset[str] = frozenset()
    sent_today: Mapping[str, int] = field(default_factory=dict)
    #: Manzil bo'yicha o'tgan soatdagi **uzilish** bildirishnomalari.
    #: «Свет вернулся» uni ataylab **o'qimaydi** (§6.2/5 ning birinchi
    #: yarmi turni ajratadi); maydon shu yerda turadi, chunki §11/6 ning
    #: uzilish bildirishnomasi aynan shu jurnalni oladi.
    sent_hour: Mapping[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class Delivery:
    """Bitta manzil uchun qaror va uning matni."""

    key: str
    user_id: str
    address_id: str
    incident_id: str
    cell: str
    lang: str
    outcome: Outcome
    reason: Reason
    #: `HOLD` da — qachon qayta urinish kerak. `SEND` da — hozir.
    send_at: datetime | None
    text_key: str
    text_args: dict[str, object]
    #: Tekshiruv qaysi bosqichda to'xtagani. `None` — hammasidan o'tdi.
    failed: Check | None = None

    @property
    def sends(self) -> bool:
        """Matn hozir ketadimi."""
        return self.outcome is Outcome.SEND

    @property
    def keys(self) -> tuple[str, ...]:
        """Xabarga chiqadigan barcha i18n kalitlari, tartibda.

        Otpiska §6.1 bo'yicha **har** bildirishnomada bor.
        """
        return (self.text_key, UNSUBSCRIBE_KEY)


@dataclass(frozen=True)
class Digest:
    """§6.2/4 — ertalabki yagona svodka.

    Tunda to'plangan bir nechta «svet qaytdi» bitta xabarga yig'iladi:
    §6.2 «отправляем одним сводным сообщением» deydi, ya'ni ertalab
    soat yettida beshta alohida xabar yuborish tekshiruvni bajarish
    emas, uni chetlab o'tish bo'lardi.
    """

    user_id: str
    lang: str
    send_at: datetime
    items: tuple[Delivery, ...]
    text_key: str = DIGEST_KEY

    @property
    def count(self) -> int:
        return len(self.items)

    @property
    def text_args(self) -> dict[str, object]:
        return {"count": self.count}


def delivery_key(incident_id: str, cell: str, address_id: str) -> str:
    """Т-7: `(hodisa, kvartal, manzil)` — takrorlanmaslikning kaliti.

    Manzil (odam emas) kalitga kiradi, chunki §6.1 bo'yicha bir odamda
    uchtagacha manzil bo'ladi va ularning ikkitasi bir kvartalda
    bo'lishi mumkin — «uy» va «ota-onalar». Ikkalasi ham ayrim xabar
    oladi: matnda aynan manzil nomi turadi.
    """
    return KEY_SEPARATOR.join((incident_id, cell, address_id))


def in_quiet_hours(moment: datetime, *, tz: tzinfo, params: TzParams) -> bool:
    """§6.2/4: mahalliy vaqt tinch soatlar oynasidamikan.

    Oyna **sutkadan oshib ketadi** (23:00 → 07:00), shuning uchun
    oddiy `from <= hour < to` ishlamaydi. Teng chegaralar («oyna yo'q»)
    alohida qaraladi: `23 <= hour or hour < 23` har doim rost bo'lardi
    va butun sutka jim qolardi.
    """
    hour = moment.astimezone(tz).hour
    start, end = params.quiet_from_hour, params.quiet_to_hour
    if start == end:
        return False
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


def next_morning(moment: datetime, *, tz: tzinfo, params: TzParams) -> datetime:
    """Tinch soatlar tugaydigan eng yaqin lahza (mahalliy vaqtda).

    Kechqurun kelgan xabar **ertangi** ertalabga, tundan keyingisi —
    o'sha kunning ertalabiga suriladi.
    """
    local = moment.astimezone(tz)
    morning = local.replace(hour=params.quiet_to_hour, minute=0, second=0, microsecond=0)
    if morning <= local:
        morning = morning + ONE_DAY
    return morning


def next_local_midnight(moment: datetime, *, tz: tzinfo) -> datetime:
    """Sutkalik hisoblagich nolga tushadigan lahza (§6.2/5).

    Limit «в сутки на человека» deydi, ya'ni u mahalliy kalendarga
    bog'langan — tinch soatlar bilan bir xil kalendarga.
    """
    local = moment.astimezone(tz)
    return local.replace(hour=0, minute=0, second=0, microsecond=0) + ONE_DAY


def render(closure: Closure, address: Address, *, tz: tzinfo) -> tuple[str, dict[str, object]]:
    """§6.3: «адрес, время, длительность».

    Vaqt mahalliy zonada va `HH:MM` da — odam soatiga qaraydi, UTC ga
    emas. Davomiylik aniq bo'lmasa **diapazon** ko'rsatiladi: §4.2 ning
    ikkita sonini bitta o'rtachaga aylantirish ma'lumotda yo'q
    aniqlikni ko'rsatish bo'lardi.
    """
    local = closure.closed_at.astimezone(tz)
    when = f"{local.hour:02d}:{local.minute:02d}"
    if closure.exact:
        return RESTORED_KEY, {
            "address": address.label,
            "time": when,
            "hours": closure.hours,
            "minutes": closure.minutes,
        }
    return RESTORED_APPROX_KEY, {
        "address": address.label,
        "time": when,
        "low": closure.low_hours,
        "high": closure.high_hours,
    }


def _decide(
    closure: Closure,
    address: Address,
    *,
    now: datetime,
    tz: tzinfo,
    params: TzParams,
    ledger: Ledger,
    key: str,
) -> tuple[Outcome, Reason, datetime | None, Check | None]:
    """§6.2 ning tartibi: obuna → tinch soatlar → limitlar.

    Т-7 ning kaliti eng birinchi tekshiriladi va u **tekshiruv emas**:
    §6.2 ning beshtasi «kimga yuborish kerak» ni hal qiladi, kalit esa
    «bu xabar allaqachon ketganmi» ni. Shuning uchun `failed` bo'sh
    qoladi — hech bir tekshiruv yiqilmagan.
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


def plan(
    closure: Closure,
    addresses: Iterable[Address],
    *,
    now: datetime,
    tz: tzinfo,
    params: TzParams,
    ledger: Ledger | None = None,
) -> tuple[Delivery, ...]:
    """Yopilgan kvartal → har bir manzil uchun qaror.

    `notifies=False` bo'lsa ro'yxat **bo'sh** — `plan_outage()` bilan
    bir xil naql: §5 jadvalining «Данные устарели» qatori
    «уведомления: **нет**» deydi, ya'ni bu `DROP` bilan sabab yozish
    emas, umuman yetkazish yasamaslik. Sabab yozilsa, keyingi qatlam
    uni «keyinroq yuborsak bo'ladi» deb o'qishi mumkin edi — jimlik
    esa hech qachon «svet qaytdi» ga aylanmaydi.

    Faqat **shu kvartalning** manzillari qaraladi: §5 jadvali
    «Частично восстановлено» uchun «да, **по кварталам**» deydi, ya'ni
    svet qaytmagan kvartaldagi odamga «svet qaytdi» yuborilmaydi.
    Filtrni chaqiruvchiga qoldirish o'sha xatoni har chaqiruv joyida
    qaytadan qilish imkonini berardi.

    Tartib — manzil identifikatori bo'yicha: Т-3 (qayta hisoblash
    o'sha natijani beradi) ro'yxatning tartibiga ham tegishli.
    """
    if not closure.notifies:
        return ()
    book = ledger if ledger is not None else Ledger()
    deliveries: list[Delivery] = []
    for address in sorted(addresses, key=lambda item: item.address_id):
        if address.cell != closure.cell:
            continue
        key = delivery_key(closure.incident_id, closure.cell, address.address_id)
        outcome, reason, send_at, failed = _decide(
            closure,
            address,
            now=now,
            tz=tz,
            params=params,
            ledger=book,
            key=key,
        )
        text_key, text_args = render(closure, address, tz=tz)
        deliveries.append(
            Delivery(
                key=key,
                user_id=address.user_id,
                address_id=address.address_id,
                incident_id=closure.incident_id,
                cell=closure.cell,
                lang=address.lang,
                outcome=outcome,
                reason=reason,
                send_at=send_at,
                text_key=text_key,
                text_args=text_args,
                failed=failed,
            )
        )
    return tuple(deliveries)


def plan_all(
    closures: Iterable[Closure],
    addresses: Iterable[Address],
    *,
    now: datetime,
    tz: tzinfo,
    params: TzParams,
    ledger: Ledger | None = None,
) -> tuple[Delivery, ...]:
    """Bir nechta yopilgan kvartal — hodisa «qisman tiklandi» bo'lganda.

    Kvartallar `cell` bo'yicha tartiblanadi (Т-3), manzillar esa har
    kvartal ichida `plan()` ning tartibida qoladi.

    Bitta kvartal ro'yxatda ikki marta uchrasa — bir marta qaraladi:
    Т-7 ning kaliti `(hodisa, kvartal, manzil)`, ya'ni takror qator
    `Ledger` gacha yetmasdan ham ikkinchi xabar yasay olmasligi kerak.
    """
    book = ledger if ledger is not None else Ledger()
    unique: dict[str, Closure] = {}
    for closure in sorted(closures, key=lambda item: item.cell):
        unique.setdefault(closure.cell, closure)
    result: list[Delivery] = []
    for closure in unique.values():
        result += list(plan(closure, addresses, now=now, tz=tz, params=params, ledger=book))
    return tuple(result)


def recipients(deliveries: Iterable[Delivery]) -> tuple[tuple[str, str], ...]:
    """Т-9: xabar **ketgan** odamlar ro'yxati, `(user_id, address_id)`.

    Faqat `SEND`: §6.4 ning tuzatishi «тем, кому уже отправили ошибку»
    deydi. Ushlab qolingan xabar hali ketmagan, ya'ni uni tuzatish
    kerak emas — uni **bekor qilish** kerak, va bu §11/6 ning ishi.
    """
    return tuple(
        (item.user_id, item.address_id) for item in deliveries if item.outcome is Outcome.SEND
    )


def held(deliveries: Iterable[Delivery]) -> tuple[Delivery, ...]:
    """Ushlab qolinganlar — qayta urinish navbati uchun."""
    return tuple(item for item in deliveries if item.outcome is Outcome.HOLD)


def digests(deliveries: Sequence[Delivery]) -> tuple[Digest, ...]:
    """§6.2/4: tunda to'plangan xabarlar — odam bo'yicha bitta svodka.

    Guruh kaliti — `(odam, chiqarish lahzasi)`. Lahza kalitga kiradi,
    chunki ikki xil sababdan ushlangan xabarlar (tinch soat va sutkalik
    limit) turli vaqtda chiqadi va ularni bitta svodkaga qo'shish
    ikkinchisini vaqtidan oldin yuborish bo'lardi.
    """
    groups: dict[tuple[str, datetime], list[Delivery]] = {}
    for item in deliveries:
        if item.outcome is not Outcome.HOLD or item.send_at is None:
            continue
        groups.setdefault((item.user_id, item.send_at), []).append(item)
    result = [
        Digest(
            user_id=user_id,
            lang=items[0].lang,
            send_at=send_at,
            items=tuple(items),
        )
        for (user_id, send_at), items in sorted(groups.items())
    ]
    return tuple(result)
