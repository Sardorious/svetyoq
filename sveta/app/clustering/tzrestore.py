"""TZ §4, §4.1, §4.2 — tiklanish, opros va «Данные устарели».

`TZ_Podtverzhdenie_i_uvedomleniya.md` §11 navbatining **to'rtinchi** bandi:
«Восстановление, опрос — самая недоделанная часть текущего продукта».
Bu modul uning **hisob** qismi; statusning o'zi Т-5 ga ko'ra baribir
`app/clustering/tzstatus.py` ning `decide()` sida tanlanadi, boshqa hech
qayerda. Bu yerda `TzStatus` umuman import qilinmaydi.

## Nima uchun kvartal, hodisa emas

В-1: «Считается **по кварталу (r9)**, не по всему инциденту. Свет
возвращают по частям.» Shuning uchun modulning asosiy birligi —
`close_block()`, va butun hodisa `evaluate_restoration()` da
kvartallarning yig'indisi sifatida chiqadi. Bitta kvartal yopilishi
qolganlariga hech narsa qilmaydi.

## Nima uchun sanash yana `tzcount` bilan

В-2: «Нужно **2 человека с разных адресов**». «Turli manzil» — bu §1.1
ning o'sha yaqinlashuvi (turli akkaunt, turli r11 katagi yoki
ko'rsatilgan manzil, ustma-ust tushmagan uy katagi). Shuning uchun bu
yerda ham o'z sanash sikli yozilmaydi: `tzcount.count_witnesses()`
chaqiriladi. Aks holda ТС-202 va ТС-203 ning **uchinchi** simmetrik
ko'rinishi (bitta odam uchta nuqtadan «свет вернулся» bosadi) jimgina
ishlab ketardi va bu safar zarari kattaroq: uzilishni **yopish**
uzilishni yaratishdan arzon bo'lardi.

Oyna ham o'sha — kvartalning §2.1 oynasi. 🔴 Qaror: TZ tiklanish uchun
alohida oyna bermaydi, ya'ni tanlov ikkitadan biri edi — oynasiz
(hodisa boshidan hamma «свет вернулся» yig'iladi) yoki §2.1 niki.
Oynasiz variant rad etildi: olti soatlik uzilishda ertalab bosilgan
tugma kechqurungi tugma bilan qo'shilib kvartalni yopardi, holbuki
ular haqida gap ketayotgan **ikki xil** tiklanish. 👤 §7 ga
`tz.restore.window_min` qo'shilishi kerakmi — ochiq savol.

## 🔴 Javob bermagan odam — nol emas, umuman yo'q

В-6: «Доля считается **от ответивших на опрос**, а не от всех
сообщавших», §4.1: «нет ответа → ничего». Shundan kelib chiqadigan
qirra TZ da yozilmagan: **hech kim javob bermasa** ulush `0/0`.

Uni `1.0` deb o'qish В-2 ning ikkinchi shartini bo'sh joyga
aylantirardi (ikki tugma bosilishi bilan kvartal yopilardi), `0.0`
deb o'qish esa opros ishlamagan zonada kvartalni **hech qachon**
yopmasdi. Tanlangan variant — ikkinchisi, lekin sababi boshqa:
javobsiz qolgan uzilishning to'g'ri yakuni «Восстановлено» emas,
§4.2 ning «Данные устарели» i. Ya'ni bu yo'l berkitilgan emas, u
boshqa eshikka olib boradi va o'sha eshik TZ da bor.

## 🔴 Ulush soatning **to'lgan** soniga qarab pasayadi

В-5: «Требуемая доля снижается с ростом длительности». Pasayish
uzluksiz funksiya bilan ham yozilishi mumkin edi, lekin u holda
porog har daqiqada o'zgarardi va bitta xabar to'plami ikki qo'shni
qayta hisoblashda ikki xil verdikt berardi. To'lgan soat —
odamga aytiladigan va Т-3 bo'yicha takrorlanadigan yagona shakl.

## Т-3: opros namunasi **tasodifiy, lekin takrorlanadigan**

§4.1 «случайную четверть» talab qiladi, Т-3 esa 90 kunlik tarixni
qayta hisoblab **o'sha natijani** olishni. Ikkalasi faqat bitta
usulda birga bajariladi: tanlov `blake2b(incident|wave|user)` dan
olinadi. Python ning o'rnatilgan `hash()` i ishlatilmaydi — u har
protsessda tasodifiylanadi (`05` §3.1 dagi bilan bir xil sabab).

To'lqin raqami xeshga **ataylab** kiradi: aks holda birinchi
to'lqinda tanlangan chorak to'rtala to'lqinda ham o'sha bo'lardi va
§4.1 ning «случайную четверть» i amalda «doimiy chorak» ga aylanardi
— o'sha odamlar to'rt marta so'raladi, qolganlar hech qachon.

§4.1 ning oxirgi qatori: «Состав выборки нигде не показывать» —
shuning uchun tanlov natijasi kartaga ham, API ga ham chiqmaydi;
`Survey` faqat botning yuborish quvuri uchun.

## Т-1 va Т-4

§7 ning birorta soni bu faylda literal emas; funksiya ichida `0` va
`1` dan boshqa son yo'q. Soat argumentda (`now`). Ikkalasi ham
`tests/test_tz_restore.py` da `ast` bilan qulflangan.

Modul **toza**: bazaga, `settings` ga va vaqtga bog'liq emas.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum

from app.clustering.tzcount import (
    Drop,
    Evidence,
    Level,
    count_witnesses,
    window_min,
)
from app.core.tzconfig import TzParams

#: Hujjat bo'limi. Reyestrlar vitrinasi (`app.admin.registries`) shuni o'qiydi.
SPEC = "TZ §4"

#: §4 ning birligi — kvartal (В-1). Doimiy: tiklanish uy darajasida ham,
#: mahalla darajasida ham hisoblanmaydi.
RESTORE_LEVEL = Level.BLOCK

#: `blake2b` digestining uzunligi (bayt) va undan chiqadigan butun
#: sonlar fazosi. Bu **implementatsiya geometriyasi**, §7 sozlamasi
#: emas: kattaroq digest tanlovni aniqroq qilmaydi, kichikrog'i esa
#: `share` ni qadamli qilardi.
SAMPLE_DIGEST_BYTES = 16
SAMPLE_SPACE = float(1 << (8 * SAMPLE_DIGEST_BYTES))

#: Kartaga chiqadigan davomiylikni soat va daqiqaga bo'lish uchun.
#: Vaqtning o'lchovi, §7 sozlamasi emas.
MINUTES_PER_HOUR = 60


@dataclass(frozen=True)
class Rule:
    """§4 ning bitta qoidasi va u qurilganmi.

    Ro'yxat kodda turadi, chunki uni `app.admin.registries` o'qiydi:
    §4 ning qaysi qismi **hisoblanadi** va qaysi qismi hali kanalsiz
    turibdi — operator ko'radigan joyda yozilishi kerak, sessiya
    jurnalida emas.
    """

    code: str
    note: str
    built: bool


RULES: tuple[Rule, ...] = (
    Rule(code="V-1", note="Hisob kvartal (r9) bo'yicha, butun hodisa bo'yicha emas", built=True),
    Rule(code="V-2", note="Turli manzildagi 2 odam VA javob berganlarning ulushi", built=True),
    Rule(code="V-3", note="Bitta odam uzilishni yopmaydi", built=True),
    Rule(
        code="V-4",
        note="«Svet qaytdi» tugmasi: nuqtani olib tashlaydi va guvohlik sanaladi",
        # Hisobning ikkala yarmi ham bor (`withdraw_points` va
        # `close_block`), lekin **tugmaning o'zi** botda yo'q: aiogram
        # qatlami §11 navbatining 5–6-bandlarida.
        built=False,
    ),
    Rule(code="V-5", note="Talab qilinadigan ulush davomiylik bilan pasayadi", built=True),
    Rule(code="V-6", note="Ulush javob berganlardan, xabar berganlardan emas", built=True),
    Rule(
        code="V-7",
        note="Datchik yoki rasmiy manba kvartalni darhol yopadi",
        # Yopish qoidasi bor (`OfficialSource`), datchikni **qabul
        # qilish** yo'q — §11 navbatining 7-bandi.
        built=False,
    ),
    Rule(code="V-8", note="Erta kelgan tiklanish xabari operatorga, avtoyopish yo'q", built=True),
    Rule(
        code="4.1",
        note="Opros: to'rt to'lqin, tasodifiy chorak, javobsizlik — hech narsa",
        # To'lqinlar hisoblanadi (`plan_survey`), lekin ularni
        # **yuboradigan** fon vazifasi va bot dialogi yo'q.
        built=False,
    ),
    Rule(code="4.2", note="Uch soat jimlik → «Ma'lumot eskirgan», ikkita son", built=True),
)


class Answer(StrEnum):
    """§4.1 ning ikkita javobi.

    Uchinchi qiymat (`NO_ANSWER`) **ataylab yo'q**: §4.1 «нет ответа →
    ничего» deydi, ya'ni javobsizlik qiymat emas, qator yo'qligi.
    Uni enum ga qo'shish В-6 ning maxrajiga (`ответившие`) jimgina
    kirib ketardi.
    """

    #: «свет уже есть» → tiklanish guvohligi.
    YES = "yes"
    #: «нет» → uzilish davom etadi, muddat uzaytiriladi.
    NO = "no"


class Blocker(StrEnum):
    """Kvartal nega yopilmadi. Jurnal va operator uchun; kartada yo'q."""

    #: Hech narsa — kvartal yopildi.
    NONE = "none"
    #: В-3: odam yetarli emas («Один человек аварию не закрывает»).
    PEOPLE = "people"
    #: В-2/В-6: javob berganlarning ulushi yetarli emas.
    SHARE = "share"
    #: Oprosga **hech kim** javob bermadi — ulushning maxraji nol.
    #: Bu holatning to'g'ri yakuni §4.2 («Данные устарели»).
    NO_ANSWERS = "no_answers"
    #: В-8: bu zonadagi eng qisqa uzilishlardan ham erta keldi.
    EARLY = "early"


@dataclass(frozen=True)
class OfficialSource:
    """В-7 — datchik yoki rasmiy manba.

    `reference` **bo'sh bo'la olmaydi**: §8 ga ko'ra operator o'z
    fikri bilan hech narsa yarata olmaydi, u faqat tashqi manbani
    kiritadi. Manbasiz «rasmiy yopish» aynan o'sha taqiqlangan narsa
    bo'lardi, faqat boshqa nom ostida.
    """

    kind: str
    reference: str

    def __post_init__(self) -> None:
        if not self.kind.strip() or not self.reference.strip():
            raise ValueError(f"{SPEC}: V-7 manbasi bo'sh bo'la olmaydi")


@dataclass(frozen=True)
class SurveyAnswer:
    """§4.1 ning bitta javobi."""

    user_id: str
    at: datetime
    answer: Answer
    #: Qaysi to'lqinning javobi (daqiqada). Faqat kuzatuv uchun.
    wave_min: int | None = None


@dataclass(frozen=True)
class SurveyWave:
    """§4.1 ning bitta to'lqini: qachon va kimdan so'raladi."""

    #: Hodisa boshidan o'tgan daqiqa (§7 — `tz.survey.waves_min`).
    minutes: int
    #: So'rov yuboriladigan lahza.
    at: datetime
    #: Tanlangan akkauntlar, kirish tartibidan qat'i nazar saralangan.
    #: **Sirtga chiqarilmaydi** (§4.1 ning oxirgi qatori).
    users: tuple[str, ...]


@dataclass(frozen=True)
class Answers:
    """В-6 ning hisobi: ulush **javob berganlardan** olinadi."""

    #: So'rov yuborilganlar soni.
    asked: int
    #: Javob berganlar soni — ulushning maxraji.
    answered: int
    #: «свет уже есть» deganlar.
    yes: int
    #: «нет» deganlar — uzilish davom etadi.
    no: int

    @property
    def share(self) -> float | None:
        """«да» larning ulushi. `None` — hech kim javob bermadi.

        `0.0` emas, aynan `None`: nol ulush «odamlar yo'q dedi»
        degani, javobsizlik esa «bilmaymiz». Ikkalasini bitta songa
        yig'ish §4.2 ni ko'rinmas qilardi.
        """
        if self.answered <= 0:
            return None
        return self.yes / self.answered

    @property
    def silent(self) -> int:
        """So'ralgan, lekin javob bermaganlar (§4.1: «ничего»)."""
        return max(self.asked - self.answered, 0)


@dataclass(frozen=True)
class Duration:
    """§4.2 — uzilish davomiyligi **ikkita son** bilan.

    «Длительность записывается двумя числами: "не меньше 2 ч, не
    больше 5 ч" и пометкой "неточно"». Aniq yopilgan uzilishda
    ikkala son teng va `exact` rost.
    """

    low_h: float
    high_h: float
    exact: bool

    def __post_init__(self) -> None:
        if self.high_h < self.low_h:
            raise ValueError(f"{SPEC}: davomiylikning yuqori cheki pastkisidan kichik")

    @property
    def hours(self) -> int:
        """Aniq davomiylikning to'lgan soatlari (§5: «точная длительность»)."""
        return int(self.low_h)

    @property
    def minutes(self) -> int:
        """Soatdan qolgan daqiqalar. Kartada soat bilan birga turadi."""
        return round((self.low_h - self.hours) * MINUTES_PER_HOUR)

    @property
    def low_hours(self) -> int:
        """§4.2 ning birinchi soni — «не меньше N ч» (pastga yaxlitlanadi)."""
        return math.floor(self.low_h)

    @property
    def high_hours(self) -> int:
        """§4.2 ning ikkinchi soni — «не больше N ч» (tepaga yaxlitlanadi).

        Yaxlitlash **tashqariga**: ikkala son ham noaniqlikni
        toraytirmasligi kerak, aks holda kartadagi oraliq haqiqiy
        oraliqdan kichik bo'lib qolardi.
        """
        return math.ceil(self.high_h)


@dataclass(frozen=True)
class BlockClosure:
    """В-1 — bitta kvartalning tiklanish holati."""

    cell: str
    #: §1.1 bo'yicha sanalgan tiklanish guvohlari.
    people: int
    #: В-2 ning birinchi sharti (`tz.restore.users`).
    need: int
    #: В-6 ning ulushi; `None` — javob yo'q.
    share: float | None
    #: В-5 dan keyingi haqiqiy talab.
    need_share: float
    #: Kvartal yopildimi.
    closed: bool
    #: В-7 bilan yopildimi (rasmiy manba).
    official: bool
    #: В-8: erta kelgan xabar — avtoyopish yo'q, operatorga.
    early: bool
    #: Operator qaraydigan holatmi (В-8 yoki qarama-qarshilik).
    to_operator: bool
    blocker: Blocker
    #: Sanoqqa kirgan akkauntlar (Т-3 determinizmi va §6.3 uchun).
    users: tuple[str, ...]
    drops: dict[Drop, int] = field(default_factory=dict)

    @property
    def remaining(self) -> int:
        """В-2 uchun yana nechta odam kerak."""
        return max(self.need - self.people, 0)


@dataclass(frozen=True)
class Restoration:
    """Butun hodisaning tiklanish kesimi (§5 ning ikkita qatori)."""

    blocks: tuple[BlockClosure, ...]
    #: Hodisa qamragan kvartallar soni.
    total: int
    #: Yopilgan kvartallar.
    closed: int
    #: §4.2 — jimlik `tz.stale_after_h` dan uzoq davom etdimi.
    stale: bool
    duration: Duration

    @property
    def all_closed(self) -> bool:
        """Hamma kvartal yopildi → «Восстановлено» (§5)."""
        return self.total > 0 and self.closed == self.total

    @property
    def any_closed(self) -> bool:
        """Bir qismi yopildi → «Частично восстановлено» (§5)."""
        return self.closed > 0

    @property
    def remaining(self) -> int:
        """Xarita ko'rsatadigan qoldiq (§5: «карта показывает остаток»)."""
        return max(self.total - self.closed, 0)

    @property
    def announced(self) -> tuple[BlockClosure, ...]:
        """§5: «да, **по кварталам**» — xabar chiqadigan kvartallar.

        🔴 185-run. `notifies` ning qorovuli (184-run) bu yerni
        **himoya qilmaydi**, va aynan shuning uchun filtr nomli
        bo'lishi kerak edi. §6.2 ning yuborish huquqi hodisaning
        **statusidan** olinadi, status esa yopilmagan kvartalda ham
        bemalol «Подтверждено жителями» bo'ladi — ya'ni `notifies`
        rost. Shu paytda `blocks` dan to'g'ridan-to'g'ri xabar yasagan
        chaqiruvchi svet qaytmagan kvartalga «Свет вернулся»
        yuborardi va birorta qorovul buni ko'rmasdi: karta to'g'ri,
        huquq to'g'ri, kvartal esa noto'g'ri.

        Ro'yxatni har chaqiruv joyida qaytadan filtrlash — o'sha
        xatoni ko'chirishning eng oson yo'li (ТС-209). Shuning uchun u
        `Restoration` ning o'zida turadi va tartibi `blocks` niki
        (Т-3).
        """
        return tuple(block for block in self.blocks if block.closed)

    @property
    def to_operator(self) -> tuple[str, ...]:
        """В-8 bo'yicha operatorga tushgan kvartallar."""
        return tuple(block.cell for block in self.blocks if block.to_operator)


@dataclass(frozen=True)
class DurationStats:
    """§4.2 ning oxirgi xatboshi — statistika uchun.

    «Такие аварии остаются в статистике длительности… Рядом со
    средней длительностью всегда публикуется доля таких аварий.»

    🔴 O'rtacha **ikkita** son bilan qaytariladi. Aniq bo'lmagan
    uzilishning o'rtasini olish (`(low+high)/2`) bitta chiroyli son
    berardi, lekin u ma'lumotda yo'q aniqlikni o'ylab topardi — va
    §4.2 ning butun mazmuni aynan shu aniqlikning yo'qligini
    ko'rsatishda.
    """

    count: int
    #: Aniq bo'lmagan («неточно») uzilishlar soni.
    imprecise: int
    average_low_h: float
    average_high_h: float

    @property
    def imprecise_share(self) -> float:
        """§4.2: o'rtacha bilan **birga** chop etiladigan ulush."""
        if self.count <= 0:
            return 0.0
        return self.imprecise / self.count


# --------------------------------------------------------------------------
# §4.1 — opros
# --------------------------------------------------------------------------


def _unit(incident_id: str, wave_min: int, user_id: str) -> float:
    """Deterministik `[0, 1)` — Т-3 ning namuna uchun talabi."""
    raw = f"{incident_id}|{wave_min}|{user_id}".encode()
    digest = hashlib.blake2b(raw, digest_size=SAMPLE_DIGEST_BYTES).digest()
    return int.from_bytes(digest, "big") / SAMPLE_SPACE


def is_sampled(incident_id: str, wave_min: int, user_id: str, *, share: float) -> bool:
    """Shu akkaunt shu to'lqinda so'raladimi (§4.1 ning «случайной четверти»)."""
    return _unit(incident_id, wave_min, user_id) < share


def plan_survey(
    incident_id: str,
    reporters: Iterable[str],
    *,
    started_at: datetime,
    params: TzParams,
) -> tuple[SurveyWave, ...]:
    """§4.1: to'rtta to'lqin, har birida **o'z** choragi.

    `reporters` — shu hodisada xabar bergan akkauntlar. Natija
    determinstik va tartibi kirishga bog'liq emas (Т-3).

    Funksiya vaqt bo'yicha hech narsa filtrlamaydi: to'lqinning
    `at` i hisoblanadi, uni **kim yuborishi** esa quvurning ishi
    (`05` §8 ning fon vazifasi). Shu ajratish tufayli tarixni qayta
    hisoblash ham shu funksiyani chaqirishning o'zidan iborat.
    """
    people = sorted(set(reporters))
    waves: list[SurveyWave] = []
    for minutes in params.survey_waves_min:
        chosen = tuple(
            user
            for user in people
            if is_sampled(incident_id, minutes, user, share=params.survey_share)
        )
        waves.append(
            SurveyWave(
                minutes=minutes,
                at=started_at + timedelta(minutes=minutes),
                users=chosen,
            )
        )
    return tuple(waves)


def tally_answers(answers: Iterable[SurveyAnswer], *, asked: int) -> Answers:
    """§4.1 + В-6: javoblarni sanaydi.

    Bir akkauntning bir necha javobi bo'lsa — **oxirgisi** qoladi:
    to'lqinlar ketma-ket keladi va «нет» dan keyingi «да» tiklanish
    haqidagi yangi ma'lumot. Т-7 («повторная отправка того же
    сообщения не создаёт второго свидетельства») shu yerda ham
    bajariladi: odam bir marta sanaladi.
    """
    latest: dict[str, SurveyAnswer] = {}
    for item in sorted(answers, key=lambda a: (a.at, a.user_id)):
        latest[item.user_id] = item
    yes = sum(1 for item in latest.values() if item.answer is Answer.YES)
    no = sum(1 for item in latest.values() if item.answer is Answer.NO)
    return Answers(asked=max(asked, len(latest)), answered=len(latest), yes=yes, no=no)


# --------------------------------------------------------------------------
# §4 — В-5, В-8 va kvartalni yopish
# --------------------------------------------------------------------------


def elapsed_hours(started_at: datetime, now: datetime) -> int:
    """Uzilishning **to'lgan** soatlari. Manfiy bo'lmaydi."""
    return max((now - started_at) // timedelta(hours=1), 0)


def required_share(hours: int, params: TzParams) -> float:
    """В-5: «Требуемая доля снижается с ростом длительности».

    «у людей садятся телефоны» — ya'ni uzoq uzilishda javob berish
    qobiliyati kamayadi, porog esa o'sha bo'lib qolsa kvartal
    hech qachon yopilmaydi. Pasayish `share_floor` da to'xtaydi.
    """
    decayed = params.restore_answered_share - params.restore_share_decay_per_hour * hours
    return max(decayed, params.restore_share_floor)


def early_threshold(history: Sequence[timedelta], params: TzParams) -> timedelta | None:
    """В-8: shu zonadagi eng qisqa uzilishlarning chegarasi.

    «Сообщение о восстановлении раньше, чем 5% самых коротких аварий
    в этой зоне, — оператору.» Persentil **eng yaqin rang** usuli
    bilan olinadi: `rank = ceil(share * n)`, natija — `rank`-o'rindagi
    uzilish.

    Tarix bo'sh bo'lsa — `None`, ya'ni qoida **ishlamaydi**. Bu ham
    qaror: bo'sh tarixda chegarani o'ylab topish (masalan «yarim
    soat») §7 ning «koddan sukut qiymati qo'yilmaydi» talabini
    buzardi, va yangi mintaqada har bir tiklanish operatorga
    tushardi. Qoidaning ishlagani `BlockClosure.early` da ko'rinadi.
    """
    ordered = sorted(history)
    if not ordered:
        return None
    rank = max(math.ceil(params.restore_early_percentile * len(ordered)), 1)
    return ordered[rank - 1]


def close_block(
    cell: str,
    evidence: Iterable[Evidence],
    *,
    now: datetime,
    started_at: datetime,
    params: TzParams,
    answers: Answers | None = None,
    official: OfficialSource | None = None,
    history: Sequence[timedelta] = (),
) -> BlockClosure:
    """В-1…В-8: bitta kvartal yopiladimi.

    `evidence` — shu kvartaldagi **tiklanish** dalillari: «Свет
    вернулся» tugmasi (В-4) va oprosning «да» javoblari (§4.1)
    birgalikda. Ikkalasi bir xil turda keladi, chunki В-2 ikkalasidan
    ham «разные адреса» ni talab qiladi; ularni ajratish faqat
    hisobning yarmiga §1.1 ni qo'llash imkonini berardi.

    Tartib TZ ning tartibi: avval В-7 (rasmiy manba darhol yopadi),
    keyin В-8 (erta xabar — operatorga), keyin В-2/В-3 (odam), keyin
    В-6 (ulush).
    """
    counted = count_witnesses(
        evidence,
        now=now,
        window_min=window_min(RESTORE_LEVEL, params),
    )
    hours = elapsed_hours(started_at, now)
    need_share = required_share(hours, params)
    tally = answers if answers is not None else Answers(asked=0, answered=0, yes=0, no=0)
    share = tally.share

    if official is not None:
        return BlockClosure(
            cell=cell,
            people=counted.people,
            need=params.restore_users,
            share=share,
            need_share=need_share,
            closed=True,
            official=True,
            early=False,
            to_operator=False,
            blocker=Blocker.NONE,
            users=counted.users,
            drops=counted.drops,
        )

    threshold = early_threshold(history, params)
    early = threshold is not None and now - started_at < threshold

    if early:
        blocker = Blocker.EARLY
    elif counted.people < params.restore_users:
        blocker = Blocker.PEOPLE
    elif share is None:
        blocker = Blocker.NO_ANSWERS
    elif share < need_share:
        blocker = Blocker.SHARE
    else:
        blocker = Blocker.NONE

    return BlockClosure(
        cell=cell,
        people=counted.people,
        need=params.restore_users,
        share=share,
        need_share=need_share,
        closed=blocker is Blocker.NONE,
        official=False,
        early=early,
        to_operator=early,
        blocker=blocker,
        users=counted.users,
        drops=counted.drops,
    )


def withdraw_points(
    evidence: Iterable[Evidence],
    restored: Iterable[str],
) -> list[Evidence]:
    """В-4 ning birinchi yarmi: «убирает точку автора».

    Tugma bosgan odamning uzilish haqidagi xabari xaritadan va
    tasdiqlash hisobidan chiqadi. Ikkinchi yarmi («и засчитывается
    как свидетельство») — o'sha akkaunt `close_block` ning
    `evidence` iga tushishi, ya'ni chaqiruvchining ishi.

    Natija — ro'yxat, kirish tartibi saqlanadi: tasdiqlash hisobi
    (`tzcount`) o'zi qayta saralaydi (Т-3).
    """
    gone = frozenset(restored)
    return [item for item in evidence if item.user_id not in gone]


# --------------------------------------------------------------------------
# §4.2 — jimlik va davomiylik
# --------------------------------------------------------------------------


def is_stale(last_message_at: datetime | None, *, now: datetime, params: TzParams) -> bool:
    """§4.2: «Если сообщений нет дольше 3 часов — статус "Данные устарели"».

    `last_message_at is None` — hodisada umuman xabar yo'q; bunday
    hodisa bo'lmaydi, lekin qayta hisoblashda uchraydigan qator
    jimgina «tiklandi» bo'lib ketmasligi uchun u ham jimlik deb
    o'qiladi.
    """
    if last_message_at is None:
        return True
    return now - last_message_at > timedelta(hours=params.stale_after_h)


def duration_of(
    started_at: datetime,
    *,
    now: datetime,
    last_message_at: datetime | None = None,
    closed_at: datetime | None = None,
) -> Duration:
    """§4.2 ning ikkita soni.

    Yopilgan uzilishda ikkalasi teng va `exact` rost. Jimlik bilan
    tugagan uzilishda pastki chek — oxirgi xabargacha (bundan keyin
    ma'lumot yo'q), yuqorisi — hozirgacha: svet oxirgi xabardan
    keyin istalgan lahzada qaytgan bo'lishi mumkin.
    """
    if closed_at is not None:
        exact_h = (closed_at - started_at) / timedelta(hours=1)
        return Duration(low_h=exact_h, high_h=exact_h, exact=True)
    seen = last_message_at if last_message_at is not None else started_at
    low = max((seen - started_at) / timedelta(hours=1), 0.0)
    high = max((now - started_at) / timedelta(hours=1), low)
    return Duration(low_h=low, high_h=high, exact=False)


def summarize_durations(durations: Iterable[Duration]) -> DurationStats:
    """§4.2: aniq bo'lmagan uzilishlar statistikadan **chiqarilmaydi**.

    «Если их выбросить, средняя длительность посчитается только по
    коротким авариям — потому что долгие чаще закрываются по тишине
    из-за разряженных телефонов.» Ya'ni ularni tashlash o'rtachani
    pastga siljitadigan tanlov bo'lardi, tozalash emas.
    """
    items = list(durations)
    if not items:
        return DurationStats(count=0, imprecise=0, average_low_h=0.0, average_high_h=0.0)
    count = len(items)
    return DurationStats(
        count=count,
        imprecise=sum(1 for item in items if not item.exact),
        average_low_h=sum(item.low_h for item in items) / count,
        average_high_h=sum(item.high_h for item in items) / count,
    )


def evaluate_restoration(
    blocks: Iterable[BlockClosure],
    *,
    started_at: datetime,
    now: datetime,
    params: TzParams,
    last_message_at: datetime | None = None,
    closed_at: datetime | None = None,
) -> Restoration:
    """Kvartallarning natijasini butun hodisaga yig'adi (§5).

    Hodisa **hamma** kvartali yopilganda «Восстановлено» bo'ladi va
    o'shanda davomiylik aniq (`closed_at`). Statusni bu funksiya
    tanlamaydi — Т-5 bo'yicha uni `tzstatus.decide()` tanlaydi.
    """
    ordered = tuple(sorted(blocks, key=lambda b: b.cell))
    closed = sum(1 for block in ordered if block.closed)
    finished = closed_at if closed_at is not None else None
    if finished is None and ordered and closed == len(ordered):
        finished = now
    return Restoration(
        blocks=ordered,
        total=len(ordered),
        closed=closed,
        stale=is_stale(last_message_at, now=now, params=params),
        duration=duration_of(
            started_at,
            now=now,
            last_message_at=last_message_at,
            closed_at=finished,
        ),
    )
