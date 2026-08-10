"""`03` §11 «Nima o'lchanadi» ↔ mahsulotning haqiqiy o'lchovlari.

**Nima uchun bu modul bor.** `03` §11 — rejaning oxirgi jadvali va u
boshqa hamma jadvaldan farq qiladi: u nima **qurilishini** emas, nima
**kuzatilishini** aytadi. Yetti bosqich, o'n to'rtta ko'rsatkich. Shu
paytgacha bu jadval hujjatda qolib kelgan va uning bilan `05` §10
metrikalar reyestri o'rtasida hech qanday bog'lanish yo'q edi — ya'ni
«R1.0 da Time-to-answer p90 kuzatiladi» degan jumla **hech qayerda
tekshirilmasdi**.

66-run shu bo'shliqning bitta uchini ko'rdi: G-5 mezoni `answer_p90`
uchun `05` §10 da metrika yo'q ekan. Bu modul o'sha savolni butun
jadvalga beradi va javobni **kodda** saqlaydi.

## Bu modul sonlarni ko'rsatmaydi

`gates.py` bugungi qiymatni oladi va «yopiqmi?» deb so'raydi. Bu yerda
savol boshqa: *bu ko'rsatkichni umuman o'lchay olamizmi?* Javob jonli
ma'lumotga bog'liq emas — u kodning tuzilishiga bog'liq, ya'ni modul
bazaga ham, `settings` ga ham tegmaydi va hisobot so'rov paytida
hisoblanmaydi. Asbob haqidagi hisobot, ko'rsatish haqidagi emas.

## To'rtta holat, ikkitasi emas

«O'lchanadi / o'lchanmaydi» ikkiligi eng muhim farqni yo'qotardi —
**bo'shliqni yopish narxini**:

* `MEASURED` — bugun raqam bor, manbasi ko'rsatilgan;
* `DERIVABLE` — ma'lumot bazada yotibdi, uni chiqaradigan so'rov yo'q
  (narxi — bitta so'rov);
* `ABSENT` — ma'lumotning **o'zi** yozilmaydi (narxi — yangi ustun,
  yangi hodisa yoki mahsulot qarori);
* `EXTERNAL` — mahsulot kodi buni hech qachon o'lchamaydi va o'lchashi
  ham kerak emas (deploy chastotasi CI/CD da).

`EXTERNAL` `ABSENT` bilan qo'shilib ketsa, hisobot ikkita deploy
ko'rsatkichini abadiy «bo'shliq» deb ko'rsatib turardi va odam butun
ro'yxatga ishonishni to'xtatardi.

## Eng qimmatli maydon — `near`

Har bir yopilmagan ko'rsatkich uchun **eng yaqin mavjud o'lchov**
yozilgan, va u «bog'lanish» emas, **ogohlantirish**: ularni
tenglashtirish bo'shliqni yopmaydi, faqat ko'rinmas qiladi. Uchta
misol, uchalasi ham shu runda topilgan:

* `answer_p90` ↔ `time_to_confirm_seconds` — ikkinchisi hodisa qachon
  **tasdiqlangani** ni o'lchaydi, foydalanuvchi savoliga qachon javob
  berilganini emas (66-run topgan);
* `matching_reports` ↔ `geo_unmatched_ratio` — nomida «unmatched»
  bo'lsa ham, u `district_id IS NULL` ni sanaydi, ya'ni **poligon
  sifati**; hodisaga biriktirilmagan xabar (`reports.outage_id IS
  NULL`) butunlay boshqa narsa;
* `notify_delivery_time` ↔ `outbox_lag_seconds` — navbatning yoshi
  yetkazish vaqti emas (`sent_at − confirmed_at` hech qayerda
  hisoblanmaydi).

## Ikkita mahsulot topilmasi

1. **`moderation_sla` — `ABSENT`, `DERIVABLE` emas.** Audit jurnalida
   `outage.reject` va `outage.merge` qatorlari vaqti bilan yotadi,
   ya'ni **qaror qabul qilingan** hodisalarning kutish vaqtini
   hisoblasa bo'ladi. Lekin SLA aynan qaror **qabul qilinmagan**
   navbat haqida: hodisa ko'rikka qachon tushgani hech qayerda
   saqlanmaydi (`needs_review` javob paytida hisoblanadi, `05` §4.2),
   ya'ni faqat yopilganlar bo'yicha o'lchangan SLA tizimli ravishda
   **yaxshi tomonga** yolg'on gapirardi.
2. **`autoconfirm_share` — bugun ma'nosiz.** `05` §4.4 status
   mashinasida `pending → confirmed` **faqat** `independent_reporters
   >= min_reporters` orqali o'tadi; moderator hodisani tasdiqlay
   olmaydi (`AuditAction` da `outage.reject` va `outage.merge` bor,
   `outage.confirm` — yo'q, garchi `05` §2.5 uni misol qilib
   keltirsa ham). Ya'ni avtotasdiqlash ulushi qurilishiga ko'ra
   `1.0`, va uni «o'lchash» tavtologiya bo'lardi. Bu — kod
   kamchiligi emas, **hujjatlar orasidagi ziddiyat**
   (`PROGRESS.md` «Ochiq savollar»).

Modul **toza**: faqat `app.obs.metrics` va `app.release.gates` ga
bog'lanadi (ikkalasi ham toza), foydalanuvchi matni yo'q — barcha
sarlavha `release.measure.*` / `release.stage.*` kalitlaridan.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.obs import metrics
from app.release import gates

#: i18n kalitlarining prefikslari. Kalitlar `MEASURE_KEYS`/`STAGE_KEYS`
#: da **ochiq** sanaladi (`tests/test_i18n_key_contract.py` ning
#: `KEY_TABLES` naqshi): f-satrdan yig'ilgan kalit skaner uchun
#: ko'rinmas bo'lardi.
MEASURE_KEY_PREFIX = "release.measure"
STAGE_KEY_PREFIX = "release.stage"

#: Bu jadvalning hujjatdagi manzili. `gates.Criterion.spec` bilan bir
#: xil rolda: hisobotni o'qiyotgan odam qaysi bandga qaytishini biladi.
SPEC = "03 §11"


class Source(StrEnum):
    """Raqam **bugun** qayerdan keladi.

    `NONE` — hech qayerdan. U `Binding` da faqat `near` bo'sh bo'lgan
    holatni ifodalash uchun emas, umuman ishlatilmaydi: bog'lanish
    yo'q bo'lsa `Binding` ning o'zi `None`. `NONE` reyestrni
    tekshirishda kerak (`_check_registry`).
    """

    #: `05` §10 metrikalar registri (`app.obs.metrics.FAMILIES`).
    METRIC = "metric"
    #: Ommaviy vitrina (`app/stats`), `module:attr` ko'rinishida.
    STATS = "stats"
    #: `03` §6 gate mezoni (`app.release.gates.CRITERION_BY_CODE`).
    GATE = "gate"
    NONE = "none"


class Coverage(StrEnum):
    """Ko'rsatkichni o'lchash uchun bugun nima yetishmaydi.

    Tartib **ma'noli**: `MEASURED` dan `ABSENT` ga qarab bo'shliqni
    yopish narxi o'sadi. `EXTERNAL` bu o'qda emas — u umuman boshqa
    javob: «bu yerda o'lchanmaydi va o'lchanmasligi kerak».
    """

    MEASURED = "measured"
    DERIVABLE = "derivable"
    ABSENT = "absent"
    EXTERNAL = "external"


#: Bo'shliq deb hisoblanadigan holatlar. `EXTERNAL` kirmaydi: CI/CD
#: ko'rsatkichini mahsulot kodidan talab qilish ro'yxatni abadiy
#: qizil qoldirardi va qolgan o'n ikkitasini ko'rinmas qilardi.
GAP_COVERAGES: frozenset[Coverage] = frozenset({Coverage.DERIVABLE, Coverage.ABSENT})


@dataclass(frozen=True)
class Binding:
    """Bitta o'lchovga havola: qaysi reyestrda va qaysi nom bilan."""

    source: Source
    ref: str

    def __str__(self) -> str:  # hisobotda bitta satr bo'lib chiqadi
        return f"{self.source}:{self.ref}"


@dataclass(frozen=True)
class Stage:
    """`03` §11 ning «Bosqich» ustuni.

    Tartib reliz tartibi bilan bir xil, va u `first_gap` ning asosi:
    qatorlar joy almashsa hisobot boshqa bosqichni «birinchi bo'shliq»
    deb ko'rsatardi va bu **to'g'ri ko'rinardi**.
    """

    code: str

    @property
    def key(self) -> str:
        return f"{STAGE_KEY_PREFIX}.{self.code}"

    @property
    def rationale_key(self) -> str:
        """«Nima uchun» ustuni — ko'rsatkich emas, uning sababi."""
        return f"{STAGE_KEY_PREFIX}.{self.code}.why"


@dataclass(frozen=True)
class Measure:
    """`03` §11 ning bitta ko'rsatkichi.

    `bound` **faqat** `MEASURED` da to'ldiriladi, `near` esa faqat
    qolganlarida: ikkalasini bir maydonga qo'shish hisobotni
    o'qiydigan odamga «bog'langan» va «bog'lash mumkin emas» ni bir
    xil ko'rsatardi — bu esa bu modulning butun ma'nosiga zid.
    """

    code: str
    stage: str
    coverage: Coverage
    bound: Binding | None = None
    near: tuple[Binding, ...] = ()

    @property
    def key(self) -> str:
        return f"{MEASURE_KEY_PREFIX}.{self.code}"

    @property
    def is_gap(self) -> bool:
        return self.coverage in GAP_COVERAGES


# --------------------------------------------------------------------------
# Reyestr — `03` §11 jadvali, aynan o'sha tartibda
# --------------------------------------------------------------------------

STAGES: tuple[Stage, ...] = (
    Stage("m0_r03"),
    Stage("pilot"),
    Stage("r10"),
    Stage("r11"),
    Stage("r12"),
    Stage("r20"),
    Stage("always"),
)

STAGE_BY_CODE: dict[str, Stage] = {stage.code: stage for stage in STAGES}


def _metric(name: str) -> Binding:
    return Binding(Source.METRIC, name)


def _stats(ref: str) -> Binding:
    return Binding(Source.STATS, ref)


def _gate(code: str) -> Binding:
    return Binding(Source.GATE, code)


MEASURES: tuple[Measure, ...] = (
    # ---- M0–R0.3 · «Muhandislik salomatligi» -----------------------------
    # Ikkalasi ham quvurning o'zi haqida: mahsulot kodi deploy
    # bo'lganini bilmaydi va bilishi ham kerak emas. G-0 ning
    # `deploy_pipeline` mezoni ham aynan shu sababdan `MANUAL`.
    Measure("deploy_frequency", "m0_r03", Coverage.EXTERNAL),
    Measure("pipeline_duration", "m0_r03", Coverage.EXTERNAL),
    # ---- Yopiq bosqich · «G-4 kirishi» -----------------------------------
    # `reports.outage_id` nullable, ya'ni son bitta `COUNT(*)` bilan
    # olinadi — lekin bunday so'rov yo'q. Eng yaqin ikkitasi ham
    # boshqa narsani sanaydi va aynan shuning uchun xavfli.
    Measure(
        "matching_reports",
        "pilot",
        Coverage.DERIVABLE,
        near=(_metric(metrics.GEO_UNMATCHED.name), _gate("confirmable_share")),
    ),
    # Mezon reyestrda bor, lekin `collector` unga **ataylab** `None`
    # beradi: «hudud ulushi» maydon bo'yicha o'lchanishi kerak, tuman
    # soni bo'yicha emas. Ustiga chegarasi ham yo'q (`N` Faza 0 dan).
    Measure(
        "reported_area_share",
        "pilot",
        Coverage.ABSENT,
        near=(_gate("reported_area_share"),),
    ),
    # ---- R1.0 · «Mahsulot va'dasi» ---------------------------------------
    # 66-run topgan bo'shliq: `03` §4 R1.0 ham, §11 ham talab qiladi,
    # `05` §10 da esa metrika yo'q.
    Measure(
        "answer_p90",
        "r10",
        Coverage.ABSENT,
        near=(_metric(metrics.TIME_TO_CONFIRM.name), _gate("answer_p90")),
    ),
    Measure(
        "map_refresh_lag",
        "r10",
        Coverage.MEASURED,
        bound=_metric(metrics.SNAPSHOT_AGE.name),
    ),
    # ---- R1.1 · «Foydalanuvchini yo'qotmaslik» ---------------------------
    # `notifications.sent_at` ham, `outages.confirmed_at` ham bor —
    # ayirma bitta so'rov. `outbox_lag_seconds` esa navbatning yoshi:
    # u navbat bo'sh bo'lganda ham nol bo'ladi, yetkazish esa sekin
    # bo'lishi mumkin.
    Measure(
        "notify_delivery_time",
        "r11",
        Coverage.DERIVABLE,
        near=(_metric(metrics.OUTBOX_LAG.name), _gate("notify_delivery_p90")),
    ),
    # O'chirish yumshoq (`subscriptions.is_active = false`), ya'ni
    # ulush hozirgi holat uchun hisoblanadi. ⚠️ `deactivated_at` yo'q,
    # shuning uchun **davr kesimida** (oyma-oy) bu son chiqmaydi —
    # faqat joriy nisbat.
    Measure("unsubscribe_share", "r11", Coverage.DERIVABLE),
    # ---- R1.2 · «Ma'lumotga ishonch» -------------------------------------
    Measure(
        "aggregate_diff",
        "r12",
        Coverage.MEASURED,
        bound=_stats("app.stats.aggregate:Aggregation.reconciles"),
    ),
    # Taqsimot **bor** va aynan taqsimot sifatida: `MahallaCoverage.bands`
    # pog'onalar bo'yicha sanoq beradi (`01` §21 dashboardi).
    Measure(
        "coverage_distribution",
        "r12",
        Coverage.MEASURED,
        bound=_stats("app.stats.mahalla_coverage:MahallaCoverage.bands"),
    ),
    # ---- R2.0 · «Ochiqlik» -----------------------------------------------
    # `http_requests_total` faqat status sinfini sanaydi — javob vaqti
    # hech qayerda o'lchanmaydi, ya'ni p95 uchun gistogramma kerak.
    Measure(
        "api_p95",
        "r20",
        Coverage.ABSENT,
        near=(_metric(metrics.HTTP_REQUESTS.name),),
    ),
    # Ommaviy API da iste'molchining identifikatori yo'q (kalit ham,
    # token ham). «Nechta tashqi foydalanuvchi» — bu o'lchov emas,
    # avval mahsulot qarori.
    Measure("external_consumers", "r20", Coverage.ABSENT),
    # ---- Doimiy · «Operatsion masshtablanuvchanlik» ----------------------
    # Modul docstringidagi 1-topilma: navbatga tushish vaqti
    # saqlanmaydi, faqat qaror qabul qilinganlar iz qoldiradi.
    Measure(
        "moderation_sla",
        "always",
        Coverage.ABSENT,
        near=(_gate("moderation_sla"),),
    ),
    # 2-topilma: `05` §4.4 da moderator tasdiqlay olmaydi, ya'ni ulush
    # qurilishiga ko'ra `1.0`.
    Measure("autoconfirm_share", "always", Coverage.ABSENT),
)

MEASURE_BY_CODE: dict[str, Measure] = {m.code: m for m in MEASURES}

#: Katalogdan so'raladigan kalitlar, **literal** ro'yxat sifatida.
MEASURE_KEYS: tuple[str, ...] = tuple(m.key for m in MEASURES)
STAGE_KEYS: tuple[str, ...] = tuple(
    key for stage in STAGES for key in (stage.key, stage.rationale_key)
)


def _check_registry() -> None:
    """Reyestrning **jimgina** buziladigan to'rtta joyi.

    Hammasi import paytida: har biri hisobotni to'g'ri **ko'rinishda**
    qoldiradi va faqat qatorlarni diqqat bilan o'qiganda bilinadi.
    """
    codes = [m.code for m in MEASURES]
    duplicates = sorted({code for code in codes if codes.count(code) > 1})
    if duplicates:
        # Nusxa bo'lsa `MEASURE_BY_CODE` bittasini yutardi.
        raise ValueError(f"ko'rsatkich kodi takrorlangan: {duplicates}")

    unknown = sorted({m.stage for m in MEASURES if m.stage not in STAGE_BY_CODE})
    if unknown:
        raise ValueError(f"notanish bosqich: {unknown}")

    empty = [s.code for s in STAGES if not any(m.stage == s.code for m in MEASURES)]
    if empty:
        # Ko'rsatkichsiz bosqich hisobotda «bo'shliq yo'q» bo'lib
        # ko'rinardi — hech narsa tekshirmagani uchun.
        raise ValueError(f"bosqich ko'rsatkichsiz: {empty}")

    for measure in MEASURES:
        measured = measure.coverage is Coverage.MEASURED
        if measured and measure.bound is None:
            # «O'lchanadi» degan da'vo manbasiz — bu aynan `gates.py`
            # ogohlantirgan yumshatishning shakli.
            raise ValueError(f"`{measure.code}`: MEASURED, lekin manbasi yo'q")
        if not measured and measure.bound is not None:
            raise ValueError(f"`{measure.code}`: manbasi bor, lekin MEASURED emas")
        if measured and measure.near:
            # Bog'langan ko'rsatkichda «eng yaqin» ogohlantirishining
            # ma'nosi yo'q va u faqat chalg'itardi.
            raise ValueError(f"`{measure.code}`: MEASURED da `near` bo'lmaydi")
        bound = (measure.bound,) if measure.bound is not None else ()
        for binding in (*bound, *measure.near):
            _check_binding(measure.code, binding)


#: `05` §10 registridagi nomlar — havolani tekshirish uchun.
_METRIC_NAMES: frozenset[str] = frozenset(f.name for f in metrics.FAMILIES)


def _check_binding(code: str, binding: Binding) -> None:
    """Havola haqiqiy reyestrga tushishini tekshiradi.

    Yozuv xatosi bilan kelgan havola hisobotni **boyroq** qilib
    ko'rsatardi: qator bor, nom bor, faqat u hech narsaga
    bog'lanmagan.
    """
    if binding.source is Source.METRIC:
        if binding.ref not in _METRIC_NAMES:
            raise ValueError(f"`{code}`: `05` §10 da bunday metrika yo'q — {binding.ref}")
    elif binding.source is Source.GATE:
        if binding.ref not in gates.CRITERION_BY_CODE:
            raise ValueError(f"`{code}`: `03` §6 da bunday mezon yo'q — {binding.ref}")
    elif binding.source is Source.STATS:
        # Import qilib tekshirilmaydi: `app.stats` bazaga bog'liq
        # modullarni tortadi va bu modulning tozaligini buzardi.
        # Havolaning **haqiqiyligi** kontrakt testida tekshiriladi.
        if ":" not in binding.ref:
            raise ValueError(f"`{code}`: `stats` havolasi `modul:atribut` bo'lishi kerak")
    else:
        raise ValueError(f"`{code}`: bog'lanishda `Source.NONE` ishlatilmaydi")


_check_registry()


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class MeasureReport:
    """Butun jadvalning bugungi holati.

    Hisobot **statik**: u jonli ma'lumotdan emas, reyestrdan
    chiqadi. Shuning uchun `evaluate()` argumentsiz va uni har
    so'rovda qayta chaqirish arzon.
    """

    measures: tuple[Measure, ...]

    @property
    def counts(self) -> dict[str, int]:
        """Holat → nechta ko'rsatkich. Nol bo'lgani ham qoladi."""
        result = {str(c): 0 for c in Coverage}
        for measure in self.measures:
            result[str(measure.coverage)] += 1
        return result

    @property
    def gaps(self) -> tuple[Measure, ...]:
        return tuple(m for m in self.measures if m.is_gap)

    @property
    def first_gap(self) -> Measure | None:
        """Reliz tartibidagi **birinchi** yopilmagan ko'rsatkich.

        Hisobotning javobi: undan keyingi bosqichlarni o'lchash haqida
        gapirishdan oldin shuni yopish kerak. `EXTERNAL` bu yerga
        tushmaydi.
        """
        for stage in STAGES:
            for measure in self.measures:
                if measure.stage == stage.code and measure.is_gap:
                    return measure
        return None

    def for_stage(self, code: str) -> tuple[Measure, ...]:
        return tuple(m for m in self.measures if m.stage == code)


def evaluate() -> MeasureReport:
    """`03` §11 jadvali, reliz tartibida."""
    order = {stage.code: i for i, stage in enumerate(STAGES)}
    return MeasureReport(measures=tuple(sorted(MEASURES, key=lambda m: order[m.stage])))
