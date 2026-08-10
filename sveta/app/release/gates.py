"""Reliz gate lari (`03` §6) — «to'xtash nuqtasi, tavsiya emas».

**Nima uchun bu modul bor.** `03` §6 to'qqizta gate ni jadval bilan
sanaydi va ularning maqomini bitta jumla bilan belgilaydi: «Har bir
gate — **to'xtash nuqtasi**, tavsiya emas. Yopilmagan gate keyingi
relizni bloklaydi.» Shu paytgacha bu jadval hujjatda qolib kelgan:
kodda `gate` so'zi umuman uchramasdi, ya'ni loyihaning eng qat'iy
qoidasi — `03` §4 dagi «**Xarita gate yopilmasdan ochilmaydi** — bu
qat'iy qoida, muhokama predmeti emas» — hech qayerda o'lchanmasdi.

Bu modul mezonlarni **bajarmaydi** (xaritani yopmaydi, deploy ni
to'xtatmaydi). U bitta savolga javob beradi: *bugungi holatda qaysi
gate yopiq, qaysi biri yo'q, va qaysi biri haqida umuman
o'lchovimiz yo'q?* Uchinchi javob birinchi ikkitasidan muhimroq.

## Uchta holat, ikkitasi emas

`CriterionStatus` da `UNMEASURED` alohida turadi va u `MET` ga
**qo'shilmaydi**. Sabab hujjatning o'zida yozilgan: `03` §6 G-4 haqida
«Uni "biroz yumshatish" taklifi paydo bo'lganda — bu tasdiqlash
tarafkashligining belgisi, texnik zarurat emas». O'lchanmagan mezonni
jimgina «muammo yo'q» deb ko'rsatadigan hisobot aynan shu
yumshatishning eng arzon shakli bo'lardi: hech kim qaror qabul
qilmaydi, gate esa o'z-o'zidan yopiladi.

Shuning uchun gate faqat **hamma** mezoni `MET` bo'lgandagina `CLOSED`;
bittasi `UNMET` bo'lsa `BLOCKED`; qolgan hamma holatda `UNKNOWN`.
`UNKNOWN` — `CLOSED` emas, ya'ni u ham keyingi relizni bloklaydi.

## Chegaralar konfiguratsiyaga bog'lanmaydi

Bu modulning qoidasi `stats/methodology.py` nikiga **teskari**, va
teskariligi ataylab. Metodologiyada birorta raqamli literal yo'q:
u sozlamalar bilan **birga siljishi** kerak, aks holda vitrina yolg'on
gapiradi. Bu yerda esa chegaralar aynan literal va ular `03` dan
parse qilinadi (`tests/test_release_gates_contract.py`):

* `p90 ≤10 s` chegarasi `settings.map_snapshot_ttl_s` ga bog'lansa,
  gate ni yopish uchun `.env` da bitta sonni o'zgartirish yetarli
  bo'lardi;
* `≥50%` chegarasi `region_config` dan olinsa, E11 dagi sozlash
  gate ni ham «sozlab» qo'yardi.

Gate — mahsulot qarori, ishga tushirish parametri emas. Uni faqat
`03` ni tahrirlab siljitish mumkin, va o'shanda kontrakt testi
o'zgarishni ko'rsatadi.

## Chegarasi yo'q mezon

`coverage.reported_area_share` ning chegarasi `None`, chunki hujjat
uni ochiq qoldirgan: «Qamrov: shahar hududining ≥N% ida kamida bitta
xabar *(N Faza 0 natijalari bo'yicha belgilanadi)*». Bu **kamchilik
emas, holat**: son o'lchanadi va hisobotda ko'rinadi, lekin mezon
`UNMEASURED` bo'lib qoladi — ya'ni G-4 ni yopish uchun avval odam
`N` ni belgilashi kerak. Chegarani «taxminan» to'ldirish gate ning
ma'nosini yo'q qilardi.

## Jadval qisqartma, mezon esa tafsilotda

`03` §6 ning «Mezon» ustuni — **xulosa**. Operativ mezon reliz
tafsilotida yozilgan va u ko'proq: jadval G-4 uchun ikkita shart
sanaydi («Zichlik chegarasi + qamrov chegarasi»), «Yopiq yig'ish
rejimi» ning chiqish mezoni esa **to'rtta**. Faqat jadvalni kodga
ko'chirish ikkita shartni jimgina yo'qotardi, shuning uchun bu yerda
har gate ning mezonlari tafsilotdan olingan va `summary_key` orqali
jadvaldagi qatorga bog'langan.

Modul **toza**: bazaga ham, `settings` ga ham murojaat qilmaydi —
o'lchovlar chaqiruvchidan `Mapping[str, float | None]` sifatida keladi.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

# --------------------------------------------------------------------------
# Chegaralar — hammasi `03` dan, hammasi literal (yuqoridagi izohga qarang)
# --------------------------------------------------------------------------

#: `03` §4 «Yopiq yig'ish rejimi»: «Kuzatilgan uzilish hodisalarining
#: **≥50%** ida ≥3 mustaqil xabar».
MIN_CONFIRMABLE_SHARE = 0.50

#: O'sha qatordan: «≥**3** mustaqil xabar». Bu son `06` §4 ning
#: `confirm.min_users` standart qiymatiga bugun teng, lekin undan
#: **olinmaydi**: `min_users` E11 da sozlanadi va u pastga tushsa gate
#: ham o'z-o'zidan yengillashardi. Ikkovi ajralib ketsa — bu odam
#: ko'rishi kerak bo'lgan hodisa (kontrakt testi tenglikni qulflaydi).
MIN_INDEPENDENT_REPORTS = 3

#: `03` §4 R1.0 chiqish mezoni: «javob p90 **≤10 soniyada** olinadi».
MAX_ANSWER_P90_S = 10.0

#: O'sha qatordan: «xarita **60 soniyada** yangilanadi».
MAX_MAP_REFRESH_S = 60.0

#: O'sha qatordan: «UZ/RU string pariteti **100%**».
MIN_STRING_PARITY = 1.0

#: `03` §4 R1.1 chiqish mezoni: «bildirishnoma tasdiqlangan hodisadan
#: **≤2 daqiqa** ichida yetkaziladi».
MAX_NOTIFY_DELIVERY_P90_S = 120.0

#: `03` §4 R1.2 chiqish mezoni: «hududlar bo'yicha yig'indi umumiy
#: natijadan **≤5%** farq qiladi». Bugun `stats.aggregate`
#: `MAX_UNASSIGNED_RATIO` ham 0.05, lekin bu yerda nusxa turadi:
#: o'sha konstanta yumshatilsa gate **siljimasligi** kerak.
MAX_AGGREGATE_DIFF = 0.05

#: `03` §6 G-8: «**Ikkinchi** mintaqa kodsiz ishga tushdi».
MIN_ACTIVE_REGIONS = 2

#: Bayroq mezonlari (`manual` va «bor/yo'q») shu qiymat bilan
#: o'lchanadi: `1.0` — bajarilgan, `0.0` — yo'q, `None` — o'lchanmagan.
FLAG_TRUE = 1.0


class CriterionKind(StrEnum):
    """Mezonni kim yopadi.

    `MACHINE` — jonli ma'lumotdan hisoblanadi. `MANUAL` — odam
    tekshiradi va qayd etadi (haqiqiy qurilmadagi zanjir, tashqi
    moderatorning mustaqilligi, moderatsiya SLA si). Farq hisobotda
    ko'rinadi, chunki «o'lchanmagan» so'zi ikkala holatda bir xil
    ko'rinsa ham, ikkinchisida **kimdir** nima qilishi kerakligini
    aytadi.
    """

    MACHINE = "machine"
    MANUAL = "manual"


class Direction(StrEnum):
    """Chegara qaysi tomondan: `≥` yoki `≤`."""

    MIN = "min"
    MAX = "max"


class CriterionStatus(StrEnum):
    """Bitta mezonning holati."""

    MET = "met"
    UNMET = "unmet"
    UNMEASURED = "unmeasured"


class GateStatus(StrEnum):
    """Gate ning holati.

    `UNKNOWN` — «bloklanmagan» degani **emas**: `blocking_gate` uni ham
    to'siq deb hisoblaydi.
    """

    CLOSED = "closed"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


#: O'lchovning birligi — hisobotni formatlash va o'qish uchun.
UNIT_SHARE = "share"
UNIT_SECONDS = "seconds"
UNIT_COUNT = "count"
UNIT_FLAG = "flag"

#: i18n kalitlarining prefikslari. Kalitlar `GATE_KEYS`/`CRITERION_KEYS`
#: da **ochiq** sanaladi: f-satrdan yig'ilgan kalit statik tahlil uchun
#: ko'rinmas bo'lardi (`tests/test_i18n_key_contract.py`).
GATE_KEY_PREFIX = "release.gate"
CRITERION_KEY_PREFIX = "release.criterion"


@dataclass(frozen=True)
class Criterion:
    """Bitta mezon: nima o'lchanadi va qaysi chegara bilan.

    `threshold=None` — chegara hali belgilanmagan (`03` dagi «N Faza 0
    natijalari bo'yicha belgilanadi»). Bunday mezon **hech qachon**
    `MET` bo'lmaydi: qiymat o'lchansa ham, uni nima bilan solishtirish
    kerakligi noma'lum.
    """

    code: str
    kind: CriterionKind
    unit: str
    spec: str
    threshold: float | None = None
    direction: Direction = Direction.MIN

    @property
    def key(self) -> str:
        return f"{CRITERION_KEY_PREFIX}.{self.code}"

    def check(self, value: float | None) -> CriterionStatus:
        """Qiymatni chegara bilan solishtiradi.

        Solishtirish **qat'iy emas** (`>=` / `<=`): hujjat mezonlarni
        `≥` va `≤` bilan yozadi, ya'ni chegaraning o'zi yopadi.
        """
        if value is None or self.threshold is None:
            return CriterionStatus.UNMEASURED
        if self.direction is Direction.MIN:
            ok = value >= self.threshold
        else:
            ok = value <= self.threshold
        return CriterionStatus.MET if ok else CriterionStatus.UNMET


@dataclass(frozen=True)
class Gate:
    """`03` §6 ning bitta qatori.

    `blocks` — «Yopilmasa» ustuni, i18n kaliti orqali. U hisobotning
    eng muhim maydoni: gate ning raqami emas, **oqibati** odamga nima
    qilib bo'lmasligini aytadi.
    """

    code: str
    release: str
    criteria: tuple[Criterion, ...]

    @property
    def slug(self) -> str:
        """`G-4` → `g4`. Kalitlarda chiziqcha va katta harf ishlatilmaydi."""
        return self.code.lower().replace("-", "")

    @property
    def summary_key(self) -> str:
        return f"{GATE_KEY_PREFIX}.{self.slug}.summary"

    @property
    def blocks_key(self) -> str:
        return f"{GATE_KEY_PREFIX}.{self.slug}.blocks"


# --------------------------------------------------------------------------
# Reyestr
# --------------------------------------------------------------------------

#: `03` §6 ning to'liq jadvali. **Tartib ma'noli** — gate lar ketma-ket
#: yopiladi va `blocking_gate` birinchi yopilmaganini qaytaradi.
GATES: tuple[Gate, ...] = (
    Gate(
        code="G-0",
        release="M0",
        criteria=(
            Criterion(
                code="deploy_pipeline",
                kind=CriterionKind.MANUAL,
                unit=UNIT_FLAG,
                spec="03 §6",
                threshold=FLAG_TRUE,
            ),
            Criterion(
                code="observability",
                kind=CriterionKind.MANUAL,
                unit=UNIT_FLAG,
                spec="03 §6",
                threshold=FLAG_TRUE,
            ),
        ),
    ),
    Gate(
        code="G-1",
        release="R0.1",
        criteria=(
            Criterion(
                code="e2e_real_device",
                kind=CriterionKind.MANUAL,
                unit=UNIT_FLAG,
                spec="03 §4 R0.1",
                threshold=FLAG_TRUE,
            ),
        ),
    ),
    Gate(
        code="G-2",
        release="R0.2",
        criteria=(
            # Asbob bor (`tools/recluster.py`, E6), lekin gate ni yopadigan
            # narsa asbobning mavjudligi emas, uning **haqiqiy ma'lumotdagi
            # yurishi**: `--sweep` `EXIT_UNSTABLE` bilan tugamasligi kerak.
            Criterion(
                code="recluster_reproducible",
                kind=CriterionKind.MANUAL,
                unit=UNIT_FLAG,
                spec="03 §6",
                threshold=FLAG_TRUE,
            ),
        ),
    ),
    Gate(
        code="G-3",
        release="R0.3",
        criteria=(
            Criterion(
                code="moderation_independent",
                kind=CriterionKind.MANUAL,
                unit=UNIT_FLAG,
                spec="03 §6",
                threshold=FLAG_TRUE,
            ),
        ),
    ),
    Gate(
        code="G-4",
        release="pilot",
        criteria=(
            Criterion(
                code="confirmable_share",
                kind=CriterionKind.MACHINE,
                unit=UNIT_SHARE,
                spec="03 §4 pilot",
                threshold=MIN_CONFIRMABLE_SHARE,
                direction=Direction.MIN,
            ),
            # Chegarasi ataylab yo'q — `N` Faza 0 dan keladi.
            Criterion(
                code="reported_area_share",
                kind=CriterionKind.MACHINE,
                unit=UNIT_SHARE,
                spec="03 §4 pilot",
                threshold=None,
                direction=Direction.MIN,
            ),
            Criterion(
                code="params_stable",
                kind=CriterionKind.MANUAL,
                unit=UNIT_FLAG,
                spec="03 §4 pilot",
                threshold=FLAG_TRUE,
            ),
            Criterion(
                code="moderation_sla",
                kind=CriterionKind.MANUAL,
                unit=UNIT_FLAG,
                spec="03 §4 pilot",
                threshold=FLAG_TRUE,
            ),
        ),
    ),
    Gate(
        code="G-5",
        release="R1.0",
        criteria=(
            Criterion(
                code="answer_p90",
                kind=CriterionKind.MACHINE,
                unit=UNIT_SECONDS,
                spec="03 §4 R1.0",
                threshold=MAX_ANSWER_P90_S,
                direction=Direction.MAX,
            ),
            Criterion(
                code="map_refresh",
                kind=CriterionKind.MACHINE,
                unit=UNIT_SECONDS,
                spec="03 §4 R1.0",
                threshold=MAX_MAP_REFRESH_S,
                direction=Direction.MAX,
            ),
            Criterion(
                code="string_parity",
                kind=CriterionKind.MACHINE,
                unit=UNIT_SHARE,
                spec="03 §4 R1.0",
                threshold=MIN_STRING_PARITY,
                direction=Direction.MIN,
            ),
        ),
    ),
    Gate(
        code="G-6",
        release="R1.1",
        criteria=(
            Criterion(
                code="notify_delivery_p90",
                kind=CriterionKind.MACHINE,
                unit=UNIT_SECONDS,
                spec="03 §4 R1.1",
                threshold=MAX_NOTIFY_DELIVERY_P90_S,
                direction=Direction.MAX,
            ),
            # Mezon — sonning **o'zi** emas, uning o'lchanib qayd
            # etilgani: «noto'g'ri bildirishnoma ulushi o'lchanadi va
            # qayd etiladi». Chegara hujjatda yo'q va o'ylab
            # topilmaydi.
            Criterion(
                code="wrong_notify_measured",
                kind=CriterionKind.MANUAL,
                unit=UNIT_FLAG,
                spec="03 §4 R1.1",
                threshold=FLAG_TRUE,
            ),
        ),
    ),
    Gate(
        code="G-7",
        release="R1.2",
        criteria=(
            Criterion(
                code="aggregate_diff",
                kind=CriterionKind.MACHINE,
                unit=UNIT_SHARE,
                spec="03 §4 R1.2",
                threshold=MAX_AGGREGATE_DIFF,
                direction=Direction.MAX,
            ),
            Criterion(
                code="coverage_index",
                kind=CriterionKind.MACHINE,
                unit=UNIT_FLAG,
                spec="03 §4 R1.2",
                threshold=FLAG_TRUE,
            ),
        ),
    ),
    Gate(
        code="G-8",
        release="R3.0",
        criteria=(
            Criterion(
                code="regions_active",
                kind=CriterionKind.MACHINE,
                unit=UNIT_COUNT,
                spec="03 §6",
                threshold=float(MIN_ACTIVE_REGIONS),
                direction=Direction.MIN,
            ),
            # «**kodsiz** ishga tushdi» — bu o'lchov emas, kuzatuv:
            # ikkinchi mintaqa uchun repoda o'zgarish bo'lmaganini
            # faqat odam tasdiqlaydi.
            Criterion(
                code="regions_no_code",
                kind=CriterionKind.MANUAL,
                unit=UNIT_FLAG,
                spec="03 §6",
                threshold=FLAG_TRUE,
            ),
        ),
    ),
)

GATE_BY_CODE: dict[str, Gate] = {gate.code: gate for gate in GATES}

#: Barcha mezonlar, gate tartibida. Kod takrorlanmaydi — `_check_registry`.
CRITERIA: tuple[Criterion, ...] = tuple(c for gate in GATES for c in gate.criteria)

CRITERION_BY_CODE: dict[str, Criterion] = {c.code: c for c in CRITERIA}

#: Katalogdan so'raladigan kalitlar, **literal** ro'yxat sifatida
#: (`tests/test_i18n_key_contract.py` ning `KEY_TABLES` naqshi).
GATE_KEYS: tuple[str, ...] = tuple(
    f"{GATE_KEY_PREFIX}.{gate.slug}.{part}" for gate in GATES for part in ("summary", "blocks")
)
CRITERION_KEYS: tuple[str, ...] = tuple(f"{CRITERION_KEY_PREFIX}.{c.code}" for c in CRITERIA)


def _check_registry() -> None:
    """Reyestrning o'zidagi ikkita jimgina xato.

    Import paytida bajariladi: ikkalasi ham hisobotni **to'g'ri
    ko'rinishda** qoldiradi va faqat sonlarni o'qiganda bilinadi.
    """
    codes = [c.code for c in CRITERIA]
    duplicates = sorted({code for code in codes if codes.count(code) > 1})
    if duplicates:
        # Nusxa bo'lsa `CRITERION_BY_CODE` bittasini yutardi va
        # o'lchov noto'g'ri gate ga tushardi.
        raise ValueError(f"mezon kodi takrorlangan: {duplicates}")
    empty = [gate.code for gate in GATES if not gate.criteria]
    if empty:
        # Mezoni yo'q gate `all(...)` bo'yicha **yopiq** bo'lardi:
        # hech narsa tekshirmagani uchun.
        raise ValueError(f"gate mezonsiz: {empty}")


_check_registry()


# --------------------------------------------------------------------------
# Baholash
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class CriterionResult:
    """Mezon + uning bugungi qiymati va holati."""

    criterion: Criterion
    value: float | None
    status: CriterionStatus


@dataclass(frozen=True)
class GateResult:
    """Gate + uning mezonlari."""

    gate: Gate
    status: GateStatus
    criteria: tuple[CriterionResult, ...]

    @property
    def is_closed(self) -> bool:
        return self.status is GateStatus.CLOSED


@dataclass(frozen=True)
class GateReport:
    """To'liq hisobot."""

    gates: tuple[GateResult, ...]

    @property
    def blocking_gate(self) -> GateResult | None:
        """Birinchi **yopilmagan** gate — u va undan keyingi hamma reliz to'xtaydi.

        `UNKNOWN` ham to'siq: «o'lchamadik» — «yopildi» emas.
        """
        for result in self.gates:
            if not result.is_closed:
                return result
        return None

    @property
    def closed_count(self) -> int:
        return sum(1 for result in self.gates if result.is_closed)


def _gate_status(criteria: tuple[CriterionResult, ...]) -> GateStatus:
    if any(item.status is CriterionStatus.UNMET for item in criteria):
        return GateStatus.BLOCKED
    if all(item.status is CriterionStatus.MET for item in criteria):
        return GateStatus.CLOSED
    return GateStatus.UNKNOWN


def evaluate(values: Mapping[str, float | None]) -> GateReport:
    """O'lchovlardan to'liq hisobot.

    `values` — `{mezon kodi: qiymat}`. Ro'yxatda yo'q mezon
    `UNMEASURED` bo'ladi; notanish kalit esa **xato**, e'tiborsiz
    emas: `confirmable_share` o'rniga `confirmed_share` yozilgan
    chaqiruv jimgina «o'lchanmagan» hisobot berardi va G-4 ning
    o'lchangan yagona qatori yo'qolardi.
    """
    unknown = sorted(set(values) - set(CRITERION_BY_CODE))
    if unknown:
        raise ValueError(f"notanish mezon kodi: {unknown}")
    results = []
    for gate in GATES:
        items = tuple(
            CriterionResult(
                criterion=criterion,
                value=values.get(criterion.code),
                status=criterion.check(values.get(criterion.code)),
            )
            for criterion in gate.criteria
        )
        results.append(GateResult(gate=gate, status=_gate_status(items), criteria=items))
    return GateReport(gates=tuple(results))
