"""Spetsifikatsiya reyestrlarining indeksi — vitrina qatlami.

## Nima uchun bu fayl kerak

66-rundan 79-rungacha o'n to'rtta run bitta shakldagi ish qildi:
hujjatning bitta bo'limi (`01` §17…§29, `03` §6/§11) kodga
**reyestr** bo'lib ko'chirildi va uning bugungi holati o'lchandi.
Bugun `app/` da o'n uchta shunday modul bor va ularning **o'n bittasi
hech qayerda ko'rinmaydi**: hisobotni faqat `pytest` chaqiradi, ya'ni
u qizarganda emas, faqat CI yurganda o'qiladi. Odam uchun esa savol
boshqacha — «bugun hujjatning qaysi bo'limi kodga zid?» — va unga
javob beradigan joy yo'q edi.

Bu modul o'sha o'n uchtasini bitta ro'yxatga yig'adi.
`GET /api/v1/admin/registries` aynan shuni ko'rsatadi. (`PROGRESS.md`
uni 74–79 runlarda `/admin/monitoring` deb rejalashtirgan edi; nom
o'zgartirildi, chunki `01` §22 ning **o'zi** «Logging & Monitoring»
deb ataladi va indeksda `monitoring` degan alohida qator bor.)

## Nima uchun bitta ustun yetmaydi

Reyestrlar bir xil savolga javob bermaydi va ularni bitta
«bajarildi / bajarilmadi» ustuniga siqish 74- va 76-runlar topgan
xatoning aynan o'zi bo'lardi. Shuning uchun ikkita o'q.

`Verdict` — reyestrning **hujjat haqidagi** o'z hukmi. Uchtala
qiymatning uchinchisi eng muhimi: `UNSCORED` yiqilish emas, **boshqa
shakldagi hisobot**. `measures`, `monitoring`, `dashboards` va
`acceptance` «hujjat yolg'on gapiryaptimi?» degan savolga umuman
javob bermaydi — ular qamrovni o'lchaydi («nechtasi bugun
o'lchanadi»), va ularning `is_accepted` i mahsulot emas, **mintaqa**
haqida. Ularni `INACCURATE` deb belgilash hujjatga u aytmagan
gapni yuklardi.

`Serving` — hisobot **operator o'qiydigan joyda** quriladimi. Bu o'q
`Verdict` ni takrorlamaydi va aynan shu yerda bu running eng jim
topilmasi turibdi (quyida).

## To'rtta reyestr prodda ko'rinmaydi — bu QAROR, kamchilik emas

`data_model`, `integrations`, `channels` va `architecture` hisobotni
**hujjat matnidan** quradi (`build_report(doc)`,
`parse_container_diagram(doc)`), ya'ni ularga `01_PRD_Samarkand.md`
kerak. Fayl repo ildizida yotadi, `Dockerfile` esa `app`, `tools`,
`tests` va `alembic` ni ko'chiradi — ya'ni hujjat obrazda **yo'q**.
Uni qo'shib qo'yish ham shunchaki `COPY` emas: build konteksti
`sveta/`, hujjatlar esa undan **bir daraja yuqorida**, ya'ni kontekst
tashqarisida.

80-run buni birinchi marta ko'rsatdi (shu paytgacha hujjatni faqat
testlar o'qiydi, testlar esa repoda yuriladi va u yerda fayl joyida),
va odam **o'sha kuni javob berdi: hujjatlar obrazga qo'shilmaydi.**

Ya'ni `Serving.DOC_BOUND` — vaqtinchalik holat emas, **doimiy
chegara**: bu to'rtta reyestr *ishlab chiqish* asbobi (CI va repo),
mahsulotning vitrinasi emas. Indeks ularni ro'yxatdan **chiqarib
tashlamaydi** — ular mavjud va ularning javobi bor, faqat boshqa
joyda; `complete: false` esa endi nosozlik haqidagi ogohlantirish
emas, prodda **kutilgan** javob.

Aynan shu sababdan `Reason.DOC_MISSING` ham xato emas, ham
«hali qilinmagan ish» emas. Ikkinchi tomoni `Serving` o'qining o'zini
oqlaydi: agar hujjat obrazda bo'lganida, bu o'q keraksiz bo'lardi.

## Modul chegarasi

`05` §1 va `03` §Q-1: bu yerda bitta ham `SELECT` yo'q va bitta ham
jadvalga murojaat yo'q. Sxema ham shu yerda yig'ilmaydi —
`app.db.models` ni import qilish 79-run o'lchagan shartni buzardi,
shuning uchun `data_model.build_current_report` o'z modulida yig'adi.
Har bir son o'z modulining sof funksiyasidan olinadi —
`release/collector.py` va `obs/collector.py` bilan bir xil tartib.
`gates` esa aynan shu sababdan bu yerda **hisoblanmaydi**:
uning yagona javobi bazadan va mintaqadan keladi
(`release/collector.collect`), ya'ni indeks uni faqat **nomlaydi** va
o'z endpointiga yuboradi.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from app.admin import security as security_mod
from app.analytics import dashboards as dashboards_mod
from app.core import api_requirements as api_requirements_mod
from app.core import architecture as architecture_mod
from app.core import glossary as glossary_mod
from app.db import data_model as data_model_mod
from app.integrations import registry as integrations_mod
from app.notifications import channels as channels_mod
from app.obs import monitoring as monitoring_mod
from app.release import acceptance as acceptance_mod
from app.release import dependencies as dependencies_mod
from app.release import functional_requirements as functional_mod
from app.release import measures as measures_mod
from app.release import plan as plan_mod
from app.release import risks as risks_mod
from app.release import roadmap as roadmap_mod
from app.release import scope as scope_mod
from app.release import success as success_mod
from app.release import user_stories as user_stories_mod

#: i18n kalitlarining prefiksi (`gates.py` ning `release.gate` naqshi).
KEY_PREFIX = "registry"

#: Hujjat matnini talab qiladigan reyestrlarning manbai. Bitta fayl —
#: to'rtala DOC_BOUND reyestr ham `01` ning bo'limlarini o'qiydi.
DOC_NAME = "01_PRD_Samarkand.md"

#: `app/admin/registries.py` → `sveta/`. Hujjatlar undan bir daraja
#: yuqorida (repo ildizi); konteynerda bu `/` va u yerda hujjat yo'q.
PACKAGE_ROOT = Path(__file__).resolve().parents[2]

#: Hujjatlar papkasi. Modul uni **topmasligi mumkin** va bu xato emas,
#: `Reason.DOC_MISSING`.
DOC_ROOT = PACKAGE_ROOT.parent


class Verdict(StrEnum):
    """Reyestrning hujjat haqidagi o'z hukmi."""

    #: Bo'lim bugungi kodni to'g'ri tasvirlaydi.
    ACCURATE = "accurate"
    #: Bo'lim bugungi kodga zid — reyestrning o'zi shunday deydi.
    INACCURATE = "inaccurate"
    #: Reyestrda bunday hukm **yo'q**: u qamrovni o'lchaydi, hujjatning
    #: rostligini emas. Yo'qlik emas, boshqa savol.
    UNSCORED = "unscored"


class Serving(StrEnum):
    """Hisobot operator o'qiydigan joyda qurilishi mumkinmi."""

    #: Sof kod: `evaluate()` ga hech narsa kerak emas.
    SELF_CONTAINED = "self_contained"
    #: Hisobot spetsifikatsiya matnidan quriladi. Matn obrazda **yo'q
    #: va bo'lmaydi** (80-run qarori) — ya'ni bu reyestrlar ishlab
    #: chiqish asbobi, mahsulot vitrinasi emas.
    DOC_BOUND = "doc_bound"
    #: Hisobot bazadan va mintaqadan keladi — indeks uni hisoblamaydi.
    LIVE = "live"


class Reason(StrEnum):
    """Hisobot nega qurilmadi. Kod, matn emas — tarjima API qatlamida."""

    DOC_MISSING = "doc_missing"
    NEEDS_REGION = "needs_region"


@dataclass(frozen=True)
class Probe:
    """Bitta reyestrning bugungi o'lchovi.

    `flagged` — reyestrning **o'z qatorlaridan** nechtasi belgilangan,
    ya'ni u har doim `total` dan katta emas. `undeclared` esa boshqa
    narsa: hujjatda **umuman yo'q**, lekin kodda bor narsalar soni.
    Ikkalasini qo'shib bitta songa aylantirish ularning ma'nosini
    yo'qotardi — birinchisi «yozilgani noto'g'ri», ikkinchisi
    «yozilmagani bor».
    """

    verdict: Verdict
    total: int
    flagged: int
    undeclared: int

    def __post_init__(self) -> None:
        if self.flagged > self.total:
            raise ValueError(f"flagged ({self.flagged}) > total ({self.total})")


@dataclass(frozen=True)
class Registry:
    """Indeksning bitta qatori."""

    #: Qisqa kod; i18n kaliti va API javobi shundan quriladi.
    code: str
    #: Hujjat bo'limi, reyestrning o'z `SPEC` konstantasidan.
    spec: str
    #: Reyestr yashaydigan modul (`app.` bilan).
    module: str
    serving: Serving
    #: Reyestrni ko'rsatadigan **o'z** endpointi. `None` — yo'q, ya'ni
    #: uni faqat shu indeks ko'rsatadi.
    endpoint: str | None
    #: O'lchovni qaytaradi. `None` — `Serving.LIVE`, hisoblanmaydi.
    probe: Callable[[str | None], Probe] | None

    @property
    def key(self) -> str:
        return f"{KEY_PREFIX}.{self.code}"

    @property
    def surfaced(self) -> bool:
        return self.endpoint is not None


# --------------------------------------------------------------------------
# O'lchovlar
#
# Har biri o'z modulining **sof** funksiyasini chaqiradi. `flagged`
# qatorlar to'plamining kuchi bo'lib olinadi (yig'indi emas): bitta
# qator ikkita sababdan belgilangan bo'lsa, u ikki marta sanalmasligi
# kerak — aks holda `flagged > total` bo'lib, hisobot boridan yomonroq
# ko'rinardi.
# --------------------------------------------------------------------------


def _verdict(accurate: bool) -> Verdict:
    return Verdict.ACCURATE if accurate else Verdict.INACCURATE


def _probe_data_model(doc: str | None) -> Probe:
    assert doc is not None
    # Sxema **shu yerda yig'ilmaydi**: `app.db.models` ni import qilish
    # `03` §Q-1 ning modul chegarasini buzardi (79-run o'lchagan shart).
    report = data_model_mod.build_current_report(doc)
    return Probe(
        verdict=_verdict(report.faithful),
        total=len(report.findings),
        flagged=len(report.diverged),
        # Diagrammada tasdig'i yo'q bog'lanishlar va tushirib
        # qoldirilgan `region_id` — ikkalasi ham «yozilmagani bor».
        undeclared=len(report.unbacked_relations) + len(report.region_gaps),
    )


def _probe_integrations(doc: str | None) -> Probe:
    assert doc is not None
    report = integrations_mod.build_report(doc)
    flagged = {
        f.row.system
        for f in report.by_warrant(integrations_mod.Warrant.OVERSTATED) + report.presumed
    }
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.findings),
        flagged=len(flagged),
        undeclared=len(report.undeclared),
    )


def _probe_channels(doc: str | None) -> Probe:
    assert doc is not None
    report = channels_mod.build_report(doc)
    flagged = {f.row.channel for f in report.overstated + report.unguarded}
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.findings),
        flagged=len(flagged),
        undeclared=len(report.undeclared),
    )


def _probe_architecture(doc: str | None) -> Probe:
    assert doc is not None
    diagram = architecture_mod.parse_container_diagram(doc)
    declined = architecture_mod.declined()
    return Probe(
        verdict=_verdict(architecture_mod.headline_holds(diagram)),
        total=len(diagram.node_ids),
        # Rasmda chizilgan, mahsulotda ataylab yo'q tugunlar. Strelkalar
        # bu yerda sanalmaydi — `total` tugunlar bo'yicha.
        flagged=len([c for c in declined if c.node_id in set(diagram.node_ids)]),
        # `app/` da bor, rasmda umuman yo'q paketlar.
        undeclared=len(architecture_mod.EMERGENT_PACKAGES),
    )


def _probe_security(_doc: str | None = None) -> Probe:
    report = security_mod.evaluate()
    flagged = set(report.absent) | set(report.undefended) | set(report.misstated)
    return Probe(
        verdict=_verdict(report.trustworthy),
        total=len(report.guarantees),
        flagged=len(flagged),
        undeclared=0,
    )


def _probe_plan(_doc: str | None = None) -> Probe:
    report = plan_mod.evaluate()
    flagged = {r.code for r in report.colliding + report.unshippable}
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.rows),
        flagged=len(flagged),
        undeclared=len(report.unplanned),
    )


def _probe_roadmap(_doc: str | None = None) -> Probe:
    """`01` §24 — uchta ro'yxat, bitta hukm.

    `total` bo'limning **hamma** qatorini oladi (vazifalar, chiqish
    mezonlari va fazalar): hukm ularning uchalasidan birga chiqadi.
    `flagged` esa faqat hujjat kod bilan ajralib ketgan joylarni
    sanaydi — gipotezasi allaqachon hal qilingan vazifalar va gate
    yopilmasdan boshlangan fazalar.
    """
    report = roadmap_mod.evaluate()
    flagged = {t.code for t in report.prejudged} | {p.code for p in report.built_ahead}
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.tasks) + len(report.criteria) + len(report.phases),
        flagged=len(flagged),
        undeclared=len(report.ahead),
    )


def _probe_glossary(_doc: str | None = None) -> Probe:
    """`01` §30 — o'nta atama, uchtasi rost.

    `flagged` ta'rifi qurilgan xulqqa mos kelmagan har qatorni oladi:
    sinf farqi (`NARROWER`/`WIDER`/`SUPERSEDED`/`UNREACHABLE`) bu yerda
    ahamiyatsiz — lug'at o'quvchisi uchun ular bir xil oqibat beradi.
    `undeclared` esa kod tayanadigan, lug'at nomlamaydigan
    tushunchalar.

    Hujjat kerak emas: `marked` reyestrda saqlanadi va uni hujjat bilan
    `test_glossary_contract` ikki tomonlama qulflaydi. Shuning uchun
    `SELF_CONTAINED`, `architecture` dan farqli.
    """
    report = glossary_mod.evaluate()
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.terms),
        flagged=len(report.imprecise),
        undeclared=len(report.missing),
    )


def _probe_success(_doc: str | None = None) -> Probe:
    """`01` §4 — o'n ikkita KPI, ikkitasi o'lchanadi.

    `flagged` ikkita mustaqil sababni **birlashtiradi**, yig'maydi:
    sonli maqsadi bor, lekin o'lchagichi yo'q qatorlar va nomi paketda
    ta'riflanmagan qatorlar. Bugun ikkala to'plam ham `K-9` ni o'z
    ichiga oladi — aynan shuning uchun yig'indi emas, birlashma
    (`flagged > total` bo'lib qolardi). `undeclared` — repo
    o'lchaydigan, §4 nomlamaydigan narsalar.

    Hujjat kerak emas: baholar reyestrda saqlanadi va ularni hujjat
    bilan `test_success_metrics_contract` ikki tomonlama qulflaydi.
    """
    report = success_mod.evaluate()
    flagged = {k.code for k in report.broken_promises} | {k.code for k in report.undefined}
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.kpis),
        flagged=len(flagged),
        undeclared=len(report.unnamed),
    )


def _probe_scope(_doc: str | None = None) -> Probe:
    """`01` §7 — o'n sakkiz qator, chegara ikki tomondan.

    `flagged` ikkita mustaqil sababni **birlashtiradi**, yig'maydi:
    chegarasi buzilgan qatorlar (`HOLLOW` va `CROSSED`) va asosi
    ishlamaydigan qatorlar. Bugun ikkala to'plam ham `S-1` ni o'z
    ichiga oladi — u ham bo'sh, ham chet ellik asosga tayanadi —
    ya'ni yig'indi `flagged > total` bo'lib qolardi.
    `undeclared` — repo qurgan, §7 esa uchala ro'yxatida ham
    nomlamagan sirtlar.

    Hujjat kerak emas: baholar reyestrda saqlanadi va ularni hujjat
    bilan `test_scope_contract` ikki tomonlama qulflaydi.
    """
    report = scope_mod.evaluate()
    broken = {i.code for i in report.hollow + report.crossed}
    flagged = broken | {i.code for i in report.unsound_warrants}
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.items),
        flagged=len(flagged),
        undeclared=len(report.unlisted),
    )


def _probe_api_requirements(_doc: str | None = None) -> Probe:
    """`01` §16 — yettita delta qatori, ustiga oltita meros xossasi.

    `flagged` uchta sababni **birlashtiradi**, yig'maydi: shartnomani
    bajarmagan qatorlar, modalligi kuchsizlangan qatorlar va paket
    ikki xil gapiradigan qatorlar. Bugun uchala to'plam ham `A-1` ni
    o'z ichiga oladi — u bir vaqtning o'zida qayta nomlangan, ixtiyoriy
    qilingan va ikki joyda ikki xil yozilgan — ya'ni yig'indi
    `flagged > total` bo'lib qolardi.

    `total` faqat delta jadvalining qatorlarini sanaydi: meros
    xossalari hujjatning **epigrafi**, jadvalning qatori emas, va
    ularning hukmi paketda umuman yo'q faylga bog'liq. `undeclared` —
    qurilgan va §16 nomlamagan interfeys shartlari.

    Hujjat kerak emas: baholar reyestrda saqlanadi va ularni hujjat
    bilan `test_api_requirements_contract` ikki tomonlama qulflaydi.
    """
    report = api_requirements_mod.evaluate()
    unkept = {
        r.code for r in report.requirements if r.delivery not in api_requirements_mod.DELIVERY_KEPT
    }
    flagged = unkept | {r.code for r in report.relaxed} | {r.code for r in report.restated}
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.requirements),
        flagged=len(flagged),
        undeclared=len(report.undeclared),
    )


def _probe_functional(_doc: str | None = None) -> Probe:
    """`01` §8 — oltita `FR-S-*` qatori, uchta o'q.

    `flagged` uchta sababni **birlashtiradi**, yig'maydi: qoidasi
    boshqacha qurilgan qatorlar, `AC` si tekshirmaydigan qatorlar va
    ochiq deb e'lon qilingan qarori jimgina yopilgan qatorlar. Bugun
    uchala to'plam ham `F-4` ni o'z ichiga oladi — u bir vaqtning
    o'zida boshqa qoidani yurgizadi, `AC` siz qolgan va sonini test
    bilan qulflagan — ya'ni yig'indi `flagged > total` bo'lib qolardi.

    `total` faqat delta qatorlarini sanaydi: epigraf meros qilgan
    o'n ikki modul jadvalning qatori emas va ularning hukmi paketda
    umuman yo'q faylga bog'liq. `undeclared` — qurilgan va §8 o'zi
    «o'zgargan» deb atagan uchta modulda nomsiz qolgan sirtlar.

    Hujjat kerak emas: baholar reyestrda saqlanadi va ularni hujjat
    bilan `test_functional_requirements_contract` ikki tomonlama
    qulflaydi.
    """
    report = functional_mod.evaluate()
    flagged = (
        {d.code for d in report.diverged}
        | {d.code for d in report.toothless}
        | {d.code for d in report.closed_deferrals}
    )
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.deltas),
        flagged=len(flagged),
        undeclared=len(report.unnamed),
    )


def _probe_user_stories(_doc: str | None = None) -> Probe:
    """`01` §9/§10 — to'qqizta band, uchta o'q.

    `total` — **bandlar**, hikoyalar emas: bitta hikoyaning ikki yarmi
    har xil holatda bo'lishi mumkin va `US-S5` da aynan shunday.

    `flagged` uchta sababni **birlashtiradi**, yig'maydi: boshqacha
    bajarilgan bandlar, `Given` i ro'y bermaydigan hikoyaning bandlari
    va repo nomlamagan bandlar. Bugun uchala to'plam ham bir-birini
    qoplaydi (masalan `C-6` uchalasida ham bor), ya'ni yig'indi
    `flagged > total` bo'lib qolardi.

    `undeclared` — qurilgan, lekin hujjat hech qanday tekshiriladigan
    da'vo qilmagan hikoyalar. Bugun bitta: `US-S4` ning obunasi
    mexanizm sifatida bor va §9 unga gherkin bloki yozmagan.

    Hujjat kerak emas: baholar reyestrda saqlanadi va ularni hujjat
    bilan `test_user_stories_contract` ikki tomonlama qulflaydi.
    """
    report = user_stories_mod.evaluate()
    flagged = (
        {c.code for c in report.diverged}
        | {c.code for c in report.vacuous}
        | {c.code for c in report.unnamed}
    )
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.clauses),
        flagged=len(flagged),
        undeclared=len(report.stories_without_gherkin),
    )


def _probe_risks(_doc: str | None = None) -> Probe:
    report = risks_mod.evaluate()
    uncovered = tuple(e for e in report.entries if not e.is_covered)
    flagged = {e.code for e in uncovered + report.spent_forecast}
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.entries),
        flagged=len(flagged),
        undeclared=len(report.undeclared),
    )


def _probe_dependencies(_doc: str | None = None) -> Probe:
    report = dependencies_mod.evaluate()
    flagged = {r.code for r in report.dangling + report.leaky}
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.rows),
        flagged=len(flagged),
        undeclared=len(report.undeclared),
    )


def _probe_dashboards(_doc: str | None = None) -> Probe:
    report = dashboards_mod.evaluate()
    return Probe(
        verdict=Verdict.UNSCORED,
        total=len(report.dashboards),
        flagged=len(report.gaps),
        undeclared=0,
    )


def _probe_monitoring(_doc: str | None = None) -> Probe:
    report = monitoring_mod.evaluate()
    return Probe(
        verdict=Verdict.UNSCORED,
        total=len(report.requirements),
        flagged=len(report.gaps),
        undeclared=0,
    )


def _probe_measures(_doc: str | None = None) -> Probe:
    report = measures_mod.evaluate()
    return Probe(
        verdict=Verdict.UNSCORED,
        total=len(report.measures),
        flagged=len(report.gaps),
        undeclared=0,
    )


def _probe_acceptance(_doc: str | None = None) -> Probe:
    """`01` §23 — mintaqa haqidagi hisobot, hujjat haqidagi emas.

    Shuning uchun `UNSCORED`: «bajarilmagan mezon» hujjatning
    yolg'onligini bildirmaydi, u ishning hali qilinmaganini bildiradi.
    `UNMEASURED` ham `flagged` ga kiradi — `gates.py` ning qoidasi
    (`03` §6 G-4 izohi): o'lchanmagan mezon bajarilgan emas.
    """
    report = acceptance_mod.evaluate()
    return Probe(
        verdict=Verdict.UNSCORED,
        total=len(report.criteria),
        flagged=len(report.unmet) + len(report.unmeasured),
        undeclared=0,
    )


REGISTRIES: tuple[Registry, ...] = (
    Registry(
        code="data_model",
        spec=data_model_mod.SPEC,
        module="app.db.data_model",
        serving=Serving.DOC_BOUND,
        endpoint=None,
        probe=_probe_data_model,
    ),
    Registry(
        code="integrations",
        spec=integrations_mod.SPEC,
        module="app.integrations.registry",
        serving=Serving.DOC_BOUND,
        endpoint=None,
        probe=_probe_integrations,
    ),
    Registry(
        code="channels",
        spec=channels_mod.SPEC,
        module="app.notifications.channels",
        serving=Serving.DOC_BOUND,
        endpoint=None,
        probe=_probe_channels,
    ),
    Registry(
        code="security",
        spec=security_mod.SPEC,
        module="app.admin.security",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_security,
    ),
    Registry(
        code="dashboards",
        spec=dashboards_mod.SPEC,
        module="app.analytics.dashboards",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_dashboards,
    ),
    Registry(
        code="monitoring",
        spec=monitoring_mod.SPEC,
        module="app.obs.monitoring",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_monitoring,
    ),
    Registry(
        code="acceptance",
        spec=acceptance_mod.SPEC,
        module="app.release.acceptance",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_acceptance,
    ),
    Registry(
        code="plan",
        spec=plan_mod.SPEC,
        module="app.release.plan",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_plan,
    ),
    Registry(
        code="roadmap",
        spec=roadmap_mod.SPEC,
        module="app.release.roadmap",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_roadmap,
    ),
    Registry(
        code="risks",
        # §27 ning nomeri `SPEC_ASSUMPTIONS` dan olinadi, hujjat nomi esa
        # takrorlanmaydi: ikkala bo'lim ham bitta hujjatda.
        spec=f"{risks_mod.SPEC_RISKS} + {risks_mod.SPEC_ASSUMPTIONS.split()[-1]}",
        module="app.release.risks",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_risks,
    ),
    Registry(
        code="dependencies",
        spec=dependencies_mod.SPEC,
        module="app.release.dependencies",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_dependencies,
    ),
    Registry(
        code="architecture",
        spec=architecture_mod.SPEC,
        module="app.core.architecture",
        serving=Serving.DOC_BOUND,
        endpoint=None,
        probe=_probe_architecture,
    ),
    Registry(
        code="glossary",
        spec=glossary_mod.SPEC,
        module="app.core.glossary",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_glossary,
    ),
    Registry(
        code="scope",
        spec=scope_mod.SPEC,
        module="app.release.scope",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_scope,
    ),
    Registry(
        code="functional_requirements",
        spec=functional_mod.SPEC,
        module="app.release.functional_requirements",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_functional,
    ),
    Registry(
        code="user_stories",
        spec=user_stories_mod.SPEC,
        module="app.release.user_stories",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_user_stories,
    ),
    Registry(
        code="api_requirements",
        spec=api_requirements_mod.SPEC,
        module="app.core.api_requirements",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_api_requirements,
    ),
    Registry(
        code="success",
        spec=success_mod.SPEC,
        module="app.release.success",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_success,
    ),
    Registry(
        code="measures",
        spec=measures_mod.SPEC,
        module="app.release.measures",
        serving=Serving.SELF_CONTAINED,
        endpoint="/admin/measures",
        probe=_probe_measures,
    ),
    Registry(
        code="gates",
        spec="03 §6",
        module="app.release.gates",
        serving=Serving.LIVE,
        endpoint="/admin/gates",
        probe=None,
    ),
)

REGISTRY_BY_CODE: dict[str, Registry] = {r.code: r for r in REGISTRIES}

#: i18n kalitlari — `test_i18n_key_contract.py` ularni katalogdan topadi.
REGISTRY_KEYS: tuple[str, ...] = tuple(r.key for r in REGISTRIES)
REASON_KEYS: tuple[str, ...] = tuple(f"{KEY_PREFIX}.reason.{r}" for r in Reason)


def _check_registry() -> None:
    """Import paytida buziladigan invariantlar.

    Ular test emas, **shart**: kodi takrorlangan yoki o'lchovsiz
    qolgan qator indeksni jimgina qisqartirardi.
    """
    codes = [r.code for r in REGISTRIES]
    if len(codes) != len(set(codes)):
        raise ValueError("reyestr kodlari takrorlangan")
    for entry in REGISTRIES:
        if entry.serving is Serving.LIVE:
            if entry.probe is not None:
                raise ValueError(f"{entry.code}: LIVE reyestr indeksda hisoblanmaydi")
            if entry.endpoint is None:
                raise ValueError(f"{entry.code}: LIVE reyestrning o'z endpointi bo'lishi shart")
        elif entry.probe is None:
            raise ValueError(f"{entry.code}: o'lchovsiz qator")
        if not entry.spec:
            raise ValueError(f"{entry.code}: bo'lim ko'rsatilmagan")


_check_registry()


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """Bitta reyestrning bugungi holati."""

    registry: Registry
    #: `None` — hisobot bu muhitda qurilmadi.
    probe: Probe | None
    reason: Reason | None

    @property
    def available(self) -> bool:
        return self.probe is not None


@dataclass(frozen=True)
class IndexReport:
    """Butun indeksning bugungi holati."""

    findings: tuple[Finding, ...]
    #: Spetsifikatsiya matni shu muhitda topildimi.
    doc_present: bool

    @property
    def counts(self) -> dict[str, int]:
        """Hukm → nechta reyestr. O'lchanmaganlar alohida sanaladi."""
        result = {str(v): 0 for v in Verdict}
        result["unavailable"] = 0
        for item in self.findings:
            key = str(item.probe.verdict) if item.probe else "unavailable"
            result[key] += 1
        return result

    @property
    def unavailable(self) -> tuple[Finding, ...]:
        """Shu muhitda qurilmaydigan hisobotlar.

        Indeksning eng muhim ro'yxati: bunday reyestr CI da yashil va
        shu bilan birga serverdagi odamga **hech qachon** javob bera
        olmaydi.
        """
        return tuple(f for f in self.findings if not f.available)

    @property
    def inaccurate(self) -> tuple[Finding, ...]:
        """Hujjat bugungi kodga zid, deb o'z reyestri aytgan bo'limlar."""
        return tuple(f for f in self.findings if f.probe and f.probe.verdict is Verdict.INACCURATE)

    @property
    def unsurfaced(self) -> tuple[Finding, ...]:
        """O'z endpointi yo'q reyestrlar — ular faqat shu indeksda ko'rinadi."""
        return tuple(f for f in self.findings if not f.registry.surfaced)

    @property
    def undeclared_total(self) -> int:
        """Hujjatlarda umuman yozilmagan narsalar soni, hammasi bo'yicha."""
        return sum(f.probe.undeclared for f in self.findings if f.probe)

    @property
    def complete(self) -> bool:
        """Indeks shu muhitda **to'liq** javob beradimi.

        Prodda `False`, repoda `True`, va bu farq **qoladi**: hujjatlar
        obrazga qo'shilmaydi (80-run qarori). Ya'ni maydon nosozlikni
        emas, **muhitni** bildiradi — «bu javobning qolgan qismini
        repoda qidiring» degani.
        """
        return not self.unavailable


def read_doc(root: Path | None = None) -> str | None:
    """Spetsifikatsiya matni yoki `None`.

    Xato ko'tarilmaydi: hujjatning yo'qligi — muhitning holati, nosozlik
    emas. Aynan shu qaror `Reason.DOC_MISSING` ni hisobotning bir qismi
    qiladi (yiqilish emas).
    """
    path = (root or DOC_ROOT) / DOC_NAME
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def evaluate(doc: str | None) -> IndexReport:
    """Indeksni yig'adi.

    `doc` — `read_doc()` natijasi; `None` bo'lsa `DOC_BOUND` qatorlar
    `Reason.DOC_MISSING` bilan qaytadi. Matnni **tashqaridan** olish
    ataylab: shu tufayli modul I/O siz qoladi va test uni ikkala
    holatda ham yurgiza oladi.
    """
    findings: list[Finding] = []
    for entry in REGISTRIES:
        if entry.probe is None:
            findings.append(Finding(entry, None, Reason.NEEDS_REGION))
            continue
        if entry.serving is Serving.DOC_BOUND and doc is None:
            findings.append(Finding(entry, None, Reason.DOC_MISSING))
            continue
        findings.append(Finding(entry, entry.probe(doc), None))
    return IndexReport(findings=tuple(findings), doc_present=doc is not None)
