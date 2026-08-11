"""Muvaffaqiyat metrikalari (`01` §4 «Success Metrics») ↔ kod.

**Nima uchun bu modul bor.** 83-run uchta nomzod qoldirdi va §4 ular
ichida eng kattasi edi: o'n ikkita KPI, ikkalasida son, sakkiztasida
«Faza 0 dan keyin» va ikkitasida ochiq rad javobi. Bo'lim boshqa
reyestrlardan bir narsa bilan farq qiladi — u **kelajakdagi**
o'lchovlar haqida, ya'ni «bajarilganmi?» degan savol unga to'g'ridan
to'g'ri berilmaydi. Berish mumkin bo'lgan savol bitta: *bugun repo bu
sonni umuman **chiqara oladimi**?* Maqsad qiymati hali yo'q bo'lsa
ham, o'lchagich bo'lishi kerak — aks holda Faza 0 tugagan kunda
o'lchash uchun hech narsa bo'lmaydi.

## Asosiy topilma: sonli ikkita maqsad — aynan javob berilmaydigan
## ikkitasi, o'lchanadigan ikkita qator esa maqsad emasligi yozilgan

Jadval to'rt qatorda aniq gapiradi va to'rttasi ham ikki juftga
ajraladi:

* **Sonli maqsad ikkita** — `Time to Value ≤10 с` va
  `Coverage Index ≥50% махаллей с покрытием выше низкого`. Repo
  ikkalasiga ham javob bera olmaydi: birinchisi paketda **umuman
  ta'riflanmagan** (butun paketda ibora bir marta uchraydi — shu
  katakda), ikkinchisining semantikasi esa qurilgan
  (`coverage.BAND_THRESHOLDS` «past pog'onadan yuqori» ni `medium` dan
  boshlaydi) va ma'lumoti hech qachon kelmaydi — `mahallas` ga
  yozadigan yo'l repoda yo'q (83-run, `glossary.Fidelity.UNREACHABLE`).
* **Repo haqiqatan chiqaradigan davomiylik ikkita** —
  `DurationCut.median_min` va `DurationCut.p90_min`, va aynan o'sha
  ikkala katakda «**не применимо как target**» yozilgan.

Ya'ni jadval o'zini teskari tartibda ko'rsatadi: o'lchagichi bor
qatorlar maqsaddan chiqarilgan, maqsadi bor qatorlarda esa o'lchagich
yo'q. Shuning uchun hisobotning bosh xossasi — `targets_are_answerable`
(`glossary.marks_hold` va `roadmap.gate_holds` bilan bir xil rolda).

## Nima uchun «bajarilganmi?» emas, «chiqara oladimi?»

75-run reyestrni `Вероятность` × `Влияние` bo'yicha o'qishdan bosh
tortgan edi: bashorat kelajak haqida, repo esa bugun haqida javob
beradi. Bu yerda ham xuddi shunday, faqat teskari tomondan — §4 ning
Target ustuni **ataylab** bo'sh (sakkiz qatorda «подлежит замеру»), va
uni bo'shligi uchun ayblash bo'limni noto'g'ri o'qish bo'lardi.
Bo'shlikning narxi boshqa joyda: 82-run `roadmap.evaluate().recorded`
ni **bo'sh** deb topdi, ya'ni Faza 0 natijasi repoda saqlanadigan joy
yo'q. Sakkizta `DEFERRED` maqsad o'sha yopilmagan gate ortida turibdi
va ular uchun qilinadigan yagona foydali ish — o'lchagichni oldindan
tayyorlash. `Reading` o'qi aynan shuni o'lchaydi.

## `Reading` — olti sinf, va ular bir-birini almashtirmaydi

67-run ning sabog'i (`measures.Coverage`) shu yerda ham ishlaydi, faqat
kengroq: «hisoblanadi / hisoblanmaydi» ikkiligi bu bo'limda **to'rtta**
turli xil to'siqni bitta katakka tiqib qo'yardi.

* `SERVED` — repo sonni hisoblaydi va javobda beradi;
* `DERIVABLE` — xom qatorlar bazada bor, yig'adigan kod yo'q. Bu qarz,
  to'siq emas: uni yozish bir kunlik ish va hech narsani kutmaydi;
* `EMITTED` — hodisa oqimida bor, lekin repoda **saqlanmaydi**
  (`analytics.track.emit` faqat jurnalga yozadi, `01` §22 esa jurnal
  stekini meros deb e'lon qiladi). Ya'ni javob repodan tashqarida
  quriladi, lekin repo unga xom ashyo beradi;
* `BLIND` — kerakli kirish mahsulotda umuman yo'q. Yig'uvchi yozish
  yordam bermaydi: yig'adigan narsa yo'q;
* `UNREACHABLE` — hisob **qurilgan**, lekin uni to'ldiradigan ma'lumot
  hech qachon paydo bo'lmaydi. `BLIND` dan farqi muhim: bu yerda
  yozilgan kod bor va u to'g'ri, kutilayotgani — ma'lumot;
* `EXTERNAL` — javob mahsulotdan tashqarida olinadi va bu **normal**
  (`NPS` — so'rovnoma). `measures.Coverage.EXTERNAL` bilan bir xil
  rolda: bo'shliq emas.

## `Target` — ustun uch xil narsa aytadi

* `QUANTIFIED` — tekshirib bo'ladigan son;
* `DEFERRED` — «подлежит установке / замеру после Ph.0». ⚠️ `NPS`
  qatoriga ehtiyot bo'lish kerak: uning katagida son **bor**
  (`выборке ≥100`), lekin bu maqsad emas, **namuna hajmi** — ya'ni
  qator sonli ko'rinadi va sonsiz;
* `DISCLAIMED` — «не применимо как target». Bo'lim buni o'zi yozadi va
  sababini ham beradi («наблюдаемая величина»), ya'ni bu bo'shliq emas.

## Teskari yo'nalish: repo o'lchaydi, §4 nomlamaydi

Uchta o'lchov ro'yxatda yo'q va uchalasi ham bitta naqshga tushadi —
**o'n ikkala KPI ham botga yoki uzilishning o'ziga tegishli**, mahsulot
esa bot + ommaviy xarita + ommaviy API. So'nggi ikkitasining birorta
KPI si yo'q. Bu 77-run (`01` §25 ommaviy API ni reliz qilmaydi) va
82-run (fazalar ommaviy API ni nomlamaydi) topgan bo'shliqning
uchinchi marta, uchinchi hujjatda takrorlanishi.

Alohida: mahsulotning **butun mazmuni** tasdiqlash (`06`), va §4 da
sifat metrikasi yo'q — «доля вердиктов «данных недостаточно»» `01` §21
da ishga tushirishning **asosiy** metrikasi deb belgilangan
(`dashboards.DASHBOARDS`, `main=True`), §4 da esa umuman yo'q. Ya'ni
paketning ikkita hujjati «главная метрика» ni ikki xil joyda saqlaydi
va §4 ning ro'yxatida u yo'q.

## Nima **qilinmadi** va nima uchun

Hech narsa tuzatilmadi: bu modul o'lchaydi, tahrirlamaydi (75-, 76-,
77-, 82- va 83-runlar bilan bir xil qoida). §4 ning ikkinchi jadvali —
kommersiya metrikalari — bu reyestrga kirmaydi: uning o'zi
«не описывает существующую или планируемую бизнес-модель» deb yozilgan,
ya'ni u KPI emas, **shablon talabiga javob**. Uning yagona tekshiriladigan
da'vosi — ogohlantirish matnining o'zi, va uni kontrakt testi hujjat
tomonidan qulflaydi.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

#: Hujjat bo'limi. `app.admin.registries` shu konstantani o'qiydi.
SPEC = "01 §4"

#: Birinchi jadvalning qatorlari soni. Hujjatdan parse qilinadi va
#: reyestr bilan solishtiriladi (`test_success_metrics_contract`).
SPEC_KPIS = 12

#: Jadval sarlavhasi — aynan.
SPEC_COLUMNS: tuple[str, ...] = (
    "KPI",
    "Baseline (Ташкент)",
    "Статус baseline",
    "Target Ph.1",
    "Статус target",
)

#: Bo'limning o'z ogohlantirishi. Har bir sonning manzili shu jumlada.
WARNING_PHRASE = "Ни одна цифра в этом разделе не является самаркандским измерением"

#: Kommersiya bloki uchun ogohlantirish — ikkinchi jadvalning yagona
#: tekshiriladigan da'vosi.
COMMERCIAL_PHRASE = "не описывает существующую или планируемую бизнес-модель"

#: `Статус target` ustunining gipoteza belgisi.
TAG_HYPOTHESIS = "[ГИПОТЕЗА]"

#: `Статус baseline` ustunining ikkita qiymati. Uchinchisi — `—`, ya'ni
#: baseline umuman yo'q.
TAG_DATA = "[ДАННЫЕ]"
TAG_BASELINE_TAS = "[BASELINE-TAS]"
TAG_NONE = "—"


class Reading(StrEnum):
    """Repo bugun bu KPI ning sonini chiqara oladimi."""

    SERVED = "served"
    DERIVABLE = "derivable"
    EMITTED = "emitted"
    BLIND = "blind"
    UNREACHABLE = "unreachable"
    EXTERNAL = "external"


#: Javob repoda **qurilgan** deb hisoblanadigan sinflar. Faqat `SERVED`:
#: `DERIVABLE` da yig'uvchi yo'q, `EMITTED` da saqlagich yo'q.
READING_ANSWERS: frozenset[Reading] = frozenset({Reading.SERVED})

#: Repo tomonidan yopilishi **mumkin bo'lmagan** sinflar — bu yerda
#: kutilayotgani kod emas, ma'lumot yoki tashqi jarayon.
READING_BLOCKED: frozenset[Reading] = frozenset(
    {Reading.BLIND, Reading.UNREACHABLE, Reading.EXTERNAL}
)


class Target(StrEnum):
    """`Target Ph.1` ustuni nima da'vo qiladi."""

    QUANTIFIED = "quantified"
    DEFERRED = "deferred"
    DISCLAIMED = "disclaimed"


@dataclass(frozen=True)
class Kpi:
    """Jadvalning bitta qatori va uning bugungi bahosi."""

    code: str
    #: Hujjatdagi KPI nomi — **aynan**, tarjimasiz.
    kpi: str
    reading: Reading
    target: Target
    #: Nima uchun aynan shu baho. Keyingi o'quvchi uchun.
    note: str
    #: `Статус baseline` ustunining belgisi: `TAG_DATA`,
    #: `TAG_BASELINE_TAS` yoki `TAG_NONE`. Hujjat bilan ikki tomonlama
    #: qulflanadi.
    baseline_tag: str = TAG_NONE
    #: O'lchagichning dalili: `modul:simvol`. `BLIND` da bo'sh bo'lishi
    #: mumkin — o'lchanadigan narsa yo'q.
    binds: tuple[str, ...] = ()
    #: Ta'rif bilan mavjud o'lchagich orasidagi farq. `SERVED` da ham
    #: bo'lishi mumkin: son chiqadi, lekin boshqa maxrajda.
    gap: str = ""
    #: KPI nomi paketda ta'riflanmagan (butun paketda faqat shu katakda).
    undefined: bool = False

    @property
    def is_answerable(self) -> bool:
        """Repo bu sonni bugun chiqara oladimi."""
        return self.reading in READING_ANSWERS

    @property
    def is_promised(self) -> bool:
        """Qator tekshiriladigan son va'da qiladimi."""
        return self.target is Target.QUANTIFIED

    @property
    def is_broken_promise(self) -> bool:
        """Son va'da qilingan, o'lchagich esa yo'q."""
        return self.is_promised and not self.is_answerable


# --------------------------------------------------------------------------
# Reyestr — `01` §4 ning birinchi jadvali, aynan o'sha tartibda
# --------------------------------------------------------------------------

KPIS: tuple[Kpi, ...] = (
    Kpi(
        code="K-1",
        kpi="MAU бота (регион)",
        reading=Reading.BLIND,
        target=Target.DEFERRED,
        baseline_tag=TAG_DATA,
        note=(
            "«Активный» bot foydalanuvchisi repoda hech qayerda "
            "qayd etilmaydi. `users` da faqat `created_at` bor, ya'ni "
            "**ro'yxatdan o'tish** oyi bo'yicha son chiqadi; takroriy "
            "`/start`, menyu bosishi yoki vitrinani ochish qatorni "
            "o'zgartirmaydi (`get_or_create_user` mavjud qatorga "
            "tegmaydi). `bot_start` hodisasi chiqadi, lekin unda "
            "foydalanuvchi identifikatori yo'q (`01` §20) — ya'ni "
            "hodisalardan ham noyob odamlar sanalmaydi."
        ),
        binds=("app.reports.models:User.created_at",),
        gap=(
            "Bazadan chiqadigan yagona yaqin son — oydagi **yangi** "
            "foydalanuvchilar; MAU undan kichik ham, katta ham bo'lishi "
            "mumkin va nisbat noma'lum."
        ),
    ),
    Kpi(
        code="K-2",
        kpi="DAU/MAU",
        reading=Reading.BLIND,
        target=Target.DEFERRED,
        note=(
            "Ikkala maxraj ham `K-1` bilan bir xil sababdan yo'q. "
            "Alohida qayd: DAU/MAU faolllikning **kunlik** signalini "
            "talab qiladi, repo esa kunlik yig'indini faqat xabarlar "
            "uchun quradi (`app.admin.digest`), ya'ni nisbat "
            "hisoblansa ham u «xabar berganlar / xabar berganlar» "
            "bo'lardi."
        ),
    ),
    Kpi(
        code="K-3",
        kpi="Репортов в месяц",
        reading=Reading.SERVED,
        target=Target.DEFERRED,
        baseline_tag=TAG_DATA,
        note=(
            "Statistika kesimi ixtiyoriy `from`/`to` ni oladi va "
            "`stats_max_period_days = 366`, ya'ni oylik oyna to'g'ridan "
            "to'g'ri so'raladi. Kunlik son alohida ham bor "
            "(`Digest.reports_total`)."
        ),
        binds=(
            "app.stats.aggregate:Bucket.reports_total",
            "app.admin.digest:Digest.reports_total",
        ),
        gap=(
            "Ommaviy vitrinada son **to'liq emas**: `is_public` "
            "chegarasidan o'tmagan hodisalarning xabarlari "
            "`Aggregation.suppressed_reports` ga ketadi va jamiga "
            "kirmaydi. Ya'ni KPI uchun admin tomondagi son olinishi "
            "kerak, vitrinadagi emas — bu farq §4 da yozilmagan."
        ),
    ),
    Kpi(
        code="K-4",
        kpi="Activation (первый репорт ≤7 дней от /start)",
        reading=Reading.DERIVABLE,
        target=Target.DEFERRED,
        note=(
            "Ikkala uchi ham bazada: `/start` qatorni **yaratadi** "
            "(`bot.service.register_user` → `intake.get_or_create_user`), "
            "ya'ni `users.created_at` — aynan `/start` payti; birinchi "
            "xabar esa `min(reports.created_at)` `user_id` bo'yicha. "
            "Yig'adigan kod yo'q, lekin kutiladigan narsa ham yo'q."
        ),
        binds=(
            "app.reports.models:User.created_at",
            "app.reports.models:Report.user_id",
        ),
        gap=(
            "⚠️ `dashboards.activation_funnel` bu KPI ni **DEGRADED** "
            "deb ko'rsatadi (`no_user_dimension`), lekin uning sababi bu "
            "qatorga tegishli emas: hodisalarda identifikator yo'q, "
            "qatorlarda esa bor. Ya'ni voronka javob bera olmaydigan "
            "savolga baza javob beradi."
        ),
    ),
    Kpi(
        code="K-5",
        kpi="Retention D30",
        reading=Reading.DERIVABLE,
        target=Target.DEFERRED,
        note=(
            "`reports` bo'yicha hisoblanadi: `user_id` + `created_at` "
            "juftligi ushlab turish oynasini beradi va "
            "`ix_reports_user_id_created_at` aynan shu so'rov uchun "
            "turibdi."
        ),
        binds=("app.reports.models:Report.user_id",),
        gap=(
            "Ta'rif torayadi: chiqadigan son «30 kundan keyin ham "
            "**xabar bergan**» ni o'lchaydi, «botdan foydalangan» ni "
            "emas. Xaritani ochgan yoki vitrinani o'qigan odam "
            "ushlanmagan hisoblanadi."
        ),
    ),
    Kpi(
        code="K-6",
        kpi="Conversion шага «геолокация»",
        reading=Reading.EMITTED,
        target=Target.DEFERRED,
        note=(
            "Ikkala qadam ham hodisa sifatida chiqariladi "
            "(`report_submit_attempt` → `report_created`), lekin "
            "hodisalar hech qayerda saqlanmaydi: `track.emit` faqat "
            "`log.info` qiladi. Nisbat jurnal stekida quriladi, "
            "repoda emas."
        ),
        binds=(
            "app.analytics.track:report_submit_attempt",
            "app.analytics.track:report_created",
        ),
        gap=(
            "`dashboards.activation_funnel` ning `refusal_invisible` "
            "cheklovi shu qatorga to'liq o'tadi: geo-ruxsatni rad etish "
            "Telegram kanalida kuzatilmaydi, ya'ni maxrajdagi tushishning "
            "sababi ko'rinmaydi."
        ),
    ),
    Kpi(
        code="K-7",
        kpi="Churn (нет активности 60 дней)",
        reading=Reading.DERIVABLE,
        target=Target.DEFERRED,
        note=(
            "`K-5` bilan bir xil manba va bir xil indeks; farq faqat "
            "oynada (60 kun) va yo'nalishda."
        ),
        binds=("app.reports.models:Report.user_id",),
        gap=(
            "«Faollik» yana xabar bilan tenglashtiriladi. Bu yerda "
            "og'ish bir tomonga: churn **yuqori** ko'rinadi, chunki "
            "xabar bermay foydalanadigan odam ketgan deb sanaladi."
        ),
    ),
    Kpi(
        code="K-8",
        kpi="NPS",
        reading=Reading.EXTERNAL,
        target=Target.DEFERRED,
        note=(
            "So'rovnoma mahsulotdan tashqarida o'tkaziladi va bu "
            "normal — `measures.Coverage.EXTERNAL` bilan bir xil rolda. "
            "Repoda na savol, na javob saqlanadi va saqlanishi ham "
            "kerak emas."
        ),
        gap=(
            "⚠️ Katakda son bor — «на выборке ≥100» — lekin u maqsad "
            "emas, **namuna hajmi**. Qator sonli ko'rinadi va sonsiz."
        ),
    ),
    Kpi(
        code="K-9",
        kpi="Time to Value",
        reading=Reading.BLIND,
        target=Target.QUANTIFIED,
        baseline_tag=TAG_BASELINE_TAS,
        undefined=True,
        note=(
            "Ibora butun paketda **bir marta** uchraydi — shu katakda. "
            "Nima o'lchanishi (`/start` dan verdiktgacha? xabardan "
            "javobgacha?) hech qayerda yozilmagan, ya'ni `≤10 с` ni "
            "tekshirish uchun avval ta'rif kerak. Repoda vaqt "
            "o'lchaydigan yagona joy — `obs.latency`, u esa HTTP "
            "sirtining bitta so'rovini o'lchaydi (`TARGET_S = 0.3`) va "
            "foydalanuvchi yo'lini emas."
        ),
        gap=(
            "Bu qator jadvaldagi yagona `[BASELINE-TAS]` + sonli "
            "maqsad juftligi, ya'ni eng «tayyor» ko'rinadigan qator — "
            "va u eng ta'rifsizi."
        ),
    ),
    Kpi(
        code="K-10",
        kpi="Медианная длительность отключения",
        reading=Reading.SERVED,
        target=Target.DISCLAIMED,
        baseline_tag=TAG_BASELINE_TAS,
        note=(
            "`DurationCut.median_min` — vitrinada chiqadi, namuna "
            "yetarli bo'lmasa `None` va chegara javobda ochiq turadi "
            "(`min_sample`)."
        ),
        binds=("app.stats.duration:DurationCut.median_min",),
    ),
    Kpi(
        code="K-11",
        kpi="P90 длительности",
        reading=Reading.SERVED,
        target=Target.DISCLAIMED,
        baseline_tag=TAG_BASELINE_TAS,
        note=(
            "`DurationCut.p90_min`, `K-10` bilan bir xil kesimdan. "
            "Ochiq hodisalar maxrajga kirmaydi va ularning ulushi "
            "ogohlantirish sifatida chiqadi (`WARNING_ONGOING`)."
        ),
        binds=("app.stats.duration:DurationCut.p90_min",),
    ),
    Kpi(
        code="K-12",
        kpi="Coverage Index по махаллям",
        reading=Reading.UNREACHABLE,
        target=Target.QUANTIFIED,
        note=(
            "Maqsadning **semantikasi qurilgan**: «покрытием выше "
            "низкого» `coverage.BAND_THRESHOLDS` da `medium` dan "
            "boshlanadi va `MahallaCoverage.bands` pog'onalar bo'yicha "
            "sonni beradi, ya'ni «≥50% махаллей» ni hisoblash uchun "
            "yozilishi kerak bo'lgan yagona narsa — nisbat. "
            "Yiqiladigani ma'lumot: repoda `mahallas` ga yozadigan yo'l "
            "yo'q (`INSERT INTO` faqat `districts` va "
            "`boundary_staging` ga boradi), ya'ni to'plam har doim bo'sh."
        ),
        binds=(
            "app.stats.coverage:BAND_THRESHOLDS",
            "app.stats.mahalla_coverage:MahallaCoverage.bands",
        ),
        gap=(
            "⚠️ Yaqin atrofda boshqa `0.5` turibdi — "
            "`mahalla_coverage.MIN_MEASURED_RATIO`. U §4 ning maqsadi "
            "**emas**: u o'lchangan mahallalar ulushi uchun "
            "ogohlantirish chegarasi. Ikkala son bir xil ko'rinadi va "
            "turli savollarga javob beradi."
        ),
    ),
)

KPI_BY_CODE: dict[str, Kpi] = {k.code: k for k in KPIS}


@dataclass(frozen=True)
class UnnamedMeasure:
    """Repo o'lchaydi, §4 esa nomlamaydi."""

    code: str
    what: str
    binds: tuple[str, ...]
    why: str


UNNAMED: tuple[UnnamedMeasure, ...] = (
    UnnamedMeasure(
        code="U-1",
        what="«Доля вердиктов «данных недостаточно»»",
        binds=("app.analytics.dashboards:DASHBOARDS",),
        why=(
            "`01` §21 uni **ishga tushirishning asosiy metrikasi** deb "
            "belgilaydi (`Dashboard.main`), §4 da esa mahsulot sifati "
            "haqida birorta qator yo'q. Paketning ikkita hujjati "
            "«главная метрика» ni ikki xil joyda saqlaydi."
        ),
    ),
    UnnamedMeasure(
        code="U-2",
        what="Ommaviy API ning iste'moli",
        binds=("app.release.measures:MEASURES",),
        why=(
            "E15 qurilgan va `03` §11 undan `external_consumers` ni "
            "so'raydi (bugun `Coverage.ABSENT`), §4 da esa ommaviy API "
            "haqida qator yo'q. 77-run buni `01` §25 da, 82-run `01` "
            "§24 da topgan — bu uchinchi hujjat."
        ),
    ),
    UnnamedMeasure(
        code="U-3",
        what="Javob vaqti gistogrammasi va xato ulushi",
        binds=(
            "app.obs.latency:snapshot",
            "app.obs.counters:error_rate",
        ),
        why=(
            "81-run ikkalasini ham qurdi va ular vitrina hamda "
            "ommaviy API uchun yagona sifat signali. §4 ning o'n ikkala "
            "qatori ham botga yoki uzilishning o'ziga tegishli, ya'ni "
            "veb sirti KPI jadvalida umuman yo'q."
        ),
    ),
)


# --------------------------------------------------------------------------
# Hujjatni o'qish
# --------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^##\s+4\.\s+Success Metrics\s*$")
_NEXT_HEADING_RE = re.compile(r"^##\s+")
_ROW_RE = re.compile(r"^\|(?P<cells>.+)\|\s*$")
_SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|$")


class SuccessMetricsError(ValueError):
    """Hujjat kutilgan shaklda emas."""


@dataclass(frozen=True)
class DocRow:
    """Hujjatdagi bitta qator — beshta katak."""

    kpi: str
    baseline: str
    baseline_status: str
    target: str
    target_status: str


def _cells(line: str) -> list[str]:
    match = _ROW_RE.match(line)
    if match is None:  # pragma: no cover — chaqiruvchi oldindan tekshiradi
        raise SuccessMetricsError(f"jadval qatori emas: {line!r}")
    return [cell.strip() for cell in match.group("cells").split("|")]


def section_text(doc: str) -> str:
    """§4 ning matni — sarlavhadan keyingi `##` gacha."""
    lines = doc.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if _HEADING_RE.match(line):
            start = index + 1
            break
    if start is None:
        raise SuccessMetricsError("`## 4. Success Metrics` topilmadi")
    end = len(lines)
    for index in range(start, len(lines)):
        if _NEXT_HEADING_RE.match(lines[index]):
            end = index
            break
    return "\n".join(lines[start:end])


def parse_kpi_table(doc: str) -> tuple[tuple[str, ...], tuple[DocRow, ...]]:
    """§4 ning **birinchi** jadvali: sarlavha + qatorlar.

    Ikkinchi jadval (kommersiya) ataylab olinmaydi: u KPI emas va
    uning ustunlari boshqa (`Метрика | Значение | Комментарий`).
    Ajratish ustunlar soni bo'yicha emas, **birinchi jadval tugagach
    to'xtash** bo'yicha qilinadi — aks holda ustunlar soni tasodifan
    mos kelgan kunda ikkala jadval qo'shilib ketardi.
    """
    header: tuple[str, ...] | None = None
    rows: list[DocRow] = []
    for line in section_text(doc).splitlines():
        stripped = line.strip()
        if not _ROW_RE.match(stripped):
            if header is not None and rows:
                break  # jadval tugadi
            continue
        if _SEPARATOR_RE.match(stripped):
            continue
        cells = _cells(stripped)
        if header is None:
            header = tuple(cells)
            continue
        if len(cells) != len(header):
            raise SuccessMetricsError(f"katak soni sarlavhaga mos emas: {stripped!r}")
        rows.append(DocRow(*cells))
    if header is None:
        raise SuccessMetricsError("§4 da jadval yo'q")
    return header, tuple(rows)


def _check_registry() -> None:
    """Reyestrning ichki qoidalari — import paytida.

    Bular hujjatga tegmaydi: hujjat bilan bog'lash kontrakt testining
    ishi. Bu yerda faqat reyestrning o'zi ziddiyatsizligi tekshiriladi.
    """
    codes = [k.code for k in KPIS]
    if len(set(codes)) != len(codes):
        raise SuccessMetricsError("KPI kodlari takrorlangan")
    if len(KPIS) != SPEC_KPIS:
        raise SuccessMetricsError(f"reyestrda {len(KPIS)} qator, kutilgani {SPEC_KPIS}")
    names = [k.kpi for k in KPIS]
    if len(set(names)) != len(names):
        raise SuccessMetricsError("KPI nomlari takrorlangan")
    allowed_tags = {TAG_DATA, TAG_BASELINE_TAS, TAG_NONE}
    for kpi in KPIS:
        if kpi.baseline_tag not in allowed_tags:
            raise SuccessMetricsError(f"{kpi.code}: noma'lum baseline belgisi")
        if kpi.is_answerable and not kpi.binds:
            raise SuccessMetricsError(f"{kpi.code}: `SERVED`, lekin dalil yo'q")
        if kpi.reading is Reading.EXTERNAL and kpi.binds:
            raise SuccessMetricsError(f"{kpi.code}: `EXTERNAL` da dalil bo'lmaydi")
        if kpi.undefined and kpi.reading is not Reading.BLIND:
            # Ta'rifsiz KPI ni o'lchab bo'lmaydi: o'lchagich bo'lsa,
            # demak kimdir ta'rifni tanlab bo'lgan va u yozilishi kerak.
            raise SuccessMetricsError(f"{kpi.code}: ta'rifsiz, lekin `BLIND` emas")
        if not kpi.note:
            raise SuccessMetricsError(f"{kpi.code}: izohsiz qator")
    unnamed_codes = [u.code for u in UNNAMED]
    if len(set(unnamed_codes)) != len(unnamed_codes):
        raise SuccessMetricsError("teskari yo'nalish kodlari takrorlangan")
    for entry in UNNAMED:
        if not entry.binds:
            raise SuccessMetricsError(f"{entry.code}: dalilsiz")


_check_registry()


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SuccessReport:
    """`01` §4 ning bugungi holati."""

    kpis: tuple[Kpi, ...]
    unnamed: tuple[UnnamedMeasure, ...]

    @property
    def by_reading(self) -> dict[Reading, tuple[str, ...]]:
        result: dict[Reading, list[str]] = {reading: [] for reading in Reading}
        for kpi in self.kpis:
            result[kpi.reading].append(kpi.code)
        return {reading: tuple(codes) for reading, codes in result.items()}

    @property
    def by_target(self) -> dict[Target, tuple[str, ...]]:
        result: dict[Target, list[str]] = {target: [] for target in Target}
        for kpi in self.kpis:
            result[kpi.target].append(kpi.code)
        return {target: tuple(codes) for target, codes in result.items()}

    @property
    def promised(self) -> tuple[Kpi, ...]:
        """Sonli maqsadi bor qatorlar."""
        return tuple(k for k in self.kpis if k.is_promised)

    @property
    def broken_promises(self) -> tuple[Kpi, ...]:
        """Son va'da qilingan, o'lchagich yo'q."""
        return tuple(k for k in self.kpis if k.is_broken_promise)

    @property
    def answerable(self) -> tuple[Kpi, ...]:
        return tuple(k for k in self.kpis if k.is_answerable)

    @property
    def disclaimed(self) -> tuple[Kpi, ...]:
        return tuple(k for k in self.kpis if k.target is Target.DISCLAIMED)

    @property
    def undefined(self) -> tuple[Kpi, ...]:
        """Paket ta'riflamagan KPI nomlari."""
        return tuple(k for k in self.kpis if k.undefined)

    @property
    def regional_baselines(self) -> tuple[str, ...]:
        """Samarqandda o'lchangan baseline lar.

        Bugun **bo'sh** va bo'lim buni o'zi yozadi (`WARNING_PHRASE`).
        Sinf 83-run ning bo'sh `UNBOUND` i bilan bir xil sababdan
        saqlanadi: bo'sh sinf da'voni **o'lchaydigan** joy, va u
        to'lgan kun Faza 0 tugagan kun bo'ladi.
        """
        return ()

    @property
    def answerable_but_disclaimed(self) -> tuple[Kpi, ...]:
        """Repo o'lchaydi, hujjat esa maqsad emas deb yozgan.

        Bosh topilmaning ikkinchi yarmi: bugungi ikkala `SERVED`
        qatori ham shu yerda.
        """
        return tuple(k for k in self.answerable if k.target is Target.DISCLAIMED)

    @property
    def targets_are_answerable(self) -> bool:
        """Sonli har bir maqsad uchun o'lchagich bormi.

        Hisobotning bosh xossasi. Bugun `False`: ikkala sonli maqsad
        ham javobsiz, o'lchanadigan ikkala qator esa maqsad emas.
        """
        return not self.broken_promises

    @property
    def accurate(self) -> bool:
        """§4 bugungi haqiqatni to'g'ri tasvirlaydimi.

        Uchta shart, uchtasi ham mustaqil: sonli maqsadning o'lchagichi
        bo'lsin; KPI nomi paketda ta'riflangan bo'lsin; repo
        o'lchaydigan narsa jadvalda nomsiz qolmasin.
        """
        return self.targets_are_answerable and not self.undefined and not self.unnamed


def evaluate() -> SuccessReport:
    """Reyestrdan to'liq hisobot.

    Argument **yo'q**: javob kodning tuzilishidan keladi
    (`glossary.evaluate` va `roadmap.evaluate` bilan bir xil sabab).
    """
    return SuccessReport(kpis=KPIS, unnamed=UNNAMED)
