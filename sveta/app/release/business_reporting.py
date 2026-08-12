"""Hisobot va muvaffaqiyat reyestri (`BRD` §20–§21) ↔ qurilgan mahsulot.

**Nima uchun bu modul bor.** 104-run BRD §18–§19 ni bog'ladi va §20–§23 ni
keyingi nomzod deb qoldirdi. Hajm katta chiqdi — bu run §20–§21 ni oladi
(Reporting: 6 hisobot + 4 dashboard + 7 KPI; Success Metrics: 8 daraja),
§22–§23 (Acceptance, Timeline) keyingi runga qoladi. Bu ikki bo'lim —
hujjatning **o'lchov** sathi: mahsulot nimani ko'rsatishi (§20) va nimasi
bilan muvaffaqiyatli sanalishi (§21) shu yerda va'da qilinadi.

## Birinchi topilma: §21 ning o'z yakuni bugun bajarilmaydi

BRD §22 oxiri loyihani «метрики §21 измерены» bo'lsa muvaffaqiyatli deb
e'lon qiladi — qiymatiga emas, **o'lchanganiga** qaraydi. Lekin sakkiz
qatordan uchtasi bugungi mahsulotda o'lchab **bo'lmaydi**: Time-to-answer
p90 (`05` §10 jadvalida bunday metrika yo'q — `app/release/collector.py`
ning ataylab `None` qatori), UZ-sessiyalar ulushi («sessiya» tushunchasi
kodda yo'q — `analytics.dashboards` ning `session_is_undefined` chegarasi)
va moderatsiya SLA si (o'lchov mexanizmi umuman yo'q). Ya'ni «o'lchanuvchanlik
mezoni» hozircha uch qatorda yiqiladi — bu §22 ga o'tishdan oldin hal
qilinishi kerak bo'lgan savol (👤).

## Ikkinchi topilma: avtotasdiq KPI si o'z-o'zidan bajariladi

§20.3 «Доля автоподтверждённых инцидентов ≥60%» KPI si moderator qo'li
bilan tasdiqlash yo'lini nazarda tutadi — aks holda «avtomatik ulush»
degan savol ma'nosiz. 104-run ko'rsatganidek kodda qo'lda «подтверждение»
YO'Q (`05` §4.4 — tasdiqlash faqat avtomatik): tasdiqlanganlarning 100% i
avtomatik, KPI qurilish bo'yicha ≥60%. Bu §19 moderator topilmasining
egizagi: hujjat mavjud bo'lmagan yo'lni o'lchamoqchi.

## Uchinchi topilma: «расхождение агрегатов» ni solishtiradigan ikkinchi son yo'q

§20.3 va §21 dagi «Расхождение агрегатов ≤5%» (`BASELINE-TAS`) ikki
mustaqil yig'indini taqqoslashni nazarda tutadi: hududlar summasi ↔ region
jami. Qurilgan vitrinada ikkalasi **bitta** manbadan chiqadi
(`app.stats.aggregate` — bitta o'tishda buketlarga yig'iladi), taqqoslash
uchun mustaqil ikkinchi hisob yo'q. Metrika Toshkent merosidan ko'chirilgan
va bu arxitekturada o'lchov sifatida bo'sh: farq ta'rif bo'yicha 0.

## To'rtinchi topilma: «sifat» hisoboti va dashboardining uch soni ham yetim

§20.1 haftalik «Отчёт качества данных» va §20.2 «Качества данных»
dashboardi uchta son so'raydi: modernatsiyadagi ulush, dubllar ulushi,
agregatlar farqi. Uchalasi ham bugun yig'ilmaydi: dubl «ulushi» yo'q
(merge bor, hisob yo'q), farq — yuqoridagidek ta'rifan bo'sh, moderatsiya
ulushi hech qayerda ko'rsatilmaydi. Hisobot ham, dashboard ham `ABSENT`.

## O'qish tartibi

To'rt jadval hujjatdagi tartibda: `REPORTS` (§20.1), `DASHBOARDS_ROWS`
(§20.2), `KPIS` (§20.3), `METRICS` (§21). Har qator hujjat katagini aynan
saqlaydi (kontrakt test hujjatdan qayta o'qiydi), baho esa kod dalili
(`binds`) bilan yuradi. `evaluate()` — yig'ma hisobot,
`app.admin.registries` indeksi shu orqali o'qiydi.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.analytics import dashboards as adash
from app.release import business_interfaces as bifc

#: Hujjat bo'limlari. `app.admin.registries` shu konstantani o'qiydi.
SPEC = "BRD §20–§21"

#: Jadval o'lchamlari — hujjatdan parse qilinadi va solishtiriladi.
SPEC_REPORT_ROWS = 6
SPEC_DASHBOARD_ROWS = 4
SPEC_KPI_ROWS = 7
SPEC_METRIC_ROWS = 8

#: §21 dagi daraja ustuni — hujjatdagi tartibda, takror bilan.
SPEC_METRIC_LEVELS: tuple[str, ...] = (
    "Продуктовый",
    "Продуктовый",
    "Данные",
    "Данные",
    "Аудитория",
    "Локализация",
    "Операционный",
    "Стратегический",
)

#: §21 izohi va §22 yakuni tayanadigan ibora — «o'lchanganlik» mezoni.
MEASURABILITY_CLAUSE = "метрики §21 измерены"

#: `analytics.dashboards` dagi UZ-sessiya chegaralari — «sessiya yo'q»
#: topilmasining dalili. Yo'qolsa, qorovul yiqiladi (topilma eskirgan).
UZ_SESSION_LIMITS: tuple[str, ...] = ("detected_is_not_chosen", "session_is_undefined")


class Claim(StrEnum):
    """§20.3 «Статус» katagining sinfi (BRD §0 belgilash tizimi)."""

    #: `ГИПОТЕЗА` — taxmin, Faza 0 tekshiradi.
    HYPOTHESIS = "hypothesis"
    #: `BASELINE-TAS` — Toshkent bazasidan ko'chirilgan bilim.
    BASELINE = "baseline"
    #: `ОЦЕНКА` — ekspert bahosi, empirik asossiz.
    ESTIMATE = "estimate"


def classify_status(cell: str) -> Claim:
    """`Статус` katagini sinfga o'giradi. Test hujjatdan qayta chaqiradi."""
    if "ГИПОТЕЗА" in cell:
        return Claim.HYPOTHESIS
    if "BASELINE-TAS" in cell:
        return Claim.BASELINE
    if "ОЦЕНКА" in cell:
        return Claim.ESTIMATE
    raise ValueError(f"{SPEC}: notanish status katagi: {cell!r}")


class Build(StrEnum):
    """§20.1–§20.2 qatorining qurilgan mahsulotdagi holati."""

    #: So'rov yo'li to'liq ishlaydi.
    LIVE = "live"
    #: Bir qismi bor, bir qismi yo'q — farq `gap` da.
    PARTIAL = "partial"
    #: Mexanizm tayyor, natija tashqi hodisani (mas. Faza 0) kutadi.
    PROVISIONED = "provisioned"
    #: Kodda hech narsa yo'q.
    ABSENT = "absent"


class Meter(StrEnum):
    """§20.3/§21 sonining o'lchanish holati."""

    #: So'rov yoki metrika bugun qiymat beradi.
    MEASURED = "measured"
    #: Xom ma'lumot bor, son hech qayerda ko'rsatilmaydi.
    DERIVABLE = "derivable"
    #: Qurilish bo'yicha ma'nosiz — o'lchashga hech narsa qolmagan.
    MOOT = "moot"
    #: Son emas, odam hukmi.
    MANUAL = "manual"
    #: O'lchov mexanizmi yo'q.
    UNMEASURED = "unmeasured"


class BusinessReportingError(RuntimeError):
    """Reyestrning ichki qarama-qarshiligi."""


@dataclass(frozen=True)
class ReportRow:
    """§20.1 ning bitta qatori — kataklar hujjat so'zlari bilan aynan."""

    name: str
    audience: str
    cadence: str
    build: Build
    note: str
    binds: tuple[str, ...] = ()
    gap: str = ""


@dataclass(frozen=True)
class DashboardRow:
    """§20.2 ning bitta qatori."""

    name: str
    content: str
    build: Build
    note: str
    binds: tuple[str, ...] = ()
    gap: str = ""


@dataclass(frozen=True)
class KpiRow:
    """§20.3 ning bitta qatori. `status` — hujjat katagi aynan."""

    kpi: str
    definition: str
    target: str
    status: str
    meter: Meter
    note: str
    binds: tuple[str, ...] = ()
    gap: str = ""

    @property
    def claim(self) -> Claim:
        return classify_status(self.status)


@dataclass(frozen=True)
class MetricRow:
    """§21 ning bitta qatori. `failure` — «Что означает провал» katagi."""

    level: str
    metric: str
    failure: str
    meter: Meter
    note: str
    binds: tuple[str, ...] = ()
    gap: str = ""


# --------------------------------------------------------------------------
# §20.1 — hisobotlar, hujjatdagi tartibda
# --------------------------------------------------------------------------

REPORTS: tuple[ReportRow, ...] = (
    ReportRow(
        name="Сводка по региону: инциденты, длительность, география",
        audience="Публика, СМИ",
        cadence="Реальное время + периодические срезы",
        build=Build.LIVE,
        note=(
            "To'liq bor: davr kesimlari bilan vitrina (`build_report`), "
            "xarita snapshoti (GeoJSON) va CSV eksport dislaymeri bilan. "
            "Real vaqt ham, davriy srez ham bitta so'rov yo'lidan chiqadi."
        ),
        binds=(
            "app.stats.service:build_report",
            "app.clustering.snapshot:build_payload",
            "app.stats.export:render",
        ),
    ),
    ReportRow(
        name="Разрез по махаллям с Coverage Index",
        audience="Публика, аналитики",
        cadence="Реальное время",
        build=Build.LIVE,
        note=(
            "Mahalla kesimi va Coverage Index hisoblanadi va vitrinada "
            "ko'rinadi; spravochnik bo'sh muhitda vitrina buni yashirmaydi "
            "(`MahallaCoverage.available=False` — `01` §21 reyestridagi "
            "`registry_unavailable` chegarasi)."
        ),
        binds=(
            "app.stats.service:mahalla_index",
            "app.stats.mahalla_coverage:summarize",
        ),
    ),
    ReportRow(
        name=(
            "Отчёт качества данных: доля модерируемых, доля дублей, "
            "расхождение агрегатов"
        ),
        audience="Команда, PO",
        cadence="Еженедельно",
        build=Build.ABSENT,
        note=(
            "Uchala son ham yig'ilmaydi: moderatsiya ulushi hech qayerda "
            "ko'rsatilmaydi, dubl «ulushi» yo'q (merge bor, hisob yo'q), "
            "agregatlar farqi bitta manba arxitekturasida ta'rifan bo'sh "
            "(uchinchi topilma). Haftalik jo'natish mexanizmi ham yo'q."
        ),
        gap="Hisobotning uch soni ham o'lchanmaydi, haftalik kanal ham yo'q (👤).",
    ),
    ReportRow(
        name="Отчёт Фазы 0: результаты проверки H-1…H-5",
        audience="PO, спонсор",
        cadence="Однократно, по завершении Ph.0",
        build=Build.PROVISIONED,
        note=(
            "Gipoteza reyestri kodda (H-1…H-5 posturasi bilan), ya'ni "
            "hisobotning skeleti tayyor — lekin Faza 0 dala ishi odamniki "
            "va o'tkazilmagan, natija katagi bo'sh."
        ),
        binds=("app.release.phase0_plan:Hypothesis",),
        gap="Ph.0 o'tkazilmagan — «результаты проверки» hali mavjud emas (👤).",
    ),
    ReportRow(
        name="Операционный отчёт модерации: очередь, SLA, доля отменённых решений",
        audience="Команда",
        cadence="Еженедельно",
        build=Build.PARTIAL,
        note=(
            "Navbat kunlik digestda bor (`queue_now`), audit jurnali ham "
            "bor. Lekin SLA hech qayerda o'lchanmaydi (`03` §11 ning ma'lum "
            "qarzi) va «отменённое решение» tushunchasi kodda yo'q — "
            "qarorni bekor qilish yo'li ham, uning ulushi ham."
        ),
        binds=("app.admin.digest:Digest", "app.admin.audit"),
        gap="SLA va bekor qilingan qarorlar ulushi o'lchanmaydi.",
    ),
    ReportRow(
        name="Отчёт о территориальных изменениях",
        audience="Команда, аналитики",
        cadence="По событию",
        build=Build.LIVE,
        note=(
            "Chegara versiyalanishi hodisalari yig'iladi va davr bo'yicha "
            "xulosalanadi (`BoundarySet`) — aynan «по событию» hisobot."
        ),
        binds=("app.stats.boundaries:summarize",),
    ),
)


# --------------------------------------------------------------------------
# §20.2 — dashboardlar, hujjatdagi tartibda
# --------------------------------------------------------------------------

DASHBOARDS_ROWS: tuple[DashboardRow, ...] = (
    DashboardRow(
        name="Публичный региональный",
        content=(
            "Карта, активные инциденты, медианная и P90 длительность, "
            "Coverage Index"
        ),
        build=Build.LIVE,
        note=(
            "Ochiq vitrina to'rt tarkibni ham beradi: xarita (snapshot + "
            "web), faol hodisalar, mediana/P90 (davomiylik kesimi), "
            "Coverage Index."
        ),
        binds=(
            "app.stats.service:region_index",
            "app.stats.duration",
            "app/api/v1/stats.py",
        ),
    ),
    DashboardRow(
        name="Операционный",
        content=(
            "Очередь модерации, аномалии объёма, состояние источников, "
            "лаг обработки"
        ),
        build=Build.PARTIAL,
        note=(
            "Bo'laklari bor — navbat (digest), laglar (`outbox_lag`, "
            "`snapshot_age`), alertlar — lekin yagona operatsion sirt yo'q "
            "va «аномалии объёма» hech qayerda aniqlanmaydi."
        ),
        binds=("app.admin.digest:Digest", "app.obs.metrics:OUTBOX_LAG"),
        gap="Yagona sirt yo'q; hajm anomaliyalari umuman aniqlanmaydi.",
    ),
    DashboardRow(
        name="Качества данных",
        content=(
            "Расхождение сумм по территориям, доля дублей, доля привязок "
            "к махалле"
        ),
        build=Build.ABSENT,
        note=(
            "§20.1 sifat hisobotining egizagi (to'rtinchi topilma): uchala "
            "son ham yig'ilmaydi. Eng yaqin metrika — `geo_unmatched_ratio` "
            "— tuman darajasida, mahalla emas."
        ),
        gap="Uch sonning uchalasi ham o'lchanmaydi — dashboard qurib bo'lmaydi.",
    ),
    DashboardRow(
        name="Запуска (Ph.0/Ph.1)",
        content=(
            "Прогресс к порогу публикации, покрытие территорий участниками, "
            "доля UZ-сессий"
        ),
        build=Build.PARTIAL,
        note=(
            "Nashr porogi progressi hisoblanadi (`maturity.compute`), "
            "qamrov ham. UZ-sessiyalar ulushi esa o'lchab bo'lmaydi: "
            "«sessiya» mahsulotda yo'q (`01` §21 reyestrining "
            "`session_is_undefined` / `detected_is_not_chosen` chegaralari)."
        ),
        binds=("app.stats.maturity:compute", "app.analytics.dashboards:DASHBOARDS"),
        gap="UZ-sessiya ulushi o'lchanmaydi — «sessiya» tushunchasi kodda yo'q.",
    ),
)


# --------------------------------------------------------------------------
# §20.3 — KPI, hujjatdagi tartibda
# --------------------------------------------------------------------------

KPIS: tuple[KpiRow, ...] = (
    KpiRow(
        kpi="Уникальных репортёров за 30 дней",
        definition="Регион",
        target="Порог из Ph.0",
        status="`ГИПОТЕЗА`",
        meter=Meter.DERIVABLE,
        note=(
            "Xom ma'lumot to'liq (har xabar muallifi bilan saqlanadi, "
            "digest kunlik repartyorlarni sanaydi), lekin 30 kunlik unikal "
            "hisob hech qayerda ko'rsatilmaydi. Porog ham yo'q — u Ph.0 "
            "natijasi."
        ),
        binds=("app.admin.digest:Digest",),
        gap="30 kunlik unikal repartyor soni hech qanday sirtda yo'q.",
    ),
    KpiRow(
        kpi="Доля территорий с ненулевым покрытием",
        definition="Махалли с ≥1 репортом / всего",
        target="≥50%",
        status="`ГИПОТЕЗА`",
        meter=Meter.MEASURED,
        note=(
            "Aynan shu kasr mahalla qamrov kesimida hisoblanadi; spravochnik "
            "bo'sh muhitda vitrina `available=False` bilan halol javob "
            "beradi."
        ),
        binds=("app.stats.mahalla_coverage:summarize", "app.stats.service:mahalla_index"),
    ),
    KpiRow(
        kpi="Доля автоподтверждённых инцидентов",
        definition="Без модерации",
        target="≥60%",
        status="`BASELINE-TAS`",
        meter=Meter.MOOT,
        note=(
            "Ikkinchi topilma: qo'lda tasdiqlash yo'li kodda YO'Q (§19 "
            "moderator topilmasining egizagi) — tasdiqlanganlarning 100% i "
            "avtomatik, KPI qurilish bo'yicha bajariladi va hech narsani "
            "o'lchamaydi."
        ),
        binds=("app.release.business_interfaces:MODERATOR_BUILT_VERBS",),
        gap="KPI mavjud bo'lmagan qo'lda-tasdiqlash yo'lini nazarda tutadi (👤 §19 egizagi).",
    ),
    KpiRow(
        kpi="Доля привязок к махалле",
        definition="Автоматических",
        target="≥90%",
        status="`ОЦЕНКА`",
        meter=Meter.DERIVABLE,
        note=(
            "Har xabar `ST_Contains` bilan mahallaga biriktiriladi, ya'ni "
            "kasrni hisoblash mumkin — lekin u hech qayerda ko'rsatilmaydi. "
            "Eng yaqin metrika (`geo_unmatched_ratio`) tuman darajasida."
        ),
        binds=("app.geo.pipeline:find_mahalla_id",),
        gap="Mahalla biriktirish ulushi metrika sifatida yo'q (tuman ulushi bor).",
    ),
    KpiRow(
        kpi="Доля UZ-сессий",
        definition="Регион",
        target="≥70%",
        status="`ГИПОТЕЗА`",
        meter=Meter.UNMEASURED,
        note=(
            "Birinchi topilmaning bir bo'lagi: «sessiya» mahsulotda yo'q, "
            "`language_detected` esa tanlangan til emas — ikkala chegara "
            "`01` §21 reyestrida qayd etilgan va odam qarorini kutadi."
        ),
        gap="O'lchov mexanizmi yo'q: sessiya ham, tanlangan til oqimi ham (👤).",
    ),
    KpiRow(
        kpi="Расхождение агрегатов",
        definition="Сумма территорий vs итог",
        target="≤5%",
        status="`BASELINE-TAS`",
        meter=Meter.MOOT,
        note=(
            "Uchinchi topilma: hududlar summasi va jami bitta o'tishda, "
            "bitta manbadan yig'iladi — taqqoslanadigan mustaqil ikkinchi "
            "son yo'q, farq ta'rif bo'yicha 0."
        ),
        binds=("app.stats.aggregate:Aggregation",),
        gap="Bitta-manba arxitekturasida bu KPI bo'sh — solishtiradigan juft yo'q.",
    ),
    KpiRow(
        kpi="Медиана времени до подтверждения",
        definition="Регион",
        target="≤3 мин",
        status="`BASELINE-TAS`",
        meter=Meter.MEASURED,
        note=(
            "`time_to_confirm_seconds` kvantillari bilan o'lchanadi "
            "(`05` §10 jadvalining qatori) — mediana shu yerdan."
        ),
        binds=(
            "app.obs.metrics:TIME_TO_CONFIRM",
            "app.clustering.repository:confirm_latency_by_region",
        ),
    ),
)


# --------------------------------------------------------------------------
# §21 — muvaffaqiyat metrikalari, hujjatdagi tartibda
# --------------------------------------------------------------------------

METRICS: tuple[MetricRow, ...] = (
    MetricRow(
        level="Продуктовый",
        metric="Time-to-answer p90 ≤10 с",
        failure="Продукт не решает свою основную задачу",
        meter=Meter.UNMEASURED,
        note=(
            "Birinchi topilmaning yadrosi: `05` §10 jadvalida bunday "
            "metrika yo'q, eng yaqini (`time_to_confirm`) boshqa narsani "
            "o'lchaydi — gate hisobida bu qator ataylab `None` "
            "(`app/release/collector.py`)."
        ),
        binds=("app/release/collector.py",),
        gap="Asosiy mahsulot metrikasi o'lchanmaydi (👤 `05` §10 kengaytiriladimi).",
    ),
    MetricRow(
        level="Продуктовый",
        metric="Плотность, достаточная для автоподтверждения",
        failure="Краудсорсинговая модель в регионе не работает",
        meter=Meter.MEASURED,
        note=(
            "Tasdiqlanuvchan klasterlar ulushi gate hisobida o'lchanadi "
            "(`confirmable_share`, `03` §6)."
        ),
        binds=(
            "app.release.collector:collect",
            "app.clustering.repository:confirmable_counts",
        ),
    ),
    MetricRow(
        level="Данные",
        metric="Расхождение агрегатов ≤5%",
        failure="Цифрам региона нельзя доверять",
        meter=Meter.MOOT,
        note="§20.3 egizagi (uchinchi topilma): bitta manba, farq ta'rifan 0.",
        binds=("app.stats.aggregate:Aggregation",),
        gap="Bitta-manba arxitekturasida bo'sh o'lchov — §20.3 bilan bitta qulf.",
    ),
    MetricRow(
        level="Данные",
        metric="Доля привязок к махалле ≥90%",
        failure="Геомодель не даёт заявленной гранулярности",
        meter=Meter.DERIVABLE,
        note="§20.3 egizagi: biriktirish bor, ulush ko'rsatilmaydi.",
        binds=("app.geo.pipeline:find_mahalla_id",),
        gap="Ulush metrika sifatida yo'q (tuman darajasidagisi bor).",
    ),
    MetricRow(
        level="Аудитория",
        metric="Доля территорий с покрытием ≥50%",
        failure="Сервис обслуживает нерепрезентативное меньшинство",
        meter=Meter.MEASURED,
        note=(
            "§20.3 dagi qamrov KPI sining egizagi — mahalla kesimida "
            "hisoblanadi. `03` dagi maydon-asosidagi mezon "
            "(`reported_area_share`) boshqa savol va u haqiqatan "
            "o'lchanmaydi — lekin §21 sanaydigan kasr shu."
        ),
        binds=("app.stats.mahalla_coverage:summarize",),
    ),
    MetricRow(
        level="Локализация",
        metric="Доля UZ-сессий ≥70%",
        failure="Языковая гипотеза опровергнута",
        meter=Meter.UNMEASURED,
        note="§20.3 egizagi: «sessiya» tushunchasi kodda yo'q.",
        gap="O'lchov mexanizmi yo'q — §20.3 bilan bitta qulf (👤).",
    ),
    MetricRow(
        level="Операционный",
        metric="SLA модерации выдержан",
        failure="Операционная модель не масштабируется на второй регион",
        meter=Meter.UNMEASURED,
        note=(
            "SLA ta'rifi ham, o'lchovi ham yo'q: navbat yoshi saqlanmaydi, "
            "qaror muddati hisoblanmaydi (`03` §11 ning ma'lum qarzi)."
        ),
        gap="SLA hech qanday ko'rinishda o'lchanmaydi.",
    ),
    MetricRow(
        level="Стратегический",
        metric="Получен воспроизводимый пакет запуска региона",
        failure="Каждый следующий регион будет стоить как первый",
        meter=Meter.MANUAL,
        note=(
            "Bu son emas, artefakt hukmi. Kodlashtirilgan qismi bor — "
            "hujjat↔kod reyestrlar indeksi (shu modul ham uning qatori) va "
            "region-agnostik konfiguratsiya — lekin «paket olindi» degan "
            "xulosa odamniki."
        ),
        binds=("app/admin/registries.py",),
        gap="Baholash mezoni yozilmagan — hukm odamda (👤).",
    ),
)


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BusinessReportingReport:
    """BRD §20–§21 ning bugungi holati."""

    reports: tuple[ReportRow, ...]
    dashboards: tuple[DashboardRow, ...]
    kpis: tuple[KpiRow, ...]
    metrics: tuple[MetricRow, ...]

    def __post_init__(self) -> None:
        self._check_counts()
        self._check_builds()
        self._check_meters()
        self._check_neighbors()

    # -- qorovullar --------------------------------------------------------

    def _check_counts(self) -> None:
        if len(self.reports) != SPEC_REPORT_ROWS:
            raise BusinessReportingError("§20.1 qatorlari soni hujjatga mos emas")
        if len(self.dashboards) != SPEC_DASHBOARD_ROWS:
            raise BusinessReportingError("§20.2 qatorlari soni hujjatga mos emas")
        if len(self.kpis) != SPEC_KPI_ROWS:
            raise BusinessReportingError("§20.3 qatorlari soni hujjatga mos emas")
        if len(self.metrics) != SPEC_METRIC_ROWS:
            raise BusinessReportingError("§21 qatorlari soni hujjatga mos emas")
        levels = tuple(m.level for m in self.metrics)
        if levels != SPEC_METRIC_LEVELS:
            raise BusinessReportingError("§21 daraja ustuni hujjatdagidan farq qildi")

    def _check_builds(self) -> None:
        for row in (*self.reports, *self.dashboards):
            if row.build in (Build.LIVE, Build.PARTIAL, Build.PROVISIONED) and not row.binds:
                raise BusinessReportingError(f"{row.name}: {row.build} dalilsiz bo'lmaydi")
            if row.build is Build.ABSENT and row.binds:
                raise BusinessReportingError(
                    f"{row.name}: `ABSENT` da dalil bo'lmaydi — dalil bor bo'lsa, "
                    "holat boshqa"
                )
            if row.build in (Build.PARTIAL, Build.PROVISIONED, Build.ABSENT) and not row.gap:
                raise BusinessReportingError(f"{row.name}: farq bor, `gap` yozilmagan")

    def _check_meters(self) -> None:
        for row in (*self.kpis, *self.metrics):
            label = getattr(row, "kpi", None) or row.metric
            if row.meter in (Meter.MEASURED, Meter.DERIVABLE, Meter.MOOT, Meter.MANUAL):
                if not row.binds:
                    raise BusinessReportingError(f"{label}: {row.meter} dalilsiz bo'lmaydi")
            if row.meter is Meter.UNMEASURED and row.binds:
                # Yagona istisno: ataylab-None dalili fayl bo'lishi mumkin.
                if any(b.startswith("app.") for b in row.binds):
                    raise BusinessReportingError(
                        f"{label}: `UNMEASURED` da ishlaydigan simvol dalili bo'lmaydi"
                    )
            if row.meter is not Meter.MEASURED and not row.gap:
                raise BusinessReportingError(f"{label}: {row.meter} da `gap` majburiy")
        for row in self.kpis:
            classify_status(row.status)

    def _check_neighbors(self) -> None:
        """Qo'shni reyestrlar bilan bog'lamlar — eskirsa shu yerda yiqiladi."""
        if "подтверждение" in bifc.MODERATOR_BUILT_VERBS:
            raise BusinessReportingError(
                "Qo'lda tasdiqlash paydo bo'ldi — avtotasdiq KPI topilmasi eskirgan"
            )
        uz = next((d for d in adash.DASHBOARDS if d.code == "uz_session_share"), None)
        if uz is None:
            raise BusinessReportingError(
                "`01` §21 reyestrida `uz_session_share` yo'qoldi — UZ topilmasi eskirgan"
            )
        limit_codes = {limit.code for limit in uz.limits}
        if not set(UZ_SESSION_LIMITS) <= limit_codes:
            raise BusinessReportingError(
                "UZ-sessiya chegaralari o'zgardi — `UNMEASURED` bahosi qayta ko'rilsin"
            )

    # -- kesimlar ----------------------------------------------------------

    @property
    def flagged(self) -> tuple[ReportRow | DashboardRow | KpiRow | MetricRow, ...]:
        """`gap` i bo'sh bo'lmagan qatorlar — hujjat bilan kod ajragan joylar."""
        return tuple(
            r for r in (*self.reports, *self.dashboards, *self.kpis, *self.metrics) if r.gap
        )

    @property
    def unmeasured(self) -> tuple[MetricRow, ...]:
        """§21 dan bugun o'lchab bo'lmaydiganlar — «izmerimost» yiqiladigan joy."""
        return tuple(m for m in self.metrics if m.meter is Meter.UNMEASURED)

    @property
    def moot(self) -> tuple[KpiRow | MetricRow, ...]:
        """Qurilish bo'yicha bo'sh o'lchovlar: avtotasdiq va agregat farqi."""
        return tuple(r for r in (*self.kpis, *self.metrics) if r.meter is Meter.MOOT)

    @property
    def by_meter(self) -> dict[Meter, int]:
        result: dict[Meter, int] = {m: 0 for m in Meter}
        for row in (*self.kpis, *self.metrics):
            result[row.meter] += 1
        return result

    @property
    def measurability_holds(self) -> bool:
        """BRD §22 yakuni («метрики §21 измерены») bugun rostmi. Bugun `False`."""
        return not self.unmeasured

    @property
    def accurate(self) -> bool:
        """§20–§21 «hujjat mahsulotni to'g'ri tasvirlaydi» deb o'qilsa rostmi.

        Bugun `False`: o'n yetti qator ajragan — sifat hisoboti/dashboardi
        yo'q, uch metrika o'lchanmaydi, ikkitasi qurilish bo'yicha bo'sh.
        """
        return not self.flagged


def evaluate() -> BusinessReportingReport:
    """Reyestrdan to'liq hisobot. Argument yo'q — 85–87, 99–104 runlar qoidasi."""
    return BusinessReportingReport(
        reports=REPORTS,
        dashboards=DASHBOARDS_ROWS,
        kpis=KPIS,
        metrics=METRICS,
    )
