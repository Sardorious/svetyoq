"""TZ §12 — «Что проверить до начала»: poroglar erishuvchanmi.

`TZ_Podtverzhdenie_i_uvedomleniya.md` §12 bitta tekshiruvni **majburiy**
deb ataydi va uni butun §2 dan oldinga qo'yadi:

> «Взять историю Ташкента и посчитать: в какой доле реальных аварий за
> первые 20 минут набиралось 3 человека с разных адресов в одной клетке
> r10? … Это единственная проверка, без которой браться за §2 не стоит.»

Tekshiruv o'tkazilmagan. Buni loyihaning o'zi ikki joyda ochiq yozib
qo'ygan (`app/core/tzconfig.py` va `app/admin/registries.py`), ya'ni
§2 ning uchala porogi — 3 / 5 / 8 — `ПРИДУМАНО` belgisi bilan qurilgan
va shu belgi bilan ishlab turibdi. Bu modul tekshiruvning **asbobi**:
tarix paydo bo'lgan zahoti javobni beradi va javobni odam o'qiydigan
shaklda qaytaradi.

## Nima uchun sanoq bu yerda qayta yozilmaydi

Asbob `tzcount.evaluate_levels()` ni chaqiradi — §1.1 ning uchala
sharti, oynalar va poroglar mahsulot kodidagi **o'sha** funksiyadan
olinadi. Sanoqni bu yerda qayta yozish oson edi va u §12 ni jimgina
foydasiz qilardi: o'lchov mahsulot qo'llaydigan qoidadan boshqa
qoida haqida son berardi, va o'sha son bilan §7 ning raqamlari
o'zgartirilardi. O'lchov faqat o'lchanayotgan narsaning o'zini
chaqirganda ma'noga ega.

## 🔴 Maxraj tasdiqlangan hodisalardan olinmaydi

Eng oson yo'l — `outages` dagi `confirmed_at IS NOT NULL` qatorlarni
olib, ularning qanchasida porog yig'ilganini sanash — **har doim
100 % beradi**: tasdiqlangan hodisa ta'rifi bo'yicha porogdan
o'tgan hodisa. Savol («porog erishuvchanmi») o'z javobini o'zi
tasdiqlaydigan shaklga aylanardi va §12 hech qachon «завышены»
demasdi.

Shuning uchun maxrajga faqat **sanoqdan mustaqil** dalil bilan
haqiqiyligi ma'lum bo'lgan hodisalar kiradi: rasmiy qatlam
(`outages.layer == 'official'` — RES e'loni, datchik, operator
kiritgan manba, TZ §8 va В-7). Bunday hodisa yo'q bo'lsa javob
**«noma'lum»**, «erishuvchan» emas: dalilsiz o'lchovni ijobiy
o'qish aynan §12 taqiqlaydigan xato.

## 🔴 §2.3 o'lchov paytida QO'LLANMAYDI

§2.3 («порог = все активные пользователи зоны, но не менее 2») kam
odamli zonani qutqaradi va u §2.1 ning raqamlari erishilmas
bo'lishi mumkinligi **uchun** yozilgan. Uni o'lchovda yoqib
qo'yish — o'lchanayotgan nosozlikni o'lchov vaqtida yamash: porog
ikkigacha tushar va deyarli har bir hodisa «erishildi» bo'lib
chiqardi. Shuning uchun `evaluate_levels()` bu yerda `active_users`
siz chaqiriladi va bu **bazaviy** porogni beradi (§2.1 jadvalining
birinchi ustuni).

## Qachon o'lchanadi

O'lchov nuqtasi — har bir xabarning vaqti. Sanoq faqat o'sha
lahzalarda o'zgaradi: sirpanuvchi oynaga yangi a'zo faqat xabar
kelganda qo'shiladi. Bitta o'lchov (birinchi oynaning oxiri) §12
ning savoliga javob berardi, lekin ikkinchi sonni — «umuman
yig'ildimi, kechroq bo'lsa ham» — bermasdi. Aynan shu ikki sonning
**farqi** amaliy: agar porog birinchi oynada deyarli hech qachon
yig'ilmasa, lekin keyinroq muntazam yig'ilsa, muammo porogda emas,
**oynada**.

`t0` — hodisaning birinchi xabari, `outages.started_at` emas.
`started_at` klasterlash tomonidan qo'yiladi va uning qiymati
sanoqning o'ziga bog'liq bo'lishi mumkin; o'lchov o'zi o'lchayotgan
jarayonning natijasiga tayanmasligi kerak.

## Т-1 / Т-3 / Т-4

Modulda §7 ning soni yo'q — poroglar, oynalar va shartlar
`TzParams` orqali `tzcount` ga o'tadi. «Ko'pchilik holatda»
(§12 ning «в большинстве случаев» i) ham son bilan emas, ikkita
**o'lchangan** sonni solishtirish bilan ifodalanadi
(`LevelResult.looks_high`). Soat argumentda: `measure()` `now` ni
umuman so'ramaydi, chunki tarix o'tmish faktlaridan iborat.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from app.clustering import repository, tzwitness
from app.clustering.tzcount import (
    Evidence,
    Level,
    ZoneVerdict,
    evaluate_levels,
    window_min,
)
from app.core.tzconfig import TzParams
from app.notifications import subscriptions as subscription_queries
from app.reports import queries as report_queries

# `SPEC` konstantasi ataylab **yo'q** — `tzsource` / `tzwitness` /
# `tzactive` bilan bir xil sabab, lekin kuchliroq shaklda: `SPEC` li
# modul `app/admin/registries.py` indeksida qator bo'lishi shart
# (`test_admin_registries.py`), indeks esa **reyestrlar** ni
# ko'rsatadi — hujjatning qatorlarini kod bilan solishtiradiganlarni.
# Bu modulda solishtiriladigan qator yo'q: u §12 ning bandlarini
# emas, **tarixni** o'lchaydi va javobi kodga emas, ma'lumotga
# bog'liq. §12 ning holati indeksda allaqachon ko'rinadi —
# `_probe_tzconfig` o'n oltala sozlamani `ПРИДУМАНО` deb belgilaydi
# va sabab sifatida aynan shu tekshiruvni ataydi.

#: `outages.layer` ning sanoqdan **mustaqil** qiymati. `crowd` qatlami
#: aynan shu modul o'lchayotgan sanoqdan tug'iladi, ya'ni uni maxrajga
#: qo'yish o'lchovni doiraviy qilardi (modul izohi, 🔴).
INDEPENDENT_LAYER = "official"


class Verdict(StrEnum):
    """O'lchovning holati.

    «Poroglar past» degan qiymat ataylab yo'q: §12 faqat bitta
    tomonga qaraydi — «не завышены ли». Pastligini bu tarix
    ko'rsatmaydi, uning uchun soxta tasdiqlar sanalishi kerak.
    """

    #: O'lchash mumkin emas — sabab `Reason` da.
    UNKNOWN = "unknown"
    #: O'lchandi; sonlar `levels` da.
    MEASURED = "measured"


class Reason(StrEnum):
    """Nega o'lchanmadi. `MEASURED` da — `NONE`."""

    NONE = "none"
    #: Tarixda umuman hodisa yo'q.
    NO_HISTORY = "no_history"
    #: Hodisa bor, lekin birortasining haqiqiyligi sanoqdan mustaqil
    #: dalil bilan ma'lum emas (modul izohi, 🔴).
    NO_INDEPENDENT_TRUTH = "no_independent_truth"
    #: Mustaqil hodisa bor, lekin so'ralgan minimumdan kam: ikkita
    #: hodisadan olingan ulush dalil emas.
    TOO_FEW_EPISODES = "too_few_episodes"


@dataclass(frozen=True)
class Episode:
    """Tarixdagi bitta hodisa — o'lchovning birligi.

    `independent` — haqiqiyligi **sanoqdan tashqarida** tasdiqlanganmi.
    Sukut qiymati yo'q: chaqiruvchi har bir hodisa uchun javob berishi
    shart, chunki `True` ni sukut qilish maxrajni doiraviy qilardi va
    `False` ni sukut qilish har qanday tarixni «noma'lum» ga
    aylantirardi.
    """

    outage_id: str
    independent: bool
    #: Hodisaning barcha xabarlari (oyna qo'llanishidan oldin).
    evidence: tuple[Evidence, ...]

    @property
    def first_at(self) -> datetime | None:
        """`t0` — birinchi xabar. Xabarsiz hodisada `None`."""
        return min((item.at for item in self.evidence), default=None)


@dataclass(frozen=True)
class EpisodeReach:
    """Bitta hodisaning bitta darajadagi natijasi."""

    outage_id: str
    level: Level
    #: Shu darajada eng ko'p yig'ilgan guvohlar soni (barcha o'lchov
    #: lahzalari va barcha zonalar bo'yicha eng kattasi). §12 ning
    #: «набирался один-два» iborasi aynan shu son haqida.
    best_people: int
    #: Birinchi oynada (`t0 … t0 + oyna`) porog yig'ildimi.
    reached_in_first_window: bool
    #: Umuman yig'ildimi — tarixning istalgan lahzasida.
    reached_ever: bool
    #: `t0` dan birinchi yig'ilishgacha o'tgan daqiqalar; yig'ilmagan
    #: bo'lsa `None`.
    minutes_to_reach: float | None


@dataclass(frozen=True)
class LevelResult:
    """Bitta darajadagi yig'ma javob."""

    level: Level
    #: Maxraj — mustaqil dalili bor hodisalar soni.
    episodes: int
    #: Birinchi oynada porogga yetganlari (§12 ning asosiy soni).
    reached_in_first_window: int
    #: Kechroq bo'lsa ham yetganlari.
    reached_ever: int
    #: `best_people` → nechta hodisada shuncha guvoh yig'ilgan.
    #: §12: «если в большинстве случаев набирался один-два».
    people_histogram: dict[int, int]

    @property
    def missed(self) -> int:
        """Birinchi oynada porogga **yetmagan** hodisalar."""
        return self.episodes - self.reached_in_first_window

    @property
    def share(self) -> float | None:
        """§12 ning «доля реальных аварий» i. Maxraj nol bo'lsa `None`.

        Nol maxrajda `0.0` qaytarish porogni «erishilmas» deb
        ko'rsatardi, holbuki o'lchanmagan.
        """
        if self.episodes == 0:
            return None
        return self.reached_in_first_window / self.episodes

    @property
    def looks_high(self) -> bool:
        """§12 ning xulosasi: «в большинстве случаев» yetmadimi.

        Sonli chegara bilan emas, ikkita **o'lchangan** sonni
        solishtirish bilan (Т-1): yetmaganlar yetganlardan ko'p
        bo'lsa — porog yuqori. Tenglikda `False`: teng bo'linish
        «ko'pchilik» emas.
        """
        return self.missed > self.reached_in_first_window

    @property
    def window_only(self) -> int:
        """Faqat oyna tufayli o'tmagan hodisalar.

        Porog kechroq yig'ilgan, ya'ni odam yetarli edi — yetmagani
        vaqt. Bu son katta bo'lsa, §7 da o'zgarishi kerak bo'lgan
        narsa porog emas, **oyna**.
        """
        return self.reached_ever - self.reached_in_first_window


@dataclass(frozen=True)
class Reachability:
    """§12 ning javobi."""

    verdict: Verdict
    reason: Reason
    #: Tarixdagi barcha hodisalar (mustaqilligidan qat'i nazar).
    episodes_seen: int
    #: Maxrajga kirganlari.
    episodes_independent: int
    #: Daraja kesimida natija. `UNKNOWN` da bo'sh.
    levels: dict[Level, LevelResult]
    #: Har hodisaning har darajadagi izi — tekshirish uchun. `UNKNOWN`
    #: da ham to'ldiriladi: o'lchov bo'lmasa ham dalil ko'rinsin.
    details: tuple[EpisodeReach, ...]

    def level(self, level: Level) -> LevelResult | None:
        """Darajaning natijasi; o'lchanmagan bo'lsa `None`."""
        return self.levels.get(level)

    @property
    def levels_that_look_high(self) -> tuple[Level, ...]:
        """§12 ning «пороги завышены» ro'yxati, tartiblangan."""
        return tuple(
            level for level in LEVEL_ORDER if level in self.levels and self.levels[level].looks_high
        )


#: Hisobotning tartibi (Т-3). §2.1 jadvalining tartibi.
LEVEL_ORDER: tuple[Level, ...] = (Level.HOUSE, Level.BLOCK, Level.MAHALLA)


def probe_moments(evidence: Iterable[Evidence]) -> tuple[datetime, ...]:
    """O'lchov lahzalari — har xabarning vaqti, takrorsiz va tartibda.

    Sanoq faqat shu lahzalarda o'sadi: sirpanuvchi oynaga yangi a'zo
    xabar kelganda qo'shiladi, oynadan chiqib ketish esa sanoqni
    faqat **kamaytiradi** va tasdiq hosil qila olmaydi.
    """
    return tuple(sorted({item.at for item in evidence}))


def _best_at(
    verdicts: Mapping[tuple[Level, str], ZoneVerdict],
    level: Level,
) -> tuple[int, bool]:
    """Bitta lahzada bitta darajaning eng yaxshi zonasi.

    Qaytadi: `(eng ko'p guvoh, birorta zona porogga yetdimi)`.

    «Eng yaxshi» — chunki hodisa bir nechta r10 katagiga yoyilgan
    bo'lishi mumkin va §2.1 darajalarni **zona bo'yicha** tekshiradi.
    Kataklarning guvohlarini qo'shish porogni sun'iy ravishda
    yig'ardi va §12 «erishuvchan» degan yolg'on javob berardi.
    """
    people = 0
    reached = False
    for (found_level, _cell), verdict in verdicts.items():
        if found_level is not level:
            continue
        people = max(people, verdict.have)
        reached = reached or verdict.reached
    return people, reached


def walk_episode(episode: Episode, *, params: TzParams) -> tuple[EpisodeReach, ...]:
    """Bitta hodisani uchala darajada boshidan oxirigacha yuradi.

    Har lahzada `tzcount.evaluate_levels()` chaqiriladi — **`active_users`
    siz**, ya'ni §2.3 o'chiq va porog bazaviy (modul izohi, 🔴).
    """
    moments = probe_moments(episode.evidence)
    start = episode.first_at

    best: dict[Level, int] = {level: 0 for level in LEVEL_ORDER}
    in_window: dict[Level, bool] = {level: False for level in LEVEL_ORDER}
    ever: dict[Level, bool] = {level: False for level in LEVEL_ORDER}
    first_reach: dict[Level, datetime | None] = {level: None for level in LEVEL_ORDER}

    for moment in moments:
        verdicts = evaluate_levels(episode.evidence, now=moment, params=params)
        for level in LEVEL_ORDER:
            people, reached = _best_at(verdicts, level)
            best[level] = max(best[level], people)
            if not reached:
                continue
            ever[level] = True
            if first_reach[level] is None:
                first_reach[level] = moment
            if start is not None and moment <= start + timedelta(minutes=window_min(level, params)):
                in_window[level] = True

    return tuple(
        EpisodeReach(
            outage_id=episode.outage_id,
            level=level,
            best_people=best[level],
            reached_in_first_window=in_window[level],
            reached_ever=ever[level],
            minutes_to_reach=_minutes_between(start, first_reach[level]),
        )
        for level in LEVEL_ORDER
    )


def _minutes_between(start: datetime | None, moment: datetime | None) -> float | None:
    """Daqiqalardagi farq. Т-1: bo'luvchi son emas, `timedelta`."""
    if start is None or moment is None:
        return None
    return (moment - start) / timedelta(minutes=1)


def measure(
    episodes: Iterable[Episode],
    *,
    params: TzParams,
    min_episodes: int,
) -> Reachability:
    """§12 ning javobi: poroglar erishuvchanmi.

    `min_episodes` ning **sukut qiymati yo'q**. Bu ataylab: bitta
    hodisadan olingan «100 %» yoki «0 %» son emas, tasodif, va
    sukut qiymati chaqiruvchini u haqda o'ylashdan xalos qilardi.
    Son §7 da yo'q, ya'ni uni kodda tanlab qo'yish Т-1 ni buzardi —
    javob chaqiruvchida bo'lishi shart.
    """
    items = list(episodes)
    details: list[EpisodeReach] = []
    for episode in sorted(items, key=lambda item: item.outage_id):
        details += walk_episode(episode, params=params)

    independent = [episode.outage_id for episode in items if episode.independent]

    if not items:
        return _unknown(Reason.NO_HISTORY, items, independent, details)
    if not independent:
        return _unknown(Reason.NO_INDEPENDENT_TRUTH, items, independent, details)
    if len(independent) < min_episodes:
        return _unknown(Reason.TOO_FEW_EPISODES, items, independent, details)

    counted = set(independent)
    levels: dict[Level, LevelResult] = {}
    for level in LEVEL_ORDER:
        rows = [row for row in details if row.level is level and row.outage_id in counted]
        histogram: dict[int, int] = {}
        for row in rows:
            histogram[row.best_people] = histogram.get(row.best_people, 0) + 1
        levels[level] = LevelResult(
            level=level,
            episodes=len(rows),
            reached_in_first_window=sum(1 for row in rows if row.reached_in_first_window),
            reached_ever=sum(1 for row in rows if row.reached_ever),
            people_histogram=dict(sorted(histogram.items())),
        )

    return Reachability(
        verdict=Verdict.MEASURED,
        reason=Reason.NONE,
        episodes_seen=len(items),
        episodes_independent=len(independent),
        levels=levels,
        details=tuple(details),
    )


def _unknown(
    reason: Reason,
    items: Sequence[Episode],
    independent: Sequence[str],
    details: Sequence[EpisodeReach],
) -> Reachability:
    """O'lchanmagan javob. `levels` bo'sh — sonlar o'ylab topilmaydi."""
    return Reachability(
        verdict=Verdict.UNKNOWN,
        reason=reason,
        episodes_seen=len(items),
        episodes_independent=len(independent),
        levels={},
        details=tuple(details),
    )


async def load(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    since: datetime,
    until: datetime,
    kind: str,
    min_trust_score: int,
    account_created_before: datetime,
) -> tuple[Episode, ...]:
    """Tarixni bazadan o'qiydi va `measure()` ning kirishiga aylantiradi.

    Hodisa boshiga bittadan so'rov (`N+1`) — va bu ataylab qabul
    qilingan: §12 **oflayn** tekshiruv, kuniga bir marta emas,
    umuman bir marta yuritiladi («занимает день работы с
    выгрузкой»). So'rovni bitta `IN` ga yig'ish `tz_evidence` ning
    kirish filtrlarini takrorlashni talab qilardi, ya'ni o'lchov
    mahsulotnikidan boshqa filtr bilan ishlashi mumkin bo'lardi —
    modul izohidagi birinchi sabab.

    `min_trust_score` va `account_created_before` — `tz_evidence`
    niki: o'lchov mahsulot ko'radigan **o'sha** xabarlarni ko'radi.
    """
    candidates = await repository.reach_candidates(
        session, region_id=region_id, since=since, until=until
    )
    episodes: list[Episode] = []
    for candidate in candidates:
        rows = await report_queries.tz_evidence(
            session,
            candidate.outage_id,
            kind=kind,
            min_trust_score=min_trust_score,
            account_created_before=account_created_before,
        )
        points = await subscription_queries.declared_points(session, [row.user_id for row in rows])
        homes = tzwitness.resolve_homes(points)
        episodes.append(
            Episode(
                outage_id=str(candidate.outage_id),
                independent=candidate.layer == INDEPENDENT_LAYER,
                evidence=tzwitness.to_evidence(rows, homes),
            )
        )
    return tuple(episodes)


def summary(reach: Reachability) -> Mapping[str, object]:
    """Hisobot uchun tekis kesim (`tools/tz_check.py` va tekshiruv).

    `tzcoverage.summary()` ning juftligi: §12 ning ikkala yarmi bitta
    hisobotga **bir xil shaklda** tushsin. Shakl chaqiruvchida emas,
    modulda yashaydi — chaqiruvchi tanlagan kesim modulning
    navbatdagi maydonini jimgina tashlab ketardi va hisobot kod
    o'lchagan narsadan boshqa narsa haqida bo'lardi.

    `levels` bo'sh bo'lishi mumkin va bu **xato emas**: `UNKNOWN` da
    sonlar o'ylab topilmaydi. Shuning uchun `verdict` ni o'qimasdan
    `levels` ga qarash mumkin emas — bo'sh lug'at «hech bir daraja
    yuqori emas» degani emas, «o'lchanmagan» degani.
    """
    return {
        "verdict": reach.verdict.value,
        "reason": reach.reason.value,
        "episodes_seen": reach.episodes_seen,
        "episodes_independent": reach.episodes_independent,
        "levels_that_look_high": tuple(level.value for level in reach.levels_that_look_high),
        "levels": {
            level.value: {
                "episodes": reach.levels[level].episodes,
                "reached_in_first_window": reach.levels[level].reached_in_first_window,
                "reached_ever": reach.levels[level].reached_ever,
                "missed": reach.levels[level].missed,
                "window_only": reach.levels[level].window_only,
                "share": reach.levels[level].share,
                "looks_high": reach.levels[level].looks_high,
                "people_histogram": dict(reach.levels[level].people_histogram),
            }
            for level in LEVEL_ORDER
            if level in reach.levels
        },
    }
