"""TZ §5 — statuslar va karta hisoblagichi.

`TZ_Podtverzhdenie_i_uvedomleniya.md` §11 navbatining ikkinchi bandi
ikkiga bo'lingan: sanash — `app/clustering/tzcount.py`, status va karta —
shu yerda.

## Nima uchun hisoblagich darhol ko'rsatiladi

§5 ning oxirgi izohi: «Счётчик "1 из 3" показывается **сразу**. Это
единственный способ объяснить человеку, почему его сообщение принято,
но аварии на карте ещё нет.» TZ ning o'zi buni **razmen** deb ataydi:
hisoblagich soxta hisob yig'moqchi bo'lgan odamga ham nechta akkaunt
kerakligini aytadi. Qaror — ko'rsatish; sababi hujjatda, kodda emas.

## Т-5: status bitta joyda o'zgaradi

Т-5 «Статус меняется в одном месте программы» deydi. Shu modulning
`decide()` funksiyasi — o'sha yagona joy. `tests/test_tz_status.py`
buni qorovul bilan qulflaydi: `app/` ning boshqa hech bir faylida
`TzStatus` ga o'zlashtirish yo'q.

`decide()` §5 jadvalining **sakkizala** qatorini hisoblaydi: §11/2 ning
uchtasi («Ожидает», «Вероятно», «Подтверждено жителями»), §11/3 ning
«Спорно» si, §11/4 ning uchtasi («Частично восстановлено»,
«Восстановлено», «Данные устарели») va §11/7 ning «Проверено
оператором» i.

## §8 — sakkizinchi status va nima uchun u kirish maydoni

«Проверено оператором | оператор внёс источник | отдельная подпись |
да». Tashqi manbaning qabuli `app.reports.tzsensor` da (§11/7), lekin
statusni **baribir** shu funksiya tanlaydi (Т-5): `decide()` ga
`verified` argumenti keladi, `TzStatus` esa o'sha modulda umuman
ko'rinmaydi. `Verified` ning o'zi shu yerda e'lon qilingan — aks holda
`clustering` va `reports` bir-birini import qilib halqa yasardi.

Uchta qaror sabab bilan:

* **Narvon.** `LADDER` da «Проверено оператором» «Подтверждено
  жителями» dan yuqori, ya'ni tashqi manba tasdiqni **ko'taradi**,
  almashtirmaydi. §8 ning talabi — operator ishi *alohida belgilansin*;
  buni status nomi va `Card.verified_by` imzosi bajaradi.
* **§2.3 ning tavqi qo'llanmaydi.** «Статус не поднимается выше
  "Вероятно"» qoidasi kam odamli zonada **odamlarning** hisobiga
  tegishli. Rasmiy manbaning kuchi zonada nechta obunachi borligiga
  bog'liq emas, aks holda chekka mahallada RESning o'z e'loni ham
  «Вероятно» bo'lib qolardi.
* **«Спорно» baribir birinchi.** Datchik odamlarning «у меня свет
  есть» dalilini bekor qila olmaydi: §8 ga ko'ra bahsli holatni
  operator **qarori** yopadi, va bu qaror — signal qabuli emas,
  alohida amal. 👤 `PROGRESS.md` ning «Ochiq savollar» ida.

## §2.2 — veto bu yerda qo'llanadi, sanash `tzdispute.py` da

§2.2: «Если 2 и более человека с разных адресов сообщили о наличии
света — подтверждение **не выдаётся**». Ya'ni qarshi dalil porogni
pasaytirmaydi va hisobga qo'shilmaydi — u **veto**, va shuning uchun
`decide()` da eng birinchi tekshiriladi. Hodisa allaqachon
tasdiqlangan bo'lsa, o'sha veto tasdiqni **qaytarib oladi** va §6.4
bo'yicha tuzatish yuborish majburiyatini tug'diradi.

## Bildirishnoma huquqi shu yerda hal qilinadi

§6.2 ning oxirgi qatori: «Уведомления отправляются **только** на
статус "Подтверждено" и выше. На "Ожидает" и "Вероятно" — никогда.»
Shuning uchun `Card.notifies` — statusning **xossasi**, chaqiruvchining
qarori emas.

Modul **toza**: bazaga, `settings` ga va vaqtga bog'liq emas; matn
faqat i18n kalitlari sifatida qaytariladi (`04` §6).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.clustering.tzcount import Shortfall, ZoneVerdict
from app.clustering.tzdispute import Rebuttals
from app.clustering.tzrestore import Restoration

#: Hujjat bo'limi.
SPEC = "TZ §5"


class TzStatus(StrEnum):
    """§5 jadvalining birinchi ustuni, aynan sakkizta qator."""

    #: «Ожидает подтверждения» — bitta xabar.
    AWAITING = "awaiting"
    #: «Вероятно» — porogning bir qismi.
    LIKELY = "likely"
    #: «Подтверждено жителями» — porog bajarildi.
    CONFIRMED = "confirmed"
    #: «Проверено оператором» — operator tashqi manba kiritdi (§8).
    OPERATOR_VERIFIED = "operator_verified"
    #: «Спорно» — §2.2 ishladi, tasdiqlash qaytarib olindi.
    DISPUTED = "disputed"
    #: «Частично восстановлено» — kvartallarning bir qismi yopildi (§4).
    PARTIALLY_RESTORED = "partially_restored"
    #: «Восстановлено» — hamma kvartallar yopildi.
    RESTORED = "restored"
    #: «Данные устарели» — 3 soat jimlik (§4.2). **Tiklanish emas.**
    STALE = "stale"


#: §5 ning oxirgi ustuni: oddiy bildirishnoma yuboriladigan statuslar.
#: §6.2: «только на статус "Подтверждено" и выше».
NOTIFYING: frozenset[TzStatus] = frozenset(
    {
        TzStatus.CONFIRMED,
        TzStatus.OPERATOR_VERIFIED,
        TzStatus.PARTIALLY_RESTORED,
        TzStatus.RESTORED,
    }
)

#: §6.4 — bu statusga o'tish **tuzatish** («исправление») yuboradi, oddiy
#: bildirishnoma emas: xato tarqatib jim qolish mumkin emas.
CORRECTING: frozenset[TzStatus] = frozenset({TzStatus.DISPUTED})

#: §5: bu statuslarda hech narsa yuborilmaydi.
SILENT: frozenset[TzStatus] = frozenset({TzStatus.AWAITING, TzStatus.LIKELY, TzStatus.STALE})

#: Tasdiqlash narvoni — §2.3 ning «статус не поднимается выше
#: "Вероятно"» iborasi shu tartibga tayanadi. Tiklanish statuslari
#: narvonda emas: ular boshqa o'q.
LADDER: tuple[TzStatus, ...] = (
    TzStatus.AWAITING,
    TzStatus.LIKELY,
    TzStatus.CONFIRMED,
    TzStatus.OPERATOR_VERIFIED,
)

#: §11/2, §11/3, §11/4 va §11/7 da qurilgan statuslar — `decide()`
#: aynan shularni qaytaradi. 178-rundan beri bu **butun** `TzStatus`:
#: sakkizinchisini («Проверено оператором») §11/7 ning tashqi manba
#: qabuli yopdi.
#: Ro'yxat kodda turadi, chunki uni **reyestr vitrinasi** o'qiydi:
#: qaysi statuslar haqiqatan hisoblanishi operator ko'radigan joyda
#: yozilishi kerak, sessiya jurnalida emas.
DECIDED_TODAY: frozenset[TzStatus] = frozenset(
    {
        TzStatus.AWAITING,
        TzStatus.LIKELY,
        TzStatus.CONFIRMED,
        TzStatus.OPERATOR_VERIFIED,
        TzStatus.DISPUTED,
        TzStatus.PARTIALLY_RESTORED,
        TzStatus.RESTORED,
        TzStatus.STALE,
    }
)

#: §5 ning «Что видит пользователь» ustuni — i18n kalitlari.
#:
#: Jadval **so'zma-so'z** yoziladi, `f"tz.status.{status}"` emas: yig'ib
#: yasalgan kalitni katalog skaneri ko'rmaydi va o'lik tarjima jimgina
#: paydo bo'lardi (`tests/test_i18n_key_contract.py` ning 3-qatlami).
STATUS_KEYS: dict[TzStatus, str] = {
    TzStatus.AWAITING: "tz.status.awaiting",
    TzStatus.LIKELY: "tz.status.likely",
    TzStatus.CONFIRMED: "tz.status.confirmed",
    TzStatus.OPERATOR_VERIFIED: "tz.status.operator_verified",
    TzStatus.DISPUTED: "tz.status.disputed",
    TzStatus.PARTIALLY_RESTORED: "tz.status.partially_restored",
    TzStatus.RESTORED: "tz.status.restored",
    TzStatus.STALE: "tz.status.stale",
}

COUNTER_KEY = "tz.card.counter"
CONFIRMED_KEY = "tz.card.confirmed"
SPARSE_KEY = "tz.card.sparse"
#: §5: «Спорно» da foydalanuvchi «подтверждение отозвано» ni ko'radi.
RETRACTED_KEY = "tz.card.retracted"
#: §2.2 ishladi, lekin tasdiq berilmagan edi — qaytarib olinadigan
#: narsa yo'q, hodisa operatorga o'tdi.
DISPUTED_KEY = "tz.card.disputed"
#: §5: «Восстановлено» — «точная длительность».
RESTORED_KEY = "tz.card.restored"
#: §5: «Частично восстановлено» — «карта показывает остаток».
PARTIAL_KEY = "tz.card.partially_restored"
#: §4.2: «свет мог вернуться, но не подтверждено» va **ikkita** son.
STALE_KEY = "tz.card.stale"
#: §5: «Проверено оператором — отдельная подпись». Kalit **argumentsiz**:
#: manbaning o'zi (`Card.verified_by`) tarjima qilinmaydi, u ma'lumot —
#: «РЭС, звонок 12:40» ni lug'atga solib bo'lmaydi. Hisoblagichning
#: sonlari bilan bir xil tartib.
VERIFIED_KEY = "tz.card.verified"
#: §8: operator bahsli holatni ko'rib chiqdi va uzilishni
#: **tasdiqlamadi**. Kalit alohida, chunki bunday hodisa narvonda
#: «Вероятно» ga tushadi va u yerdagi oddiy hisoblagich («1 / 3 —
#: yana 2 ta xabar kutilmoqda») odamga hodisa hamon tasdiqlanish
#: yo'lida ekanini aytardi, holbuki qaror allaqachon qabul qilingan.
REJECTED_KEY = "tz.card.rejected"


def status_key(status: TzStatus) -> str:
    """Statusning i18n kaliti. Qattiq kodlangan matn — bloklovchi defekt."""
    return STATUS_KEYS[status]


def notifies(status: TzStatus) -> bool:
    """§6.2 ning oxirgi qatori: yuborish huquqi statusning xossasi."""
    return status in NOTIFYING


def cap_at_likely(status: TzStatus) -> TzStatus:
    """§2.3: kam odamli zonada narvon «Вероятно» da to'xtaydi."""
    if status not in LADDER:
        return status
    if LADDER.index(status) <= LADDER.index(TzStatus.LIKELY):
        return status
    return TzStatus.LIKELY


@dataclass(frozen=True)
class Verified:
    """§8 — operator kiritgan tashqi manba, `decide()` ning kirishi.

    Tip shu yerda turadi, `app.reports.tzsensor` da emas: statusni
    tanlaydigan modul o'z kirishini o'zi e'lon qiladi, va shunda
    ikkala paket bir-birini import qilmaydi. Qabul tomonida ko'prik
    bor — `tzsensor.verified_fields()`, uni test qulflaydi.

    `reference` bo'sh bo'la olmaydi: §8 «не может создать
    подтверждение по собственному мнению без внешнего источника»
    deydi, ya'ni manbasiz `Verified` — aynan o'sha taqiqlangan narsa,
    faqat tip ichida.
    """

    #: Kanal nomi: `sensor` / `operator` / `feed`.
    source: str
    #: «На основании чего» — kartadagi imzoning o'zi.
    reference: str
    #: Signal qachon kelgan (Т-4: chaqiruvchi beradi).
    at: datetime
    #: «Кто» — `operator` kanalida majburiy, avtomatikda `None`.
    actor: str | None = None

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.reference.strip():
            raise ValueError(f"{SPEC}: §8 — manbasiz tekshiruv bo'lmaydi")


@dataclass(frozen=True)
class Resolution:
    """§8 — operatorning bahsli holat bo'yicha qarori.

    `Verified` tashqi **manba** haqida («что известно»); bu esa
    operatorning **qarori** haqida («что решено»). Ikkalasi bir xil
    emas: manba hodisani ko'tara oladi, qaror esa §2.2 ning vetosini
    yopadi. Tip shu yerda turadi, `app.admin.tzoperator` da emas —
    `Verified` bilan bir xil sabab: statusni tanlaydigan modul o'z
    kirishini o'zi e'lon qiladi va shunda `clustering` bilan `admin`
    bir-birini import qilmaydi. Qabul tomonida ko'prik bor
    (`tzoperator.resolution_fields()`), uni test qulflaydi.

    🔴 **Qaror o'zi ko'rgan dalillarni yopadi, kelajakni emas.**
    `saw` — qaror qabul qilingan lahzada sanoqda turgan qarshi dalil
    akkauntlari. Yangi akkaunt paydo bo'lsa, veto qaytadi
    (`covers()` `False` beradi). Aks holda bitta qaror hodisani §2.2
    dan **abadiy** himoyalab qo'yardi, va to'suvchi uchun eng arzon
    yo'l operatorni bir marta chalg'itish bo'lardi — tasdiqlashni
    soxtalashtirishdan ancha arzon.
    """

    #: Operator uzilishni tasdiqladimi (`False` — rad etdi).
    confirmed: bool
    #: §8: «кто».
    actor: str
    #: §8: «на основании чего».
    reference: str
    #: Qaror qachon qabul qilingan (Т-4: chaqiruvchi beradi).
    at: datetime
    #: Qaror qamragan qarshi dalil akkauntlari.
    saw: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.actor.strip() or not self.reference.strip():
            raise ValueError(f"{SPEC}: §8 — imzosiz qaror bo'lmaydi")

    def covers(self, rebuttals: Rebuttals | None) -> bool:
        """Bugungi qarshi dalillar qarorga sig'adimi."""
        if rebuttals is None:
            return True
        return frozenset(rebuttals.users) <= self.saw


@dataclass(frozen=True)
class Card:
    """§5 — foydalanuvchi ko'radigan karta.

    Karta **hech qachon o'chirilmaydi** (§5 ning oxirgi qatori va
    Т-10): rad etilgan hodisa «Спорно» yoki «Отклонено» bo'ladi,
    lekin ko'rinib turadi. Shuning uchun bu yerda «karta yo'q»
    holati yo'q — birinchi xabardan boshlab har doim karta bor.
    """

    status: TzStatus
    #: Sanalgan guvohlar (§1.1 bo'yicha).
    have: int
    #: Kerakli son — §2.3 dan keyingi haqiqiy porog.
    need: int
    #: Yana nechta kutilmoqda.
    remaining: int
    #: Xaritadagi nuqtalar soni (§5: «число подтвердивших и точек»).
    points: int
    #: §2.3 ishladimi — kartada alohida qator bilan aytiladi.
    sparse: bool
    #: Bildirishnoma yuboriladimi (§6.2).
    notifies: bool
    #: Hisoblagich matnining i18n kaliti va argumentlari.
    text_key: str
    text_args: dict[str, int]
    #: Statusning i18n kaliti.
    status_key: str
    #: Nima yetishmayapti — kartada emas, jurnalda va admin panelida.
    shortfall: Shortfall
    #: §2.2 ishladimi (qarshi dalillar porogi bajarildi).
    disputed: bool = False
    #: Tasdiq **qaytarib olindimi**: §2.2 ishlagan va oldingi status
    #: bildirishnoma yuboradigan status edi.
    retracted: bool = False
    #: §6.4 — tuzatish yuborish majburiyati. Bu opsiya emas: xatoni
    #: tarqatib jim qolish mumkin emas.
    corrects: bool = False
    #: §2.2 — «передаётся оператору» (§8 hal qiladi).
    to_operator: bool = False
    #: Sanalgan qarshi guvohlar. Kartada ko'rsatilmaydi, jurnalda bor.
    against: int = 0
    #: §4 — yopilgan va jami kvartallar. «Частично восстановлено» da
    #: xarita **qoldiqni** ko'rsatadi, ya'ni ikkala son ham kerak.
    closed_blocks: int = 0
    total_blocks: int = 0
    #: §4.2 — jimlik statusga aylandimi.
    stale: bool = False
    #: §8 — tashqi manba kiritilganmi.
    verified: bool = False
    #: §8 — operator bahsli holatni ko'rib chiqdimi. Kartada
    #: operatorning amali **alohida** belgilanadi, ya'ni bu bayroq
    #: «Подтверждено жителями» dan farqni ko'rsatadigan yagona narsa.
    resolved: bool = False
    #: §8 — operator ko'rib chiqdi va **tasdiqlamadi**.
    rejected: bool = False
    #: §5 ning «отдельная подпись» i: manbaning o'zi. **Tarjima
    #: qilinmaydi** — bu ma'lumot, i18n kaliti emas.
    verified_by: str = ""

    @property
    def keys(self) -> tuple[str, ...]:
        """Kartaga chiqadigan barcha i18n kalitlari, tartibda."""
        if self.sparse:
            return (self.status_key, self.text_key, SPARSE_KEY)
        return (self.status_key, self.text_key)


def is_disputed(
    rebuttals: Rebuttals | None,
    previous: TzStatus | None,
) -> bool:
    """§2.2 ning veto sharti, va uning **yopishqoqligi**.

    🔴 Qaror sabab bilan. Bir marta «Спорно» ga tushgan hodisa qarshi
    dalillar §2.1 oynasidan chiqib ketgani uchun **o'z-o'zidan**
    tasdiqlangan holatga qaytmaydi. Oyna sirpanuvchi, ya'ni qaytish
    muqarrar bo'lardi: to'suvchi ikkita xabar yuboradi, hodisa
    «Спорно» ga tushadi va «tasdiqlash qaytarib olindi» ketadi,
    yigirma daqiqadan keyin hodisa qayta tasdiqlanadi va **yana**
    bildirishnoma ketadi — bir kechada bir necha marta. §8 ga ko'ra
    bahsli holatni yopadigan yagona kuch — operator, shuning uchun
    avtomatik qaytish yo'q.

    Operatorning qarori — `decide()` ning `resolution` argumenti
    (`app.admin.tzoperator`, 181-run). Bu funksiya uni **bilmaydi**:
    u faqat vetoning o'zini o'lchaydi, qarorni esa `decide()`
    qo'llaydi. Sabab oddiy — veto va uni yopadigan kuch bir xil
    savolga javob bermaydi, va ularni bitta funksiyada birlashtirish
    «qaror bormi» ni «dalil bormi» bilan aralashtirardi.
    """
    if previous is TzStatus.DISPUTED:
        return True
    return rebuttals is not None and rebuttals.vetoed


def is_stale(restoration: Restoration | None, previous: TzStatus | None) -> bool:
    """§4.2 ning sharti va uning **chegarasi**.

    «Если сообщений нет дольше 3 часов — статус "Данные устарели", а
    не "Восстановлено".» Jimlikning o'zini `tzrestore.is_stale()`
    o'lchaydi; bu yerda hal qilinadigan narsa — u **statusga**
    aylanadimi.

    🔴 Qaror: tasdiqlanmagan hodisa «Данные устарели» ga tushmaydi.
    §2.1 oynasi sirpanuvchi, ya'ni uch soatdan keyin bitta xabarli
    hodisa baribir «Ожидает» ga qaytadi va uni «свет мог вернуться»
    deb e'lon qilish odam ko'rmagan uzilishni bo'lgan deb aytish
    bo'lardi. Shart shuning uchun ikkitadan biri: kvartallarning bir
    qismi allaqachon yopilgan, yoki oldingi status bildirishnoma
    yuboradigan status edi.
    """
    if restoration is None or not restoration.stale:
        return False
    if restoration.any_closed:
        return True
    return previous is not None and notifies(previous)


def decide(
    verdict: ZoneVerdict,
    *,
    rebuttals: Rebuttals | None = None,
    previous: TzStatus | None = None,
    restoration: Restoration | None = None,
    verified: Verified | None = None,
    resolution: Resolution | None = None,
) -> Card:
    """Т-5 ning yagona joyi: zona verdikti → status va karta.

    Qaror tartibi §5 jadvalining tartibi, lekin §2.2 undan **oldin**
    turadi — «подтверждение не выдаётся» degani veto:

    * §2.2 ishladi (yoki avval ishlagan edi) → «Спорно»;
    * hamma kvartal yopildi (§4) → «Восстановлено»;
    * jimlik uch soatdan oshdi (§4.2) → «Данные устарели»;
    * kvartallarning bir qismi yopildi → «Частично восстановлено»;
    * §8 ning tashqi manbasi bor → «Проверено оператором»;
    * porog bajarildi va zona kam odamli emas → «Подтверждено жителями»;
    * porog bajarildi, lekin §2.3 ishladi → «Вероятно» (§2.3 ning
      «не поднимается выше» qoidasi);
    * bitta guvoh → «Ожидает подтверждения»;
    * qolganida → «Вероятно» («часть порога»).

    🔴 **Nima uchun «Спорно» tiklanishdan oldin.** §8 ga ko'ra bahsli
    holatni faqat operator yopadi; tiklanish dalili uni avtomatik
    yopa olsa, §2.2 ning butun ma'nosi yo'qolardi — to'suvchi
    «свет вернулся» ni bosib hodisani «tiklandi» deb yopib qo'yardi.

    🔴 **Nima uchun jimlik qisman tiklanishdan oldin.** Uch soat
    jimlikdan keyin biz **qolgan** kvartallar haqida hech narsa
    bilmaymiz, «Частично восстановлено» esa aynan ular haqida da'vo.
    Yopilgan kvartallarning bildirishnomasi o'sha lahzada allaqachon
    ketgan, ya'ni bu pasayish hech narsani qaytarib olmaydi.

    Guvoh umuman yo'q holati ham «Ожидает» beradi: xabar bor, lekin
    §1.1 dan o'tmagan. Т-8 bo'yicha foydalanuvchiga himoya ishlagani
    aytilmaydi — u oddiy hisoblagichni ko'radi.

    `previous` — jurnalga yozilgan oldingi status. U ikki narsa uchun
    kerak: vetoning yopishqoqligi (`is_disputed`) va §6.4 — tuzatish
    faqat **bildirishnoma ketishi mumkin bo'lgan** statusdan keyin
    majburiy.

    `resolution` — §8 ning operatori bergan qaror. U vetoni yopadigan
    **yagona** kuch (`is_disputed` ning docstringi), lekin faqat o'zi
    ko'rgan dalillar doirasida (`Resolution.covers`).

    🔴 **Rad etish narvonni «Вероятно» da to'xtatadi.** §5 jadvalida
    «Отклонено» degan status yo'q va Т-5 to'qqizinchisini o'ylab
    topishni taqiqlaydi. Vetoni yopib qo'yib narvonni erkin
    qoldirish esa hodisani darhol «Подтверждено жителями» ga
    qaytarardi — ya'ni operatorning «tasdiqlamadim» degan qarori
    tasdiqlashga aylanardi. «Вероятно» rostgo'y: xabarlar bor,
    tasdiq yo'q, va §6.2 ga ko'ra bu statusdan bildirishnoma
    ketmaydi. Tavqning o'zi §2.3 uchun yozilgan `cap_at_likely()` —
    ikkinchi mexanizm yozilmadi.
    """
    resolved = resolution is not None and resolution.covers(rebuttals)
    confirmed_by_operator = resolved and resolution is not None and resolution.confirmed
    rejected = resolved and resolution is not None and not resolution.confirmed
    disputed = is_disputed(rebuttals, previous) and not resolved
    stale = is_stale(restoration, previous)

    if disputed:
        status = TzStatus.DISPUTED
    elif restoration is not None and restoration.all_closed:
        status = TzStatus.RESTORED
    elif stale:
        status = TzStatus.STALE
    elif restoration is not None and restoration.any_closed:
        status = TzStatus.PARTIALLY_RESTORED
    elif verified is not None or confirmed_by_operator:
        status = TzStatus.OPERATOR_VERIFIED
    elif verdict.reached:
        status = TzStatus.CONFIRMED
    elif verdict.have <= 1:
        status = TzStatus.AWAITING
    else:
        status = TzStatus.LIKELY

    # §2.3 ning tavqi **odamlarning** hisobiga tegishli: «Если активных
    # пользователей в зоне меньше порога». Rasmiy manba zonadagi
    # obunachilar soniga bog'liq emas, shuning uchun tekshirilgan
    # hodisa tavqdan o'tmaydi — aks holda chekka mahallada RESning o'z
    # e'loni ham «Вероятно» bo'lib qolardi.
    if verdict.sparse and verified is None and not confirmed_by_operator:
        status = cap_at_likely(status)

    # §8 ning rad etishi: narvon «Вероятно» dan yuqoriga chiqmaydi.
    # Tiklanish va jimlik statuslari bundan mustasno — ular narvonda
    # emas (`LADDER`), va operatorning «uzilish tasdiqlanmadi» degan
    # qarori svet qaytgani haqidagi keyingi faktni bekor qilmaydi.
    if rejected:
        status = cap_at_likely(status)

    against = rebuttals.people if rebuttals is not None else 0
    # §6.4: tasdiq qaytarib olindi, ya'ni oldin bildirishnoma ketishi
    # mumkin edi. `previous is None` — jurnalda oldingi status yo'q,
    # demak hech narsa yuborilmagan.
    #
    # Rad etish ham xuddi shu majburiyatni tug'diradi va aynan shu
    # sababdan `tzoutage.Cause.OPERATOR` mavjud («operator tekshirdi
    # va tasdiqlamadi»): bildirishnoma ketgan, endi u noto'g'ri.
    retracted = (
        previous is not None
        and notifies(previous)
        and (status is TzStatus.DISPUTED or (rejected and not notifies(status)))
    )

    if status is TzStatus.DISPUTED:
        text_key = RETRACTED_KEY if retracted else DISPUTED_KEY
        text_args = {"against": against}
    elif status is TzStatus.RESTORED and restoration is not None:
        text_key = RESTORED_KEY
        text_args = {
            "hours": restoration.duration.hours,
            "minutes": restoration.duration.minutes,
        }
    elif status is TzStatus.STALE and restoration is not None:
        # §4.2: davomiylik **ikkita** son bilan va «неточно» pometasi
        # bilan yoziladi. Kartada ham shunday — bitta o'rtacha son
        # ma'lumotda yo'q aniqlikni ko'rsatardi.
        text_args = {
            "low": restoration.duration.low_hours,
            "high": restoration.duration.high_hours,
        }
        text_key = STALE_KEY
    elif status is TzStatus.PARTIALLY_RESTORED and restoration is not None:
        text_key = PARTIAL_KEY
        text_args = {
            "closed": restoration.closed,
            "total": restoration.total,
            "remaining": restoration.remaining,
        }
    elif status is TzStatus.OPERATOR_VERIFIED:
        # §5: «отдельная подпись», ya'ni bu yerda hisoblagich emas.
        # Odamlarning soni kartada baribir qoladi (`Card.have`), lekin
        # imzo uni «подтвердили жители» deb o'qishga imkon bermaydi.
        text_key = VERIFIED_KEY
        text_args = {}
    elif rejected:
        # §8: operatorning amali kartada **alohida** belgilanadi.
        # Hisoblagich bu yerda ham ko'rsatilmaydi — qaror qabul
        # qilingan, ya'ni «yana ikkita xabar kutilmoqda» yolg'on.
        text_key = REJECTED_KEY
        text_args = {}
    elif status is TzStatus.CONFIRMED:
        text_key = CONFIRMED_KEY
        text_args = {"have": verdict.have, "points": verdict.points}
    else:
        text_key = COUNTER_KEY
        text_args = {
            "have": verdict.have,
            "need": verdict.need,
            "remaining": verdict.remaining,
        }

    return Card(
        status=status,
        have=verdict.have,
        need=verdict.need,
        remaining=verdict.remaining,
        points=verdict.points,
        sparse=verdict.sparse,
        notifies=notifies(status),
        text_key=text_key,
        text_args=text_args,
        status_key=status_key(status),
        shortfall=verdict.shortfall,
        disputed=status is TzStatus.DISPUTED,
        retracted=retracted,
        corrects=retracted,
        to_operator=status is TzStatus.DISPUTED,
        against=against,
        closed_blocks=restoration.closed if restoration is not None else 0,
        total_blocks=restoration.total if restoration is not None else 0,
        stale=status is TzStatus.STALE,
        verified=status is TzStatus.OPERATOR_VERIFIED,
        resolved=resolved,
        rejected=rejected,
        # Imzo faqat status haqiqatan «Проверено оператором» bo'lganda
        # yoki operator rad etganda qo'yiladi: «Спорно» ga tushgan
        # hodisada tashqi manbaning imzosi kartada turishi uni
        # tasdiqlangandek ko'rsatardi. Rad etishda imzo aksincha —
        # §8 «на основании чего» ni aynan shu holatda talab qiladi.
        verified_by=_signature(status, verified, resolution, rejected),
    )


def _signature(
    status: TzStatus,
    verified: Verified | None,
    resolution: Resolution | None,
    rejected: bool,
) -> str:
    """Kartadagi «отдельная подпись» ning matni. Tarjima qilinmaydi."""
    if rejected and resolution is not None:
        return resolution.reference
    if status is not TzStatus.OPERATOR_VERIFIED:
        return ""
    if verified is not None:
        return verified.reference
    if resolution is not None:
        return resolution.reference
    return ""
