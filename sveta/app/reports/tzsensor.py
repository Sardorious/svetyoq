"""TZ §11/7 — datchiklar va rasmiy manbalarning qabuli.

`TZ_Podtverzhdenie_i_uvedomleniya.md` §11 navbatining **yettinchi** va
oxirgi bandi: «Приём датчиков — можно параллельно». Hujjatda unga
atalgan alohida bo'lim yo'q, ya'ni talab uchta joydan yig'iladi:

* **В-7** (§4): «Датчик или официальный источник закрывают квартал
  сразу» — tashqi signal tiklanishni **darhol** yopadi;
* **§8**: operator «внести официальный источник» qila oladi, lekin
  «не может создать подтверждение по собственному мнению без внешнего
  источника»; kartada uning ishi **alohida** belgilanadi — «Проверено
  оператором», «Подтверждено жителями» emas;
* **§6.3**: rejali ishlar e'lonining to'rtinchi ustuni — «источник».

Ya'ni §11/7 bitta narsani quradi: tashqi signal tizimga **qanday
kiradi** va u yerda nima bo'ladi. Hisobning o'zi bu yerda yo'q — u
`app.clustering.tzcount` da; status ham bu yerda tanlanmaydi — Т-5
bo'yicha u faqat `app.clustering.tzstatus.decide()` da tanlanadi. Bu
modul `TzStatus` ni import ham qilmaydi.

## Nima uchun `app.reports`, `app.clustering` emas

Qabul qilingan signal — bu **xabar**, faqat odamdan emas. `app.reports`
allaqachon manbalar reyestrini (`sources.py`, `06` §2) saqlaydi va
`clustering` ham, `notifications` ham uni import qiladi (`05` §1 dagi
yo'nalish). Modulni `clustering` ga qo'yish `notifications` ni undan
uzib qo'yardi (u `clustering` ni ataylab import qilmaydi, 176- va
177-runlarning qarori), `notifications` ga qo'yish esa В-7 ni
tiklanishdan uzardi. `reports` — ikkalasi ham ko'radigan yagona joy.

Modul **leaf**: `app.core.tzconfig` dan boshqa hech narsani import
qilmaydi. Ikkala ko'prik ham (В-7 uchun `official_fields()`, §8 uchun
`verified_fields()`) lug'at qaytaradi, chaqiruvchi esa undan o'zining
tipini yasaydi. Aks holda halqa chiqardi: `clustering.tzstatus` bu
modulni import qiladi, bu modul esa `clustering.tzrestore` ni.

## 🔴 Manbasiz signal yo'q, ro'yxatdan o'tmagan manba ham yo'q

§8 ning taqiqi («без внешнего источника») faqat operatorga emas,
butun kanalga tegishli. Shuning uchun:

* `reference` bo'sh bo'la olmaydi — bu `Reading` ning konstruktorida
  tekshiriladi, kechroq emas;
* har bir `source_id` **reyestrda** bo'lishi shart (`Source`).
  Ro'yxatdan o'tmagan qurilma — noma'lum odamning telefoni bilan bir
  xil huquqda bo'lardi, holbuki u §2.1 ning porogini butunlay
  aylanib o'tadi;
* datchikning katagi **reyestrda** yozilgan, xabarda emas. Xabar
  boshqa katakni ko'rsatsa — `CELL_MISMATCH`. Aks holda bitta buzilgan
  qurilma shaharning istalgan kvartalini yopa olardi.

Operator va rasmiy kanal uchun aksincha: katak xabarda keladi (odam
qaysi kvartal haqida gapirayotganini o'zi biladi), lekin `actor`
majburiy — §8: «Все действия пишутся в журнал с указанием, **кто** и
на основании чего».

## 🔴 Takror xabar — yangi fakt emas (Т-7)

Т-7: «Повторная отправка того же сообщения не создаёт второго
свидетельства». Datchik uchun bu qoida odamdagidan **kuchliroq**
ishlaydi: qurilma holatini har daqiqada takrorlaydi va bir kechada
mingta «света нет» yuboradi. Ikki qatlam:

1. `dedup_key()` — `blake2b(manba|signal|katak|vaqt)`. Xuddi o'sha
   xabar ikkinchi marta kelsa (`seen`), u umuman fakt bo'lmaydi.
   Python ning o'rnatilgan `hash()` i ishlatilmaydi: u har protsessda
   tasodifiylanadi va Т-3 ning takrorlanuvchanligini buzardi.
2. `Reject.REPEAT` — vaqti boshqa, lekin **holati o'sha**. Bu ham
   yangi fakt emas: qurilma o'zgarishni emas, borligini bildiryapti.

Ya'ni qabul qilinadigan narsa — xabar emas, **holat o'zgarishi**.

## 🔴 «Raqqosa» datchik operatorga boradi, jimgina tashlanmaydi

Buzuq qurilma holatni daqiqada o'n marta almashtiradi. Har almashinuv
В-7 bo'yicha kvartalni yopib qayta ochardi, ya'ni bir kechada o'nlab
«свет вернулся» bildirishnomasi. `tz.sensor.min_state_min` shuni
to'sadi.

Lekin to'silgan xabar **yo'qolmaydi**: `Rejection.to_operator` uni §8
ning odamiga olib chiqadi. Т-8 («при срабатывании защиты пользователь
получает обычный ответ») bu yerda qo'llanmaydi — u odamga qarshi
himoya haqida, buzuq qurilmani esa yashirish kerak emas, uni
tuzatish kerak.

## Т-4: soat argumentda

Modulning birorta funksiyasi tizim soatiga qaramaydi; `now` har doim
argument. §7 ning birorta soni literal emas (`tests/test_tz_sensor.py`
ikkalasini ham `ast` bilan qulflaydi).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from app.core.tzconfig import TzParams

#: Hujjat bo'limi. Reyestrlar vitrinasi (`app.admin.registries`) shuni o'qiydi.
SPEC = "TZ §11/7"


class Channel(StrEnum):
    """Signal qayerdan keladi. Uchtasi ham **tashqi manba** (§8)."""

    #: Qurilma. Katagi reyestrda qotirilgan, odam ishtirok etmaydi.
    SENSOR = "sensor"
    #: §8 ning operatori: RESga qo'ng'iroq, rasmiy e'lon, xat.
    #: Manba **va** kim kiritgani ikkalasi ham majburiy.
    OPERATOR = "operator"
    #: Avtomatik rasmiy kanal (1055 va shunga o'xshash), odamsiz.
    FEED = "feed"


class Signal(StrEnum):
    """Signal nima deyapti."""

    #: «Света нет» — §8 ning «Проверено оператором» iga olib boradi.
    POWER_OFF = "power_off"
    #: «Свет есть» — В-7, kvartal darhol yopiladi.
    POWER_ON = "power_on"
    #: §6.3 ning uchinchi qatori: rejali ishlar e'loni.
    PLANNED = "planned"
    #: Qurilma holatni bilmaydi (aloqa yo'q, o'zini tekshiryapti).
    #: §4.1 ning «нет ответа → ничего» i bilan bir xil: hech narsa.
    UNKNOWN = "unknown"


class Reject(StrEnum):
    """Xabar nega faktga aylanmadi. Jurnalda va operator panelida."""

    NONE = "none"
    #: Manba reyestrda yo'q.
    UNKNOWN_SOURCE = "unknown_source"
    #: Reyestrda bor, lekin ishonch olib qo'yilgan (buzuq, sinovda).
    UNTRUSTED = "untrusted"
    #: Datchik o'z katagidan boshqasini ko'rsatdi.
    CELL_MISMATCH = "cell_mismatch"
    #: Operator/kanal xabarida katak yo'q.
    NO_CELL = "no_cell"
    #: §8: kim kiritgani ko'rsatilmagan.
    NO_ACTOR = "no_actor"
    #: Vaqti kelajakda — soat noto'g'ri qo'yilgan.
    FUTURE = "future"
    #: `tz.sensor.max_age_min` dan eski.
    TOO_OLD = "too_old"
    #: Т-7: aynan shu xabar allaqachon qabul qilingan.
    DUPLICATE = "duplicate"
    #: Holat o'zgarmadi — qurilmaning takroriy xabari.
    REPEAT = "repeat"
    #: `tz.sensor.min_state_min` dan tez almashdi.
    FLAPPING = "flapping"
    #: `Signal.UNKNOWN` — ma'lumot yo'q.
    NO_STATE = "no_state"


#: §8 ga olib chiqiladigan rad etishlar: bular qurilmaning yoki
#: sozlamaning nosozligi, ya'ni ular haqida **odam** bilishi kerak.
#: Qolganlari (`REPEAT`, `DUPLICATE`, `NO_STATE`) — normal ish tartibi.
TO_OPERATOR: frozenset[Reject] = frozenset(
    {
        Reject.UNKNOWN_SOURCE,
        Reject.UNTRUSTED,
        Reject.CELL_MISMATCH,
        Reject.FUTURE,
        Reject.TOO_OLD,
        Reject.FLAPPING,
    }
)

#: Holat o'zgarishi sifatida kuzatiladigan signallar. `PLANNED` bu
#: ro'yxatda **yo'q**: e'lon qurilmaning holati emas, u kelajak haqida
#: va uni «takroriy» deb tashlash e'lonning yangilanishini yo'qotardi.
STATEFUL: frozenset[Signal] = frozenset({Signal.POWER_OFF, Signal.POWER_ON})

#: `blake2b` digestining uzunligi (bayt). Implementatsiya geometriyasi,
#: §7 sozlamasi emas.
KEY_DIGEST_BYTES = 16


@dataclass(frozen=True)
class Source:
    """Ro'yxatdan o'tgan manba.

    Reyestrning o'zi bazada (`region_config` emas, alohida jadval —
    hali yaratilmagan, `INBOUND` ga qarang). Bu yerda uning **shakli**
    va qoidalari.
    """

    source_id: str
    channel: Channel
    #: `SENSOR` uchun majburiy: qurilma o'rnatilgan kvartal (r9).
    #: `OPERATOR`/`FEED` uchun `None` — katak xabarda keladi.
    cell: str | None = None
    #: Ishonch olib qo'yilganmi (buzuq deb belgilangan, sinovda).
    trusted: bool = True
    note: str = ""

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError(f"{SPEC}: manba identifikatori bo'sh")
        if self.channel is Channel.SENSOR and not (self.cell or "").strip():
            raise ValueError(f"{SPEC}: datchikning katagi reyestrda qotirilishi shart")
        if self.channel is not Channel.SENSOR and self.cell is not None:
            raise ValueError(f"{SPEC}: {self.channel} kanalida katak xabarda keladi")


@dataclass(frozen=True)
class Reading:
    """Kirgan bitta xabar — hali fakt emas."""

    source_id: str
    signal: Signal
    at: datetime
    #: §8: «на основании чего». Bo'sh bo'la olmaydi.
    reference: str
    #: `OPERATOR`/`FEED` uchun majburiy, `SENSOR` uchun reyestrdan.
    cell: str | None = None
    #: §8: «кто». `OPERATOR` uchun majburiy.
    actor: str | None = None
    #: `PLANNED` uchun: ishlar qachon boshlanadi (§6.3).
    starts_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.reference.strip():
            # §8: manbasiz «rasmiy» signal — aynan o'sha taqiqlangan
            # «по собственному мнению», faqat boshqa nom ostida.
            raise ValueError(f"{SPEC}: §8 — manbasiz signal qabul qilinmaydi")


@dataclass(frozen=True)
class Fact:
    """Qabul qilingan signal. Jurnalga shu yoziladi (Т-2, Т-6)."""

    #: Т-7 ning kaliti.
    key: str
    source_id: str
    channel: Channel
    signal: Signal
    cell: str
    at: datetime
    reference: str
    actor: str | None = None
    starts_at: datetime | None = None

    @property
    def closes_block(self) -> bool:
        """В-7: kvartalni darhol yopadigan fakt."""
        return self.signal is Signal.POWER_ON

    @property
    def verifies_outage(self) -> bool:
        """§8: «Проверено оператором» ga olib boradigan fakt."""
        return self.signal is Signal.POWER_OFF


@dataclass(frozen=True)
class Rejection:
    """Qabul qilinmagan xabar va sababi."""

    reading: Reading
    reason: Reject

    @property
    def to_operator(self) -> bool:
        """§8 ning odamiga ko'rinadimi."""
        return self.reason in TO_OPERATOR


@dataclass(frozen=True)
class State:
    """Manbaning oxirgi qabul qilingan holati (`REPEAT`/`FLAPPING` uchun)."""

    signal: Signal
    at: datetime


@dataclass(frozen=True)
class Intake:
    """Bitta qabul sikli natijasi."""

    accepted: tuple[Fact, ...]
    rejected: tuple[Rejection, ...]

    @property
    def keys(self) -> frozenset[str]:
        """Т-7: chaqiruvchi keyingi siklda `seen` ga shuni qo'shadi."""
        return frozenset(fact.key for fact in self.accepted)

    @property
    def to_operator(self) -> tuple[Rejection, ...]:
        """§8 ga ko'rinadigan rad etishlar."""
        return tuple(item for item in self.rejected if item.to_operator)

    def closures(self) -> tuple[Fact, ...]:
        """В-7 — kvartallarni darhol yopadigan faktlar."""
        return tuple(fact for fact in self.accepted if fact.closes_block)

    def verifications(self) -> tuple[Fact, ...]:
        """§8 — «Проверено оператором» ga asos bo'ladigan faktlar."""
        return tuple(fact for fact in self.accepted if fact.verifies_outage)

    def planned(self) -> tuple[Fact, ...]:
        """§6.3 — rejali ishlar e'lonlari."""
        return tuple(fact for fact in self.accepted if fact.signal is Signal.PLANNED)

    def state(self) -> dict[str, State]:
        """Manbalarning yangi holati — keyingi siklga `last` bo'lib qaytadi."""
        latest: dict[str, State] = {}
        for fact in self.accepted:
            if fact.signal not in STATEFUL:
                continue
            known = latest.get(fact.source_id)
            if known is None or fact.at >= known.at:
                latest[fact.source_id] = State(signal=fact.signal, at=fact.at)
        return latest


def dedup_key(source_id: str, signal: Signal, cell: str, at: datetime) -> str:
    """Т-7 ning kaliti — takrorlanadigan, protsessga bog'liq emas."""
    raw = "|".join((source_id, signal.value, cell, at.isoformat()))
    return hashlib.blake2b(raw.encode("utf-8"), digest_size=KEY_DIGEST_BYTES).hexdigest()


def _cell_of(reading: Reading, source: Source) -> tuple[str | None, Reject]:
    """Fakt qaysi kvartalga tegishli — va katak qoidasi buzildimi."""
    if source.channel is Channel.SENSOR:
        pinned = source.cell or ""
        claimed = (reading.cell or "").strip()
        if claimed and claimed != pinned:
            return None, Reject.CELL_MISMATCH
        return pinned, Reject.NONE
    claimed = (reading.cell or "").strip()
    if not claimed:
        return None, Reject.NO_CELL
    return claimed, Reject.NONE


def _clock(reading: Reading, *, now: datetime, params: TzParams) -> Reject:
    """Vaqt qoidasi: kelajak yo'q, juda eski xabar ham yo'q."""
    if reading.at > now:
        return Reject.FUTURE
    if now - reading.at > timedelta(minutes=params.sensor_max_age_min):
        return Reject.TOO_OLD
    return Reject.NONE


def _state_rule(
    reading: Reading,
    known: State | None,
    *,
    params: TzParams,
) -> Reject:
    """Holat o'zgarishi qoidasi: takror emasmi, tez almashmadimi."""
    if known is None or reading.signal not in STATEFUL:
        return Reject.NONE
    if reading.at < known.at:
        # Eski xabar kech keldi: u hozirgi holatni bekor qila olmaydi.
        return Reject.REPEAT
    if reading.signal is known.signal:
        return Reject.REPEAT
    if reading.at - known.at < timedelta(minutes=params.sensor_min_state_min):
        return Reject.FLAPPING
    return Reject.NONE


def classify(
    reading: Reading,
    *,
    now: datetime,
    sources: Mapping[str, Source],
    params: TzParams,
    seen: frozenset[str] = frozenset(),
    last: Mapping[str, State] | None = None,
) -> tuple[Fact | None, Reject]:
    """Bitta xabar: fakt bo'ladimi va bo'lmasa nega.

    Tartib **ataylab shunday**: avval manba (kim), keyin katak (qayer),
    keyin vaqt (qachon), keyin takror (Т-7), oxirida holat. Har qadam
    o'zidan oldingisini nazarda tutadi — noma'lum manbaning katagi
    haqida gapirishning ma'nosi yo'q, va rad etish sababi doim
    **birinchi** buzilgan qoidani nomlaydi.
    """
    source = sources.get(reading.source_id)
    if source is None:
        return None, Reject.UNKNOWN_SOURCE
    if not source.trusted:
        return None, Reject.UNTRUSTED
    if source.channel is Channel.OPERATOR and not (reading.actor or "").strip():
        return None, Reject.NO_ACTOR

    cell, verdict = _cell_of(reading, source)
    if cell is None:
        return None, verdict

    verdict = _clock(reading, now=now, params=params)
    if verdict is not Reject.NONE:
        return None, verdict

    if reading.signal is Signal.UNKNOWN:
        return None, Reject.NO_STATE

    key = dedup_key(reading.source_id, reading.signal, cell, reading.at)
    if key in seen:
        return None, Reject.DUPLICATE

    known = (last or {}).get(reading.source_id)
    verdict = _state_rule(reading, known, params=params)
    if verdict is not Reject.NONE:
        return None, verdict

    return (
        Fact(
            key=key,
            source_id=source.source_id,
            channel=source.channel,
            signal=reading.signal,
            cell=cell,
            at=reading.at,
            reference=reading.reference.strip(),
            actor=(reading.actor or None),
            starts_at=reading.starts_at,
        ),
        Reject.NONE,
    )


def accept(
    readings: Iterable[Reading],
    *,
    now: datetime,
    sources: Mapping[str, Source],
    params: TzParams,
    seen: frozenset[str] = frozenset(),
    last: Mapping[str, State] | None = None,
) -> Intake:
    """Xabarlar to'plami → faktlar va rad etishlar.

    Xabarlar **vaqt bo'yicha** tartiblanadi: bitta paketda kelgan
    `off`/`on` juftligining ma'nosi ularning tartibiga bog'liq, paketdagi
    tartib esa tarmoqniki, hodisalarniki emas. Sikl davomida `seen` va
    `last` yangilanib boradi — aks holda bitta paketdagi ikkita bir xil
    xabar ikkita fakt bo'lardi (Т-7).
    """
    ordered = sorted(readings, key=lambda item: (item.at, item.source_id))
    known: dict[str, State] = dict(last or {})
    fresh: set[str] = set(seen)
    facts: list[Fact] = []
    rejects: list[Rejection] = []

    for reading in ordered:
        fact, reason = classify(
            reading,
            now=now,
            sources=sources,
            params=params,
            seen=frozenset(fresh),
            last=known,
        )
        if fact is None:
            rejects.append(Rejection(reading=reading, reason=reason))
            continue
        facts.append(fact)
        fresh.add(fact.key)
        if fact.signal in STATEFUL:
            known[fact.source_id] = State(signal=fact.signal, at=fact.at)

    return Intake(accepted=tuple(facts), rejected=tuple(rejects))


# --------------------------------------------------------------------------
# Ko'priklar — chaqiruvchi o'z tipini yasaydi (halqa bo'lmasin)
# --------------------------------------------------------------------------


def official_fields(fact: Fact) -> dict[str, str]:
    """В-7 ko'prigi: `tzrestore.OfficialSource(**official_fields(fact))`.

    Lug'at qaytariladi, tip emas: `app.clustering.tzrestore` bu modulni
    import qiladigan tomon, teskarisi halqa bo'lardi. Ko'prikning
    shakli `tests/test_tz_sensor.py` da haqiqiy `OfficialSource` bilan
    qulflangan.
    """
    if not fact.closes_block:
        raise ValueError(f"{SPEC}: V-7 faqat `power_on` faktiga tegishli")
    return {"kind": fact.channel.value, "reference": fact.reference}


def verified_fields(fact: Fact) -> dict[str, object]:
    """§8 ko'prigi: `tzstatus.Verified(**verified_fields(fact))`.

    O'sha sabab bilan lug'at. `actor` ham ko'chiriladi: §8 «кто и на
    основании чего» ni **ikkalasini** talab qiladi, va kartadagi
    «отдельная подпись» aynan shu ikkitadan yasaladi.
    """
    if not fact.verifies_outage:
        raise ValueError(f"{SPEC}: §8 tekshiruvi faqat `power_off` faktiga tegishli")
    return {
        "source": fact.channel.value,
        "reference": fact.reference,
        "at": fact.at,
        "actor": fact.actor,
    }


# --------------------------------------------------------------------------
# Reyestr — `app.admin.registries` shuni o'qiydi
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Inbound:
    """§11/7 ning bitta signali va uning **haqiqiy kirish yo'li**.

    Ikkita da'vo ataylab ajratilgan. `built` — qabul mantiqi shu
    signalni biladimi. `wired` — o'sha signal tashqaridan **kira
    oladimi**: reyestr bormi, yozadigan yo'l bormi, natija saqlanadimi.

    Ikkalasini bitta bayroqqa qo'shish reyestrni yolg'onga
    aylantirardi: «datchik qabul qilinadi» va «datchik ulangan» —
    turli da'volar, va В-7 aynan ikkinchisiga tayanadi.

    179-run ikkinchi da'voni yopdi: `tz_sources` reyestri, `tz_signals`
    jurnali (Т-2) va `POST /api/v1/tz/readings`. `need` bo'sh emas —
    unda **qolgan** ish yozilgan, va u boshqa savolga tegishli: kanal
    bor, uning qulay yuzasi yo'q.
    """

    signal: Signal
    #: Qabul mantiqi shu signalni biladimi.
    built: bool
    #: Tashqaridan kiradigan haqiqiy kanal bormi.
    wired: bool
    #: Nima yetishmayapti (kanal bor bo'lsa ham).
    need: str


INBOUND: tuple[Inbound, ...] = (
    Inbound(
        signal=Signal.POWER_OFF,
        built=True,
        wired=True,
        need="§8 operatorining paneli — bugun faqat `POST /tz/readings`",
    ),
    Inbound(
        signal=Signal.POWER_ON,
        built=True,
        wired=True,
        need="qurilmaning o'z hisob ma'lumoti — bugun shlyuz tokeni",
    ),
    Inbound(
        signal=Signal.PLANNED,
        built=True,
        wired=True,
        need="§6.3 e'lon shakli — bugun faqat `POST /tz/readings`",
    ),
)
