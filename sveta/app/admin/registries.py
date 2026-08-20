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
from app.admin import tzoperator as tzoperator_mod
from app.analytics import dashboards as dashboards_mod
from app.clustering import tzdispute as tzdispute_mod
from app.clustering import tzrestore as tzrestore_mod
from app.clustering import tzscale as tzscale_mod
from app.clustering import tzstatus as tzstatus_mod
from app.core import api_requirements as api_requirements_mod
from app.core import architecture as architecture_mod
from app.core import glossary as glossary_mod
from app.core import tzconfig as tzconfig_mod
from app.db import data_model as data_model_mod
from app.integrations import registry as integrations_mod
from app.notifications import channels as channels_mod
from app.notifications import tzoutage as tzoutage_mod
from app.notifications import tzrestored as tznotify_mod
from app.obs import monitoring as monitoring_mod
from app.release import acceptance as acceptance_mod
from app.release import business_acceptance as bacc_mod
from app.release import business_architecture as barch_mod
from app.release import business_environment as benv_mod
from app.release import business_glossary as bglos_mod
from app.release import business_interfaces as bifc_mod
from app.release import business_reporting as brep_mod
from app.release import business_requirements as business_mod
from app.release import business_rules as brl_mod
from app.release import dependencies as dependencies_mod
from app.release import functional_requirements as functional_mod
from app.release import measures as measures_mod
from app.release import nfr_appendix as nfr_appendix_mod
from app.release import phase0_plan as phase0_mod
from app.release import plan as plan_mod
from app.release import risks as risks_mod
from app.release import roadmap as roadmap_mod
from app.release import scope as scope_mod
from app.release import success as success_mod
from app.release import tz_acceptance as tzacc_mod
from app.release import user_stories as user_stories_mod
from app.release import ux_requirements as ux_mod
from app.reports import tzsensor as tzsensor_mod

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


def _probe_tzstatus(_doc: str | None = None) -> Probe:
    """TZ §5 — sakkizta status, ulardan yettitasi qurilgan.

    `flagged` — `decide()` bugun **qaytara olmaydigan** statuslar.
    Bugun bitta: «Проверено оператором» (§8). Tiklanishning uchtasi
    §11/4 da qurildi va endi bu ro'yxatda emas.
    Verdikt shuning uchun hamon salbiy: §5 jadvali bugungi kodni
    to'liq tasvirlamaydi va buni operator ko'radigan joyda aytish
    kerak. Operator paneli (§8) qurilganda u o'z-o'zidan ijobiyga
    o'tadi.

    `undeclared` har doim `0`: `TzStatus` ning har bir a'zosi §5
    jadvalining qatori — `tests/test_tz_status.py` buni literal
    ro'yxat bilan qulflaydi.
    """
    total = len(tzstatus_mod.TzStatus)
    decided = len(tzstatus_mod.DECIDED_TODAY)
    return Probe(
        verdict=_verdict(decided == total),
        total=total,
        flagged=total - decided,
        undeclared=0,
    )


def _probe_tzdispute(_doc: str | None = None) -> Probe:
    """TZ §2.2 — qarshi dalillar va tasdiqni qaytarib olish.

    `flagged` — §2.2 ning **hali bajarilmagan** majburiyatlari. Bugun
    bitta: tuzatishning haqiqiy yuborilishi (§6.4). Sanash, veto,
    «Спорно» va operatorga o'tkazish qurilgan, lekin xabar yuboradigan
    quvur §11 navbatining 6-bandida — ya'ni hozircha `Card.corrects`
    faqat **majburiyatni e'lon qiladi**, uni bajarmaydi.

    Verdikt shuning uchun salbiy: §6.4 «Это не опция» deydi va shu
    holat operator ko'radigan joyda turishi kerak.

    `undeclared` har doim `0`: ro'yxat §2.2 ning o'z matnidan olingan.
    """
    total = len(tzdispute_mod.OBLIGATIONS)
    built = sum(1 for item in tzdispute_mod.OBLIGATIONS if item.built)
    return Probe(
        verdict=_verdict(built == total),
        total=total,
        flagged=total - built,
        undeclared=0,
    )


def _probe_tzrestore(_doc: str | None = None) -> Probe:
    """TZ §4 — tiklanish, opros va «Данные устарели».

    `flagged` — §4 ning **kanalsiz** qolgan qoidalari. Bugun uchta va
    uchalasining ham hisobi yozilgan, yetishmayotgani — yuboradigan
    yoki qabul qiladigan qatlam: В-4 ning tugmasi va §4.1 ning opros
    dialogi (§11 navbatining 5–6-bandlari), В-7 ning datchik qabuli
    (7-band).

    Verdikt shuning uchun salbiy: `close_block()` bugun ishlaydi,
    lekin uni chaqiradigan hech kim yo'q — va bu holat operator
    ko'radigan joyda turishi kerak.

    `undeclared` har doim `0`: ro'yxat §4 ning o'z jadvalidan olingan.
    """
    total = len(tzrestore_mod.RULES)
    built = sum(1 for item in tzrestore_mod.RULES if item.built)
    return Probe(
        verdict=_verdict(built == total),
        total=total,
        flagged=total - built,
        undeclared=0,
    )


def _probe_tzacceptance(_doc: str | None = None) -> Probe:
    """TZ §10 — qabul ro'yxati (ТС-201…ТС-220).

    `flagged` — hali **qurilmagan** bandlar (183-rundan beri nol:
    `0016` Т-10 ning bazadagi taqig'ini qo'ydi va ТС-218 yopildi).
    `undeclared` — yo'l bo'ylab o'lchanmagan, ya'ni faqat o'z
    modulida tekshirilgan bandlar: ular «bajarilgan» ko'rinadi, lekin
    modullar **orasidagi** nosozlikni ko'rmaydi. 181-run ning eng
    qimmat defekti aynan o'sha oraliqda edi.

    Verdikt shuning uchun hamon salbiy: §10 — hujjatning yakuniy
    ro'yxati va uni «20/20» deb o'qish operatorni chalg'itardi —
    yigirmatadan faqat bir nechtasi uchidan-uchiga yurilgan.
    """
    report = tzacc_mod.evaluate()
    return Probe(
        verdict=_verdict(report.clean),
        total=report.total,
        flagged=report.total - report.built,
        undeclared=report.per_module + report.unmeasured,
    )


def _probe_tzscale(_doc: str | None = None) -> Probe:
    """TZ §3 — masshtab: tuman va shahar.

    Bu bo'lim §11 ning navbatida **umuman yo'q** va shu sababdan
    172–181 runlarda qurilmay qoldi: §7 ning `tz.scale.*` sozlamalari
    reyestrda, migratsiyada va vitrinada bor edi, lekin ularni
    o'qiydigan kod yo'q edi. 182-run hisobni qurdi.

    `flagged` — bugun bitta va u **ulash** tarafida. 190-run
    ma'lumot tarafini yopdi: maxrajni beradigan so'rov
    (`reports.queries.blocks_with_users`) va uni §3 ning kirishiga
    aylantiradigan `app.clustering.tzsource` bor. Qolgani —
    `tzscale.evaluate()` ni fuqaro oqimidan chaqirish: bugun
    `outages.scale` ni hamon `06` §5.3 ning narvoni to'ldiradi.
    Verdikt shuning uchun **salbiy** bo'lib qoladi: hisob ham,
    maxraj ham to'g'ri, lekin ular hech qanday kartaga chiqmaydi.

    `undeclared` har doim `0`: ro'yxat §3 ning o'z jadvalidan olingan.
    """
    total = len(tzscale_mod.RULES)
    built = sum(1 for item in tzscale_mod.RULES if item.built)
    return Probe(
        verdict=_verdict(built == total),
        total=total,
        flagged=total - built,
        undeclared=0,
    )


def _probe_tznotify(_doc: str | None = None) -> Probe:
    """TZ §6.3 — bildirishnomaning to'rt turi.

    `flagged` — hali **yasalmaydigan** turlar. 176-runda bittasi
    qurilgan edi («Свет вернулся», §6.3 ning o'z tartibi bo'yicha);
    177-run §11/6 ni bajarib qolgan uchtasini qo'shdi — uzilish,
    rejali ishlar va §6.4 ning tuzatishi (`app.notifications.tzoutage`).

    Verdikt shuning uchun endi ijobiy. U «hammasi yuborilyapti»
    demaydi: reyestr **xabar yasalishini** o'lchaydi, uni chatga
    uzatadigan qatlam alohida. Rejali ishlarning e'lonini kiritish
    (§8 ning operatori) va Т-9 ning jurnal jadvali hali yo'q — bu
    ikkisi `PROGRESS.md` da yozilgan.

    `undeclared` har doim `0`: ro'yxat §6.3 ning o'z jadvalidan olingan.
    """
    total = len(tznotify_mod.NOTICES)
    built = sum(1 for item in tznotify_mod.NOTICES if item.built)
    return Probe(
        verdict=_verdict(built == total),
        total=total,
        flagged=total - built,
        undeclared=0,
    )


def _probe_tzoutage(_doc: str | None = None) -> Probe:
    """TZ §6.3 ning qolgan uch turi va §6.4 — kirish kanallari.

    `tznotify` xabar **yasaladimi** ni o'lchaydi; bu reyestr ikkinchi
    savolni o'lchaydi: yasash uchun kerak bo'lgan ma'lumot qayerdan
    keladi. Uchtadan ikkitasi ulangan: uzilish (hisob va status bor)
    va tuzatish — 180-run Т-9 ning jadvalini qurdi (`tz_receipts`,
    `0014`) va uni o'qiydigan qatlamni (`app.notifications.tzreceipts`)
    yozdi, ya'ni «kimga xato xabar ketgan» endi saqlanadi.

    Uchinchisi yo'q: rejali ishlarning e'lonini §8 ning operatori
    kiritadi va bunday kirish yo'li hali yozilmagan. Verdikt shuning
    uchun hamon salbiy. Ikkala savolni bitta reyestrga qo'shish farqni
    yo'qotardi: «tuzatish qurilgan» va «tuzatishni kimga yuborishni
    bilamiz» — turli da'volar, va §6.4 aynan ikkinchisini talab qiladi.

    `undeclared` har doim `0`: ro'yxat modulning o'z jadvalidan.
    """
    total = len(tzoutage_mod.CHANNELS)
    wired = sum(1 for item in tzoutage_mod.CHANNELS if item.wired)
    return Probe(
        verdict=_verdict(wired == total),
        total=total,
        flagged=total - wired,
        undeclared=0,
    )


def _probe_tzsensor(_doc: str | None = None) -> Probe:
    """TZ §11/7 — datchik va rasmiy manba qabuli.

    `flagged` — tashqaridan **kira olmaydigan** signallar. 178-run da
    uchchalasi ham shunday edi: qabul mantiqi ularni bilardi (`built`),
    lekin na reyestr, na yozadigan endpoint, na jurnal bor edi.

    179-run uchchalasini ham uladi (`tz_sources`, `tz_signals`,
    `POST /tz/readings`), ya'ni `flagged` endi nol va verdikt ijobiy.
    O'lchov **kanal** haqida: har signalning `need` i hali bo'sh emas
    (operator paneli, qurilmaning o'z kaliti), lekin ular qulaylik va
    xavfsizlik savollari — «signal kira oladimi» degan savolga
    ikkalasi ham `ha` deb javob beradi. `tzoutage` reyestri bilan bir
    xil savol, boshqa tomondan qo'yilgan.

    `undeclared` har doim `0`: ro'yxat modulning o'z jadvalidan.
    """
    total = len(tzsensor_mod.INBOUND)
    wired = sum(1 for item in tzsensor_mod.INBOUND if item.wired)
    return Probe(
        verdict=_verdict(wired == total),
        total=total,
        flagged=total - wired,
        undeclared=0,
    )


def _probe_tzoperator(_doc: str | None = None) -> Probe:
    """TZ §8 — operatorning to'rtta vakolati.

    `total` — §8 ning ro'yxati; `flagged` — vakolat bajarilgandan
    keyin **qolgan** ish (`Power.need`). To'rttasi ham `wired`: amal
    bajariladi va jurnalga tushadi. Lekin ikkitasining `need` i bo'sh
    emas va verdikt shuning uchun salbiy — bahsli holatning qarori
    ham, uzilishni yopish ham hodisaning haqiqiy statusiga yetib
    bormaydi: butun TZ qatlami mavjud E5 klasterlashining **yonida**
    turadi. Buni `01` §7 ning DP-4 qorovuli alohida o'lchaydi va bu
    reyestr uni takrorlaydi, yashirmaydi.

    `undeclared` har doim `0`: ro'yxat modulning o'z jadvalidan.
    """
    total = len(tzoperator_mod.POWERS)
    flagged = sum(1 for item in tzoperator_mod.POWERS if item.need)
    unwired = sum(1 for item in tzoperator_mod.POWERS if not item.wired)
    return Probe(
        verdict=_verdict(flagged == 0 and unwired == 0),
        total=total,
        flagged=flagged + unwired,
        undeclared=0,
    )


def _probe_tzconfig(_doc: str | None = None) -> Probe:
    """TZ §7 — o'n oltita sozlama, hech biri o'lchanmagan.

    `flagged` — kelib chiqishi `ПРИДУМАНО` bo'lgan qatorlar. Bugun
    **hammasi**, va verdikt shuning uchun salbiy: 👤 qarori bo'yicha
    Toshkent tarixi ishlatilmaydi, ya'ni TZ §12 ning oldindan
    tekshiruvi o'tkazilmagan va sonlar Samarqandning o'z ma'lumotidan
    keyin o'lchanadi. Reyestr shu holatni yashirmaydi — u operator
    ko'radigan joyda turadi.

    `undeclared` bu yerda har doim `0`: §7 jadvalidan tashqarida
    sozlama bo'lsa, u umuman boshqa hujjatniki (`06` §9).
    """
    marks = tzconfig_mod.origins()
    invented = sum(1 for origin in marks.values() if origin is tzconfig_mod.Origin.INVENTED)
    return Probe(
        verdict=_verdict(invented == 0),
        total=len(marks),
        flagged=invented,
        undeclared=0,
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


def _probe_ux_requirements(_doc: str | None = None) -> Probe:
    """`01` §11–§14 — oqim grafi va o'n beshta qator, uchta o'q.

    `total` — §12–§14 ning qatorlari **va** §11 ning baholanadigan
    tugunlari: bo'lim to'rtta, artefakti esa ikki xil (graf va jadval),
    ya'ni ularni bitta songa qo'shmaslik javobni yashirardi.

    `flagged` uchta sababni **birlashtiradi**, yig'maydi: sirti to'liq
    bo'lmagan qatorlar, repo ko'ra olmaydigan qatorlar va nusxalari
    zid qatorlar. Bugun to'plamlar bir-birini qoplaydi (`UX-S1`
    uchalasida ham bor), ya'ni yig'indi `flagged > total` bo'lib
    qolardi. Uzilgan tugunlar ham shu yerga qo'shiladi.

    `undeclared` — qurilgan, lekin talab nomlagan joyda **emas**
    narsalar. Bugun bittasi: `N` «Предложить подписку» —
    `Surface.REACHABLE`.

    Hujjat kerak emas: baholar reyestrda saqlanadi va ularni hujjat
    bilan `test_ux_requirements_contract` ikki tomonlama qulflaydi.
    """
    report = ux_mod.evaluate()
    judged = [n for n in report.nodes if n.kind in ux_mod.JUDGED_KINDS]
    flagged = (
        {c.code for c in report.unmet}
        | {c.code for c in report.unwatched}
        | {c.code for c in report.drifting}
        | {n.key for n in report.broken_nodes}
    )
    reachable_only = [n for n in report.nodes if n.surface is ux_mod.Surface.REACHABLE]
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.clauses) + len(judged),
        flagged=len(flagged),
        undeclared=len(reachable_only),
    )


def _probe_nfr_appendix(_doc: str | None = None) -> Probe:
    """`01` §15 + §31 — NFR deltasi va meros ilovasi (99-run).

    `total` — yetti NFR qatori **va** §31 ning uch reyestri (o'n meros
    hujjati, olti zamechanie, o'n standart): bo'lim ikkita, artefakti
    to'rt xil, ularni bitta jinsga keltirish javobni yashirardi.

    `flagged` to'rt sababni birlashtiradi: «bajarilgan» dan boshqa
    sinfdagi qatorlar (`S-03` o'lchab bo'lmaydi, `S-04` repo
    tashqarisida, `S-07` mazmuni yo'q hujjatda), repoda yo'q meros
    hujjatlari (o'ntasi ham), kodda izi yo'q zamechanielar va kod
    guvohisiz standartlar.

    `undeclared` — 0: §15/§31 nomlamagan, lekin qurilgan narsa
    topilmadi (bo'limlar ro'yxat, sirt emas).

    Hujjat kerak emas: baholar reyestrda saqlanadi va ularni hujjat
    bilan `test_nfr_appendix_contract` ikki tomonlama qulflaydi.
    """
    report = nfr_appendix_mod.evaluate()
    flagged = (
        len(report.nfrs)
        - len(report.kept)
        + sum(1 for d in report.inherited_docs)  # o'ntasi ham repoda yo'q
        + len(report.unwitnessed_remarks)
        + (len(report.standards) - len(report.witnessed_standards))
    )
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.nfrs)
        + len(report.inherited_docs)
        + len(report.remarks)
        + len(report.standards),
        flagged=flagged,
        undeclared=0,
    )


def _probe_phase0_plan(_doc: str | None = None) -> Probe:
    """`02` — Faza 0 validatsiya rejasi (100-run).

    Birinchi reyestr `01` dan **tashqarida**: paketning ikkinchi
    hujjati. `total` — sakkiz gipoteza, yetti metod, to'qqiz chiqish
    mezoni, o'n risk, besh skoup qatori va Ilova D ning olti meros
    zamechaniesi. §8.1 matritsasi sanalmaydi: uning qatorlari alohida
    artefakt emas, gipotezalarning kombinatsiyasi.

    `flagged` besh sababni birlashtiradi: mahsulot oldindan hal qilib
    qo'ygan gipotezalar (oltitasi — beshta tasdiq tomonga, `H-6` rad
    tomonga), belgilanmagan chiqish mezonlari (to'qqizalasi — o'lchov
    oynasi ochilmagan), kritik risklar (`PH0-R-06`, `PH0-R-08`),
    repo bilan ziddiyatdagi skoup qatori (`PH0-OS-01`) va Faza 0
    yopishga urinmaydigan meros zamechanielari (to'rttasi).

    `undeclared` — 0: hujjat reja, sirt emas; rejadan tashqarida
    qurilgan narsa boshqa reyestrlarning savoli.

    Hujjat kerak emas: baholar reyestrda saqlanadi va ularni hujjat
    bilan `test_phase0_plan_contract` ikki tomonlama qulflaydi.
    """
    report = phase0_mod.evaluate()
    flagged = (
        len(report.prejudged)
        + len(report.unchecked_exits)
        + len(report.critical_risks)
        + len(report.scope_tensions)
        + len(report.unclosed_remarks)
    )
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.hypotheses)
        + len(report.methods)
        + len(report.exit_criteria)
        + len(report.risks)
        + len(report.out_of_scope)
        + len(phase0_mod.INHERITED_REMARK_CODES),
        flagged=flagged,
        undeclared=0,
    )


def _probe_business_requirements(_doc: str | None = None) -> Probe:
    """BRD §8 — 28 ta `BR-*` qatori (101-run).

    Paketning uchinchi hujjati indeksda. `total` — jadval qatorlari.
    `flagged` — `BUILT` bo'lmaganlar: hujjatning o'z legendasida High
    «блокирует запуск», va ularning o'n bittasi shu to'plamda.

    `undeclared` — 0, lekin sababi `phase0_plan` dagidan boshqa: BRD
    biznes sathida gapiradi va qurilgan-nomlanmagan sirtlarni allaqachon
    `functional_requirements.UNNAMED` bilan `scope` sanaydi — bir
    narsani ikki reyestrda ikki marta e'lon qilish hisobni buzadi.

    Hujjat kerak emas: baholar reyestrda, hujjat bilan tenglikni
    `test_business_requirements_contract` ikki tomonlama qulflaydi.
    """
    report = business_mod.evaluate()
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.requirements),
        flagged=sum(
            1 for r in report.requirements if r.delivered not in business_mod.DELIVERED_KEPT
        ),
        undeclared=0,
    )


def _probe_business_rules(_doc: str | None = None) -> Probe:
    """BRD §13 — 15 ta `BRL-*` qoidasi (102-run).

    `total` — jadval qatorlari. `flagged` — yozilganidek
    bajarilmaydiganlar; ular ichida rasmiy qatlam haqidagi ikkala
    qator ham bor (`OFFICIAL_PAIR`): `BRL-03` ishonchni o'zi taqiqlagan
    chegara qiymatiga qo'yadi, `BRL-08` esa statistika agregatida
    qatlamni yo'qotadi.

    `undeclared` — 0, `business_requirements` bilan bir sabab: §13
    xatti-harakat sathida gapiradi va qurilgan-nomlanmagan xulqni
    boshqa reyestrlar allaqachon sanaydi.

    Hujjat kerak emas: baholar reyestrda, hujjat bilan tenglikni
    `test_business_rules_contract` ikki tomonlama qulflaydi.
    """
    report = brl_mod.evaluate()
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.rules),
        flagged=len(report.broken),
        undeclared=0,
    )


def _probe_business_interfaces(_doc: str | None = None) -> Probe:
    """BRD §18–§19 — 18 qator: 10 integratsiya, 8 rol (104-run).

    `total` — ikki jadval qatorlarining yig'indisi. `flagged` ikki
    sababni yig'adi va bu xavfsiz (to'plamlar kesishmaydi — har qator
    o'z jadvalida): `gap` i bo'sh bo'lmagan integratsiyalar (hujjat
    bilan kod ajragan joylar — webhook↔polling, muzlatilgan seed,
    o'lik geokoder talabi, Kafka/Redis↔ADR-05, skoupdan oldinda
    qurilgan Open Data) va `BUILT` bo'lmagan rollar (sakkizdan
    ikkitasi to'liq).

    `undeclared` — 1: Overpass API ikkala hujjatning §18 idan ham
    tashqarida (73-run + 104-run).

    Hujjat kerak emas: baholar reyestrda, hujjat bilan tenglikni
    `test_business_interfaces_contract` ikki tomonlama qulflaydi.
    """
    report = bifc_mod.evaluate()
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.integrations) + len(report.roles),
        flagged=len(report.flagged_integrations) + len(report.flagged_roles),
        undeclared=1,
    )


def _probe_business_reporting(_doc: str | None = None) -> Probe:
    """BRD §20–§21 — 25 qator: 6 hisobot, 4 dashboard, 7 KPI, 8 metrika (105-run).

    `total` — to'rt jadval qatorlarining yig'indisi. `flagged` — `gap` i
    bo'sh bo'lmagan qatorlar; to'plamlar kesishmaydi (har qator o'z
    jadvalida), shuning uchun yig'ish xavfsiz: yig'ilmaydigan sifat
    hisoboti/dashboardi, o'lchab bo'lmaydigan uch §21 metrikasi
    (Time-to-answer, UZ-sessiya, SLA), qurilish bo'yicha bo'sh ikki
    o'lchov (avtotasdiq ulushi, agregat farqi) va son ko'rsatilmaydigan
    `DERIVABLE` qatorlar.

    `undeclared` — 0: bu bo'limlar tizim e'lon qilmaydi, o'lchov va'da
    qiladi; e'lon qilinmagan o'lchov tushunchasi bu yerda bo'sh.

    Hujjat kerak emas: baholar reyestrda, hujjat bilan tenglikni
    `test_business_reporting_contract` ikki tomonlama qulflaydi.
    """
    report = brep_mod.evaluate()
    return Probe(
        verdict=_verdict(report.accurate),
        total=(
            len(report.reports) + len(report.dashboards) + len(report.kpis) + len(report.metrics)
        ),
        flagged=len(report.flagged),
        undeclared=0,
    )


def _probe_business_acceptance(_doc: str | None = None) -> Probe:
    """BRD §22–§23 — 21 qator: 14 qabul mezoni, 7 faza (106-run).

    `total` — ikki jadval qatorlarining yig'indisi. `flagged` — `gap` i
    bo'sh bo'lmagan qatorlar; to'plamlar kesishmaydi (mezon o'z jadvalida,
    faza o'znikida), yig'ish xavfsiz: `LIVE` bo'lmagan o'nta mezon
    (Ph.0 ning beshalasi ham — dala ishi odamniki, Toshkent regressiyasi
    va skoupli rollar bu repoda ifodalanmaydi) va beshta faza (uchtasi
    go/no-go dan oldin bajarib qo'yilgan — xronologiya topilmasi, Ph.0
    boshlanmagan, Support ta'rifan yopilmaydi).

    `undeclared` — 0: bu bo'limlar qabul va jadvalni va'da qiladi, tizim
    e'lon qilmaydi; e'lon qilinmagan xulq tushunchasi bu yerda bo'sh.

    Hujjat kerak emas: baholar reyestrda, hujjat bilan tenglikni
    `test_business_acceptance_contract` ikki tomonlama qulflaydi.
    """
    report = bacc_mod.evaluate()
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.acceptance) + len(report.phases),
        flagged=len(report.flagged),
        undeclared=0,
    )


def _probe_business_architecture(_doc: str | None = None) -> Probe:
    """BRD §24 — 25 qator: 19 diagramma tuguni, 6 arxitektura qarori (107-run).

    `total` — diagramma tugunlari (Users subgraph siz — u auditoriya,
    mahsulot emas) va qarorlar jadvalining yig'indisi. `flagged` — `gap` i
    bo'sh bo'lmagan qatorlar; to'plamlar kesishmaydi (tugun diagrammada,
    qaror o'z jadvalida), yig'ish xavfsiz: oltita `ABSENT` tugun
    (Kafka/Redis — ADR-05, ombor/ingestor/geokoder/manba oqimi — umuman
    yo'q), yorlig'i kodga zid uchta `RESHAPED` (Go-bot, React-web,
    DBSCAN-worker), va'da qilingan qismi yetishmaydigan to'rt monolit
    tuguni va yarim bajarilgan bitta qaror (Territory Registry).

    `undeclared` — 0: bo'lim mahsulot shaklini va'da qiladi, tizim e'lon
    qilmaydi; e'lon qilinmagan xulq tushunchasi bu yerda bo'sh.

    Hujjat kerak emas: baholar reyestrda, hujjat bilan tenglikni
    `test_business_architecture_contract` ikki tomonlama qulflaydi.
    """
    report = barch_mod.evaluate()
    return Probe(
        verdict=_verdict(report.accurate),
        total=len(report.nodes) + len(report.decisions),
        flagged=len(report.flagged),
        undeclared=0,
    )


def _probe_business_glossary(_doc: str | None = None) -> Probe:
    """BRD §25–§26 — 50 qator: 17 atama, 9 hujjat, 12 standart, 4
    diagramma, 8 ochiq savol (108-run, paket yakuni).

    `flagged` — `gap` i bo'sh bo'lmagan qatorlar: ikkita eskirgan «3 часа»
    atamasi (`BR-014` egizagi), ikkita yolg'on tasdiq (DBSCAN va kodda
    mavjud bo'lmagan qamrov-tashqarisi statusi), §26.1 ning repoda yo'q
    to'qqiz hujjati, SEC holatiga zid xavfsizlik standarti da'vosi va 👤 qarori
    bekor qilgan `OQ-1` «bloklaydi» ustuni. To'plamlar kesishmaydi —
    har qator o'z jadvalida, yig'ish xavfsiz.

    `undeclared` — 1: butun BRD «джиттер» ni bilmaydi, mahsulotning
    markaziy maxfiylik mexanizmi (`05` §3.1) lug'atdan tashqarida.

    Hujjat kerak emas: baholar reyestrda, hujjat bilan tenglikni
    `test_business_glossary_contract` ikki tomonlama qulflaydi.
    """
    report = bglos_mod.evaluate()
    return Probe(
        verdict=_verdict(report.accurate),
        total=(
            len(report.terms)
            + len(report.docs)
            + len(report.standards)
            + len(report.diagrams)
            + len(report.oq)
        ),
        flagged=len(report.flagged),
        undeclared=len(bglos_mod.UNDECLARED_TERMS),
    )


def _probe_business_environment(_doc: str | None = None) -> Probe:
    """BRD §14–§17 — 39 qator: 10 taxmin, 7 cheklov, 12 risk, 10 bog'liqlik (103-run).

    `total` — to'rt jadval qatorlarining yig'indisi. `flagged` to'rt
    sababni **yig'adi** va bu xavfsiz (to'plamlar kesishmaydi — har
    qator faqat o'z jadvalida): javobi oldindan tanlangan taxminlar,
    buzilgan/chetga qo'yilgan cheklovlar, chorasi repoda to'liq
    bo'lmagan risklar va qurilgan mahsulotda o'lik bog'liqliklar.

    `undeclared` — 0, `business_requirements` bilan bir sabab: bu
    bo'limlar muhitni tasvirlaydi, qurilgan-nomlanmagan xulqni boshqa
    reyestrlar sanaydi.

    Hujjat kerak emas: baholar reyestrda, hujjat bilan tenglikni
    `test_business_environment_contract` ikki tomonlama qulflaydi.
    """
    report = benv_mod.evaluate()
    return Probe(
        verdict=_verdict(report.accurate),
        total=(
            len(report.assumptions)
            + len(report.constraints)
            + len(report.risks)
            + len(report.dependencies)
        ),
        flagged=(
            len(report.prejudged)
            + len(report.breached)
            + len(report.waived)
            + len(report.unguarded_risks)
            + len(report.moot)
        ),
        undeclared=0,
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
        code="phase0_plan",
        spec=phase0_mod.SPEC,
        module="app.release.phase0_plan",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_phase0_plan,
    ),
    Registry(
        code="business_requirements",
        spec=business_mod.SPEC,
        module="app.release.business_requirements",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_business_requirements,
    ),
    Registry(
        code="business_rules",
        spec=brl_mod.SPEC,
        module="app.release.business_rules",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_business_rules,
    ),
    Registry(
        code="business_environment",
        spec=benv_mod.SPEC,
        module="app.release.business_environment",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_business_environment,
    ),
    Registry(
        code="business_interfaces",
        spec=bifc_mod.SPEC,
        module="app.release.business_interfaces",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_business_interfaces,
    ),
    Registry(
        code="business_reporting",
        spec=brep_mod.SPEC,
        module="app.release.business_reporting",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_business_reporting,
    ),
    Registry(
        code="business_acceptance",
        spec=bacc_mod.SPEC,
        module="app.release.business_acceptance",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_business_acceptance,
    ),
    Registry(
        code="business_architecture",
        spec=barch_mod.SPEC,
        module="app.release.business_architecture",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_business_architecture,
    ),
    Registry(
        code="business_glossary",
        spec=bglos_mod.SPEC,
        module="app.release.business_glossary",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_business_glossary,
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
        code="tzstatus",
        spec=tzstatus_mod.SPEC,
        module="app.clustering.tzstatus",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_tzstatus,
    ),
    Registry(
        code="tzdispute",
        spec=tzdispute_mod.SPEC,
        module="app.clustering.tzdispute",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_tzdispute,
    ),
    Registry(
        code="tzrestore",
        spec=tzrestore_mod.SPEC,
        module="app.clustering.tzrestore",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_tzrestore,
    ),
    Registry(
        code="tzacceptance",
        spec=tzacc_mod.SPEC,
        module="app.release.tz_acceptance",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_tzacceptance,
    ),
    Registry(
        code="tzscale",
        spec=tzscale_mod.SPEC,
        module="app.clustering.tzscale",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_tzscale,
    ),
    Registry(
        code="tznotify",
        spec=tznotify_mod.SPEC,
        module="app.notifications.tzrestored",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_tznotify,
    ),
    Registry(
        code="tzoutage",
        spec=tzoutage_mod.SPEC,
        module="app.notifications.tzoutage",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_tzoutage,
    ),
    Registry(
        code="tzsensor",
        spec=tzsensor_mod.SPEC,
        module="app.reports.tzsensor",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_tzsensor,
    ),
    Registry(
        code="tzoperator",
        spec=tzoperator_mod.SPEC,
        module="app.admin.tzoperator",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_tzoperator,
    ),
    Registry(
        code="tzconfig",
        spec=tzconfig_mod.SPEC,
        module="app.core.tzconfig",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_tzconfig,
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
        code="ux_requirements",
        spec=ux_mod.SPEC,
        module="app.release.ux_requirements",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_ux_requirements,
    ),
    Registry(
        code="nfr_appendix",
        spec=nfr_appendix_mod.SPEC,
        module="app.release.nfr_appendix",
        serving=Serving.SELF_CONTAINED,
        endpoint=None,
        probe=_probe_nfr_appendix,
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
